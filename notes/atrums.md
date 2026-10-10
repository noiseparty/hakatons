# Ātrums telefonā (2026-10-10)

Measured with Playwright: 375×740, CPU ×4, "Slow 4G" (Lighthouse preset: RTT 150 ms, 1.6 Mb/s down, 750 kb/s up), cold browser cache, service worker blocked. API warm (responses cached in the local test proxy, as after the pre-pitch check). Static files gzipped like Caddy. Median of 3 runs. Scripts: `merit.py` / `krit.py` (session-local; method below).

| Metric | Before (#82) | After (this PR) |
|---|---:|---:|
| Search usable (classifier + scenarios loaded) | **3.90 s** | **1.74 s** |
| `load` event | 4.00 s | 3.90 s |
| Card for "plūdi Ogre" after Enter (advice + nearest places) | 1.33 s | 1.38 s |
| → page open to card | ~5.2 s | **~3.1 s** |
| Network quiet (map tiles, all layer points) | 22.9 s | 21.3 s |
| Transfer (until quiet) | 1 173 KB | 1 132 KB |
| Requests | 95 | 91 |
| Cumulative layout shift | 0.20 | 0.16 |

Where the bytes go (after): map tiles ~560 KB, API ~407 KB (of which the all-layers `/api/objekti?…limit=20000` is ~420 KB uncompressed-equivalent of points), our JS + Leaflet ~128 KB, CSS 14 KB, `scenariji.json` 37 KB.

## What was slow

The waterfall showed `scenariji.json` (37 KB) only requested after **all** scripts had run (~1.8 s) and then competing for bandwidth with the 420 KB all-layers points request, so the search waited until ~3.9 s. The three startup API calls (`kategorijas`, `regioni`, `avoti`) also only started after every script executed.

## What changed

- `<link rel="preload" as="fetch" crossorigin="anonymous">` for `scenariji.json`, `/api/kategorijas`, `/api/regioni`, `/api/avoti`: they start at ~0.2 s, in parallel with the scripts, and the later `fetch()` calls reuse them (verified: one request each, no "preload not used" warning).
- The all-layers points request gets `fetch(…, { priority: 'low' })` (only for the map's full load, not for nearest-place queries), so the card's small queries go first on HTTP/2.
- Leaflet 1.9.4 and markercluster 1.5.3 vendored in `production/vendor/leaflet/` (byte-identical to unpkg: same SRI hashes; BSD-2 / MIT licences included): no third-party DNS/TLS on the critical path, and the offline service worker caches them with the shell.
- `preconnect` to `tile.openstreetmap.org` (tiles start right after the map is created).
- `vendor/qrcode.js` (12 KB) is loaded only when the user presses "Drukāt".
- The warnings banner is visible from the start ("Ielādē LVĢMC brīdinājumus…"), so the map doesn't jump down when it arrives (CLS 0.20 → 0.16; the rest is the banner growing from one to two lines on a phone and the Prognoze button).
- Caddy: `Cache-Control: public, max-age=300` for JS/CSS/JSON/images, `no-cache` for HTML (VPS step; files have no version in their names, so the cache is short).

## Not done (and why)

- `defer` on the scripts: they are already at the end of `<body>` and discovered by the preload scanner, so `defer` would only move execution after parsing a 4 KB HTML — no measurable gain, while the inline "Leaflet failed" check and the order between files would have to change.
- Lazy-loading `demo.js`, `zonas.js`, `saraksts.js`, `noverojumi.js`: together ~22 KB gz (~0.1 s on Slow 4G); each creates its own buttons or is used synchronously by the search, so lazy loading means stubs in other people's files the night before the pitch. Worth it later with a build step.
- The 420 KB all-layers points request is the biggest item; slimming it (fewer properties, or viewport-bounded loading) is an API change for later.
