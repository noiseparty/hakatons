// Bezsaiste (plusma.js reģistrē): vispirms tīkls, kešs tikai tad, ja tīkla nav. Tā izmaiņas main nonāk pie lietotāja
// uzreiz, bet bez interneta lapa (un localStorage saglabātā kopsavilkuma karte) joprojām atveras. /api/* netiek kešots.
const KESA = 'mana-adrese-v1';
const SAKUMS = ['./', 'index.html', 'stils.css', 'app.js', 'plusma.js', 'plusma.json', 'meklesana.js', 'klasifikators.js',
  'avoti.js', 'scenariji.json'];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(KESA).then(k => k.addAll(SAKUMS)).catch(() => {}));
  self.skipWaiting();
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(v => Promise.all(v.filter(k => k !== KESA).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);
  if (e.request.method !== 'GET') return;
  const savs = url.origin === location.origin && !url.pathname.startsWith('/api/');
  const leaflet = url.hostname === 'unpkg.com';
  if (!savs && !leaflet) return;
  e.respondWith(fetch(e.request).then(r => {
    if (r.ok || r.type === 'opaque') { const kopija = r.clone(); caches.open(KESA).then(k => k.put(e.request, kopija)); }
    return r;
  }).catch(() => caches.match(e.request, { ignoreSearch: true }).then(r => r || caches.match('index.html'))));
});
