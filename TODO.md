# TODO

Team task log. **Read `README.md` → "Working together" first** (git workflow + format of this file).
`main` is protected — change this file via a branch + PR, never by pushing to `main`.

## Pending
- [ ] Load the team's interest-point datasets into the map DB (how-to: `src/karte/README.md`) — added 2026-10-09 18:11 +03:00 by noiseparty
- [ ] Incidents layer: LVC live road events (closures, ice, accidents) into `objekti` with `derigs_lidz`; needs NAP API key — added 2026-10-09 18:11 +03:00 by noiseparty
- [ ] Pick the problem/user and the 3–6 step flow for our prototype — added 2026-10-09 17:13 +03:00 by noiseparty

## In progress

## Done
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
