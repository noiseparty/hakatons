# Demo scenarios: which data we have, what would make them real, what is missing

The demo panel (`production/demo.js`, `demo.css`, data in `production/demo/scenariji.json`) is the "Demo" tab on the right edge of https://map.repo.lv (a bottom sheet on phones). Each scenario puts the map into a simulated crisis. **Simulated:** the warning banner, zones, events and markers, all labelled SIMULĀCIJA. **Real:** the nearest places, route links and sources, all live from `/api/objekti`. "Beigt demo" restores the layers, the flood toggle, the map view and the real LVĢMC banner.

Direct links for the pitch: `https://map.repo.lv/?demo=<code>`, e.g. `?demo=drons`, `?demo=vetra-2026`, `?demo=bez-sakariem&regions=100003470` (Ogre).

Written 2026-10-10. Licences: as stated by the publisher. "Not open" means no licence or API is published.

---

## 1. Yellow warning: strong wind (`vejs`), Kurzeme coast

| | |
|---|---|
| **Used now** | Warning polygon = real municipal boundaries (VZD, CC BY 4.0, via `/api/regioni`). Banner in the same form as the real LVĢMC banner (`bridinajumi.js`). Advice is ours. |
| **Would make it real** | **LVĢMC hydro-meteorological warnings**, https://data.gov.lv/dati/lv/dataset/hidrometeorologiskie-bridinajumi, CC0. Already live in the app (`/api/bridinajumi`, polygon check). The demo only shows what a yellow warning looks like when there isn't one tonight. **LVĢMC observations** (gusts per station, last hour + 365-day archive), https://data.gov.lv/dati/lv/dataset/hidrometeorologiskie-noverojumi, CC0. |
| **Missing** | Observed gusts on the map (the CSV is there; no loader yet). Warning texts with advice per level come from LVĢMC only as free text. |

## 2. Red warning: storm (`vetra`), Rīga, Jūrmala, Mārupe

| | |
|---|---|
| **Used now** | Same as 1, plus real layers switched on: shelters (VUGD/112.lv, ⚠ no licence) and 24/7 hospitals (VM disaster medicine plan). The card shows the nearest shelter, the nearest accommodation (municipal CA plan, page link) and the nearest 24/7 hospital, with route links and the source of each. |
| **Would make it real** | The real LVĢMC red warning (above). Shelter status (open / full) would need VUGD or the municipalities to publish it. |
| **Missing** | Live shelter status and capacity (`TODO.md`). Shelters list has no open licence (ask VUGD to publish on data.gov.lv). |

## 3. Drone sighting in a city (`drons`), Rēzekne

| | |
|---|---|
| **Used now** | A 1 km closed zone (simulated circle). The nearest real shelter **outside** the zone that is also **farther from the zone centre than you**, so the route leads away from it. Dashed direction line plus Google/Waze/OSM route links. Real context in the card: drones fell at an oil depot in Rēzekne on 7 May 2026, and 112.lv was briefly down under load during the May cell-broadcast alerts ([LSM, 23.05.2026](https://www.lsm.lv/raksts/zinas/latvija/23.05.2026-sunapraides-bridinajumu-prblemu-del-secina-112lv-lietotnes-uzlabosanai-vajag-vel-600-000-eiro.a648459/)). |
| **Would make it real** | A machine-readable alert feed: the content of the cell broadcast (šūnu apraide) and 112.lv as **CAP (Common Alerting Protocol)** with a polygon. Nothing like this is published today; the cell broadcast reaches phones only. |
| **Missing** | Any public feed of air-threat zones or closed areas. Routing that avoids a polygon (OSRM/GraphHopper can, if self-hosted with OSM data, ODbL). |

## 4. Night, cut hand (`nakts`), Saulkrasti at 03:00

| | |
|---|---|
| **Used now** | Nearest **24/7 emergency department** (`neatliekama_24h`, VM disaster medicine plan, annex 12) with a route line. The 4 nearest pharmacies (ZVA, CC0) are greyed as "probably closed at night". First-aid steps. A red "zvaniet 112" text if the bleeding doesn't stop. The family-doctor advice line 66016001 (24/7) as plain text, without a link. |
| **Would make it real** | **Pharmacy opening hours.** The ZVA register (https://data.gov.lv, CC0) has no hours. OpenStreetMap `opening_hours` (ODbL) covers part of them; we already show it in popups when present. A list of **night / 24 h pharmacies** from ZVA or the chains. |
| **Missing** | Opening hours from an authoritative source. Emergency department load or waiting times (NMPD/hospitals, not public). Today the "closed" mark is an assumption and says so. |

## 5. Flooding in Ogre: seek higher ground (`pludi-ogre`)

| | |
|---|---|
| **Used now** | LVĢMC flood-risk zones (WMS, CC0), real assembly points and accommodation (CA plan), the nearest river gauge (LVĢMC, CC0), and **higher-ground polygons computed from the LĢIA digital elevation model**. |
| **Elevation data** | **LĢIA digitālais reljefa modelis 20 m**, https://www.lgia.gov.lv/lv/digit%C4%81lais-reljefa-modelis, **CC BY 4.0** (LĢIA open-data page). Download: `https://s3.storage.pub.lvdc.gov.lv/lgia-opendata/citi/dtm/DTM_Latvija_20m.7z` (380 MB 7z → 4.7 GB text "X Y Z", LKS-92 TM, LAS-2000.5 heights). Pipeline: `src/demo/augstumi.py` (uv: pandas, rasterio, shapely, pyproj). It cuts the bbox, grids at 20 m, thresholds, polygonizes, simplifies to 15 m and writes `production/demo/augstumi-ogre.geojson` (20 KB, 4 polygons, 37.5 km²). The full-country cut takes ~90 s; `--saglabat` caches the cut as `.npy`. Alternative: Copernicus DEM GLO-30 (free, but its licence is "all rights reserved, free use with attribution", not CC). We did not use it. |
| **Threshold: 23 m, not 15 m** | In Ogre the Daugava is the Rīga HES reservoir with its surface at ~17–18 m, and the lowest DEM cell in the area is 12.9 m. **≥15 m covers 99.6 % of the area**, so it can't show higher ground. We use **≥23 m**: ~5 m above the river and above the 22.15 m Ogre gauge threshold noted in `TODO.md`. That leaves the river valleys out (85 % of the area is still ≥22 m; the town sits on a terrace). Re-run with another `--slieksnis` if a hydrologist suggests a better value. |
| **Missing** | Flood **depth** and water level for a given gauge reading (LVĢMC has the models; not published as open data). River-gauge danger thresholds (PRIS) need LVĢMC permission. The DTM ignores embankments and buildings; the popup says the polygons are a guide, not an evacuation order. |

## 6. Storm of 22–23 Aug 2026, replay (`vetra-2026`), Bauska

| | |
|---|---|
| **Real figures in the card** (with links) | Gusts **over 30 m/s** overnight on 23 Aug ([Sadales tīkls via LV portāls](https://lvportals.lv/dienaskartiba/393543-sadales-tikls-vetras-seku-likvidacija-iesaistitas-206-brigades-iedzivotaji-aicinati-zinot-par-bojajumiem-elektrolinijas-2026)). **~245 000** customers without power on 23 Aug at 13:00 and ~260 000 affected overall; ~11 000 still without power on the morning of 26 Aug ([LSM 26.08.2026](https://eng.lsm.lv/article/economy/economy/26.08.2026-most-households-have-electricity-restored-after-storm-in-latvia.a660364/)). Largest outages in the Bauska, Krāslava, Madona, Rēzekne and Jelgava municipalities ([ST 23.08 18:00](https://lvportals.lv/dienaskartiba/393547-elektroapgade-lidz-plkst-18-00-atjaunota-vairak-neka-100-000-klientu-2026)). **3 080** VUGD calls, 1 death, 3 injured ([VUGD 24.08](https://lvportals.lv/dienaskartiba/393556-brivdienas-sanemti-vairak-neka-3000-pieteikumi-uz-veja-raditiem-postijumiem-2026)). Only **~70 of ~500** fuel stations have generators ([Saeima committee](https://lvportals.lv/dienaskartiba/394194-tautsaimniecibas-komisija-krizes-bridi-neviens-novads-nedrikst-palikt-bez-pieejas-degvielai-2026)). **4 800** insurance claims and EUR 8.05 M reserved ([LAA 28.08](https://lvportals.lv/dienaskartiba/393792-apdrosinataji-pec-nedelas-nogales-vetras-sanemusi-jau-4800-atlidzibas-pieteikumu-2026)). |
| **Simulated** | Outage areas (circles around Bauska, a rural area, Iecava). Fallen trees and closed road sections on A7/P103 (real road geometry from OSM, simulated closure). The jam marker. Real ATMs (OSM, ODbL) and fuel stations inside the outage areas are greyed ✕; the card shows the **nearest working one outside the outage**, plus the nearest accommodation (warm place) and shelter. Advice: LR1 on the radio (Rīga 90.7 FM), Sadales tīkls 8404 for fallen lines, 112 only for life threats. |
| **Would make it real** | **Sadales tīkls outage map** JSON (`karte.sadalestikls.lv/lv/atslegumi-elektrotikla/unplanned`): public but **no licence**; ask ST (already in `TODO.md`). **LVC road events (DATEX II)** via the National Access Point (transportdata.gov.lv, CC0): **live since #51/#61** (`/api/celi` on the real keys); the replay could use real events instead of the simulated A7/P103 closure. **LVĢMC observations** (above) for the actual gust maxima per station: the dataset exists (CC0, 365-day archive), not loaded yet. |
| **Missing** | Live ATM / card-terminal status (banks don't publish). Which fuel stations have generators (the ministry list isn't public). Restoration ETA per street. The pitch's earlier "~277 000 households" was never verified; since 2026-10-10 the pitch uses the verified **~260 000 customers affected** (~245 000 at one moment on 23 Aug). Observed LVĢMC station gust maxima for 22–23 Aug were not found; sources disagree on the warning level (red in the west vs orange). |

## 7. No power and no mobile network across a city or municipality (`bez-sakariem`)

| | |
|---|---|
| **Used now** | Pick the area (Rīga, Ogre, Bauska, Rēzekne, Liepāja, Daugavpils, Valmiera; real VZD boundary). Every layer that depends on live status (pharmacies, ATMs, fuel stations, river gauges) is greyed with "status nezināms". The card lists where to go **without a phone**: the nearest VUGD fire depots and police (IeM IC, CC0), the 24/7 hospital and the municipal assembly points (CA plans). Offline advice plus a **print / save as PDF** button (print CSS prints only the card). |
| **Would make it real** | Operator outage areas (LMT, Tele2, Bite): not public. National roaming in a crisis is only a proposal (Saeima committee, above). **LR1 frequency list:** confirmed against the official Latvijas Radio page (https://latvijasradio.lsm.lv/lv/par-mums/frekvences/, read 10.10.2026): Rīga 90,7 is correct; all 16 transmitters are on https://map.repo.lv/info.html (#62). Not structured data, so it's copied by hand. |
| **Missing** | A real offline mode. The site has no service worker, so without the internet it won't open. The honest answer in the card is "print it now". A PWA with cached tiles and data for the user's own area is the obvious next step. |

## Missing data across scenarios

| Need | Verdict (2026-10-10) | Action |
|---|---|---|
| **Riga public transport, live** (which trams/buses run during a storm or evacuation) | No open real-time feed. Rīgas satiksme publishes only a **static GTFS** timetable (CC0). The live endpoint behind saraksti.lv is undocumented and has no licence, so it can't be used. A **historical GTFS-RT dump** exists on Zenodo (CC BY 4.0), usable only for research or a replay, not live. | Email **info@rigassatiksme.lv** asking for a GTFS-RT feed under an open licence. |
| **Border waiting times** | NAP card exists (`ROBEZAS_LAIKS`, key on the VPS), but the feed doesn't answer yet. | B (`noiseparty/satiksme-2`) keeps checking; the status page shows it. |
| **Traffic: speed limits** for a real free-flow speed | Not subscribed on NAP; `/api/satiksme` estimates free flow from the highest speed seen. | Subscribe the speed-limit dataset if it exists on NAP. |

## Real events (group "Reāli notikumi", added 2026-10-10 night)

The panel now has two groups. **Reāli notikumi**: what happened in Latvia, with 1–3 figures and sources in the card plus "Ko Jūs redzētu šajā lietotnē". **Simulācijas**: the original 7.

On the map, zones, smoke cones and markers are still simulated and labelled SIMULĀCIJA; the event coordinates are approximate. Nearest places are live data. The 2026-08 storm replay (`vetra-2026`) moved into the real group.

Each scenario has `vaicajums`, the query the replay mode (`atskanot.js`, #83) runs first. Checked against the classifier on main.

Facts were researched by subagents on 2026-10-10 and checked against the opened sources. Anything only seen in search snippets was left out.

| Code | Event | Figures in the card (source) | Map state | Open data that would make it real | Missing |
|---|---|---|---|---|---|
| `brell-2025` | Baltic grid leaves BRELL, 8–9 Feb 2025 | ~1 day isolated operation; sync with Continental Europe 9 Feb; no change for consumers (ERR, AST) | Pick a city; live-status layers grey "status nezināms"; where to go without a phone; printable | Sadales tīkls outage JSON (public, **no licence**); AST system state (no open feed) | No outage happened. The card says so and shows the "what if" |
| `drons-2024` | Shahed-type drone crash, Gaigalava, 7 Sep 2024 | No casualties or third-party damage (MoD); carried explosives, destroyed on site (LSM) | 1.5 km closed zone (approximate site), nearest shelter outside and away from it, VUGD depot, 24/7 hospital | A machine-readable cell-broadcast / CAP feed with polygons | Exact site not public. MoD/LSM don't mention a public alert; we say exactly that, not "there was no alert" |
| `drons-2026` | Drones over Latgale, Rēzekne oil depot, 7 May 2026 | 2 crashed, a 3rd crossed; 4 empty tanks damaged (MoD 8.05); 112.lv overload (LSM 23.05) | LV-ALERT text as the banner, 800 m zone around the depot (approximate), shelter outside | CAP / LV-ALERT feed | Cell broadcast content isn't published as data |
| `jekabpils-2023` | Daugava ice-jam flood, Jēkabpils, Jan 2023 (again Feb 2024) | Above the orange mark; Sakas sala partly flooded, locals only; power cut to flooded houses; dam seeping, sandbagged (LSM 11.01.2023, 27.02.2024) | Flood zones on, Jēkabpils gauge, assembly points and accommodation (CA plan) | LVĢMC gauge history (CC0, loaded hourly); PRIS danger levels (need permission) | Peak level in metres: only an unverified 8.91 m (thesis snippet), not shown |
| `stikli-2018` | Stiklu purvs peat fire, 17 Jul 2018 | 70 of ~120 Stikli residents evacuated incl. 21 children; NAF helicopter; >100 ha (LSM) | Smoke cone toward Stikli (direction from reports, not wind data) + approximate fire area; accommodation outside the smoke | LVĢMC observations (wind) for a real smoke direction; VMD fire data | **Fire-water intake points** (`udens_nemsana`) aren't in the live DB yet (planned layer), so not switched on |
| `ulmana-2026` | Warehouse fire, K. Ulmaņa gatve 2, Rīga, 30 Jun 2026 | 3 500 m² in a 40 000 m² complex; ~200 + ~180 evacuated (jauns.lv); close windows, ventilation off (LV portāls) | Smoke cone NNE (assumed SSW wind), accommodation and pharmacy outside the smoke, 24/7 hospital | LVĢMC observations (wind) | LSM English gives "about 450 evacuated" (another figure); we use the jauns.lv split |
| `bauskas-2026` | Gas explosion, Bauskas iela 15, Rīga, 2 Jan 2026 | 46 evacuated (35 + 11), 2 dead, 2 injured; Gaso call 14:58; heated bus, hotel for 15 days for 16 people (LSM) | Address-level decision "Ēka slēgta", accommodation, 24/7 hospital | Building-closure status from the municipality (none) | A third death and the >€60k aid were seen only in snippets; left out |
| `meldru-2026` | Scrap-metal fire, Meldru iela 3, port of Rīga, 17–18 Jul 2026 | Call 19:10, out 07:08 (~12 h); 300 m², ~30 000 t; no injuries; windows closed in Vecmīlgrāvis/Vecāķi (LSM) | Smoke cone NE, pharmacy outside the smoke, 24/7 hospital | Wind observations; fire-water points | Same as above |
| `ddos-2025` | DDoS on gov.lv and eParaksts, 2 Oct 2025 | ~1 h, some resources 1 h 20 min (LSM/LVRTC) | Map unchanged; links to statuss.html and info.html | — | — (`vaicajums` "nestrādā e-pakalpojumi" → `e_pakalpojumi`) |

### Three weather events (added 2026-10-10 morning, `noiseparty/demo-3`)

These are in the "Reāli notikumi" group after `jekabpils-2023`, so the panel and the replay show the weather events together (floods, storm, heat), then fires, gas, DDoS. Facts below were checked against the opened pages; only facts are used, no copied text.

| Code | Event | Figures in the card (source) | Map state | `vaicajums` → scenario |
|---|---|---|---|---|
| `latgale-2017` | Rain and floods in Latgale, end of Aug 2017 | Rēzekne 123.1 mm in 24 h, a station record ([LVĢMC year review, LV portāls 29.12.2017](https://lvportals.lv/dienaskartiba/292408-latvijas-iedzivotaju-velmem-visatbilstosakie-laika-apstakli-sogad-bija-marta-2017)); 159 mm in 32 h = 229 % of the August norm ([Crisis Management Council, LV portāls 29.08.2017](https://lvportals.lv/dienaskartiba/289353-kvp-atbalsta-ierosinajumu-izsludinat-arkartejo-situaciju-27-novados-2017)); emergency by [Cabinet order No. 455 of 29.08.2017](https://likumi.lv/ta/id/293167), 29.08–30.11.2017, 27 then 29 municipalities; rivers up >2 m, >100 000 ha unharvested, <5 % insured, ~€1 M for roads ([LSM 29.08.2017](https://www.lsm.lv/raksts/zinas/latvija/pludu-skartajas-teritorijas-izsludina-arkartas-situaciju.a248273/)); Saeima approved unanimously ([LSM 07.09.2017](https://www.lsm.lv/raksts/zinas/ekonomika/saeima-piekrit-pludu-del-arkartas-situaciju-izsludinat-29-novados.a249271/)) | Flood-risk zones on, Rēzekne as the place, nearest river gauge, assembly point + accommodation (CA plan); simulated: warning over 8 Latgale municipalities, approximate rain area (25 km circle, not in the view), 2 markers (flooded field, washed-out road) | "plūdi Rēzekne" → `pludi` |
| `vetra-2005` | Storm "Ervīns" (Gudrun), 8–9 Jan 2005 | Highest gusts 40 m/s in Ventspils; sea ≥1 m above mean for 23–24 h and >2 m for 7–8 h, highest in 100–120 years of records; ~40 % of the coast eroded ([LSM 09.01.2025](https://www.lsm.lv/raksts/dzive--stils/vide-un-dzivnieki/09.01.2025-20-gadi-kops-si-gadsimta-postosakas-vetras-latvija-ka-plosijas-ervins.a582388/)); ~60 % of consumers without power on 9 Jan, ~35 % on 10 Jan afternoon, energy crisis declared, Liepāja losses 600–700 k lats ([Latvijas Vēstnesis 11.01.2005](https://www.vestnesis.lv/ta/id/99233)); all of Ventspils and part of Liepāja 2 days without heating and hot water, Ventspils/Liepāja/Rīga ports closed, >7 000 VUGD calls ([The Baltic Times 12.01.2005](https://www.baltictimes.com/news/articles/11724/)) | Flood-risk zones on (incl. the coast), accommodation, assembly point, shelter; ATMs and fuel stations inside a simulated 4.5 km "no power" circle greyed with the nearest working one outside; markers: port closed, tree on lines; LR1 Ventspils 99,2 / Liepāja 107,1 FM in the advice | "vētra Ventspils" → `vetra_jumts` (same as `vejs` / `vetra`) |
| `karstums-2021` | Heat wave, 19–23 Jun 2021 | LVĢMC red warning for all of Latvia on 19.06: >32 °C by day, nights not below 20 °C; NVD: drink water, stay in shade ([LSM 20.06.2021](https://eng.lsm.lv/article/weather/weather/extreme-heat-warning-across-latvia.a409828/)); 33.7 °C in Daugavgrīva and Pāvilosta on 21.06, monthly records at several stations, warmest June night (up to 23.7 °C) ([LSM "this day": 21 June](https://www.lsm.lv/raksts/laika-zinas/diena-vesture/21.06.2013-21-junijs.a73668/)); Rīga night of 23.06 not below 24.2 °C, record until Aug 2023 ([LSM 07.08.2023](https://eng.lsm.lv/article/weather/weather/07.08.2023-sunday-night-was-hottest-in-history-of-latvia.a519169/)) | Layers: `noturibas_punkts` (OSM libraries / culture houses as "cooler place by day", labelled not confirmed), `udens_punkts` (drinking water), pharmacies, plus the 24/7 hospital in the card; simulated: warning over Rīga, 2.5 km "hottest part of the city" circle | "karstums Rīga" → `karstums` |

**Corrections to the brief, from the sources:** the 2017 emergency was declared **for agriculture only** (Cabinet order No. 455, coordinated by the Ministry of Agriculture), not a general state emergency. June 2021 peaked at **33.7 °C**, not 34–37 °C (no source found for ≥34 °C in Latvia in June 2021; 34 °C was Lithuania). The 2005 outage was **national** (~60 % of consumers), not only Kurzeme. The ">2 m" surge is the sea level along the coast relative to the mean (LSM), not a Liepāja gauge reading.

**Not verified, left out:** an LVĢMC warning level for Latgale in Aug 2017 (the banner is simulated); exact flooded areas and roads in 2017; per-station gusts in Liepāja 2005 (only snippets: 35 m/s); a Liepāja water-level reading for 2005; deaths in 2005 (Baltic Times reports a child killed in a candle fire in Tukums district; not in the card); June 2021 monthly mean (LVĢMC June 2021 review URL returned 404); shopping centres as cooling places (no such category in the map DB).

**Would make it real:** LVĢMC observations (CC0, 365-day archive) for real rain/gust/temperature per station; LVĢMC sea-level gauges; a published list of cooling places from municipalities (none today).

**Classifier:** after classifier round 2 (#81), every `vaicajums` lands on the right scenario: "dūmi no noliktavas Rīga" → `dumi_ara`, "nestrādā e-pakalpojumi" → `e_pakalpojumi`.

**Smoke cones:** zone type `sektors` in `demo.js`: source, `virziens` (where the smoke goes, degrees from north), `platums`, `garums_m`. Nearest places can be filtered to outside the cone (`arpus`).

---

## Rules kept

- Everything injected carries a visible **SIMULĀCIJA** badge: the map corner, banner, card, and tooltips/popups of zones and markers.
- No `tel:` links (phone numbers are plain text; Playwright checks there are 0 `a[href^="tel:"]`). "Jūs" form.
- Only open-licence data on the map, the same sources as the live map. The DTM is CC BY 4.0, credited in the polygon popup and the card.
- While a demo runs, the real LVĢMC banner and the forecast/warnings panel (`prognozes.js`, #46) are hidden so they don't mix with the simulation. Both come back on "Beigt demo" (the forecast panel stays closed until opened).
- `app.js` is untouched. The only hook is 2 lines in `index.html` (`demo.css`, `demo.js`); `demo.js` uses `app.js` globals.

## Check

`uv run --no-project --with playwright src/demo/parbaude.py` serves `production/` locally and proxies `/api/*` to map.repo.lv (read-only). It runs every scenario at 375×740 and 1280×800, then "Beigt demo" and a direct link. It saves screenshots to `ekr-demo/` and fails on JS errors, HTTP errors (except the known LVĢMC flood WMS 404 tiles), `tel:` links or horizontal scroll.
