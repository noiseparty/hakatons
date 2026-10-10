// "Kas Jums vajadzīgs?" (Ko tev vajag?): krīzes meklēšana — viens vaicājums ir gana. Teksts → scenārijs (klasifikators.js + scenariji.json,
// bez AI, pārlūkā) + vieta (adrese ar mājas numuru → VZD /api/adreses; vietvārds → reģions; citādi mana vieta).
// Rezultātā uzreiz: padoms, tuvākās vietas scenārija slāņos, drošās vietas (evakuācija, izmitināšana no CA plāniem,
// patvertne, 24/7 slimnīca), plūdu scenārijiem — plūdu riska zona un upes līmenis; LVĢMC brīdinājumu josla (bridinajumi.js).
// Lieto app.js globālos (karte, stavoklis, iegut…).
const krizesMeklesana = (() => {
  const UZ_KATEGORIJU = 3;
  // Drošās vietas: rāda situācijām un vietas/adreses vaicājumiem. Tukšai kategorijai — norāde uz patvertni.
  const DROSAS = [
    { kods: 'evakuacijas_punkts', nos: 'Evakuācijas pulcēšanās vieta', ikona: '🚩', aizstat: true },
    { kods: 'izmitinasana', nos: 'Izmitināšanas vieta', ikona: '🏠', aizstat: true },
    { kods: 'patvertne', nos: 'Tuvākā patvertne', ikona: '🛡️' },
    { kods: 'neatliekama_24h', nos: '24/7 neatliekamā palīdzība', ikona: '🏥' },
  ];
  const PLUDU_SCENARIJI = new Set(['pludi', 'udens_celas']);
  // Nokrišņu un augsnes konteksta rinda (Open-Meteo caur /api/augsne): plūdiem, lietusgāzēm un vētrām
  const LAIKA_SCENARIJI = new Set(['pludi', 'udens_celas', 'negaiss', 'vetra_jumts', 'viesulvetra']);
  // Vējš tuvākajā LVĢMC stacijā tagad (/api/noverojumi): vētrām un vējam
  const VEJA_SCENARIJI = new Set(['vetra_jumts', 'viesulvetra', 'negaiss', 'sniegavetra', 'koks_pari_celam', 'vads_pari_celam']);
  const AVOTI_LVGMC = {
    pludi: '<a href="https://data.gov.lv/dati/lv/dataset/3-cikla-latvijas-pldu-postjumu-vietu-un-pldu-riska-kartes1" target="_blank" rel="noopener">LVĢMC plūdu riska kartes 2026–2031</a> · CC0',
    udens: '<a href="https://data.gov.lv/dati/lv/dataset/hidrometeorologiskie-noverojumi" target="_blank" rel="noopener">LVĢMC hidroloģiskie novērojumi</a> · CC0',
    bridinajumi: '<a href="https://data.gov.lv/dati/lv/dataset/hidrometeorologiskie-bridinajumi" target="_blank" rel="noopener">LVĢMC hidrometeoroloģiskie brīdinājumi</a> · CC0',
  };
  let klasifikators = null;
  let talakGimenes = {};        // scenariji.json talak_gimenes: "Kas notiks tālāk" soļi pa scenāriju ģimenēm
  let pedejais = null;          // { teksts, scenarijs } — atkārto, kad mainās atrašanās vieta vai reģions
  let pieprasijums = null;
  const rezultatuSlanis = L.layerGroup().addTo(karte);
  const kaste = el('rezultati');

  let bezDatiem = false;  // /api/kategorijas, /regioni vai /avoti neielādējās (app.js)

  async function sakt(regioniSaraksts, datiNav = false) {
    bezDatiem = datiNav;
    try {
      const noteikumi = await (await fetch('scenariji.json')).json();
      klasifikators = Klasifikators.izveidot(noteikumi, regioniSaraksts);
      izveidotIndeksu(noteikumi);
      talakGimenes = noteikumi.talak_gimenes || {};
    } catch {
      el('jautajums').disabled = true;
      el('jautajums').placeholder = 'Meklēšana nav pieejama';
      return;
    }
    const q = new URLSearchParams(location.search).get('q');
    const saitesVieta = typeof Dalities !== 'undefined' && Dalities.vietaNoUrl();  // dalities.js: ?q=…&lat=&lon= — atskaites punkts no saites
    if (q && saitesVieta) stavoklis.vieta = saitesVieta;
    if (q) { el('jautajums').value = q; meklet(q); raditRezultatus(); }
  }

  el('meklet-forma').addEventListener('submit', e => {
    e.preventDefault();
    aizvertPopularos();
    const teksts = el('jautajums').value.trim();
    if (teksts) { meklet(teksts); raditRezultatus(); } else notirit();
  });

  // Biežāk meklētais: tukšajā laukā ieklikšķinot — 3 populārākie atpazītie vaicājumi (/api/meklejumi/top, kešs 60 s).
  // Ja API nav pieejams vai atpazīto ir mazāk par 3 — papildina ar šiem piemēriem, lai nekad nav tukšs.
  // Saglabāto tekstu nerāda: "atpazits" apgalvo klients, tāpēc katru vaicājumu klasificē vēlreiz un rāda tikai
  // scenārija nosaukumu (+ vietu) no klasifikatora; neatpazītos vai tikai aptuveni atpazītos izmet.
  const POPULARI_REZERVE = ['nav elektrības', 'plūdi ogrē', 'tuvākā patvertne'];
  const populari = el('populari');
  const popPogas = populari.querySelector('.populari-pogas');
  let popularie = null, popularieLaiks = 0, popIelade = null;
  let uzskaite = null;  // { vaicajums, klikskis } pēdējai skaitītajai meklēšanai (zinot(), zemāk)

  function popularieNoVaicajumiem(vaicajumi) {
    const rez = new Map();
    for (const v of [...vaicajumi, ...POPULARI_REZERVE]) {
      const k = klasifikators.klasificet(String(v));
      const s = k.scenariji[0];
      if (!s || k.aptuveni || k.dzivibas_draudi) continue;
      const teksts = s.nosaukums + (k.vieta ? ' ' + k.vieta.nosaukums : '');
      if (!rez.has(teksts)) rez.set(teksts, { teksts, kods: s.kods, nos: s.nosaukums + (k.vieta ? ' · ' + k.vieta.nosaukums : '') });
      if (rez.size === 3) break;
    }
    return [...rez.values()];
  }

  async function atvertPopularos() {
    const lauks = el('jautajums');
    if (lauks.value.trim() || lauks.disabled || !klasifikators) return;
    if (!popularie || Date.now() - popularieLaiks > 60000) {
      popIelade ||= iegut('/meklejumi/top?n=10').then(d => d.vaicajumi, () => []).then(v => {
        popularie = popularieNoVaicajumiem(Array.isArray(v) ? v : []);
        popularieLaiks = Date.now();
        popIelade = null;
      });
      await popIelade;
      if (lauks.value.trim() || !populari.contains(document.activeElement) && document.activeElement !== lauks) return;
    }
    populari.classList.remove('ieteikumi');
    el('populari-virsraksts').textContent = 'Biežāk meklētais';
    popPogas.innerHTML = popularie.map(p =>
      `<button type="button" data-teksts="${esc(p.teksts)}" data-kods="${esc(p.kods)}">${esc(p.nos)}</button>`).join('');
    populari.hidden = false;
  }
  function aizvertPopularos() {
    clearTimeout(ieteikumuTaimeris);
    populari.hidden = true;
  }
  el('jautajums').addEventListener('focus', atvertPopularos);
  el('jautajums').addEventListener('click', atvertPopularos);
  let ieteikumuTaimeris = null;
  el('jautajums').addEventListener('input', () => {
    clearTimeout(ieteikumuTaimeris);
    ieteikumuTaimeris = setTimeout(() => {
      const t = el('jautajums').value.trim();
      if (!t) atvertPopularos();
      else if (t.length >= 2) raditIeteikumus(t);
      else aizvertPopularos();
    }, 80);
  });
  popPogas.addEventListener('click', e => {
    const poga = e.target.closest('button[data-kods]');
    const scenarijs = klasifikators?.scenariji.find(s => s.kods === poga?.dataset.kods);
    if (!scenarijs) return;
    aizvertPopularos();
    el('jautajums').value = poga.dataset.teksts;
    uzskaite = null;  // ieteikumu klikšķi neskaita, citādi tie paši sev pieskaita popularitāti
    meklet(poga.dataset.teksts, scenarijs);  // ar scenāriju: teksts dod tikai vietu, meklet() neskaita
    raditRezultatus();
  });
  // Tastatūra: ↓ no lauka uz pirmo, ←/→/↑/↓ starp pogām, Escape aizver un atgriežas laukā
  el('meklet-forma').addEventListener('keydown', e => {
    if (populari.hidden) return;
    const pogas = [...popPogas.querySelectorAll('button')];
    const i = pogas.indexOf(document.activeElement);
    if (e.key === 'Escape') { aizvertPopularos(); el('jautajums').focus(); e.preventDefault(); return; }
    if (e.key === 'ArrowDown' && i < 0 && document.activeElement === el('jautajums')) { pogas[0]?.focus(); e.preventDefault(); return; }
    if (i < 0) return;
    const solis = { ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1 }[e.key];
    if (!solis) return;
    e.preventDefault();
    if (i + solis < 0) el('jautajums').focus();
    else pogas[Math.min(i + solis, pogas.length - 1)].focus();
  });
  // Klikšķis vai fokuss ārpus lauka un saraksta aizver
  document.addEventListener('pointerdown', e => { if (!el('meklet-forma').contains(e.target)) aizvertPopularos(); });
  el('meklet-forma').addEventListener('focusout', e => {
    if (e.relatedTarget && !el('jautajums').contains(e.relatedTarget) && !populari.contains(e.relatedTarget)) aizvertPopularos();
  });

  // ---- Drukas kļūdas, vārdu formas, latīņu burtiem rakstīta krievu valoda (pirms klasifikatora) ----
  // Klasifikators salīdzina vārdu sākumus bez garumzīmēm. Ja tas neko neatrod (vai tikai aptuveni), mēģinām vēlreiz ar
  // labotu tekstu: katru vārdu, kas nesākas ne ar vienu atslēgvārdu, aizstājam ar tuvāko atslēgvārdu — pēc galotnes
  // noņemšanas vai ar vienu burta kļūdu (Damerau-Levenšteins ≤ 1, vārdiem no 5 burtiem). Vieta paliek no oriģinālā.
  const vienk = s => String(s ?? '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '');
  const GALOTNES = ['iem', 'am', 'as', 'os', 'us', 'ai', 'ei', 'em', 'im', 'is', 'es', 'a', 'e', 'i', 'u', 's'];
  // Krieviski, bet latīņu burtiem (translitā) → latviskais atslēgvārds; kirilicu atslēgvārdi jau saprot
  const TRANSLITS = [
    ['pozhar', 'ugunsgrēks'], ['pozar', 'ugunsgrēks'], ['navodnen', 'plūdi'], ['zatop', 'plūdi'], ['potop', 'plūdi'],
    ['ukryt', 'patvertne'], ['ubezhish', 'patvertne'], ['bomboubezh', 'patvertne'], ['bolnic', 'slimnīca'], ['bolnits', 'slimnīca'],
    ['apteka', 'aptieka'], ['apteki', 'aptieka'], ['skoraya', 'ātrā palīdzība'], ['skoraja', 'ātrā palīdzība'], ['vrach', 'ārsts'],
    ['policiy', 'policija'], ['policij', 'policija'], ['militsi', 'policija'], ['evakuac', 'evakuācija'],
    ['elektrichestv', 'elektrība'], ['sveta net', 'nav elektrības'], ['net sveta', 'nav elektrības'],
    ['vody net', 'nav ūdens'], ['net vody', 'nav ūdens'], ['uragan', 'vētra'], ['shtorm', 'vētra'], ['burya', 'vētra'],
    ['vzryv', 'sprādziens'], ['trevog', 'trauksme'], ['sirena', 'trauksme'], ['benzin', 'degviela'], ['bankomat', 'bankomāts'],
  ];
  let indekss = [];  // [{ k: atslēgvārds bez garumzīmēm, orig }] — viena vārda, latīņu burtiem, no 3 burtiem
  // Ātrumam (telefonā katrs taustiņš): atslēgvārdi bez garumzīmēm pa scenārijiem, sagatavoti vienreiz, un jau
  // labotie vārdi — labotVardu ir tīra funkcija no vārda un indeksa, tāpēc rezultāts nemainās.
  const normAtsl = new Map();
  const laboti = new Map();

  function izveidotIndeksu(noteikumi) {
    for (const sc of noteikumi.scenariji) normAtsl.set(sc.kods, sc.atslegvardi.map(a => vienk(a)));
    const redzets = new Set();
    for (const sc of noteikumi.scenariji) for (const a of sc.atslegvardi) {
      const k = vienk(a.replace(/\$$/, '')).trim();
      if (k.length < 3 || /\s/.test(k) || !/^[a-z]+$/.test(k) || redzets.has(k)) continue;
      redzets.add(k);
      indekss.push({ k, vesels: a.endsWith('$') });
    }
    indekss.sort((a, b) => b.k.length - a.k.length);  // garākie (precīzākie) pirmie
  }

  // Optimālā virknes salīdzināšana (Damerau-Levenšteins ar blakus burtu apmaiņu); pārtrauc, ja > 1
  function dl1(a, b) {
    if (Math.abs(a.length - b.length) > 1) return 2;
    // ar vienu labojumu (aizstāšana, ielikšana, dzēšana, blakus burtu maiņa) vismaz viens no šiem sakrīt — ātra atmešana
    if (a[0] !== b[0] && a[1] !== b[1] && a[1] !== b[0] && a[0] !== b[1]) return 2;
    const d = Array.from({ length: a.length + 1 }, (_, i) => [i]);
    for (let j = 1; j <= b.length; j++) d[0][j] = j;
    for (let i = 1; i <= a.length; i++) {
      let min = Infinity;
      for (let j = 1; j <= b.length; j++) {
        const c = a[i - 1] === b[j - 1] ? 0 : 1;
        d[i][j] = Math.min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + c);
        if (i > 1 && j > 1 && a[i - 1] === b[j - 2] && a[i - 2] === b[j - 1]) d[i][j] = Math.min(d[i][j], d[i - 2][j - 2] + 1);
        min = Math.min(min, d[i][j]);
      }
      if (min > 1) return 2;
    }
    return d[a.length][b.length];
  }

  function labotVardu(v) {
    if (!laboti.has(v)) {
      if (laboti.size > 2000) laboti.clear();
      laboti.set(v, labotVarduBezKesas(v));
    }
    return laboti.get(v);
  }

  function labotVarduBezKesas(v) {
    if (!/^[a-z]+$/.test(v) || v.length < 4) return v;
    if (indekss.some(x => x.vesels ? v === x.k : v.startsWith(x.k))) return v;  // jau atpazīstams
    // galotne nost: "plūdos" → "plud" → atslēgvārds, kas sākas ar to
    for (const g of GALOTNES) {
      if (!v.endsWith(g) || v.length - g.length < 4) continue;
      const sakne = v.slice(0, -g.length);
      const x = indekss.find(x => x.k.startsWith(sakne) || sakne.startsWith(x.k));
      if (x) return x.k;
    }
    if (v.length < 5) return v;
    // viena burta kļūda atslēgvārda garumā (± 1 burts), garākiem atslēgvārdiem no 5 burtiem
    for (const x of indekss) {
      if (x.k.length < 5) continue;
      for (const garums of [x.k.length, x.k.length + 1, x.k.length - 1]) {
        if (garums > v.length || garums < 4) continue;
        if ((x.vesels ? dl1(v, x.k) : dl1(v.slice(0, garums), x.k)) <= 1) return x.k;
      }
    }
    return v;
  }

  function labot(teksts) {
    let t = ' ' + vienk(teksts).replace(/[^\p{L}\p{N}]+/gu, ' ').trim() + ' ';
    for (const [no, uz] of TRANSLITS) t = t.replace(new RegExp(' ' + no + '[a-z]*', 'g'), ' ' + vienk(uz));
    return t.trim().split(' ').map(labotVardu).join(' ');
  }

  // Oriģinālais teksts, ja tas jau ir atpazīts; citādi labotais (vieta un 112 — no abiem)
  function klasificetLabots(teksts) {
    const rez = klasifikators.klasificet(teksts);
    if (rez.scenariji.length && !rez.aptuveni) return rez;
    const labots = labot(teksts);
    if (labots === vienk(teksts).trim()) return rez;
    const r2 = klasifikators.klasificet(labots);
    if (!r2.scenariji.length || r2.aptuveni && rez.scenariji.length) return rez;
    return { ...r2, vieta: rez.vieta || r2.vieta, dzivibas_draudi: rez.dzivibas_draudi || r2.dzivibas_draudi,
      zvanit112: rez.zvanit112 || r2.zvanit112, labots };
  }

  // ---- Ieteikumi rakstot: līdz 6 situācijām (+ atpazītā vieta); Enter / klikšķis meklē ar izvēlēto situāciju ----
  function ieteikumi(teksts) {
    const k = klasificetLabots(teksts);
    const rez = [...k.scenariji];
    const vardi = vienk(teksts).replace(/[^\p{L}\p{N}]+/gu, ' ').trim().split(' ');
    const pedejais = vardi[vardi.length - 1] || '';
    if (pedejais.length >= 2) {
      const sc = klasifikators.scenariji;
      // atslēgvārds sākas ar rakstāmo vārdu ("plū" → plūdi), tad nosaukumā ir šis vārds
      const pecAtslegas = sc.filter(s => (normAtsl.get(s.kods) || s.atslegvardi.map(vienk)).some(a => a.startsWith(pedejais)));
      const pecNosaukuma = sc.filter(s => vienk(s.nosaukums).split(/[^a-z]+/).some(v => v.startsWith(pedejais)));
      for (const s of [...pecAtslegas, ...pecNosaukuma]) if (!rez.includes(s)) rez.push(s);
    }
    return { scenariji: rez.slice(0, 6), vieta: k.vieta };
  }

  function raditIeteikumus(teksts) {
    if (!klasifikators || el('jautajums').disabled) return;
    const { scenariji, vieta } = ieteikumi(teksts);
    if (!scenariji.length) { aizvertPopularos(); return; }
    populari.classList.add('ieteikumi');
    el('populari-virsraksts').textContent = 'Ieteikumi';
    popPogas.innerHTML = scenariji.map(s => `<button type="button" data-teksts="${esc(teksts)}" data-kods="${esc(s.kods)}">` +
      `${esc(s.nosaukums)}${vieta ? ` <small>· ${esc(vieta.nosaukums)}</small>` : ''}</button>`).join('');
    populari.hidden = false;
  }

  // Uzskaite: atpazītu vaicājumu (situācija vai slānis) vienreiz pēc meklēšanas un vienreiz, kad atver rezultātu.
  // Sūta tikai tekstu bez adreses; bez lietotāja datiem. Kļūdas klusi ignorē.
  function zinot(vaicajums, klikskis = false) {
    fetch(API + '/meklejumi', { method: 'POST', keepalive: true, headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ vaicajums, atpazits: true, klikskis }) }).catch(() => {});
  }

  // Telefonā rezultāti ir zem kartes (un panelis var būt aizvērts): atveram to un ritinām līdz rezultātiem
  function raditRezultatus() {
    if (!matchMedia('(max-width: 800px)').matches) return;
    if (typeof Apaksa !== 'undefined') { el('jautajums').blur(); return Apaksa.atvert('puse'); }  // apaksa.js: lapa virs kartes
    if (document.body.classList.contains('panelis-slegts')) el('panelis-poga').click();
    el('jautajums').blur();
    setTimeout(() => kaste.scrollIntoView({ behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth', block: 'start' }), 250);
  }
  kaste.addEventListener('click', e => {
    const darbiba = e.target.closest('[data-darbiba]')?.dataset.darbiba;
    if (darbiba === 'notirit') notirit();
    if (darbiba === 'atrast') atrastMani();
    const cits = klasifikators?.scenariji.find(s => s.kods === e.target.closest('[data-cits]')?.dataset.cits);
    if (cits && pedejais) meklet(pedejais.teksts, cits);
    const li = e.target.closest('li[data-lat]');
    if (li && uzskaite && !uzskaite.klikskis) { uzskaite.klikskis = true; zinot(uzskaite.vaicajums, true); }
    if (li && !e.target.closest('a')) {
      const ll = { lat: +li.dataset.lat, lng: +li.dataset.lon };
      karte.setView(ll, Math.max(karte.getZoom(), 16));
      L.popup().setLatLng(ll).setContent(popupSaturs(JSON.parse(li.dataset.p), ll)).openOn(karte);
    }
  });

  function notirit() {
    if (typeof Dalities !== 'undefined') Dalities.notiritUrl();
    pedejais = null;
    uzskaite = null;
    if (pieprasijums) pieprasijums.abort();
    rezultatuSlanis.clearLayers();
    kaste.hidden = true;
    kaste.innerHTML = '';
    el('jautajums').value = '';
    bridinajumi(null);
  }

  function atkartot() {
    if (pedejais) meklet(pedejais.teksts, pedejais.scenarijs);
  }

  // app.js: atrašanās vietu neizdevās noteikt — paskaidrojam rezultātos, nevis tikai panelī zem tiem
  function vietaNav(liegta) {
    const zina = kaste.querySelector('.vieta-zina');
    if (zina) zina.innerHTML = `<span class="kluda">${liegta ? 'Atrašanās vieta nav atļauta.' : 'Atrašanās vietu neizdevās noteikt.'}</span>
      Pievienojiet vaicājumam adresi vai pilsētu, piem., „${esc(pedejais?.teksts || 'plūdi')} Ogrē” vai „… Brīvības 15 Ogre”.`;
  }

  // Kur meklēt: adrese vaicājumā → vietvārds vaicājumā (reģionu meklet() jau izvēlējās) → mana atrašanās vieta →
  // izvēlētais reģions. Reģionam ņem bbox centru.
  function izcelsme(vieta, adrese) {
    if (adrese) return { lat: adrese.lat, lon: adrese.lon, apraksts: `no adreses ${isaAdrese(adrese.adrese)}`, nosaukums: isaAdrese(adrese.adrese) };
    if (vieta) return { ...centrs(vieta), apraksts: `no centra (${vieta.nosaukums})`, regions: true, nosaukums: vieta.nosaukums };
    if (stavoklis.vieta?.noSaites) return { ...stavoklis.vieta, apraksts: 'no saitē norādītās vietas', nosaukums: 'Saitē norādītajā vietā' };
    if (stavoklis.vieta) return { ...stavoklis.vieta, apraksts: stavoklis.vieta.adrese ? `no adreses ${isaAdrese(stavoklis.vieta.adrese)}` : 'no Jums',
      nosaukums: stavoklis.vieta.adrese ? isaAdrese(stavoklis.vieta.adrese) : 'Jūsu vietā' };
    const r = regioni[stavoklis.regions];
    if (r) return { ...centrs(r), apraksts: `no centra (${r.nosaukums})`, regions: true, nosaukums: r.nosaukums };
    return null;
  }
  // bridinajumi.js (josla augšā); ja tas neielādējās — bez joslas
  const bridinajumi = (v, n) => { if (typeof Bridinajumi !== 'undefined') Bridinajumi.atjaunot(v, n); };
  const centrs = r => ({ lat: (r.bbox[1] + r.bbox[3]) / 2, lon: (r.bbox[0] + r.bbox[2]) / 2 });

  // Adrese vaicājumā ir tad, ja tajā ir skaitlis (mājas numurs): "plūdi Brīvības 15 Ogre", "aptieka Rīgas iela 5 Cēsīs".
  // Mēģinām garākās vārdu virknes ap numuru (pirms tā ir scenārija vārdi); /api/adreses vajag, lai visi vārdi sakrīt.
  async function atrastAdresi(teksts, signal) {
    const vardi = teksts.replace(/[,;]+/g, ' ').trim().split(/\s+/);
    const nr = vardi.findIndex(v => /\d/.test(v));
    if (nr < 0) return null;
    const varianti = [];
    for (let no = 0; no <= nr; no++) for (let lidz = vardi.length; lidz > nr; lidz--) varianti.push(vardi.slice(no, lidz));
    varianti.sort((a, b) => b.length - a.length);
    for (const v of varianti.filter(v => v.length >= 2).slice(0, 6)) {
      try {
        const a = await iegut('/adreses?' + new URLSearchParams({ q: v.join(' '), limit: 1 }), signal);
        // atlikums: vaicājums bez adreses vārdiem — no tā nosaka situāciju ("Mednieku iela" nav medības)
        if (a.length) return { ...a[0], atlikums: vardi.filter(x => !v.includes(x)).join(' ') };
      } catch (e) {
        if (e.name === 'AbortError') throw e;
        return null;  // adrešu meklēšana nav pieejama — turpinām ar vietvārdu / atrašanās vietu
      }
    }
    return null;
  }

  // scenarijs: izvēlēts ar pogu ("Vai domāji…?") — tad tekstu izmanto tikai vietai un 112.
  async function meklet(teksts, scenarijs = null) {
    if (!klasifikators) return;
    pedejais = { teksts, scenarijs };
    let rez = klasificetLabots(teksts);
    if (scenarijs) {
      rez.scenariji = [scenarijs];
      rez.zvanit112 = rez.dzivibas_draudi || !!scenarijs.zvanit112;
    }
    kaste.hidden = false;
    rezultatuSlanis.clearLayers();
    if (pieprasijums) pieprasijums.abort();
    pieprasijums = new AbortController();
    const signal = pieprasijums.signal;

    // Dzīvības draudi — uzreiz, pirms jebkādas ielādes (teksts, bez pogām un saitēm)
    const draudi = rez.dzivibas_draudi
      ? '<p class="draudi">⚠ Izklausās, ka apdraudēta dzīvība. Zvaniet 112 tūlīt: dispečers palīdzēs, ko darīt.</p>' : '';
    const zvanitTeksts = !rez.dzivibas_draudi && rez.zvanit112 ? '<p class="zvanit-teksts">Ja apdraudēta dzīvība vai veselība, zvaniet 112.</p>' : '';

    let adrese = null;
    if (/\d/.test(teksts)) {
      kaste.innerHTML = draudi + '<p class="piezime">Meklē adresi…</p>';
      try { adrese = await atrastAdresi(teksts, signal); } catch { return; }  // atcelts ar jaunu meklēšanu
      if (adrese && !scenarijs) {
        const draudiBija = rez.dzivibas_draudi;
        rez = klasificetLabots(adrese.atlikums);
        rez.dzivibas_draudi ||= draudiBija;
        rez.zvanit112 ||= draudiBija;
      }
    }

    // Vieta kartē: adrese (tad reģiona filtru noņemam) vai vietvārds vaicājumā ("lācis Ogrē") — vienmēr, arī ja
    // scenārijs nav atpazīts vai tam nav slāņu kartē.
    let jaunsRegions = false;
    if (adrese) {
      if (stavoklis.regions) { radtRegionu(''); jaunsRegions = true; }
      izveletiesAdresi(adrese, false);  // app.js: sākumpunkts, marķieris, atjauno karti
    } else if (rez.vieta) {
      jaunsRegions = stavoklis.regions !== rez.vieta.kods;
      radtRegionu(rez.vieta.kods);
    }
    const vieta = adrese ? null : rez.vieta;
    const no = izcelsme(vieta, adrese);
    if (typeof Dalities !== 'undefined') Dalities.atjaunotUrl(teksts, no);  // adreses joslā ?q=…[&lat=&lon=], lai rezultātu var nosūtīt
    bridinajumi(no, no?.nosaukums);

    const [galvenais, ...citi] = rez.scenariji;
    if (!scenarijs) {  // "Vai domājāt" pogas atkārto to pašu tekstu — neskaitām otrreiz
      uzskaite = galvenais ? { vaicajums: adrese ? adrese.atlikums : teksts, klikskis: false } : null;
      if (uzskaite) zinot(uzskaite.vaicajums);
    }
    const kurTeksts = adrese ? isaAdrese(adrese.adrese) : vieta?.nosaukums;
    const pludi = galvenais && PLUDU_SCENARIJI.has(galvenais.kods);
    // Lēmums vispirms (112, brīdinājums šai vietai, plūdu zona jā/nē), tad situācija, padoms un vietas
    const galva = draudi + zvanitTeksts +
      (no ? '<div id="rez-lemums"></div>' + (pludi ? pluduBloks() : '') : '') +
      (galvenais
        ? `<p class="sapratu">${galvenais.nr ? 'Situācija' : 'Meklēju'}: <b>${esc(galvenais.nosaukums)}</b>${kurTeksts ? ' · ' + esc(kurTeksts) : ''}</p>` +
          (galvenais.padoms ? `<p class="padoms">${esc(galvenais.padoms)}</p>` : '')
        : kurTeksts ? `<p class="sapratu">${adrese ? 'Adrese' : 'Vieta'}: <b>${esc(kurTeksts)}</b></p>` +
            '<p class="piezime">Uzrakstiet arī, kas notiek, piem., „plūdi”, „nav elektrības”, „evakuācija”.</p>' : '') +
      (no ? '<p class="piezime" id="rez-mana-vieta" hidden></p>' : '') +
      (bezDatiem ? '<p class="piezime kluda">Kartes dati pašlaik nav pieejami: tuvākās vietas nevaram parādīt. Padoms un 112 ir spēkā.</p>' : '');
    const vaiDomaji = citi.length ? `<p class="piezime">Vai domājāt:</p><div class="atras-pogas">` +
      citi.map(s => `<button type="button" data-cits="${esc(s.kods)}">${esc(s.nosaukums)}</button>`).join('') + '</div>' : '';
    const beigas = talakBloks(galvenais) + vaiDomaji +
      '<button type="button" class="otra" data-darbiba="saraksts"><span aria-hidden="true">☰</span> Visi kartes objekti sarakstā</button>' +
      '<button type="button" class="otra" data-darbiba="zinot"><span aria-hidden="true">📣</span> Ziņot par bīstamību šeit</button>' +
      (typeof Dalities !== 'undefined' ? Dalities.pogas() : '') + notiritPoga();

    // Nekas nav atpazīts: ne situācija, ne vieta
    if (!galvenais && !kurTeksts) {
      if (jaunsRegions) atjaunot();
      kaste.innerHTML = draudi + `<p class="piezime">Nesapratām, kas Jums vajadzīgs. Uzrakstiet citiem vārdiem, piem., „patvertne”, „ārsts”,
        „plūdi Ogrē”, „nav elektrības Brīvības 15 Ogre”.</p>` + (draudi ? '' : '<p class="zvanit-teksts">Ja apdraudēta dzīvība vai veselība, zvaniet 112.</p>') + notiritPoga();
      return;
    }

    // Scenārija slāņi (kas jau ir kartē) + drošās vietas situācijām un vietas/adreses vaicājumiem
    const kodi = (galvenais?.kategorijas || []).filter(k => kategorijas[k]?.skaits);
    const arDrosam = !galvenais || galvenais.nr || galvenais.kods === 'patvertne';
    const drosas = arDrosam ? DROSAS.filter(d => !kodi.includes(d.kods)) : [];
    if (kodi.length) {
      stavoklis.kategorijas = new Set(kodi);
      document.querySelectorAll('#kategorijas input').forEach(i => { i.checked = stavoklis.kategorijas.has(i.value); });
    }
    if (pludi) radtPludus(true);  // app.js: plūdu riska zonu slānis kartē
    const laiks = galvenais && LAIKA_SCENARIJI.has(galvenais.kods);
    if (galvenais?.kods === 'negaiss' && typeof Zibens !== 'undefined') Zibens.radit(true);  // zibens.js: pēdējās 30 min
    if (kodi.length || jaunsRegions) atjaunot();

    if (!no) {
      kaste.innerHTML = galva + `<p class="piezime vieta-zina">Lai atrastu tuvākās vietas, pievienojiet adresi vai pilsētu, piem.,
        „${esc(teksts)} Ogrē” vai „${esc(teksts)} Brīvības 15 Ogre”, vai nosakiet savu atrašanās vietu.</p>
        <button type="button" class="galvena" data-darbiba="atrast"><span aria-hidden="true">📍</span> Noteikt manu atrašanās vietu</button>` + beigas;
      return;
    }

    kaste.innerHTML = galva + '<div id="rez-vietas"><p class="piezime">Meklē tuvākās vietas…</p></div><div id="rez-pasvaldiba"></div>' + beigas;
    const ll = { lat: no.lat.toFixed(5), lon: no.lon.toFixed(5) };
    lemumaDati(ll, no, signal);
    if (pludi) pluduDati(ll, signal);
    if (no.apraksts === 'no Jums') manaVietaDati(ll, signal);
    pasvaldibaDati(ll, no, signal);
    const vietas = h => { const d = kaste.querySelector('#rez-vietas'); if (d) d.innerHTML = h; };
    let neizdevas = false;  // /api/objekti neatbildēja — tad nesakām "datos nav", bet "neizdevās ielādēt"
    const tuvakas = (k, n) => iegut('/objekti?' + new URLSearchParams({ kategorijas: k, ...ll, limit: n }), signal)
      .catch(e => { if (e.name === 'AbortError') throw e; neizdevas = true; return { features: [] }; });
    try {
      const [grupas, drosasF] = await Promise.all([
        Promise.all(kodi.map(k => tuvakas(k, UZ_KATEGORIJU * 2))),
        Promise.all(drosas.map(d => kategorijas[d.kods]?.skaits ? tuvakas(d.kods, 5) : { features: [] })),
      ]);
      grupas.forEach(g => { g.features = izveleties(g.features); });
      const drosasVietas = drosasF.map(g => izveleties(g.features)[0] || null);
      const vejs = galvenais && VEJA_SCENARIJI.has(galvenais.kods);
      vietas((vejs ? vejaBloks() : '') + (laiks ? augsnesBloks() : '') + '<div id="rez-celi"></div><div id="rez-satiksme"></div>' +
        (neizdevas ? '<p class="piezime kluda">Daļu tuvāko vietu neizdevās ielādēt. Mēģiniet vēlreiz pēc brīža; padoms un 112 ir spēkā.</p>' : '') +
        kodi.map((k, i) => grupa(k, grupas[i].features, no, neizdevas)).join('') +
        (drosas.length && !neizdevas ? drosasBloks(drosas, drosasVietas, no) : '') +
        '<p class="piezime">Attālums taisnā līnijā ' + esc(no.apraksts) + '.</p>');
      zimetKarte([...grupas.map(g => g.features), ...drosasVietas.filter(Boolean).map(f => [f])], no, vieta);
      // Maršruts līdz tuvākajai patvertnei (citādi 24/7 slimnīcai), kas apiet spēkā esošus ceļu slēgumus (marsruts.js)
      const merkis = drosasVietas[drosas.findIndex(d => d.kods === 'patvertne')] || drosasVietas[drosas.findIndex(d => d.kods === 'neatliekama_24h')];
      if (merkis && !no.regions && typeof Marsruts !== 'undefined' && merkis.properties.attalums_m < 20000) {
        const [mlon, mlat] = merkis.geometry.coordinates;
        Marsruts.rindai(kaste.querySelector(`li[data-lat="${mlat}"][data-lon="${mlon}"]`), [no.lat, no.lon], [mlat, mlon],
          { slanis: rezultatuSlanis, signal });
      }
      if (laiks) augsnesDati(ll, signal);
      if (vejs) vejaDati(ll, signal);
      // celi.js: spēkā esošs ceļa slēgums vai negadījums ~5 km rādiusā — viena rinda; bez datiem nekā nerāda
      if (typeof Celi !== 'undefined') Celi.rinda(ll, signal).then(h => { const d = kaste.querySelector('#rez-celi'); if (d) d.innerHTML = h; }, () => {});
      // zonas.js: satiksme apvidū (LVC) un slidens ceļš tuvumā — rinda tikai tad, ja ir dati
      if (typeof Zonas !== 'undefined') Zonas.satiksmesRinda(ll).then(h => { const d = kaste.querySelector('#rez-satiksme'); if (d && !signal.aborted) d.innerHTML = h; }, () => {});
    } catch (e) {
      if (e.name !== 'AbortError') vietas('<p class="piezime kluda">Vietas neizdevās ielādēt. Mēģiniet vēlreiz pēc brīža.</p>');
    }
  }

  // "Kas notiks tālāk": kartītes noslēgums — ko darīt tagad, kas notiks, kur būs ziņas, kad meklēt vēlreiz
  function talakBloks(scenarijs) {
    const soli = Array.isArray(scenarijs?.talak) ? scenarijs.talak : talakGimenes[scenarijs?.talak] || talakGimenes._;
    if (!soli?.length) return '';
    return '<div class="talak"><h3>Kas notiks tālāk</h3><ol>' + soli.map(t => {
      const m = /^(Tagad|Tālāk):\s*/.exec(t);
      return '<li>' + (m ? `<b>${m[1]}:</b> ${esc(t.slice(m[0].length))}` : esc(t)) + '</li>';
    }).join('') + '</ol></div>';
  }

  // Specializētās slimnīcas (dzemdību nams, psihiatrija; ipasibas.specializeta) un simulētie prototipa punkti (avots sim-…,
  // piem. ūdens punkti blakus reālajiem OSM) pēc pārējiem, citādi pēc attāluma.
  const izveleties = features => features
    .map((f, i) => ({ f, i, spec: f.properties.ipasibas?.specializeta || /^sim-/.test(f.properties.avots || '') ? 1 : 0 }))
    .sort((a, b) => a.spec - b.spec || a.i - b.i).slice(0, UZ_KATEGORIJU).map(x => x.f);

  const notiritPoga = () => '<button type="button" class="otra" data-darbiba="notirit"><span aria-hidden="true">✕</span> Notīrīt meklēšanu</button>';

  function vienums(f, no, virsraksts) {
    // attālums no reģiona centra nav "no tevis", tāpēc uznirstošajā logā to nerādām
    const p = no.regions ? { ...f.properties, attalums_m: null } : f.properties;
    const i = p.ipasibas || {};
    const [lon, lat] = f.geometry.coordinates;
    const ca = (i.komentars ? `<small class="ca-avots">${esc(i.komentars)}</small>` : i.vietas ? `<small>${esc(i.vietas)} vietas</small>` :
      i.marsruti ? `<small>${esc(i.marsruti)} maršruti: ${esc(i.marsrutu_saraksts)}</small>` : '') +
      (/^https?:\/\//.test(i.plans_url || '') ? `<small><a href="${esc(i.plans_url)}" target="_blank" rel="noopener">Atvērt CA plānu${i.lpp ? ` (lpp. ${esc(i.lpp)})` : ''}</a></small>` : '');
    return `<li tabindex="0" data-lat="${lat}" data-lon="${lon}" data-p="${esc(JSON.stringify(p))}">
      <span class="teksts">${virsraksts || ''}${ObjektaStatuss.zime(p)}<b>${esc(nosaukums(p) || kategorijas[p.kategorija]?.nosaukums || '')}</b><small>${esc(p.adrese || '')}</small>${ca}${ObjektaStatuss.statuss(p, true)}${marsrutaSaites(lat, lon, no.regions ? null : no)}</span>
      <span class="attalums">${attalums(f.properties.attalums_m)}</span></li>`;
  }

  function grupa(kods, features, no, neizdevas = false) {
    const k = kategorijas[kods];
    if (!features.length) return neizdevas ? '' : `<p class="piezime">${esc(k.nosaukums)}: tuvākā vieta mūsu datos nav zināma.</p>`;
    return `<h3><span class="punkts" style="background:${esc(k.krasa)}"></span>${esc(k.nosaukums)}</h3>` +
      `<ol class="rez-saraksts">${features.map(f => vienums(f, no)).join('')}</ol>`;
  }

  // Tuvākā katrā drošo vietu kategorijā. Ja pašvaldības CA plānā vietu nav (vai slānis vēl nav ielādēts) — nekad
  // tukša rinda: norāde uz tuvāko patvertni (tā ir tajā pašā sarakstā).
  function drosasBloks(drosas, vietas, no) {
    const rindas = drosas.map((d, i) => {
      const virsraksts = `<span class="drosa-nos"><span aria-hidden="true">${d.ikona}</span> ${esc(d.nos)}</span>`;
      const f = vietas[i];
      if (f && d.aizstat && f.properties.attalums_m > 10000) {
        return vienums(f, no, virsraksts + '<small class="tala">Tuvākā mūsu datos ir tālu, citā pašvaldībā. Jautājiet savai pašvaldībai vai izmantojiet tuvāko patvertni.</small>');
      }
      if (f) return vienums(f, no, virsraksts);
      return `<li class="tuksa"><span class="teksts">${virsraksts}<small>${d.aizstat
        ? 'Šai vietai pašvaldības CA plānā mūsu datos vēl nav. Izmantojiet tuvāko patvertni.' : 'Datos nav atrasta. Jautājiet pašvaldībai.'}</small></span></li>`;
    }).join('');
    return `<h3>Drošās vietas tuvumā</h3><ol class="rez-saraksts drosas">${rindas}</ol>`;
  }

  // Lēmuma rinda: spēkā esošs LVĢMC brīdinājums šai vietai (poligonā) vai "nav"; neizdodas — rindu nerāda
  function lemumaDati(ll, no, signal) {
    iegut('/bridinajumi?' + new URLSearchParams(ll), signal).then(d => {
      const el = kaste.querySelector('#rez-lemums');
      if (!el) return;
      const kur = no.regions ? 'šajā apvidū' : 'šai vietai';
      const sie = (d.bridinajumi || []).filter(b => b.attiecas).sort((a, b) => b.limenis - a.limenis);
      const lidz = b => b.lidz ? ', līdz ' + new Date(b.lidz).toLocaleString('lv-LV', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' }) : '';
      el.innerHTML = (sie.length
        ? `<p class="lemums bridinajums-${esc(sie[0].krasa.toLowerCase())}"><span aria-hidden="true">⚠</span> <b>LVĢMC brīdinājums ${kur}:</b> ` +
          sie.map(b => `${esc(b.krasa)} — ${esc(b.paradiba)}${lidz(b)}`).join('; ') + '</p>'
        : `<p class="lemums lemums-nav"><b>LVĢMC brīdinājumu ${kur} nav.</b></p>`) +
        `<small class="avots-rinda">${AVOTI_LVGMC.bridinajumi}</small>`;
    }).catch(e => {
      const el = kaste.querySelector('#rez-lemums');
      if (!el || e.name === 'AbortError') return;
      el.innerHTML = '<p class="lemums lemums-nezinams"><b>LVĢMC brīdinājumus šobrīd neizdevās pārbaudīt.</b> ' +
        'Skatiet meteo.lv vai klausieties LR1.</p>';
    });
  }

  // Atrašanās vieta pēc GPS: tuvākā VZD adrese (≤ 300 m)
  function manaVietaDati(ll, signal) {
    iegut('/adreses/tuvaka?' + new URLSearchParams(ll), signal).then(a => {
      const el = kaste.querySelector('#rez-mana-vieta');
      if (!el || !a.adrese) return;
      el.textContent = `Jūsu atrašanās vieta: ~${isaAdrese(a.adrese)} (VZD adrešu reģistrs)`;
      el.hidden = false;
    }).catch(() => {});
  }

  // Pašvaldība: CA plāns, tīmekļvietne, pašvaldības tālrunis un e-pasts (UR, CC0) kā teksts — bez tel: saitēm;
  // VPVKAC centrs (2022) tikai tad, ja UR kontaktu nav
  function pasvaldibaDati(ll, no, signal) {
    iegut('/pasvaldiba?' + new URLSearchParams(ll), signal).then(p => {
      const el = kaste.querySelector('#rez-pasvaldiba');
      if (!el) return;
      const saite = (url, t) => /^https?:\/\//.test(url || '') ? ` · <a href="${esc(url)}" target="_blank" rel="noopener">${t}</a>` : '';
      const k = p.kontakti, c = k ? null : p.vpvkac;
      el.innerHTML = `<p class="pasvaldiba-rinda">${no.regions ? 'Pašvaldība' : 'Jūsu pašvaldība'}: <b>${esc(p.nosaukums)}</b>` +
        saite(p.ca_plans_url || p.ca_lapa, 'CA plāns') + saite(p.majas_lapa, 'tīmekļvietne') +
        (k?.talrunis ? ` · tālr. ${esc(k.talrunis.replace(/^\+371/, ''))}` : '') + (k?.epasts ? ` · ${esc(k.epasts)}` : '') +
        (c?.talrunis ? ` · VPVKAC ${esc(c.punkts)}: tālr. ${esc(c.talrunis)}` : '') + '</p>' +
        // abonēšana bez lietotnes: Atom plūsma un kalendārs šai pašvaldībai (karte_api.py /api/plusma.xml, /api/kalendars.ics)
        `<p class="abonet-rinda">Abonēt brīdinājumus: <a href="/api/plusma.xml?regions=${encodeURIComponent(p.kods)}" type="application/atom+xml">RSS</a>` +
        ` · <a href="/api/kalendars.ics?regions=${encodeURIComponent(p.kods)}">Kalendārs</a></p>` +
        `<small class="avots-rinda">Pašvaldību CA plāni (oficiāli dokumenti)` +
        (k ? ' · <a href="https://data.gov.lv/dati/dataset/public-persons-institutions" target="_blank" rel="noopener">Uzņēmumu reģistrs, publisko personu saraksts</a> · CC0' : '') +
        (c ? ' · <a href="https://data.gov.lv/dati/lv/dataset/vpvkac-kontakti" target="_blank" rel="noopener">VPVKAC kontaktpunkti</a>, 2022 · CC0' : '') + '</small>';
    }).catch(() => {});
  }

  // Plūdu scenārijiem: plūdu riska zona adresē (LVĢMC WMS caur /api/pludi; lēns, līdz 15 s) un tuvākās upes līmenis
  function pluduBloks() {
    return `<ul class="fakti" id="rez-pludi-bloks">
      <li id="rez-pludi"><span class="ikona" aria-hidden="true">🌊</span><div><b>Plūdu riska zona</b><span>Pārbauda… (līdz 15 s)</span></div></li>
      <li id="rez-udens"><span class="ikona" aria-hidden="true">📏</span><div><b>Tuvākā upe vai ezers</b><span>Ielādē…</span></div></li></ul>`;
  }
  function pluduRinda(id, saturs) { const li = kaste.querySelector('#' + id); if (li) li.querySelector('div').innerHTML = saturs; }
  function pluduDati(ll, signal) {
    pluduZona(ll, signal, 0);
    pluduUdens(ll, signal);
  }
  // /api/pludi atbild ne ilgāk par 25 s; ja LVĢMC karšu serviss vēl rēķina — 202 {ielade}: vēlreiz pēc 10 s (≤ 2 reizes)
  function pluduZona(ll, signal, meginajums) {
    iegut('/pludi?' + new URLSearchParams(ll), signal).then(p => {
      if (p.ielade) {
        pluduRinda('rez-pludi', `<b>Plūdu riska zona</b><span>${meginajums < 2 ? 'Plūdu kartes vēl ielādējas, mēģinām vēlreiz pēc 10 s…'
          : 'Plūdu kartes pašlaik atbild lēni. Plūdu zonas redzamas kartē (slānis ieslēgts).'}</span>`);
        if (meginajums < 2) setTimeout(() => { if (!signal.aborted) pluduZona(ll, signal, meginajums + 1); }, 10000);
        return;
      }
      const t = p.zona
        ? `<strong class="jā">Jā</strong>: ${p.veidi.map(v => `${esc(v.veids)} (${String(v.varbutiba_proc).replace('.', ',')} % varbūtība gadā)`).join(', ')}`
        : p.nepilnigi ? 'Pēc pieejamajām kartēm nē, bet daļa karšu neatbildēja.' : '<strong class="nē">Nē</strong>: nav applūstošā teritorijā (10 %, 1 % un 0,5 % kartes).';
      pluduRinda('rez-pludi', `<b>Plūdu riska zona</b><span>${t}</span><small class="avots-rinda">${AVOTI_LVGMC.pludi}</small>`);
    }).catch(e => {
      if (e.name !== 'AbortError') pluduRinda('rez-pludi', '<b>Plūdu riska zona</b><span>Neizdevās pārbaudīt. Plūdu zonas redzamas kartē (slānis ieslēgts).</span>');
    });
  }
  function pluduUdens(ll, signal) {
    iegut('/udens?' + new URLSearchParams({ ...ll, limit: 3 }), signal).then(d => {
      const s = d.stacijas[0];
      if (!s) throw new Error('nav');
      // prognoze: tuvākā no 3 stacijām, kurai LVĢMC to dod (prognoze ir ~35 no 74 stacijām)
      const ps = d.stacijas.find(x => x.prognoze);
      const pr = ps?.prognoze;
      const cm = v => (v < 0 ? '−' : '') + Math.abs(v);
      const prognoze = pr ? `<small>Prognoze ${pr.dienas} dienām${ps !== s ? ` (${esc(ps.nosaukums)}, ${attalums(ps.attalums_m)})` : ''}: ` +
        `<b>${esc(pr.virziens)}</b> (${pr.izmaina_cm > 0 ? '+' : ''}${cm(pr.izmaina_cm)} cm pēc modeļa)` +
        (pr.josla_50_cm ? `, līmenis ~${cm(pr.josla_50_cm[0])}…${cm(pr.josla_50_cm[1])} cm (50 % varbūtība)` : '') +
        `. <a href="https://data.gov.lv/dati/lv/dataset/hidrologiskas-prognozes" target="_blank" rel="noopener">LVĢMC hidroloģiskās prognozes</a> · CC0</small>` :
        '<small>LVĢMC ūdens līmeņa prognoze tuvākajām stacijām nav (to dod ~35 no 74 stacijām).</small>';
      const izm = s.izmaina_24h_cm;
      const tend = izm == null ? '' : izm > 0 ? `, 24 h: ↑ +${izm} cm` : izm < 0 ? `, 24 h: ↓ −${Math.abs(izm)} cm` : ', 24 h: nemainās';
      const laiks = new Date(s.laiks).toLocaleString('lv-LV', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' });
      pluduRinda('rez-udens', `<b>Tuvākā upe vai ezers</b><span>${esc(s.nosaukums)} (${attalums(s.attalums_m)}): ${s.limenis_cm} cm${tend}` +
        `${s.vecs ? ' — dati novecojuši' : ''}</span><small>Mērīts ${laiks}. Bīstamības līmeņi nav atvērtie dati.</small>${prognoze}<small class="avots-rinda">${AVOTI_LVGMC.udens}</small>`);
    }).catch(e => {
      if (e.name !== 'AbortError') pluduRinda('rez-udens', '<b>Tuvākā upe vai ezers</b><span>Ūdens līmeņa datus neizdevās ielādēt.</span>');
    });
  }

  // Vējš tagad tuvākajā LVĢMC stacijā (ar brāzmām)
  function vejaBloks() {
    return `<ul class="fakti"><li id="rez-vejs"><span class="ikona">💨</span><div><b>Vējš tagad</b><span>Ielādē…</span></div></li></ul>`;
  }
  function vejaDati(ll, signal) {
    iegut('/noverojumi?' + new URLSearchParams({ ...ll, limit: 8 }), signal).then(d => {
      const s = d.stacijas.find(x => x.brazmas != null && !x.vecs);
      if (!s) throw new Error('nav');
      const N = typeof Noverojumi !== 'undefined' ? Noverojumi : null;
      const sk = x => String(Math.abs(x) >= 10 ? Math.round(x) : (+x).toFixed(1)).replace('.', ',');
      pluduRinda('rez-vejs', `<b>Vējš tagad</b><span>${esc(s.nosaukums)} (${attalums(s.attalums_m)}): brāzmas <b>${sk(s.brazmas)} m/s</b>` +
        `${s.vejs != null ? `, vidēji ${sk(s.vejs)} m/s ${N ? N.virziens(s.virziens) : ''}` : ''}</span>` +
        `<small>Mērīts ${esc(new Date(s.laiks).toLocaleTimeString('lv-LV', { hour: '2-digit', minute: '2-digit' }))}. LVĢMC meteoroloģiskā stacija.</small>` +
        `<small class="avots-rinda"><a href="${esc(d.avots.url)}" target="_blank" rel="noopener">LVĢMC novērojumi</a> · ${esc(d.avots.licence)}</small>`);
    }).catch(e => {
      if (e.name !== 'AbortError') pluduRinda('rez-vejs', '<b>Vējš tagad</b><span>Tuvumā nav svaigu stacijas datu.</span>');
    });
  }

  // Nokrišņi pēdējās 26 dienās + augsnes mitrums: konteksts (cik ūdens zeme vēl var uzņemt), nevis brīdinājums
  function augsnesBloks() {
    return `<ul class="fakti"><li id="rez-augsne"><span class="ikona">🌧️</span><div><b>Nokrišņi un augsne</b><span>Ielādē…</span></div></li></ul>`;
  }
  function augsnesDati(ll, signal) {
    const avots = '<a href="https://open-meteo.com/" target="_blank" rel="noopener">Open-Meteo</a> · CC BY 4.0';
    iegut('/augsne?' + new URLSearchParams(ll), signal).then(a => {
      const mm = x => String(Math.round(x)).replace('.', ',');
      pluduRinda('rez-augsne', `<b>Nokrišņi un augsne</b><span>Pēdējās ${a.dienas_pagatne} dienās: ${mm(a.nokrisni_pagatne_mm)} mm nokrišņu` +
        `${a.augsne ? `; augsne ${esc(a.augsne)}` : ''}</span><small>Nākamajās ${a.dienas_prognoze} dienās: ${mm(a.nokrisni_prognoze_mm)} mm. ` +
        `Modeļa aprēķins šai vietai, nav brīdinājums.</small><small class="avots-rinda">${avots}</small>`);
    }).catch(e => {
      if (e.name !== 'AbortError') pluduRinda('rez-augsne', '<b>Nokrišņi un augsne</b><span>Datus neizdevās ielādēt.</span>');
    });
  }

  // Karti pietuvina sākumpunktam (un vaicājuma vietai) + tuvākajai vietai katrā kategorijā; tālākās (piem., 24/7
  // slimnīca citā novadā) tikai uzzīmē, citādi pilsēta paliek mazā stūrītī.
  function zimetKarte(grupas, no, vieta) {
    const punkti = [[no.lat, no.lon]];
    if (vieta) punkti.push([vieta.bbox[1], vieta.bbox[0]], [vieta.bbox[3], vieta.bbox[2]]);
    for (const g of grupas) if (g[0] && g[0].properties.attalums_m < 30000) punkti.push([...g[0].geometry.coordinates].reverse());
    for (const f of grupas.flat()) {
      const [lon, lat] = f.geometry.coordinates;
      const k = kategorijas[f.properties.kategorija] || {};
      L.circleMarker([lat, lon], { radius: 10, color: '#1c1917', weight: 2.5, fillColor: k.krasa || '#57534e', fillOpacity: 1 })
        .bindPopup(() => popupSaturs(no.regions ? { ...f.properties, attalums_m: null } : f.properties, { lat, lng: lon }))
        .addTo(rezultatuSlanis);
    }
    if (no.regions) L.circleMarker([no.lat, no.lon], { radius: 5, color: '#1c1917', weight: 2, fillOpacity: 0 })
      .bindTooltip('Attālumi no šejienes').addTo(rezultatuSlanis);
    // telefonā apakšā ir rezultātu lapa (apaksa.js): sākumpunkts un tuvākā vieta paliek redzami virs tās
    const apaksa = typeof Apaksa !== 'undefined' ? Apaksa.augstums() : 0;
    karte.fitBounds(L.latLngBounds(punkti), { paddingTopLeft: [40, 40], paddingBottomRight: [40, 40 + apaksa], maxZoom: 15 });
  }

  // Enter rezultātu sarakstā = klikšķis
  kaste.addEventListener('keydown', e => { if (e.key === 'Enter' && e.target.matches('li[data-lat]')) e.target.click(); });

  return { sakt, atkartot, meklet, vietaNav, labot, ieteikumi };
})();
