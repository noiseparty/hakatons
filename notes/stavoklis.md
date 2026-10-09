# Stāvoklis 2026-10-10 (handoff between sessions and machines)

Status for whoever picks up next (a new Claude session, a teammate, another PC). Update this file whenever the merge state changes. Tasks live in `TODO.md`; this file is the snapshot.

## In progress: batch 2 (started 2026-10-10 morning, orchestrator + terminals A–E)

VPS cleanup from batch 1 is done (map_test dropped, restart watcher updated). Five branches, one per terminal, merge order **B → C → E → A → D** (B, C, E all add delimited sections to `karte_api.py` / `shema.sql`; A and D add hooks to `app.js`). Each PR says what was tested and lists VPS steps; the coordinator merges only after the user's OK, without `--delete-branch`.

| Terminal | Branch | What | Own files |
|---|---|---|---|
| A | `noiseparty/zonas` | Warnings banner collapses left on desktop when expanded → fix. Flood-risk zones render as dots → real polygons with borders; new `zonas.js` registry, overlapping zones = "paaugstināts risks" | `bridinajumi.js`, `zonas.js`, `stils.css`, flood section of `app.js` |
| B | `noiseparty/popularie` | Click on the empty search bar → "Biežāk meklētais": top 3 queries by popularity; table `meklejumi`, `POST /api/meklejumi`, `GET /api/meklejumi/top`, seeded demo queries | `meklesana.js`, API + schema section |
| C | `noiseparty/statuss` | Public status page `statuss.html`: site, API/DB, VZD, LVĢMC warnings, flood WMS, water levels (stale >6 h), CA points, shelters, OSM tiles; 15-min uptime bars for 24 h, 7-day %; `GET /api/statuss`, table `statuss_parbaudes`, in-process checker | `statuss.html/js`, API + schema section, link in `avoti.js` |
| D | `noiseparty/demo` | Right-side hideable "Demo" sidebar with simulated scenarios (yellow wind, red storm, drone no-go zone + shelter, night cut hand → 24/7 ER, Ogre flood → ground ≥15 m from open DEM, 2026-08-22/23 storm replay, phone + grid down for a region); "SIMULĀCIJA" badge, "Beigt demo"; report `notes/demo-scenariji.md` on missing data | `demo.js`, `demo.css`, `demo/scenariji.json`, tiny hooks |
| E | `noiseparty/lvgmc` | Phase 1: research of LVĢMC + other official open data → `notes/research/04_lvgmc_un_oficialie_dati.md`. Phase 2: "Prognoze / ziņas" feed (today/tomorrow per region from LVĢMC forecasts + warnings, regions highlighted), `GET /api/prognozes` | `prognozes.js`, API section |

Still queued (user's wording, not yet assigned): more zone types for the overlap logic; whatever the user adds next.

## Batch 1 (night of 2026-10-09/10): all merged

PRs #31–#42 are merged into `main` and live on https://map.repo.lv.

## What's live

**Front door:** the "Ko tev vajag?" search in the header (LV/RU/EN free text, 119 scenarios, no AI in the product). One query gives one result card:
- the scenario's advice;
- the nearest evacuation assembly point and temporary accommodation (with capacity and a link to the CA plan page);
- the nearest shelter and 24/7 hospital;
- for flood queries, flood zone yes/no at the place and the nearest river level;
- an address or place in the query sets the reference point (e.g. "plūdi Mednieku iela 9 Ogre").

The 4-step flow (#36) was replaced by this at the user's request (#38). There are no 112 buttons: life-threat queries show a red text line "zvaniet 112".

**Everywhere:** LVĢMC warnings banner at the top. Basemap OSM / OpenTopoMap "Reljefs" (no Esri). The filter panel is closed by default on phones, and load errors show a message bar.

**Map layers (live DB `map`):**

| Layer | Objects | Source |
|---|---:|---|
| `patvertne` | 778 | VUGD / 112.lv (⚠ no open licence) |
| `evakuacijas_punkts` | 730 | municipal CA plans (29 municipalities), plan + page per point |
| `izmitinasana` | 579 (104 213 places) | municipal CA plans |
| `neatliekama_24h` | 37 | VM disaster medicine plan, annex 12 |
| `slimnica` | 69 | IeM IC (CC0) |
| `aptieka` | 814 | ZVA (CC0) |
| `policija` | 55 | IeM IC (CC0) |
| `ugunsdzeseji` | 87 | IeM IC (CC0) |
| `bankomats` / `degviela` | 802 / 588 | OpenStreetMap (ODbL) |
| `udens_limenis` | 74 | LVĢMC (CC0), hourly via `hakatons-udens.timer` |

Plus a flood risk zones toggle (LVĢMC WMS), and 117 regions/cities and 550 685 addresses from VZD (CC BY 4.0).

**API** (`src/karte/api/karte_api.py`): `/api/objekti`, `/api/kategorijas`, `/api/regioni`, `/api/avoti`, `/api/adreses`, `/api/bridinajumi`, `/api/pludi`, `/api/udens`, `/api/veseliba`.

**Pitch:** `notes/pitch.md` (10-min script, demo path, judge Q&A) and `notes/presentation_ideas.md`. The latter has the verified Jūrmala error: assembly point #10 Melluži is at 56.064 instead of 56.964 in the official plan, ~100 km off, in Lithuania (checked against the original PDF by sha256 and against VZD). CA-plan quality report with the 41 coordinate errors: `notes/ca-plani-kvalitate.md`.

## VPS

Batch-1 VPS steps are done (2026-10-10 morning): test DB/API removed, `hakatons-map-api-restart.path` re-copied and active. New VPS steps come from the batch-2 PR descriptions.

Writing to the live server from a Claude session is blocked by the permission classifier ("production deploy"). Read-only SSH checks work. So the user runs these steps, or approves them explicitly.

## Known gaps

- **No real-phone test yet** of the search-first UI (only Playwright at 375 px). This is the top task for the morning.
- **No "Kas notiks tālāk" block** in the result card yet (judging criterion 3: a clear ending with what happens next).
- **Scenario advice** in `production/scenariji.json` still uses the "tu" form; the UI texts use "Jūs".
- **Flood WMS upstream** (LVĢMC geo-dpps) answers in 1–30 s. It's cached server-side for ~10 min after the first hit, so warm the demo addresses ("Ogre, plūdi", the Jūrmala address) right before the pitch.
- **Unpublished lists:** 12 municipalities don't publish their assembly-point/accommodation lists. When the nearest point is more than 10 km away, the result says it's in another municipality.
- **Shelters licence:** the 112.lv shelters data has no open licence (shown with ⚠ in the UI).
- **River-level danger thresholds** (PRIS) need LVĢMC permission, so the popup shows the level and trend but not "dangerous"/"normal".

## Before judging (Oct 10)

- **Freeze `main` an hour before the pitch:** every merge is live within ~1 min.
- Test the demo path on two real phones, with location allowed AND denied.
- Record a backup screen video and put screenshots in the slides.
- Check `/api/veseliba`, address search, the warnings banner and the water level just before going on stage.

## How we work (parallel sessions)

- **One git worktree per session.** Never run two sessions in the same folder: a branch switch in one changes files under the other.
  ```bash
  git fetch
  git worktree add ../hakatons-<topic> -b noiseparty/<topic> origin/main
  # when done:
  git worktree remove ../hakatons-<topic>
  ```
- **Split the files:** each session owns its own files, e.g. one owns `production/` + `karte_api.py`, another the data and loaders in `src/karte/`.
- **Additive schema edits:** sessions that both touch `shema.sql` only append their own blocks.
- **`TODO.md` while a stack of PRs is open:** edit it in one consolidated pass after the merges to avoid conflicts.
- **Stacked PRs:** merge strictly in order. After a squash merge, check that the next PR's base moved to `main` (`gh pr edit <n> --base main`).

**Worktrees left on this PC:** `..\hakatons-ca-plani` (#32, merged), `..\hakatons-pitch` (#31, merged), `..\hakatons-ui` (#38, merged) and `..\hakatons-todo` (this PR). All can be removed with `git worktree remove`.
