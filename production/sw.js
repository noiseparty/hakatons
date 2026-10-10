// map.repo.lv bezsaistes režīms (service worker; reģistrē offline.js, tikai https vai localhost).
//
// - Lapa un mūsu JS/CSS/JSON: vispirms tīkls (vienmēr svaigs pēc deploy), bez tīkla — saglabātā kopija.
//   Tāpēc VERSION jāmaina TIKAI tad, ja mainās šis fails vai SHELL saraksts (citādi pārlūks sw.js neatjauno);
//   parastiem production/ labojumiem nekas nav jādara (VPS nav build soļa).
// - Leaflet no unpkg (versija URL): kešs vispirms.
// - Kartes fona flīzes (OSM, OpenTopoMap): kešs vispirms; ~2500 flīžu (~50 MB), vecākās izmet.
// - /api/*: vispirms tīkls; katru veiksmīgo atbildi saglabā ar laiku (galvene x-sw-saglabats). Bez tīkla —
//   saglabātā, ja nav vecāka par 6 h (mainīgie dati: brīdinājumi, ūdens, ceļi, satiksme…) vai 7 dienām (vietas,
//   slāņi, adreses); atbildei pievieno x-sw-no-kesas: 1, lai lapa var rādīt "saglabāts <laiks>".
const VERSION = '2026-10-10n-zonas3';
const SHELL = 'shell-' + VERSION, API = 'api-v1', FLIZES = 'flizes-v1', CDN = 'cdn-v1';
const SHELL_FAILI = [
  './', 'index.html', 'stils.css', 'demo.css', 'info.html', 'info.css', 'api.html', 'api.css', 'statuss.html', 'statuss.css', 'statuss.js',
  'avoti.js', 'klasifikators.js', 'app.js', 'zonas.js', 'meklesana.js', 'runa.js', 'apaksa.js', 'saraksts.js',
  'bridinajumi.js', 'zibens.js', 'prognozes.js', 'celi.js', 'demo.js', 'atskanot.js', 'offline.js', 'scenariji.json', 'darbvirsma.js', 'darbvirsma.css',
  'objekta-statuss.js', 'marsruts.js', 'dalities.js', 'noverojumi.js', 'vendor/qrcode.js', 'ikonas.js', 'ikonas/ikonas.svg', 'vendor/leaflet/leaflet.js', 'vendor/leaflet/leaflet.css',
  'vendor/leaflet/leaflet.markercluster.js', 'vendor/leaflet/MarkerCluster.css',
  'demo/scenariji.json', 'demo/augstumi-ogre.geojson', 'manifest.webmanifest', 'ikonas/ikona.svg',
  'ikonas/ikona-192.png', 'ikonas/ikona-512.png', 'izmainas.css', 'izmainas.js', 'izmainas.json',
];
const CDN_FAILI = [];  // Leaflet tagad ir vendor/leaflet (SHELL_FAILI)
const FLIZU_HOSTI = /(^|\.)tile\.openstreetmap\.org$|(^|\.)tile\.opentopomap\.org$/;
const FLIZU_MAX = 2500;
const API_MAINIGIE = /^\/api\/(bridinajumi|udens|celi|satiksme|zibens|prognozes|augsne|statuss|meklejumi)/;
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
    if (r.ok) c.put(req, await arLaiku(r)).catch(() => {});
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
    const r = await tikls(req, 6000);
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

let apgriez = false;
async function apgriezt(c, max) {
  if (apgriez) return;
  apgriez = true;
  try {
    const keys = await c.keys();  // ievietošanas secībā: vecākās pirmās
    if (keys.length > max) await Promise.all(keys.slice(0, keys.length - max + Math.round(max / 10)).map(k => c.delete(k)));
  } finally { apgriez = false; }
}

self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.origin === location.origin) {
    if (url.pathname.startsWith('/api/')) return e.respondWith(api(req));
    return e.respondWith(shell(req));
  }
  if (FLIZU_HOSTI.test(url.hostname)) return e.respondWith(kesaVispirms(req, FLIZES, FLIZU_MAX));
  if (url.hostname === 'unpkg.com') return e.respondWith(kesaVispirms(req, CDN, 0));
});
