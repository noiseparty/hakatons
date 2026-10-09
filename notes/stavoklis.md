# Stāvoklis 2026-10-10 00:45 (handoff between sessions and machines)

Written by the orchestrator session. Update this file whenever the merge state changes.

## Live site (main)

map.repo.lv = `main` before PRs #31–#38: map with shelters, official CC0 layers, OSM ATMs/fuel, crisis search (119 scenarios), clustering, region filter. Live DB `map`: 3 230 objects. The Esri satellite basemap is still live until #37 merges.

## Open PRs, merge strictly in this order (all MERGEABLE, nothing merged yet)

| # | What | Base | VPS steps after merge |
|---|---|---|---|
| 33 | Address search (VZD, `/api/adreses`) | main | `psql "$MAP_DB_OWNER_DSN" -f src/karte/db/shema.sql`; `bash src/karte/db/adreses.sh` (the live DB already has `adreses` with 550 685 rows, so quick). Then `curl 'https://map.repo.lv/api/adreses?q=brivibas%2015%20ogre&limit=3'` |
| 34 | LVĢMC water level layer (74 gauges, hourly) + flood scenarios | #33 | `gh pr edit 34 --base main` if GitHub didn't retarget. Units `hakatons-udens.{path,service,timer}` already installed; the .path applies the schema and loads the gauges. Check `systemctl status hakatons-udens.timer`, `journalctl -u hakatons-udens -n 20` |
| 35 | API: `/api/bridinajumi`, `/api/pludi`, `/api/udens` (no DB, cached) | #34 | none; API restarts itself. Check the three curls in the PR |
| 36 | 4-step flow "Mana adrese krīzē" | #35 | none (superseded by #38 but must merge first because #37/#38 stack on it) |
| 37 | Demo-safety fixes: phone panel closed by default, load-error bars, **Esri removed** (OpenTopoMap "Reljefs") | #36 | none |
| 38 | **Search-first UI**: flow removed, no tel:112 anywhere, safe places + flood zone + river level + warnings banner in one result | #37 | none |
| 32 | 730 evacuation assembly points + 579 accommodation sites from CA plans (terminal A) | main | A loads the staged files from /tmp on the VPS once #33's schema is live, then rebases #32 (trivial conflicts in `shema.sql`: keep B's `grant … adreses`, append A's inserts; `TODO.md`: union) |
| 31 | Pitch draft (`notes/pitch.md`, `notes/presentation_ideas.md`) | main | none; any time |

Rule: the user looks at the integration build first, then gives an explicit OK per merge. Every merge is live in ~1 min.

## Known gaps left by the PRs

- Flood WMS upstream (LVĢMC geo-dpps) answers in 1–30 s; cached server-side after the first hit per ~10 m. Warm the demo addresses before the pitch.
- Scenario advice texts in `scenariji.json` are still "tu" form; the new UI texts are "Jūs".
- No real-phone test yet of any of #33–#38. Playwright 375 × 740 only.
- `/api/adreses` SQL tested only on the `map_test` DB (works), not on live yet.
- Evacuation/accommodation points: 12 municipalities don't publish their lists; result shows "citā pašvaldībā" if the nearest is > 10 km.

## Test infrastructure (terminal C's session; tell C to tear it down when done)

- Worktree `C:\Users\ZX202\kodi\hakatons-integracija`, branch `test/integracija` (not pushed) = main + #32–#38.
- http://localhost:8080 serves that build; `/api` goes through an SSH tunnel to a test API on the VPS (127.0.0.1:8921) backed by DB `map_test` (copy of live + all PR data). Live `map` untouched.
- Add a PR to it: `git -C ..\hakatons-integracija merge origin/noiseparty/<branch>`.
- Cleanup: `pkill -f "[m]ap_test-src/src/karte/api"`, `sudo -u postgres dropdb map_test`, `rm -rf /tmp/map_test-src /tmp/map_test-api.log`, stop tunnel + dev server, `git worktree remove ../hakatons-integracija; git branch -D test/integracija`.
- Other worktrees: `..\hakatons-ca-plani` (terminal A, #32), `..\hakatons-ui` (B, clean), `..\hakatons-test` (B, detached, removable).

## Agreements

- Nobody edits `TODO.md` until all merges are done; then one consolidated pass.
- Facts for the pitch verified: Jūrmala assembly point #10 (Melluži) in the official plan is at lat 56.064 instead of 56.964 (one-digit typo, ~100 km, in Lithuania), checked against the original PDF (sha256 matches) and VZD. 41 coordinate errors in total across plans (`notes/ca-plani-kvalitate.md`).
