// "Kas Jums vajadzīgs?" (Ko tev vajag?): krīzes meklēšana — viens vaicājums ir gana. Teksts → scenārijs (klasifikators.js + scenariji.json,
// bez AI, pārlūkā) + vieta (adrese ar mājas numuru → VZD /api/adreses; vietvārds → reģions; citādi mana vieta).
// Rezultātā uzreiz: padoms, tuvākās vietas scenārija slāņos, drošās vietas (evakuācija, izmitināšana no CA plāniem,
// patvertne, 24/7 slimnīca), plūdu scenārijiem — plūdu riska zona un upes līmenis; LVĢMC brīdinājumu josla (bridinajumi.js).
// Lieto app.js globālos (karte, stavoklis, iegut…).
const krizesMeklesana = (() => {
  const UZ_KATEGORIJU = 3;
  // Drošās vietas: rāda situācijām un vietas/adreses vaicājumiem. Tukšai kategorijai — norāde uz patvertni.
  const DROSAS = [
    { kods: 'evakuacijas_punkts', nos: 'Evakuācijas pulcēšanās vieta', ikona: 'karogs', aizstat: true },
    { kods: 'izmitinasana', nos: 'Izmitināšanas vieta', ikona: 'maja', aizstat: true },
    { kods: 'patvertne', nos: 'Tuvākā patvertne', ikona: 'patvertne' },
    { kods: 'neatliekama_24h', nos: '24/7 neatliekamā palīdzība', ikona: 'slimnica' },
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
    // rezerves avots (Meteoalarm noteikumi: nosaukt LVĢMC, saite uz meteoalarm.org, atruna par kavēšanos)
    bridinajumiRezerves: 'LVĢMC brīdinājumi caur <a href="https://www.meteoalarm.org" target="_blank" rel="noopener">Meteoalarm (EUMETNET)</a> · CC BY 4.0. ' +
      'Iespējama kavēšanās; jaunākā informācija — <a href="https://www.meteoalarm.org" target="_blank" rel="noopener">www.meteoalarm.org</a>.',
  };
  // Kartītes rāmis RU/EN valodā (valoda.js); padomi paliek latviski. Atslēga = latviskais teksts.
  // Funkcijās ar savu mainīgo t (radioRinda, pluduZona) — Valoda.t.
  const t = (k, m) => typeof Valoda !== 'undefined' ? Valoda.t(k, m) : k;
  let klasifikators = null;
  let talakGimenes = {};        // scenariji.json talak_gimenes: "Kas notiks tālāk" soļi pa scenāriju ģimenēm
  let pedejais = null;          // { teksts, scenarijs } — atkārto, kad mainās atrašanās vieta vai reģions
  let konteksts = null;         // { kods, nosaukums, vieta, adrese } pēdējam rezultātam — zinot.js aizpilda ziņojumu ("tikai vienreiz")
  let pieprasijums = null;
  const rezultatuSlanis = L.layerGroup().addTo(karte);
  const kaste = el('rezultati');

  let bezDatiem = false;  // /api/kategorijas, /regioni vai /avoti neielādējās (app.js)

  // Soļu josla zem meklēšanas lauka: 1 Jautājums (raksta / tukšs) → 2 Atbilde (kartīte) → 3 Rīcība (maršruts, vieta,
  // ziņojums). Josla stāv virs rezultāta: datorā kreisajā kolonnā zem ievada (darbvirsma.js), telefonā cilnē Rezultāts (sheet.js).
  const soluJosla = document.createElement('ol');
  soluJosla.className = 'soli';
  soluJosla.setAttribute('aria-label', t('Soļi'));
  // data-t: valoda.js nomaina uzrakstus, kad mainās kartītes valoda (LV/RU/EN)
  soluJosla.innerHTML = ['Jautājums', 'Atbilde', 'Rīcība'].map((v, i) =>
    `<li data-solis="${i + 1}"><span class="solis-nr">${i + 1}</span> <span data-t="${v}">${t(v)}</span></li>`).join('');
  kaste.before(soluJosla);  // galvenē ir tikai lauks; soļi stāv virs rezultāta (telefonā sheet.js tos pārceļ cilnē)
  function solis(n) {
    for (const li of soluJosla.children) {
      const ir = +li.dataset.solis === n;
      li.classList.toggle('aktivs', ir);
      if (ir) li.setAttribute('aria-current', 'step'); else li.removeAttribute('aria-current');
    }
  }
  solis(1);
  el('jautajums').addEventListener('input', () => solis(1));
  // 3. solis: maršruta saite, vieta sarakstā, kartes logs ar maršrutu, "Ziņot" (arī galvenē), kad kartīte ir atvērta
  const RICIBA = '.marsruts a, li[data-lat], [data-darbiba="zinot"], [data-darbiba="saraksts"], [data-darbiba="pludu-zonas"]';
  document.addEventListener('click', e => {
    if (kaste.hidden || !e.target.closest) return;
    if (kaste.contains(e.target) ? e.target.closest(RICIBA) : e.target.closest('[data-darbiba="zinot"], .leaflet-popup .marsruts a')) solis(3);
  });

  // Simulētie prototipa dati (avots "sim-…", atseviski_dati/*.csv) īstā vaicājuma kartītē nerādās; tikai demo režīmā
  // (?demo=… vai atvērts demo panelis), un tur ar zīmi "SIMULĒTI DATI — prototips" (objekta-statuss.js).
  const demoRezims = () => new URLSearchParams(location.search).has('demo') || document.body.classList.contains('demo-aktivs');
  const simulets = f => /^sim-/.test(f?.properties?.avots || '');
  const tikaiSimuleti = k => (kategorijas[k]?.avoti || []).length > 0 && kategorijas[k].avoti.every(a => /^sim-/.test(a));

  async function sakt(regioniSaraksts, datiNav = false) {
    bezDatiem = datiNav;
    try {
      const noteikumi = await (await fetch('scenariji.json')).json();
      klasifikators = Klasifikators.izveidot(noteikumi, regioniSaraksts);
      izveidotIndeksu(noteikumi);
      talakGimenes = noteikumi.talak_gimenes || {};
    } catch {
      el('jautajums').disabled = true;
      el('jautajums').placeholder = t('Meklēšana nav pieejama');
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
    karte.closePopup();  // iepriekšējā rezultāta logs nepaliek vaļā (un nebīdās ārpus kartes) zem jaunās kartītes
    const teksts = el('jautajums').value.trim();
    if (teksts) { meklet(teksts); raditRezultatus(); } else notirit();
  });

  // Biežāk meklētais: tukšajā laukā ieklikšķinot — 3 populārākie atpazītie vaicājumi (/api/meklejumi/top, kešs 60 s).
  // Ja API nav pieejams vai atpazīto ir mazāk par 3 — papildina ar šiem piemēriem, lai nekad nav tukšs.
  // Saglabāto tekstu nerāda: "atpazits" apgalvo klients, tāpēc katru vaicājumu klasificē vēlreiz un rāda tikai
  // scenārija nosaukumu (+ vietu) no klasifikatora; neatpazītos vai tikai aptuveni atpazītos izmet.
  const POPULARI_REZERVE = ['nav elektrības', 'plūdi ogrē', 'tuvākā patvertne'];

  // Pirmais skats (pirms pirmās meklēšanas): ko rakstīt, 3 piemēri, kas uzreiz meklē, un rinda par datiem.
  // Datorā — kreisajā kolonnā (darbvirsma.js), pazūd pēc pirmās meklēšanas (atceras pārlūkā, body.ir-meklets);
  // telefonā — lapas tukšais stāvoklis virs tēmu pogām (sheet.js), redzams, kamēr nav rezultāta.
  const PIEMERI = [['Ogre, plūdi', 'pludi'], ['nav elektrības Rēzekne', 'zibens'], ['cilvēks nav pie samaņas', 'pleksteris']];
  const PIRMA_MEKLESANA = 'pirma-meklesana';
  try { if (localStorage.getItem(PIRMA_MEKLESANA)) document.body.classList.add('ir-meklets'); } catch { /* privātais režīms */ }
  function atzimetMekletu() {
    if (document.body.classList.contains('ir-meklets')) return;
    document.body.classList.add('ir-meklets');
    try { localStorage.setItem(PIRMA_MEKLESANA, '1'); } catch { /* privātais režīms */ }
  }
  const pirmaisSkats = (ievads = 'Uzrakstiet vienā rindā, kas notiek un kur: pilsēta, adrese ar mājas numuru vai „Rādīt tuvākos man”.') =>
    `<div class="pirmais-skats" role="group" aria-label="${t('Piemēri, kā meklēt')}"><p class="ps-ievads">${t(ievads)}</p>` +
    `<div class="ps-cipi">${PIEMERI.map(([q, ik]) => `<button type="button" class="ps-cips" data-piemers="${esc(q)}">${Ik(ik)}<span>${esc(q)}</span></button>`).join('')}</div>` +
    `<p class="ps-dati">${Ik('info')}<span>${t('Atbildi saliekam no atvērtajiem datiem: LVĢMC brīdinājumi un plūdu kartes, VZD adreses, pašvaldību civilās aizsardzības plāni, slimnīcas un patvertnes. Katrai rindai ir avots un licence.')}</span></p></div>`;
  document.addEventListener('click', e => {
    const q = e.target.closest('[data-piemers]')?.dataset.piemers;
    if (!q || el('jautajums').disabled) return;
    el('jautajums').value = q;
    el('meklet-forma').requestSubmit();
  });
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
    el('populari-virsraksts').textContent = t('Biežāk meklētais');
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
    if (rez.scenariji.length) return rez;
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
    if (darbiba === 'pludu-zonas') {  // kritisks upes līmenis: plūdu zonu slānis kartē; telefonā lapu nolaiž, lai karte redzama
      radtPludus(true);
      if (typeof Apaksa !== 'undefined' && Apaksa.aktiva()) Apaksa.atvert('peek');
      else if (matchMedia('(max-width: 800px)').matches) el('karte')?.scrollIntoView({ block: 'start' });
    }
    const cits = klasifikators?.scenariji.find(s => s.kods === e.target.closest('[data-cits]')?.dataset.cits);
    if (cits && pedejais) meklet(pedejais.teksts, cits);
    const li = e.target.closest('li[data-lat]');
    if (li && uzskaite && !uzskaite.klikskis) { uzskaite.klikskis = true; zinot(uzskaite.vaicajums, true); }
    if (li && !e.target.closest('a')) {
      const ll = { lat: +li.dataset.lat, lng: +li.dataset.lon };
      // bez animācijas: logs atveras uzreiz, un Leaflet automātiskā pārbīde rēķina pēc gala skata (animācijas laikā
      // tā logu atstāja zem galvenes un "Karte | Reljefs")
      karte.setView(ll, Math.max(karte.getZoom(), 16), { animate: false });
      L.popup().setLatLng(ll).setContent(popupSaturs(JSON.parse(li.dataset.p), ll)).openOn(karte);
    }
  });

  function notirit() {
    if (typeof Dalities !== 'undefined') Dalities.notiritUrl();
    pedejais = null;
    konteksts = null;
    uzskaite = null;
    if (pieprasijums) pieprasijums.abort();
    rezultatuSlanis.clearLayers();
    kaste.hidden = true;
    kaste.innerHTML = '';
    el('jautajums').value = '';
    bridinajumi(null);
    solis(1);
  }

  // Poga "Notīrīt" meklēšanas joslā: viss uz sākumu — lauks, rezultāts un apakšas lapa, piespiedu scenārijs,
  // atskaites punkts, visi URL parametri (?q, lat, lon, regions, demo), demo, scenārija ieslēgtie slāņi (sākumā slāņi izslēgti).
  const notiritPoga2 = el('notirit-meklesanu');
  const raditNotiritPogu = () => { notiritPoga2.hidden = !(el('jautajums').value || !kaste.hidden); };
  function notiritVisu() {
    if (typeof Demo !== 'undefined' && document.body.classList.contains('demo-aktivs')) Demo.beigt();
    notirit();
    aizvertPopularos();
    if (typeof Apaksa !== 'undefined' && Apaksa.aizvert) Apaksa.aizvert();
    stavoklis.vieta = null;
    if (vietasSlanis) { vietasSlanis.remove(); vietasSlanis = null; }
    if (typeof tuvakaSlanis !== 'undefined' && tuvakaSlanis) { tuvakaSlanis.remove(); tuvakaSlanis = null; }
    stavoklis.kategorijas = new Set();
    document.querySelectorAll('#kategorijas input').forEach(i => { i.checked = false; });
    // Visi pārklājuma slāņi (plūdi, zonas, zibens, laikapstākļi, ceļi, ziņojumi): izslēdz caur to pašu "change" klausītāju
    document.querySelectorAll('.kat.parklajums input:checked').forEach(i => {
      i.checked = false;
      i.dispatchEvent(new Event('change', { bubbles: true }));
    });
    // Reģiona filtrs uz "Visa Latvija", bet karti nepārvietojam (radtRegionu() pārvietotu skatu)
    stavoklis.regions = '';
    el('regions').value = '';
    if (typeof robezaSlanis !== 'undefined' && robezaSlanis) { robezaSlanis.remove(); robezaSlanis = null; }
    atjaunot();
    history.replaceState(null, '', location.pathname);
    raditNotiritPogu();
    // datorā pirmais skats (piemēri) atgriežas — citādi kreisā kolonna pēc notīrīšanas paliek tukša
    document.body.classList.remove('ir-meklets');
    try { localStorage.removeItem(PIRMA_MEKLESANA); } catch { /* privātais režīms */ }
    el('jautajums').focus();
  }
  notiritPoga2.addEventListener('click', notiritVisu);
  el('jautajums').addEventListener('input', raditNotiritPogu);
  new MutationObserver(raditNotiritPogu).observe(kaste, { attributes: true, attributeFilter: ['hidden'] });
  // Escape tukšā laukā = Notīrīt (ja atvērts "Biežāk meklētais", Escape vispirms aizver tikai to — formas klausītājs)
  el('jautajums').addEventListener('keydown', e => {
    if (e.key === 'Escape' && populari.hidden && !el('jautajums').value) { e.preventDefault(); notiritVisu(); }
  });

  function atkartot() {
    if (pedejais) meklet(pedejais.teksts, pedejais.scenarijs);
  }

  // app.js: atrašanās vietu neizdevās noteikt — paskaidrojam rezultātos, nevis tikai panelī zem tiem
  function vietaNav(liegta) {
    const zina = kaste.querySelector('.vieta-zina');
    if (!zina) return;
    zina.innerHTML = `<span class="kluda">${t(liegta ? 'Atrašanās vieta nav atļauta.' : 'Atrašanās vietu neizdevās noteikt.')}</span>
      ${t('vieta_nav', { x: esc(pedejais?.teksts || 'plūdi') })}`;
    zina.hidden = false;
  }

  // Kur meklēt: adrese vaicājumā → vietvārds vaicājumā (reģionu meklet() jau izvēlējās) → mana atrašanās vieta →
  // izvēlētais reģions. Reģionam ņem bbox centru.
  function izcelsme(vieta, adrese) {
    if (adrese) return { lat: adrese.lat, lon: adrese.lon, apraksts: `no adreses ${isaAdrese(adrese.adrese)}`, nosaukums: isaAdrese(adrese.adrese) };
    if (vieta) return { ...centrs(vieta), apraksts: `no centra (${vieta.nosaukums})`, regions: true, nosaukums: vieta.nosaukums };
    if (stavoklis.vieta?.noSaites) return { ...stavoklis.vieta, apraksts: 'no saitē norādītās vietas', nosaukums: t('Saitē norādītajā vietā') };
    if (stavoklis.vieta) return { ...stavoklis.vieta, apraksts: stavoklis.vieta.adrese ? `no adreses ${isaAdrese(stavoklis.vieta.adrese)}` : 'no Jums',
      nosaukums: stavoklis.vieta.adrese ? isaAdrese(stavoklis.vieta.adrese) : t('Jūsu vietā') };
    const r = regioni[stavoklis.regions];
    if (r) return { ...centrs(r), apraksts: `no centra (${r.nosaukums})`, regions: true, nosaukums: r.nosaukums };
    // Nav ne adreses, ne vietas, ne atrašanās vietas ("cilvēks nav pie samaņas", "redzu dronu"): tuvākās vietas no kartes
    // centra (nekad tikai padoms), kamēr lietotājs nenospiež "Izmantot manu atrašanās vietu"
    // Telefonā karte stiepjas zem apakšējās lapas: centrs = redzamās daļas (virs lapas) vidus, nevis konteinera vidus
    const izm = karte.getSize();
    const zem = typeof Apaksa !== 'undefined' && Apaksa.aktiva() ? Apaksa.atstarpes().paddingBottomRight[1] : 0;
    let c = karte.containerPointToLatLng([izm.x / 2, Math.max(0, izm.y - zem) / 2]);
    if (!latvija.contains(c)) c = latvija.getCenter();
    return { lat: c.lat, lon: c.lng, apraksts: 'no kartes centra', regions: true, kartesCentrs: true, nosaukums: t('Kartes centrā') };
  }
  // bridinajumi.js (josla augšā); ja tas neielādējās — bez joslas
  const bridinajumi = (v, n) => { if (typeof Bridinajumi !== 'undefined') Bridinajumi.atjaunot(v, n); };
  const centrs = r => ({ lat: (r.bbox[1] + r.bbox[3]) / 2, lon: (r.bbox[0] + r.bbox[2]) / 2 });

  // Adrese vaicājumā ir tad, ja tajā ir skaitlis (mājas numurs): "plūdi Brīvības 15 Ogre", "aptieka Rīgas iela 5 Cēsīs".
  // Mēģinām garākās vārdu virknes ap numuru (pirms tā ir scenārija vārdi); /api/adreses vajag, lai visi vārdi sakrīt.
  // Nav atrasta → { neatrasta: "Nekāda iela 99", atlikums } (kartītē to pasaka un rāda pēc vietvārda). Variantam jāsatur
  // ielas nosaukums (vārds pirms numura; pirms "iela" — vēl viens), un, ja vaicājumā ir vietvārds, adresei jābūt tajā:
  // citādi "Baznīcas iela 2, Cēsis" atrada Jūrmalu, "Nekāda iela 99, Ogre" — Brīvības ielu 99.
  const IELAS_VEIDI = /^(iela|iel\.?|gatve|prospekts|prosp\.?|bulvāris|bulv\.?|ceļš|šoseja|laukums|aleja|dambis|krastmala|līnija|šķērsiela)$/i;
  async function atrastAdresi(teksts, signal) {
    const vardi = teksts.replace(/[,;]+/g, ' ').trim().split(/\s+/);
    const nr = vardi.findIndex(v => /\d/.test(v));
    if (nr < 0) return null;
    const iela = nr === 0 ? 0 : nr - (nr > 1 && IELAS_VEIDI.test(vardi[nr - 1]) ? 2 : 1);  // ielas pirmais vārds
    const parejie = vardi.filter((x, i) => i < iela || i > nr).join(' ');
    const vieta = parejie && klasifikators.klasificet(parejie).vieta;  // ne no ielas vārdiem ("Rīgas iela" nav Rīga)
    const rb = vieta && regioni[vieta.kods]?.bbox;
    const vietaDer = a => !rb || (a.lon >= rb[0] - 0.05 && a.lon <= rb[2] + 0.05 && a.lat >= rb[1] - 0.05 && a.lat <= rb[3] + 0.05);
    const varianti = [];
    for (let no = 0; no <= iela; no++) for (let lidz = vardi.length; lidz > nr; lidz--) varianti.push(vardi.slice(no, lidz));
    varianti.sort((a, b) => b.length - a.length);
    const adreseTeksts = vardi.slice(iela, nr + 1).join(' ');
    for (const v of varianti.filter(v => v.length >= 2).slice(0, 6)) {
      try {
        const a = await iegut('/adreses?' + new URLSearchParams({ q: v.join(' '), limit: 1 }), signal);
        // atlikums: vaicājums bez adreses vārdiem — no tā nosaka situāciju ("Mednieku iela" nav medības)
        if (a.length && vietaDer(a[0])) {
          // VZD dod tuvāko numuru, ja šāda nav ("Rīgas iela 5" → "Rīgas iela 2"): kartītē to pasaka
          const numuri = a[0].adrese.split(', ')[0].toLowerCase().split(/\s+/);
          const cits = !numuri.includes(vardi[nr].toLowerCase()) && !numuri.some(n => vardi[nr].toLowerCase().startsWith(n + '-'));
          return { ...a[0], atlikums: vardi.filter(x => !v.includes(x)).join(' '), citsNumurs: cits ? adreseTeksts : null };
        }
      } catch (e) {
        if (e.name === 'AbortError') throw e;
        return null;  // adrešu meklēšana nav pieejama — turpinām ar vietvārdu / atrašanās vietu
      }
    }
    // "… iela 99" — skaidri adrese: sakām, ka nav atrasta; "zvanīju 112", "3 cilvēki" — nav adrese, klusējam kā līdz šim
    return IELAS_VEIDI.test(vardi[nr - 1] || '') ? { neatrasta: adreseTeksts, atlikums: parejie } : null;
  }

  // scenarijs: izvēlēts ar pogu ("Vai domāji…?") — tad tekstu izmanto tikai vietai un 112.
  async function meklet(teksts, scenarijs = null) {
    if (!klasifikators) return;
    atzimetMekletu();
    pedejais = { teksts, scenarijs };
    kaste.lang = typeof Valoda !== 'undefined' ? Valoda.noteikt(teksts) : 'lv';
    let rez = klasificetLabots(teksts);
    if (scenarijs) {
      rez.scenariji = [scenarijs];
      rez.zvanit112 = rez.dzivibas_draudi || !!scenarijs.zvanit112;
    }
    kaste.hidden = false;
    solis(2);
    rezultatuSlanis.clearLayers();
    if (pieprasijums) pieprasijums.abort();
    pieprasijums = new AbortController();
    const signal = pieprasijums.signal;

    // Dzīvības draudi — uzreiz, pirms jebkādas ielādes (teksts, bez pogām un saitēm)
    const draudi = rez.dzivibas_draudi
      ? '<p class="draudi">' + Ik('uzmanibu') + ' ' + t('Izklausās, ka apdraudēta dzīvība. Zvaniet 112 tūlīt: dispečers palīdzēs, ko darīt.') + '</p>' : '';
    const zvanitTeksts = !rez.dzivibas_draudi && rez.zvanit112 ? '<p class="zvanit-teksts">' + t('Ja apdraudēta dzīvība vai veselība, zvaniet 112.') + '</p>' : '';

    let adrese = null;
    if (/\d/.test(teksts)) {
      kaste.innerHTML = draudi + '<p class="piezime">' + t('Meklē adresi…') + '</p>';
      try { adrese = await atrastAdresi(teksts, signal); } catch { return; }  // atcelts ar jaunu meklēšanu
      if (adrese && !scenarijs) {
        const draudiBija = rez.dzivibas_draudi;
        rez = klasificetLabots(adrese.atlikums);
        rez.dzivibas_draudi ||= draudiBija;
        rez.zvanit112 ||= draudiBija;
      } else if (adrese?.neatrasta) rez.vieta = klasificetLabots(adrese.atlikums).vieta;  // ne no ielas vārdiem
    }
    // Adrese nav VZD reģistrā (vai atrasts cits numurs): kartītē skaidri pasakām, un vieta ir vietvārds / atrašanās vieta
    const neatrasta = adrese?.neatrasta || adrese?.citsNumurs;
    const adresesPiezime = !neatrasta ? '' : '<p class="piezime adrese-nav">' + (adrese.citsNumurs
      ? t('Adrese „{a}” VZD adrešu reģistrā nav atrasta; rādām atrasto: {x}.', { a: esc(neatrasta), x: esc(isaAdrese(adrese.adrese)) })
      : rez.vieta ? t('Adrese „{a}” VZD adrešu reģistrā nav atrasta; rādām pēc vietas: {x}.', { a: esc(neatrasta), x: esc(rez.vieta.nosaukums) })
        : t('Adrese „{a}” VZD adrešu reģistrā nav atrasta. Pārbaudiet adresi vai izmantojiet savu atrašanās vietu.', { a: esc(neatrasta) })) + '</p>';
    if (adrese?.neatrasta) adrese = null;

    // Vieta kartē: adrese (tad reģiona filtru noņemam) vai vietvārds vaicājumā ("lācis Ogrē") — vienmēr, arī ja
    // scenārijs nav atpazīts vai tam nav slāņu kartē.
    let jaunsRegions = false;
    if (adrese) {
      if (stavoklis.regions) { radtRegionu(''); jaunsRegions = true; }
      izveletiesAdresi(adrese, false);  // app.js: sākumpunkts, marķieris, atjauno karti
    } else if (rez.vieta) {
      if (typeof atmestAdresi === 'function') atmestAdresi();  // app.js: iepriekšējās adreses marķieris prom
      jaunsRegions = stavoklis.regions !== rez.vieta.kods;
      radtRegionu(rez.vieta.kods);
    }
    const vieta = adrese ? null : rez.vieta;
    const no = izcelsme(vieta, adrese);
    const centra = !!no.kartesCentrs;  // ne adreses, ne vietas: attālumi no kartes centra, brīdinājumi/prognoze šai vietai nav jēgpilni
    if (typeof Dalities !== 'undefined') Dalities.atjaunotUrl(teksts, centra ? null : no);  // adreses joslā ?q=…[&lat=&lon=], lai rezultātu var nosūtīt
    bridinajumi(centra ? null : no, centra ? null : no.nosaukums);

    const [galvenais, ...citi] = rez.scenariji;
    konteksts = { kods: galvenais?.kods || null, nosaukums: galvenais?.nosaukums || '', vieta: centra ? null : no, adrese: adrese?.adrese || null };
    if (!scenarijs) {  // "Vai domājāt" pogas atkārto to pašu tekstu — neskaitām otrreiz
      uzskaite = galvenais ? { vaicajums: adrese ? adrese.atlikums : teksts, klikskis: false } : null;
      if (uzskaite) zinot(uzskaite.vaicajums);
    }
    const kurTeksts = adrese ? isaAdrese(adrese.adrese) : vieta?.nosaukums;
    const pludi = galvenais && PLUDU_SCENARIJI.has(galvenais.kods);
    const zona = pludi && !centra;  // lēmums = plūdu riska zona jā/nē šai adresei / vietai
    // Nākamā darbība "Izmantot manu atrašanās vietu": attālumi nav no lietotāja (kartes vai pilsētas centrs) un GPS vēl nav
    const vajagVietu = !!no.regions && !stavoklis.vieta;
    // Secība (telefonā pirmais ekrāns): 112 (tikai dzīvības draudi) → lēmums + viena nākamā darbība → ko sapratām →
    // LVĢMC brīdinājums šai vietai → 24 h prognoze → fakti (plūdu zona, upe) → vietas → padoms → "Kas notiks tālāk"
    const galva = draudi + lemumaBloks(zona, no, vajagVietu) +
      (galvenais
        ? `<p class="sapratu">${t(galvenais.nr ? 'Situācija' : 'Meklēju')}: <b>${esc(galvenais.nosaukums)}</b>${kurTeksts ? ' · ' + esc(kurTeksts) : ''}</p>`
        : kurTeksts ? `<p class="sapratu">${t(adrese ? 'Adrese' : 'Vieta')}: <b>${esc(kurTeksts)}</b></p>` +
            '<p class="piezime">' + t('Uzrakstiet arī, kas notiek, piem., „plūdi”, „nav elektrības”, „evakuācija”.') + '</p>' : '') +
      adresesPiezime + zvanitTeksts +
      (centra ? '' : '<div id="rez-lemums"></div><div id="rez-prognoze"></div>' + (pludi ? pluduBloks() : '')) +
      (no.regions ? '' : '<p class="piezime" id="rez-mana-vieta" hidden></p>') +
      (bezDatiem ? '<p class="piezime kluda">' + t('Kartes dati pašlaik nav pieejami: tuvākās vietas nevaram parādīt. Padoms un 112 ir spēkā.') + '</p>' : '');
    const padoms = galvenais?.padoms ? (typeof Valoda !== 'undefined' ? Valoda.padomiPiezime() : '') +
      `<p class="padoms" lang="lv">${esc(galvenais.padoms)}${padomuAvots(galvenais.padomu_avots)}</p>` : '';
    const vaiDomaji = citi.length ? `<p class="piezime">${t('Vai domājāt:')}</p><div class="atras-pogas">` +
      citi.map(s => `<button type="button" data-cits="${esc(s.kods)}">${esc(s.nosaukums)}</button>`).join('') + '</div>' : '';
    const beigas = talakBloks(galvenais, no) + vaiDomaji +
      '<button type="button" class="otra" data-darbiba="saraksts">' + Ik('saraksts') + ' ' + t('Visi kartes objekti sarakstā') + '</button>' +
      '<button type="button" class="otra" data-darbiba="zinot">' + Ik('zinot') + ' ' + t('Ziņot par bīstamību šeit') + '</button>' +
      (typeof Dalities !== 'undefined' ? Dalities.pogas() : '') + notiritPoga();

    // Nekas nav atpazīts: ne situācija, ne vieta
    if (!galvenais && !kurTeksts) {
      if (jaunsRegions) atjaunot();
      kaste.innerHTML = draudi + adresesPiezime + `<p class="piezime">${t('nesapratam')}</p>` + (draudi ? '' : '<p class="zvanit-teksts">' + t('Ja apdraudēta dzīvība vai veselība, zvaniet 112.') + '</p>') + notiritPoga();
      return;
    }

    // Scenārija slāņi (kas jau ir kartē) + drošās vietas situācijām un vietas/adreses vaicājumiem.
    // Slānis tikai ar simulētiem datiem (uzlādes punkti) īstā vaicājumā netiek ne ieslēgts, ne rādīts kartītē.
    const demo = demoRezims();
    const kodi = (galvenais?.kategorijas || []).filter(k => kategorijas[k]?.skaits && (demo || !tikaiSimuleti(k)));
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

    kaste.innerHTML = galva + '<div id="rez-vietas"><p class="piezime">' + t('Meklē tuvākās vietas…') + '</p></div>' + padoms +
      (centra ? '' : '<div id="rez-pasvaldiba"></div>') + beigas;
    const ll = { lat: no.lat.toFixed(5), lon: no.lon.toFixed(5) };
    if (!centra) {
      lemumaDati(ll, no, signal);
      prognozesDati(ll, no, signal);
      if (pludi) pluduDati(ll, signal);
      pasvaldibaDati(ll, no, signal);
    }
    if (no.apraksts === 'no Jums') manaVietaDati(ll, signal);
    const vietas = h => { const d = kaste.querySelector('#rez-vietas'); if (d) d.innerHTML = h; };
    let neizdevas = false;  // /api/objekti neatbildēja — tad nesakām "datos nav", bet "neizdevās ielādēt"
    const tuvakas = (k, n, papildus = {}) => iegut('/objekti?' + new URLSearchParams({ kategorijas: k, ...ll, limit: n, ...papildus }), signal)
      .then(d => demo ? d : { ...d, features: (d.features || []).filter(f => !simulets(f)) })
      .catch(e => { if (e.name === 'AbortError') throw e; neizdevas = true; return { features: [] }; });
    try {
      // Bankomāti (nav elektrības, skaidra nauda…): vispirms tuvākais kritiskais (banku saraksts — strādā arī krīzē)
      const atmI = kodi.indexOf('bankomats');
      const [grupas, drosasF, kritiskais] = await Promise.all([
        Promise.all(kodi.map(k => tuvakas(k, UZ_KATEGORIJU * 2))),
        Promise.all(drosas.map(d => kategorijas[d.kods]?.skaits ? tuvakas(d.kods, 5) : { features: [] })),
        atmI >= 0 ? tuvakas('bankomats', 3, { kritiskais: 1 }) : { features: [] },
      ]);
      // Dzīvais statuss: slēgtu / nedarbojošos / pilnu vietu izlaiž un ņem nākamo (izlaistās — viena rinda virs saraksta)
      const izlaisti = grupas.map(g => { const a = atlasit(g.features); g.features = izveleties(a.derigi); return a.izlaisti; });
      const kritiskie = atlasit(kritiskais.features);
      const kf = kritiskie.derigi[0];
      if (atmI >= 0) {
        if (kf) grupas[atmI].features = [kf, ...grupas[atmI].features.filter(f => f.id !== kf.id)].slice(0, UZ_KATEGORIJU);
        const zinami = new Set(izlaisti[atmI].map(x => x.f.id));
        izlaisti[atmI].push(...kritiskie.izlaisti.filter(x => !zinami.has(x.f.id) && (!kf || x.f.properties.attalums_m <= kf.properties.attalums_m)));
      }
      const drosasAtl = drosasF.map(g => atlasit(g.features));
      const drosasVietas = drosasAtl.map(a => izveleties(a.derigi)[0] || null);
      const drosasIzlaisti = drosasAtl.map((a, i) => a.izlaisti.filter(x => !drosasVietas[i] || x.f.properties.attalums_m <= drosasVietas[i].properties.attalums_m));
      const vejs = !centra && galvenais && VEJA_SCENARIJI.has(galvenais.kods);
      const arLaiku = laiks && !centra;
      vietas((vejs ? vejaBloks() : '') + (arLaiku ? augsnesBloks() : '') + (centra ? '' : '<div id="rez-celi"></div><div id="rez-satiksme"></div>') +
        (neizdevas ? '<p class="piezime kluda">' + t('Daļu tuvāko vietu neizdevās ielādēt. Mēģiniet vēlreiz pēc brīža; padoms un 112 ir spēkā.') + '</p>' : '') +
        kodi.map((k, i) => grupa(k, grupas[i].features, no, neizdevas, izlaisti[i])).join('') +
        (drosas.length && !neizdevas ? drosasBloks(drosas, drosasVietas, no, drosasIzlaisti) : '') +
        '<p class="piezime">' + t('Attālums taisnā līnijā') + (kaste.lang === 'en' || kaste.lang === 'ru' ? (no.regions ? ' ' + aprakstsT(no) : '') : ' ' + esc(no.apraksts)) + '.</p>');
      zimetKarte([...grupas.map(g => g.features), ...drosasVietas.filter(Boolean).map(f => [f])], no, vieta);
      aizpilditLemumu(lemumaVieta(kodi, grupas, drosas, drosasVietas, rez.dzivibas_draudi), no, zona, galvenais);
      // Maršruts līdz tuvākajai patvertnei (citādi 24/7 slimnīcai), kas apiet spēkā esošus ceļu slēgumus (marsruts.js)
      const merkis = drosasVietas[drosas.findIndex(d => d.kods === 'patvertne')] || drosasVietas[drosas.findIndex(d => d.kods === 'neatliekama_24h')];
      if (merkis && !no.regions && typeof Marsruts !== 'undefined' && merkis.properties.attalums_m < 20000) {
        const [mlon, mlat] = merkis.geometry.coordinates;
        Marsruts.rindai(kaste.querySelector(`li[data-lat="${mlat}"][data-lon="${mlon}"]`), [no.lat, no.lon], [mlat, mlon],
          { slanis: rezultatuSlanis, signal });
      }
      if (arLaiku) augsnesDati(ll, signal);
      if (vejs) vejaDati(ll, signal);
      // celi.js: spēkā esošs ceļa slēgums vai negadījums ~5 km rādiusā — viena rinda; bez datiem nekā nerāda
      if (!centra && typeof Celi !== 'undefined') Celi.rinda(ll, signal).then(h => { const d = kaste.querySelector('#rez-celi'); if (d) d.innerHTML = h; }, () => {});
      // zonas.js: satiksme apvidū (LVC) un slidens ceļš tuvumā — rinda tikai tad, ja ir dati
      if (!centra && typeof Zonas !== 'undefined') Zonas.satiksmesRinda(ll).then(h => { const d = kaste.querySelector('#rez-satiksme'); if (d && !signal.aborted) d.innerHTML = h; }, () => {});
    } catch (e) {
      if (e.name === 'AbortError') return;
      vietas('<p class="piezime kluda">' + t('Vietas neizdevās ielādēt. Mēģiniet vēlreiz pēc brīža.') + '</p>');
      aizpilditLemumu(null, no, zona, galvenais);
    }
  }

  // Padoma oficiālais avots (scenariji.json padomu_avots): maza saite zem padoma teksta
  const PADOMU_AVOTI = { 'vugd.gov.lv': 'VUGD', 'sargs.lv': 'Aizsardzības ministrija, „Kā rīkoties krīzes gadījumā”', 'lsm.lv': 'LSM (Gaso skaidrojums)' };
  function padomuAvots(url) {
    if (!url) return '';
    let nos = 'oficiālā vietne';
    try { const h = new URL(url).hostname.replace(/^www\./, ''); nos = PADOMU_AVOTI[h] || h; } catch { return ''; }
    return `<small class="avots-rinda padoma-avots">${t('Avots')}: <a href="${esc(url)}" target="_blank" rel="noopener">${esc(nos)}</a></small>`;
  }

  // ---- Lēmuma bloks kartītes augšā (telefonā redzams pusatvērtā lapā bez ritināšanas) ----
  // Viena rinda ar lēmumu (ikona + krāsa) un viena nākamā darbība. Plūdiem lēmums = plūdu riska zona jā/nē, darbība =
  // maršruts uz tuvāko pulcēšanās vietu; citādi lēmums = tuvākā vajadzīgā vieta, darbība = maršruts. Ja attālumi nav no
  // lietotāja (kartes vai pilsētas centrs), darbība = "Izmantot manu atrašanās vietu".
  const VIETAS = {
    evakuacijas_punkts: ['Tuvākā pulcēšanās vieta', 'karogs'], izmitinasana: ['Tuvākā izmitināšanas vieta', 'maja'],
    patvertne: ['Tuvākā patvertne', 'patvertne'], neatliekama_24h: ['Tuvākā 24/7 neatliekamā palīdzība', 'slimnica'],
    slimnica: ['Tuvākā ārstniecības iestāde', 'slimnica'], aptieka: ['Tuvākā aptieka', 'zales'], bankomats: ['Tuvākais bankomāts', 'nauda'],
    policija: ['Tuvākā policija', 'policija'], ugunsdzeseji: ['Tuvākais ugunsdzēsēju depo', 'vugd'], degviela: ['Tuvākā degvielas uzpilde', 'degviela'],
    noturibas_punkts: ['Tuvākais noturības punkta kandidāts', 'eka'], pietura: ['Tuvākā pietura', 'autobuss'],
  };
  const vietasVards = kods => { const [v, ik] = VIETAS[kods] || ['Tuvākā vieta', 'vieta']; return [t(v), ik]; };
  const vietasPoga = () => `<button type="button" class="galvena vietas-poga" data-darbiba="atrast">${Ik('vieta')} ${t('Izmantot manu atrašanās vietu')}</button>`;
  // Attāluma izcelsme kartītes valodā: "no kartes centra", "no centra (Ogre)"; citādi (adrese, Jūs) kā izcelsme() to deva
  const aprakstsT = no => no.kartesCentrs ? t('no kartes centra') : no.regions ? t('no centra ({x})', { x: esc(no.nosaukums) }) : esc(no.apraksts);
  const lemumaRinda = (tonis, ikona, virsraksts, teksts, piezime = '') =>
    `<p class="lemums-rinda lemums-${tonis}"><span class="lemums-ikona">${Ik(ikona)}</span>` +
    `<span class="lemums-teksts"><b>${virsraksts}:</b> ${teksts}${piezime ? ` <small>${piezime}</small>` : ''}</span></p>`;
  const pirmaisTeikums = s => String(s || '').split(/(?<=[.!?])\s/)[0];

  function lemumaBloks(zona, no, vajagVietu) {
    const kur = no.regions ? t('{x}, centrs', { x: esc(no.nosaukums) }) : '';
    const rinda = zona ? lemumaRinda('gaida', 'pludi', t('Plūdu riska zona'), t('pārbauda…'), kur)
      : lemumaRinda('gaida', 'vieta', t('Tuvākā vieta'), t('meklē…'));
    return `<section class="lemums-bloks" id="rez-galvenais" aria-label="${t('Lēmums')}">` +
      `<div id="rez-lemuma-rinda"${zona ? ` data-kur="${kur}"` : ''}>${rinda}</div>` +
      `<div id="rez-darbiba" class="lemums-darbiba">${vajagVietu ? vietasPoga() : ''}</div>` +
      (vajagVietu ? '<p class="piezime vieta-zina" hidden></p>' : '') + '</section>';
  }

  // Lēmuma vieta: dzīvības draudos — 24/7 neatliekamā palīdzība; citādi pirmā scenārija slānī, tad drošās vietas.
  // Upju stacijas nav vieta, kurp doties; CA plāna vieta > 10 km (citā pašvaldībā) — ņem nākamo (patvertni).
  function lemumaVieta(kodi, grupas, drosas, drosasVietas, draudi) {
    const visi = [...kodi.map((k, i) => ({ kods: k, f: grupas[i].features[0] })), ...drosas.map((d, i) => ({ kods: d.kods, f: drosasVietas[i] }))]
      .filter(x => x.f && x.kods !== 'udens_limenis' &&
        !(['evakuacijas_punkts', 'izmitinasana'].includes(x.kods) && x.f.properties.attalums_m > 10000));
    return (draudi && visi.find(x => x.kods === 'neatliekama_24h')) || visi[0] || null;
  }

  function aizpilditLemumu(x, no, zona, galvenais) {
    const rinda = kaste.querySelector('#rez-lemuma-rinda'), darbiba = kaste.querySelector('#rez-darbiba');
    if (!rinda || !darbiba) return;
    if (!x) {
      // padoms ir latviski (oficiālais avots) arī RU/EN kartītē
      const pt = pirmaisTeikums(galvenais?.padoms);
      if (!zona) rinda.innerHTML = lemumaRinda('info', 'info', t('Ko darīt'),
        pt ? `<span lang="lv">${esc(pt)}</span>` : t('Ja apdraudēta dzīvība vai veselība, zvaniet 112.'));
      return;
    }
    const p = x.f.properties;
    const [vards, ikona] = vietasVards(x.kods);
    const nos = esc(nosaukums(p) || kategorijas[x.kods]?.nosaukums || '');
    const att = attalums(p.attalums_m) + (no.regions ? ` <small>${aprakstsT(no)}</small>` : '');
    if (!zona) rinda.innerHTML = lemumaRinda('vieta', ikona, vards, `<b class="lemums-vietas-nos">${nos}</b> · ${att}`);
    const vietasRinda = zona ? `<p class="lemums-vietas-rinda">${Ik(ikona)} ${vards}: <b>${nos}</b> · ${att}</p>` : '';
    const poga = darbiba.querySelector('[data-darbiba="atrast"]');
    if (poga) { if (vietasRinda) poga.insertAdjacentHTML('beforebegin', vietasRinda); return; }
    const [lon, lat] = x.f.geometry.coordinates;
    darbiba.innerHTML = vietasRinda + marsrutaSaites(lat, lon, no.regions ? null : no);
  }

  // Plūdu lēmums: zona (/api/pludi) × upes statuss (/api/udens); pārzīmē, kad pienāk katra no atbildēm
  function zimetPluduLemumu() {
    const r = kaste.querySelector('#rez-lemuma-rinda[data-kur]');
    const z = pluduStavoklis.lemums;
    if (!r || !z) return;
    const s = pluduStavoklis.stacija;
    const kritisks = s?.statuss === 'kritisks';
    r.innerHTML = lemumaRinda(kritisks && z.tonis !== 'ne' ? 'ja' : z.tonis, 'pludi', t('Plūdu riska zona'), z.teksts +
      (kritisks ? ` · <b>${t('upe virs kritiskā līmeņa')}</b>` : ''), r.dataset.kur);
  }

  // "Kas notiks tālāk": kartītes noslēgums — ko darīt tagad, kas notiks, kur būs ziņas, kad meklēt vēlreiz
  // LR1 raidītāji (production/lr1.json, src/info/radio_karte.py): "Radio krīzē" rinda ar tuvākā raidītāja frekvenci
  let lr1 = null;
  fetch('lr1.json').then(r => r.ok ? r.json() : null).then(d => { lr1 = d; }).catch(() => {});
  function radioRinda(no) {
    const saite = `<a href="info.html#b-radio">${Valoda.t('visas frekvences')}</a>`;
    if (!lr1?.raiditaji?.length || no?.lat == null) return `<li><b>${Valoda.t('Radio krīzē')}:</b> Latvijas Radio 1 · ${saite}</li>`;
    const km = s => {
      const f1 = no.lat * Math.PI / 180, f2 = s.lat * Math.PI / 180;
      const a = Math.sin((f2 - f1) / 2) ** 2 + Math.cos(f1) * Math.cos(f2) * Math.sin((s.lon - no.lon) * Math.PI / 360) ** 2;
      return 12742 * Math.asin(Math.sqrt(a));
    };
    const t = lr1.raiditaji.map(s => ({ s, d: km(s) })).sort((a, b) => a.d - b.d)[0];
    const fr = t.s.lr1.map(f => f.replace('.', ',')).join(' vai ');
    return `<li><b>${Valoda.t('Radio krīzē')}:</b> LR1 ${esc(fr)} FM (tuvākais raidītājs: ${esc(t.s.vieta)}, ~${Math.round(t.d)} km) · ${saite}</li>`;
  }

  function talakBloks(scenarijs, no) {
    const soli = Array.isArray(scenarijs?.talak) ? scenarijs.talak : talakGimenes[scenarijs?.talak] || talakGimenes._;
    if (!soli?.length) return '';
    return '<div class="talak"><h3>' + t('Kas notiks tālāk') + '</h3>' + (typeof Valoda !== 'undefined' ? Valoda.padomiPiezime() : '') + '<ol lang="lv">' + soli.map(t => {
      const m = /^(Tagad|Tālāk):\s*/.exec(t);
      return '<li>' + (m ? `<b>${m[1]}:</b> ${esc(t.slice(m[0].length))}` : esc(t)) + '</li>';
    }).join('') + radioRinda(no) + '</ol></div>';
  }

  // Specializētās slimnīcas (dzemdību nams, psihiatrija; ipasibas.specializeta) un simulētie prototipa punkti (avots sim-…,
  // piem. ūdens punkti blakus reālajiem OSM) pēc pārējiem, citādi pēc attāluma.
  const izveleties = features => features
    .map((f, i) => ({ f, i, spec: f.properties.ipasibas?.specializeta || /^sim-/.test(f.properties.avots || '') ? 1 : 0 }))
    .sort((a, b) => a.spec - b.spec || a.i - b.i).slice(0, UZ_KATEGORIJU).map(x => x.f);

  // Dzīvais statuss (ObjektaStatuss.nepieejams): {derigi, izlaisti: [{f, iemesls}]}. Izlaistas tikai tās, kas ir tuvāk par
  // pēdējo derīgo, ko rādām (tālākas nevienu neinteresē). "nav zināms" un vecs statuss — derīga vieta.
  function atlasit(features) {
    const derigi = [], izlaisti = [];
    for (const f of features) {
      const iemesls = ObjektaStatuss.nepieejams(f.properties);
      if (iemesls) { if (derigi.length < UZ_KATEGORIJU) izlaisti.push({ f, iemesls }); } else derigi.push(f);
    }
    return { derigi, izlaisti };
  }
  // "Tuvākais (Swedbank, Rīgas iela 1) izlaists: nedarbojas." — viena rinda; vairākām — "Tuvākie (…; …) izlaisti: …"
  function izlaistiRinda(izlaisti) {
    if (!izlaisti?.length) return '';
    const vards = x => esc(nosaukums(x.f.properties) || kategorijas[x.f.properties.kategorija]?.nosaukums || 'vieta') +
      (x.f.properties.adrese ? ', ' + esc(x.f.properties.adrese) : '');
    const iemesli = [...new Set(izlaisti.map(x => x.iemesls))].join(' / ');
    const v = izlaisti.slice(0, 2).map(vards).join('; ') + (izlaisti.length > 2 ? `; +${izlaisti.length - 2}` : '');
    return `<small class="izlaists">${Ik('uzmanibu')} ${izlaisti.length > 1 ? 'Tuvākie' : 'Tuvākais'} (${v}) ${izlaisti.length > 1 ? 'izlaisti' : 'izlaists'}: ${esc(iemesli)} (dzīvais statuss).</small>`;
  }

  const notiritPoga = () => '<button type="button" class="otra" data-darbiba="notirit">' + Ik('aizvert') + ' ' + t('Notīrīt meklēšanu') + '</button>';

  function vienums(f, no, virsraksts) {
    // attālums no reģiona centra nav "no tevis", tāpēc uznirstošajā logā to nerādām
    const p = no.regions ? { ...f.properties, attalums_m: null } : f.properties;
    const i = p.ipasibas || {};
    const [lon, lat] = f.geometry.coordinates;
    // Pulcēšanās un izmitināšanas vietas (avots ca-plani) izvilka MI no pašvaldību CA plāniem: zīme ar saiti uz plāna lappusi
    const plans = /^https?:\/\//.test(i.plans_url || '') ? esc(i.plans_url) + (i.lpp ? '#page=' + encodeURIComponent(i.lpp) : '') : '';
    const ca = (i.komentars ? `<small class="ca-avots">${esc(i.komentars)}</small>` : i.vietas ? `<small>${esc(i.vietas)} vietas</small>` :
      i.marsruti ? `<small>${esc(i.marsruti)} maršruti: ${esc(i.marsrutu_saraksts)}</small>` : '') +
      (plans && p.avots === 'ca-plani'
        ? `<small class="mi-zime">${Ik('dokuments')} ${t('izvilkts ar MI no CA plāna')}, <a href="${plans}" target="_blank" rel="noopener">${i.lpp ? t('{x}. lpp.', { x: esc(i.lpp) }) : t('atvērt plānu')}</a></small>`
        : plans ? `<small><a href="${plans}" target="_blank" rel="noopener">${t('Atvērt CA plānu')}${i.lpp ? ` (${t('{x}. lpp.', { x: esc(i.lpp) })})` : ''}</a></small>` : '') +
      // avots un licence katrai vietai (CA plāna vietām avots jau ir komentārā ar lappusi)
      (p.avots === 'ca-plani' && i.komentars ? '' : Avoti.rinda(p.avots));
    return `<li tabindex="0" data-lat="${lat}" data-lon="${lon}" data-p="${esc(JSON.stringify(p))}">
      <span class="teksts">${virsraksts || ''}${ObjektaStatuss.zime(p)}<b>${esc(nosaukums(p) || kategorijas[p.kategorija]?.nosaukums || '')}</b><small>${esc(p.adrese || '')}</small>${ca}${ObjektaStatuss.statusaBloks(p, true)}${marsrutaSaites(lat, lon, no.regions ? null : no)}</span>
      <span class="attalums">${attalums(f.properties.attalums_m)}</span></li>`;
  }

  function grupa(kods, features, no, neizdevas = false, izlaisti = []) {
    const k = kategorijas[kods];
    if (!features.length) return neizdevas ? '' : `<p class="piezime">${esc(k.nosaukums)}: tuvākā ${izlaisti.length ? 'strādājošā ' : ''}vieta mūsu datos nav zināma.</p>${izlaistiRinda(izlaisti)}`;
    return `<h3>${Ikonas.formaHTML(kods)}${esc(k.nosaukums)}</h3>` + izlaistiRinda(izlaisti) +
      `<ol class="rez-saraksts">${features.map(f => vienums(f, no, f.properties.ipasibas?.kritiskais === '1'
        ? '<span class="krit-zime">KRITISKAIS</span> <small>skaidra nauda arī krīzes laikā</small><br>' : '')).join('')}</ol>`;
  }

  // Tuvākā katrā drošo vietu kategorijā. Ja pašvaldības CA plānā vietu nav (vai slānis vēl nav ielādēts) — nekad
  // tukša rinda: norāde uz tuvāko patvertni (tā ir tajā pašā sarakstā).
  function drosasBloks(drosas, vietas, no, izlaisti = []) {
    const rindas = drosas.map((d, i) => {
      const virsraksts = `<span class="drosa-nos">${Ik(d.ikona)} ${esc(t(d.nos))}</span>` + izlaistiRinda(izlaisti[i]);
      const f = vietas[i];
      if (f && d.aizstat && f.properties.attalums_m > 10000) {
        return vienums(f, no, virsraksts + '<small class="tala">' + t('Tuvākā mūsu datos ir tālu, citā pašvaldībā. Jautājiet savai pašvaldībai vai izmantojiet tuvāko patvertni.') + '</small>');
      }
      if (f) return vienums(f, no, virsraksts);
      return `<li class="tuksa"><span class="teksts">${virsraksts}<small>${t(d.aizstat
        ? 'Šai vietai pašvaldības CA plānā mūsu datos vēl nav. Izmantojiet tuvāko patvertni.' : 'Datos nav atrasta. Jautājiet pašvaldībai.')}</small></span></li>`;
    }).join('');
    return `<h3>${t('Drošās vietas tuvumā')}</h3><ol class="rez-saraksts drosas">${rindas}</ol>`;
  }

  // Lēmuma rinda: spēkā esošs LVĢMC brīdinājums šai vietai (poligonā) vai "nav"; neizdodas — rindu nerāda
  function lemumaDati(ll, no, signal) {
    iegut('/bridinajumi?' + new URLSearchParams(ll), signal).then(d => {
      const el = kaste.querySelector('#rez-lemums');
      if (!el) return;
      const kur = t(no.regions ? 'šajā apvidū' : 'šai vietai');
      // rezerves avots (Meteoalarm, d.rezerves): vieta pārbaudīta pēc pašvaldības; attiecas null — nav zināms, rāda
      const rez = !!d.rezerves;
      const sie = (d.bridinajumi || []).filter(b => rez ? b.attiecas !== false : b.attiecas).sort((a, b) => b.limenis - a.limenis);
      const fmt = iso => new Date(iso).toLocaleString('lv-LV', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' });
      const lidz = b => (b.lidz ? ', līdz ' + fmt(b.lidz) : '') + (rez && b.izdots ? ` (izdots ${fmt(b.izdots)})` : '');
      const piezime = rez ? ' <small class="rezerves">rezerves avots: Meteoalarm</small>' : '';
      el.innerHTML = (sie.length
        ? `<p class="lemums bridinajums-${esc(sie[0].krasa.toLowerCase())}">${Ik('brid')} <b>${t('LVĢMC brīdinājums {kur}:', { kur })}</b> ` +
          sie.map(b => `${esc(b.krasa)} — ${esc(b.paradiba)}${lidz(b)}`).join('; ') + piezime + '</p>'
        : `<p class="lemums lemums-nav"><b>${t('LVĢMC brīdinājumu {kur} nav.', { kur })}</b>${piezime}</p>`) +
        `<small class="avots-rinda">${rez ? AVOTI_LVGMC.bridinajumiRezerves : AVOTI_LVGMC.bridinajumi}</small>`;
    }).catch(e => {
      const el = kaste.querySelector('#rez-lemums');
      if (!el || e.name === 'AbortError') return;
      el.innerHTML = '<p class="lemums lemums-nezinams"><b>' + t('LVĢMC brīdinājumus šobrīd neizdevās pārbaudīt.') + '</b> ' +
        t('Skatiet meteo.lv vai klausieties LR1.') + '</p>';
    });
  }

  // "Nākamās 24 h": LVĢMC ikstundas prognoze tuvākajai prognožu vietai (/api/prognoze) — temperatūra, nokrišņi,
  // brāzmas un viens riska vārds pēc sliekšņiem. Avots nav pieejams vai prognoze par īsu — rindu nerāda (bez kļūdas).
  function prognozesDati(ll, no, signal) {
    iegut('/prognoze?' + new URLSearchParams(ll), signal).then(d => {
      const el = kaste.querySelector('#rez-prognoze');
      const p = d.prognoze;
      if (!el || !p || p.tmin == null) return;
      const sk = x => String(Math.abs(x) >= 10 || x === Math.round(x) ? Math.round(x) : (+x).toFixed(1)).replace('.', ',');
      const gr = x => (Math.round(x) > 0 ? '+' : Math.round(x) < 0 ? '−' : '') + Math.abs(Math.round(x));  // −3…+5 °C
      const stunda = t => t.slice(11, 16);
      const virsr = p.stundas >= 23 ? 'Nākamās 24 h' : `Nākamās ${p.stundas} h (līdz ${stunda(p.lidz)})`;
      const r = p.riski?.[0];
      const vieta = d.vieta?.nosaukums ? ` (${esc(d.vieta.nosaukums)}${d.vieta.attalums_m > 1500 ? ', ' + attalums(d.vieta.attalums_m) : ''})` : '';
      const dalas = [Math.round(p.tmin) === Math.round(p.tmax) ? `${gr(p.tmin)} °C` : `${gr(p.tmin)}…${gr(p.tmax)} °C`];
      if (p.nokrisni_mm != null) dalas.push(p.nokrisni_mm >= 0.1 ? `nokrišņi ${sk(p.nokrisni_mm)} mm` : 'bez nokrišņiem');
      if (p.brazmas_max != null) dalas.push(`brāzmas līdz ${sk(p.brazmas_max)} m/s`);
      const izdota = d.izdota ? new Date(d.izdota).toLocaleString('lv-LV', { timeZone: 'Europe/Riga', day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' }) : '';
      const avots = d.avots || {};
      el.innerHTML = `<p class="prognoze-rinda">${Ik('prognoze')} <b>${virsr}</b>${vieta}: ${dalas.join(', ')}` +
        ` — <b class="risks risks-${r ? r.limenis : 0}">${r ? esc(p.riski.map(x => x.vards).join(', ')) : 'bez būtiskiem riskiem'}</b></p>` +
        `<small class="avots-rinda"><a href="${esc(avots.url || 'https://data.gov.lv/dati/lv/dataset/meteorologiskas-prognozes-apdzivotam-vietam-jaunaka-datu-kopa')}" target="_blank" rel="noopener">LVĢMC prognoze</a>` +
        `${izdota ? ', izdota ' + esc(izdota) : ''} · ${esc(avots.licence || 'CC0 1.0')}. Prognoze, nevis brīdinājums.</small>`;
      // "Kas notiks tālāk": ja gaidāms risks, pirmajā vietā atgādinājums par laikapstākļiem
      const ol = kaste.querySelector('.talak ol');
      if (r && r.limenis >= 1 && ol) {
        ol.insertAdjacentHTML('afterbegin', `<li><b>Laikapstākļi:</b> ${p.stundas >= 23 ? 'nākamajās 24 h' : 'līdz ' + stunda(p.lidz)} — ${esc(r.vards)} (LVĢMC prognoze). ` +
          'Sekojiet LVĢMC brīdinājumiem un meklējiet vēlreiz, ja situācija mainās.</li>');
      }
    }).catch(() => {});
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
  // klientu apkalpošanas centrs (VPVKAC, 2023-11) kā atsevišķa rinda tikai pašvaldībām, kurām centrs sarakstā ir
  function pasvaldibaDati(ll, no, signal) {
    iegut('/pasvaldiba?' + new URLSearchParams(ll), signal).then(p => {
      const el = kaste.querySelector('#rez-pasvaldiba');
      if (!el) return;
      const saite = (url, t) => /^https?:\/\//.test(url || '') ? ` · <a href="${esc(url)}" target="_blank" rel="noopener">${t}</a>` : '';
      const k = p.kontakti, c = p.vpvkac;
      el.innerHTML = `<p class="pasvaldiba-rinda">${no.regions ? t('Pašvaldība') : t('Jūsu pašvaldība')}: <b>${esc(p.nosaukums)}</b>` +
        saite(p.ca_plans_url || p.ca_lapa, t('CA plāns')) + saite(p.majas_lapa, t('tīmekļvietne')) +
        (k?.talrunis ? ` · tālr. ${esc(k.talrunis.replace(/^\+371/, ''))}` : '') + (k?.epasts ? ` · ${esc(k.epasts)}` : '') + '</p>' +
        (k?.adrese ? `<p class="pasvaldiba-rinda">${t('Pašvaldības adrese:')} ${esc(k.adrese)}</p>` : '') +
        (c ? `<p class="pasvaldiba-rinda">${t('Klientu apkalpošanas centrs:')} ${esc(c.adrese)}${c.talrunis ? ` · tālr. ${esc(c.talrunis)}` : ''}</p>` : '') +
        // abonēšana bez lietotnes: Atom plūsma un kalendārs šai pašvaldībai (karte_api.py /api/plusma.xml, /api/kalendars.ics)
        `<p class="abonet-rinda">${t('Abonēt brīdinājumus:')} <a href="/api/plusma.xml?regions=${encodeURIComponent(p.kods)}" type="application/atom+xml">RSS</a>` +
        ` · <a href="/api/kalendars.ics?regions=${encodeURIComponent(p.kods)}">${t('Kalendārs')}</a></p>` +
        `<small class="avots-rinda">${t('Pašvaldību CA plāni (oficiāli dokumenti)')}` +
        (k ? ' · <a href="https://data.gov.lv/dati/dataset/public-persons-institutions" target="_blank" rel="noopener">Uzņēmumu reģistrs, publisko personu saraksts</a> · CC0' : '') +
        (c ? ' · <a href="https://data.gov.lv/dati/lv/dataset/vpvkac-kontakti" target="_blank" rel="noopener">VPVKAC kontakti</a>, 2023-11 · CC0' : '') + '</small>';
    }).catch(() => {});
  }

  // Plūdu scenārijiem: plūdu riska zona adresē (/api/pludi: LVĢMC karšu kopija vai WMS) un tuvākās upes līmenis
  function pluduBloks() {
    return `<ul class="fakti" id="rez-pludi-bloks">
      <li id="rez-pludi"><span class="ikona">${Ik('pludi')}</span><div><b>${t('Plūdu riska zona')}</b><span>${t('Pārbauda…')}</span></div></li>
      <li id="rez-udens"><span class="ikona">${Ik('limenis')}</span><div><b>${t('Tuvākā upe vai ezers')}</b><span>${t('Ielādē…')}</span></div></li></ul>`;
  }
  function pluduRinda(id, saturs) { const li = kaste.querySelector('#' + id); if (li) li.querySelector('div').innerHTML = saturs; }
  // Abu atbilžu kopsavilkums (adrese plūdu zonā? × upes statuss pret CA plāna slieksni): rinda bloka augšā
  let pluduStavoklis = {};
  function pluduDati(ll, signal) {
    pluduStavoklis = { zona: undefined, stacija: null };
    pluduZona(ll, signal, 0);
    pluduUdens(ll, signal);
  }
  const mLv = v => (v < 0 ? '−' : '') + Math.abs(v).toFixed(2).replace('.', ',');
  const STATUSA_NOS = { 'normāls': 'Normāls līmenis', 'paaugstināts': 'Paaugstināts līmenis', 'kritisks': 'Kritisks līmenis' };
  const STATUSA_KLASE = { 'normāls': 'normals', 'paaugstināts': 'paaugstinats', 'kritisks': 'kritisks' };
  const zonuPoga = () => `<button type="button" class="otra udens-zonas-poga" data-darbiba="pludu-zonas">${Ik('pludi')} ${t('Rādīt plūdu zonas kartē')}</button>`;
  function pluduSecinajums() {
    zimetPluduLemumu();
    const { zona, stacija: s } = pluduStavoklis;
    const bloks = kaste.querySelector('#rez-pludi-bloks');
    if (!bloks || !s || s.statuss === 'normāls') return;
    let li = bloks.querySelector('#rez-pludi-secinajums');
    if (!li) {
      li = document.createElement('li');
      li.id = 'rez-pludi-secinajums';
      li.className = 'udens-secinajums udens-' + STATUSA_KLASE[s.statuss];
      bloks.prepend(li);
    }
    const kur = `ūdens līmenis (${esc(s.vieta || s.nosaukums)})`;
    const t = s.statuss === 'kritisks'
      ? (zona === true ? `<b>Šī vieta ir plūdu riska zonā, un ${kur} ir virs kritiskā.</b> Plūdu zonas adreses var applūst: esiet gatavi doties uz evakuācijas vietu un sekojiet pašvaldības norādēm.`
        : zona === false ? `<b>${kur[0].toUpperCase() + kur.slice(1)} ir virs kritiskā.</b> Šī vieta nav plūdu riska zonā, bet plūdu zonas adreses tuvumā var applūst; izvairieties no tām.`
          : `<b>${kur[0].toUpperCase() + kur.slice(1)} ir virs kritiskā.</b> Plūdu riska zonas adreses var applūst.`)
      : (zona === true ? `<b>Šī vieta ir plūdu riska zonā, un ${kur} ir paaugstināts.</b> Sekojiet līmenim un sagatavojieties.`
        : `<b>${kur[0].toUpperCase() + kur.slice(1)} ir paaugstināts.</b> Sekojiet līmenim un LVĢMC brīdinājumiem.`);
    li.innerHTML = `<span class="ikona">${Ik('brid')}</span><div><span>${t}</span>${s.statuss === 'kritisks' ? zonuPoga() : ''}</div>`;
  }
  // "Ogre pie Ogres: 21,40 m, 0,75 m zem kritiskā 22,15 m, +0,12 m/24 h" (slieksnis no CA plāna, src/karte/db/udens_slieksni.json)
  function statusaRinda(s) {
    const lidz = s.lidz_kritiskajam_m;
    const att = lidz == null ? '' : lidz > 0 ? `, ${mLv(lidz)} m zem kritiskā ${mLv(s.kritiskais)} m`
      : `, ${mLv(-lidz)} m virs kritiskā ${mLv(s.kritiskais)} m`;
    const izm = s.izmaina_24h_cm;
    const tend = izm == null ? '' : `, ${izm > 0 ? '+' : ''}${mLv(izm / 100)} m/24 h`;
    const a = s.sliekshna_avots;
    const avots = a ? `Slieksnis: <a href="${esc(a.url)}" target="_blank" rel="noopener">${esc(a.nosaukums)}</a>${a.lpp ? ', ' + esc(a.lpp) + ' lpp.' : ''}` +
      (s.slieksnis_pienemts ? ` „Paaugstināts” sākas ${mLv(s.kritiskais - s.slieksnis)} m zem kritiskā (mūsu pieņēmums, plānā tāda sliekšņa nav).` : '') : '';
    const pr = s.prognoze?.statuss && s.prognoze.statuss !== 'normāls' ? ` LVĢMC prognoze pēc ${s.prognoze.dienas} dienām: ${esc(s.prognoze.statuss)} (${mLv(s.prognoze.mediana_m)} m).` : '';
    return `<span class="udens-statuss udens-${STATUSA_KLASE[s.statuss]}"><b>${STATUSA_NOS[s.statuss]}</b> · ${esc(s.vieta || s.nosaukums)}: ` +
      `${mLv(s.limenis_m)} m${att}${tend}</span>${pr ? `<small>${pr}</small>` : ''}${avots ? `<small>${avots}</small>` : ''}`;
  }
  // /api/pludi: LVĢMC karšu kopija PostGIS (uzreiz) → LVĢMC WMS ar kešu → {zinams: false}. API gaida ≤ 6 s; ja LVĢMC
  // vēl rēķina — 202 {ielade}: vēlreiz pēc 10 s (≤ 2 reizes). Ja LVĢMC neatbild, bet atbilde saglabāta — {novecojis}.
  const proc = v => String(v).replace('.', ',') + ' %';
  const METODES = { 'PostGIS kopija': 'LVĢMC karšu kopija mūsu datubāzē', 'LVĢMC WMS': 'LVĢMC karšu serviss, tikko' };
  function pluduTeksts(p) {
    if (p.zona) return `<strong class="jā">Jā</strong>: ${p.veidi.map(v => `${esc(v.veids)} (${proc(v.varbutiba_proc)} varbūtība gadā)`).join(', ')}`;
    if (p.nepilnigi) return 'Pēc pieejamajām kartēm nē, bet daļa karšu neatbildēja.';
    const k = (p.varbutibas?.length ? p.varbutibas : [10, 1, 0.5]).map(proc);
    return `<strong class="nē">Nē</strong>: nav applūstošā teritorijā (${k.length > 1 ? k.slice(0, -1).join(', ') + ' un ' + k[k.length - 1] : k[0]} kartes).`;
  }
  function pluduAvots(p) {
    const a = p.avota_info;
    const avots = a && p.avots === 'lvgmc-pludi-faili'
      ? `<a href="${esc(a.url)}" target="_blank" rel="noopener">${esc(a.nosaukums)}</a> · ${esc(a.licence)}` : AVOTI_LVGMC.pludi;
    const m = p.metode ? METODES[p.metode] || (p.metode.startsWith('kešs no ') ? 'saglabātā LVĢMC atbilde no ' + p.metode.slice(8) : p.metode) : '';
    return `<small class="avots-rinda">${avots}</small>` + (m ? `<small class="avots-rinda pludi-metode">Pārbaudīts: ${esc(m)}</small>` : '');
  }
  function pluduZona(ll, signal, meginajums) {
    iegut('/pludi?' + new URLSearchParams(ll), signal).then(p => {
      if (p.zinams === false) {  // LVĢMC neatbild, un saglabātas atbildes šai vietai nav (pirms p.ielade: tas ir arī šeit)
        pluduRinda('rez-pludi', `<b>Plūdu riska zona</b><span>${esc(p.iemesls || 'LVĢMC plūdu karte šobrīd neatbild')}, un šai vietai saglabātas atbildes nav. ` +
          'Mēģiniet pēc brīža; plūdu zonu slānis kartē ir ieslēgts.</span>' + pluduAvots(p));
        pluduStavoklis.lemums = { tonis: 'nezinams', teksts: 'LVĢMC plūdu karte šobrīd neatbild' };
        zimetPluduLemumu();
        return;
      }
      if (p.ielade) {
        pluduRinda('rez-pludi', `<b>${Valoda.t('Plūdu riska zona')}</b><span>${meginajums < 2 ? 'Plūdu kartes vēl ielādējas, mēģinām vēlreiz pēc 10 s…'
          : 'Plūdu kartes pašlaik atbild lēni. Plūdu zonas redzamas kartē (slānis ieslēgts).'}</span>`);
        pluduStavoklis.lemums = meginajums < 2 ? { tonis: 'gaida', teksts: Valoda.t('kartes vēl ielādējas…') }
          : { tonis: 'nezinams', teksts: Valoda.t('pašlaik nevar pārbaudīt; zonas redzamas kartē') };
        zimetPluduLemumu();
        if (meginajums < 2) setTimeout(() => { if (!signal.aborted) pluduZona(ll, signal, meginajums + 1); }, 10000);
        return;
      }
      const t = p.novecojis ? `${esc(p.iemesls || 'LVĢMC plūdu karte šobrīd neatbild')}; pēdējais zināmais: ${pluduTeksts(p)}` : pluduTeksts(p);
      pluduRinda('rez-pludi', `<b>${Valoda.t('Plūdu riska zona')}</b><span>${t}</span>${pluduAvots(p)}`);
      pluduStavoklis.zona = p.zona ? true : p.nepilnigi ? undefined : false;
      // lēmuma rindai īsi: lielākā varbūtība gadā
      const maks = p.zona ? Math.max(...p.veidi.map(v => +v.varbutiba_proc || 0)) : 0;
      const proc = String(maks).replace('.', Valoda.aktiva() === 'en' ? '.' : ',');
      pluduStavoklis.lemums = p.zona ? { tonis: 'ja', teksts: `<strong>${Valoda.t('Jā')}</strong>${maks ? ` (${Valoda.t('{x} % varbūtība gadā', { x: proc })})` : ''}` }
        : p.nepilnigi ? { tonis: 'nezinams', teksts: Valoda.t('pēc pieejamajām kartēm nē (daļa karšu neatbildēja)') }
          : { tonis: 'ne', teksts: `<strong>${Valoda.t('Nē')}</strong>, ${Valoda.t('nav applūstošā teritorijā')}` };
      pluduSecinajums();
    }).catch(e => {
      if (e.name === 'AbortError') return;
      pluduRinda('rez-pludi', '<b>' + t('Plūdu riska zona') + '</b><span>' + t('Neizdevās pārbaudīt. Plūdu zonas redzamas kartē (slānis ieslēgts).') + '</span>');
      pluduStavoklis.lemums = { tonis: 'nezinams', teksts: t('neizdevās pārbaudīt; zonas redzamas kartē') };
      zimetPluduLemumu();
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
      // statuss: tuvākā no 3 stacijām ar slieksni (CA plānā) un svaigu mērījumu, ne tālāk par 30 km
      const ss = d.stacijas.find(x => x.statuss && !x.vecs && x.limenis_m != null && x.attalums_m <= 30000);
      pluduStavoklis.stacija = ss || null;
      pluduRinda('rez-udens', `<b>${t('Tuvākā upe vai ezers')}</b>${ss ? statusaRinda(ss) : ''}<span>${esc(s.nosaukums)} (${attalums(s.attalums_m)}): ${s.limenis_cm} cm${tend}` +
        `${s.vecs ? ' — dati novecojuši' : ''}</span><small>Mērīts ${laiks}.${ss ? '' : ' Bīstamības līmeņi šai stacijai nav publiski pieejami (LVĢMC sliekšņi nav atvērtie dati).'}</small>` +
        `${prognoze}<small class="avots-rinda">${AVOTI_LVGMC.udens}</small>`);
      pluduSecinajums();
    }).catch(e => {
      if (e.name !== 'AbortError') pluduRinda('rez-udens', '<b>' + t('Tuvākā upe vai ezers') + '</b><span>Ūdens līmeņa datus neizdevās ielādēt.</span>');
    });
  }

  // Vējš tagad tuvākajā LVĢMC stacijā (ar brāzmām)
  function vejaBloks() {
    return `<ul class="fakti"><li id="rez-vejs"><span class="ikona">${Ik('vejs')}</span><div><b>${t('Vējš tagad')}</b><span>${t('Ielādē…')}</span></div></li></ul>`;
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
    return `<ul class="fakti"><li id="rez-augsne"><span class="ikona">${Ik('lietus')}</span><div><b>Nokrišņi un augsne</b><span>Ielādē…</span></div></li></ul>`;
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
      L.marker([lat, lon], { icon: Ikonas.markeris(f.properties.kategorija, k.krasa, 30), title: nosaukums(f.properties) || k.nosaukums || '', zIndexOffset: 500 })
        .bindPopup(() => popupSaturs(no.regions ? { ...f.properties, attalums_m: null } : f.properties, { lat, lng: lon }))
        .addTo(rezultatuSlanis);
    }
    if (no.regions) L.circleMarker([no.lat, no.lon], { radius: 5, color: '#1c1917', weight: 2, fillOpacity: 0 })
      .bindTooltip(t('Attālumi no šejienes')).addTo(rezultatuSlanis);
    // telefonā apakšā ir rezultātu lapa (apaksa.js): sākumpunkts un tuvākā vieta paliek redzami virs tās
    const atst = typeof Apaksa !== 'undefined' && Apaksa.aktiva() ? Apaksa.atstarpes() : { paddingTopLeft: [40, 40], paddingBottomRight: [40, 40] };
    karte.fitBounds(L.latLngBounds(punkti), { ...atst, maxZoom: 15 });
  }

  // Enter rezultātu sarakstā = klikšķis
  kaste.addEventListener('keydown', e => { if (e.key === 'Enter' && e.target.matches('li[data-lat]')) e.target.click(); });

  return { sakt, atkartot, meklet, vietaNav, labot, ieteikumi, pirmaisSkats, konteksts: () => konteksts };
})();
