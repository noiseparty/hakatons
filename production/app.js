// map.repo.lv: karte ar filtriem. Dati no /api (src/karte/api/karte_api.py, Postgres `map` uz VPS).
const API = '/api';
const GRUPAS = { patvertnes: 'Patvertnes', veseliba: 'Veselība', infrastruktura: 'Infrastruktūra', vide: 'Vide un ūdeņi', transports: 'Transports', incidenti: 'Incidenti' };

const latvija = L.latLngBounds([55.6, 20.8], [58.15, 28.3]);
const karte = L.map('karte', { maxBounds: latvija.pad(0.3), minZoom: 6, preferCanvas: true, zoomControl: false }).fitBounds(latvija);
const pamatkartes = {
  karte: L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19, crossOrigin: true,  // CORS: sw.js flīzes saglabā bezsaistei
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> līdzstrādnieki'
  }),
  // reljefs (augstumi, upju ielejas): OSM dati + SRTM, atvērta licence (Esri satelītattēli nav atvērtie dati)
  reljefs: L.tileLayer('https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png', {
    maxZoom: 17, crossOrigin: true,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> līdzstrādnieki, SRTM · stils &copy; <a href="https://opentopomap.org">OpenTopoMap</a> (CC BY-SA)'
  })
};
// Ja fona attēli neielādējas (nav interneta, serviss nepieejams) — skaidrs paziņojums, nevis pelēks laukums
let flizesIeladetas = false, flizuKludas = 0;
for (const slanis of Object.values(pamatkartes)) {
  slanis.on('tileload', () => { flizesIeladetas = true; });
  slanis.on('tileerror', () => {
    if (++flizuKludas !== 8 || flizesIeladetas) return;
    el('kartes-kluda').textContent = 'Kartes fona attēli neielādējas. Pārbaudiet interneta savienojumu; punkti un meklēšana strādā arī bez fona.';
    el('kartes-kluda').hidden = false;
  });
}
pamatkartes.karte.addTo(karte);
L.control.scale({ imperial: false, position: 'bottomleft' }).addTo(karte);

const el = id => document.getElementById(id);

// ---- Kartes vadība (tuvināšana, pamatkarte, panelis mobilajā) ----
el('tuvinat').addEventListener('click', () => karte.zoomIn());
el('talinat').addEventListener('click', () => karte.zoomOut());
el('mana-vieta').addEventListener('click', () => atrastMani());
document.querySelectorAll('[data-pamats]').forEach(b => b.addEventListener('click', () => {
  for (const [kods, slanis] of Object.entries(pamatkartes)) {
    if (kods === b.dataset.pamats) slanis.addTo(karte); else slanis.remove();
  }
  document.querySelectorAll('[data-pamats]').forEach(x => {
    x.classList.toggle('aktiva', x === b);
    x.setAttribute('aria-pressed', x === b);
  });
}));
el('panelis-poga').addEventListener('click', () => {
  const atverts = !document.body.classList.toggle('panelis-slegts');
  el('panelis-poga').setAttribute('aria-expanded', atverts);
  setTimeout(() => karte.invalidateSize(), 200);
});
// Telefonā filtru panelis sākumā aizvērts: karte visā augstumā; meklēšanas rezultāti to atver (meklesana.js)
if (matchMedia('(max-width: 800px)').matches) {
  document.body.classList.add('panelis-slegts');
  el('panelis-poga').setAttribute('aria-expanded', 'false');
}
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const statuss = (t, kluda) => { el('statuss').textContent = t; el('statuss').classList.toggle('kluda', !!kluda); };

const stavoklis = { vieta: null, regions: '', kategorijas: new Set() };
let kategorijas = {};
let regioni = {};
// Tālinot punkti apvienojas grupās: jo tālāk, jo lielākā rādiusā (px), lai kartē nav juceklis.
// Grupas aplis rāda skaitu un slāņu krāsu proporcijas; pilsētā (no 13) — atsevišķi punkti.
const objektuSlanis = L.markerClusterGroup({
  maxClusterRadius: z => z <= 8 ? 110 : z <= 10 ? 60 : z <= 11 ? 40 : 25,
  disableClusteringAtZoom: 13,
  showCoverageOnHover: false,
  spiderfyOnMaxZoom: false,
  chunkedLoading: true,
  iconCreateFunction: grupasIkona
}).addTo(karte);
let robezaSlanis = null;
let vietasSlanis = null;
let tuvakaSlanis = null;
let pieprasijums = null;
let redzamie = [];  // pēdējā ielāde; pa tiem meklē meklēšanas lauks

async function iegut(cels, signal, prioritate) {
  const r = await fetch(API + cels, prioritate ? { signal, priority: prioritate } : { signal });
  if (!r.ok) throw new Error(r.status);
  return r.json();
}

function grupasIkona(grupa) {
  const skaiti = {};
  for (const m of grupa.getAllChildMarkers()) skaiti[m.options.fillColor] = (skaiti[m.options.fillColor] || 0) + 1;
  const n = grupa.getChildCount();
  let lidz = 0;
  const dalas = Object.entries(skaiti).sort((a, b) => b[1] - a[1])
    .map(([krasa, k]) => `${krasa} ${lidz}deg ${lidz += k / n * 360}deg`).join(', ');
  const izmers = n < 10 ? 30 : n < 100 ? 36 : n < 1000 ? 44 : 52;
  return L.divIcon({
    html: `<span style="background:conic-gradient(${dalas})"><b>${n < 10000 ? n : Math.round(n / 1000) + 'k'}</b></span>`,
    className: 'grupa-ikona', iconSize: [izmers, izmers]
  });
}

// Maršruts līdz vietai: Google Maps un Waze ņem tālruņa atrašanās vietu paši; OSM (ar kājām) — no manas vietas, ja zināma.
function marsrutaSaites(lat, lon, no) {
  const [x, y] = [(+lat).toFixed(6), (+lon).toFixed(6)];
  const saites = [
    ['Google Maps', `https://www.google.com/maps/dir/?api=1&destination=${x}%2C${y}`],
    ['Waze', `https://www.waze.com/ul?ll=${x}%2C${y}&navigate=yes`],
    ['OSM', `https://www.openstreetmap.org/directions?engine=fossgis_osrm_foot&route=${no ? `${no.lat}%2C${no.lon}` : ''}%3B${x}%2C${y}`]
  ];
  return '<span class="marsruts"><span>Maršruts:</span>' +
    saites.map(([nos, url]) => `<a href="${url}" target="_blank" rel="noopener">${nos}</a>`).join('') + '</span>';
}

function attalums(m) {
  if (m == null) return '';
  return m < 1000 ? m + ' m' : (m / 1000).toFixed(m < 10000 ? 1 : 0).replace('.', ',') + ' km';
}

// ---- Atrašanās vieta ----
function atrastMani(pecTam) {
  const teksts = el('vieta-teksts');
  if (!('geolocation' in navigator)) { teksts.textContent = 'Šis pārlūks nevar noteikt atrašanās vietu. Izvēlieties reģionu zemāk.'; return; }
  el('atrast').disabled = true;
  teksts.textContent = 'Nosaka atrašanās vietu…';
  navigator.geolocation.getCurrentPosition(poz => {
    el('atrast').disabled = false;
    const { latitude: lat, longitude: lon, accuracy } = poz.coords;
    if (!latvija.pad(0.3).contains([lat, lon])) {
      teksts.textContent = 'Jūs atrodaties ārpus Latvijas, tāpēc attālumus nerādām. Izvēlieties reģionu zemāk.';
      return;
    }
    stavoklis.vieta = { lat, lon };
    if (vietasSlanis) vietasSlanis.remove();
    vietasSlanis = L.layerGroup([
      L.circle([lat, lon], { radius: accuracy, color: '#1d4ed8', weight: 1, fillOpacity: .08, interactive: false }),
      L.circleMarker([lat, lon], { radius: 8, color: '#fff', weight: 3, fillColor: '#1d4ed8', fillOpacity: 1 }).bindTooltip('Tu esi šeit')
    ]).addTo(karte);
    el('atrast').textContent = '📍 Atjaunot manu atrašanās vietu';
    teksts.textContent = 'Meklēšanas rezultāti sakārtoti pēc attāluma no Jums (taisnā līnijā).';
    if (tuvakaSlanis) { tuvakaSlanis.remove(); tuvakaSlanis = null; }
    if (!stavoklis.regions && !pecTam) karte.setView([lat, lon], 13);
    atjaunot();
    krizesMeklesana.atkartot();  // meklesana.js
    if (pecTam) pecTam();
  }, kluda => {
    el('atrast').disabled = false;
    teksts.textContent = kluda.code === kluda.PERMISSION_DENIED
      ? 'Atrašanās vieta nav atļauta. Izvēlieties reģionu vai pilsētu zemāk (vai atļaujiet to pārlūka iestatījumos).'
      : 'Neizdevās noteikt atrašanās vietu. Izvēlieties reģionu vai pilsētu zemāk.';
    krizesMeklesana.vietaNav(kluda.code === kluda.PERMISSION_DENIED);  // meklesana.js: paskaidro arī rezultātos
  }, { enableHighAccuracy: true, timeout: 15000, maximumAge: 60000 });
}
el('atrast').addEventListener('click', () => atrastMani());

// ---- Tuvākā patvertne: neatkarīgi no filtriem, ar līniju no tevis līdz tai ----
async function tuvakaPatvertne() {
  if (!stavoklis.vieta) { atrastMani(tuvakaPatvertne); return; }
  const { lat, lon } = stavoklis.vieta;
  const teksts = el('vieta-teksts');
  try {
    const q = new URLSearchParams({ kategorijas: 'patvertne', lat: lat.toFixed(5), lon: lon.toFixed(5), limit: 1 });
    const f = (await iegut('/objekti?' + q)).features[0];
    if (!f) { teksts.textContent = 'Patvertņu datus neizdevās atrast.'; return; }
    const [plon, plat] = f.geometry.coordinates;
    if (tuvakaSlanis) tuvakaSlanis.remove();
    const marker = L.circleMarker([plat, plon], { radius: 10, color: '#fff', weight: 3, fillColor: kategorijas.patvertne?.krasa || '#b91c1c', fillOpacity: 1 })
      .bindPopup(() => popupSaturs(f.properties, { lat: plat, lng: plon }));
    tuvakaSlanis = L.layerGroup([
      L.polyline([[lat, lon], [plat, plon]], { color: '#0077c8', weight: 3, dashArray: '6 6', interactive: false }),
      marker
    ]).addTo(karte);
    karte.fitBounds(L.latLngBounds([[lat, lon], [plat, plon]]), { padding: [60, 60], maxZoom: 16 });
    marker.openPopup();
    teksts.textContent = `Tuvākā patvertne: ${f.properties.adrese || nosaukums(f.properties)} · ${attalums(f.properties.attalums_m)} taisnā līnijā.`;
  } catch {
    teksts.textContent = 'Tuvāko patvertni neizdevās ielādēt. Mēģiniet vēlreiz pēc brīža.';
  }
}
el('tuvaka').addEventListener('click', tuvakaPatvertne);

// Ja atļauja jau dota iepriekš, nosakām vietu uzreiz (bez jauna jautājuma).
navigator.permissions?.query({ name: 'geolocation' }).then(p => { if (p.state === 'granted') atrastMani(); }).catch(() => {});

// ---- Reģioni ----
function aizpilditRegionus(saraksts) {
  regioni = Object.fromEntries(saraksts.map(r => [r.kods, r]));
  const grupas = [['valstspilseta', 'Valstspilsētas'], ['novads', 'Novadi'], ['pilseta', 'Pilsētas novados']];
  for (const [tips, nos] of grupas) {
    const og = document.createElement('optgroup');
    og.label = nos;
    for (const r of saraksts.filter(r => r.tips === tips)) {
      const o = document.createElement('option');
      o.value = r.kods;
      o.textContent = r.tips === 'pilseta' && regioni[r.novads_kods] ? `${r.nosaukums} (${regioni[r.novads_kods].nosaukums})` : r.nosaukums;
      og.append(o);
    }
    el('regions').append(og);
  }
}

el('regions').addEventListener('change', e => {
  radtRegionu(e.target.value);
  atjaunot();
  krizesMeklesana.atkartot();  // meklesana.js
});

// Arī krīzes meklēšana (meklesana.js), kad vaicājumā ir vietvārds ("patvertne Ogrē").
function radtRegionu(kods) {
  stavoklis.regions = kods;
  el('regions').value = kods;
  if (robezaSlanis) { robezaSlanis.remove(); robezaSlanis = null; }
  const r = regioni[stavoklis.regions];
  if (r) {
    const [w, s, ee, n] = r.bbox;
    karte.fitBounds([[s, w], [n, ee]]);
    iegut('/regioni/' + encodeURIComponent(r.kods)).then(gj => {
      if (stavoklis.regions !== r.kods) return;
      robezaSlanis = L.geoJSON(gj, { style: { color: '#1c1917', weight: 2, dashArray: '6 4', fill: false }, interactive: false }).addTo(karte);
    }).catch(() => {});
  } else if (stavoklis.vieta) {
    karte.setView([stavoklis.vieta.lat, stavoklis.vieta.lon], 13);
  } else {
    karte.fitBounds(latvija);
  }
}

// ---- Kategorijas ----
// Lieli slāņi (~12 000 pieturu, ūdens ņemšanas vietas) sākumā izslēgti; tos ieslēdz filtrā vai meklēšanas scenārijs
const IZSLEGTI_SAKUMA = new Set(['pietura', 'udens_nemsana']);

function aizpilditKategorijas(saraksts) {
  kategorijas = Object.fromEntries(saraksts.map(k => [k.kods, k]));
  const kaste = el('kategorijas');
  // zināmās grupas GRUPAS secībā, jaunas (no datubāzes) beigās ar savu kodu
  const grupas = [...new Set([...Object.keys(GRUPAS), ...saraksts.map(k => k.grupa)])];
  for (const grupa of grupas) {
    const k = saraksts.filter(k => k.grupa === grupa);
    if (!k.length) continue;
    const div = document.createElement('details');
    div.className = 'grupa';
    div.dataset.grupa = grupa;
    div.innerHTML = `<summary><span class="grupa-nos">${esc(GRUPAS[grupa] || grupa)}</span><span class="skaits"></span></summary>` + k.map(k => `
      <label class="kat"><input type="checkbox" value="${esc(k.kods)}" ${!k.skaits ? 'disabled' : IZSLEGTI_SAKUMA.has(k.kods) ? '' : 'checked'}>
        <span class="punkts" style="background:${esc(k.krasa)}"></span>${esc(k.nosaukums)}${k.avoti.every(Avoti.atverts) ? '' : ' <span class="bez-licences" title="Avotam nav norādīta atvērta licence (skat. Datu avoti)">⚠</span>'}
        <span class="skaits">${k.skaits}</span></label>`).join('');
    kaste.append(div);
  }
  kaste.querySelectorAll('input').forEach(i => { if (i.checked) stavoklis.kategorijas.add(i.value); });
  kopsavilkumi();
  kaste.addEventListener('change', e => {
    if (e.target.checked) stavoklis.kategorijas.add(e.target.value); else stavoklis.kategorijas.delete(e.target.value);
    kopsavilkumi();
    atjaunot();
  });
}

// Aizvērtas grupas virsrakstā: cik slāņu ieslēgti un cik tajos objektu.
function kopsavilkumi() {
  for (const d of el('kategorijas').querySelectorAll('details.grupa')) {
    const k = Object.values(kategorijas).filter(k => k.grupa === d.dataset.grupa && k.skaits);
    const iesl = k.filter(k => stavoklis.kategorijas.has(k.kods));
    d.querySelector('summary .skaits').textContent =
      `${iesl.length}/${k.length} · ${iesl.reduce((s, k) => s + k.skaits, 0)}`;
  }
}

// ---- Objekti ----
// Bez nosaukuma (bieži OSM bankomātiem) rādām operatoru vai zīmolu.
const nosaukums = p => p.nosaukums || p.ipasibas?.operator || p.ipasibas?.brand || '';
const kartosanai = p => nosaukums(p).replace(/^[\s"'„“«]+/, '');
const pecNosaukuma = (a, b) => {
  const x = kartosanai(a.properties), y = kartosanai(b.properties);
  return !x - !y || x.localeCompare(y, 'lv');  // bez nosaukuma — beigās
};

// Ūdens līmenis (LVĢMC): cm virs posteņa nulles un m LAS-2000,5; mērījuma laiks UTC → vietējais
const komats = x => String(x).replace('.', ',');
function udensLimenis(i) {
  const izm = i.izmaina_24h_cm;
  const r = [`Ūdens līmenis: <strong>${i.limenis_cm} cm</strong>` + (i.limenis_m != null ? ` (${komats(i.limenis_m)} m LAS)` : '')];
  if (izm != null) r.push(`<small>Pēdējās 24 h: ${izm > 0 ? '↑ +' : izm < 0 ? '↓ −' : '→ '}${Math.abs(izm)} cm</small>`);
  if (i.udens_temp != null) r.push(`<small>Ūdens temperatūra: ${komats(i.udens_temp)} °C</small>`);
  if (i.laiks) r.push(`<small>Mērīts ${new Date(i.laiks).toLocaleString('lv-LV', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })}</small>`);
  return r.join('<br>');
}

function popupSaturs(p, ll) {
  const k = kategorijas[p.kategorija] || {};
  const i = p.ipasibas || {};
  const rindas = [];
  if (p.adrese) rindas.push(esc(p.adrese));
  if (i.limenis_cm != null) rindas.push(udensLimenis(i));
  if (i.piezime) rindas.push('<small>' + esc(i.piezime) + '</small>');
  if (i.opening_hours || i.darba_laiks) rindas.push('<small>Darba laiks: ' + esc(i.opening_hours || i.darba_laiks) + '</small>');
  if (i.veids && ObjektaStatuss.raditVeidu(p)) rindas.push('<small>' + esc(i.veids) + (i.ligzdas ? ` · ${esc(i.ligzdas)} ligzdas` : '') + '</small>');
  if (i.operator && i.operator !== p.nosaukums) rindas.push('<small>' + esc(i.operator) + '</small>');
  if (i.phone) rindas.push('<small>Tālr.: ' + esc(i.phone) + '</small>');  // bez tālruņa saitēm (komandas lēmums)
  if (i.komentars) rindas.push('<small>' + esc(i.komentars) + '</small>');
  if (p.kategorija === 'patvertne') rindas.push('<small>Ietilpība, piekļūstamība ar ratiņkrēslu, mājdzīvnieki: nav norādīts (112.lv datos šo ziņu nav)</small>');
  if (i.marsruti) rindas.push(`<small>${esc(i.veidi)} · ${esc(i.marsruti)} maršruti: ${esc(i.marsrutu_saraksts)}</small>`);
  if (i.apzimejums) rindas.push('<small>Apzīmējums: ' + esc(i.apzimejums) + '</small>');
  if (/^https?:\/\//.test(i.plans_url || '')) rindas.push(`<small><a href="${esc(i.plans_url)}" target="_blank" rel="noopener">Atvērt CA plānu${i.lpp ? ` (lpp. ${esc(i.lpp)})` : ''}</a></small>`);
  if (p.attalums_m != null) rindas.push('<small>' + attalums(p.attalums_m) + ' ' + (stavoklis.vieta?.adrese ? 'no adreses' : 'no Jums') + '</small>');
  return `<div class="popup">${ObjektaStatuss.zime(p)}<b>${esc(nosaukums(p) || k.nosaukums || 'Objekts')}</b>` +
    (nosaukums(p) && k.nosaukums ? `<small>${esc(k.nosaukums)}</small><br>` : '') +
    rindas.join('<br>') + ObjektaStatuss.statuss(p) + marsrutaSaites(ll.lat, ll.lng, stavoklis.vieta) + Avoti.rinda(p.avots) + '</div>';
}

async function atjaunot() {
  if (pieprasijums) pieprasijums.abort();
  pieprasijums = new AbortController();
  objektuSlanis.clearLayers();
  if (!stavoklis.kategorijas.size) { redzamie = []; statuss('Izvēlieties vismaz vienu slāni.'); return; }
  const q = new URLSearchParams({ kategorijas: [...stavoklis.kategorijas].join(','), limit: 20000 });
  if (stavoklis.regions) q.set('regions', stavoklis.regions);
  if (stavoklis.vieta) { q.set('lat', stavoklis.vieta.lat.toFixed(5)); q.set('lon', stavoklis.vieta.lon.toFixed(5)); }
  statuss('Ielādē…');
  try {
    // visi slāņa punkti (līdz ~400 KB): zema prioritāte, lai meklēšanas dati (scenariji.json, tuvākās vietas) nāk pirmie
    const gj = await iegut('/objekti?' + q, pieprasijums.signal, stavoklis.vieta ? undefined : 'low');
    for (const f of gj.features) {
      const [lon, lat] = f.geometry.coordinates;
      const k = kategorijas[f.properties.kategorija] || {};
      f._slanis = L.circleMarker([lat, lon], { radius: 6, color: '#fff', weight: 1.5, fillColor: k.krasa || '#57534e', fillOpacity: .9 })
        .bindPopup(() => popupSaturs(f.properties, { lat, lng: lon }));
    }
    objektuSlanis.addLayers(gj.features.map(f => f._slanis));
    if (!stavoklis.vieta) gj.features.sort(pecNosaukuma);
    redzamie = gj.features;
    const r = regioni[stavoklis.regions];
    statuss(`${gj.features.length} objekti${r ? ' · ' + r.nosaukums : ''}`);
  } catch (e) {
    if (e.name !== 'AbortError') statuss('Datus neizdevās ielādēt. Mēģiniet vēlreiz pēc brīža.', true);
  }
}

// ---- Meklēšana pa kartē ielādētajiem objektiem (bez garumzīmēm, pēc nosaukuma, adreses, slāņa) ----
const MEKL_GARUMS = 8;
const vienkarsot = s => String(s ?? '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();

// Punkts var būt paslēpts grupā, tāpēc uznirstošo logu atver pie koordinātām, nevis pie punkta.
function atvertObjektu(f) {
  const ll = f._slanis.getLatLng();
  karte.setView(ll, Math.max(karte.getZoom(), 16));
  L.popup().setLatLng(ll).setContent(popupSaturs(f.properties, ll)).openOn(karte);
}

// ---- Adreses (VZD adrešu reģistrs caur /api/adreses): izvēlētā adrese kļūst par atskaites punktu ----
const isaAdrese = a => a.split(', ').slice(0, 2).join(', ');  // "Brīvības iela 15, Ogre"
let adresuPieprasijums = null;
let adresuTaimeris = null;

// atkartot = false, ja adresi izvēlējās pati krīzes meklēšana (adrese vaicājumā)
function izveletiesAdresi(a, atkartot = true) {
  stavoklis.vieta = { lat: a.lat, lon: a.lon, adrese: a.adrese };
  if (vietasSlanis) vietasSlanis.remove();
  vietasSlanis = L.layerGroup([
    L.circleMarker([a.lat, a.lon], { radius: 9, color: '#fff', weight: 3, fillColor: '#0077c8', fillOpacity: 1 })
      .bindTooltip(isaAdrese(a.adrese), { permanent: true, direction: 'top', offset: [0, -8] })
  ]).addTo(karte);
  if (tuvakaSlanis) { tuvakaSlanis.remove(); tuvakaSlanis = null; }
  el('atrast').textContent = '📍 Rādīt tuvākos man';
  el('vieta-teksts').textContent = `Saraksts sakārtots pēc attāluma no adreses ${isaAdrese(a.adrese)} (taisnā līnijā).`;
  karte.setView([a.lat, a.lon], 16);
  atjaunot();
  if (atkartot) krizesMeklesana.atkartot();  // meklesana.js
}

function meklesanasRinda(krasa, virsraksts, apaksa, izveleties) {
  const li = document.createElement('li');
  li.tabIndex = 0;
  li.setAttribute('role', 'option');
  li.innerHTML = `<span class="punkts" style="background:${esc(krasa)}"></span>
    <span class="teksts"><b>${esc(virsraksts)}</b><small>${esc(apaksa)}</small></span>`;
  li.addEventListener('click', izveleties);
  li.addEventListener('keydown', e => { if (e.key === 'Enter') izveleties(); });
  return li;
}

function meklet() {
  const ul = el('mekl-rezultati');
  const vaicajums = el('meklet').value.trim();
  const vardi = vienkarsot(vaicajums).split(/\s+/).filter(Boolean);
  ul.innerHTML = '';
  clearTimeout(adresuTaimeris);
  if (adresuPieprasijums) adresuPieprasijums.abort();
  if (!vardi.length || vardi.join('').length < 2) { ul.hidden = true; return; }

  const adresuGrupa = document.createElement('li');
  adresuGrupa.className = 'mekl-grupa';
  adresuGrupa.textContent = 'Adreses';
  if (vardi.join('').length >= 3) {
    adresuGrupa.textContent = 'Adreses · meklē…';
    adresuTaimeris = setTimeout(async () => {
      adresuPieprasijums = new AbortController();
      try {
        const adreses = await iegut('/adreses?' + new URLSearchParams({ q: vaicajums, limit: 5 }), adresuPieprasijums.signal);
        adresuGrupa.textContent = adreses.length ? 'Adreses' : 'Adreses · nav atrasta';
        let pec = adresuGrupa;
        for (const a of adreses) {
          const li = meklesanasRinda('#0077c8', isaAdrese(a.adrese), a.adrese, () => {
            ul.hidden = true; el('meklet').value = isaAdrese(a.adrese); izveletiesAdresi(a);
          });
          pec.after(li);
          pec = li;
        }
      } catch (e) {
        // kamēr /api/adreses nav pieejams (404), adrešu grupu vienkārši nerādām
        if (e.name !== 'AbortError') adresuGrupa.remove();
      }
    }, 250);
  }
  ul.append(adresuGrupa);

  const objektuGrupa = document.createElement('li');
  objektuGrupa.className = 'mekl-grupa';
  objektuGrupa.textContent = 'Kartē';
  ul.append(objektuGrupa);
  const atrasti = [];
  for (const f of redzamie) {
    const p = f.properties;
    const teksts = vienkarsot([nosaukums(p), p.adrese, kategorijas[p.kategorija]?.nosaukums].join(' '));
    if (vardi.every(v => teksts.includes(v)) && atrasti.push(f) >= MEKL_GARUMS) break;
  }
  for (const f of atrasti) {
    const p = f.properties;
    const k = kategorijas[p.kategorija] || {};
    ul.append(meklesanasRinda(k.krasa, nosaukums(p) || k.nosaukums, p.adrese || k.nosaukums, () => {
      ul.hidden = true; el('meklet').value = nosaukums(p) || p.adrese || ''; atvertObjektu(f);
    }));
  }
  if (!atrasti.length) objektuGrupa.textContent = 'Kartē · nekas ieslēgtajos slāņos';
  ul.hidden = false;
}
el('meklet').addEventListener('input', meklet);
el('meklet').addEventListener('keydown', e => {
  if (e.key === 'Escape') el('mekl-rezultati').hidden = true;
  if (e.key === 'ArrowDown') el('mekl-rezultati').querySelector('li[tabindex]')?.focus();
});
document.addEventListener('click', e => { if (!e.target.closest('.meklesana')) el('mekl-rezultati').hidden = true; });

// ---- Plūdu riska zonas (LVĢMC 3. cikla kartes 2026–2031, CC0): zīmē zonas.js (laukumi ar robežu, pārklāšanās) ----
function radtPludus(ieslegt) {
  el('pludu-slanis').checked = ieslegt;
  Zonas.radit('pludi', ieslegt);
}
el('pludu-slanis').addEventListener('change', e => radtPludus(e.target.checked));

Promise.all([iegut('/kategorijas'), iegut('/regioni'), Avoti.ieladet()])
  .then(([k, r]) => {
    aizpilditKategorijas(k); aizpilditRegionus(r); atjaunot(); krizesMeklesana.sakt(r);
  })
  .catch(() => {
    statuss('Datus neizdevās ielādēt. Mēģiniet vēlreiz pēc brīža.', true);
    krizesMeklesana.sakt([], true);  // padoms un 112 rinda strādā arī bez kartes datiem
  });
