# Result cards, round 4: the headline address flow (2026-10-10)

Branch `noiseparty/kartites-4`. Round 3 (`notes/kartites-3.md`) could not cover "<situation> <street> <number>, <town>"
because the fixtures had no VZD addresses. This round: 8 real addresses × the 20 most common scenarios, at 375 × 740
(mobile emulation, touch) and 1280 × 800 (desktop) = 320 cards, from recorded fixtures, no load on map.repo.lv beyond
14 single GETs.

## How to run

```bash
# once (already done, files committed): 14 live GETs + local computation of the per-point answers
MAP_DB_DSN="host=127.0.0.1 port=1 connect_timeout=1" uv run --no-project --python 3.12 --with "psycopg[binary]" src/testi/fiksturas_adreses.py
# test
uv run --no-project --python 3.12 src/demo/lokali.py --port 8792 --fiksturas src/testi/fiksturas --attalums-km 5
uv run --no-project --python 3.12 --with playwright src/testi/kartites.py --url http://127.0.0.1:8792 --varianti "" --adreses --top20 [--ekrans 1280x800]
```

Query = first keyword of the scenario + the address, e.g. "plūdi Brīvības iela 12, Ogre", no geolocation.
TOP20 = the 7 quick buttons (patvertne, ārsts, aptieka, ugunsgrēks, policija, degviela, bankomāts) + the top searches
from `/api/meklejumi/top` (plūdi, nav elektrības, droni, nav sakaru) + udens_celas, evakuacija, gaisa_trauksme,
vetra_jumts, negaiss, nav_udens, nav_siltuma, sirdslekme, autoavarija.

### Fixtures: what is live, what is computed, what is substituted

| Endpoint | Source | GETs to map.repo.lv |
|---|---|---|
| `/api/adreses?q=…&limit=1` | live, the 8 addresses as meklesana.js sends them (commas → spaces) + "iela 99 Ogre" and "Baznīcas iela 2" (the shorter variants meklesana.js tried for the two non-existent ones) | 10 |
| `/api/objekti` | round-3 pool (around Ogre) + a ±0,12° × ±0,2° box around Jelgava, Daugavpils, Ventspils, Rēzekne (`api_objekti_<town>.json`; the Ogre pool has no bus stops/pharmacies/ATMs that far) | 4 |
| `/api/pludi` | computed locally with `karte_api.pludi(?wms=1)` → LVĢMC WMS, as the VPS does without the PostGIS copy | 0 |
| `/api/udens`, `/api/prognoze`, `/api/bridinajumi`, `/api/noverojumi` | computed locally with the `karte_api.py` functions (LVĢMC on data.gov.lv); warnings without the Meteoalarm fallback | 0 |
| `/api/augsne` | computed locally (Open-Meteo) | 0 |
| `/api/pasvaldiba` | computed locally from `src/karte/dati/pasvaldibas.json`; municipality from the `/api/regioni` bbox (city if inside, else the smallest county), not the PostGIS boundary | 0 |
| `/api/celi`, `/api/marsruts`, `/api/adreses/tuvaka` | not recorded per point: the Ogre fixture within 5 km (`--attalums-km 5`), otherwise 404 (the card copes: no road line) | 0 |

**14 live GETs in total** (sequential). Not-found addresses fall back to the place centre (`regioni` bbox centre, as
meklesana.js `centrs()`): those points (Cēsis, Ogre) were computed too. For the Ogre centre the LVĢMC WMS did not answer
during recording, so its flood row is the honest "LVĢMC plūdu karte šobrīd neatbild" line — this exercises that path.

`lokali.py --fiksturas` now: answers `/api/adreses` from `adreses/<q>.json`; for a q that was not recorded it returns
the recorded addresses that contain every word (like `LIKE '%word%'`) — **an emulation**: the real ranking over all of
Latvia may differ for short variants. Per-point endpoints take `punkti/<path>__<lat>_<lon>.json` within 500 m.

## What the 8 addresses resolve to

| Query | VZD (live) | Flood zone (LVĢMC WMS) | Nearest gauge | Threshold |
|---|---|---|---|---|
| Brīvības iela 12, Ogre | Brīvības iela 12, Ogre | Nē | Ogre, 2,4 km, normāls | yes (CA plan, critical 22,15 m) |
| Mednieku iela 9, Ogre | Mednieku iela 9, Ogre | Nē | Ogre, 2,3 km, normāls | yes |
| Lielā iela 1, Jelgava | Lielā iela 1, Jelgava | Nē | Jelgava, 0,4 km | no ("nav publiski pieejami" line) |
| Rīgas iela 5, Daugavpils | **Rīgas iela 2**, Daugavpils (no nr. 5 in VZD) | Nē | Daugavpils, 1,1 km | no |
| Jūras iela 3, Ventspils | Jūras iela 3, Ventspils | Nē | Vendzava, 24 km | no |
| Baznīcas iela 2, Cēsis | not found (Cēsis has Baznīcas laukums); the shorter variant "Baznīcas iela 2" → **Jūrmala** | Cēsis centre: Nē | Melturi, 10 km | no |
| Nekāda iela 99, Ogre | not found; the variant "iela 99 Ogre" → **Brīvības iela 99**, Ogre | Ogre centre: neatbild | Ogre, 1,9 km, normāls | yes |
| Skolas iela 4a, Rēzekne | Skolas iela 4A, Rēzekne | Nē | Griškāni, 6,6 km | no |

All points had a yellow LVĢMC wind warning at recording time (06:15), shown as "LVĢMC brīdinājums šai vietai".

## Checks per card (new in round 4)

On top of the round-3 checks (scenario, decision first, next step, places, source line per place, advice, "Kas notiks
tālāk", no undefined/null/NaN, links resolvable, no `tel:`/`mailto:`, card and popup on screen, layers, no JS errors,
ready < 4 s):

- **adrese**: the card shows the resolved address ("Brīvības iela 12, Ogre"); when the address is not in VZD (or VZD
  gave another house number) the card says "… nav atrasta" and shows the place name;
- **plūdi** (pludi, udens_celas): the flood row and the decision line say Jā / Nē / "neatbild" (never stuck on "Pārbauda…");
- **upe**: the gauge row has a level in cm; where the gauge has a threshold (Ogre) the status line with the critical
  level is shown, otherwise the "Bīstamības līmeņi … nav publiski pieejami" text;
- **soļi**: the step strip is visible, on screen, and on step 2 "Atbilde";
- **tel**: no `tel:`/`sms:` link anywhere in the page.

## Results

| Run | Cards | Without errors | Failures |
|---|---|---|---|
| before (main 02f8802), 375 × 740 | 160 | 90 | `adrese` 80 (all cards of Daugavpils, Cēsis, Nekāda: silent wrong address), `slāņi` 16, `upe` 2 (Jūrmala point, no fixture) |
| after, 375 × 740 (+ 5 edge cases: 0 errors) | 160 | **144** | `slāņi` 16 |
| after, 1280 × 800 | 160 | **144** | `slāņi` 16 |
| round-3 regression (129 × 3 variants, Ogre), after | 387 | 372 | `slāņi` 15 (same as round 3) |

Classifier tests (`src/meklesana/testi.py`): green.

### Fixed (production/meklesana.js `atrastAdresi`, valoda.js)

1. **Wrong town.** "Baznīcas iela 2, Cēsis" is not in VZD; the next variant without the town, "Baznīcas iela 2",
   returned **Jūrmala**, and the whole card (decision, places, warnings) was for Jūrmala, with only "· Baznīcas iela 2,
   Jūrmala" as a hint. Now, if the query names a place (classifier on the words outside the street + number, so
   "Rīgas iela" is not Rīga), the found address must be inside that place's bbox (+0,05°).
2. **Wrong street.** "Nekāda iela 99, Ogre": the variant "iela 99 Ogre" found **Brīvības iela 99**. Now every variant
   must contain the street name (the word before the number, and the one before "iela/gatve/prospekts/…").
3. **Silent other house number.** "Rīgas iela 5, Daugavpils" → VZD's best match is Rīgas iela 2 (no nr. 5). The card
   keeps it but says: "Adrese „Rīgas iela 5” VZD adrešu reģistrā nav atrasta; rādām atrasto: Rīgas iela 2, Daugavpils."
4. **Not found → said clearly.** When "… iela N" is not found: "Adrese „Nekāda iela 99” VZD adrešu reģistrā nav
   atrasta; rādām pēc vietas: Ogre." and the card continues for the place (centre, "Izmantot manu atrašanās vietu"),
   with the scenario taken from the remaining words (so "Mednieku iela" / "Skolas iela" do not trigger hunting / school
   threats). Without a place: "… Pārbaudiet adresi vai izmantojiet savu atrašanās vietu." RU/EN translations added.
   Queries with a number that are not addresses ("zvanīju 112", "3 cilvēki …") stay silent as before (note only after
   "iela/gatve/…").

### Remaining

- `slāņi` 16 = nav_elektribas (wifi_punkts) and nav_sakaru × 8 addresses: the VPS has not loaded the #118 OSM layers
  (TODO line from round 3). Cards are not dead ends.
- Classifier (not address-related, seen while checking): "3 cilvēki iesprostoti liftā" → "Smaga autoavārija"
  (`iesprost` keyword). TODO line added.
- Desktop 1280: the search field is narrow ("nav elekt…") next to "Notīrīt" and the microphone; usable, cosmetic.

## Not tested

- The real `/api/adreses` ranking for variants that were not recorded (emulated from 10 recorded rows), and the
  PostGIS flood copy (the WMS answer was used).
- Road closures and routes for points outside Ogre (404 → no line), real phones, iOS Safari, Firefox, RU/EN chrome for
  the address cards (spot-checked RU and EN by hand: note translated, no JS errors).
