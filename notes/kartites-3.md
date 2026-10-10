# Result cards, round 3: "works on a phone with no dead ends" (2026-10-10, after ~30 merges)

Branch `noiseparty/kartites-3`. Every scenario in `production/scenariji.json` (129) × 3 variants at 375 × 740
(mobile emulation, touch), plus the 5 edge cases from round 1. **No load on map.repo.lv:** the API is served
from 19 responses recorded once (19 sequential GETs, `src/testi/fiksturas_ierakstit.py`), and everything else is local.

## How to run

```bash
uv run --no-project --python 3.12 src/demo/lokali.py --port 8763 --fiksturas src/testi/fiksturas
uv run --no-project --python 3.12 --with playwright src/testi/kartites.py --url http://127.0.0.1:8763 [--vietas] [--csv k.csv]
```

- `lokali.py --fiksturas DIR` answers `/api/*` from the recorded files (key = endpoint path). `/api/objekti` is
  computed from one recorded `?bbox=<all of Latvia>&lat&lon&limit=5000` (16 layers, nearest per layer around Ogre):
  nearest by category and distance from the requested point, or the points in a bbox. `/api/adreses` returns `[]`.
  Missing fixture → 404 (the page must cope). `--ierakstit N` lets it fetch a missing one (≤ N, sequential).
- The test aborts every non-local request (tiles, fonts), so it does not load OSM either.
- Recorded at 05:32 for Ogre: yellow LVĢMC wind warning, flood zone "yes" (spring floods 10 %), Ogre gauge normal.
  Re-record after the VPS data changes: delete `src/testi/fiksturas/` and run the recorder again (2.1 MB, committed).
- `lokali.py` and the test's own server now use a listen backlog of 128: with the default 5, three tabs loading
  ~35 scripts at once on Windows dropped random scripts (`net::ERR_NO_BUFFER_SPACE`, "krizesMeklesana is not defined").

## Variants and checks

| Variant | Setup |
|---|---|
| with location | geolocation granted (Ogre centre), query = first keyword of the scenario |
| without location | no geolocation, same query: places from the map centre + "Izmantot manu atrašanās vietu" (#139) |
| RU | as "with location", `localStorage.valoda = 'ru'` (LV/RU/EN switch, #137) |
| `--vietas` (optional) | the 4 place-name points from round 1 (Rīgā, Ogrē, Rēzeknē, Alūksnes novadā) |

Per card: the right scenario; decision block first (`#rez-galvenais` / LVĢMC line / 112); at least one next step
(route link, place row, 112 text or location button); places or a clear "not known" text; **a source line for every
place row**; advice and "Kas notiks tālāk"; no "undefined"/"null"/"NaN"/"[object"; no empty heading; **every link in
the card and in the first place's popup is internal and resolvable** (file in `production/`, `#id` present, `/api/`
route exists in `karte_api.py`) **or http(s)** — no `tel:`, `mailto:`, `javascript:`; **card and popup within the
375 px screen**, page does not scroll sideways; every scenario layer is in `/api/kategorijas`; no JS errors; ready < 4 s.

## Results

| Run | Cards | Without errors | Failures found | Fixed |
|---|---|---|---|---|
| before (main 09c685b + new checks) | 387 | 124 | `avots` 258 (every card with places), `slāņi` 15 | — |
| after fix, merged with main cda6c18 (incl. #139 card reorder, up to #153) | 387 | **372** | `slāņi` 15 | `avots` 258 → 0 |
| `--vietas` (7 variants, before #139) | 903 | 868 | `slāņi` 35 | — |
| edge cases | 5 | 5 | — | — |

Classifier tests (`src/meklesana/testi.py`): green before and after.

### Fixed

- **No source/licence on place rows** (258 of 387 cards): only CA-plan places had "Avots: … CA plāns, lpp. N";
  shelters (vugd-112, ⚠ no licence), 24/7 hospitals (vm-24h), pharmacies (zva-fdu), police / fire depots
  (iemic-*), OSM ATMs / fuel / resilience points, LVĢMC gauges, bus stops had none in the card (only in the map popup).
  Fix: `production/meklesana.js` `vienums()` appends `Avoti.rinda(p.avots)` ("Avots: <dataset> (<publisher>) ·
  <licence>", with the ⚠ note for 112.lv) unless the place is a CA-plan place that already has its source comment.
  One generic line, no change to `scenariji.json`.

### Remaining (not a front-end bug)

- **`slāņi` 15 = 5 scenarios × 3 variants:** `ev_uzlade` (elektromobilis), `wifi_punkts` (nav_elektribas, nav_sakaru),
  `veterinars` (dzivnieks_ievainots, majdzivnieks_pazudis) are in `shema.sql` / `osm_poi.py` (#118) but not in the live
  `/api/kategorijas` at recording time — the VPS has not loaded them. The cards are not dead ends (the front end skips
  missing layers; safe places, advice, 112 and next steps are there), but these scenarios show none of their own
  places until the VPS step is done. `scenariji.json` left as is on purpose. TODO line added.
- "Without location" has no LVĢMC verdict for a place (by design since #139: the map centre is not the user's place);
  its decision block is "nearest X from the map centre" + "Izmantot manu atrašanās vietu".
- RU chrome: source lines from `Avoti.rinda` and CA comments stay Latvian ("Avots: …"), like the other data texts.

## Not tested

- Real phones (only Chromium mobile emulation), iOS Safari, Firefox.
- Live API behaviour (slow `/api/pludi`, 202 retries, LVĢMC outages beyond the two stubbed 503 edge cases).
- Address queries with a house number (fixtures return no addresses) and other places than Ogre / map centre with
  real nearest data (fixture places are the nearest ~125 per layer around Ogre).
- EN chrome (RU only, as asked).
