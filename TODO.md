# TODO

Team task log. **Read `README.md` → "Working together" first** (git workflow + format of this file).
`main` is protected — change this file via a branch + PR, never by pushing to `main`.

## Pending
- [ ] Load the team's interest-point datasets into the map DB (how-to: `src/karte/README.md`) — added 2026-10-09 18:11 +03:00 by noiseparty
- [ ] Incidents layer: LVC live road events (closures, ice, accidents) into `objekti` with `derigs_lidz`; needs NAP API key — added 2026-10-09 18:11 +03:00 by noiseparty
- [ ] Pick the problem/user and the 3–6 step flow for our prototype — added 2026-10-09 17:13 +03:00 by noiseparty
- [ ] "Noturības punkti" (resilience points) layer: culture centres/libraries/schools with heat/charging/water/wifi/generator flags + status & `last_updated` — see `notes/research/` — added 2026-10-09 18:36 +03:00 by noiseparty
- [ ] Live power-outage layer from Sadales tīkls JSON (`karte.sadalestikls.lv/lv/atslegumi-elektrotikla/unplanned`), cached; ask ST for permission (no licence) — added 2026-10-09 18:36 +03:00 by noiseparty
- [ ] Live weather/flood warnings banner + polygons (LVĢMC on data.gov.lv / MeteoAlarm Atom feed for Latvia) — added 2026-10-09 18:36 +03:00 by noiseparty
- [ ] Ogre river gauge (LVĢMC live level) vs 22.15 m threshold + flood zones → highlight affected addresses — added 2026-10-09 18:36 +03:00 by noiseparty
- [ ] Load official CC0 layers: VUGD depots, police stations, hydrants/water intakes, ZVA pharmacies (daily), NVD medical institutions — added 2026-10-09 18:36 +03:00 by noiseparty
- [ ] Drinking-water points & boil-water notices layer (OSM + municipal manual entry) — added 2026-10-09 18:36 +03:00 by noiseparty
- [ ] Public info card: LR1 FM frequency, 112, cell broadcast, sirens, 72h checklist — added 2026-10-09 18:36 +03:00 by noiseparty
- [ ] Commission-only layers: social-care providers (LM register), vulnerable-population density (GEOSTAT 1 km), Seveso/hazard sites, HES dams — added 2026-10-09 18:36 +03:00 by noiseparty
- [ ] Status freshness rule: any status older than 6 h (operational) / 24 h (static) shows "unknown" — added 2026-10-09 18:36 +03:00 by noiseparty
- [ ] "Wartime mode": public and restricted data as separate files; drop critical infra/generators, blur outages to ~1 km² — added 2026-10-09 18:36 +03:00 by noiseparty
- [ ] Use the 22–23.08.2026 storm (~277k customers without power) as the demo scenario in the pitch — added 2026-10-09 18:36 +03:00 by noiseparty
- [ ] Verify unconfirmed sources in `notes/research/01`: NATO 2026 requirements, CER sector list, likumi.lv links, resilience-point draft rules — added 2026-10-09 18:36 +03:00 by noiseparty

## In progress

## Done
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
