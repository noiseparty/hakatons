# 01 — Crisis services & critical infrastructure taxonomy for the CA crisis map

**Scope:** Which services and critical-infrastructure layers a city-wide crisis map (Ogres novads first) should show, for which crisis, with which attributes, and for which audience.
**Date:** 2026-10-09 · **Audience:** hackathon team (AI & Open Data 2026)
**Already in `avoti/` (not proposed again here):** 112.lv public shelters (patvertnes), VZD VARIS addresses + NĪVKIS buildings/basements, LVĢMC flood-zone WMS + river levels, LVC road network/DATEX II closures/bridges, CA plan tables 26/27 (19 evacuation assembly points, 11 evacuation accommodation centres), hazardous-cargo rail corridor, administrative boundaries.

---

## 1. Frameworks used (and what each one adds)

| Framework | What it says | What it means for the map | Source |
|---|---|---|---|
| **EU CER Directive 2022/2557** | 11 critical-entity sectors: energy, transport, banking, financial market infrastructure, health, drinking water, waste water, digital infrastructure, public administration, space, food (production/processing/distribution) | A checklist of sectors: every sector should have at least one map layer or status indicator | [EUR-Lex 2022/2557](https://eur-lex.europa.eu/eli/dir/2022/2557/oj) |
| **LV critical infrastructure (CI) rules** | MK Nr. 508 (2021, under the Nacionālās drošības likums) lost force on 16.01.2026. A replacement draft that matches the CER Directive (25-TA-1988) covers CI identification, incident reporting and resilience | CI object lists are **classified/restricted**. Show them only to the commission and never publish them | [likumi.lv 324689](https://likumi.lv/ta/id/324689) · [TAP 25-TA-1988 opinions](https://tapportals.mk.gov.lv/attachments/legal_acts/reviews/additional_documents/38fa6e61-e25a-4e20-b548-9cd05b934051/download) |
| **NATO 7 Baseline Requirements** (2016, raised in 2026) | Continuity of government · energy · uncontrolled population movement · food & water · mass casualties/health · civil communications · civil transport | Gives the top-level grouping of map layers (section 3). It also requires keeping civilian evacuation routes separate from military movement, which is an OPSEC issue | [NATO topic 132722](https://www.nato.int/cps/en/natohq/topics_132722.htm) · [2026 BR brochure](https://nato.int/content/dam/nato/webready/documents/publications-and-reports/20260918_brochure-requirements-resilience2026-en.pdf) |
| **FEMA Community Lifelines** (Toolkit 2.1, 8 lifelines) | Safety & Security · Food, Hydration, Shelter · Health & Medical · Energy · Communications · Transportation · Hazardous Materials · Water Systems | **Status model:** each lifeline gets a green/yellow/red/grey status per area. Use this as the dashboard header | [Cal OES factsheet](https://www.caloes.ca.gov/wp-content/uploads/Recovery/Documents/Community-Lifelines-Factsheet_8_19_24.pdf) · [FEMA BRIC lifelines](https://www.fema.gov/sites/default/files/2020-07/fema_bric_session-4_community-lifelines.pdf) |
| **MK noteikumi Nr. 658** (CA plans, in force since 01.01.2023) + Civilās aizsardzības un katastrofas pārvaldīšanas likums | Municipal CA plans must cover the military-threat section, drinking-water reserves, fuel and heating-fuel reserves, food reserves, mobile energy sources, evacuation and accommodation | These are the layers the plan is **legally required** to hold, so the map should render them | [LV portāls on military-threat plans](https://lvportals.lv/norises/352590-pasvaldibas-izstrada-ricibas-planus-militara-apdraudejuma-gadijuma-2023) · [likumi.lv CA law](https://likumi.lv/ta/id/282333) |
| **LV 72h guidance** "Kā rīkoties krīzes gadījumā" (MoD, 2024 ed.) | Self-sufficiency for 72 h: water, food, medicines, information sources, evacuation, family plan, war | Resident mode should answer: where do I get water, information, heat and charging after 72 h? | [VUGD PDF 2024](https://vugd.gov.lv/lv/media/1351/download) · [sargs.lv](https://www.sargs.lv) |
| **LV "noturības punkti" (resilience points)** — new | After the 23.08.2026 storm (the strongest summer storm since at least 1966), the Cabinet crisis meeting of 24.08.2026 decided that municipalities **must set up resilience points** offering information, drinking water and communications during blackouts. The regulation is still being drafted; the Crisis Management Centre (KVC) was due to submit proposals by 15.09.2026. Fuel stations were suggested as host sites | **This is the most topical new layer for the hackathon pitch** | [LV portāls 26.08.2026 (VARAM)](https://lvportals.lv/dienaskartiba/393702-varam-janovers-trukumi-ko-vetra-atklaja-elektroapgade-sakaros-un-koordinacija-2026) · [LV portāls telecom resilience](https://lvportals.lv/dienaskartiba/394507-tautsaimniecibas-komisija-nepieciesams-steidzams-risinajums-sakaru-noturibai-krizes-2026) · [Līgatne/Cēsis storm review](https://www.ligatne.lv/lv/ligatne/aktualitates/zinas/vetra-ka-parbaudijums-gatavibai-krizes-situacijam/pdf) |
| **LV heat-supply priority users** (draft energy-crisis rules) | Priority users: residential buildings, hospitals, social-care institutions, emergency services, telecom nodes, water and sewerage stations | Defines the "priority consumers" layer for the blackout and heating scenarios | [TAP 24-TA-215 opinions](https://tapportals.mk.gov.lv/attachments/legal_acts/reviews/additional_documents/7ff75bed-200c-4344-be92-db0904b46dbc/download) |
| **Ukraine "Points of Invincibility"** (Пункти незламності) | Provide heat, water, electricity/charging, mobile + Starlink internet, first aid, rest, and supplies for mothers and children. Required kit: generator + fuel + Starlink + heater. The Diia map filters by internet/heating/generator/mobile and supports **offline map download**. Points are **hidden in frontline oblasts** for security reasons | The best reference UX for the resilience-point layer and for OPSEC practice | [Wikipedia](https://en.wikipedia.org/wiki/Points_of_Invincibility) · [Babel: Diia map](https://babel.ua/en/news/99748-a-map-with-invincibility-points-was-added-to-diia) · [ONOVA GIS hub](https://onova.org.ua/en/news/mapa-punktiv-nezlamnosti-na-onova-gis-hub) |
| **Sweden** "Om krisen eller kriget kommer" (MSB, Nov 2024) | Covers sirens + "Viktigt meddelande till allmänheten" on P4 radio, shelters, water, food, cash, evacuation, first aid, and the threat picture (war, cyber, terror, nature) | Map needs: siren coverage, radio frequencies, shelters, cash access | [The Local 2024](https://www.thelocal.se/20241118/sweden-releases-updated-version-of-if-crisis-or-war-comes-booklet) · [msb.se](https://www.msb.se/sv/publikationer/om-krisen-eller-kriget-kommer/) |
| **Finland** 72tuntia.fi (SPEK) | 72 h at home without electricity, heat or water. Covers shelter-in-place (ventilation off), building civil-defence shelters, and reliable info from Yle, the municipality and utilities | Map needs: water-collection points, shelter-in-place zones, utility outage status | [72tuntia.fi/en](https://72tuntia.fi/en) · [EU CP Knowledge Network](https://civil-protection-knowledge-network.europa.eu/media/brochure-citizens-home-preparedness-and-72-hours-self-sufficiency-finland) |
| **Norway** DSB egenberedskap | 3 days of self-reliance if power, mobile and internet fail; 9 L water per person. Police order evacuations; the municipality provides health and social care to evacuees and relatives | Map needs: evacuee/relative reception centre, outage areas | [DSB brochure](https://www.statsforvalteren.no/siteassets/fm-vestland/samfunnstryggleik-og-beredskap/beredskap/eigenberedskap/brosjyrer/dsb-eigenberedskap---brosjyre-nynorsk.pdf) · [Oslo evacuation](https://www.oslo.kommune.no/beredskap-og-egenberedskap/evakuering/) |

**Key lesson from the August 2026 Latvian storm:** the two failures were **prolonged blackouts** and **loss of mobile and internet service when masts ran out of power**. Municipalities lacked one picture of which roads were blocked and where power and communications were down. The proposed fixes are unified municipal crisis information points, alternative communications for municipal leaders, and generators. The map must therefore (a) work **offline** and (b) carry **status**, not only locations.

---

## 2. Crisis types (columns)

| Code | Crisis |
|---|---|
| **ST** | Severe storm / snowstorm / extreme cold or heat |
| **BO** | Prolonged, wide-area power failure (blackout) |
| **UF** | Infrastructure failure: water, heating, telecom, gas, bridge or road collapse |
| **FL** | Flood / ice jam / Daugava HES dam failure |
| **CH** | Chemical or industrial accident, hazardous cargo (rail/road) |
| **WA** | War / military attack (air strikes, drones, shelling) |
| **ML** | Martial law / state of exception (izņēmuma stāvoklis), mobilisation |
| **PA** | Pandemic / epidemic |
| **CY** | Cyberattack (payments, telecom, utilities SCADA) |
| **EV** | Mass evacuation / incoming evacuees (internal or from other regions) |
| **FS** | Fuel shortage / supply-chain disruption |

---

## 3. Service × crisis matrix

Legend: **C** = critical (must be on the map), **U** = useful, **·** = not applicable / low value.
Audience: **P** = public, **R** = restricted to the commission, **P/R** = public point with restricted attributes. ⚠ = OPSEC-sensitive in WA/ML.

### 3.1 Safety, security & warning (NATO BR1 · FEMA Safety & Security)

| Layer | ST | BO | UF | FL | CH | WA | ML | PA | CY | EV | FS | Aud. |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Public shelters / patvertnes *(already in avoti/)* | U | · | · | · | U | **C** | **C** | · | · | U | · | P |
| Shelter-in-place guidance zones (seal windows, ventilation off) | · | · | · | · | **C** | **C** | U | · | · | · | · | P |
| Siren / warning coverage (VUGD sirens, cell-broadcast areas) | U | U | · | **C** | **C** | **C** | **C** | · | U | **C** | · | P (coverage) / R ⚠ (sites) |
| Police, State Police, Municipal Police stations | U | U | U | U | U | U | **C** | · | U | **C** | U | P |
| Fire & rescue (VUGD) depots | U | U | U | U | U | U ⚠ | U | · | · | U | · | P |
| Hazard / exclusion zones (chemical plume, blast radius, cordons) | · | · | U | **C** | **C** | **C** | U | · | · | **C** | · | P |
| Curfew zones, checkpoints, movement restrictions | · | · | · | · | U | **C** | **C** | U | · | **C** | · | P (zones) / R ⚠ (posts) |
| Unexploded ordnance / debris reporting zones | U | · | · | · | · | **C** | U | · | · | · | · | P |
| Seveso / high-hazard sites (paaugstinātas bīstamības objekti) | · | U | U | **C** | **C** | **C** ⚠ | U | · | U | U | · | R (buffer zone P) |

### 3.2 Continuity of government & public information (NATO BR1, BR6 · FEMA Communications)

| Layer | ST | BO | UF | FL | CH | WA | ML | PA | CY | EV | FS | Aud. |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **Resilience points / noturības punkti** (info + water + charging + Wi-Fi + heat; Ukraine-style) | **C** | **C** | **C** | U | · | **C** | **C** | · | **C** | U | U | P |
| Municipal crisis information points (pašvaldības klientu centri, pagastu pārvaldes) | **C** | **C** | **C** | **C** | U | **C** | **C** | U | **C** | **C** | U | P |
| Crisis commission / operations centre (KVC) | U | U | U | U | U | U ⚠ | U ⚠ | U | U | U | U | R |
| Radio: FM frequencies (LR1 / Latvijas Radio, local) + coverage | **C** | **C** | U | U | **C** | **C** | **C** | · | **C** | U | · | P |
| Public notice boards / printed bulletin points (offline fallback) | U | **C** | U | U | · | **C** | **C** | · | **C** | U | · | P |
| Mobile network outage map (per operator: LMT, Tele2, Bite) | **C** | **C** | **C** | U | · | U | U | · | **C** | · | · | P (area) / R (masts ⚠) |
| Public Wi-Fi / satellite (Starlink) access points | U | **C** | **C** | · | · | **C** | U | · | **C** | U | · | P |

### 3.3 Energy (NATO BR2 · FEMA Energy · CER energy)

| Layer | ST | BO | UF | FL | CH | WA | ML | PA | CY | EV | FS | Aud. |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Power outage areas + estimated restoration time (Sadales tīkls) | **C** | **C** | U | U | · | **C** | U | · | **C** | · | · | P |
| Device charging points (public) | **C** | **C** | U | U | · | **C** | U | · | U | U | · | P |
| Warming centres (cold) / cooling centres (heat) | **C** | **C** | **C** (heating) | U | · | **C** | U | · | U | U | U | P |
| District heating status (Ogres Namsaimnieks / boiler houses) | U | **C** | **C** | U | · | U | · | · | **C** | · | U | P (area) / R (plants ⚠) |
| Gas supply outages (Gaso) | U | U | **C** | U | U | U | · | · | U | · | · | P (area) |
| Priority consumers (hospitals, care homes, water/sewerage pumps, telecom nodes) | **C** | **C** | **C** | U | · | **C** ⚠ | U | U | **C** | · | **C** | R |
| Mobile generator inventory + deployment | **C** | **C** | **C** | U | · | **C** ⚠ | U | · | U | U | **C** | R |
| Substations, transformers, HV lines, HES dams | U | U | U | **C** | · | ⚠ | ⚠ | · | U | · | · | R only (never public) |

### 3.4 Food, water & shelter (NATO BR4 · FEMA Food/Hydration/Shelter, Water Systems)

| Layer | ST | BO | UF | FL | CH | WA | ML | PA | CY | EV | FS | Aud. |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Drinking water distribution points (cisterns, bottled water) | U | **C** | **C** | **C** | **C** | **C** | U | · | U | U | · | P |
| Water supply / boil-water notice areas (Ogres Namsaimnieks) | U | **C** | **C** | **C** | **C** | U | · | · | **C** | · | · | P |
| Public wells / pumps (non-electric water sources) | · | **C** | **C** | U | · | **C** | U | · | U | · | · | P |
| Sewage pumping-station failure areas | U | **C** | **C** | **C** | · | U | · | · | U | · | · | P (area) |
| Evacuation accommodation centres *(table 27, already in avoti/)* | U | U | U | **C** | **C** | **C** | U | · | · | **C** | · | P |
| Evacuation assembly points *(table 26, already in avoti/)* | · | · | · | **C** | **C** | **C** | U | · | · | **C** | · | P |
| Grocery stores open (with backup power / paper payment) | U | **C** | U | U | · | **C** | U | **C** | **C** | U | **C** | P |
| Food / humanitarian aid distribution (Red Cross, municipal social service) | U | U | U | **C** | U | **C** | U | U | U | **C** | U | P |
| Municipal food / water / fuel reserve stores (MK 658) | U | U | U | U | · | ⚠ | ⚠ | U | · | U | **C** | R only |
| Evacuee / relative reception & registration centre | · | · | · | **C** | **C** | **C** | U | · | · | **C** | · | P |

### 3.5 Health & mass casualties (NATO BR5 · FEMA Health & Medical)

| Layer | ST | BO | UF | FL | CH | WA | ML | PA | CY | EV | FS | Aud. |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Hospitals / ER (Ogres slimnīca) + status | **C** | **C** | U | **C** | **C** | **C** | U | **C** | **C** | U | U | P (bed and status details R) |
| GP practices / emergency medical aid (NMPD) points | U | U | U | U | U | U | U | **C** | U | U | · | P |
| Pharmacies on duty / open with backup power | U | **C** | U | U | U | **C** | U | **C** | **C** | U | U | P |
| Dialysis, oxygen-dependent and home-ventilator patients | **C** | **C** | **C** | **C** | U | **C** | U | U | U | **C** | · | R only (personal data, GDPR) |
| Care homes, social-care institutions | **C** | **C** | **C** | **C** | **C** | **C** | U | **C** | U | **C** | U | P (location) / R (residents, needs) |
| Vulnerable people register (mobility-impaired, lone elderly) | **C** | **C** | **C** | **C** | **C** | **C** | U | **C** | · | **C** | · | R only (GDPR) |
| Blood donation points (VADC) | · | · | · | · | U | **C** | U | · | · | · | · | P |
| Vaccination / testing points | · | · | · | · | · | · | · | **C** | · | U | · | P |
| Temporary morgue / mass-fatality site | · | · | · | U | U | **C** | · | U | · | · | · | R |
| Veterinary clinics, animal shelters, pet-friendly shelters | U | U | · | **C** | U | U | · | · | · | **C** | · | P |
| Livestock farms needing generators (milking, ventilation) | U | **C** | U | **C** | U | U | · | · | · | U | U | R |

### 3.6 Transport & population movement (NATO BR3, BR7 · FEMA Transportation)

| Layer | ST | BO | UF | FL | CH | WA | ML | PA | CY | EV | FS | Aud. |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Road closures, fallen trees, ice *(LVC DATEX II in avoti/)* + municipal streets | **C** | U | **C** | **C** | **C** | **C** | **C** | · | · | **C** | U | P |
| Bridge status / load limits *(LVC in avoti/)* | U | · | **C** | **C** | · | **C** ⚠ | U | · | · | **C** | · | P (status) / R (structural detail) |
| Evacuation routes (civilian) | U | · | · | **C** | **C** | **C** | **C** | · | · | **C** | · | P (kept separate from military routes ⚠) |
| Public transport status (bus, rail — Pasažieru vilciens, Ogres autobusi) | U | **C** | U | U | U | U | U | U | U | **C** | **C** | P |
| Evacuation transport pick-up points (for people without cars) | · | · | · | **C** | **C** | **C** | U | · | · | **C** | U | P |
| Fuel stations open, with backup power, purchase limits | U | **C** | · | U | · | **C** | **C** | · | **C** | **C** | **C** | P |
| Military supply routes, staging areas (Host Nation Support) | · | · | · | · | · | ⚠ | ⚠ | · | · | ⚠ | · | **never shown** |

### 3.7 Finance, schools & everyday services (CER banking · FEMA Safety/Food)

| Layer | ST | BO | UF | FL | CH | WA | ML | PA | CY | EV | FS | Aud. |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ATMs / bank branches working (cash access) | U | **C** | U | U | · | **C** | **C** | · | **C** | U | U | P |
| Shops accepting cash / offline payment | U | **C** | · | · | · | **C** | U | · | **C** | · | U | P |
| Post offices (Latvijas Pasts: pensions, benefits) | · | U | · | · | · | U | U | U | U | U | · | P |
| Schools & kindergartens (open/closed, child reunification point) | **C** | **C** | **C** | **C** | **C** | **C** | **C** | **C** | U | U | · | P |
| Social services offices, Red Cross / Samariešu / NGO volunteer points | U | U | U | **C** | U | **C** | U | **C** | U | **C** | · | P |
| Places of worship / community halls used as gathering points | U | U | · | U | · | U | · | · | · | U | · | P |

### 3.8 Hazardous materials, waste & sanitation (FEMA HazMat · CER waste water)

| Layer | ST | BO | UF | FL | CH | WA | ML | PA | CY | EV | FS | Aud. |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Hazmat rail/road corridor buffers *(already in avoti/)* | · | · | U | U | **C** | **C** | · | · | · | U | · | P (buffers) |
| Wastewater treatment plant status / overflow | U | **C** | **C** | **C** | U | U | · | · | U | · | · | P (area) / R (site) |
| Waste collection status, storm-debris drop-off points | **C** | U | U | **C** | · | U | · | U | · | · | U | P |
| Mobile toilets / sanitation points | U | U | **C** | **C** | · | **C** | · | · | · | **C** | · | P |
| Decontamination points | · | · | · | · | **C** | **C** | · | · | · | U | · | P (when active) |

---

## 4. Attributes per layer (minimum data model)

Every point layer shares a **common status core**, with type-specific extras listed below.

**Common core (all layers):**
`id, name, type, address (VARIS code), lat/lon, municipality/parish, status [open | limited | closed | unknown], status_reason, opening_hours, capacity_total, capacity_free, backup_power [none | generator | battery | grid-independent], backup_runtime_h, accessible (wheelchair, step-free), languages, contact (phone/radio), audience [public | restricted], source, last_updated (ISO timestamp), verified_by`

**Rule:** show `last_updated` prominently. If a status has not been refreshed within 6 h (operational) or 24 h (static), set it to "unknown". Never display a stale "open".

| Layer group | Extra attributes |
|---|---|
| Shelters | shelter type (patvertne / basement / protected space), protection level, entrance coordinates, ventilation, water/toilet on site, key holder (R) |
| Resilience points / warming centres / charging | services flags: `heat, charging, wifi, satellite, drinking_water, hot_food, first_aid, toilets, child_corner, pets_allowed`; generator fuel autonomy (h); sockets count |
| Water distribution | water source (cistern/bottled/well), potable Y/N, litres available, container required Y/N, schedule |
| Outage areas (power / water / heat / telecom / gas) | polygon, operator, affected customers, cause, estimated restoration time (ETR), priority-restoration flag |
| Hospitals / pharmacies | ER open Y/N, backup power, free beds (R), surge capacity (R), specialties, on-duty schedule, prescription service available |
| Fuel / ATMs / shops | fuel types, purchase limit, payment methods (cash/card/offline), queue estimate, cash available |
| Schools / care homes | open/closed, students/residents count (R), evacuation status, reunification point |
| Evacuation centres / assembly points | beds, meals per day, free capacity, medical staff present, transport pick-up time, registration desk |
| Roads / bridges | closure type (full/lane/weight), reason, alternative route, expected reopening, max load |
| Vulnerable people (R only) | dependency type (dialysis/oxygen/ventilator/mobility/lone), backup power at home, assigned responder, check status: `contacted / visited / evacuated` |

---

## 5. Public vs restricted layers — OPSEC rules for war and martial law

**Principle (from Ukraine 2022–2026 practice):** publish **where people can get help**. Never publish **what the adversary could target** or **what reveals defensive capability or damage effects**. Diia hides even the Points of Invincibility in frontline oblasts. The SBU prosecutes real-time posting of strike locations and air-defence activity (Criminal Code Art. 114-2), has asked owners to switch off street webcams, and regional commands have recommended a 3 h delay before publishing strike aftermath ([SBU on webcams](https://ssu.gov.ua/en/novyny/sbu-zaklykaie-vlasnykiv-vulychnykh-vebkamer-vymknuty-onlaintransliatsiiu-shchob-ne-dopomahaty-rf-navodyty-rakety-na-ukrainu), [Mediacenter: 3h rule](https://mediacenter.org.ua/photos-and-videos-from-the-sites-of-attacks-on-civilian-targets-can-be-made-public-at-least-three-hours-later-military-commandment/), [UNN: SBU appeal](https://unn.ua/en/news/the-sbu-urges-ukrainians-not-to-publish-photos-and-videos-of-enemy-shelling)).

### Public (resident mode)
Shelters, resilience/warming/charging points, water distribution, evacuation assembly points and accommodation centres, open pharmacies/shops/fuel/ATMs, hospitals (open/closed only), schools (open/closed), outage **areas** (coarse polygons), road closures, radio frequencies, hazard and shelter-in-place zones, curfew **zones**, aid distribution, vet and pet shelters.

### Restricted (commission mode, authenticated, not in public offline bundle)
Vulnerable-person register (GDPR), care-home resident counts, hospital bed and surge capacity, generator inventory, municipal reserve stores (food/fuel/water), priority-consumer list, Seveso site details, key holders, commission location, staff rosters, stocks.

### Never publish (WA/ML), and keep out of the app entirely unless an accredited system is used
- Critical-infrastructure object lists (MK 508 successor). These are restricted by law.
- Substations, transformers, HV line routes, water intakes, pumping stations, boiler plants, telecom masts as **exact points**. Publish only effect polygons.
- **Damage/strike locations in real time**, and photos of impact sites. Apply a delay and coarsening policy.
- Military, Home Guard (Zemessardze) and NBS positions, staging areas, supply routes, checkpoints as points, and air-defence assets.
- Locations of the crisis commission, KVC and alternative command posts.
- Fuel and food reserve depots.
- Live counts of people inside shelters or evacuation centres. Show a coarse "space available" indicator only.

**Design consequences:**
1. Run two separate data products (public GeoJSON vs restricted API). Never hide restricted data with CSS/JS filters, because client-side hiding leaks.
2. Use a **"wartime mode" toggle** that automatically strips or coarsens sensitive layers, mirroring how Diia hides frontline regions.
3. Generalise outage and damage polygons to a grid (e.g. 1 km² or parish).
4. Keep an audit log on restricted layers.

---

## 6. Prioritised MVP layer list (beyond what is already in avoti/)

| # | Layer | Why first | Likely data source (to research in 02) |
|---|---|---|---|
| 1 | **Resilience points / noturības punkti** (+ warming and charging) | National decision of 24.08.2026, regulation pending. This is the strongest pitch | Municipality (manual entry form), fuel stations |
| 2 | Power / telecom outage areas + ETR | The #1 failure in the August 2026 storm | Sadales tīkls outage map, operators |
| 3 | Drinking-water points + water/heat outage areas | MK 658 reserves, 72 h guidance | Ogres Namsaimnieks, municipality |
| 4 | Hospitals, pharmacies on duty, care homes | Mass casualties, vulnerable people | NVD/SPKC registers, Zāļu valsts aģentūra pharmacy register |
| 5 | Fuel stations, ATMs, open shops with backup power | Blackout, cyber, fuel shortage | OSM, bank/fuel-company locators, crowd-reported status |
| 6 | Schools / kindergartens + reunification points | Every scenario | VIIS / municipality |
| 7 | Radio frequencies + siren coverage | Warning when mobile networks are down | LVRTC, VUGD |
| 8 | Vulnerable-people register (restricted) | Commission's top operational need | Municipal social service |

---

### Sources (primary first)
- EU CER Directive 2022/2557 — https://eur-lex.europa.eu/eli/dir/2022/2557/oj
- MK Nr. 508 (CI, lost force 16.01.2026) — https://likumi.lv/ta/id/324689 · successor draft 25-TA-1988 — https://tapportals.mk.gov.lv
- NATO resilience & 7 BRs — https://www.nato.int/cps/en/natohq/topics_132722.htm · 2026 brochure — https://nato.int/content/dam/nato/webready/documents/publications-and-reports/20260918_brochure-requirements-resilience2026-en.pdf · CIMIC handbook — https://www.cimic-coe.org/handbook-entries/welcome-to-the-cimic-handbook/vii-resilience/7-2-seven-baseline-requirements/
- FEMA Community Lifelines — https://www.caloes.ca.gov/wp-content/uploads/Recovery/Documents/Community-Lifelines-Factsheet_8_19_24.pdf
- LV 72h booklet 2024 — https://vugd.gov.lv/lv/media/1351/download
- LV storm Aug 2026 / resilience points — https://lvportals.lv/dienaskartiba/393702-varam-janovers-trukumi-ko-vetra-atklaja-elektroapgade-sakaros-un-koordinacija-2026 · https://lvportals.lv/dienaskartiba/394507-tautsaimniecibas-komisija-nepieciesams-steidzams-risinajums-sakaru-noturibai-krizes-2026 · https://www.ligatne.lv/lv/ligatne/aktualitates/zinas/vetra-ka-parbaudijums-gatavibai-krizes-situacijam/pdf
- LV municipal military-threat CA plan sections (MK 658) — https://lvportals.lv/norises/352590-pasvaldibas-izstrada-ricibas-planus-militara-apdraudejuma-gadijuma-2023
- LV state of exception law "Par ārkārtējo situāciju un izņēmuma stāvokli" — https://likumi.lv/ta/id/255948 (verify current version)
- Ukraine Points of Invincibility — https://en.wikipedia.org/wiki/Points_of_Invincibility · https://babel.ua/en/news/99748-a-map-with-invincibility-points-was-added-to-diia
- Sweden MSB brochure — https://www.msb.se/sv/publikationer/om-krisen-eller-kriget-kommer/
- Finland 72tuntia — https://72tuntia.fi/en
- Norway DSB — https://www.statsforvalteren.no/siteassets/fm-vestland/samfunnstryggleik-og-beredskap/beredskap/eigenberedskap/brosjyrer/dsb-eigenberedskap---brosjyre-nynorsk.pdf

**Caveats:** The full text of the 2026 NATO BRs was not retrieved. The resilience-point regulation was still a draft as of the last sources (Aug–Sep 2026). The CER sector list and the likumi.lv IDs for the CA law and the state-of-exception law were cited from memory and should be verified.
