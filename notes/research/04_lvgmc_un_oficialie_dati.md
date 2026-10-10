# LVĢMC un citi oficiālie dati krīžu kartei (pārbaudīts 2026-10-10)

Catalogue of what LVĢMC and other official bodies publish that we could show on https://map.repo.lv, with the licence actually checked (CKAN `license_id` via `https://data.gov.lv/dati/api/3/action/package_show?id=<name>`). Earlier inventory: `02_latvia_open_data_inventory.md`. Small samples (<20 KB each): `paraugi/`.

Common facts for LVĢMC on data.gov.lv: organisation `lvgmc` (28 datasets), **all CC0-1.0** (attribution not required; we still credit "LVĢMC / data.gov.lv"). CSV, UTF-8 with BOM, all values quoted, times in Latvian local time without a zone. Downloads have **no CORS header**, so the browser can't read them directly; everything goes through our API (`src/karte/api/karte_api.py`). CKAN `datastore_search_sql` works for filtering large resources.

## Tabula

| # | Avots | URL | Formāts | Biežums | Licence | Koord. | Ko mēs ar to darām | Tiešām atvērts? |
|---|---|---|---|---|---|---|---|---|
| 1 | **LVĢMC hidrometeoroloģiskie brīdinājumi** | [hidrometeorologiskie-bridinajumi](https://data.gov.lv/dati/lv/dataset/hidrometeorologiskie-bridinajumi): `bridinajumu_metadata.csv`, `bridinajumu_poligoni.csv` (vertex per row), `bridinajumu_novadi.csv`, `novadi.csv` | CSV (not CAP) | irregular, as issued | CC0 | ✅ polygons | Banner (live), **warning polygons on the map + feed items** (this PR) | ✅ |
| 2 | **LVĢMC prognozes apdzīvotām vietām** | [meteorologiskas-prognozes-apdzivotam-vietam-jaunaka-datu-kopa](https://data.gov.lv/dati/lv/dataset/meteorologiskas-prognozes-apdzivotam-vietam-jaunaka-datu-kopa): `cities.csv` (6 427 places: 82 towns, 6 282 villages, 63 other), `forecast_cities.csv` (hourly, 24 h, 70.8 MB), `forecast_cities_day.csv` (daily, 7 days, 16.6 MB), `forcity_param.csv`, `weather_codes.csv` | CSV long format `CITY_ID, PARA_ID, DATUMS, VERTIBA` | several times a day (resources re-uploaded with each new run) | CC0 | ✅ per place | **"Prognoze / ziņas" feed + regions coloured by forecast** (this PR); later "next 24 h at your place" in the result card | ✅ |
| 3 | LVĢMC novērojumi (meteo + hidro) | [hidrometeorologiskie-noverojumi](https://data.gov.lv/dati/lv/dataset/hidrometeorologiskie-noverojumi): `meteo_operativie_dati.csv`, `hidro_operativie_dati.csv`, `laika_operativie_dati.csv` (weather phenomena as text), station tables (`GEOGR1` = lon, `GEOGR2` = lat) | CSV | hourly | CC0 | ✅ via stations | River levels (live: `/api/udens`); could add current gusts / "LIETUS" text | ✅ |
| 4 | LVĢMC hidroloģiskās prognozes | [hidrologiskas-prognozes](https://data.gov.lv/dati/lv/dataset/hidrologiskas-prognozes): `hidro_forecast.csv` (105 KB; `UDLIM` level in m a.s.l. LAS-2000.5, ensemble `MINIM…V5…MEDIANA…MAXIM`, 14 days) | CSV | daily | CC0 | via station | "River expected to rise" next to the gauge; needs height-system conversion vs observed `LIMEN` (cm from gauge zero) | ✅ |
| 5 | LVĢMC zibens režģis | [telpiskie-hidrometeorologiskie-noverojumi](https://data.gov.lv/dati/lv/dataset/telpiskie-hidrometeorologiskie-noverojumi): `zibens_rezgis_operativie_dati.csv` (`LAIKS, LON, LAT, CC, CG, TOTAL`, 5×5 km, last 24 h, 4.7 MB) | CSV | hourly | CC0 | ✅ grid | Thunderstorm layer (only useful in summer) | ✅ |
| 6 | LVĢMC telpiskās prognozes (9 dienas) | [telpiskas-meteorologiskas-prognozes](https://data.gov.lv/dati/lv/dataset/telpiskas-meteorologiskas-prognozes): one CSV per parameter (`wgust`, `tp`, `t`, `tstm`, `sd`, …), 23–26 MB each | CSV grid | 2×/day | CC0 | ✅ grid | Wind / precipitation heat map; heavy, would need server-side tiling | ✅ |
| 7 | LVĢMC jūras prognozes | [telpiskas-juras-prognozes](https://data.gov.lv/dati/lv/dataset/telpiskas-juras-prognozes): waves, sea level, ice | CSV grid, ~180 MB each | 2×/day | CC0 | ✅ | Storm surge context for the coast; too heavy for the demo | ✅ |
| 8 | LVĢMC klimats | [klimatiskie-dati](https://data.gov.lv/dati/lv/dataset/klimatiskie-dati): 1991–2020 normals, monthly stats, scenarios | CSV | monthly | CC0 | not checked | "Typical October" context — marginal | ✅ |
| 9 | LVĢMC plūdu riska kartes | ĢeoLatvija WMS (3rd cycle) | WMS | static | CC0 | ✅ | Live: `/api/pludi` + map toggle | ✅ |
| 10 | Radar / precipitation images | — | — | — | — | — | Not published as open data (nothing on data.gov.lv; videscentrs radar pictures have no licence) | ❌ |
| 11 | **Meteoalarm (EUMETNET)** | [JSON](https://feeds.meteoalarm.org/api/v1/warnings/feeds-latvia) (CAP structure, polygons) · [Atom](https://feeds.meteoalarm.org/feeds/meteoalarm-legacy-atom-latvia) (EMMA_ID) | CAP JSON / Atom | minutes–hours | "equivalent to CC BY 4.0 with additional redistribution requirements" (feed `<rights>`); T&C page not read | ✅ polygons | Cross-check / fallback for the LVĢMC banner (same sender: LVĢMC) | ⚠ conditions unread |
| 12 | LVC / NAP (transportdata.gov.lv) | [DCAT](https://www.transportdata.gov.lv/api/v1/subscriber/metadata_dcat) (55 datasets): road closures, roadworks, accidents, slippery road, poor conditions, visibility, road weather stations | DATEX II XML (live), GeoJSON/CSV (static) | continuous | CC0 | ✅ | "Closures / slippery road on your route" layer | ✅ but **free per-dataset API key** (`dati/nap_atslegas.json`, server-side only); no LVC camera dataset |
| 13 | Sadales tīkls outages | sadalestikls.lv map | website | live | none found | ? | Link only | ❌ no open data, no API found |
| 14 | VUGD / VP / NMPD | data.gov.lv: depot and station addresses (CC0, already on the map), NMPD calls `oper_info` (annual, per municipality, no coords) | CSV | annual | CC0 | addresses only | Context ("calls per municipality"), not live | ✅ but not live |
| 15 | LV-Alert (šūnu apraide) | — (messages re-posted on 112.lv) | — | — | — | — | Explanatory line + link to 112.lv | ❌ no feed/archive |
| 16 | Municipal feeds | e.g. `jelgava.lv/rss` (news); Rīga open data on data.gov.lv (CC BY 4.0: public shelters, municipal police) | RSS / CSV | varies | mostly unstated; Rīga CC BY 4.0 | varies | Rīga shelters could replace the ⚠ 112.lv list in Rīga | partly |

Also found, not yet checked: `evakuacijas-pulcesanas-vietas` (CC BY 4.0) on data.gov.lv — evacuation assembly points from some publisher; compare with our CA-plan extraction.

## Ko varam rādīt rīt (ranking)

1. **LVĢMC prognozes apdzīvotām vietām → "Prognoze / ziņas" lente.** CC0, coordinates, 7 days, max gusts / precipitation / temperature per place. On 10.10 it shows gusts up to 22.5 m/s and 21.6 mm of rain, so the demo has real content. Built in PR `noiseparty/lvgmc` (`/api/prognozes`).
2. **LVĢMC brīdinājumu poligoni on the map.** Already fetched for the banner; this PR draws them and turns each warning into a feed item that zooms to its area.
3. **LVĢMC hidroloģiskās prognozes next to the gauges** (small CSV, CC0). Needs the LAS-2000.5 ↔ gauge-zero conversion from the station table: a few hours of work.
4. Meteoalarm as a fallback for the warnings — **T&C read 2026-10-10, verdict: allowed with conditions** (see below).

### Meteoalarm redistribution terms (read 2026-10-10)

Source: https://www.meteoalarm.org/en/live/page/terms-and-conditions ("Last Updated: 15/03/2024"; the page is a JS app, text read from its CMS API `cms-visualization.meteoalarm.org/api/v1/content-pages/terms-and-conditions?locale=en`). The feeds page https://feeds.meteoalarm.org/ links "License (CC BY 4.0)". Latvia Atom feed: https://feeds.meteoalarm.org/feeds/meteoalarm-legacy-atom-latvia (RSS was sunset on 2026-01-14). No registration or key.

Clause 5 "Use and Redistribution of Information": the warning **Information** may be redistributed "under terms equivalent to … CC BY 4.0", plus:
- if modified, the unmodified original must be redistributed alongside;
- for single-country data the issuing service must always be named — for Latvia **LVĢMC**;
- the **time of issue** must be shown;
- internet applications must **link to www.meteoalarm.org**;
- operational redistribution must be real-time: **average delay < 5 min, never > 10 min** (so cache ≤ 10 min);
- this **disclaimer must be published**: "Time delays between this website and the www.meteoalarm.org website are possible. For the most up-to-date awareness information as published by the participating National Meteorological and Hydrological Services, please refer to www.meteoalarm.org."
- Meteoalarm's own **Content** (icons, maps, design, software) is not covered — don't copy it.

**Verdict for map.repo.lv:** usable as a fallback for `/api/bridinajumi`, if the banner then shows "LVĢMC (caur Meteoalarm)", the issue time, a link to meteoalarm.org and the disclaimer, keeps the text unchanged, and refreshes within 10 min. Not needed while the LVĢMC data.gov.lv CSV (CC0) works, which has none of these conditions.
5. LVC closures / slippery roads — keys exist, but DATEX II parsing + server-side proxy is a half-day job.

**Blocks the rest:** no open radar; Sadales tīkls and LV-Alert have no feed at all; NAP needs keys and DATEX II parsing; gridded forecasts are 25–180 MB per parameter; NMPD/VUGD data is annual, not live.
