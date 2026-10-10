// Krīzes meklēšana bez AI: no brīva teksta (LV/RU/EN) nosaka vajadzību (scenāriju), vai zvanīt 112, un vietu.
// Noteikumi: scenariji.json. Teksts nekur netiek sūtīts, viss notiek pārlūkā.
// Pavirši rakstītam tekstam (telefonā): garumzīmes nost abās pusēs, apostrofs vārdā pazūd, cipari atdalīti no burtiem,
// vieta var būt pielipusi vārdam, krievu valoda latīņu burtiem, viena drukas kļūda vai dubults burts (notes/klasifikators.md, 4. kārta).
const Klasifikators = (() => {
  // mazie burti, bez garumzīmēm un mīkstinājumiem (ā→a, ķ→k, й→и); apostrofs vārda vidū pazūd ("rel'sov" → "relsov"),
  // izņemot angļu saīsinājumus ("can't" → "can t", kā atslēgvārdos); "ogre15" → "ogre 15";
  // pieturzīmes → atstarpes; abās malās atstarpe
  const normalizet = s => ' ' + String(s ?? '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '')
    .replace(/(\p{L})['’ʼ`](?!(?:t|s|ll|re|ve|d|m)(?!\p{L}))(?=\p{L})/gu, '$1')
    .replace(/(\p{L})(?=\p{N})|(\p{N})(?=\p{L})/gu, '$1$2 ')
    .replace(/[^\p{L}\p{N}]+/gu, ' ').trim() + ' ';

  // 'patvert' → ' patvert' (vārda sākums); 'deg$' → ' deg ' (vesels vārds). Tekstam abās malās ir atstarpe.
  function raksts(atslegvards) {
    const vesels = atslegvards.endsWith('$');
    const t = normalizet(vesels ? atslegvards.slice(0, -1) : atslegvards).trimEnd();
    const vardi = t.trim().split(' ').length;
    return { teksts: t + (vesels ? ' ' : ''), vardi, svars: vardi, vesels, saknes: t.trim() };
  }

  // Damerau-Levenšteins, bet tikai "0, 1 vai vairāk" (vairāk = 2): vajag tikai ≤ 1, tāpēc agri pārtraucam
  function dl1(a, b) {
    if (Math.abs(a.length - b.length) > 1) return 2;
    // ar vienu labojumu (aizstāšana, ielikšana, dzēšana, blakus burtu maiņa) kāds no šiem pāriem sakrīt — ātra atmešana
    if (a[0] !== b[0] && a[1] !== b[1] && a[1] !== b[0] && a[0] !== b[1]) return 2;
    let iepr2 = null, iepr = Array.from({ length: b.length + 1 }, (_, i) => i);
    for (let i = 1; i <= a.length; i++) {
      const rinda = [i];
      let min = i;
      for (let j = 1; j <= b.length; j++) {
        let d = Math.min(iepr[j] + 1, rinda[j - 1] + 1, iepr[j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1));
        if (iepr2 && j > 1 && a[i - 1] === b[j - 2] && a[i - 2] === b[j - 1]) d = Math.min(d, iepr2[j - 2] + 1);
        rinda[j] = d;
        if (d < min) min = d;
      }
      if (min > 1) return 2;
      iepr2 = iepr;
      iepr = rinda;
    }
    return Math.min(iepr[b.length], 2);
  }

  // Krievu valoda latīņu burtiem: kirilicas atslēgvārdus pārvēršam latīņu burtos, un abas puses — vienotā formā,
  // lai dažādas shēmas sakrīt (pozhar, bolnitsa/bolnica, vyzvat/vizvat, poterjalsja/poteryalsya, kholodno/holodno)
  const KIR = { а: 'a', б: 'b', в: 'v', г: 'g', д: 'd', е: 'e', ж: 'zh', з: 'z', и: 'i', к: 'k', л: 'l', м: 'm', н: 'n',
    о: 'o', п: 'p', р: 'r', с: 's', т: 't', у: 'u', ф: 'f', х: 'h', ц: 'c', ч: 'ch', ш: 'sh', щ: 'sch', ъ: '', ы: 'i',
    ь: '', э: 'e', ю: 'ju', я: 'ja' };
  const kanons = v => v.replace(/shch/g, 'sch').replace(/kh/g, 'h').replace(/ts/g, 'c').replace(/yu/g, 'ju')
    .replace(/ya/g, 'ja').replace(/yo/g, 'e').replace(/y/g, 'i').replace(/w/g, 'v').replace(/x/g, 'ks');
  const latiniski = v => kanons(Array.from(v, c => KIR[c] ?? c).join(''));
  const bezDubultiem = v => v.replace(/(.)\1+/g, '$1');
  const LABOTA_SVARS = 0.85;  // labots vārds sver mazāk par precīzi atrastu: precīzais uzvar, ja abi ir vaicājumā

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

  // Garākā vārda sākuma garums, kas ir kopā (0, ja neviena)
  function garakaisSakums(v, kopa) {
    for (let k = v.length; k >= 1; k--) if (kopa.has(v.slice(0, k))) return k;
    return 0;
  }

  const TIPA_PRIORITATE = { valstspilseta: 0, pilseta: 1, novads: 2 };
  const labakaVieta = (a, b) => !a || b.forma.length > a.forma.length ||
    (b.forma.length === a.forma.length && TIPA_PRIORITATE[b.regions.tips] < TIPA_PRIORITATE[a.regions.tips]);

  // regioni: [{kods, nosaukums, tips, bbox}] no /api/regioni
  function sagatavotVietas(regioni, sinonimi = {}) {
    const vietas = [];
    for (const r of regioni) {
      // otrā forma ir ģenitīvs (Ogres, Alojas) — pielipušai vietai to neņemam ("nenoskalojas" ≠ Aloja)
      vietvarduFormas(r.nosaukums).forEach((forma, i) => vietas.push({ forma: ' ' + forma, regions: r, genitivs: i === 1 }));
    }
    for (const [nosaukums, formas] of Object.entries(sinonimi)) {
      const r = regioni.filter(r => r.nosaukums === nosaukums).sort((a, b) => TIPA_PRIORITATE[a.tips] - TIPA_PRIORITATE[b.tips])[0];
      if (r) for (const f of formas) vietas.push({ forma: normalizet(f), regions: r });
    }
    return vietas;
  }

  function atrastVietu(teksts, vietas) {
    let labaka = null;
    for (const v of vietas) if (teksts.includes(v.forma) && labakaVieta(labaka, v)) labaka = v;
    return labaka?.regions || null;
  }

  // Vieta pielipusi vārdam ("pludiogre", "ogrepludi", "nav elektribasrezekne"): vietas forma ≥ 4 burti vārda sākumā
  // vai beigās, atlikums ≥ 3 burti. Atgriež tekstu ar atdalītu vietu, lai atlikumu var atpazīt.
  function atdalitVietu(teksts, vietas, latVardi) {
    let labaka = null;
    const vardi = teksts.trim().split(' ');
    for (const [i, w] of vardi.entries()) {
      if (w.length < 7) continue;
      for (const v of vietas) {
        const f = v.forma.trim();
        if (f.length < 4 || f.includes(' ') || w.length - f.length < 3) continue;
        // ja atslēgvārds sniedzas vietas daļā, tā nav pielipusi vieta
        const zinams = garakaisSakums(w, latVardi);
        const beigas = !v.genitivs && w.endsWith(f) && zinams <= w.length - f.length;
        const sakums = !beigas && w.startsWith(f) && zinams <= f.length;
        if ((beigas || sakums) && labakaVieta(labaka, v)) {
          labaka = { ...v, i, dalits: beigas ? w.slice(0, -f.length) + ' ' + f : f + ' ' + w.slice(f.length) };
        }
      }
    }
    if (!labaka) return null;
    vardi[labaka.i] = labaka.dalits;
    return { teksts: ' ' + vardi.join(' ') + ' ', vieta: labaka.regions };
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
    const vietuVardi = new Set(vietas.map(v => v.forma.trim()).filter(f => !f.includes(' ')));
    // "Vai domājāt…?": citi scenāriji, kas ir ne vairāk kā 15 % zem labākā (slieksnis 0.85; src/meklesana/vaicajumi.json)
    const slieksnis = noteikumi.vai_domajat_slieksnis ?? 0.85;

    // Ātrumam: atslēgvārdi pēc pirmajiem 1–3 burtiem (ar atstarpi, ja īsāks) — vaicājumā meklējam tikai tos,
    // kuru sākums ir kādā vaicājuma vārda sākumā. s = scenārija nr. sarakstā, −1 = dzīvības draudi.
    const pecSakuma = new Map();
    const visi = [...scenariji.flatMap((s, i) => s.raksti.map(r => ({ r, s: i }))), ...draudi.map(r => ({ r, s: -1 }))];
    for (const [nr, x] of visi.entries()) {
      x.nr = nr;  // secība failā: vienādiem atrastajiem paliek tā pati kā agrāk
      const k = x.r.teksts.slice(1, 4);
      if (!pecSakuma.has(k)) pecSakuma.set(k, []);
      pecSakuma.get(k).push(x);
    }

    // Vārdnīca labošanai: katrs atslēgvārdu vārds (latīņu → pats, kirilicas → latīniskā forma) un krievu vietvārdi
    const latVardi = new Set(), kirVardi = new Map(), dubLat = new Map(), dubKir = new Map(), dlVardi = [];
    const vardnicai = [...visi.map(x => x.r.saknes), ...Object.values(noteikumi.vietu_sinonimi || {}).flat().map(f => normalizet(f).trim())];
    for (const v of new Set(vardnicai.flatMap(s => s.split(' ')))) {
      const kir = /[а-я]/.test(v);
      if (!kir && !/^[a-z]+$/.test(v)) continue;
      const lat = kir ? latiniski(v) : v;
      if (lat.length < 3) { if (!kir) latVardi.add(v); continue; }
      if (kir) { if (!kirVardi.has(lat)) kirVardi.set(lat, v); } else latVardi.add(v);
      const dub = bezDubultiem(lat), dubKopa = kir ? dubKir : dubLat;
      if (dub.length >= 4 && !dubKopa.has(dub)) dubKopa.set(dub, v);
      if (lat.length >= 5) dlVardi.push({ lat, orig: v, kir });
    }
    // Damerau-Levenšteina kandidāti (≥ 5 burti): vārds un visi tā varianti bez viena burta ("simetriskā dzēšana" —
    // divas virknes ar DL ≤ 1 vienmēr dod kopīgu šādu variantu), tāpēc vaicājumā jāpārbauda tikai daži desmiti atslēgu.
    // Sagatavo pirmajā reizē, kad vajag (lapas ielāde paliek ātra).
    let pecDzesuma = null;
    function dzesumuIndekss() {
      if (pecDzesuma) return pecDzesuma;
      pecDzesuma = new Map();
      const pielikt = (k, x) => { const a = pecDzesuma.get(k); if (!a) pecDzesuma.set(k, [x]); else if (a[a.length - 1] !== x) a.push(x); };
      for (const x of dlVardi) {
        pielikt(x.lat, x);
        for (let i = 0; i < x.lat.length; i++) pielikt(x.lat.slice(0, i) + x.lat.slice(i + 1), x);
      }
      return pecDzesuma;
    }

    // Vārds, ko neatpazina neviens atslēgvārds → { vards, veids } vai null. tikaiDubulti: tikai 2) solis (ja vaicājumā
    // jau kaut kas atrasts). Tīra funkcija, tāpēc kešojam.
    const labotie = new Map();
    function labotVardu(w, tikaiDubulti = false) {
      const k = (tikaiDubulti ? '2' : '') + w;
      if (!labotie.has(k)) {
        if (labotie.size > 3000) labotie.clear();
        labotie.set(k, labotVarduBezKesas(w, tikaiDubulti));
      }
      return labotie.get(k);
    }

    function labotVarduBezKesas(w, tikaiDubulti) {
      if (!/^[a-z]+$/.test(w)) return null;
      const c = kanons(w);
      const lLat = garakaisSakums(w, latVardi), lKir = garakaisSakums(c, kirVardi);
      // 1) krieviski latīņu burtiem: "pozhar" → "пожар", "sveta" → "света"; 3 burtu vārdi ("net") — tikai veseli
      if (!tikaiDubulti && lKir > lLat && (lKir >= 4 || lKir === c.length)) return { vards: kirVardi.get(c.slice(0, lKir)) + c.slice(lKir), veids: 'translits' };
      if (w.length < 4 || lLat >= 4 || lLat === w.length) return null;  // par īsu vai jau pazīstams vārds
      // 2) dubults burts: "pluudi" → "pludi", "ezzera" → "ezera"
      for (const [v, kopa] of [[w, dubLat], [c, dubKir]]) {
        const d = bezDubultiem(v);
        if (d === v) continue;
        for (let k = d.length; k >= 4; k--) {
          const orig = kopa.get(d.slice(0, k));
          if (orig) return { vards: orig + d.slice(k), veids: 'dubults' };
        }
      }
      if (tikaiDubulti) return null;
      // 3) viena kļūda (Damerau-Levenšteins ≤ 1) atslēgvārdā no ≥ 5 burtiem; garākais atslēgvārds uzvar.
      // Vārda sākumu garumā g salīdzina ar atslēgvārdu garumā g, g − 1 vai g + 1 (aizstāts, iztrūkst, lieks burts).
      let lab = null;
      for (const avots of new Set([w, c])) {
        for (let g = 4; g <= avots.length; g++) {
          const q = avots.slice(0, g);
          const atslegas = [q];
          for (let i = 0; i < g; i++) atslegas.push(q.slice(0, i) + q.slice(i + 1));
          for (const a of atslegas) for (const x of dzesumuIndekss().get(a) || []) {
            // garāks atslēgvārds uzvar; tam pašam — garums tuvāk atslēgvārdam ("nevra" → "nevar", nevis "nevar" + "a")
            const tuvums = Math.abs(g - x.lat.length);
            if ((x.kir ? c : w) !== avots || tuvums > 1 || lab && (x.lat.length < lab.x.lat.length ||
              x.lat.length === lab.x.lat.length && tuvums >= lab.tuvums)) continue;
            // īsiem (5–6 burti): pirmais burts pareizs (vai samainīts ar otro) un aiz tā ne vairāk par galotni
            // ("pludmale" ≠ "pludi", "jauki" ≠ "lauki")
            const iss = x.lat.length < 7;
            if (iss && (avots.length - g > 2 || avots[0] !== x.lat[0] && !(avots[0] === x.lat[1] && avots[1] === x.lat[0]))) continue;
            if (dl1(q, x.lat) <= 1) lab = { x, tuvums, atlikums: avots.slice(g) };
          }
        }
      }
      return lab ? { vards: lab.x.orig + lab.atlikums, veids: 'kluda' } : null;
    }

    // Atrastie atslēgvārdi tekstā: { pec: [[vārda nr, vārdi, svars, burti, r]] katram scenārijam, draudi, aizņemtie vārdi }
    function atrast(t) {
      const sakumi = new Set();
      for (let i = 1; i < t.length; i++) if (t[i - 1] === ' ' && t[i] !== ' ') for (let k = 1; k <= 3; k++) sakumi.add(t.substr(i, k));
      const vardaNr = [];
      for (let i = 0, nr = -1; i < t.length; i++) { if (t[i] !== ' ' && t[i - 1] === ' ') nr++; vardaNr[i] = nr; }
      const pec = scenariji.map(() => []);
      const aiznemti = new Set();
      let draudiAtrasti = false;
      for (const k of sakumi) {
        for (const { r, s, nr } of pecSakuma.get(k) || []) {
          const i = t.indexOf(r.teksts);
          if (i < 0) continue;
          const no = vardaNr[i + 1];
          for (let j = 0; j < r.vardi; j++) aiznemti.add(no + j);
          if (s < 0) draudiAtrasti = true;
          else pec[s].push([no, r.vardi, r.svars, r.saknes.length, nr]);
        }
      }
      return { pec, draudiAtrasti, aiznemti };
    }

    function klasificet(vaicajums) {
      let t = normalizet(vaicajums);
      let vieta = atrastVietu(t, vietas);
      if (!vieta) { const a = atdalitVietu(t, vietas, latVardi); if (a) ({ teksts: t, vieta } = a); }
      let atr = atrast(t);
      // Vārdus, kuros neviens atslēgvārds nesākas (un kas nav vietvārdi vai cipari), mēģinām labot un meklējam vēlreiz
      const vardi = t.trim().split(' ');
      const laboti = new Set();
      let arKludu = false;
      // Pilnā labošana (translits, viena kļūda) tikai tad, ja precīzi nav atrasts neviens scenārijs
      const bezLabosanas = atr.pec.some(p => p.length);
      const jauni = vardi.map((v, i) => {
        if (atr.aiznemti.has(i) || vietuVardi.has(v)) return v;
        // ja kaut kas jau atrasts, labojam tikai dubultus burtus: citādi pareizi, bet atslēgvārdos neesoši vārdi
        // ("augsta", "daudzi") "labotos" par līdzīgiem atslēgvārdiem ("auksta", "drudzi")
        const l = labotVardu(v, bezLabosanas);
        if (!l) return v;
        laboti.add(i);
        if (l.veids !== 'translits') arKludu = true;
        return l.vards;
      });
      if (laboti.size) {
        const t2 = ' ' + jauni.join(' ') + ' ';
        atr = atrast(t2);
        vieta ||= atrastVietu(t2, vietas);
      }
      // Katrs vaicājuma vārds scenārijam dod punktus vienreiz: atrastos atslēgvārdus ņem no stiprākā, un tos, kas
      // pārklājas ar jau paņemtu ("car on fire" un "fire"), neskaita ("ugunsgrēks" atbilst gan 'ugun', gan 'ugunsgrēk').
      const punkti = atrasti => {
        atrasti.sort((a, b) => b[2] - a[2] || b[1] - a[1] || a[4] - b[4]);
        const aiznemti = new Set();
        let summa = 0, burti = 0;
        for (const [no, garums, svars, b] of atrasti) {
          const vardi = Array.from({ length: garums }, (_, j) => no + j);
          if (vardi.some(v => aiznemti.has(v))) continue;
          vardi.forEach(v => aiznemti.add(v));
          summa += vardi.some(v => laboti.has(v)) ? svars * LABOTA_SVARS : svars;
          burti += b;
        }
        return [summa, burti];
      };
      const rez = scenariji.map((s, i) => { const [p, b] = punkti(atr.pec[i]); return { s, punkti: p, burti: b }; });
      const max = Math.max(...rez.map(x => x.punkti));
      // Pirmais = galvenais; citi ("Vai domāji…?") tikai, ja sasniedz `slieksnis` daļu no labākā. Vienādiem paliek secība failā.
      const atrasti = rez.filter(x => x.punkti && x.punkti >= max * slieksnis)
        // vienādiem punktiem — garāks (konkrētāks) atrastais vārda sākums ("бомбоубежищ" pirms "бомб"), tad secība failā
        .sort((a, b) => b.punkti - a.punkti || b.burti - a.burti).slice(0, 3);
      // "cilvēks neelpo" bez cita scenārija → noklusētais (medicīna)
      const noklusets = scenariji.find(s => s.kods === noteikumi.dzivibas_draudi_scenarijs);
      if (atr.draudiAtrasti && !atrasti.length && noklusets) atrasti.push({ s: noklusets });
      return {
        scenariji: atrasti.map(x => x.s),
        // aptuveni = atrasts tikai pēc drukas kļūdas labošanas (translits nav "aptuveni")
        aptuveni: arKludu && !bezLabosanas && atrasti.length > 0,
        zvanit112: atr.draudiAtrasti || !!atrasti[0]?.s.zvanit112,
        dzivibas_draudi: atr.draudiAtrasti,
        vieta,
        ...(laboti.size ? { labots: jauni.join(' ') } : {}),
      };
    }

    return { klasificet, scenariji, labotVardu };
  }

  return { izveidot, normalizet, vietvarduFormas };
})();

// Vaicājuma valoda ('lv' | 'ru' | 'en') rezultāta kartītes "rāmim" (valoda.js); padomi paliek latviski.
// Kirilica → krievu; latīņu burtiem — angļu vārdi pret latviešu vārdiem (garumzīmes, palīgvārdi). Vietvārdi ar lielo
// burtu (Rēzekne, Ogre) neskaitās, tāpēc "flood Rēzekne" ir angliski, "нет света Rēzekne" — krieviski.
// Krievu translits ("net sveta") — pēc dažiem biežiem vārdiem. Nezināms → 'lv'.
Klasifikators.valoda = (() => {
  const EN = new Set(('flood flooding flooded floods fire fires smoke burning burns power outage electricity blackout water ' +
    'need help shelter shelters bunker hospital doctor pharmacy police ambulance storm wind tree fallen road closed blocked ' +
    'evacuation evacuate where nearest near me my house home is there the an we in at of and with without heat heating cold ' +
    'gas leak injured hurt bleeding unconscious breathing explosion siren alarm missing child food money cash atm fuel petrol ' +
    'station ice snow lightning thunder drone war attack bomb what how can sick ill hungry safe danger dangerous out ' +
    'flat apartment building collapsed river rising level warning lost help').split(' '));
  const LV = new Set('nav ir un kur man mums vajag ar bez pie uz kas ka es mes mana mans musu ja ta tur ko kad lidz'.split(' '));
  const RU_LAT = new Set('net sveta svet vody pozhar pomogite gde ukrytie bolnica bolnitsa navodnenie pomoshch skoraya skoraja'.split(' '));
  return function valoda(vaicajums) {
    const vardi = String(vaicajums ?? '').split(/[^\p{L}]+/u).filter(Boolean);
    let kir = 0, lat = 0, en = 0, lv = 0, ru = 0;
    for (const v of vardi) {
      if (/\p{Script=Cyrillic}/u.test(v)) { kir++; continue; }
      const m = v.toLowerCase();
      const bez = m.normalize('NFD').replace(/[̀-ͯ]/g, '');
      if (EN.has(m)) en++;
      else if (LV.has(bez)) lv++;
      else if (RU_LAT.has(m)) ru++;
      else if (/^\p{Lu}/u.test(v)) continue;  // nezināms vārds ar lielo burtu — vietvārds (Rēzekne, Ogre)
      else if (m !== bez) lv++;
      lat++;
    }
    if (kir && kir >= lat) return 'ru';
    if (en > lv && en >= ru) return 'en';
    if (ru > lv && ru > en) return 'ru';
    return 'lv';
  };
})();

if (typeof module !== 'undefined') module.exports = Klasifikators;
