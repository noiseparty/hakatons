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
| **Would make it real** | **Sadales tīkls outage map** JSON (`karte.sadalestikls.lv/lv/atslegumi-elektrotikla/unplanned`): public but **no licence**; ask ST (already in `TODO.md`). **LVC road events (DATEX II)** via the National Access Point (transportdata.gov.lv), free API key, loader in the kit (`avoti/celu-tikls/`); check the licence terms. **LVĢMC observations** (above) for the actual gust maxima per station: the dataset exists (CC0, 365-day archive), not loaded yet. |
| **Missing** | Live ATM / card-terminal status (banks don't publish). Which fuel stations have generators (the ministry list isn't public). Restoration ETA per street. **Not verified:** the pitch's "~277 000 households" (seen only in a search snippet; the verified figures are ~245 000 at one point in time and ~260 000 affected overall). Observed LVĢMC station gust maxima for 22–23 Aug were not found; sources disagree on the warning level (red in the west vs orange). |

## 7. No power and no mobile network across a city or municipality (`bez-sakariem`)

| | |
|---|---|
| **Used now** | Pick the area (Rīga, Ogre, Bauska, Rēzekne, Liepāja, Daugavpils, Valmiera; real VZD boundary). Every layer that depends on live status (pharmacies, ATMs, fuel stations, river gauges) is greyed with "status nezināms". The card lists where to go **without a phone**: the nearest VUGD fire depots and police (IeM IC, CC0), the 24/7 hospital and the municipal assembly points (CA plans). Offline advice plus a **print / save as PDF** button (print CSS prints only the card). |
| **Would make it real** | Operator outage areas (LMT, Tele2, Bite): not public. National roaming in a crisis is only a proposal (Saeima committee, above). **LR1 frequency list:** https://latvijasradio.lsm.lv/lv/lr1/frekvences/ is not structured data. The card states only Rīga 90.7 FM, taken from a secondary source (to be confirmed against the official LR / NEPLP list). |
| **Missing** | A real offline mode. The site has no service worker, so without the internet it won't open. The honest answer in the card is "print it now". A PWA with cached tiles and data for the user's own area is the obvious next step. |

---

## Rules kept

- Everything injected carries a visible **SIMULĀCIJA** badge: the map corner, banner, card, and tooltips/popups of zones and markers.
- No `tel:` links (phone numbers are plain text; Playwright checks there are 0 `a[href^="tel:"]`). "Jūs" form.
- Only open-licence data on the map, the same sources as the live map. The DTM is CC BY 4.0, credited in the polygon popup and the card.
- While a demo runs, the real LVĢMC banner and the forecast/warnings panel (`prognozes.js`, #46) are hidden so they don't mix with the simulation. Both come back on "Beigt demo" (the forecast panel stays closed until opened).
- `app.js` is untouched. The only hook is 2 lines in `index.html` (`demo.css`, `demo.js`); `demo.js` uses `app.js` globals.

## Check

`uv run --no-project --with playwright src/demo/parbaude.py` serves `production/` locally and proxies `/api/*` to map.repo.lv (read-only). It runs every scenario at 375×740 and 1280×800, then "Beigt demo" and a direct link. It saves screenshots to `ekr-demo/` and fails on JS errors, HTTP errors (except the known LVĢMC flood WMS 404 tiles), `tel:` links or horizontal scroll.
