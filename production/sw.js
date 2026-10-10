// map.repo.lv bezsaistes režīms (service worker; reģistrē atjaunot.js, tikai https vai localhost).
// Jauna VERSION: install → skipWaiting, activate → vecie shell-* keši prom + clients.claim; atjaunot.js tad rāda
// "Pieejama jauna versija · Atsvaidzināt" (lapu pati nepārlādē). ?svaigs=1 noņem SW un visus kešus.
//
// - Lapa un mūsu JS/CSS/JSON: vispirms tīkls (vienmēr svaigs pēc deploy), bez tīkla — saglabātā kopija.
//   Tāpēc VERSION jāmaina TIKAI tad, ja mainās šis fails vai SHELL saraksts (citādi pārlūks sw.js neatjauno);
//   parastiem production/ labojumiem nekas nav jādara (VPS nav build soļa).
// - Leaflet no unpkg (versija URL): kešs vispirms.
// - Kartes fona flīzes (OSM, OpenTopoMap): kešs vispirms; ~2500 flīžu (~50 MB), vecākās izmet.
// - /api/*: vispirms tīkls; katru veiksmīgo atbildi saglabā ar laiku (galvene x-sw-saglabats). Bez tīkla —
//   saglabātā, ja nav vecāka par 6 h (mainīgie dati: brīdinājumi, ūdens, ceļi, satiksme…) vai 7 dienām (vietas,
//   slāņi, adreses); atbildei pievieno x-sw-no-kesas: 1, lai lapa var rādīt "saglabāts <laiks>".
// - Plūdu zonu flīzes /api/pludi/flize/…: kešs vispirms, bez 8 s termiņa (LVĢMC caur API atbild līdz 30 s); ≤ 800 flīžu;
//   "aizņemts" un kļūdas (Cache-Control: no-store) nesaglabā.
const VERSION = '2026-10-10cc-kartites3';
const SHELL = 'shell-' + VERSION, API = 'api-v1', FLIZES = 'flizes-v1', CDN = 'cdn-v1';
// Saraksts ģenerēts: uv run --no-project --python 3.12 src/testi/sw_faili.py --rakstit (no index/info/statuss/api/trukstosie
// .html un to JS/CSS/JSON atsaucēm). Pēc jauna faila pievienošanas palaidiet to un nomainiet VERSION.
const SHELL_FAILI = [
  './', 'index.html', 'info.html', 'statuss.html', 'api.html', 'trukstosie.html', 'scenariji.json',
  'vendor/leaflet/leaflet.css', 'vendor/leaflet/MarkerCluster.css', 'manifest.webmanifest', 'ikonas/ikona.svg',
  'ikonas/ikona-32.png', 'ikonas/ikona-180.png', 'stils.css', 'demo.css', 'izmainas.css', 'darbvirsma.css',
  'ikonas/ikonas.svg', 'vendor/leaflet/leaflet.js', 'vendor/leaflet/leaflet.markercluster.js', 'pieejamiba.js',
  'atjaunot.js', 'offline.js', 'ikonas.js', 'avoti.js', 'klasifikators.js', 'valoda.js', 'objekta-statuss.js',
  'app.js', 'marsruts.js', 'zonas.js', 'meklesana.js', 'dalities.js', 'runa.js', 'apaksa.js', 'saraksts.js',
  'bridinajumi.js', 'zibens.js', 'noverojumi.js', 'prognozes.js', 'celi.js', 'zinot.js', 'demo.js', 'izmainas.js',
  'kajene.js', 'atskanot.js', 'sheet.js', 'darbvirsma.js', 'statuss.css', 'info.css', 'statuss.js', 'api.css',
  'openapi.json', 'vendor/leaflet/images/layers.png', 'vendor/leaflet/images/layers-2x.png',
  'vendor/leaflet/images/marker-icon.png', 'ikonas/ikona-192.png', 'ikonas/ikona-512.png', 'lr1.json',
  'vendor/qrcode.js', 'demo/scenariji.json', 'izmainas.json', 'demo/augstumi-ogre.geojson',
];
const CDN_FAILI = [];  // Leaflet tagad ir vendor/leaflet (SHELL_FAILI)
const FLIZU_HOSTI = /(^|\.)tile\.openstreetmap\.org$|(^|\.)tile\.opentopomap\.org$/;
const FLIZU_MAX = 2500;
const API_MAX = 300;  // saglabātās /api atbildes (ar kartes skatiem); vecākās izmet
const PLUDU_FLIZES = 'pludi-flizes-v1', PLUDU_FLIZU_MAX = 800;
const API_MAINIGIE = /^\/api\/(bridinajumi|udens|celi|satiksme|zibens|prognozes?|augsne|statuss|meklejumi|noverojumi|zinojumi|veseliba)/;
const H6 = 6 * 3600e3, D7 = 7 * 24 * 3600e3;

self.addEventListener('install', e => {
  e.waitUntil((async () => {
    const shell = await caches.open(SHELL);
    // pa vienam: viens trūkstošs fails nedrīkst apturēt instalēšanu
    await Promise.all(SHELL_FAILI.map(u => shell.add(new Request(u, { cache: 'reload' })).catch(() => {})));
    const cdn = await caches.open(CDN);
    await Promise.all(CDN_FAILI.map(async u => {
      if (!(await cdn.match(u))) await cdn.add(new Request(u, { mode: 'cors' })).catch(() => {});
    }));
    await self.skipWaiting();
  })());
});

self.addEventListener('activate', e => {
  e.waitUntil((async () => {
    for (const k of await caches.keys()) if (k.startsWith('shell-') && k !== SHELL) await caches.delete(k);
    await self.clients.claim();
  })());
});

// Tīkls ar termiņu: lēnā tīklā pēc `ms` ņem kešu (ja ir). Pēc tīkla kļūdas 15 s neprasām tīklu pirms keša
// (citādi bez sakariem katrs pieprasījums gaida savu kļūdu un lapa atveras lēni); tīklu mēģina fonā.
let bezTiklaLidz = 0;
function tikls(req, ms) {
  if (Date.now() < bezTiklaLidz) {
    fetch(req.clone ? req.clone() : req).then(() => { bezTiklaLidz = 0; }, () => {});
    return Promise.reject(new Error('nesen nebija tīkla'));
  }
  return new Promise((ok, nok) => {
    const t = setTimeout(() => nok(new Error('termiņš')), ms);
    fetch(req).then(r => { clearTimeout(t); bezTiklaLidz = 0; ok(r); },
      e => { clearTimeout(t); bezTiklaLidz = Date.now() + 15000; nok(e); });
  });
}

async function arLaiku(r) {
  const h = new Headers(r.headers);
  h.set('x-sw-saglabats', new Date().toISOString());
  return new Response(await r.clone().blob(), { status: r.status, statusText: r.statusText, headers: h });
}

async function noKesas(c, req, maxVecums) {
  const r = await c.match(req);
  if (!r) return null;
  const laiks = Date.parse(r.headers.get('x-sw-saglabats') || '');
  if (maxVecums && laiks && Date.now() - laiks > maxVecums) return null;
  const h = new Headers(r.headers);
  h.set('x-sw-no-kesas', '1');
  return new Response(await r.blob(), { status: r.status, statusText: r.statusText, headers: h });
}

async function api(req) {
  const c = await caches.open(API);
  const url = new URL(req.url);
  const maxVecums = API_MAINIGIE.test(url.pathname) ? H6 : D7;
  try {
    const r = await tikls(req, 8000);
    // kartes skata punkti (/api/objekti?bbox=…) — katrs skats savs URL, tāpēc API kešam robeža (vecākos izmet)
    if (r.ok) c.put(req, await arLaiku(r)).then(() => { if (url.searchParams.has('bbox')) apgriezt(c, API_MAX); }).catch(() => {});
    return r;
  } catch (e) {
    const k = await noKesas(c, req, maxVecums);
    if (k) return k;
    return new Response(JSON.stringify({ kluda: 'Nav interneta, un saglabātu datu šim pieprasījumam nav.' }), {
      status: 503, headers: { 'Content-Type': 'application/json; charset=utf-8', 'x-sw-bez-tikla': '1' } });
  }
}

async function shell(req) {
  const c = await caches.open(SHELL);
  try {
    // lapas (HTML) vienmēr pārbauda serverī (ETag), nevis ņem no pārlūka HTTP keša — citādi pēc deploy var redzēt veco lapu
    const lapa = req.mode === 'navigate' || /(\/|\.html)$/.test(new URL(req.url).pathname);
    const r = await tikls(lapa ? new Request(req, { cache: 'no-cache' }) : req, 6000);
    if (r.ok && r.type === 'basic') c.put(req, r.clone()).catch(() => {});
    return r;
  } catch (e) {
    const k = await c.match(req, { ignoreSearch: req.mode === 'navigate' });
    if (k) return k;
    if (req.mode === 'navigate') return (await c.match('index.html')) || (await c.match('./')) || Response.error();
    return Response.error();
  }
}

async function kesaVispirms(req, nosaukums, max) {
  const c = await caches.open(nosaukums);
  const k = await c.match(req);
  if (k) return k;
  const r = await fetch(req);
  if (r.ok || r.type === 'opaque') {
    await c.put(req, r.clone()).catch(() => {});
    if (max) apgriezt(c, max);
  }
  return r;
}

async function pluduFlize(req) {
  const c = await caches.open(PLUDU_FLIZES);
  const k = await c.match(req);
  if (k) return k;
  const r = await fetch(req);
  if (r.ok && !/no-store/.test(r.headers.get('Cache-Control') || '')) {
    await c.put(req, r.clone()).catch(() => {});
    apgriezt(c, PLUDU_FLIZU_MAX);
  }
  return r;
}

let apgriez = false;
async function apgriezt(c, max) {
  if (apgriez) return;
  apgriez = true;
  try {
    const keys = await c.keys();  // ievietošanas secībā: vecākās pirmās
    if (keys.length > max) await Promise.all(keys.slice(0, keys.length - max + Math.round(max / 10)).map(k => c.delete(k)));
  } finally { apgriez = false; }
}

// atjaunot.js (statuss.html) jautā aktīvo versiju
self.addEventListener('message', e => {
  if (e.data === 'versija' && e.ports[0]) e.ports[0].postMessage({ versija: VERSION });
});

self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.origin === location.origin) {
    if (url.pathname.startsWith('/api/pludi/flize/')) return e.respondWith(pluduFlize(req));
    if (url.pathname.startsWith('/api/')) return e.respondWith(api(req));
    return e.respondWith(shell(req));
  }
  if (FLIZU_HOSTI.test(url.hostname)) return e.respondWith(kesaVispirms(req, FLIZES, FLIZU_MAX));
  if (url.hostname === 'unpkg.com') return e.respondWith(kesaVispirms(req, CDN, 0));
});
