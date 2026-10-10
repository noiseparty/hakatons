// Zonas kartē: reģistrs ar zonu slāņiem (plūdu riska zonas, LVĢMC brīdinājumu apgabali, satiksme, slidens ceļš).
// Visas ieslēgtās zonas zīmē viens kanvas flīžu slānis: katrai zonai sava aizpildījuma krāsa un skaidra robeža;
// kur pārklājas divas vai vairākas riska zonas — "paaugstināts risks" (tumšāks, svītrots laukums ar sarkanu robežu).
// Plūdu zonas: LVĢMC WMS (geo-dpps.viss.gov.lv, CC0). Ģeometriju serviss nedod (nav WFS, GetFeatureInfo bez
// ģeometrijas), tāpēc WMS attēlu pārvēršam maskā: necaurspīdīgs pikselis = zonā. Flīzes nāk caur mūsu API ar diska kešu
// (/api/pludi/flize/<paka>/<z>/<x>/<y>.png, karte_api.py), jo WMS atbild 5–30 s; ja API to vēl nezina (404) — tieši no
// WMS kā agrāk (serviss atļauj CORS no map.repo.lv).
// Brīdinājumi: vienkāršotie poligoni no /api/prognozes (kešots 5 min), rezerve /api/bridinajumi?poligoni=1 (LVĢMC, data.gov.lv, CC0).
// Satiksme, ceļu meteostacijas, robežpunkti: /api/satiksme (LVC, transportdata.gov.lv, CC0); satiksmes zonas ir
// novadi un valstspilsētas (/api/prognozes/robezas, VZD CC BY 4.0).
// Lieto: app.js (radtPludus), meklesana.js (satiksmeRinda — rinda rezultātu kartītē).
const Zonas = (() => {
  const PLUDU_WMS = 'https://geo-dpps.viss.gov.lv/api/DPPSPackage/client/';
  const PLUDU_FLIZE = '/api/pludi/flize/';
  const LIELUMS = 512;  // lielas flīzes: 4× mazāk pieprasījumu lēnajam WMS (atbild ~5 s neatkarīgi no izmēra)
  const SLIDENS_M = 15000;  // ceļu meteostacijas "zona": rādiuss ap staciju
  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const saite = (url, t) => `<a href="${url}" target="_blank" rel="noopener">${t}</a>`;
  const laiks = iso => iso ? new Date(iso).toLocaleString('lv-LV', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' }) : '';
  const LVC_AVOTS = saite('https://transportdata.gov.lv', 'LVC / transportdata.gov.lv') + ' · CC0';
  const SATIKSME = ['brīva', 'lēna', 'sastrēgums', 'nav datu'];  // limenis 0–3 no /api/satiksme

  // Reģistrs. krasas(v) → [aizpildījums rgba, robeža rgb] pēc maskas vērtības v (1–255).
  // skaitit(v) — vai šī vieta skaitās riska zona pārklāšanās aprēķinā; svitrot(v) — svītrots aizpildījums.
  // poligoni: [{ gredzeni: [[[lat, lon], ...], ...] | aplis: [lat, lon, metri], v, teksts, bbox }]
  const ZONAS = [
    {
      kods: 'pludi', nosaukums: 'plūdu riska zona',
      apraksts: 'Plūdu riska zona: applūst vismaz reizi 100 gados (1 % varbūtība gadā)',
      avots: saite('https://data.gov.lv/dati/lv/dataset/3-cikla-latvijas-pldu-postjumu-vietu-un-pldu-riska-kartes1', 'LVĢMC plūdu riska kartes 2026–2031') + ' · CC0',
      minZoom: 8,
      // slānis 1 = 1 % (100 gadu) applūšana; pārklājums [dienvidi, rietumi, ziemeļi, austrumi] — ārpus tā nepieprasām;
      // paka — nosaukums API flīzēm (karte_api.py PLUDU_PAKAS ar tiem pašiem ceļiem un pārklājumiem)
      wms: [
        { paka: 'pali', cels: '3._cikla_L_557_7iFPTq/b7ad025f-833a-4b4f-a845-d5cec9d24092', slanis: '1', robezas: [55.76, 20.88, 57.67, 27.92] },  // pavasara pali
        { paka: 'ledus', cels: '3._cikla_L_558_jIS73E/3322e012-8cb3-4a4c-8acf-a467e25a17b3', slanis: '1', robezas: [56.38, 23.95, 56.64, 26.01] },  // ledus sastrēgumi
        { paka: 'juras', cels: '3._cikla_L_556_karVbb/cc6f2ed3-dbfb-42d0-98e1-4d9f10f57fea', slanis: '1', robezas: [56.06, 20.84, 57.88, 24.49] },  // jūras vējuzplūdi
      ],
      krasas: () => [[37, 99, 235, 90], [29, 78, 216]],
    },
    {
      kods: 'bridinajumi', nosaukums: 'LVĢMC brīdinājuma apgabals',
      avots: saite('https://data.gov.lv/dati/lv/dataset/hidrometeorologiskie-bridinajumi', 'LVĢMC hidrometeoroloģiskie brīdinājumi') + ' · CC0',
      sledzis: { id: 'bridinajumu-slanis', teksts: 'Brīdinājumu apgabali (LVĢMC)', krasa: '#eab308', nav: 'šobrīd nav' },
      poligoni: [],  // v: līmenis 1–3 (+4, ja hidroloģisks)
      // pārklāšanos veido tikai oranžie/sarkanie vai ar ūdeni saistītie brīdinājumi — visas Latvijas dzeltenais vējš ne
      skaitit: v => (v & 3) >= 2 || (v & 4) > 0,
      krasas: v => (v &= 3) >= 3 ? [[220, 38, 38, 45], [185, 28, 28]] : v === 2 ? [[234, 88, 12, 45], [194, 65, 12]] : [[234, 179, 8, 45], [161, 98, 7]],
      ieladet: ieladetBridinajumus,
    },
    {
      kods: 'satiksme', nosaukums: 'satiksme (LVC)',
      avots: LVC_AVOTS,
      sledzis: { id: 'satiksmes-slanis', teksts: 'Satiksme pa novadiem (LVC, tiešsaistē)', krasa: '#f59e0b', nav: 'dati nav pieejami' },
      poligoni: [],  // v: limenis + 1 (1 brīva, 2 lēna, 3 sastrēgums, 4 nav datu)
      skaitit: v => v === 3,  // brīva vai lēna satiksme nav risks; sastrēgums ir (evakuācija, palīdzības piekļuve)
      krasas: v => v === 1 ? [[22, 163, 74, 55], [21, 128, 61]] : v === 2 ? [[245, 158, 11, 70], [180, 83, 9]]
        : v === 3 ? [[220, 38, 38, 80], [153, 27, 27]] : [[120, 113, 108, 50], [87, 83, 78]],
      legenda: '<span class="skala"><i style="background:#16a34a"></i>brīva <i style="background:#f59e0b"></i>lēna ' +
        '<i style="background:#dc2626"></i>sastrēgums <i style="background:#a8a29e"></i>nav datu</span>',
      ieladet: ieladetSatiksmi,
    },
    {
      kods: 'slidens', nosaukums: 'slidens ceļš (LVC meteostacija)',
      avots: LVC_AVOTS,
      sledzis: { id: 'slidena-slanis', teksts: 'Slidens ceļš (LVC ceļu meteostacijas, 15 km)', krasa: '#38bdf8', nav: 'dati nav pieejami' },
      poligoni: [],  // v: 1 nav slidens, 2 slidens
      skaitit: v => v === 2,
      svitrot: v => v === 2,
      krasas: v => v === 2 ? [[56, 189, 248, 90], [3, 105, 161]] : [[186, 230, 253, 45], [125, 211, 252]],
      ieladet: ieladetSatiksmi,
    },
  ];
  const PARKLAJUMS = { aizp: [127, 29, 29, 120], svitra: [185, 28, 28, 210], robeza: [220, 38, 38] };
  const ieslegtas = new Set();
  const maskas = new Map();  // `${z}/${x}/${y}` → { kods: Uint8Array } (WMS zonām; klikšķim un pārzīmēšanai)
  const MASKU_MAX = 64;  // katra maska 512×512 B ≈ 262 KB → ≤ ~17 MB telefonā; LRU: Map secība = pēdējā lietošana
  const maskaKese = atslega => {
    const k = maskas.get(atslega);
    if (k) { maskas.delete(atslega); maskas.set(atslega, k); }
    return k;
  };
  const zona = kods => ZONAS.find(z => z.kods === kods);

  function attels(url) {
    return new Promise((ok, nav) => {
      const img = new Image();
      img.crossOrigin = 'anonymous';
      img.onload = () => ok(img);
      img.onerror = nav;
      img.src = url;
    });
  }

  function flizesRobezas(coords) {
    const nw = karte.unproject(coords.scaleBy(L.point(LIELUMS, LIELUMS)), coords.z);
    const se = karte.unproject(coords.add([1, 1]).scaleBy(L.point(LIELUMS, LIELUMS)), coords.z);
    return { nw, se };
  }

  // Plūdu flīze caur API (diska kešs): XYZ z = Leaflet z − 1, jo Leaflet flīze ir 512 px. X-Flize: aiznemts (API rindā
  // jau 4 pieprasījumi uz LVĢMC) — vēlreiz pēc 2, 4, 6 s; 404 — API bez šī galapunkta (vecāka versija) → tiešais WMS.
  let bezApiFlizem = false;
  async function apiFlize(s, coords) {
    for (let reize = 0; reize < 4; reize++) {
      const r = await fetch(`${PLUDU_FLIZE}${s.paka}/${coords.z - 1}/${coords.x}/${coords.y}.png`);
      if (r.status === 404) { bezApiFlizem = true; return null; }
      if (!r.ok) throw new Error('plūdu flīze ' + r.status);
      if (r.headers.get('X-Flize') !== 'aiznemts') return createImageBitmap(await r.blob());
      await new Promise(ok => setTimeout(ok, 2000 * (reize + 1)));
    }
    throw new Error('plūdu flīžu rinda pilna');
  }

  // WMS flīze EPSG:3857 tieši Leaflet flīzes robežās (bez izkropļojumiem); serviss mēdz atbildēt lēni — vienreiz atkārtojam
  async function wmsMaska(z, coords) {
    const { nw, se } = flizesRobezas(coords);
    const a = L.CRS.EPSG3857.project(nw), b = L.CRS.EPSG3857.project(se);
    const maska = new Uint8Array(LIELUMS * LIELUMS);
    const kanva = document.createElement('canvas');
    kanva.width = kanva.height = LIELUMS;
    const ctx = kanva.getContext('2d', { willReadFrequently: true });
    for (const s of z.wms) {
      const [d, r, zi, a2] = s.robezas;
      if (se.lat > zi || nw.lat < d || se.lng < r || nw.lng > a2) continue;
      let img = bezApiFlizem ? null : await apiFlize(s, coords);
      if (!img) {
        const url = PLUDU_WMS + s.cels + '?' + new URLSearchParams({
          service: 'WMS', version: '1.3.0', request: 'GetMap', layers: s.slanis, styles: '', crs: 'EPSG:3857',
          bbox: [a.x, b.y, b.x, a.y].join(','), width: LIELUMS, height: LIELUMS, format: 'image/png', transparent: 'TRUE',
        });
        try { img = await attels(url); } catch { img = await attels(url + '&r=1'); }
      }
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

  // ---- Formas: gredzeni (poligons/multipoligons, evenodd) vai aplis ----
  function bbox(p) {
    if (p.aplis) {
      const [lat, lon, m] = p.aplis, dLat = m / 111320, dLon = m / (111320 * Math.cos(lat * Math.PI / 180));
      return [lat - dLat, lon - dLon, lat + dLat, lon + dLon];
    }
    const b = [90, 180, -90, -180];
    for (const g of p.gredzeni) for (const [lat, lon] of g) {
      b[0] = Math.min(b[0], lat); b[1] = Math.min(b[1], lon); b[2] = Math.max(b[2], lat); b[3] = Math.max(b[3], lon);
    }
    return b;
  }
  const forma = (gredzeni, v, teksts, papildus = {}) => { const p = { gredzeni, v, teksts, ...papildus }; p.bbox = bbox(p); return p; };
  const aplis = (lat, lon, m, v, teksts, papildus = {}) => { const p = { aplis: [lat, lon, m], v, teksts, ...papildus }; p.bbox = bbox(p); return p; };

  function attalumsM(a, b) {
    const R = 6371000, r = Math.PI / 180;
    const x = (b.lng - a.lng) * r * Math.cos((a.lat + b.lat) / 2 * r), y = (b.lat - a.lat) * r;
    return Math.sqrt(x * x + y * y) * R;
  }
  function punktsGredzena(lat, lon, g) {
    let iekša = false;
    for (let i = 0, j = g.length - 1; i < g.length; j = i++) {
      const [yi, xi] = g[i], [yj, xj] = g[j];
      if ((yi > lat) !== (yj > lat) && lon < (xj - xi) * (lat - yi) / (yj - yi) + xi) iekša = !iekša;
    }
    return iekša;
  }
  function formaSatur(p, ll) {
    const [s, w, n, e] = p.bbox;
    if (ll.lat < s || ll.lat > n || ll.lng < w || ll.lng > e) return false;
    if (p.aplis) return attalumsM(ll, L.latLng(p.aplis[0], p.aplis[1])) <= p.aplis[2];
    return p.gredzeni.reduce((iek, g) => iek !== punktsGredzena(ll.lat, ll.lng, g), false);  // evenodd: caurumi un daļas
  }

  // Formas → maska ar vērtību v; vienādas v formas zīmē vienā ceļā (viens getImageData uz vērtību), augstākā v uzvar
  function poligonuMaska(z, coords) {
    const { nw, se } = flizesRobezas(coords);
    const redzamas = z.poligoni.filter(({ bbox: [s, w, n, e] }) => !(s > nw.lat || n < se.lat || w > se.lng || e < nw.lng));
    if (!redzamas.length) return null;
    const kanva = document.createElement('canvas');
    kanva.width = kanva.height = LIELUMS;
    const ctx = kanva.getContext('2d', { willReadFrequently: true });
    const sakums = coords.scaleBy(L.point(LIELUMS, LIELUMS));
    const pt = (lat, lon) => karte.project([lat, lon], coords.z).subtract(sakums);
    const mpp = 40075016.686 / (256 * 2 ** coords.z);  // metri pikselī ekvatorā
    const maska = new Uint8Array(LIELUMS * LIELUMS);
    const vertibas = [...new Set(redzamas.map(p => p.v))].sort((a, b) => (a & 3) - (b & 3) || a - b);
    for (const v of vertibas) {
      ctx.clearRect(0, 0, LIELUMS, LIELUMS);
      ctx.beginPath();
      for (const p of redzamas) {
        if (p.v !== v) continue;
        if (p.aplis) {
          const [lat, lon, m] = p.aplis, c = pt(lat, lon);
          ctx.moveTo(c.x + m / (mpp * Math.cos(lat * Math.PI / 180)), c.y);
          ctx.arc(c.x, c.y, m / (mpp * Math.cos(lat * Math.PI / 180)), 0, 2 * Math.PI);
          continue;
        }
        for (const g of p.gredzeni) g.forEach(([lat, lon], i) => { const t = pt(lat, lon); i ? ctx.lineTo(t.x, t.y) : ctx.moveTo(t.x, t.y); });
      }
      ctx.fill('evenodd');
      const px = ctx.getImageData(0, 0, LIELUMS, LIELUMS).data;
      for (let i = 0; i < maska.length; i++) if (px[i * 4 + 3] > 127) maska[i] = v;
    }
    return maska;
  }

  const robeza = (m, x, y) => {  // vai pikselis ir maskas malā (blakus cita vērtība); flīzes malas neskaitās
    const v = m(y * LIELUMS + x);
    for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) {
      const xx = x + dx, yy = y + dy;
      if (xx >= 0 && yy >= 0 && xx < LIELUMS && yy < LIELUMS && m(yy * LIELUMS + xx) !== v) return true;
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
      if (skaits[i] >= 2) { krasot(i, (x + y) % 8 < 2 ? PARKLAJUMS.svitra : PARKLAJUMS.aizp); continue; }
      // virsū riska zona (šeit tāda ir ne vairāk kā viena), citādi pēdējā reģistrā — satiksmes fons nepārklāj plūdus
      let virsu = null;
      for (const [z, m] of saraksts) {
        if (!m[i]) continue;
        virsu = [z, m[i]];
        if (!z.skaitit || z.skaitit(m[i])) break;
      }
      if (!virsu) continue;
      const [z, v] = virsu, [aizp, mala] = z.krasas(v);
      krasot(i, z.svitrot?.(v) && (x - y + LIELUMS) % 8 < 2 ? [...mala, 200] : aizp);
    }
    for (const [z, m] of saraksts) for (let y = 0; y < LIELUMS; y++) for (let x = 0; x < LIELUMS; x++) {
      const i = y * LIELUMS + x;
      if (m[i] && skaits[i] < 2 && robeza(j => m[j], x, y)) krasot(i, z.krasas(m[i])[1]);
    }
    for (let y = 0; y < LIELUMS; y++) for (let x = 0; x < LIELUMS; x++) {
      const i = y * LIELUMS + x;
      if (skaits[i] >= 2 && robeza(j => skaits[j] >= 2 ? 1 : 0, x, y)) krasot(i, PARKLAJUMS.robeza);
    }
    ctx.putImageData(img, 0, 0);
  }

  // Poligonu zonas (satiksme, slidens, brīdinājumi) zīmē uzreiz; plūdu WMS maska pienāk vēlāk (serviss atbild 5–60 s)
  // un tad flīzi pārzīmē — lēns vai nepieejams WMS neaiztur pārējās zonas
  let gaidaWms = 0;
  const Slanis = L.GridLayer.extend({
    createTile(coords, gatavs) {
      const kanva = L.DomUtil.create('canvas', 'zonu-flize');
      kanva.width = kanva.height = LIELUMS;
      const atslega = `${coords.z}/${coords.x}/${coords.y}`;
      const aktivas = ZONAS.filter(z => ieslegtas.has(z.kods) && coords.z >= (z.minZoom || 0));
      const poligonu = aktivas.filter(z => !z.wms && z.poligoni.length).map(z => [z, poligonuMaska(z, coords)]).filter(([, m]) => m);
      const wms = aktivas.filter(z => z.wms);
      const kese = maskaKese(atslega) || {};
      const gatavas = () => wms.filter(z => kese[z.kods]).map(z => [z, kese[z.kods]]);
      zimet(kanva, [...gatavas(), ...poligonu].sort((a, b) => ZONAS.indexOf(a[0]) - ZONAS.indexOf(b[0])));
      setTimeout(() => gatavs(null, kanva), 0);
      const trukst = wms.filter(z => !kese[z.kods]);
      if (!trukst.length) return kanva;
      gaidaWms++; atjaunotLegendu();
      Promise.all(trukst.map(z => wmsMaska(z, coords).then(m => { kese[z.kods] = m; }, () => { ielade = 'kluda'; }))).then(() => {
        maskas.delete(atslega);
        maskas.set(atslega, kese);
        while (maskas.size > MASKU_MAX) maskas.delete(maskas.keys().next().value);
        if (kanva.isConnected) zimet(kanva, [...gatavas(), ...poligonu].sort((a, b) => ZONAS.indexOf(a[0]) - ZONAS.indexOf(b[0])));
        gaidaWms--; atjaunotLegendu();
      });
      return kanva;
    },
  });
  const slanis = new Slanis({
    tileSize: LIELUMS, zIndex: 250, updateWhenZooming: false, updateWhenIdle: true, keepBuffer: 1,
    attribution: 'Zonas: ' + saite('https://data.gov.lv/dati/lv/dataset/3-cikla-latvijas-pldu-postjumu-vietu-un-pldu-riska-kartes1', 'LVĢMC') + ', ' + saite('https://transportdata.gov.lv', 'LVC') + ' (CC0)',
  });

  // Leģenda kartes stūrī, kamēr kāda zona ieslēgta
  const legenda = L.control({ position: 'bottomright' });  // kreisajā pusē ir "Prognoze" panelis (prognozes.js)
  legenda.onAdd = () => L.DomUtil.create('div', 'zonu-legenda');
  function atjaunotLegendu() {
    const div = legenda.getContainer();
    if (!div) return;
    const z = karte.getZoom();
    div.innerHTML = ZONAS.filter(x => ieslegtas.has(x.kods)).map(x => {
      if (x.legenda) return x.legenda;
      const v = x.svitrot ? 2 : 1, [a, r] = x.krasas(v);
      const fons = x.svitrot ? `repeating-linear-gradient(-45deg, rgb(${r}) 0 2px, rgba(${a.slice(0, 3)},${a[3] / 255}) 2px 6px)` : `rgba(${a.slice(0, 3)},${a[3] / 255})`;
      return `<span><i style="background:${fons};border-color:rgb(${r})"></i>${esc(x.nosaukums)}</span>`;
    }).join('') +
      (ieslegtas.size >= 2 ? '<span><i class="parklajas"></i>paaugstināts risks (zonas pārklājas)</span>' : '') +
      (ieslegtas.has('pludi') && z < 8 ? '<small>Tuviniet karti, lai redzētu plūdu zonas</small>' : '') +
      (gaidaWms && ieslegtas.has('pludi') ? '<small>Ielādē plūdu zonas… LVĢMC serviss var atbildēt līdz minūtei</small>' : '') +
      (ielade === 'kluda' && ieslegtas.has('pludi') ? '<small>Daļa plūdu zonu neielādējās (LVĢMC serviss neatbild). Pabīdiet karti, lai mēģinātu vēlreiz.</small>' : '');
  }

  function radit(kods, ieslegt) {
    if (ieslegt) ieslegtas.add(kods); else ieslegtas.delete(kods);
    if (kods === 'satiksme') { if (ieslegt) satiksmesPunkti.addTo(karte); else satiksmesPunkti.remove(); }
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
  karte.on('moveend', () => { if (!gaidaWms && ielade === 'kluda') { ielade = ''; atjaunotLegendu(); } });
  karte.on('zoomend', atjaunotLegendu);

  // ---- Klikšķis: kuras zonas ir šajā vietā; ja divas vai vairāk riska zonas — brīdinājums par paaugstinātu risku ----
  function zonasVieta(ll) {
    const z = karte.getZoom(), p = karte.project(ll, z).floor();
    const x = Math.floor(p.x / LIELUMS), y = Math.floor(p.y / LIELUMS);
    const kese = maskaKese(`${z}/${x}/${y}`) || {};
    const i = (p.y - y * LIELUMS) * LIELUMS + (p.x - x * LIELUMS);
    const atrastas = [];
    for (const zn of ZONAS) {
      if (!ieslegtas.has(zn.kods)) continue;
      if (zn.wms) { if (kese[zn.kods]?.[i]) atrastas.push({ zona: zn, teksts: zn.apraksts, skaitas: true }); continue; }
      const sheit = zn.poligoni.filter(pp => formaSatur(pp, ll));
      if (sheit.length) atrastas.push({ zona: zn, teksts: sheit.map(pp => pp.teksts).join('; '), skaitas: sheit.some(pp => !zn.skaitit || zn.skaitit(pp.v)) });
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
      const riski = atrastas.filter(a => a.skaitas);
      const augsts = new Set(riski.map(a => a.zona.kods)).size >= 2;
      L.popup({ maxWidth: Math.min(300, karte.getSize().x - 70) }).setLatLng(e.latlng).setContent(
        '<div class="popup zonu-popup">' +
        (augsts ? `<b class="paaugstinats">Paaugstināts risks</b><p>Šeit pārklājas: ${riski.map(a => esc(a.zona.nosaukums)).join(' + ')}; ieteicams izvairīties.</p>` : '') +
        atrastas.map(a => `<p><b>${esc(a.zona.nosaukums[0].toUpperCase() + a.zona.nosaukums.slice(1))}</b><br>${a.teksts}` +
          `<br><small class="popup-avots">Avots: ${a.zona.avots}</small></p>`).join('') +
        '</div>').openOn(karte);
    }, 0);
  });

  // ---- Brīdinājumu apgabali ----
  const LIMENI = { 1: 'Dzeltenais', 2: 'Oranžais', 3: 'Sarkanais' };
  const bridForma = (punkti, limenis, paradiba, lidz) => forma([punkti],
    limenis | (/lietus|plūd|vējuzplūd|pali|sastrēg|ūdens/i.test(paradiba) ? 4 : 0),
    esc(`${LIMENI[limenis] || 'Dzeltenais'} brīdinājums: ${String(paradiba).toLowerCase()}${lidz ? `, līdz ${lidz}` : ''}`));
  // Vispirms /api/prognozes: poligoni tur jau vienkāršoti (~1 km pielaide; neapstrādātais "Latvija" ir ~42 000 virsotņu,
  // ~1 MB) un serverī kešoti 5 min. "Līdz" ņem no tā paša brīdinājuma ziņas virsraksta. Ja prognozes nav pieejamas
  // vai tajās nav poligonu — neapstrādātie no /api/bridinajumi?poligoni=1 (bez brīdinājumiem tā atbilde ir maza).
  async function ieladetBridinajumus() {
    try {
      const r = await fetch('/api/prognozes');
      if (r.ok) {
        const d = await r.json();
        const lidz = Object.fromEntries((d.zinas || []).filter(z => z.veids === 'bridinajums')
          .map(z => [z.id, (/, līdz ([\d.: ]+)$/.exec(z.virsraksts || '') || [])[1]]));
        const poligoni = (d.bridinajumu_poligoni || []).filter(p => p.poligons?.length >= 3)
          .map(p => bridForma(p.poligons, p.limenis, p.paradiba, lidz[p.id]));
        if (poligoni.length) return (zona('bridinajumi').poligoni = poligoni).length;
      }
    } catch { /* rezerve zemāk */ }
    const r = await fetch('/api/bridinajumi?poligoni=1');
    if (!r.ok) throw new Error(r.status);
    zona('bridinajumi').poligoni = (await r.json()).bridinajumi.flatMap(b => (b.poligoni || []).map(punkti =>
      bridForma(punkti, b.limenis, b.paradiba, b.lidz ? laiks(b.lidz) : '')));
    return zona('bridinajumi').poligoni.length;
  }

  // ---- Satiksme, ceļu meteostacijas, robežpunkti: /api/satiksme (kešots 5 min) ----
  // Zonas: tips "regions" — novada/valstspilsētas robeža (/api/prognozes/robezas, citādi /api/regioni/<kods>), "rezgis" — bbox.
  // Novadi bez uzskaites iekārtām ir pelēki ("nav mērījumu"). Avots katrai datu kopai no `kopas` (LVC NAP, CC0).
  let satiksmesDati = null, satiksmesLaiks = 0, robezas = null;
  const gredzeni = geom => (geom.type === 'MultiPolygon' ? geom.coordinates : [geom.coordinates]).flat().map(g => g.map(([lon, lat]) => [lat, lon]));
  const kopasAvots = k => k?.datu_kopa_url ? `${saite(esc(k.datu_kopa_url), esc(k.nosaukums))} (LVC) · ${esc(k.licence || 'CC0 1.0')}` : LVC_AVOTS;
  async function satiksme() {
    if (satiksmesDati && Date.now() - satiksmesLaiks < 300000) return satiksmesDati;
    const [d, r] = await Promise.all([
      fetch('/api/satiksme').then(x => x.ok ? x.json() : Promise.reject(new Error(x.status))),
      robezas || fetch('/api/prognozes/robezas').then(x => x.ok ? x.json() : null).catch(() => null),
    ]);
    if (r) robezas = r;
    const kopas = d.kopas || {};
    const robezaPecKoda = Object.fromEntries((robezas?.features || []).map(f => [String(f.properties?.kods ?? f.id), f]));
    const zonas = d.zonas || [];
    await Promise.all(zonas.filter(z => z.tips !== 'rezgis' && !robezaPecKoda[z.kods]).map(z =>
      fetch('/api/regioni/' + encodeURIComponent(z.kods)).then(x => x.ok ? x.json() : null).then(f => { if (f?.geometry) robezaPecKoda[z.kods] = f; }, () => {})));
    zona('satiksme').avots = kopasAvots(kopas.merijumi) + '<br>' + kopasAvots(kopas.vietas);
    const arDatiem = new Set();
    zona('satiksme').poligoni = zonas.flatMap(z => {
      const lim = Math.min(3, Math.max(0, +z.limenis || 0));
      let g;
      if (z.tips === 'rezgis' && z.bbox) { const [w, s, e, n] = z.bbox; g = [[[s, w], [n, w], [n, e], [s, e]]]; }
      else if (robezaPecKoda[z.kods]?.geometry) g = gredzeni(robezaPecKoda[z.kods].geometry);
      if (!g) return [];
      arDatiem.add(String(z.kods));
      return [forma(g, lim + 1, satiksmesTeksts(z), { dati: z, nosaukums: z.nosaukums })];
    }).concat((robezas?.features || []).filter(f => f.geometry && !arDatiem.has(String(f.properties?.kods ?? f.id))).map(f =>
      forma(gredzeni(f.geometry), 4, `${esc(f.properties?.nosaukums)}: nav mērījumu (šajā novadā nav LVC satiksmes uzskaites iekārtu)`,
        { dati: { limenis: 3 }, nosaukums: f.properties?.nosaukums })));
    // ceļu meteostacijas: temperatūru LVC atvērtajos datos nav — tikai "slidens: jā/nē"
    const slidensKopas = new Set();
    zona('slidens').poligoni = (d.stacijas || []).filter(s => s.lat && s.lon).map(s => {
      slidensKopas.add(s.avots);
      return aplis(+s.lat, +s.lon, SLIDENS_M, s.slidens ? 2 : 1, stacijasTeksts(s, kopas[s.avots]), { dati: s, avots: kopasAvots(kopas[s.avots]) });
    });
    zona('slidens').avots = [...slidensKopas].map(k => kopasAvots(kopas[k])).join('<br>') || kopasAvots(kopas.slidens_meteo);
    satiksmesPunkti.clearLayers();
    for (const p of d.punkti || []) {
      if (!p.lat || !p.lon) continue;
      const lim = Math.min(3, Math.max(0, +p.limenis || 0));
      L.circleMarker([p.lat, p.lon], { radius: 5, color: '#fff', weight: 1.5, fillColor: PUNKTU_KRASAS[lim], fillOpacity: 1 })
        .bindPopup(`<div class="popup"><b>Satiksmes uzskaites iekārta${p.nosaukums ? ' ' + esc(p.nosaukums) : ''}</b><br>Satiksme: <b>${SATIKSME[lim]}</b>` +
          (p.atrums != null ? `<br>Ātrums ${Math.round(p.atrums)} km/h${p.atrums_brivs != null ? ` (brīvā plūsmā ~${Math.round(p.atrums_brivs)} km/h)` : ''}` : '') +
          (p.plusma_h != null ? `<br>${p.plusma_h} transportlīdzekļi stundā` : '') + (p.laiks ? `<br><small>Mērīts ${laiks(p.laiks)}</small>` : '') +
          `<br><small class="popup-avots">Avots: ${kopasAvots(kopas.merijumi)}</small></div>`).addTo(satiksmesPunkti);
    }
    for (const b of d.robezas || []) {
      if (!b.lat || !b.lon) continue;
      const min = b.gaidisana_min;
      L.marker([b.lat, b.lon], {
        icon: L.divIcon({ className: 'robezas-ikona', html: `<span>${min == null ? '?' : Math.round(min)}<small>min</small></span>`, iconSize: [40, 28] }),
        title: `${b.nosaukums}: gaidīšana ${min == null ? 'nav datu' : Math.round(min) + ' min'}`,
      }).bindPopup(`<div class="popup"><b>Robežpunkts ${esc(b.nosaukums)}</b>${b.virziens ? `<br>Virziens: ${esc(b.virziens)}` : ''}` +
        `<br>Gaidīšana: ${min == null ? 'nav datu' : `<b>${Math.round(min)} min</b>`}${b.laiks ? `<br><small>Dati: ${laiks(b.laiks)}</small>` : ''}` +
        `<br><small class="popup-avots">Avots: ${kopasAvots(kopas.robezas)}</small></div>`).addTo(satiksmesPunkti);
    }
    satiksmesDati = d; satiksmesLaiks = Date.now();
    return d;
  }
  const PUNKTU_KRASAS = ['#16a34a', '#f59e0b', '#dc2626', '#a8a29e'];
  const satiksmesPunkti = L.layerGroup();  // uzskaites iekārtas un robežpunkti — kopā ar satiksmes zonām
  function satiksmesTeksts(z) {
    const lim = Math.min(3, Math.max(0, +z.limenis || 0));
    return `${esc(z.nosaukums)}: <b>${SATIKSME[lim]}</b>` +
      (z.atrums_vid != null ? `<br>Vidējais ātrums ${Math.round(z.atrums_vid)} km/h` + (z.atrums_brivs != null ? ` (brīvā plūsmā ~${Math.round(z.atrums_brivs)} km/h)` : '') : '') +
      (z.plusma_h != null ? `<br>${z.plusma_h} transportlīdzekļi stundā` : '') +
      `<br><small>${z.iekartas != null ? `${z.iekartas} uzskaites iekārtas, ` : ''}${z.merijumi != null ? `${z.merijumi} mērījumi` : ''}${z.laiks ? ', ' + laiks(z.laiks) : ''}</small>`;
  }
  function stacijasTeksts(s, kopa) {
    const nos = s.nosaukums && !/^slippery$/i.test(s.nosaukums) ? esc(s.nosaukums) : 'Ceļa meteostacija';
    const t = v => `${(+v).toFixed(1).replace('.', ',')} °C`;
    return `${nos}: slidens — <b>${s.slidens ? 'jā' : 'nē'}</b>` +
      (s.cela_temp != null ? `<br>Ceļa virsma ${t(s.cela_temp)}${s.gaisa_temp != null ? `, gaiss ${t(s.gaisa_temp)}` : ''}` : '') +
      (s.laiks ? `<br><small>Dati: ${laiks(s.laiks)}${kopa ? ' · ' + esc(kopa.nosaukums) : ''}</small>` : '');
  }
  async function ieladetSatiksmi() {
    await satiksme();
    return zona('satiksme').poligoni.length + zona('slidens').poligoni.length + satiksmesPunkti.getLayers().length;
  }

  // Rinda rezultātu kartītē (meklesana.js): satiksme apvidū, kurā ir sākumpunkts, un slidens ceļš 15 km rādiusā
  async function satiksmesRinda(vieta) {
    await satiksme();
    const ll = L.latLng(+vieta.lat, +vieta.lon);
    const z = zona('satiksme').poligoni.find(p => formaSatur(p, ll));
    const sl = zona('slidens').poligoni.filter(p => p.v === 2 && formaSatur(p, ll))
      .map(p => [p, attalumsM(ll, L.latLng(p.aplis[0], p.aplis[1]))]).sort((a, b) => a[1] - b[1])[0];
    if (!z && !sl) return '';
    const d = z?.dati, lim = d ? Math.min(3, Math.max(0, +d.limenis || 0)) : 3;
    return '<ul class="fakti">' +
      (z ? `<li><span class="ikona">${Ik('auto')}</span><div><b>Satiksme šajā apvidū</b><span>${lim === 3 ? 'nav mērījumu' : SATIKSME[lim]}` +
        (d.atrums_vid != null && lim < 3 ? ` (vid. ${Math.round(d.atrums_vid)} km/h)` : '') + `</span>` +
        `<small>${esc(z.nosaukums || '')}${d.laiks ? ', ' + laiks(d.laiks) : ''}</small><small class="avots-rinda">${zona('satiksme').avots}</small></div></li>` : '') +
      (sl ? `<li><span class="ikona">${Ik('sniegs')}</span><div><b>Slidens ceļš tuvumā</b><span>LVC ziņo par slidenu ceļu ${(sl[1] / 1000).toFixed(0)} km no šīs vietas</span>` +
        `<small class="avots-rinda">${sl[0].avots}</small></div></li>` : '') + '</ul>';
  }

  // ---- Slēdži panelī zem plūdu zonām (pēc reģistra secības) ----
  let pec = document.getElementById('pludu-slanis')?.closest('label');
  for (const zn of ZONAS.filter(x => x.sledzis && pec)) {
    const { id, teksts, krasa, nav } = zn.sledzis;
    const l = document.createElement('label');
    l.className = 'kat parklajums';
    l.innerHTML = `<input type="checkbox" id="${id}">${Ikonas.formaSvg('kvadrats', krasa, 16)}${esc(teksts)}`;
    pec.after(l);
    pec = l;
    const cb = l.querySelector('input');
    cb.addEventListener('change', async () => {
      if (!cb.checked) return radit(zn.kods, false);
      try {
        if (!zn.poligoni.length && !await zn.ieladet()) {
          cb.checked = false;
          l.lastChild.textContent = `${teksts}: ${nav}`;
          return;
        }
        l.lastChild.textContent = teksts;
        radit(zn.kods, true);
      } catch {
        cb.checked = false;
        l.lastChild.textContent = `${teksts}: neizdevās ielādēt`;
      }
    });
  }

  return { radit, zonasVieta, satiksmesRinda, ZONAS };
})();
