# Phone tests: device matrix of the live site (2026-10-10)

**Run:** `src/demo/ierices.py` (Playwright device profiles), on https://map.repo.lv and on the fixed branch via `src/demo/lokali.py`, which serves `production/` and proxies `/api` to the live site.

**Devices:** iPhone SE (320×568, WebKit), iPhone 14 (390×664, WebKit), Pixel 7 (412×839, Chromium), Galaxy S9+ (320×658, Chromium), iPad Mini (768×1024, WebKit). Each device ran with location **allowed** (Ogre) and **denied**.

**Path** (`notes/pitch.md` §5):
1. Home page.
2. "plūdi Ogre", "nav elektrības Rīgā", "cilvēks nav pie samaņas".
3. Bottom sheet on phones: peek / half / full, the main action button, demo panel vs sheet.
4. All 7 `?demo=` links, then "Beigt demo".
5. Prognoze panel, Datu avoti, statuss.html.

**Logged per step:** JS errors, failed requests, horizontal scroll, tap targets under 44 px, text under 12 px, the 112 line, the SIMULĀCIJA badges. Screenshots and JSON reports are outside the repo, in `..\telefonu-tests\`. The team's own check, `src/testi/parbaude.py`, was also run against the fixed branch.

## Found on the live site and fixed in this PR

| # | What | Where | Fix |
|---|---|---|---|
| 1 | **JS error** "krizesMeklesana is not defined" on load when location is already allowed (Pixel 7, Galaxy S9+). The geolocation answer arrived before `meklesana.js` had loaded. | `app.js` | The automatic location check now starts after `DOMContentLoaded`. |
| 2 | **Dead end on iPhone SE.** The "Demo" tab covered the ✕ of the open Prognoze panel, so it couldn't be closed and the Datu avoti step timed out. | `demo.css` | While the forecast panel is open on a phone, the Demo tab is hidden. The tab also moved below the 44 px map buttons. |
| 3 | **Tap targets under 44 px**, 150–210 per run on the live site. Examples: search field 41, "Meklēt" 41, "Filtri" 36, zoom/location buttons 38, Karte/Reljefs 28, Prognoze 35, Šodien/Rīt/Parīt 31, ✕ buttons 35–36, Demo tab 29 wide, route chips ~22, layer rows and groups 39, warning summary 38–40, select fields 40–43. | `stils.css`, `demo.css` | One phone-only block (`max-width: 800px`) sets all of these to ≥ 44 px. Route chips are 40 px, a deliberate compromise in long lists. |
| 4 | **Text under 12 px:** SIMULĀCIJA badge 11.2, cluster counts 11.5, route chips 11.5, zone legend 10.4. | `stils.css`, `demo.css` | Raised to ≥ 12 px. |
| 5 | Zone legend ("plūdu riska zona") overlapped the Karte/Reljefs switch on 320 px phones. | `stils.css` | At ≤ 400 px the legend sits above the switch. |
| 6 | Three-line simulated warning banner on 320 px screens left ~170 px of map. | `demo.css` | On phones the demo banner is one line with an ellipsis; tapping it expands. The demo sheet is capped at the screen height minus 200 px. |

## Also in this PR (user requests via the orchestrator)

- **All layers off on load.**
  - No layer checkbox is checked and no `/api/objekti` request is made. The map shows only the basemap, warnings and search; the status pill reads "Slāņi izslēgti".
  - The search result turns on its scenario's layers (e.g. "plūdi Ogre" → assembly points + river gauges), and demo scenarios turn on theirs.
  - "Beigt demo" returns to all off. All four checks were verified with Playwright at 375×740 and 1280×800.
- **Changelog "#" button:**
  - A 44 px button before "Krīzes karte" opens a "Kas jauns" `<dialog>`, a bottom sheet on phones.
  - Contents: `production/izmainas.json`, 19 entries by date in the Jūs form.
  - Escape, ✕ or a click outside closes it.
  - Header markup change: only the button plus a `.galva-kreisi` wrapper around the existing `<h1>`; no other header styles changed.

## Not fixed (not front end, or a deliberate choice)

- **`/api/meklejumi/top` answers 503** on the live API ("Biežāk meklētais"). This is the only red item in `src/testi/parbaude.py`. API/VPS side.
- **Flood WMS (geo-dpps)**: some tiles give CORS or 404 errors, and the zone check can take 15–30 s. The upstream LVĢMC service is slow. Warm the demo addresses right before the pitch.
- **Map markers are 30 px** (clusters, demo icons). Each one also appears as a full-width row in the result card or demo card, so we left the map icons small to keep the map readable.
- **Bottom sheet (#60)** works on every phone: peek → half → full → peek, the main action button is 44 px and on screen, and the demo panel and result sheet are never open together. Note: on "plūdi …" queries the sheet's first line shows the LVĢMC warning until the flood-zone check returns, which can take up to 30 s.
- **112 line** ("zvaniet 112") is shown on every device for "cilvēks nav pie samaņas". No `tel:` links anywhere.

## Results after the fixes

See the PR description (filled in from the last matrix run).

## Backup demo video and slide screenshots (outside the repo)

`src/demo/video.py` records the 60-second pitch path at 390×844 (Chromium, location = Ogre) and saves to `C:\Users\ZX202\kodi\demo-video\`:

- `map-repo-lv-demo-390x844.webm`: the video
- `01-sakums.png` … `11-statuss.png`: search → flood card (decision, safe places, advice / what happens next) → 112 line → `?demo=vetra-2026` (card + map) → `?demo=pludi-ogre` (card + map) → statuss.html

These were recorded against the live site **before** this PR (filters were still on at load). Re-run `uv run --no-project --with playwright src/demo/video.py` after the merge for a final take.
