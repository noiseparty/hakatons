# Avotu pārbaude 2026-10-10 (geolatvija, NAP, satiksme, zibens, senotajs, organizatori)

Six sources the user had open in the browser, checked by research agents on 2026-10-10 ~02:00. Ranking at the end. Only licences actually read on the source page count; "BY-NC" is not open for us (CLAUDE.md allows CC0 / CC BY / ODbL).

## 1. geolatvija.lv — "we are version 2.0 of this"

What it is: the national geoportal (VARAM/VRAA), a React SPA built for spatial planning (TAPIS zoning, participation budgets, a catalogue of 282 "ģeoprodukti"). Opens on a map and is responsive, but: cookie modal + promo modal first; default layers are zoning; address search gave no result in a headless test; 282 products the user must find and toggle; **no decision, no nearest shelter/hospital, no route, nothing about floods, shelters or warnings.** That is the pitch contrast: same official sources, one answer instead of a catalogue.

API: the catalogue is open and keyless: `https://geolatvija.lv/api/v1/public/geoproducts?page=1&pageSize=30`, `/api/v1/public/geoproducts/{id}` returns service URLs + licence. Services are proxied via `https://geo-dpps.viss.gov.lv/api/DPPSPackage/client/<pkg>/<uuid>` (anonymous, CORS reflects our origin, no key, no rate limit seen). Append `?service=WMS|WFS|WMTS&request=GetCapabilities`.

| Service | Package | Licence (catalogue) | Use |
|---|---|---|---|
| LVĢMC flood risk maps #309 (WMS) / #437 WMTS "Juras_veja_pludi" | `Pludu_risk_436_WTD8Ns/5e95ad7d-1362-47a1-9fd0-8226a06f7989`, `Pludu_risk_437_Y5CRtd/0d5ba0f8-7ce6-4476-bd96-7d6f890f822f` | CC BY-NC 4.0 ⚠ | flood zones (we already use the data.gov.lv 3rd-cycle maps, which are CC0; keep those) |
| Flood risk zones #171 (WFS) | `Pludu_risk_289_dchGXE/457870f3-deaf-400b-8d4d-32dfab44f96f` | CC BY-NC ⚠ | vector polygons for point-in-polygon |
| VZD addresses #291 WMS/WFS | `Adresu_tel_391_gaWJqT/ea7cceeb-044c-458c-8190-0f668cf2320a`, `Adresu_tel_418_k6gL2A/3d692785-0c95-44a8-816c-f2f91493c4ce` | CC BY 4.0 | addresses (we load VZD ourselves) |
| Administrative units #290 WMS/WFS | `Administra_387_4QDrLG/295a31bc-2220-44d9-88ff-30e857b8f2cc`, `Administra_420_OaRrgY/6a587613-c9e5-43b3-961f-60df2d42c5d8` | CC BY 4.0 | boundaries (we have regioni) |
| Buildings #135 WFS | `Ekas_un_bu_419_kg61P8/37f45682-3bd3-4df2-9e81-76364ad7d05b` | CC BY 4.0 | building footprints |
| LVĢMC met stations / observations #170, #161 | `Valsts_met_286_93CBgP/c9d79136-12fa-4654-8a8d-afd0d05afc58`, `Valsts_met_287_IwuGgz/31291d80-72e7-4b0c-854b-fd2ce90d9d1e` | CC BY-NC ⚠ | weather |
| Forest fire danger classes #110 WMS | `Meza_uguns_161_NgvXjv/917ea225-dd1d-4aae-9098-7ab8c64dcb50` | CC BY-NC ⚠ | fire risk |

Caveats: LĢIA basemaps / orthophoto / DEM have **no anonymous service** (e-application licence; `wms.lgia.gov.lv/open/...` returned 403). The LĢIA open-data page (CC BY 4.0) lists orthophoto cycles and the **20 m DEM as downloads only**; that is what terminal D uses for the ≥15 m high-ground layer. The catalogue marks most LVĢMC / LĢIA services BY-NC while data.gov.lv publishes the same LVĢMC data as CC0: cite data.gov.lv.

## 2. transportdata.gov.lv (NAP) — official live road data

56 DCAT datasets, almost all LVC, **all CC0**. Catalogue keyless (`https://www.transportdata.gov.lv/api/v1/subscriber/metadata_dcat`); every file download needs a free per-dataset key (`x-api-key`; register as "DATU ŅĒMĒJS" at transportdata.gov.lv/lv/8195, press ABONĒT per dataset). Download: `POST https://www.transportdata.gov.lv/api/v1/get/file/download-file` with body `{"file_id":"<id>","format":"xml"}`. Format DATEX II v3 `SituationPublication`. No GTFS-RT, no cameras, no ferries / airports on NAP.

Useful feeds: road closures (card 75611a36-e66b-40cf-af2c-69db48c278cf), accidents / incidents (e8659cdd-…), lane closures (82e20567-…), road works (35fa5c41-…, aacdd187-…), slippery road / poor conditions (f3204a64-…, 18e8ab75-…; HTTP 204 in summer), weather station readings (5a1e9a81-…) + locations (3d2d3df3-…), weight limits GeoJSON (d5337096-…). Also keyless: LVC "Waze feed" `data.lvceli.lv/waze_feed/defaultv2.aspx` (XML, licence not stated, was empty). GTFS: ATD buses (data.gov.lv, CC0, daily), trains (vivi.lv), Rīgas satiksme.

The kit already parses all of this: `ai-open-data-2026-hakatons/ca-plani-hakatons/avoti/celu-tikls/datubaze.py` (`_situacijas`), keys in gitignored `dati/nap_atslegas.json` (17 datasets subscribed 2026-07-31 by the kit authors; **check whether we have our own keys, otherwise register**). Nothing from NAP is on map.repo.lv yet → terminal B, branch `noiseparty/celi`: `/api/celi` + layer + result-card line. VPS: keys go to `/etc/hakatons/map.env`.

## 3. Real-time traffic: openwebninja.com, wazeapi.com — avoid

| Source | Latvia | Cost | Terms |
|---|---|---|---|
| OpenWebNinja `/waze/alerts-and-jams` | unverified | 50 free requests, then $0.03 per 10 | resells scraped Waze / Google data; terms not retrievable; legal risk |
| wazeapi.com | unverified | 100 free, $35 / month | "does not own the data", silent on public display, **prohibits safety-critical use**, not affiliated with Waze |
| Waze for Cities (CCP) | LAU partner since 2019 | free | public bodies only, internal use, no republishing |
| TomTom Traffic | likely | 2 500 requests / day free | attribution; display terms unverified |
| LVC DATEX II via NAP | state roads | free | CC0 ✅ |

Decision: official DATEX II only (section 2). The two scrapers are unlicensed and forbid safety-critical use; a crisis map cannot be built on them, and alternating between them doubles the risk. TomTom is the only third-party option worth a labelled layer later.

## 4. Lightning / storms in real time

| Source | Access | Latvia | Licence | Verdict |
|---|---|---|---|---|
| **FMI open data WFS** `https://opendata.fmi.fi/wfs`, stored query `fmi::observations::lightning::simple` | XML, individual strikes, minutes of lag, 600 requests / 5 min | yes (bbox 20.8,55.6,28.3,58.1 returned 2 752 values on a 2025 storm day) | **CC BY 4.0** | ✅ use |
| LVĢMC lightning grid (data.gov.lv) `zibens_rezgis_operativie_dati.csv` | CSV, hourly, 5×5 km cells, last 24 h, 2–3 h lag, mostly zeros | yes | CC0 | ✅ density layer, label the lag |
| Meteoalarm Latvia (CAP JSON / Atom) | live warning polygons | yes | ~CC BY 4.0 + redistribution T&C (unread) | backup for the banner |
| Blitzortung / lightningmaps.org | WebSocket / JSON | yes | private / entertainment only, no redistribution, **no storm-warning use** | ❌ |
| RainViewer radar | tiles | yes | personal / educational only | ❌ |
| Windy / OpenWeatherMap embeds | widgets | yes | own ToS, not open | ❌ |
| EUCLID / nowcast | commercial | yes | paid | ❌ |

→ terminal E, branch `noiseparty/zibens`: `/api/zibens` (FMI, 60 s cache) + layer "Zibens (30 min)"; an empty result is shown as "Pēdējās 30 min zibens nav reģistrēts".

## 5. senotajs.lv — where their data comes from

Sources listed on senotajs.lv/info/dati: rain + temperature = **LVĢMC open data (CC0)** interpolated to a ~30 km grid; forecasts = LVĢMC populated-places forecast (CC0, the same dataset behind our `/api/prognozes`); soil moisture 3–9 cm + ET₀ = **Open-Meteo** (CC BY 4.0, free for non-commercial use under 10 000 calls / day); the "26 days" is a Boletus heuristic, not a dataset; the bear layer is a read-only heatmap of lacukarte.lv / lacupedas.lv / iNaturalist / GBIF reports, last 12 months, rounded to ~1 km, **no licence, no API**; basemap OSM; satellite Esri (we removed Esri). No NASA / Copernicus / ECMWF, no own stations.

What to copy: (a) a context line "Pēdējās 26 dienās: 53 mm; augsne mitra (Open-Meteo, CC BY 4.0, nav brīdinājums)" from `https://api.open-meteo.com/v1/forecast?latitude=&longitude=&daily=precipitation_sum&hourly=soil_moisture_3_to_9cm&past_days=26&forecast_days=3&timezone=Europe%2FRiga` (→ terminal E); (b) lacukarte.lv's report UX for our own "ziņot par bīstamību" feature (fallen tree, blocked road, outage): moderated, confirm / dispute counts, 7-day default filter, coordinates rounded to ~1 km, stored in our own table under our own licence (not built yet).

## 6. Organisers' repo (lata-org/ai-open-data-2026-hakatons)

Nothing new since our vendored commit 8371565 (2026-10-09 08:20Z): 3 commits in total, 0 issues / PRs, README byte-identical, no storm data. The submission text is one sentence: "Sestdien komanda nodod publicētu prototipu vai maketu, 10 minūšu prezentāciju un skaidru atbildi, kas ir lietotājs un kā viņu sasniegs." No form, deadline time or slide format is stated; ask on the day. **Pitch risk:** criterion 3 asks for "3 līdz 6 soļi, kopsavilkums pirms iesniegšanas un skaidrs noslēgums ar norādi, kas sekos"; our single result card replaces the steps, so the pitch needs one sentence on that and the card needs its "Kas notiks tālāk" block.

## Ranking: what to show today

1. **LVC road closures / incidents** (NAP, CC0, live): terminal B, in progress.
2. **Lightning, last 30 min** (FMI, CC BY 4.0) + LVĢMC 24 h grid (CC0): terminal E, in progress.
3. **Rain + soil context line** (Open-Meteo, CC BY 4.0): terminal E, in progress.
4. **LĢIA 20 m DEM** (CC BY 4.0, download) for the ≥15 m high-ground layer: terminal D, in progress.
5. Pitch slide "geolatvija.lv 1.0 vs 2.0": a catalogue of 282 products vs one answer, same official sources.
6. Later: "ziņot par bīstamību" community reports (lacukarte pattern); a labelled TomTom layer; GTFS stops for evacuation; Meteoalarm as banner backup after reading its T&C.

Not usable: Blitzortung, RainViewer, Windy / OWM embeds, openwebninja, wazeapi, senotajs bear data, LĢIA WMS (needs a licence application), geolatvija BY-NC services.
