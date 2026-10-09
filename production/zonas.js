// Zonas kartē: reģistrs ar zonu slāņiem (plūdu riska zonas, LVĢMC brīdinājumu apgabali; vēlāk citi).
// Visas ieslēgtās zonas zīmē viens kanvas flīžu slānis: katrai zonai sava aizpildījuma krāsa un skaidra robeža;
// kur pārklājas divas vai vairākas zonas — "paaugstināts risks" (tumšāks, svītrots laukums ar sarkanu robežu).
// Plūdu zonas: LVĢMC WMS (geo-dpps.viss.gov.lv, CC0). Ģeometriju serviss nedod (nav WFS, GetFeatureInfo bez
// ģeometrijas), tāpēc WMS attēlu pārvēršam maskā: necaurspīdīgs pikselis = zonā. Serviss atļauj CORS no map.repo.lv.
// Brīdinājumi: /api/bridinajumi?poligoni=1 (LVĢMC, data.gov.lv, CC0). Lieto: app.js (radtPludus), meklesana.js.
const Zonas = (() => {
  const PLUDU_WMS = 'https://geo-dpps.viss.gov.lv/api/DPPSPackage/client/';
  const LIELUMS = 512;  // lielas flīzes: 4× mazāk pieprasījumu lēnajam WMS (atbild ~5 s neatkarīgi no izmēra)
  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const saite = (url, t) => `<a href="${url}" target="_blank" rel="noopener">${t}</a>`;

  // Reģistrs. krasas(v) → [aizpildījums rgba, robeža rgb] pēc maskas vērtības v (1–255).
  const ZONAS = [
    {
      kods: 'pludi', nosaukums: 'plūdu riska zona',
      apraksts: 'Plūdu riska zona: applūst vismaz reizi 100 gados (1 % varbūtība gadā)',
      avots: saite('https://data.gov.lv/dati/lv/dataset/3-cikla-latvijas-pldu-postjumu-vietu-un-pldu-riska-kartes1', 'LVĢMC plūdu riska kartes 2026–2031') + ' · CC0',
      minZoom: 8,
      // slānis 1 = 1 % (100 gadu) applūšana; pārklājums [dienvidi, rietumi, ziemeļi, austrumi] — ārpus tā nepieprasām
      wms: [
        { cels: '3._cikla_L_557_7iFPTq/b7ad025f-833a-4b4f-a845-d5cec9d24092', slanis: '1', robezas: [55.76, 20.88, 57.67, 27.92] },  // pavasara pali
        { cels: '3._cikla_L_558_jIS73E/3322e012-8cb3-4a4c-8acf-a467e25a17b3', slanis: '1', robezas: [56.38, 23.95, 56.64, 26.01] },  // ledus sastrēgumi
        { cels: '3._cikla_L_556_karVbb/cc6f2ed3-dbfb-42d0-98e1-4d9f10f57fea', slanis: '1', robezas: [56.06, 20.84, 57.88, 24.49] },  // jūras vējuzplūdi
      ],
      krasas: () => [[37, 99, 235, 90], [29, 78, 216]],
    },
    {
      kods: 'bridinajumi', nosaukums: 'LVĢMC brīdinājuma apgabals',
      avots: saite('https://data.gov.lv/dati/lv/dataset/hidrometeorologiskie-bridinajumi', 'LVĢMC hidrometeoroloģiskie brīdinājumi') + ' · CC0',
      poligoni: [],  // [{ punkti: [[lat, lon], ...], v: līmenis 1–3 (+4, ja hidroloģisks), teksts }]
      // pārklāšanos veido tikai oranžie/sarkanie vai ar ūdeni saistītie brīdinājumi — visas Latvijas dzeltenais vējš ne
      skaitit: v => (v & 3) >= 2 || (v & 4) > 0,
      krasas: v => (v &= 3) >= 3 ? [[220, 38, 38, 45], [185, 28, 28]] : v === 2 ? [[234, 88, 12, 45], [194, 65, 12]] : [[234, 179, 8, 45], [161, 98, 7]],
    },
  ];
  const PARKLAJUMS = { aizp: [127, 29, 29, 120], svitra: [185, 28, 28, 210], robeza: [220, 38, 38] };
  const ieslegtas = new Set();
  const maskas = new Map();  // `${z}/${x}/${y}` → { kods: Uint8Array } (WMS zonām; klikšķim un pārzīmēšanai)

  function attels(url) {
    return new Promise((ok, nav) => {
      const img = new Image();
      img.crossOrigin = 'anonymous';
      img.onload = () => ok(img);
      img.onerror = nav;
      img.src = url;
    });
  }

  // WMS flīze EPSG:3857 tieši Leaflet flīzes robežās (bez izkropļojumiem); serviss mēdz atbildēt lēni — vienreiz atkārtojam
  async function wmsMaska(zona, coords, robezas) {
    const nw = karte.unproject(coords.scaleBy(L.point(LIELUMS, LIELUMS)), coords.z);
    const se = karte.unproject(coords.add([1, 1]).scaleBy(L.point(LIELUMS, LIELUMS)), coords.z);
    const a = L.CRS.EPSG3857.project(nw), b = L.CRS.EPSG3857.project(se);
    const maska = new Uint8Array(LIELUMS * LIELUMS);
    const kanva = document.createElement('canvas');
    kanva.width = kanva.height = LIELUMS;
    const ctx = kanva.getContext('2d', { willReadFrequently: true });
    for (const s of zona.wms) {
      const [d, r, z, a2] = s.robezas;
      if (se.lat > z || nw.lat < d || se.lng < r || nw.lng > a2) continue;
      const url = PLUDU_WMS + s.cels + '?' + new URLSearchParams({
        service: 'WMS', version: '1.3.0', request: 'GetMap', layers: s.slanis, styles: '', crs: 'EPSG:3857',
        bbox: [a.x, b.y, b.x, a.y].join(','), width: LIELUMS, height: LIELUMS, format: 'image/png', transparent: 'TRUE',
      });
      let img;
      try { img = await attels(url); } catch { img = await attels(url + '&r=1'); }
      ctx.clearRect(0, 0, LIELUMS, LIELUMS);
      ctx.drawImage(img, 0, 0);
      const px = ctx.getImageData(0, 0, LIELUMS, LIELUMS).data;
      for (let i = 0; i < maska.length; i++) if (px[i * 4 + 3] > 40) maska[i] = 1;
    }
    // tālā skatā upju palieņu zonas ir 1 px šauras un izskatās pēc punktiem — paplašinām par 1 px, lai būtu nepārtrauktas
    return coords.z <= 10 ? paplasinat(maska) : maska;
  }

  function paplasinat(m) {
    const r = new Uint8Array(m.length);
    for (let y = 0; y < LIELUMS; y++) for (let x = 0; x < LIELUMS; x++) {
      if (!m[y * LIELUMS + x]) continue;
      for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) {
        const xx = x + dx, yy = y + dy;
        if (xx >= 0 && yy >= 0 && xx < LIELUMS && yy < LIELUMS) r[yy * LIELUMS + xx] = 1;
      }
    }
    return r;
  }

  // Poligoni → maska ar vērtību v (augstākais līmenis uzvar)
  function poligonuMaska(zona, coords) {
    const kanva = document.createElement('canvas');
    kanva.width = kanva.height = LIELUMS;
    const ctx = kanva.getContext('2d', { willReadFrequently: true });
    const sakums = coords.scaleBy(L.point(LIELUMS, LIELUMS));
    const maska = new Uint8Array(LIELUMS * LIELUMS);
    for (const p of [...zona.poligoni].sort((a, b) => (a.v & 3) - (b.v & 3) || a.v - b.v)) {
      ctx.clearRect(0, 0, LIELUMS, LIELUMS);
      ctx.beginPath();
      p.punkti.forEach(([lat, lon], i) => {
        const t = karte.project([lat, lon], coords.z).subtract(sakums);
        i ? ctx.lineTo(t.x, t.y) : ctx.moveTo(t.x, t.y);
      });
      ctx.fill();
      const px = ctx.getImageData(0, 0, LIELUMS, LIELUMS).data;
      for (let i = 0; i < maska.length; i++) if (px[i * 4 + 3] > 127) maska[i] = p.v;
    }
    return maska;
  }

  const robeza = (m, x, y) => {  // vai pikselis ir maskas malā (blakus pikselis ārpus); flīzes malas neskaitās
    for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) {
      const xx = x + dx, yy = y + dy;
      if (xx >= 0 && yy >= 0 && xx < LIELUMS && yy < LIELUMS && !m(yy * LIELUMS + xx)) return true;
    }
    return false;
  };

  function zimet(kanva, saraksts) {  // saraksts: [[zona, maska]]
    const ctx = kanva.getContext('2d');
    const img = ctx.createImageData(LIELUMS, LIELUMS), d = img.data;
    const skaits = new Uint8Array(LIELUMS * LIELUMS);
    for (const [z, m] of saraksts) for (let i = 0; i < m.length; i++) if (m[i] && (!z.skaitit || z.skaitit(m[i]))) skaits[i]++;
    const krasot = (i, [r, g, b, a = 255]) => { d[i * 4] = r; d[i * 4 + 1] = g; d[i * 4 + 2] = b; d[i * 4 + 3] = a; };
    for (let y = 0; y < LIELUMS; y++) for (let x = 0; x < LIELUMS; x++) {
      const i = y * LIELUMS + x;
      if (!skaits[i]) continue;
      if (skaits[i] >= 2) { krasot(i, (x + y) % 8 < 2 ? PARKLAJUMS.svitra : PARKLAJUMS.aizp); continue; }
      for (const [z, m] of saraksts) if (m[i]) { krasot(i, z.krasas(m[i])[0]); break; }
    }
    for (const [z, m] of saraksts) for (let y = 0; y < LIELUMS; y++) for (let x = 0; x < LIELUMS; x++) {
      const i = y * LIELUMS + x;
      if (m[i] && skaits[i] < 2 && robeza(j => m[j], x, y)) krasot(i, z.krasas(m[i])[1]);
    }
    for (let y = 0; y < LIELUMS; y++) for (let x = 0; x < LIELUMS; x++) {
      const i = y * LIELUMS + x;
      if (skaits[i] >= 2 && robeza(j => skaits[j] >= 2, x, y)) krasot(i, PARKLAJUMS.robeza);
    }
    ctx.putImageData(img, 0, 0);
  }

  const Slanis = L.GridLayer.extend({
    createTile(coords, gatavs) {
      const kanva = L.DomUtil.create('canvas', 'zonu-flize');
      kanva.width = kanva.height = LIELUMS;
      const atslega = `${coords.z}/${coords.x}/${coords.y}`;
      const aktivas = ZONAS.filter(z => ieslegtas.has(z.kods) && coords.z >= (z.minZoom || 0));
      Promise.all(aktivas.map(async z => {
        if (!z.wms) return [z, z.poligoni.length ? poligonuMaska(z, coords) : null];
        const kese = maskas.get(atslega) || {};
        if (!kese[z.kods]) {
          kese[z.kods] = await wmsMaska(z, coords);
          maskas.set(atslega, kese);
          if (maskas.size > 400) maskas.delete(maskas.keys().next().value);
        }
        return [z, kese[z.kods]];
      })).then(saraksts => {
        zimet(kanva, saraksts.filter(([, m]) => m));
        gatavs(null, kanva);
      }, kluda => gatavs(kluda, kanva));
      return kanva;
    },
  });
  const slanis = new Slanis({
    tileSize: LIELUMS, zIndex: 250, updateWhenZooming: false, keepBuffer: 1,
    attribution: 'Zonas: ' + saite('https://data.gov.lv/dati/lv/dataset/3-cikla-latvijas-pldu-postjumu-vietu-un-pldu-riska-kartes1', 'LVĢMC') + ' (CC0)',
  });

  // Leģenda kartes stūrī, kamēr kāda zona ieslēgta
  const legenda = L.control({ position: 'bottomleft' });  // augšā kreisajā stūrī ir "Prognoze" poga (prognozes.js)
  legenda.onAdd = () => L.DomUtil.create('div', 'zonu-legenda');
  function atjaunotLegendu() {
    const div = legenda.getContainer();
    if (!div) return;
    const z = karte.getZoom();
    div.innerHTML = ZONAS.filter(x => ieslegtas.has(x.kods)).map(x => {
      const [a, r] = x.krasas(1);
      return `<span><i style="background:rgba(${a.slice(0, 3)},${a[3] / 255});border-color:rgb(${r})"></i>${esc(x.nosaukums)}</span>`;
    }).join('') +
      (ieslegtas.size >= 2 ? '<span><i class="parklajas"></i>paaugstināts risks (zonas pārklājas)</span>' : '') +
      (ieslegtas.has('pludi') && z < 8 ? '<small>Tuviniet karti, lai redzētu plūdu zonas</small>' : '') +
      (ielade === 'notiek' ? '<small>Ielādē zonas… LVĢMC serviss var atbildēt līdz 30 s</small>' : '') +
      (ielade === 'kluda' ? '<small>Daļa zonu neielādējās. Pabīdiet karti, lai mēģinātu vēlreiz.</small>' : '');
  }

  function radit(kods, ieslegt) {
    if (ieslegt) ieslegtas.add(kods); else ieslegtas.delete(kods);
    if (ieslegtas.size) {
      if (!karte.hasLayer(slanis)) slanis.addTo(karte); else slanis.redraw();
      if (!legenda.getContainer()) legenda.addTo(karte);
      atjaunotLegendu();
    } else {
      slanis.remove();
      legenda.remove();
    }
  }
  let ielade = '';
  slanis.on('loading', () => { ielade = 'notiek'; atjaunotLegendu(); });
  slanis.on('tileerror', () => { ielade = 'kluda'; });
  slanis.on('load', () => { if (ielade === 'notiek') ielade = ''; atjaunotLegendu(); });
  karte.on('zoomend', atjaunotLegendu);

  // ---- Klikšķis: kuras zonas ir šajā vietā; ja divas vai vairāk — brīdinājums par paaugstinātu risku ----
  function punktsPoligona(lat, lon, p) {
    let iekša = false;
    for (let i = 0, j = p.length - 1; i < p.length; j = i++) {
      const [yi, xi] = p[i], [yj, xj] = p[j];
      if ((yi > lat) !== (yj > lat) && lon < (xj - xi) * (lat - yi) / (yj - yi) + xi) iekša = !iekša;
    }
    return iekša;
  }
  function zonasVieta(ll) {
    const z = karte.getZoom(), p = karte.project(ll, z).floor();
    const x = Math.floor(p.x / LIELUMS), y = Math.floor(p.y / LIELUMS);
    const kese = maskas.get(`${z}/${x}/${y}`) || {};
    const i = (p.y - y * LIELUMS) * LIELUMS + (p.x - x * LIELUMS);
    const atrastas = [];
    for (const zona of ZONAS) {
      if (!ieslegtas.has(zona.kods)) continue;
      if (zona.wms) { if (kese[zona.kods]?.[i]) atrastas.push({ zona, teksts: zona.apraksts, skaitas: true }); continue; }
      const sheit = zona.poligoni.filter(pp => punktsPoligona(ll.lat, ll.lng, pp.punkti));
      if (sheit.length) atrastas.push({ zona, teksts: sheit.map(pp => pp.teksts).join('; '), skaitas: sheit.some(pp => !zona.skaitit || zona.skaitit(pp.v)) });
    }
    return atrastas;
  }
  let pedejaisPopup = 0;
  // logs ir svarīgāks par leģendu (telefonā tie pārklātos)
  karte.on('popupopen', () => { pedejaisPopup = Date.now(); legenda.getContainer()?.classList.add('paslepta'); });
  karte.on('popupclose', () => legenda.getContainer()?.classList.remove('paslepta'));
  karte.on('click', e => {
    if (!ieslegtas.size) return;
    setTimeout(() => {
      if (Date.now() - pedejaisPopup < 400) return;  // klikšķis bija uz objekta punkta — tā logs svarīgāks
      const atrastas = zonasVieta(e.latlng);
      if (!atrastas.length) return;
      const augsts = new Set(atrastas.filter(a => a.skaitas).map(a => a.zona.kods)).size >= 2;
      L.popup({ maxWidth: Math.min(300, karte.getSize().x - 70) }).setLatLng(e.latlng).setContent(
        '<div class="popup zonu-popup">' +
        (augsts ? `<b class="paaugstinats">Paaugstināts risks</b><p>Šeit pārklājas: ${atrastas.filter(a => a.skaitas).map(a => esc(a.zona.nosaukums)).join(' + ')}; ieteicams izvairīties.</p>` : '') +
        atrastas.map(a => `<p>${augsts ? '' : '<b>' + esc(a.zona.nosaukums[0].toUpperCase() + a.zona.nosaukums.slice(1)) + '</b><br>'}${esc(a.teksts)}` +
          `<br><small class="popup-avots">Avots: ${a.zona.avots}</small></p>`).join('') +
        '</div>').openOn(karte);
    }, 0);
  });

  // ---- Brīdinājumu apgabali: ielādē vienreiz, slēdzis panelī zem plūdu zonām ----
  const LIMENI = { 1: 'Dzeltenais', 2: 'Oranžais', 3: 'Sarkanais' };
  async function ieladetBridinajumus() {
    const r = await fetch('/api/bridinajumi?poligoni=1');
    if (!r.ok) throw new Error(r.status);
    const zona = ZONAS.find(z => z.kods === 'bridinajumi');
    zona.poligoni = (await r.json()).bridinajumi.flatMap(b => (b.poligoni || []).map(punkti => ({
      punkti, v: b.limenis | (/lietus|plūd|vējuzplūd|pali|sastrēg|ūdens/i.test(b.paradiba) ? 4 : 0),
      teksts: `${LIMENI[b.limenis] || esc(b.krasa)} brīdinājums: ${b.paradiba.toLowerCase()}` +
        (b.lidz ? `, līdz ${new Date(b.lidz).toLocaleString('lv-LV', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })}` : ''),
    })));
    return zona.poligoni.length;
  }
  const pludi = document.getElementById('pludu-slanis')?.closest('label');
  if (pludi) {
    const l = document.createElement('label');
    l.className = 'kat parklajums';
    l.innerHTML = '<input type="checkbox" id="bridinajumu-slanis"><span class="punkts" style="background:#eab308"></span>' +
      'Brīdinājumu apgabali (LVĢMC)';
    pludi.after(l);
    const cb = l.querySelector('input');
    cb.addEventListener('change', async () => {
      if (!cb.checked) return radit('bridinajumi', false);
      try {
        if (!ZONAS[1].poligoni.length && !await ieladetBridinajumus()) {
          cb.checked = false;
          l.lastChild.textContent = 'Brīdinājumu apgabali (LVĢMC): šobrīd nav';
          return;
        }
        radit('bridinajumi', true);
      } catch {
        cb.checked = false;
        l.lastChild.textContent = 'Brīdinājumu apgabali (LVĢMC): neizdevās ielādēt';
      }
    });
  }

  return { radit, zonasVieta, ZONAS };
})();
