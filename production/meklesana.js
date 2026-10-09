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
  const AVOTI_LVGMC = {
    pludi: '<a href="https://data.gov.lv/dati/lv/dataset/3-cikla-latvijas-pldu-postjumu-vietu-un-pldu-riska-kartes1" target="_blank" rel="noopener">LVĢMC plūdu riska kartes 2026–2031</a> · CC0',
    udens: '<a href="https://data.gov.lv/dati/lv/dataset/hidrometeorologiskie-noverojumi" target="_blank" rel="noopener">LVĢMC hidroloģiskie novērojumi</a> · CC0',
  };
  let klasifikators = null;
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
    } catch {
      el('jautajums').disabled = true;
      el('jautajums').placeholder = 'Meklēšana nav pieejama';
      return;
    }
    const q = new URLSearchParams(location.search).get('q');
    if (q) { el('jautajums').value = q; meklet(q); raditRezultatus(); }
  }

  el('meklet-forma').addEventListener('submit', e => {
    e.preventDefault();
    const teksts = el('jautajums').value.trim();
    if (teksts) { meklet(teksts); raditRezultatus(); } else notirit();
  });

  // Telefonā rezultāti ir zem kartes (un panelis var būt aizvērts): atveram to un ritinām līdz rezultātiem
  function raditRezultatus() {
    if (!matchMedia('(max-width: 800px)').matches) return;
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
    if (li && !e.target.closest('a')) {
      const ll = { lat: +li.dataset.lat, lng: +li.dataset.lon };
      karte.setView(ll, Math.max(karte.getZoom(), 16));
      L.popup().setLatLng(ll).setContent(popupSaturs(JSON.parse(li.dataset.p), ll)).openOn(karte);
    }
  });

  function notirit() {
    pedejais = null;
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
    let rez = klasifikators.klasificet(teksts);
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
        rez = klasifikators.klasificet(adrese.atlikums);
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
    bridinajumi(no, no?.nosaukums);

    const [galvenais, ...citi] = rez.scenariji;
    const kurTeksts = adrese ? isaAdrese(adrese.adrese) : vieta?.nosaukums;
    const galva = draudi +
      (galvenais
        ? `<p class="sapratu">${galvenais.nr ? 'Situācija' : 'Meklēju'}: <b>${esc(galvenais.nosaukums)}</b>${kurTeksts ? ' · ' + esc(kurTeksts) : ''}</p>` +
          (galvenais.padoms ? `<p class="padoms">${esc(galvenais.padoms)}</p>` : '')
        : kurTeksts ? `<p class="sapratu">${adrese ? 'Adrese' : 'Vieta'}: <b>${esc(kurTeksts)}</b></p>` +
            '<p class="piezime">Uzrakstiet arī, kas notiek, piem., „plūdi”, „nav elektrības”, „evakuācija”.</p>' : '') +
      zvanitTeksts +
      (bezDatiem ? '<p class="piezime kluda">Kartes dati pašlaik nav pieejami: tuvākās vietas nevaram parādīt. Padoms un 112 ir spēkā.</p>' : '');
    const vaiDomaji = citi.length ? `<p class="piezime">Vai domājāt:</p><div class="atras-pogas">` +
      citi.map(s => `<button type="button" data-cits="${esc(s.kods)}">${esc(s.nosaukums)}</button>`).join('') + '</div>' : '';
    const beigas = vaiDomaji + notiritPoga();

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
    const pludi = galvenais && PLUDU_SCENARIJI.has(galvenais.kods);
    if (kodi.length) {
      stavoklis.kategorijas = new Set(kodi);
      document.querySelectorAll('#kategorijas input').forEach(i => { i.checked = stavoklis.kategorijas.has(i.value); });
    }
    if (pludi) radtPludus(true);  // app.js: plūdu riska zonu slānis kartē
    if (kodi.length || jaunsRegions) atjaunot();

    if (!no) {
      kaste.innerHTML = galva + `<p class="piezime vieta-zina">Lai atrastu tuvākās vietas, pievienojiet adresi vai pilsētu, piem.,
        „${esc(teksts)} Ogrē” vai „${esc(teksts)} Brīvības 15 Ogre”, vai nosakiet savu atrašanās vietu.</p>
        <button type="button" class="galvena" data-darbiba="atrast"><span aria-hidden="true">📍</span> Noteikt manu atrašanās vietu</button>` + beigas;
      return;
    }

    kaste.innerHTML = galva + '<p class="piezime">Meklē tuvākās vietas…</p>';
    const ll = { lat: no.lat.toFixed(5), lon: no.lon.toFixed(5) };
    const tuvakas = (k, n) => iegut('/objekti?' + new URLSearchParams({ kategorijas: k, ...ll, limit: n }), signal)
      .catch(e => { if (e.name === 'AbortError') throw e; return { features: [] }; });
    try {
      const [grupas, drosasF] = await Promise.all([
        Promise.all(kodi.map(k => tuvakas(k, UZ_KATEGORIJU * 2))),
        Promise.all(drosas.map(d => kategorijas[d.kods]?.skaits ? tuvakas(d.kods, 5) : { features: [] })),
      ]);
      grupas.forEach(g => { g.features = izveleties(g.features); });
      const drosasVietas = drosasF.map(g => izveleties(g.features)[0] || null);
      kaste.innerHTML = galva +
        (pludi ? pluduBloks() : '') +
        kodi.map((k, i) => grupa(k, grupas[i].features, no)).join('') +
        (drosas.length ? drosasBloks(drosas, drosasVietas, no) : '') +
        '<p class="piezime">Attālums taisnā līnijā ' + esc(no.apraksts) + '.</p>' + beigas;
      zimetKarte([...grupas.map(g => g.features), ...drosasVietas.filter(Boolean).map(f => [f])], no, vieta);
      if (pludi) pluduDati(ll, signal);
    } catch (e) {
      if (e.name !== 'AbortError') kaste.innerHTML = galva + '<p class="piezime kluda">Vietas neizdevās ielādēt. Mēģiniet vēlreiz pēc brīža.</p>' + beigas;
    }
  }

  // Specializētās slimnīcas (dzemdību nams, psihiatrija; ipasibas.specializeta) pēc vispārējām, citādi pēc attāluma.
  const izveleties = features => features
    .map((f, i) => ({ f, i, spec: f.properties.ipasibas?.specializeta ? 1 : 0 }))
    .sort((a, b) => a.spec - b.spec || a.i - b.i).slice(0, UZ_KATEGORIJU).map(x => x.f);

  const notiritPoga = () => '<button type="button" class="otra" data-darbiba="notirit"><span aria-hidden="true">✕</span> Notīrīt meklēšanu</button>';

  function vienums(f, no, virsraksts) {
    // attālums no reģiona centra nav "no tevis", tāpēc uznirstošajā logā to nerādām
    const p = no.regions ? { ...f.properties, attalums_m: null } : f.properties;
    const i = p.ipasibas || {};
    const [lon, lat] = f.geometry.coordinates;
    const ca = (i.komentars ? `<small class="ca-avots">${esc(i.komentars)}</small>` : i.vietas ? `<small>${esc(i.vietas)} vietas</small>` : '') +
      (/^https?:\/\//.test(i.plans_url || '') ? `<small><a href="${esc(i.plans_url)}" target="_blank" rel="noopener">Atvērt CA plānu${i.lpp ? ` (lpp. ${esc(i.lpp)})` : ''}</a></small>` : '');
    return `<li tabindex="0" data-lat="${lat}" data-lon="${lon}" data-p="${esc(JSON.stringify(p))}">
      <span class="teksts">${virsraksts || ''}<b>${esc(nosaukums(p) || kategorijas[p.kategorija]?.nosaukums || '')}</b><small>${esc(p.adrese || '')}</small>${ca}${marsrutaSaites(lat, lon, no.regions ? null : no)}</span>
      <span class="attalums">${attalums(f.properties.attalums_m)}</span></li>`;
  }

  function grupa(kods, features, no) {
    const k = kategorijas[kods];
    if (!features.length) return '';
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

  // Plūdu scenārijiem: plūdu riska zona adresē (LVĢMC WMS caur /api/pludi; lēns, līdz 15 s) un tuvākās upes līmenis
  function pluduBloks() {
    return `<ul class="fakti" id="rez-pludi-bloks">
      <li id="rez-pludi"><span class="ikona" aria-hidden="true">🌊</span><div><b>Plūdu riska zona</b><span>Pārbauda… (līdz 15 s)</span></div></li>
      <li id="rez-udens"><span class="ikona" aria-hidden="true">📏</span><div><b>Tuvākā upe vai ezers</b><span>Ielādē…</span></div></li></ul>`;
  }
  function pluduRinda(id, saturs) { const li = kaste.querySelector('#' + id); if (li) li.querySelector('div').innerHTML = saturs; }
  function pluduDati(ll, signal) {
    iegut('/pludi?' + new URLSearchParams(ll), signal).then(p => {
      const t = p.zona
        ? `<strong class="jā">Jā</strong>: ${p.veidi.map(v => `${esc(v.veids)} (${String(v.varbutiba_proc).replace('.', ',')} % varbūtība gadā)`).join(', ')}`
        : p.nepilnigi ? 'Pēc pieejamajām kartēm nē, bet daļa karšu neatbildēja.' : '<strong class="nē">Nē</strong>: nav applūstošā teritorijā (10 %, 1 % un 0,5 % kartes).';
      pluduRinda('rez-pludi', `<b>Plūdu riska zona</b><span>${t}</span><small class="avots-rinda">${AVOTI_LVGMC.pludi}</small>`);
    }).catch(e => {
      if (e.name !== 'AbortError') pluduRinda('rez-pludi', '<b>Plūdu riska zona</b><span>Neizdevās pārbaudīt. Plūdu zonas redzamas kartē (slānis ieslēgts).</span>');
    });
    iegut('/udens?' + new URLSearchParams({ ...ll, limit: 1 }), signal).then(d => {
      const s = d.stacijas[0];
      if (!s) throw new Error('nav');
      const izm = s.izmaina_24h_cm;
      const tend = izm == null ? '' : izm > 0 ? `, 24 h: ↑ +${izm} cm` : izm < 0 ? `, 24 h: ↓ −${Math.abs(izm)} cm` : ', 24 h: nemainās';
      const laiks = new Date(s.laiks).toLocaleString('lv-LV', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' });
      pluduRinda('rez-udens', `<b>Tuvākā upe vai ezers</b><span>${esc(s.nosaukums)} (${attalums(s.attalums_m)}): ${s.limenis_cm} cm${tend}` +
        `${s.vecs ? ' — dati novecojuši' : ''}</span><small>Mērīts ${laiks}. Bīstamības līmeņi nav atvērtie dati.</small><small class="avots-rinda">${AVOTI_LVGMC.udens}</small>`);
    }).catch(e => {
      if (e.name !== 'AbortError') pluduRinda('rez-udens', '<b>Tuvākā upe vai ezers</b><span>Ūdens līmeņa datus neizdevās ielādēt.</span>');
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
    karte.fitBounds(L.latLngBounds(punkti), { padding: [40, 40], maxZoom: 15 });
  }

  // Enter rezultātu sarakstā = klikšķis
  kaste.addEventListener('keydown', e => { if (e.key === 'Enter' && e.target.matches('li[data-lat]')) e.target.click(); });

  return { sakt, atkartot, meklet, vietaNav };
})();
