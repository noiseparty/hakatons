// Demo panelis (labā mala; telefonā — apakšā): simulēti krīzes scenāriji, kas maina karti. Dati: demo/scenariji.json.
// Viss, ko scenārijs ieliek (brīdinājums, zonas, notikumi), ir ar zīmi SIMULĀCIJA; tuvākās vietas — īstie dati no /api/objekti.
// "Beigt demo" atjauno slāņus, plūdu slāni un kartes skatu. Saite ?demo=<kods>[&regions=<kods>] atver scenāriju uzreiz.
// Lieto app.js globālos (karte, stavoklis, kategorijas, regioni, iegut, atjaunot, kopsavilkumi, statuss, radtPludus,
// popupSaturs, marsrutaSaites, attalums, nosaukums, esc, el); app.js netiek mainīts.
const Demo = (() => {
  const LIMENI = { 1: ['dzeltens', 'Dzeltenais', '#eab308'], 2: ['oranzs', 'Oranžais', '#ea580c'], 3: ['sarkans', 'Sarkanais', '#b91c1c'] };
  const telefons = () => matchMedia('(max-width: 800px)').matches;
  const ZIME = '<span class="demo-zime">SIMULĀCIJA</span>';
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
    <aside id="demo-panelis" aria-label="Demo scenāriji">
      <div class="demo-galva"><b>Demo scenāriji</b>${ZIME}
        <button type="button" class="demo-aizvert" aria-label="Aizvērt demo paneli">✕</button></div>
      <div id="demo-saturs"></div>
    </aside>`);
  el('bridinajums').insertAdjacentHTML('afterend', '<div id="demo-josla" class="bridinajums demo-josla" role="status" hidden></div>');
  const panelis = el('demo-panelis'), saturs = el('demo-saturs'), josla = el('demo-josla');

  function atvert(atverts) {
    const bija = document.body.classList.contains('demo-atverts');
    document.body.classList.toggle('demo-atverts', atverts);
    el('demo-cilne').setAttribute('aria-expanded', atverts);
    if (atverts && !dati) ieladet().then(zimetSarakstu);
    // telefonā panelis aizsedz kartes apakšu: pēc atvēršanas/aizvēršanas scenārija vietu rāda vēlreiz
    if (aktivs && bija !== atverts && telefons()) setTimeout(radit, 300);
  }
  el('demo-cilne').addEventListener('click', () => atvert(!document.body.classList.contains('demo-atverts')));
  panelis.querySelector('.demo-aizvert').addEventListener('click', () => atvert(false));
  document.addEventListener('keydown', e => { if (e.key === 'Escape' && document.body.classList.contains('demo-atverts')) atvert(false); });

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
    saturs.innerHTML = `<p class="piezime">Izdomāti krīzes gadījumi prezentācijai. Brīdinājumi, zonas un notikumi ir simulēti;
      tuvākās vietas, maršruti un avoti ir īstie kartes dati.</p>
      <ul class="demo-saraksts">${dati.scenariji.map(s => `<li><button type="button" data-demo="${esc(s.kods)}"
        ${aktivs?.sc.kods === s.kods ? 'aria-current="true"' : ''}><span class="demo-ikona-l">${s.ikona}</span>
        <span><b>${esc(s.nosaukums)}</b><small>${esc(s.isi)}</small></span></button></li>`).join('')}</ul>` +
      (aktivs ? beigtPoga() : '');
  }
  const beigtPoga = () => '<button type="button" class="galvena demo-beigt" data-darbiba="beigt">■ Beigt demo, rādīt īsto karti</button>';

  saturs.addEventListener('click', e => {
    const b = e.target.closest('button');
    const kods = b?.dataset.demo;
    if (kods) sakt(kods);
    if (b?.dataset.darbiba === 'beigt') beigt();
    if (b?.dataset.darbiba === 'saraksts') zimetSarakstu();
    if (b?.dataset.darbiba === 'drukat') print();
    const li = e.target.closest('li[data-lat]');
    if (li && !e.target.closest('a')) {
      const ll = { lat: +li.dataset.lat, lng: +li.dataset.lon };
      karte.setView(ll, Math.max(karte.getZoom(), 15));
      L.popup().setLatLng(ll).setContent(li.dataset.p ? popupSaturs(JSON.parse(li.dataset.p), ll) : li.dataset.teksts).openOn(karte);
      if (telefons()) atvert(false);
    }
  });
  saturs.addEventListener('change', e => { if (e.target.id === 'demo-regions' && aktivs) sakt(aktivs.sc.kods, e.target.value); });
  saturs.addEventListener('keydown', e => { if (e.key === 'Enter' && e.target.matches('li[data-lat]')) e.target.click(); });

  // ---- Ģeometrija ----
  function metri(a, b) {
    const r = Math.PI / 180, dLat = (b[0] - a[0]) * r, dLon = (b[1] - a[1]) * r;
    const h = Math.sin(dLat / 2) ** 2 + Math.cos(a[0] * r) * Math.cos(b[0] * r) * Math.sin(dLon / 2) ** 2;
    return Math.round(2 * 6371000 * Math.asin(Math.sqrt(h)));
  }
  const zonā = (zona, ll) => zona.tips === 'aplis' && metri(zona.centrs, ll) <= zona.radiuss_m;
  const ll = f => [f.geometry.coordinates[1], f.geometry.coordinates[0]];
  const ikona = (teksts, klase = '') => L.divIcon({ html: `<span>${teksts}</span>`, className: 'demo-ikona ' + klase, iconSize: [30, 30] });

  // Kartes laukums, ko neaizsedz panelis (labajā malā vai telefonā apakšā)
  function atstarpes() {
    if (!document.body.classList.contains('demo-atverts')) return { padding: [40, 40] };
    return telefons()
      ? { paddingTopLeft: [20, 20], paddingBottomRight: [20, panelis.offsetHeight + 20] }
      : { paddingTopLeft: [30, 30], paddingBottomRight: [panelis.offsetWidth + 30, 30] };
  }

  // ---- Scenārija sākšana un beigšana ----
  async function sakt(kods, regions) {
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
    document.body.classList.add('demo-aktivs');
    el('demo-karte-zime').hidden = false;
    atvert(true);
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
    radtPludus(!!sc.pludi || saglabats.pludi);

    const r = regions ? regioni[regions] : null;
    const vieta = sc.vieta || (r && { lat: (r.bbox[1] + r.bbox[3]) / 2, lon: (r.bbox[0] + r.bbox[2]) / 2, nosaukums: r.nosaukums + ', centrs' });
    zimetJoslu(sc, r);
    saturs.innerHTML = karte_(sc, r, '<p class="piezime">Ielādē tuvākās vietas…</p>');
    saturs.scrollTop = 0;
    karte.invalidateSize();

    const robezas = L.latLngBounds([]);
    if (vieta) {
      robezas.extend([vieta.lat, vieta.lon]);
      L.marker([vieta.lat, vieta.lon], { icon: ikona('📍', 'demo-es'), zIndexOffset: 1000 })
        .bindTooltip(esc(vieta.nosaukums), { permanent: true, direction: 'top', offset: [0, -14] }).addTo(slanis);
    }
    zimetZonas(sc, robezas);

    // Brīdinājuma reģioni (VZD robežas) vai izvēlētais reģions bez sakariem
    const regionuKodi = regions ? [regions] : sc.bridinajums?.regioni || [];
    const [regionuGj, bloki] = await Promise.all([
      Promise.all(regionuKodi.map(k => iegut('/regioni/' + k).catch(() => null))),
      tuvakieBloki(sc, vieta, regions),
    ]);
    if (mana !== paaudze) return;
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
  const radit = () => { if (aktivs && skats?.isValid()) karte.fitBounds(skats, { maxZoom: 15, ...atstarpes() }); };
  // app.js: slāņu izvēles rūtiņas un grupu skaiti panelī
  function raditSlanus() {
    document.querySelectorAll('#kategorijas input').forEach(i => { i.checked = stavoklis.kategorijas.has(i.value); });
    kopsavilkumi();
  }

  function beigt() {
    paaudze++;
    aktivs = null;
    skats = null;
    slanis.clearLayers();
    slanis.remove();
    document.body.classList.remove('demo-aktivs');
    el('demo-karte-zime').hidden = true;
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

  // ---- Simulētā brīdinājuma josla (īstā LVĢMC josla demo laikā paslēpta, demo.css) ----
  function zimetJoslu(sc, r) {
    const b = sc.bridinajums;
    if (!b) { josla.hidden = true; return; }
    const [klase, vards] = LIMENI[b.limenis];
    const lidz = new Date(Date.now() + (b.lidz_h || 6) * 3600e3)
      .toLocaleString('lv-LV', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' });
    const kur = r ? r.nosaukums : (b.regioni || []).map(k => regioni[k]?.nosaukums).filter(Boolean).join(', ');
    josla.className = 'bridinajums demo-josla ' + klase;
    josla.innerHTML = `<details><summary>${ZIME} ⚠ ${b.vards ? esc(b.vards) : vards + ' brīdinājums'}: ${esc(b.paradiba.toLowerCase())}` +
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
    for (const l of sc.linijas || []) {
      L.polyline(l.koord, { color: '#b91c1c', weight: 7, opacity: .85, dashArray: '2 10', lineCap: 'round' })
        .bindTooltip('SIMULĀCIJA · ' + esc(l.nosaukums), { sticky: true }).addTo(slanis);
      robezas.extend(l.koord);
    }
    for (const m of sc.markieri || []) {
      L.marker([m.lat, m.lon], { icon: ikona(m.ikona, 'demo-notikums') })
        .bindTooltip('SIMULĀCIJA · ' + esc(m.nosaukums)).addTo(slanis);
    }
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
      : L.circleMarker([lat, lon], { radius: 11, color: '#1c1917', weight: 3, fillColor: k.krasa || '#57534e', fillOpacity: 1 })
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
      return strada ? vienums(strada, vieta, `${p.ikona} ${esc(p.nos)}`, `<small class="tala">Tuvumā nestrādā: ${iekšā.length} (pelēkie ✕ kartē)</small>`)
        : tuksa(`${p.ikona} ${esc(p.nos)}`, `Tuvākajos ${visi.length} nav neviena ārpus elektrības zonas.`);
    }));

    const saraksts = await Promise.all((sc.tuvakie || []).map(async t => {
      let visi = await tuvakie(t.kategorija, vieta, t.limit || 5);
      const arpus = zonas.filter(z => (t.arpus || []).includes(z.id));
      visi = visi.filter(f => !arpus.some(z => zonā(z, ll(f))));
      const prom = zonas.find(z => z.id === t.prom_no);
      // prom no zonas: patvertne, kas ir tālāk no zonas centra nekā Jūs (neved cauri zonai), citādi tuvākā ārpus tās
      const f = (prom && visi.find(f => metri(prom.centrs, ll(f)) > metri(prom.centrs, [vieta.lat, vieta.lon]) + 300)) || visi[0];
      const virsraksts = `${t.ikona} ${esc(t.nos)}`;
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
        return fs.length ? fs.map((f, i) => vienums(f, null, i ? '' : `${d.ikona} ${esc(d.nos)}`)).join('')
          : tuksa(`${d.ikona} ${esc(d.nos)}`, 'Datos nav atrasta. Jautājiet pašvaldībai.');
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
    return `<button type="button" class="otra demo-atpakal" data-darbiba="saraksts">← Visi scenāriji</button>
      <article class="demo-kartite">
        <p class="demo-virsraksts">${ZIME}${sc.laiks ? `<span class="demo-laiks">🕒 ${esc(sc.laiks)}</span>` : ''}</p>
        <h2>${sc.ikona} ${esc(sc.nosaukums)}</h2>
        ${regionuIzvele}
        ${sc.draudi ? `<p class="draudi">⚠ ${esc(sc.draudi)}</p>` : ''}
        <h3>Kas notiek</h3><ul class="demo-notiek">${sc.notiek.map(t => `<li>${esc(t)}</li>`).join('')}</ul>
        <h3>Ko darīt</h3><ol class="padoms demo-darit">${sc.darit.map(t => `<li>${esc(t)}</li>`).join('')}</ol>
        ${sc.zvanit112 && !sc.draudi ? '<p class="zvanit-teksts">Ja apdraudēta dzīvība vai veselība, zvaniet 112.</p>' : ''}
        ${(sc.zonas || []).some(z => z.tips === 'geojson') ? '<p class="piezime kluda demo-zonu-kluda" hidden>Reljefa slāni neizdevās ielādēt.</p>' : ''}
        ${tuvakas}
        ${sc.fakti ? `<h3>Reālie skaitļi</h3><ul class="fakti">${sc.fakti.map(f => `<li><span class="ikona">${f.ikona}</span><div><b>${esc(f.virsraksts)}</b>
          <span>${esc(f.teksts)}</span><small class="avots-rinda">Avots: ${avotaSaite(f.avots)}</small></div></li>`).join('')}</ul>` : ''}
        ${sc.druka ? '<button type="button" class="otra demo-druka" data-darbiba="drukat">🖨 Drukāt vai saglabāt PDF (bezsaistei)</button>' : ''}
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

  return { sakt, beigt, atvert };
})();
