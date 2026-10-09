// Krīzes meklēšana bez AI: no brīva teksta (LV/RU/EN) nosaka vajadzību (scenāriju), vai zvanīt 112, un vietu.
// Noteikumi: scenariji.json. Teksts nekur netiek sūtīts, viss notiek pārlūkā.
const Klasifikators = (() => {
  // mazie burti, bez garumzīmēm un mīkstinājumiem (ā→a, ķ→k), pieturzīmes → atstarpes; abās malās atstarpe
  const normalizet = s => ' ' + String(s ?? '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '')
    .replace(/[^\p{L}\p{N}]+/gu, ' ').trim() + ' ';

  // 'patvert' → ' patvert' (vārda sākums); 'deg$' → ' deg ' (vesels vārds). Tekstam abās malās ir atstarpe.
  function raksts(atslegvards) {
    const vesels = atslegvards.endsWith('$');
    const t = normalizet(vesels ? atslegvards.slice(0, -1) : atslegvards).trimEnd();
    const vardi = t.trim().split(' ').length;
    return { teksts: t + (vesels ? ' ' : ''), vardi, svars: vardi, vesels, saknes: t.trim() };
  }

  function levenshtein(a, b) {
    let iepr = Array.from({ length: b.length + 1 }, (_, i) => i);
    for (let i = 1; i <= a.length; i++) {
      const rinda = [i];
      for (let j = 1; j <= b.length; j++) {
        rinda[j] = Math.min(iepr[j] + 1, rinda[j - 1] + 1, iepr[j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1));
      }
      iepr = rinda;
    }
    return iepr[b.length];
  }

  // Viena burta kļūda (dakteri → daktetri) garākiem viena vārda atslēgvārdiem; īsākiem par 6 burtiem
  // ir pārāk daudz nejaušu sakritību (bumbu ≈ bumbieri).
  function lidzigs(vards, r) {
    if (r.svars > 1 || r.saknes.length < 6) return false;
    const n = r.saknes.length;
    const garumi = r.vesels ? [vards.length] : [n, n + 1];
    return garumi.some(g => vards.length >= g && Math.abs(g - n) <= 1 && levenshtein(vards.slice(0, g), r.saknes) <= 1);
  }

  // Latviskās vietvārdu formas, ko cilvēki raksta: Ogre/Ogrē/Ogres, Cēsis/Cēsīs/Cēsu, Talsi/Talsos,
  // Tukums/Tukumā, Ventspils/Ventspilī, Saldus/Saldū; "Ogres novads/novadā" → 'ogres novad'.
  function vietvarduFormas(nosaukums) {
    const n = normalizet(nosaukums).trim();
    if (n.endsWith(' novads')) return [n.slice(0, -1)];
    const f = [n, n + 's'];
    if (n.endsWith('pils')) f.push(n.slice(0, -1) + 'i');
    else if (n.endsWith('is')) f.push(n.slice(0, -2) + 'u');
    else if (n.endsWith('us')) f.push(n.slice(0, -2) + 'u');
    else if (n.endsWith('i')) f.push(n.slice(0, -1) + 'os', n.slice(0, -1) + 'u');
    else if (n.endsWith('s')) f.push(n.slice(0, -1) + 'a');
    return f.map(x => x + ' ');
  }

  const TIPA_PRIORITATE = { valstspilseta: 0, pilseta: 1, novads: 2 };

  // regioni: [{kods, nosaukums, tips, bbox}] no /api/regioni
  function sagatavotVietas(regioni, sinonimi = {}) {
    const vietas = [];
    for (const r of regioni) {
      for (const forma of vietvarduFormas(r.nosaukums)) vietas.push({ forma: ' ' + forma, regions: r });
    }
    for (const [nosaukums, formas] of Object.entries(sinonimi)) {
      const r = regioni.filter(r => r.nosaukums === nosaukums).sort((a, b) => TIPA_PRIORITATE[a.tips] - TIPA_PRIORITATE[b.tips])[0];
      if (r) for (const f of formas) vietas.push({ forma: normalizet(f), regions: r });
    }
    return vietas;
  }

  function atrastVietu(teksts, vietas) {
    let labaka = null;
    for (const v of vietas) {
      if (!teksts.includes(v.forma)) continue;
      if (!labaka || v.forma.length > labaka.forma.length ||
          (v.forma.length === labaka.forma.length && TIPA_PRIORITATE[v.regions.tips] < TIPA_PRIORITATE[labaka.regions.tips])) labaka = v;
    }
    return labaka?.regions || null;
  }

  // noteikumi: scenariji.json saturs. Atgriež sagatavotu klasifikatoru.
  function izveidot(noteikumi, regioni = []) {
    const scenariji = noteikumi.scenariji.map(s => ({ ...s, raksti: s.atslegvardi.map(raksts) }));
    // Atslēgvārds, kas ir daudzos scenārijos ("dūm", "evaku"), sver mazāk nekā rets ("kūl"): svars / √(scenāriju skaits).
    const biezums = {};
    for (const s of scenariji) for (const t of new Set(s.raksti.map(r => r.teksts))) biezums[t] = (biezums[t] || 0) + 1;
    for (const s of scenariji) for (const r of s.raksti) r.svars /= Math.sqrt(biezums[r.teksts]);
    const draudi = noteikumi.dzivibas_draudi.map(raksts);
    const vietas = sagatavotVietas(regioni, noteikumi.vietu_sinonimi);
    // "Vai domājāt…?": citi scenāriji, kas sasniedz šo daļu no labākā punktiem (noskaņots ar src/meklesana/vaicajumi.json)
    const slieksnis = noteikumi.vai_domajat_slieksnis ?? 0.45;

    function klasificet(vaicajums) {
      const t = normalizet(vaicajums);
      const vardi = t.trim().split(' ').filter(Boolean);
      // Katrs vaicājuma vārds scenārijam dod punktus vienreiz: no labākā atslēgvārda, kas sākas tajā
      // ("ugunsgrēks" atbilst gan 'ugun', gan 'ugunsgrēk' — skaitām tikai vienu).
      // Katrs vaicājuma vārds scenārijam dod punktus vienreiz: atrastos atslēgvārdus ņem no stiprākā, un tos, kas
      // pārklājas ar jau paņemtu ("car on fire" un "fire"), neskaita.
      const vardaNr = [];
      for (let i = 0, nr = -1; i < t.length; i++) { if (t[i] !== ' ' && t[i - 1] === ' ') nr++; vardaNr[i] = nr; }
      const punkti = s => {
        const atrasti = [];
        for (const r of s.raksti) {
          const i = t.indexOf(r.teksts);
          if (i >= 0) atrasti.push([vardaNr[i + 1], r.vardi, r.svars, r.saknes.length]);
        }
        atrasti.sort((a, b) => b[2] - a[2] || b[1] - a[1]);
        const aiznemti = new Set();
        let summa = 0, burti = 0;
        for (const [no, garums, svars, b] of atrasti) {
          const vardi = Array.from({ length: garums }, (_, j) => no + j);
          if (vardi.some(v => aiznemti.has(v))) continue;
          vardi.forEach(v => aiznemti.add(v));
          summa += svars;
          burti += b;
        }
        return [summa, burti];
      };
      let rez = scenariji.map(s => { const [p, b] = punkti(s); return { s, punkti: p, burti: b, aptuveni: false }; });
      const draudiAtrasti = draudi.some(r => t.includes(r.teksts));
      // Aptuveno (ar drukas kļūdu) meklējam tikai tad, ja nekas cits nav atrasts — arī dzīvības draudi.
      if (!draudiAtrasti && rez.every(x => !x.punkti)) {
        rez = scenariji.map(s => ({ s, punkti: s.raksti.some(r => vardi.some(v => lidzigs(v, r))) ? 1 : 0, aptuveni: true }));
      }
      const max = Math.max(...rez.map(x => x.punkti));
      // Pirmais = galvenais; citi ("Vai domāji…?") tikai, ja sasniedz `slieksnis` daļu no labākā. Vienādiem paliek secība failā.
      const atrasti = rez.filter(x => x.punkti && (x.punkti === max || x.punkti > max * slieksnis))
        // vienādiem punktiem — garāks (konkrētāks) atrastais vārda sākums ("бомбоубежищ" pirms "бомб"), tad secība failā
        .sort((a, b) => b.punkti - a.punkti || (b.burti || 0) - (a.burti || 0)).slice(0, 3);
      // "cilvēks neelpo" bez cita scenārija → noklusētais (medicīna)
      const noklusets = scenariji.find(s => s.kods === noteikumi.dzivibas_draudi_scenarijs);
      if (draudiAtrasti && !atrasti.length && noklusets) atrasti.push({ s: noklusets, aptuveni: false });
      return {
        scenariji: atrasti.map(x => x.s),
        aptuveni: atrasti.some(x => x.aptuveni),
        zvanit112: draudiAtrasti || !!atrasti[0]?.s.zvanit112,
        dzivibas_draudi: draudiAtrasti,
        vieta: atrastVietu(t, vietas),
      };
    }

    return { klasificet, scenariji };
  }

  return { izveidot, normalizet, vietvarduFormas };
})();

if (typeof module !== 'undefined') module.exports = Klasifikators;
