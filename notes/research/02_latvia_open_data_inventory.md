# 02 — Latvian open data inventory for the crisis map

**Date:** 2026-10-09 · **Scope:** Ogres novads first, extensible to all 43 municipalities · **Method:** I ran 60+ `package_search` queries against the data.gov.lv CKAN API, called `package_show` on the key datasets, and fetched the first 400 bytes of each resource to check that it works. I also probed the portals directly and ran an Overpass count for Ogres novads.

Legend:
- **Verified**: ✅ = I fetched it today and got real data. ⚠️ = it responds, but with a caveat. ❌ = it is blocked or there is no open feed.
- **Freq.**: Live = updated many times a day or in near real time. D = daily. W = weekly. A = annual. S = static or irregular.
- **Coords**: Y = the data has coordinates. A = it has an address or VZD code only, so it needs geocoding through VARIS (already in `avoti/kadastrs`). N = no location.
- **CRS note:** most state data is in **LKS-92 / EPSG:3059**. Reproject it to WGS84 for Leaflet.

---

## 0. Already in `avoti/` (do not re-propose)

| Data | Source | Where |
|---|---|---|
| 781 public shelters (31 in Ogres novads) | 112.lv / VUGD / IeM IC | `avoti/patvertnes/` |
| Addresses with coordinates (VARIS `aw_eka`), admin hierarchy | VZD (CC BY 4.0, D) | `avoti/kadastrs/` |
| Cadastre (NĪVKIS): buildings, basements, floors, material | VZD (W) | `avoti/kadastrs/` |
| State road network, priority roads (MK 188), bridge tonnage, black spots, DATEX II closures/icing/road weather | LVC NAP transportdata.gov.lv | `avoti/celu-tikls/` |
| Flood risk zones WMS (10/100/200 yr), Ogre river gauge | LVĢMC / ĢEOLatvija | concept doc §1.2 |
| Evacuation points, municipal boundary, dangerous-goods rail corridor | Ogre CA plan, VZD/LĢIA | concept doc §1.2 |

---

## 1. Emergency services and public safety

| Source | Owner | Endpoint | Format | Freq. | Licence | Coords | Layer / crisis | Verified |
|---|---|---|---|---|---|---|---|---|
| **VUGD fire depots** (87 nationwide; "VUGD Ogres daļa", Rīgas iela 4) | IeM IC (VKCP IĢIS) | [CSV](https://data.gov.lv/dati/dataset/2466e938-6eba-4016-8ff8-f7e3f2736249/resource/a91ff743-e064-41d4-b449-b29d713fc6fb/download/vugd_depo_adreses.csv) · [dataset](https://data.gov.lv/dati/lv/dataset/vkcp-igis-vugd-depo-adreses) | CSV | continuous | CC0 | Y (LKS-92) | Responders · all | ✅ |
| **State Police stations** (41) | IeM IC | [CSV](https://data.gov.lv/dati/dataset/f37fb118-4dfe-4011-9816-ebe964ebc203/resource/80cc2dd9-f424-4c5c-9bbc-a01c02bfcb28/download/vp_iecirknu_adreses.csv) · [dataset](https://data.gov.lv/dati/lv/dataset/vkcp-igis-vp-iecirknu-adreses) | CSV | continuous | CC0 | Y (LKS-92) | Responders · martial law, unrest | ✅ |
| **Municipal police units** | IeM IC | [dataset](https://data.gov.lv/dati/lv/dataset/vkcp-igis-pasvaldibas-policijas-vienibu-adreses) | CSV (`;`, cp1257) | A (2024) | CC0 | Y (LKS + WGS) | Responders | ✅ (encoding!) |
| **Fire hydrants and open water intake points** (~16.6k) | IeM IC | [CSV](https://data.gov.lv/dati/dataset/d43c5e7f-7c11-4b0e-8222-51261c23d752/resource/b3705fbe-3b29-47a3-a8c7-cdb3269d26cc/download/atklatas_udens_nemsanas_vietas_un_hidranti.csv) | CSV | continuous | CC0 | Y (LKS-92) | Firefighting water; emergency non-potable water | ✅ |
| VKCP emergency-event statistics + event-type classifier | IeM IC | [dataset](https://data.gov.lv/dati/lv/dataset/vkcp-arkartas-notikumu-statistikas-dati) | CSV | continuous | CC0 | N/aggregated | Historical risk heat-map | ✅ (listed) |
| NMPD call statistics by territory | NMPD | [dataset](https://data.gov.lv/dati/lv/dataset/nmp_izsaukumi_adm_teritorija) | CSV/JSON | A | CC0 | N | Context only | listed |
| **NMPD ambulance stations** | — | — | — | — | — | — | Responders | ❌ **GAP** |

## 2. Health and medicines

| Source | Owner | Endpoint | Format | Freq. | Licence | Coords | Layer | Verified |
|---|---|---|---|---|---|---|---|---|
| **Medical institutions with lat/long** (473; 18 rows for Ogre, incl. Ogres slimnīca) | IeM IC (from NVD) | [CSV](https://data.gov.lv/dati/dataset/05068340-d155-49cc-9a37-ab7d63ccd769/resource/5ea6e4aa-ee21-462a-8590-283483d2b0a4/download/medicinasiestades.csv) | CSV | A (**last 2024-07**) | CC0 | Y (WGS84) | Hospitals, GPs · all | ✅ (stale; cross-check) |
| **NVD health services (INSPIRE)**, layer `nvd_health_services_type` | NVD via ĢEOLatvija | [WMS](https://geo-dpps.viss.gov.lv/api/DPPSPackage/client/Veselibas__91_1JBLK0/cdef1763-de86-4b84-8780-ac859fac183e) · [ATOM](https://geolatvija.lv/api/v1/atom/c0313e71-7473-452b-8062-52024afd4808/serviceatoma) | WMS/ATOM | continuous | CC0 | Y | Health overlay | ✅ |
| **Pharmacies: ZVA pharmaceutical licence register** (~1,036 rows; 25 for Ogre) | ZVA | [CSV](https://dati.zva.gov.lv/fdu-registrs/export/fdu_register.csv) · [JSON](https://dati.zva.gov.lv/fdu-registrs/export/fdu_register.json) · [XML](https://dati.zva.gov.lv/fdu-registrs/export/fdu_register.xml) | CSV/JSON/XML | D | CC0 | Y (`object_coord_x/y`) | Pharmacies · pandemic, blackout | ✅ |
| Hospital discharge feeds (PSKUS, RAKUS, BKUS) | Hospitals | data.gov.lv `*izrakstisanas*` | url | D | CC0 | N | Capacity proxy (Riga only) | listed |
| SPKC urgent notifications by institution | SPKC | [dataset](https://data.gov.lv/dati/lv/dataset/steidzemie-pazinojumi-iestades) | CSV | A | CC0 | N | Pandemic context | listed |
| **Hospital bed and ICU availability, backup-generator status** | — | — | — | — | — | — | Health resilience | ❌ **GAP** (not public) |

## 3. Vulnerable populations and social care

| Source | Owner | Endpoint | Format | Freq. | Licence | Coords | Layer | Verified |
|---|---|---|---|---|---|---|---|---|
| **Social service provider register** (2,087 providers; 158 rows mention Ogre: care homes, group flats, rehab, day centres; includes residential vs non-residential and planned client count) | LM | [JSON (daily file)](https://data.gov.lv/dati/lv/dataset/socialo-pakalpojumu-sniedzeju-registra-dati) | JSON | **D** | CC0 | A (VZD address code, so join to VARIS) | **Priority evacuation / welfare checks** in blackout, heat failure, flood | ✅ |
| Out-of-family care support centres | LM | [dataset](https://data.gov.lv/dati/lv/dataset/aktualais-arpusgimenes-aprupes-atbalsta-centru-saraksts) | XLSX | S | CC0 | A | Vulnerable | listed |
| Disability counts by municipality (VDEĀVK) | VDEĀVK | data.gov.lv `pilngadigo-personu-ar-invaliditati-*` | XLSX | A | CC0 | N (municipality) | Needs estimate | listed |
| Population by age group, municipality/parish | CSP / PMLP | [CSP `iedzivotaji`](https://data.gov.lv/dati/lv/dataset/iedzivotaji), [PMLP](https://data.gov.lv/dati/lv/dataset/latvijas-iedzivotaju-skaits-pasvaldibas) | CSV | A | CC BY / CC0 | N (ATVK code) | Choropleth: 65+ and children share | ✅ |
| **Population distribution (INSPIRE PD)** | CSP | [ATOM](https://inspire.stat.gov.lv/geoserver/www/atom/pd-service-feed.xml) · [WMS](https://geo-dpps.viss.gov.lv/api/DPPSPackage/client/Pastavigo__107_c2BZM8/8efc886c-fb5d-480d-86f5-9a4cf3cc17f7) | ATOM/WMS | A | CC0 | Y (grid) | People-at-risk in a polygon | ✅ |
| **Dwellings in 1 km and 100 m grid** (incl. `HEAT_DW`, heating type, building age) | CSP | [dataset](https://data.gov.lv/dati/lv/dataset/majokli-rezgis) | CSV (grid codes) | census 2011/2021 | CC BY | Y (grid ID) | **Heating-failure exposure**, building age | ✅ |
| Functional territories demo (age breakdown, GPKG) | CSP | [dataset](https://data.gov.lv/dati/lv/dataset/ft) | GPKG/CSV | S | CC0 | Y | Population | ✅ |
| **Individual persons needing assistance (bedridden, oxygen, dialysis)** | — | — | — | — | — | — | — | ❌ **GAP** (GDPR; municipal social service holds it, so show only aggregated) |

## 4. Education, culture and gathering places (potential heating, info and assembly points)

| Source | Owner | Endpoint | Format | Freq. | Licence | Coords | Layer | Verified |
|---|---|---|---|---|---|---|---|---|
| **Educational institutions (VIIS-based, by type: PII, schools, higher ed)**, layers `izm_iestades_*`, `izm_point_*` | IZM via ĢEOLatvija | [WMS](https://geo-dpps.viss.gov.lv/api/DPPSPackage/client/Izglitibas_549_v0TWpe/a227e614-f247-4e91-9f47-d2ad2ff3cb28) · [portal](https://geolatvija.lv/main?geoProductId=330) | WMS (+WFS sibling datasets) | continuous | CC0 | Y | Schools/kindergartens (evac priority + candidate shelters/heating points) | ✅ |
| **Culture institutions** (7,775 rows; 211 Ogre rows; libraries, culture centres, museums, venues) | KISC | [CSV](https://data.gov.lv/dati/lv/dataset/6d564a05-1d8c-49b8-835f-c969c61da182/resource/92af15f3-9674-426e-925c-86c6254baa0d/download/objektusaraksts.csv) | CSV | continuous | CC0 | Y (WGS + LKS) | **Culture centres and libraries are candidate "warming / info / charging points"** | ✅ |
| Riga: education/culture/sports territories | Rīgas dome | [dataset](https://data.gov.lv/dati/lv/dataset/izglitibas-kulturas-un-sporta-iestazu-lietosana-nodotas-teritorijas) | SHP/GPKG/KML | M | CC BY | Y | Reference model | listed |

## 5. Utilities: electricity, gas, heat, water, telecom

| Source | Owner | Endpoint | Format | Freq. | Licence | Coords | Layer | Verified |
|---|---|---|---|---|---|---|---|---|
| **Sadales tīkls outage map, unplanned outages** | AS Sadales tīkls | `https://karte.sadalestikls.lv/lv/atslegumi-elektrotikla/unplanned` (also `/planned`, `/applications`); UI: [karte.sadalestikls.lv](https://karte.sadalestikls.lv) | **JSON** (undocumented): `disconnects[]` with LKS-92 x/y (fields misnamed `lat`/`lng`), `clients_all`, `outage_id`, end time | **Live** | **none stated**, quasi-open | Y (LKS-92) | **Blackout layer** (customers affected per point) | ✅ (returned live outages today). Ask ST for permission/ToS; cache politely |
| AST transmission outage map | AS Augstsprieguma tīkls | ast.lv (outage map shown during the 2026-08-22 storm) | HTML | Live | — | — | Substation-level blackout | ❌ 403 to scripts |
| Gas network (Gaso / Conexus) | Gaso, Conexus | gaso.lv | — | — | — | — | Gas outages | ❌ 403 / no feed (**GAP**) |
| **LPG cylinder sale points** + **LPG filling stations** | PTAC | [sale points](https://data.gov.lv/dati/lv/dataset/gazes-balonu-tirdzniecibas-vietas) · [filling](https://data.gov.lv/dati/lv/dataset/naftas-gazes-balonu-uzpildes-stacijas) | CSV | **D** | CC0 | A | Alt. heating/cooking fuel (blackout, gas failure) | ✅ (small: ~14 rows) |
| Drinking-water quality monitoring stations | VI/LVĢMC via ĢEOLatvija | [dataset (WFS)](https://data.gov.lv/dati/lv/dataset/dzeram-dens-kvalitte-un-monitoringa-stacijas-dati-wfs) | WMS/WFS | continuous | CC0 | Y | Water-supply nodes proxy | listed |
| Protection zones around water intakes | ĢEOLatvija | [dataset](https://data.gov.lv/dati/lv/dataset/aizsargjoslas-ap-dens-emanas-vietm) | WMS/WFS | continuous | CC0 | Y | **Locates municipal wells/intakes** (water-failure layer) | listed |
| Wastewater discharge points, agglomerations | ĢEOLatvija | [discharge](https://data.gov.lv/dati/lv/dataset/notekdeu-novadanas-vietas) · [agglom.](https://data.gov.lv/dati/lv/dataset/aglomercijas-komunlie-notekdei) | WMS/WFS | continuous | CC0 | Y | Sewage failure / pollution | listed |
| Riga heating-supply zones (reference) | Rīgas dome | [dataset](https://data.gov.lv/dati/lv/dataset/rigas-teritorialas-zonas-siltumapgades-veida-izvelei) | SHP/GPKG | A | CC BY | Y | District-heating area (model for Ogre) | listed |
| Number-allocation reports | Elektroniskie sakari | data.gov.lv | CSV | Q | CC0 | N | not useful | — |
| National broadband availability GIS (MK 424, 2025-07-08); public part only | SM / ESB / SPRK | not found as a download | — | — | — | — | Telecom coverage | ❌ **GAP** |
| **District-heating boiler houses and networks (Ogre: "Ogres Namsaimnieks"), water/sewer networks, pumping stations with backup power, telecom masts with backup power, mobile coverage** | — | — | — | — | — | — | Infrastructure failure | ❌ **GAP**: use OSM plus a municipal manual layer (see §10) |

## 6. Hazards, weather and warnings

| Source | Owner | Endpoint | Format | Freq. | Licence | Coords | Layer | Verified |
|---|---|---|---|---|---|---|---|---|
| **Hydrometeorological warnings, with polygons** | LVĢMC | [dataset](https://data.gov.lv/dati/lv/dataset/hidrometeorologiskie-bridinajumi): `bridinajumu_metadata.csv`, `bridinajumu_poligoni.csv` (lat/lon vertices), `bridinajumu_novadi.csv` | CSV | **Live** (irregular) | CC0 | Y (polygons) | **Storm / wind / flood warning layer** | ✅ |
| **Meteoalarm Latvia (CAP)** | EUMETNET / LVĢMC | [JSON](https://feeds.meteoalarm.org/api/v1/warnings/feeds-latvia) · [Atom](https://feeds.meteoalarm.org/feeds/meteoalarm-legacy-atom-latvia) | CAP JSON/Atom | **Live** | Meteoalarm terms (attribution) | Y (polygons) | Same, CAP-standard (backup feed) | ✅ |
| **Live hydro and meteo observations** (`meteo_operativie_dati.csv`, `hidro_operativie_dati.csv` + archives) | LVĢMC | [dataset](https://data.gov.lv/dati/lv/dataset/hidrometeorologiskie-noverojumi) | CSV (STATION_ID, param, time, value) | **Live** | CC0 | via station list | River levels (Ogre, Daugava), wind gusts | ✅ |
| Hydrological forecasts (percentile bands) | LVĢMC | [CSV](https://data.gov.lv/dati/dataset/5d9b0379-c0b8-4ce9-9094-7c30b5502433/resource/a967bf11-139f-4040-84d6-ce7c68006a8b/download/hidro_forecast.csv) | CSV | D | CC0 | via station | Flood forecast | ✅ |
| **Lightning density grid** (operational) | LVĢMC | [dataset](https://data.gov.lv/dati/lv/dataset/telpiskie-hidrometeorologiskie-noverojumi) | CSV lat/lon grid | Live | CC0 | Y | Thunderstorm layer | ✅ |
| Meteo station locations | LVĢMC via ĢEOLatvija | [WFS](https://geo-dpps.viss.gov.lv/api/DPPSPackage/client/Valsts_met_287_IwuGgz/31291d80-72e7-4b0c-854b-fd2ce90d9d1e) | WFS 2.0 | S | CC0 | Y | Station geometry for joins | ✅ |
| Flood risk zones WFS (vector, complements the WMS already used) | ĢEOLatvija | [WFS](https://geo-dpps.viss.gov.lv/api/DPPSPackage/client/Pludu_risk_289_dchGXE/457870f3-deaf-400b-8d4d-32dfab44f96f) · 3rd-cycle maps [dataset](https://data.gov.lv/dati/lv/dataset/3-cikla-latvijas-pldu-postjumu-vietu-un-pldu-riska-kartes) | WFS 2.0 | S | CC0 | Y | Flood, with vector intersection to addresses | ✅ |
| Air quality: monthly + modelled zones | LVĢMC | [monthly JSON](https://data.gov.lv/dati/lv/dataset/ikmenesa-gaisa-kvalitate), [modelled](https://data.gov.lv/dati/lv/dataset/gaisa-kvalittes-modelts-teritorijas) | JSON/WMS | M | CC0 | Y | Chemical accident / fire smoke context | listed |
| Radon assessment | VARAM | data.gov.lv `radona-gazes-limena-novertejums-latvija` | CSV | S | CC0 | — | minor | — |

## 7. Industrial, chemical and military hazards

| Source | Owner | Endpoint | Format | Freq. | Licence | Coords | Layer | Verified |
|---|---|---|---|---|---|---|---|---|
| **Seveso sites** (objects requiring an industrial accident prevention programme or safety report) | VVD / EVA | [dataset](https://data.gov.lv/dati/lv/dataset/objekti-kuriem-jaizstrada-rupniecisko-avariju-noversanas-programma-vai-drosibas-parskats) | XLSX | semi-annual | CC0 | A (geocode) | **Chemical accident zones** (buffer 500/1000 m) | ✅ |
| **EU Industrial Sites Registry (E-PRTR/IED)** | LVĢMC | [GML 2025](https://data.gov.lv/dati/lv/dataset/es-rupniecisko-vietu-registrs) | GML (INSPIRE) | A | CC0 | Y | Industrial hazard points | ✅ |
| PRTR pollutant release register | ĢEOLatvija | [dataset](https://data.gov.lv/dati/lv/dataset/piesrojoo-vielu-prneses-reistrs-prtr) | WMS/WFS | S | CC0 | Y | Same | listed |
| VVD A/B category permits | VVD | [dataset](https://data.gov.lv/dati/lv/dataset/izsniegtas-atlaujas-un-licences) | CSV/XLSX | continuous | CC0 | A | Polluting installations | listed |
| PVD-supervised food businesses (shops, producers, warehouses) | PVD | [ZIP](https://pakalpojumi.pvd.gov.lv/lv/opendata_files/ipvd_object_opendata/download) | ZIP (CSV) | D (metadata 2024) | CC0 | A | **Food supply points** (shortage, war) | ✅ |
| Restriction zones around military airfields/ranges | LĢIA | [dataset](https://data.gov.lv/dati/lv/dataset/ierobeojumu-zonas-ap-militrajiem-lidlaukiem-un-militrs-avicijas-poligoniem) | WMS/WFS | S | CC0 | Y | War / martial-law context | listed |
| Airfields (INSPIRE) | ĢEOLatvija | [dataset](https://data.gov.lv/dati/lv/dataset/lidlauki-inspire-dati) | WMS/WFS | S | CC0 | Y | Evac / logistics | ⚠️ WFS returned 500 |
| Registered weapons (aggregated) | IeM IC | data.gov.lv `registretie-ieroci-un-ierocu-ipasnieki` | CSV | M | CC0 | N | not for map | — |

## 8. Transport and mobility (beyond LVC NAP)

| Source | Owner | Endpoint | Format | Freq. | Licence | Coords | Layer | Verified |
|---|---|---|---|---|---|---|---|---|
| **Regional and intercity bus GTFS** (covers Ogre routes) | ATD | [gtfs-latvia-lv.zip](https://www.atd.lv/sites/default/files/GTFS/gtfs-latvia-lv.zip) (29 MB) · [dataset](https://data.gov.lv/dati/lv/dataset/atd-gtfs) | GTFS | D | CC0 | Y (stops) | **Evacuation pick-up points**, public transport status | ✅ |
| **Rail GTFS** (Rīga–Ogre–Lielvārde line) | ATD / Vivi | [GTFS.zip](https://vivi.lv/uploads/GTFS.zip) | GTFS | M | CC0 | Y | Rail evacuation | ✅ |
| Rail stations and stops | Pasažieru vilciens | [dataset](https://data.gov.lv/dati/lv/dataset/dezlcela-stacijas-un-pieturas-punkti) | XLSX | 2019 | CC0 | A/Y | Stations | listed (old) |
| Rīgas satiksme GTFS (reference) | Rīgas satiksme | [dataset](https://data.gov.lv/dati/lv/dataset/marsrutu-saraksti-rigas-satiksme-sabiedriskajam-transportam) | GTFS | M | CC0 | Y | Riga only | ✅ |
| Fuel prices (weekly avg) / fuel market monitoring | EVA | data.gov.lv `videjas_cenas`, `degvielas-tirgus-monitorings` | XML | W/M | CC0 | N | Fuel-shortage context only | listed |
| LVM forest roads and bridges | AS LVM | [dataset](https://data.gov.lv/dati/lv/dataset/as-latvijas-valsts-mezi-mezsaimniecibas-infrastruktura) | SHP | W | CC0 | Y | Alternative/detour routes, forest-fire access | listed |
| **Fuel stations** (no state register with location) | — | — | — | — | — | — | Fuel shortage, blackout | ❌ **GAP**: OSM (19 in Ogres novads) |

## 9. Base maps, boundaries and imagery

| Source | Owner | Endpoint | Format | Licence | Verified |
|---|---|---|---|---|---|
| Admin territories 2021/2026 (municipalities, parishes) | VARAM | [GeoJSON](https://data.gov.lv/dati/dataset/7bb04db9-97ce-4a30-b93a-10ba8dafd104/resource/3ded58bd-c0dc-419a-97ff-59ba45a7b1b0/download/administrativas_teritorijas_2021.geojson) (EPSG:3059) · [dataset](https://data.gov.lv/dati/lv/dataset/atr) | CC0 | ✅ |
| VZD cadastre spatial (parcels/buildings SHP) | VZD | [dataset](https://data.gov.lv/dati/lv/dataset/kadastra-informacijas-sistemas-atverti-telpiskie-dati) | CC BY | listed (W) |
| LĢIA orthophoto (8th cycle 2022–24) / topo 1:50k WMS | LĢIA | [WMS info](https://www.lgia.gov.lv/en/wms-servisi): **free but needs signed licence + login** via e-pieteikumi.lgia.gov.lv | free, authorised | ⚠️ not anonymous; for the public site use OSM tiles |
| LĢIA open data (topo 1:50k ZIP, 1:250k) | LĢIA | data.gov.lv `topogrfisk-karte-mrog-1-50-000-2-izdevums` | CC0 | listed |
| **OpenStreetMap Latvia extract** | Geofabrik | [latvia-latest.osm.pbf](https://download.geofabrik.de/europe/latvia-latest.osm.pbf) (134 MB), `-free.shp.zip`, `-free.gpkg.zip`; data up to 2026-10-08 | ODbL | ✅ |

## 10. Riga as reference model (same CKAN; shows the target data model for Ogre)

- [Riga public shelters](https://data.gov.lv/dati/lv/dataset/rigas-valstspilsetas-pasvaldibas-teritorija-izvietotas-publiskas-patvertnes) (SHP/GPKG/KML, weekly, CC BY): `caoip_publiskas_patversmes.*` ✅
- [Riga evacuation assembly points](https://data.gov.lv/dati/lv/dataset/evakuacijas-pulcesanas-vietas) (`caoip_evakuacijas_vietas.*`, weekly) ✅
- Riga municipal police structure, institution register (REST), heating zones. **This is the template Ogre should publish**, e.g. `ogre_caoip_*`.
- Note: `opendata.riga.lv` did not resolve. Riga data is now on data.gov.lv under the "Rīgas dome" organisation.

## 11. Warning and communication channels (context, not data feeds)

| Channel | Status | Data access |
|---|---|---|
| **LV-Alert cell broadcast** (šūnu apraide) | Live since 2025-07-01; first message sent 2025-07-10. Levels: red (presidential: state of emergency, mobilisation), orange (extreme: chemical, evacuation), yellow (severe: LVĢMC orange/red) | **No public archive/API** ([LV portāls](https://lvportals.lv/dienaskartiba/378055-latvija-ieviesta-sunu-apraide-jauns-riks-agrinas-bridinasanas-sistema-iedzivotaju-drosibai-2025), [LSM](https://www.lsm.lv/raksts/zinas/latvija/11.07.2025-sunu-apraide-tehniski-strada-kapec-dala-iedzivotaju-pazinojumus-nesanema.a606484/)). Use Meteoalarm/LVĢMC for the weather part. ❌ |
| 112.lv / 112 app | Shelters (already used), guidance | Shelters only |
| sargs.lv "72 stundas" / MoD crisis booklet | Citizen guidance text | Link from the residents' 72h guide; no data |
| Ogre POIC (24/7 municipal operational info centre, set up after the Aug 2026 storm) | Announced ([LV portāls](https://lvportals.lv/dienaskartiba/393721-pec-vetras-ogres-novada-pasvaldiba-uzsak-diennakts-pasvaldibas-operativas-informacijas-centra-izveidi-2026)) | **Natural owner of the manual crisis layers** in §12 |

Context: the 2026-08-22 storm (>30 m/s) left **~277,000 customers without power** at the peak. AST published the affected substations (Preiļi, Barkava, Viļāni, Birži), and Sadales tīkls ran a live outage map ([LV portāls](https://lvportals.lv/dienaskartiba/393537-vetras-del-fikseti-elektroapgades-traucejumi-parvades-tikla-aktuala-situacija-plkst-20-00-2026)). This is a strong demo scenario.

---

## 12. Gaps and how to fill them

OSM counts for "Ogres novads" come from an Overpass query run today.

| Gap (no open authoritative data) | Crisis | Fill with | OSM coverage in Ogres novads |
|---|---|---|---|
| Fuel stations (and which have backup generators / priority supply) | blackout, fuel shortage, war | OSM `amenity=fuel`, plus a municipal flag `backup_power=yes`, plus a crowd-sourced "open now" status | 19 |
| ATMs / bank branches working offline | blackout, cyberattack | OSM `amenity=atm|bank` | 17 ATMs |
| Grocery stores (food supply) | shortage, war | OSM `shop=supermarket|convenience` + PVD register (address) | 55 |
| Electrical substations (risk nodes) | blackout | OSM `power=substation` (sensitive: aggregate/hide in public view) | 151 |
| Water towers, pumping stations, wastewater plants (+ backup power) | water failure | OSM `man_made=water_tower|water_works|pumping_station|wastewater_plant` + utility (Ogres Namsaimnieks) manual entry | 54 |
| Telecom masts / coverage | telecom failure, war | OSM `tower:type=communication` (61). Coverage maps are not open; operators (LMT/Tele2/Bite) on request | 61 |
| Road bridges (critical crossings over the Ogre and Daugava) | infrastructure failure, war | OSM `bridge=yes` + LVC bridge tonnage (in avoti) | 211 ways |
| Pharmacies | pandemic | ZVA (✅ official) > OSM (23) | 23 |
| **Heating / warming points, charging points, drinking-water distribution points, info points, assembly points, field kitchens** | blackout in winter, heat failure, war | **Municipal manual layer** (CA commission / POIC), seeded from candidates: culture centres + schools (KISC/VIIS) with generator flag. Publish as CKAN dataset like Riga `caoip_*` | n/a |
| Generator inventory, critical facilities with backup power (hospital, water, boilers) | blackout | Manual / restricted layer for the commission only (not public) | n/a |
| NMPD ambulance stations | all | OSM `emergency=ambulance_station` + NMPD request | — |
| Gas network / outages, district-heating networks, AST outage feed | infra failure | Request a data-sharing agreement (Gaso, Conexus, AST, Ogres Namsaimnieks); until then, manual incident pins | — |
| Vulnerable individuals register | all | Keep at aggregate level (CSP grid + LM providers). Individual lists stay with the social service | — |
| Live road blockages from fallen trees (municipal roads) | storm | LVC DATEX covers state roads only. Add a crowd-sourced / municipal report layer (photo + point) | — |

## 13. Fastest wins for the hackathon (all ✅ today, CC0, coordinates or VZD code)

1. Sadales tīkls live outages JSON, giving a **blackout heatmap** (respect ToS, cache every 5–10 min).
2. LVĢMC warnings CSV with polygons (or Meteoalarm CAP), giving the **active warning overlay**.
3. VUGD depots + VP stations + medical institutions + ZVA pharmacies, giving the **services layer**.
4. LM social-provider register, joined to VARIS, giving **vulnerable-sites layer** (care homes first).
5. KISC culture centres + IZM schools, giving **candidate warming / info points** (the commission confirms them).
6. ATD/Vivi GTFS stops, giving **evacuation pick-up points**.
7. Seveso + EU Industrial Sites, buffered, giving **chemical hazard zones**.
8. CSP 100 m dwelling grid (`HEAT_DW`, building age), giving **heating-failure exposure**.
