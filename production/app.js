// map.repo.lv: karte ar filtriem. Dati no /api (src/karte/api/karte_api.py, Postgres `map` uz VPS).
const API = '/api';
const SARAKSTA_GARUMS = 100;
const GRUPAS = { patvertnes: 'Patvertnes', veseliba: 'Veselība', infrastruktura: 'Infrastruktūra', incidenti: 'Incidenti' };

const latvija = L.latLngBounds([55.6, 20.8], [58.15, 28.3]);
const karte = L.map('karte', { maxBounds: latvija.pad(0.3), minZoom: 6, preferCanvas: true }).fitBounds(latvija);
L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
  maxZoom: 19,
  attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> līdzstrādnieki'
}).addTo(karte);
L.control.scale({ imperial: false }).addTo(karte);

const el = id => document.getElementById(id);
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const statuss = (t, kluda) => { el('statuss').textContent = t; el('statuss').classList.toggle('kluda', !!kluda); };

const stavoklis = { vieta: null, regions: '', kategorijas: new Set() };
let kategorijas = {};
let regioni = {};
const objektuSlanis = L.featureGroup().addTo(karte);
let robezaSlanis = null;
let vietasSlanis = null;
let pieprasijums = null;

async function iegut(cels, signal) {
  const r = await fetch(API + cels, { signal });
  if (!r.ok) throw new Error(r.status);
  return r.json();
}

function attalums(m) {
  if (m == null) return '';
  return m < 1000 ? m + ' m' : (m / 1000).toFixed(m < 10000 ? 1 : 0).replace('.', ',') + ' km';
}

// ---- Atrašanās vieta ----
function atrastMani() {
  const teksts = el('vieta-teksts');
  if (!('geolocation' in navigator)) { teksts.textContent = 'Šis pārlūks nevar noteikt atrašanās vietu. Izvēlies reģionu zemāk.'; return; }
  el('atrast').disabled = true;
  teksts.textContent = 'Nosaka atrašanās vietu…';
  navigator.geolocation.getCurrentPosition(poz => {
    el('atrast').disabled = false;
    const { latitude: lat, longitude: lon, accuracy } = poz.coords;
    if (!latvija.pad(0.3).contains([lat, lon])) {
      teksts.textContent = 'Tu atrodies ārpus Latvijas, tāpēc attālumus nerādām. Izvēlies reģionu zemāk.';
      return;
    }
    stavoklis.vieta = { lat, lon };
    if (vietasSlanis) vietasSlanis.remove();
    vietasSlanis = L.layerGroup([
      L.circle([lat, lon], { radius: accuracy, color: '#1d4ed8', weight: 1, fillOpacity: .08, interactive: false }),
      L.circleMarker([lat, lon], { radius: 8, color: '#fff', weight: 3, fillColor: '#1d4ed8', fillOpacity: 1 }).bindTooltip('Tu esi šeit')
    ]).addTo(karte);
    el('atrast').textContent = '📍 Atjaunot manu atrašanās vietu';
    teksts.textContent = 'Saraksts sakārtots pēc attāluma no tevis (taisnā līnijā).';
    if (!stavoklis.regions) karte.setView([lat, lon], 13);
    atjaunot();
  }, kluda => {
    el('atrast').disabled = false;
    teksts.textContent = kluda.code === kluda.PERMISSION_DENIED
      ? 'Atrašanās vieta nav atļauta. Izvēlies reģionu vai pilsētu zemāk (vai atļauj to pārlūka iestatījumos).'
      : 'Neizdevās noteikt atrašanās vietu. Izvēlies reģionu vai pilsētu zemāk.';
  }, { enableHighAccuracy: true, timeout: 15000, maximumAge: 60000 });
}
el('atrast').addEventListener('click', atrastMani);

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

el('regions').addEventListener('change', async e => {
  stavoklis.regions = e.target.value;
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
  atjaunot();
});

// ---- Kategorijas ----
function aizpilditKategorijas(saraksts) {
  kategorijas = Object.fromEntries(saraksts.map(k => [k.kods, k]));
  const kaste = el('kategorijas');
  // zināmās grupas GRUPAS secībā, jaunas (no datubāzes) beigās ar savu kodu
  const grupas = [...new Set([...Object.keys(GRUPAS), ...saraksts.map(k => k.grupa)])];
  for (const grupa of grupas) {
    const k = saraksts.filter(k => k.grupa === grupa);
    if (!k.length) continue;
    const div = document.createElement('div');
    div.className = 'grupa';
    div.innerHTML = `<div class="grupa-nos">${esc(GRUPAS[grupa] || grupa)}</div>` + k.map(k => `
      <label class="kat"><input type="checkbox" value="${esc(k.kods)}" ${k.skaits ? 'checked' : 'disabled'}>
        <span class="punkts" style="background:${esc(k.krasa)}"></span>${esc(k.nosaukums)}${k.avoti.every(Avoti.atverts) ? '' : ' <span class="bez-licences" title="Avotam nav norādīta atvērta licence (skat. Datu avoti)">⚠</span>'}
        <span class="skaits">${k.skaits}</span></label>`).join('');
    kaste.append(div);
  }
  kaste.querySelectorAll('input').forEach(i => { if (i.checked) stavoklis.kategorijas.add(i.value); });
  kaste.addEventListener('change', e => {
    if (e.target.checked) stavoklis.kategorijas.add(e.target.value); else stavoklis.kategorijas.delete(e.target.value);
    atjaunot();
  });
}

// ---- Objekti ----
// Bez nosaukuma (bieži OSM bankomātiem) rādām operatoru vai zīmolu.
const nosaukums = p => p.nosaukums || p.ipasibas?.operator || p.ipasibas?.brand || '';
const kartosanai = p => nosaukums(p).replace(/^[\s"'„“«]+/, '');
const pecNosaukuma = (a, b) => {
  const x = kartosanai(a.properties), y = kartosanai(b.properties);
  return !x - !y || x.localeCompare(y, 'lv');  // bez nosaukuma — beigās
};

function popupSaturs(p, ll) {
  const k = kategorijas[p.kategorija] || {};
  const i = p.ipasibas || {};
  const rindas = [];
  if (p.adrese) rindas.push(esc(p.adrese));
  if (i.piezime) rindas.push('<small>' + esc(i.piezime) + '</small>');
  if (i.opening_hours) rindas.push('<small>Darba laiks: ' + esc(i.opening_hours) + '</small>');
  if (i.operator && i.operator !== p.nosaukums) rindas.push('<small>' + esc(i.operator) + '</small>');
  if (i.phone) rindas.push('<small>Tālr.: <a href="tel:' + esc(i.phone.replace(/\s/g, '')) + '">' + esc(i.phone) + '</a></small>');
  if (i.komentars) rindas.push('<small>' + esc(i.komentars) + '</small>');
  if (p.attalums_m != null) rindas.push('<small>' + attalums(p.attalums_m) + ' no tevis</small>');
  const no = stavoklis.vieta ? `${stavoklis.vieta.lat},${stavoklis.vieta.lon}` : '';
  const marsruts = `https://www.openstreetmap.org/directions?engine=fossgis_osrm_foot&route=${no}%3B${ll.lat}%2C${ll.lng}`;
  return `<div class="popup"><b>${esc(nosaukums(p) || k.nosaukums || 'Objekts')}</b>` +
    (nosaukums(p) && k.nosaukums ? `<small>${esc(k.nosaukums)}</small><br>` : '') +
    rindas.join('<br>') + `<br><a href="${marsruts}" target="_blank" rel="noopener">Maršruts ↗</a><br>${Avoti.rinda(p.avots)}</div>`;
}

function zimetSarakstu(features) {
  const ol = el('saraksts');
  ol.innerHTML = '';
  const radit = features.slice(0, SARAKSTA_GARUMS);
  el('saraksts-virsraksts').textContent = stavoklis.vieta
    ? `Tuvākie (${radit.length} no ${features.length})`
    : `Saraksts (${radit.length} no ${features.length})`;
  for (const f of radit) {
    const p = f.properties;
    const k = kategorijas[p.kategorija] || {};
    const li = document.createElement('li');
    li.tabIndex = 0;
    li.innerHTML = `<span class="punkts" style="background:${esc(k.krasa)}"></span>
      <span class="teksts"><b>${esc(nosaukums(p) || k.nosaukums)}</b><small>${esc([nosaukums(p) ? k.nosaukums : '', p.adrese].filter(Boolean).join(' · '))}</small></span>
      <span class="attalums">${attalums(p.attalums_m)}</span>`;
    const atvert = () => { karte.setView(f._slanis.getLatLng(), Math.max(karte.getZoom(), 16)); f._slanis.openPopup(); };
    li.addEventListener('click', atvert);
    li.addEventListener('keydown', e => { if (e.key === 'Enter') atvert(); });
    ol.append(li);
  }
  if (!features.length) ol.innerHTML = '<li class="piezime">Nekas neatbilst izvēlētajiem filtriem.</li>';
}

async function atjaunot() {
  if (pieprasijums) pieprasijums.abort();
  pieprasijums = new AbortController();
  objektuSlanis.clearLayers();
  if (!stavoklis.kategorijas.size) { zimetSarakstu([]); statuss('Izvēlies vismaz vienu slāni.'); return; }
  const q = new URLSearchParams({ kategorijas: [...stavoklis.kategorijas].join(','), limit: 20000 });
  if (stavoklis.regions) q.set('regions', stavoklis.regions);
  if (stavoklis.vieta) { q.set('lat', stavoklis.vieta.lat.toFixed(5)); q.set('lon', stavoklis.vieta.lon.toFixed(5)); }
  statuss('Ielādē…');
  try {
    const gj = await iegut('/objekti?' + q, pieprasijums.signal);
    for (const f of gj.features) {
      const [lon, lat] = f.geometry.coordinates;
      const k = kategorijas[f.properties.kategorija] || {};
      f._slanis = L.circleMarker([lat, lon], { radius: 6, color: '#fff', weight: 1.5, fillColor: k.krasa || '#57534e', fillOpacity: .9 })
        .bindPopup(() => popupSaturs(f.properties, { lat, lng: lon }))
        .addTo(objektuSlanis);
    }
    if (!stavoklis.vieta) gj.features.sort(pecNosaukuma);
    zimetSarakstu(gj.features);
    const r = regioni[stavoklis.regions];
    statuss(`${gj.features.length} objekti${r ? ' · ' + r.nosaukums : ''}`);
  } catch (e) {
    if (e.name !== 'AbortError') statuss('Datus neizdevās ielādēt. Mēģini vēlreiz pēc brīža.', true);
  }
}

Promise.all([iegut('/kategorijas'), iegut('/regioni'), Avoti.ieladet()])
  .then(([k, r]) => {
    karte.attributionControl.addAttribution(Avoti.atsauce());
    aizpilditKategorijas(k); aizpilditRegionus(r); atjaunot();
  })
  .catch(() => statuss('Datus neizdevās ielādēt. Mēģini vēlreiz pēc brīža.', true));
