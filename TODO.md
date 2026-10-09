# TODO

Team task log. **Read `README.md` → "Working together" first** (git workflow + format of this file).
`main` is protected — change this file via a branch + PR, never by pushing to `main`.

## Pending
- [ ] Ask VUGD / IeM IC to publish the national public shelters list on data.gov.lv with an open license (now shown from 112.lv with ⚠ no license) — added 2026-10-09 19:09 +03:00 by noiseparty
- [ ] Find the official publication URL of the VM hospital list PDF (`atseviski_dati/12. pielikums…`; the vp.gov.lv copy is 404) and add it to `avoti` — added 2026-10-09 19:09 +03:00 by noiseparty
- [ ] Esri satellite basemap is LIVE on map.repo.lv (came with the redesign, #18) but Esri imagery is not open data: remove it or replace with an open basemap — added 2026-10-09 20:48 +03:00 by noiseparty
- [ ] Check the license of `atseviski_dati/Kritisko_ATM saraksts_22.09.2026_hakatonam.xlsx` before putting it on the map — added 2026-10-09 20:48 +03:00 by noiseparty
- [ ] Load the team's interest-point datasets into the map DB (how-to: `src/karte/README.md`) — added 2026-10-09 18:11 +03:00 by noiseparty
- [ ] Incidents layer: LVC live road events (closures, ice, accidents) into `objekti` with `derigs_lidz`; needs NAP API key — added 2026-10-09 18:11 +03:00 by noiseparty
- [ ] Pick the problem/user and the 3–6 step flow for our prototype — added 2026-10-09 17:13 +03:00 by noiseparty
- [ ] "Noturības punkti" (resilience points) layer: culture centres/libraries/schools with heat/charging/water/wifi/generator flags + status & `last_updated` — see `notes/research/` — added 2026-10-09 18:36 +03:00 by noiseparty
- [ ] Live power-outage layer from Sadales tīkls JSON (`karte.sadalestikls.lv/lv/atslegumi-elektrotikla/unplanned`), cached; ask ST for permission (no licence) — added 2026-10-09 18:36 +03:00 by noiseparty
- [ ] Live weather/flood warnings banner + polygons (LVĢMC on data.gov.lv / MeteoAlarm Atom feed for Latvia) — added 2026-10-09 18:36 +03:00 by noiseparty
- [ ] Ogre river gauge (LVĢMC live level) vs 22.15 m threshold + flood zones → highlight affected addresses — added 2026-10-09 18:36 +03:00 by noiseparty
- [ ] Remaining official CC0 layers: fire-water intake points (VKCP IĢIS `vkcp-igis-atklatas-udens-nemsanas-vietas`); refresh ZVA + IeM IC data daily (`valsts_dati.py` + `ielade_visu.sh`) — added 2026-10-09 20:48 +03:00 by noiseparty
- [ ] Test the whole map on a real phone (location prompt, dropdowns, list, popups) — added 2026-10-09 20:48 +03:00 by noiseparty
- [ ] Drinking-water points & boil-water notices layer (OSM + municipal manual entry) — added 2026-10-09 18:36 +03:00 by noiseparty
- [ ] Public info card: LR1 FM frequency, 112, cell broadcast, sirens, 72h checklist — added 2026-10-09 18:36 +03:00 by noiseparty
- [ ] Commission-only layers: social-care providers (LM register), vulnerable-population density (GEOSTAT 1 km), Seveso/hazard sites, HES dams — added 2026-10-09 18:36 +03:00 by noiseparty
- [ ] Status freshness rule: any status older than 6 h (operational) / 24 h (static) shows "unknown" — added 2026-10-09 18:36 +03:00 by noiseparty
- [ ] "Wartime mode": public and restricted data as separate files; drop critical infra/generators, blur outages to ~1 km² — added 2026-10-09 18:36 +03:00 by noiseparty
- [ ] Use the 22–23.08.2026 storm (~277k customers without power) as the demo scenario in the pitch — added 2026-10-09 18:36 +03:00 by noiseparty
- [ ] Verify unconfirmed sources in `notes/research/01`: NATO 2026 requirements, CER sector list, likumi.lv links, resilience-point draft rules — added 2026-10-09 18:36 +03:00 by noiseparty
- [ ] Crisis search: test on a real phone, and show "Ko tev vajag?" above the map on mobile (panel is below it now) — added 2026-10-09 19:11 +03:00 by noiseparty
- [ ] Crisis search: use live status once layers have it (skip out-of-service ATMs, closed roads, full shelters) — added 2026-10-09 19:11 +03:00 by noiseparty
- [ ] Crisis search: load the planned layers its scenarios already reference — `noturibas_punkts` (heat/charging/water), `udens_punkts`, `evakuacijas_punkts`, `uzlades_stacija` — added 2026-10-09 20:20 +03:00 by noiseparty
- [ ] Have someone with first-aid / civil-protection background review the advice texts (7 needs + 119 scenarios) in `production/scenariji.json` — added 2026-10-09 20:20 +03:00 by noiseparty
- [ ] Shelter data has duplicates (e.g. Ogre, "Zinību iela 3" twice with different spelling); dedupe on load — added 2026-10-09 19:11 +03:00 by noiseparty

## In progress

## Done
- [x] Official CC0 layers loaded: VUGD depots, VP + municipal police, ZVA pharmacies, IeM IC medical institutions (PR #14) — done 2026-10-09 20:48 +03:00 by noiseparty
- [x] Crisis scenarios: all 119 from `notes/SCENARIJI.md` in the search classifier (own advice, map layers, 112), rare keywords weigh more, "Vai domāji…?" alternatives; #72/#73 not implemented as written (profiling) — done 2026-10-09 20:20 +03:00 by noiseparty (added 2026-10-09 18:46 +03:00 by noiseparty)
- [x] Papildināt scenārijus: aizsalušas caurules, kanalizācija nestrādā, lifts nedarbojas, izsists logs, auto ceļa malā, trauma var/nevar kustēties — `notes/SCENARIJI.md` Nr 113–119, `production/scenariji.json` atslēgvārdi + "nevar kustēt" dzīvības draudos, 6 testi (70/70 ok) — done 2026-10-09 20:15 +03:00 by iesalnieksjanLatvia (added 2026-10-09 20:15 +03:00 by iesalnieksjanLatvia)
- [x] Papildināt scenārijus: troksnis kaimiņš, huligāni uz ielas — `notes/SCENARIJI.md` (Nr 111–112), `production/scenariji.json` policijas atslēgvārdi (troksn/kaimiņ/шум/сосед/nois/neighbor/hooligan) + 4 testi `src/meklesana/testi.json` (64/64 ok) — done 2026-10-09 19:52 +03:00 by iesalnieksjanLatvia (added 2026-10-09 19:52 +03:00 by iesalnieksjanLatvia)
- [x] Izveidot `notes/SCENARIJI.md` — 110 dzīves/katastrofas/krīzes scenāriji ar meklēšanas atslēgvārdiem (pirmais melnraksts krīzes-meklēšanas klasifikatoram) — done 2026-10-09 19:34 +03:00 by iesalnieksjanLatvia (added 2026-10-09 19:34 +03:00 by iesalnieksjanLatvia)
- [x] Crisis search "Ko tev vajag?" without AI: free text (LV/RU/EN) → scenario, 112 prompt, place name → 3 nearest per layer; rules in `production/scenariji.json`, tests in `src/meklesana/` — done 2026-10-09 19:11 +03:00 by noiseparty
- [x] Map data sources: `avoti` table with license/publisher/links, shown in the map (Datu avoti panel, each popup, attribution); pharmacies, hospitals, police, fire stations switched from OSM to official CC0 data (ZVA, IeM IC) — done 2026-10-09 19:09 +03:00 by noiseparty
- [x] Map layer: 37 hospitals with 24/7 emergency care (VM disaster medicine plan, annex 12), addresses checked, coordinates from VZD address register — done 2026-10-09 18:46 +03:00 by noiseparty
- [x] Research crisis-map services & open data (taxonomy, ~55 Latvian sources, intl feeds + case studies, top-15 layers) → `notes/research/` — done 2026-10-09 18:36 +03:00 by noiseparty (added 2026-10-09 18:36 +03:00 by noiseparty)
- [x] Map DB + API + filters: PostGIS db `map` on the VPS, `/api` (`src/karte/`), regions/cities from VZD, OSM ATMs/pharmacies/hospitals/police/fire/fuel, "nearest to me" with geolocation allowed for map.repo.lv — done 2026-10-09 18:11 +03:00 by noiseparty
- [x] Publish OpenStreetMap map of Latvia with 781 public shelters (VUGD / 112.lv) at https://map.repo.lv — done 2026-10-09 17:41 +03:00 by noiseparty
- [x] Add easy mode: one-click setup, update and save for teammates — done 2026-10-09 17:33 +03:00 by noiseparty
- [x] Set up prod deploy to the VPS: `production/` on `main` → https://map.repo.lv, pulled every minute (see `notes/deploy.md`) — done 2026-10-09 17:30 +03:00 by noiseparty (added 2026-10-09 17:20 +03:00 by noiseparty)
- [x] Add AGENTS.md so non-Claude agents (Mistral etc.) pick up the workflow — done 2026-10-09 17:23 +03:00 by noiseparty (added 2026-10-09 17:23 +03:00 by noiseparty)
- [x] Write git workflow + TODO.md rules for all AI agents into README.md — done 2026-10-09 17:21 +03:00 by noiseparty (added 2026-10-09 17:21 +03:00 by noiseparty)
- [x] Protect `main`: PRs required (0 approvals, self-merge OK), no force-push or deletion, applies to admins too — done 2026-10-09 17:20 +03:00 by noiseparty (added 2026-10-09 17:13 +03:00 by noiseparty)
- [x] Add TODO.md and the `todo` skill for tracking tasks — done 2026-10-09 17:13 +03:00 by noiseparty (added 2026-10-09 17:13 +03:00 by noiseparty)
- [x] Add CLAUDE.md and project skills (VDAA guidelines, road DB) — done 2026-10-09 17:00 +03:00 by noiseparty (added 2026-10-09 17:00 +03:00 by noiseparty)
- [x] Invite teammates krissjanis and iesalnieksjanLatvia as collaborators — done 2026-10-09 17:00 +03:00 by noiseparty (added 2026-10-09 17:00 +03:00 by noiseparty)
- [x] Set up team repo and copy hackathon data (lata-org/ai-open-data-2026-hakatons@8371565) — done 2026-10-09 17:00 +03:00 by noiseparty (added 2026-10-09 17:00 +03:00 by noiseparty)
