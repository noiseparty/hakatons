// Demo panelis (datorā — kreisajā kolonnā; telefonā — apakšā virs kartes): simulēti krīzes scenāriji, kas maina karti.
// Dati: demo/scenariji.json. Viss, ko scenārijs ieliek (brīdinājums, zonas, notikumi), ir ar zīmi SIMULĀCIJA; tuvākās
// vietas — īstie dati no /api/objekti. Demo laikā galvenes rindā ir josla "SIMULĀCIJA · scenārijs · Scenāriji · Beigt demo"
// (tā neaizsedz karti, uznirstošos logus un lapas lēmuma rindu). "Beigt demo" atjauno slāņus, plūdu slāni un kartes skatu.
// Saite ?demo=<kods>[&regions=<kods>] atver scenāriju uzreiz. Lieto app.js globālos (karte, stavoklis, kategorijas, regioni,
// iegut, atjaunot, kopsavilkumi, statuss, radtPludus, popupSaturs, marsrutaSaites, attalums, nosaukums, esc, el).
const Demo = (() => {
  const LIMENI = { 1: ['dzeltens', 'Dzeltenais', '#eab308'], 2: ['oranzs', 'Oranžais', '#ea580c'], 3: ['sarkans', 'Sarkanais', '#b91c1c'] };
  const telefons = () => matchMedia('(max-width: 800px)').matches;
  const ZIME = '<span class="demo-zime" data-t="SIMULĀCIJA">SIMULĀCIJA</span>';
  // Paneļa grupas: reālie notikumi pēc krīzes veida (scenārija "tips"), tad simulācijas tajā pašā secībā
  const TIPI = [['pludi', 'Plūdi'], ['vetra', 'Vētra'], ['karstums', 'Karstums'], ['elektriba', 'Elektrība un BRELL'],
    ['drosiba', 'Droni un drošība'], ['ugunsgreks', 'Ugunsgrēki, dūmi, gāze'], ['sakari', 'Sakari un e-pakalpojumi'], ['veseliba', 'Veselība']];
  const tipaVieta = s => { const i = TIPI.findIndex(([k]) => k === s.tips); return i < 0 ? TIPI.length : i; };
  const kartot = saraksts => saraksts.map((s, i) => [s, i]).sort((a, b) => tipaVieta(a[0]) - tipaVieta(b[0]) || a[1] - b[1]).map(([s]) => s);
  const reali = () => kartot(dati.scenariji.filter(s => s.grupa === 'reals'));
  const simulacijas = () => kartot(dati.scenariji.filter(s => s.grupa !== 'reals'));
  let dati = null;
  let aktivs = null;          // { sc, regions }
  let saglabats = null;       // stāvoklis pirms demo, lai "Beigt demo" to atjaunotu
  let paaudze = 0;            // pārslēdzot scenāriju, novecojušās ielādes neko nezīmē
  let skats = null;           // scenārija kartes robežas (radit())
  const slanis = L.layerGroup();

  // ---- DOM: cilne kartes labajā malā, panelis, josla zem LVĢMC joslas, zīme kartē ----
  const laukums = el('kartes-laukums');
  laukums.insertAdjacentHTML('beforeend', `
    <button id="demo-cilne" type="button" aria-controls="demo-panelis" aria-expanded="false">Demo</button>
    <div id="demo-karte-zime" hidden>${ZIME}</div>
    <aside id="demo-panelis" aria-label="Demo scenāriji" data-t-aria="Demo scenāriji">
      <div class="demo-galva"><b data-t="Demo scenāriji">Demo scenāriji</b>${ZIME}
        <button type="button" class="demo-aizvert" aria-label="Aizvērt demo paneli" data-t-aria="Aizvērt demo paneli">${Ik('aizvert')}</button></div>
      <div id="demo-saturs"></div>
    </aside>`);
  el('bridinajums').insertAdjacentHTML('afterend', '<div id="demo-josla" class="bridinajums demo-josla" role="status" hidden></div>');
  // Galvenes josla demo laikā (bez atskaņošanas; atskaņošanas josla — atskanot.js — ir tajā pašā vietā)
  document.querySelector('header').insertAdjacentHTML('beforeend', `
    <div id="demo-galvene" class="demo-galvene" role="region" aria-label="Demo režīms" data-t-aria="Demo režīms" hidden>${ZIME}
      <b class="demo-galvene-nos"></b>
      <button type="button" class="demo-galvene-poga" data-darbiba="demo-panelis" aria-controls="demo-panelis" aria-expanded="false">${Ik('saraksts')}<span data-t="Scenāriji">Scenāriji</span></button>
      <button type="button" class="demo-galvene-poga demo-galvene-beigt" data-darbiba="beigt">${Ik('apturet')}<span data-t="Beigt demo">Beigt demo</span></button>
    </div>`);
  const panelis = el('demo-panelis'), saturs = el('demo-saturs'), josla = el('demo-josla'), galvene = el('demo-galvene');
  const atvertsJa = () => document.body.classList.contains('demo-atverts');

  // Datorā panelis ir kreisās kolonnas (#panelis, darbvirsma.js) pirmais elements, telefonā — kartes laukumā (apakšā)
  const plats = matchMedia('(min-width: 801px)');
  function novietotPaneli() {
    const kol = el('panelis');
    if (plats.matches && kol) {
      if (kol.firstElementChild !== panelis) kol.prepend(panelis);
      if (atvertsJa()) document.body.classList.remove('dv-kreisa-slegta');  // sakļauta kreisā kolonna atveras
    } else if (panelis.parentElement !== laukums) laukums.append(panelis);
  }
  plats.addEventListener('change', () => setTimeout(() => { novietotPaneli(); karte.invalidateSize(); }, 0));

  function atvert(atverts) {
    const bija = atvertsJa();
    document.body.classList.toggle('demo-atverts', atverts);
    el('demo-cilne').setAttribute('aria-expanded', atverts);
    galvene.querySelector('[data-darbiba="demo-panelis"]').setAttribute('aria-expanded', atverts);
    if (atverts) novietotPaneli();
    if (atverts && plats.matches) el('panelis').scrollTop = 0;
    if (atverts && !dati) ieladet().then(zimetSarakstu);
    if (bija !== atverts) setTimeout(() => karte.invalidateSize(), 0);
    // telefonā panelis aizsedz kartes apakšu: pēc atvēršanas/aizvēršanas scenārija vietu rāda vēlreiz
    if (aktivs && bija !== atverts && telefons()) setTimeout(radit, 300);
  }
  el('demo-cilne').addEventListener('click', () => atvert(!atvertsJa()));
  panelis.querySelector('.demo-aizvert').addEventListener('click', () => atvert(false));
  document.addEventListener('keydown', e => { if (e.key === 'Escape' && atvertsJa()) atvert(false); });
  // "Beigt demo" (panelī vai galvenē) beidz arī atskaņošanu; meklēšana (meklesana.js) sauc Demo.beigt() tieši
  const beigtLietotajs = () => (typeof Atskanot !== 'undefined' && Atskanot?.aktivs ? Atskanot.beigt() : beigt());
  galvene.addEventListener('click', e => {
    const d = e.target.closest('[data-darbiba]')?.dataset.darbiba;
    if (d === 'beigt') beigtLietotajs();
    if (d === 'demo-panelis') atvert(!atvertsJa());
  });

  async function ieladet() {
    try {
      dati = await (await fetch('demo/scenariji.json')).json();
    } catch {
      saturs.innerHTML = '<p class="piezime kluda">Demo scenārijus neizdevās ielādēt.</p>';
    }
    return dati;
  }

  function zimetSarakstu() {
    if (!dati) return;
    // rinda: ikona · nosaukums · datums un vieta · "Simulēts" (izdomātiem gadījumiem)
    const poga = s => `<li><button type="button" data-demo="${esc(s.kods)}" title="${esc(s.isi || '')}"
        ${aktivs?.sc.kods === s.kods ? 'aria-current="true"' : ''}><span class="demo-ikona-l">${Ikonas.no(s.ikona)}</span>
        <span class="demo-rinda"><b>${esc(s.nosaukums)}</b><small>${[s.kad, s.kur].filter(Boolean).map(esc).join(' · ')}</small></span>
        ${s.grupa === 'reals' ? '' : '<span class="demo-sim">Simulēts</span>'}</button></li>`;
    const saraksts = sc => `<ul class="demo-saraksts">${sc.map(poga).join('')}</ul>`;
    const pecTipa = sc => TIPI.map(([k, nos]) => [nos, sc.filter(s => s.tips === k)]).concat([['Citi', sc.filter(s => tipaVieta(s) === TIPI.length)]])
      .filter(([, x]) => x.length).map(([nos, x]) => `<h4 class="demo-tips">${esc(nos)}</h4>${saraksts(x)}`).join('');
    const r = reali(), s = simulacijas();
    saturs.innerHTML =
      (r.length ? '<h3 class="demo-grupa">Reāli notikumi</h3><p class="piezime">Kas notika Latvijā (skaitļi ar avotiem) un ko Jūs redzētu šajā lietotnē. ' +
        'Karte rāda simulāciju; tuvākās vietas ir īstie dati.</p>' + pecTipa(r) : '') +
      (s.length ? '<h3 class="demo-grupa">Simulācijas</h3><p class="piezime">Izdomāti krīzes gadījumi. Brīdinājumi, zonas un notikumi ir simulēti; ' +
        'tuvākās vietas, maršruti un avoti ir īstie kartes dati.</p>' + saraksts(s) : '') +
      (aktivs ? beigtPoga() : '');
  }
  const beigtPoga = () => '<button type="button" class="galvena demo-beigt" data-darbiba="beigt">' + Ik('apturet') + ' Beigt demo, rādīt īsto karti</button>';

  saturs.addEventListener('click', e => {
    const b = e.target.closest('button');
    const kods = b?.dataset.demo;
    if (kods) sakt(kods);
    if (b?.dataset.darbiba === 'beigt') beigtLietotajs();
    if (b?.dataset.darbiba === 'demo-saraksts') zimetSarakstu();  // ne "saraksts": to tver saraksts.js
    if (b?.dataset.darbiba === 'drukat') { document.body.classList.add('druka-demo'); print(); }  // demo.css drukas stili tikai šeit
    const li = e.target.closest('li[data-lat]');
    if (li && !e.target.closest('a')) {
      const ll = { lat: +li.dataset.lat, lng: +li.dataset.lon };
      karte.setView(ll, Math.max(karte.getZoom(), 15), { animate: false });  // logs — pēc gala skata, ne animācijas vidū
      L.popup().setLatLng(ll).setContent(li.dataset.p ? popupSaturs(JSON.parse(li.dataset.p), ll) : li.dataset.teksts).openOn(karte);
      if (telefons()) atvert(false);
    }
  });
  addEventListener('afterprint', () => document.body.classList.remove('druka-demo'));
  saturs.addEventListener('change', e => { if (e.target.id === 'demo-regions' && aktivs) sakt(aktivs.sc.kods, e.target.value); });
  saturs.addEventListener('keydown', e => { if (e.key === 'Enter' && e.target.matches('li[data-lat]')) e.target.click(); });

  // ---- Ģeometrija ----
  function metri(a, b) {
    const r = Math.PI / 180, dLat = (b[0] - a[0]) * r, dLon = (b[1] - a[1]) * r;
    const h = Math.sin(dLat / 2) ** 2 + Math.cos(a[0] * r) * Math.cos(b[0] * r) * Math.sin(dLon / 2) ** 2;
    return Math.round(2 * 6371000 * Math.asin(Math.sqrt(h)));
  }
  const virziens = (a, b) => {  // azimuts no a uz b, grādi no ziemeļiem
    const r = Math.PI / 180, y = Math.sin((b[1] - a[1]) * r) * Math.cos(b[0] * r);
    const x = Math.cos(a[0] * r) * Math.sin(b[0] * r) - Math.sin(a[0] * r) * Math.cos(b[0] * r) * Math.cos((b[1] - a[1]) * r);
    return (Math.atan2(y, x) / r + 360) % 360;
  };
  const punktsNo = (c, gr, m) => {  // punkts m metrus no c azimutā gr (pietiek mazos attālumos)
    const r = Math.PI / 180;
    return [c[0] + m * Math.cos(gr * r) / 111320, c[1] + m * Math.sin(gr * r) / (111320 * Math.cos(c[0] * r))];
  };
  // Sektors: dūmu konuss no avota vēja virzienā (virziens = kurp iet dūmi), platums grādos
  const sektors = z => [z.centrs, ...Array.from({ length: 13 }, (_, i) => punktsNo(z.centrs, z.virziens - z.platums / 2 + i * z.platums / 12, z.garums_m))];
  const zonā = (zona, ll) => zona.tips === 'aplis' ? metri(zona.centrs, ll) <= zona.radiuss_m
    : zona.tips === 'sektors' ? metri(zona.centrs, ll) <= zona.garums_m && Math.abs(((virziens(zona.centrs, ll) - zona.virziens + 540) % 360) - 180) <= zona.platums / 2
    : false;
  const ll = f => [f.geometry.coordinates[1], f.geometry.coordinates[0]];
  const ikona = (teksts, klase = '') => L.divIcon({ html: `<span>${Ikonas.no(teksts) || esc(teksts)}</span>`, className: 'demo-ikona ' + klase, iconSize: [30, 30] });

  // Kartes laukums, ko neaizsedz apakšējā lapa vai telefonā atvērtais panelis (datorā panelis ir kreisajā kolonnā, ne kartē)
  function atstarpes() {
    const atverts = atvertsJa() && telefons();
    if (typeof Apaksa !== 'undefined' && Apaksa.aktiva()) {
      // sānos vairāk vietas: vietas pastāvīgā uzraksta ("Jūsu vieta (Saulkrasti)") puse sniedzas pāri punktam uz abām pusēm
      const a = Apaksa.atstarpes(Math.max(Apaksa.augstums(), atverts ? panelis.offsetHeight : 0));
      return { paddingTopLeft: [Math.max(80, a.paddingTopLeft[0]), a.paddingTopLeft[1]], paddingBottomRight: [Math.max(80, a.paddingBottomRight[0]), a.paddingBottomRight[1]] };
    }
    if (telefons()) return { paddingTopLeft: [20, 20], paddingBottomRight: [20, (atverts ? panelis.offsetHeight : 0) + 20] };
    // dators: augšā "Karte | Reljefs" un SIMULĀCIJA zīme, labajā pusē kartes rīki, apakšā leģenda (darbvirsma.js)
    const legenda = document.querySelector('.dv-legenda');
    return { paddingTopLeft: [40, 64], paddingBottomRight: [72, (legenda?.offsetHeight || 0) + 32] };
  }

  // ---- Scenārija sākšana un beigšana ----
  // iestatijumi.panelis: false — paneli neatver (atskaņošana: telefonā redzama lapa ar meklēšanas kartīti)
  async function sakt(kods, regions, iestatijumi = {}) {
    if (!dati && !(await ieladet())) return;
    const sc = dati.scenariji.find(s => s.kods === kods);
    if (!sc) return;
    if (!saglabats) {
      saglabats = { kategorijas: new Set(stavoklis.kategorijas), pludi: el('pludu-slanis').checked, skats: karte.getBounds() };
      slanis.addTo(karte);
    }
    const mana = ++paaudze;
    regions = sc.regionu_izvele ? (regions || sc.regionu_izvele[0]) : null;
    aktivs = { sc, regions };
    if (iestatijumi.panelis !== false) rezultats(kods, regions);  // atskaņošana to jau izsaukusi (atskanot.js) pirms scenārija
    else simIestatit(sc, regions);
    document.body.classList.add('demo-aktivs');
    el('demo-karte-zime').hidden = false;
    galvene.querySelector('.demo-galvene-nos').innerHTML = `${Ikonas.no(sc.ikona)} ${esc(sc.nosaukums)}`;
    galvene.hidden = false;
    if (iestatijumi.panelis !== false) atvert(!SC_ID[kods]);  // scenārijam ar rezultātu — Rezultāts (kreisā kolonna / lapa) (rīcības plāns); "Scenāriji" galvenē atver sarakstu
    if (telefons() && !document.body.classList.contains('panelis-slegts')) el('panelis-poga').click();
    history.replaceState(null, '', '?' + new URLSearchParams(regions ? { demo: kods, regions } : { demo: kods }));
    slanis.clearLayers();
    karte.closePopup();
    aizvertPrognozi();

    // Slāņi: scenārija īstie slāņi kartē; plūdu riska zonas
    if (sc.slani) {
      stavoklis.kategorijas = new Set(sc.slani.filter(k => kategorijas[k]?.skaits));
      raditSlanus();
      atjaunot();
      if (!stavoklis.kategorijas.size) statuss('Demo · simulācija');  // nevis "Izvēlies vismaz vienu slāni"
    }
    // Plūdu zonas (LVĢMC WMS, atbild 5–30 s) tikai pēc lapas "load": citādi saite ?demo=pludi-… gaida flīzes, pirms lapa ielādēta;
    // kartīte un reljefa slānis parādās uzreiz, zonu leģenda (zonas.js) rāda "Ielādē zonas…"
    const pludi = !!sc.pludi || saglabats.pludi;
    if (!pludi || document.readyState === 'complete') radtPludus(pludi);
    else addEventListener('load', () => setTimeout(() => { if (aktivs?.sc === sc) radtPludus(true); }, 0), { once: true });

    const r = regions ? regioni[regions] : null;
    const vieta = sc.vieta || (r && { lat: (r.bbox[1] + r.bbox[3]) / 2, lon: (r.bbox[0] + r.bbox[2]) / 2, nosaukums: r.nosaukums + ', centrs' });
    zimetJoslu(sc, r);
    saturs.innerHTML = karte_(sc, r, '<p class="piezime">Ielādē tuvākās vietas…</p>');
    saturs.scrollTop = 0;
    karte.invalidateSize();

    const robezas = L.latLngBounds([]);
    if (vieta) {
      robezas.extend([vieta.lat, vieta.lon]);
      L.marker([vieta.lat, vieta.lon], { icon: ikona('vieta', 'demo-es'), zIndexOffset: 1000 })
        .bindTooltip(esc(vieta.nosaukums), { permanent: true, direction: 'top', offset: [0, -14] }).addTo(slanis);
    }
    zimetZonas(sc, robezas);

    // Brīdinājuma reģioni (VZD robežas) vai izvēlētais reģions bez sakariem
    const regionuKodi = regions ? [regions] : sc.bridinajums?.regioni || [];
    const [regionuGj, bloki, celi] = await Promise.all([
      Promise.all(regionuKodi.map(k => iegut('/regioni/' + k).catch(() => null))),
      tuvakieBloki(sc, vieta, regions),
      celuNotikumi(sc, vieta),
    ]);
    if (mana !== paaudze) return;
    // Ceļi: īstie LVC notikumi tagad; ja to nav vai avots neatbild — scenārija simulētais slēgums (celu_rezerve)
    if (sc.celi_lvc) {
      if (celi?.length) zimetCelus(celi, robezas); else zimetRezervi(sc, robezas);
      bloki.html = celuBloks(sc, celi) + bloki.html;
    }
    const krasa = regions ? '#57534e' : LIMENI[sc.bridinajums?.limenis]?.[2] || '#b91c1c';
    const regRobezas = L.latLngBounds([]);
    for (const gj of regionuGj.filter(Boolean)) {
      const g = L.geoJSON(gj, { style: { color: krasa, weight: 2, fillColor: krasa, fillOpacity: regions ? .12 : sc.zonas ? .05 : .18, dashArray: regions ? '6 4' : null } })
        .bindTooltip(`SIMULĀCIJA · ${esc(sc.bridinajums?.paradiba || sc.nosaukums)}: ${esc(gj.properties.nosaukums)}`, { sticky: true })
        .addTo(slanis);
      g.bringToBack();
      regRobezas.extend(g.getBounds());
    }
    saturs.innerHTML = karte_(sc, r, bloki.html);
    if (typeof Marsruts !== 'undefined') for (const m of bloki.marsruti || []) {
      Marsruts.rindai(saturs.querySelector(`li[data-lat="${m.uz[0]}"][data-lon="${m.uz[1]}"]`), [vieta.lat, vieta.lon], m.uz,
        { zonas: sc.zonas, slanis, aizstat: m.linija });
    }
    for (const p of bloki.punkti) robezas.extend(p);
    skats = sc.skats === 'regioni' || regions || !robezas.isValid() ? regRobezas : robezas;
    radit();
    aizvertPrognozi();  // prognozes.js datorā atveras pats pēc ielādes; saitē ?demo= tas var notikt tikai tagad
  }
  // Īstā LVĢMC prognožu un brīdinājumu lente (prognozes.js) demo laikā aizvērta un paslēpta (demo.css), lai nejaucas ar simulāciju
  const aizvertPrognozi = () => { if (typeof Prognozes !== 'undefined') Prognozes.atvert(false); };
  // Leaflet klusējot izmet setView/fitBounds, kamēr notiek tuvināšanas animācija (piem., tikko beidzies iepriekšējais
  // scenārijs vai meklēšanas kartīte pietuvināja karti): tad skatu rāda pēc tās beigām — citādi karte paliek vecajā vietā
  const radit = () => {
    if (!aktivs || !skats?.isValid()) return;
    if (karte._animatingZoom) { karte.once('zoomend', radit); return; }
    karte.fitBounds(skats, { maxZoom: 15, ...atstarpes() });
  };
  // app.js: slāņu izvēles rūtiņas un grupu skaiti panelī
  function raditSlanus() {
    document.querySelectorAll('#kategorijas input').forEach(i => { i.checked = stavoklis.kategorijas.has(i.value); });
    kopsavilkumi();
  }

  function beigt() {
    paaudze++;
    aktivs = null;
    simIzslegt();
    if (rezultatsDemo) { rezultatsDemo = false; krizesMeklesana.notirit(); }
    skats = null;
    slanis.clearLayers();
    slanis.remove();
    document.body.classList.remove('demo-aktivs');
    el('demo-karte-zime').hidden = true;
    galvene.hidden = true;
    josla.hidden = true;
    history.replaceState(null, '', location.pathname);
    if (saglabats) {
      stavoklis.kategorijas = saglabats.kategorijas;
      raditSlanus();
      radtPludus(saglabats.pludi);
      atjaunot();
      karte.fitBounds(saglabats.skats);
      saglabats = null;
    }
    karte.invalidateSize();
    zimetSarakstu();
  }

  // ---- Simulētais stāvoklis: VIENS objekts baro "Situācija tagad" (dators + telefons), LVĢMC joslu, "Situācija" nozīmi un Rezultātu ----
  // Esošie renderētāji (bridinajumi.js, darbvirsma.js, sheet.js, meklesana.js) nemainās: demo laikā to /api pieprasījumi
  // (bridinajumi, udens, celi) saņem atbildi no šī objekta (fetch aizvietotājs zemāk); beidzot demo atbildes atkal ir īstās.
  // Elektrības atslēgumiem atsevišķa saraksta nav: tie ir brīdinājums "Elektroapgādes pārtraukums" ar klientu skaitu.
  const SC_ID = {  // demo scenārijs -> scenariji.json (meklēšanas rezultāta rīcības plāns)
    'pludi-ogre': 'pludi', 'jekabpils-2023': 'pludi', 'latgale-2017': 'pludi', 'vetra-2005': 'vetra_jumts', vetra: 'vetra_jumts', vejs: 'vetra_jumts',
    'vetra-2026': 'nav_elektribas', 'brell-2025': 'nav_elektribas', 'bez-sakariem': 'nav_sakaru', 'karstums-2021': 'karstums',
    'stikli-2018': 'meza_ugunsgreks', 'ulmana-2026': 'dumi_ara', 'meldru-2026': 'dumi_ara', 'bauskas-2026': 'gazes_smarza',
    'drons-2024': 'droni', 'drons-2026': 'droni', drons: 'droni', nakts: 'asinosana', 'ddos-2025': 'e_pakalpojumi' };
  const SIM_PAPILDU = {  // papildu simulētais stāvoklis pa scenārijiem: upju posteņi, ceļu slēgumi, atslēgumi
    'pludi-ogre': { udens: [{ stacija: 'SIM-OGRE', nosaukums: 'Ogre', lat: 56.8128, lon: 24.6417, limenis_cm: 214, izm: 62 }],
      celi: [{ nosaukums: 'Applūdusi iela', apraksts: 'Slēgta Brīvības iela pie Ogres upes: applūdusi brauktuve.', lat: 56.8139, lon: 24.6093 }], atslegumi: { n: '1 800', kur: 'Ogres novads' } },
    'jekabpils-2023': { udens: [{ stacija: 'SIM-JEKABPILS', nosaukums: 'Daugava, Jēkabpils', lat: 56.4936, lon: 25.8587, limenis_cm: 468, izm: 85 }],
      celi: [{ nosaukums: 'Applūdis ceļš', apraksts: 'Slēgts ceļš uz Sakas salu: applūdis.', lat: 56.5, lon: 25.87 }] },
    'latgale-2017': { udens: [{ stacija: 'SIM-REZEKNE', nosaukums: 'Rēzekne, Rēzeknes upe', lat: 56.5099, lon: 27.3331, limenis_cm: 301, izm: 74 }],
      celi: [{ nosaukums: 'Applūdusi ceļa daļa', apraksts: 'Slēgts ceļš: applūdis pie Rēzeknes.', lat: 56.52, lon: 27.31 }], atslegumi: { n: '3 000', kur: 'Latgale' } },
    'vetra-2005': { celi: [{ nosaukums: 'Koki uz ceļa', apraksts: 'Slēgts ceļš: koki pāri brauktuvei.', lat: 57.39, lon: 21.56 }], atslegumi: { n: '40 000', kur: 'Kurzemes piekraste' } },
    vetra: { celi: [{ nosaukums: 'Koks uz ceļa', apraksts: 'Slēgta josla: koks pāri brauktuvei.', lat: 56.949, lon: 24.105 }], atslegumi: { n: '8 000', kur: 'Rīga' } },
    'vetra-2026': { atslegumi: { n: '12 000', kur: 'Bauskas novads' } },
    'brell-2025': { atslegumi: { n: '100 000', kur: 'Rīga' } },
    'bez-sakariem': { atslegumi: { n: 'visi', kur: null } } };
  const tt = (k, p) => Valoda.t(k, p);
  let sim = null;  // { sc, bridinajumi, udens, celi }
  function simIzveidot(sc, kodsRegiona) {
    const r = kodsRegiona ? regioni[kodsRegiona] : null, p = SIM_PAPILDU[sc.kods] || {}, b = sc.bridinajums;
    const no = new Date(), lidz = h => new Date(no.getTime() + h * 3600e3).toISOString();
    const regNos = k => (k || []).map(x => regioni[x]?.nosaukums).filter(Boolean).join(', ');
    const brid = [];
    if (b) brid.push({ id: 'sim-' + sc.kods, krasa: LIMENI[b.limenis][1], limenis: b.limenis, paradiba: b.paradiba, notikums: b.vards || b.paradiba,
      regioni: r ? r.nosaukums : regNos(b.regioni), apgabali: [], no: no.toISOString(), lidz: lidz(b.lidz_h || 6), teksts: b.teksts, riski: b.riski, attiecas: true, poligoni: [] });
    if (p.atslegumi && !(b && /elektro/i.test(b.paradiba))) {
      const kur = p.atslegumi.kur || (r && r.nosaukums) || '';
      brid.push({ id: 'sim-atsl-' + sc.kods, krasa: LIMENI[2][1], limenis: 2, paradiba: tt('Elektroapgādes pārtraukums'), regioni: kur, apgabali: [], no: no.toISOString(), lidz: lidz(12),
        teksts: tt('Bez elektrības: {n} klientu · {kur}', { n: p.atslegumi.n, kur }), riski: '', attiecas: true, poligoni: [] });
    }
    const udens = (p.udens || []).map(s => ({ ...s, limenis_m: null, izmaina_24h_cm: s.izm, laiks: no.toISOString(), vecs: false, prognoze: null }));
    const celi = (p.celi || []).concat((sc.linijas || []).map(l => ({ nosaukums: l.nosaukums.replace(/\s*\(simulācija\)/, ''), apraksts: l.nosaukums, lat: l.koord[0][0], lon: l.koord[0][1], linija: l.koord })))
      .map((c, i) => ({ id: 'sim-celi-' + i, tips: 'slegums', cels: null, linija: [], aktivs: true, no: no.toISOString(), lidz: lidz(12), ...c }));
    return { sc, bridinajumi: brid, udens, celi };
  }
  const JSONATB = o => new Response(JSON.stringify(o), { status: 200, headers: { 'Content-Type': 'application/json' } });
  function simAtbilde(url) {
    if (!sim || !/\/api\/(bridinajumi|udens|celi|objekti)\b/.test(url)) return null;
    const u = new URL(url, location.href), cels = u.pathname;
    if (cels === '/api/bridinajumi') return { avots: 'SIMULĀCIJA', simulacija: true, laiks_lv: new Date().toISOString(), bridinajumi: sim.bridinajumi };
    if (cels === '/api/celi') {
      if (!sim.celi.length) return null;
      const c = u.searchParams.get('lat') ? L.latLng(+u.searchParams.get('lat'), +u.searchParams.get('lon')) : null, r = +u.searchParams.get('r');
      const n = sim.celi.map(x => c ? { ...x, attalums_m: Math.round(c.distanceTo([x.lat, x.lon])) } : x).filter(x => !c || !r || x.attalums_m <= r);
      return { avots: 'SIMULĀCIJA', simulacija: true, konfigurets: true, notikumi: n };
    }
    if (!sim.udens.length) return null;
    if (cels === '/api/udens') {
      const c = L.latLng(+u.searchParams.get('lat'), +u.searchParams.get('lon'));
      return { avots: 'SIMULĀCIJA', simulacija: true, stacijas: sim.udens.map(s => ({ ...s, attalums_m: Math.round(c.distanceTo([s.lat, s.lon])) }))
        .sort((a, b) => a.attalums_m - b.attalums_m).slice(0, +u.searchParams.get('limit') || 5) };
    }
    if (cels === '/api/objekti' && u.searchParams.get('kategorijas') === 'udens_limenis' && !u.searchParams.get('bbox') && !u.searchParams.get('lat'))
      return { features: sim.udens.map(s => ({ geometry: { coordinates: [s.lon, s.lat] }, properties: { nosaukums: s.nosaukums, ipasibas: s } })) };
    return null;
  }
  const _fetch = window.fetch.bind(window);
  window.fetch = (a, o) => { const x = sim && simAtbilde(String(a?.url || a)); return x ? Promise.resolve(JSONATB(x)) : _fetch(a, o); };
  // zīme "SIMULĒTI DATI" uz Rezultāta un Situācijas konteineriem (CSS ::before ar data-sim; tulkojas līdz ar valodu)
  const ZIMES = '#rezultati, #dv-situacija, #lapa-situacija';
  function simZimes() { document.querySelectorAll(ZIMES).forEach(e => { if (sim) e.dataset.sim = tt('SIMULĒTI DATI'); else delete e.dataset.sim; }); }
  document.addEventListener('valoda-maina', simZimes);
  function simIestatit(sc, kodsRegiona) {
    sim = simIzveidot(sc, kodsRegiona);
    simZimes();
    document.dispatchEvent(new Event('sim-maina'));
  }
  function simIzslegt() {
    if (!sim) return;
    sim = null;
    simZimes();
    document.dispatchEvent(new Event('sim-maina'));  // renderētāji atkal ielādē īstos datus
  }
  // Rezultāts (kā īstā meklēšana): rīcības plāns, 112, lēmums, tuvākās vietas — meklesana.js ar scenārija id un scenārija vietu
  let rezultatsDemo = false;
  async function rezultats(kods, regions) {
    if (!dati && !(await ieladet())) return;
    const sc = dati.scenariji.find(s => s.kods === kods), km = typeof krizesMeklesana !== 'undefined' ? krizesMeklesana : null;
    if (!sc) return;
    simIestatit(sc, sc.regionu_izvele ? (regions || sc.regionu_izvele[0]) : null);
    const s = SC_ID[kods] && km?.scenarijsPec(SC_ID[kods]);
    if (!km || !s || !sc.vaicajums) return;
    if (typeof atmestAdresi === 'function') atmestAdresi();
    if (typeof radtRegionu === 'function' && stavoklis.regions) radtRegionu('');
    if (sc.vieta) karte.setView([sc.vieta.lat, sc.vieta.lon], 11, { animate: false });
    el('jautajums').value = sc.vaicajums;
    rezultatsDemo = true;
    return km.meklet(sc.vaicajums, s);
  }

  // Simulētais brīdinājums tagad nāk no stāvokļa objekta (bridinajumi.js); šī josla paliek paslēpta
  function zimetJoslu(sc, r) {
    josla.hidden = true;
    return;
    const b = sc.bridinajums;
    if (!b) { josla.hidden = true; return; }
    const [klase, vards] = LIMENI[b.limenis];
    const lidz = Valoda.fmtDatums(new Date(Date.now() + (b.lidz_h || 6) * 3600e3), true);  // DD/MM/YYYY HH:MM visās valodās
    const kur = r ? r.nosaukums : (b.regioni || []).map(k => regioni[k]?.nosaukums).filter(Boolean).join(', ');
    josla.className = 'bridinajums demo-josla ' + klase;
    josla.innerHTML = `<details><summary>${ZIME} ${Ik('brid')} ${b.vards ? esc(b.vards) : vards + ' brīdinājums'}: ${esc(b.paradiba.toLowerCase())}` +
      `${kur ? ` (${esc(kur)})` : ''}, līdz ${lidz}</summary><p>${esc(b.teksts)}</p><p class="riski">${esc(b.riski)}</p>` +
      `<p class="avots-rinda">Šis brīdinājums ir izdomāts demo vajadzībām; īstie LVĢMC brīdinājumi parādās šeit, kad demo beidzas.</p></details>`;
    josla.hidden = false;
  }

  function zimetZonas(sc, robezas) {
    for (const z of sc.zonas || []) {
      const stils = { color: z.krasa, weight: 2, fillColor: z.krasa, fillOpacity: .25, dashArray: '8 6' };
      const teksts = `<div class="popup">${ZIME}<b>${esc(z.nosaukums)}</b><small>${esc(z.apraksts)}</small></div>`;
      if (z.tips === 'aplis') {
        const c = L.circle(z.centrs, { ...stils, radius: z.radiuss_m }).bindPopup(teksts)
          .bindTooltip(`SIMULĀCIJA · ${esc(z.nosaukums)}`, { sticky: true }).addTo(slanis);
        if (!z.arpus_skata) robezas.extend(c.getBounds());
      } else if (z.tips === 'sektors') {
        const p = L.polygon(sektors(z), { ...stils, fillOpacity: .3 }).bindPopup(teksts)
          .bindTooltip(`SIMULĀCIJA · ${esc(z.nosaukums)}`, { sticky: true }).addTo(slanis);
        if (!z.arpus_skata) robezas.extend(p.getBounds());
      } else if (z.tips === 'geojson') {
        fetch(z.url).then(r => r.ok ? r.json() : Promise.reject()).then(gj => {
          if (!aktivs || aktivs.sc !== sc) return;
          L.geoJSON(gj, { style: { ...stils, dashArray: null, fillOpacity: .3, weight: 1 } })
            .bindPopup(f => `<div class="popup">${ZIME}<b>${esc(z.nosaukums)}</b><small>${esc(f.feature.properties.apraksts || z.apraksts)}</small>` +
              `${gj.avots ? `<small class="popup-avots">Avots: ${avotaSaite(gj.avots)}</small>` : ''}</div>`)
            .addTo(slanis).bringToBack();
        }).catch(() => {
          const p = saturs.querySelector('.demo-zonu-kluda');
          if (p) p.hidden = false;
        });
      }
    }
    // celu_rezerve: simulētais ceļu slēgums tikai tad, ja īsto LVC notikumu nav (zimetRezervi pēc /api/celi atbildes)
    zimetLinijas(sc, robezas, x => !(sc.celi_lvc && x.celu_rezerve));
  }

  function zimetLinijas(sc, robezas, der) {
    for (const l of (sc.linijas || []).filter(der)) {
      L.polyline(l.koord, { color: '#b91c1c', weight: 7, opacity: .85, dashArray: '2 10', lineCap: 'round' })
        .bindTooltip('SIMULĀCIJA · ' + esc(l.nosaukums), { sticky: true }).addTo(slanis);
      robezas.extend(l.koord);
    }
    for (const m of (sc.markieri || []).filter(der)) {
      L.marker([m.lat, m.lon], { icon: ikona(m.ikona, 'demo-notikums') })
        .bindTooltip('SIMULĀCIJA · ' + esc(m.nosaukums)).addTo(slanis);
    }
  }
  const zimetRezervi = (sc, robezas) => zimetLinijas(sc, robezas, x => x.celu_rezerve);

  // ---- Ceļi tagad: īstie LVC notikumi (/api/celi, CC0) ap scenārija vietu ----
  // [] — spēkā esošu notikumu nav; null — avots neatbild 4 s laikā vai nav konfigurēts (atskaņošanas solis negaida ilgāk)
  async function celuNotikumi(sc, vieta) {
    const c = sc.celi_lvc;
    if (!c || !vieta) return null;
    const ctrl = new AbortController();
    const taimeris = setTimeout(() => ctrl.abort(), 4000);
    try {
      const d = await iegut('/celi?' + new URLSearchParams({ lat: vieta.lat, lon: vieta.lon, r: c.r_m || 30000 }), ctrl.signal);
      if (!d.konfigurets) return null;
      return (d.notikumi || []).filter(n => n.aktivs && (!c.tipi || c.tipi.includes(n.tips))).slice(0, c.max || 6);
    } catch { return null; } finally { clearTimeout(taimeris); }
  }
  const celuTips = n => (typeof Celi !== 'undefined' && Celi.TIPI?.[n.tips]) || { ikona: 'uzmanibu', krasa: '#b91c1c' };
  const celuPopups = n => typeof Celi !== 'undefined' && Celi.popups ? Celi.popups(n)
    : `<div class="popup"><b>${esc(n.nosaukums)}</b>${n.apraksts ? `<p>${esc(n.apraksts)}</p>` : ''}</div>`;

  function zimetCelus(notikumi, robezas) {
    for (const n of notikumi) {
      const t = celuTips(n);
      if (n.linija) L.polyline(n.linija, { color: t.krasa, weight: 6, opacity: .9 }).bindPopup(() => celuPopups(n)).addTo(slanis);
      L.marker([n.lat, n.lon], { icon: L.divIcon({ className: 'celu-ikona', html: `<span style="background:${t.krasa}">${Ik(t.ikona)}</span>`, iconSize: [44, 44], iconAnchor: [22, 22] }),
        title: n.nosaukums, zIndexOffset: 400 }).bindPopup(() => celuPopups(n)).addTo(slanis);
      if (n.attalums_m < 10000) robezas.extend([n.lat, n.lon]);
    }
  }

  function celuBloks(sc, notikumi) {
    const c = sc.celi_lvc, km = Math.round((c.r_m || 30000) / 1000) + ' km';
    if (notikumi?.length) {
      return `<h3>${Ik('slegts')} Ceļi tagad: īstie LVC dati</h3>` +
        `<p class="piezime">Šobrīd spēkā esoši notikumi ${km} rādiusā (nevis vētras dienā). Kartē — krāsainās līnijas.</p>` +
        '<ol class="rez-saraksts demo-celi">' + notikumi.map(n => `<li tabindex="0" data-lat="${n.lat}" data-lon="${n.lon}" data-teksts="${esc(celuPopups(n))}">
          <span class="teksts"><b>${Ik(celuTips(n).ikona)} ${esc(n.nosaukums)}${n.cels ? ' · ' + esc(n.cels) : ''}</b>
          ${n.apraksts ? `<small>${esc(n.apraksts)}</small>` : ''}</span><span class="attalums">${attalums(n.attalums_m)}</span></li>`).join('') +
        `</ol><p class="avots-rinda">Avots: ${avotaSaite(dati.avoti.celi || { nos: 'LVC, transportdata.gov.lv', licence: 'CC0' })}</p>`;
    }
    return `<p class="piezime demo-celi-rezerve">${Ik('uzmanibu')} Ceļi: ${notikumi ? `LVC datos ${km} rādiusā šobrīd nav slēgumu vai negadījumu`
      : 'LVC ceļu dati pašlaik nav pieejami'}, tāpēc kartē rādām ${esc(c.rezerve || 'ceļu slēgumu')}: <b>simulēts</b>.</p>`;
  }

  const avotaSaite = a => (a.url ? `<a href="${esc(a.url)}" target="_blank" rel="noopener">${esc(a.nos)}</a>` : esc(a.nos)) +
    (a.licence ? ' · ' + esc(a.licence) : '');

  // ---- Tuvākās vietas: īstie dati; zonu filtrs (ārpus zonas, prom no tās), pelēkotie (nestrādā), slēgtie ----
  async function tuvakie(kategorija, vieta, limit, regions) {
    if (!kategorijas[kategorija]?.skaits) return [];
    const q = { kategorijas: kategorija, lat: vieta.lat.toFixed(5), lon: vieta.lon.toFixed(5), limit };
    if (regions) q.regions = regions;
    try { return (await iegut('/objekti?' + new URLSearchParams(q))).features; } catch { return []; }
  }

  function vienums(f, vieta, virsraksts, piezime = '') {
    const p = f.properties;
    const [lat, lon] = ll(f);
    return `<li tabindex="0" data-lat="${lat}" data-lon="${lon}" data-p="${esc(JSON.stringify(p))}">
      <span class="teksts">${virsraksts ? `<span class="drosa-nos">${virsraksts}</span>` : ''}<b>${esc(nosaukums(p) || kategorijas[p.kategorija]?.nosaukums || '')}</b>
      <small>${esc(p.adrese || '')}</small>${piezime}${marsrutaSaites(lat, lon, vieta)}${Avoti.rinda(p.avots)}</span>
      <span class="attalums">${attalums(p.attalums_m)}</span></li>`;
  }
  const tuksa = (virsraksts, teksts) => `<li class="tuksa"><span class="teksts"><span class="drosa-nos">${virsraksts}</span><small>${teksts}</small></span></li>`;

  function atzimet(f, krasa = null, teksts = null) {
    const [lat, lon] = ll(f);
    const k = kategorijas[f.properties.kategorija] || {};
    const m = teksts
      ? L.marker([lat, lon], { icon: ikona(krasa, 'demo-pelekots') }).bindPopup(`<div class="popup">${ZIME}<b>${esc(teksts)}</b></div>` + popupSaturs(f.properties, { lat, lng: lon }))
      : L.marker([lat, lon], { icon: Ikonas.markeris(f.properties.kategorija, k.krasa, 30), title: nosaukums(f.properties) || k.nosaukums || '', zIndexOffset: 500 })
        .bindPopup(() => popupSaturs(f.properties, { lat, lng: lon }));
    m.addTo(slanis);
  }

  async function tuvakieBloki(sc, vieta, regions) {
    const punkti = [], dalas = [], marsruti = [];
    const zonas = sc.zonas || [];
    // Pelēkotie: punkti elektrības zonās nestrādā; sarakstā — tuvākais strādājošais ārpus zonām
    const pelekot = await Promise.all((sc.pelekot || []).map(async p => {
      const visi = await tuvakie(p.kategorija, vieta, 80);
      const iekšā = visi.filter(f => zonas.some(z => zonā(z, ll(f))));
      iekšā.forEach(f => atzimet(f, '✕', p.teksts));
      const strada = visi.find(f => !iekšā.includes(f));
      if (strada) { atzimet(strada); if (strada.properties.attalums_m < 30000) punkti.push(ll(strada)); }
      return strada ? vienums(strada, vieta, `${Ikonas.no(p.ikona)} ${esc(p.nos)}`, `<small class="tala">Tuvumā nestrādā: ${iekšā.length} (pelēkie ✕ kartē)</small>`)
        : tuksa(`${Ikonas.no(p.ikona)} ${esc(p.nos)}`, `Tuvākajos ${visi.length} nav neviena ārpus elektrības zonas.`);
    }));

    const saraksts = await Promise.all((sc.tuvakie || []).map(async t => {
      let visi = await tuvakie(t.kategorija, vieta, t.limit || 5);
      const arpus = zonas.filter(z => (t.arpus || []).includes(z.id));
      visi = visi.filter(f => !arpus.some(z => zonā(z, ll(f))));
      const prom = zonas.find(z => z.id === t.prom_no);
      // prom no zonas: patvertne, kas ir tālāk no zonas centra nekā Jūs (neved cauri zonai), citādi tuvākā ārpus tās
      const f = (prom && visi.find(f => metri(prom.centrs, ll(f)) > metri(prom.centrs, [vieta.lat, vieta.lon]) + 300)) || visi[0];
      const virsraksts = `${Ikonas.no(t.ikona)} ${esc(t.nos)}`;
      if (!f) return tuksa(virsraksts, 'Datos nav atrasta. Jautājiet pašvaldībai.');
      atzimet(f);
      if (f.properties.attalums_m < 30000 || t.linija) punkti.push(ll(f));
      // taisnā līnija — līdz ielādējas maršruts, kas apiet zonu (marsruts.js); ja maršrutētājs neatbild, tā paliek
      if (t.linija) marsruti.push({ uz: ll(f), linija: L.polyline([[vieta.lat, vieta.lon], ll(f)], { color: '#0077c8', weight: 4, dashArray: '8 8' }).addTo(slanis) });
      const tala = f.properties.attalums_m > 10000 && ['evakuacijas_punkts', 'izmitinasana'].includes(t.kategorija)
        ? '<small class="tala">Tuvākā mūsu datos ir tālu, citā pašvaldībā.</small>' : '';
      return vienums(f, vieta, virsraksts, (t.linija ? '<small class="marsruta-piezime">Zilā raustītā līnija: virziens taisnā līnijā; ejiet pa ielām.</small>' : '') + tala);
    }));
    if (pelekot.length + saraksts.length) {
      dalas.push(`<h3>${sc.pelekot ? 'Kas strādā tuvumā' : 'Tuvākās vietas'}</h3><ol class="rez-saraksts drosas">${[...pelekot, ...saraksts].join('')}</ol>`);
    }

    // Naktī slēgtās (aptiekas): pelēkas kartē un sarakstā
    if (sc.slegtas) {
      const s = sc.slegtas;
      const visi = (await tuvakie(s.kategorija, vieta, s.n));
      visi.forEach(f => atzimet(f, '✕', s.teksts));
      if (visi.length) dalas.push(`<h3>${esc(kategorijas[s.kategorija]?.nosaukums || '')} tuvumā</h3><ol class="rez-saraksts slegtas">` +
        visi.map(f => vienums(f, vieta, '', `<small class="tala">${esc(s.teksts)}</small>`)).join('') + '</ol>');
    }

    // Bez sakariem: reģiona dzīvā statusa slāņi pelēki ar "?"; saraksts, kur doties bez telefona
    if (sc.bez_sakariem && regions) {
      const b = sc.bez_sakariem;
      const nez = (await Promise.all(b.nezinams.map(k => tuvakie(k, vieta, 1500, regions)))).flat();
      for (const f of nez) {
        const [lat, lon] = ll(f);
        L.circleMarker([lat, lon], { radius: 6, color: '#57534e', weight: 1.5, dashArray: '2 2', fillColor: '#d6d3d1', fillOpacity: .9 })
          .bindPopup(`<div class="popup">${ZIME}<b>Status nezināms</b><small>Bez elektrības un sakariem nav zināms, vai ${esc((kategorijas[f.properties.kategorija]?.nosaukums || 'vieta').toLowerCase())} strādā.</small></div>` +
            popupSaturs({ ...f.properties, attalums_m: null }, { lat, lng: lon })).addTo(slanis);
      }
      const doties = await Promise.all(b.doties.map(async d => {
        let fs = await tuvakie(d.kategorija, vieta, d.n, regions);
        if (!fs.length) fs = await tuvakie(d.kategorija, vieta, 1);  // reģionā nav — tuvākā ārpus tā
        fs.forEach(f => atzimet(f));
        return fs.length ? fs.map((f, i) => vienums(f, null, i ? '' : `${Ikonas.no(d.ikona)} ${esc(d.nos)}`)).join('')
          : tuksa(`${Ikonas.no(d.ikona)} ${esc(d.nos)}`, 'Datos nav atrasta. Jautājiet pašvaldībai.');
      }));
      dalas.unshift(`<p class="piezime demo-legenda"><span class="demo-nez"></span> Pelēkie punkti (${nez.length}): aptiekas, bankomāti, DUS, upju posteņi, kuru stāvoklis nav zināms.</p>`);
      dalas.push(`<h3>Kur doties bez telefona</h3><ol class="rez-saraksts drosas">${doties.join('')}</ol>` +
        `<p class="piezime">Attālums taisnā līnijā no ${esc(regioni[regions]?.nosaukums || '')} centra.</p>`);
    }
    return { html: dalas.join(''), punkti, marsruti };
  }

  // ---- Kartīte "Kas notiek / Ko darīt" (meklēšanas rezultāta klases no stils.css) ----
  function karte_(sc, r, tuvakas) {
    const avoti = (sc.avoti || []).map(k => dati.avoti[k]).filter(Boolean);
    const regionuIzvele = sc.regionu_izvele ? `<label class="demo-regions">Teritorija bez elektrības un sakariem
      <select id="demo-regions">${sc.regionu_izvele.map(k => `<option value="${k}" ${r?.kods === k ? 'selected' : ''}>${esc(regioni[k]?.nosaukums || k)}</option>`).join('')}</select></label>` : '';
    return `<button type="button" class="otra demo-atpakal" data-darbiba="demo-saraksts">← Visi scenāriji</button>
      <article class="demo-kartite">
        <p class="demo-virsraksts">${ZIME}${sc.laiks ? `<span class="demo-laiks">${Ik('pulkstenis')} ${esc(sc.laiks)}</span>` : ''}</p>
        <h2>${Ikonas.no(sc.ikona)} ${esc(sc.nosaukums)}</h2>
        ${regionuIzvele}
        ${sc.draudi ? `<p class="draudi">${Ik('uzmanibu')} ${esc(sc.draudi)}</p>` : ''}
        ${sc.lemums ? `<p class="demo-lemums">${esc(sc.lemums)}</p>` : ''}
        ${sc.grupa === 'reals' ? `<p class="demo-reals">Reāls notikums: ${esc(sc.datums)}. Skaitļi — no avotiem zemāk; kartes zonas un notikumi — simulācija.</p>` : ''}
        <h3>${sc.grupa === 'reals' ? 'Kas notika' : 'Kas notiek'}</h3><ul class="demo-notiek">${sc.notiek.map(t => `<li>${esc(t)}</li>`).join('')}</ul>
        ${sc.redzetu ? `<h3>Ko Jūs redzētu šajā lietotnē</h3><ul class="demo-notiek demo-redzetu">${sc.redzetu.map(t => `<li>${esc(t)}</li>`).join('')}</ul>` : ''}
        <h3>Ko darīt</h3><ol class="padoms demo-darit">${sc.darit.map(t => `<li>${esc(t)}</li>`).join('')}</ol>
        ${sc.saites ? `<p class="demo-saites">${sc.saites.map(a => `<a class="otra-saite" href="${esc(a.url)}">${esc(a.nos)}</a>`).join('')}</p>` : ''}
        ${sc.zvanit112 && !sc.draudi ? '<p class="zvanit-teksts">Ja apdraudēta dzīvība vai veselība, zvaniet 112.</p>' : ''}
        ${(sc.zonas || []).some(z => z.tips === 'geojson') ? '<p class="piezime kluda demo-zonu-kluda" hidden>Reljefa slāni neizdevās ielādēt.</p>' : ''}
        ${tuvakas}
        ${sc.fakti ? `<h3>${sc.grupa === 'reals' ? 'Skaitļi un avoti' : 'Reālie skaitļi'}</h3><ul class="fakti">${sc.fakti.map(f => `<li><span class="ikona">${Ikonas.no(f.ikona)}</span><div><b>${esc(f.virsraksts)}</b>
          <span>${esc(f.teksts)}</span><small class="avots-rinda">Avots: ${avotaSaite(f.avots)}</small></div></li>`).join('')}</ul>` : ''}
        ${sc.druka ? '<button type="button" class="otra demo-druka" data-darbiba="drukat">' + Ik('drukat') + ' Drukāt vai saglabāt PDF (bezsaistei)</button>' : ''}
        <p class="avots-rinda demo-avoti">Simulēts: ${sc.bridinajums ? 'brīdinājums, ' : ''}notikumi${sc.zonas || sc.linijas ? ', zonas kartē' : ''}.
          Dati: ${avoti.map(avotaSaite).join('; ')}.</p>
      </article>` + beigtPoga();
  }

  // ?demo=<kods>: atver scenāriju, kad kartes kategorijas un reģioni ielādēti (app.js)
  const q = new URLSearchParams(location.search);
  if (q.get('demo')) {
    const sakums = Date.now();
    (function gaidit() {
      if (Object.keys(kategorijas).length && Object.keys(regioni).length) sakt(q.get('demo'), q.get('regions'));
      else if (Date.now() - sakums < 10000) setTimeout(gaidit, 200);
      else sakt(q.get('demo'), q.get('regions'));
    })();
  }

  // Paneļa secība (atskanot.js atskaņo tieši tādā): reālie notikumi pēc veida, tad simulācijas
  const kartiba = async () => (dati || await ieladet()) ? [...reali(), ...simulacijas()] : [];

  return { sakt, beigt, rezultats, atvert, kartiba, atstarpes };
})();
