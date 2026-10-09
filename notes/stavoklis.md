# Stāvoklis 2026-10-10 01:01 (handoff between sessions and machines)

Status for whoever picks up next (a new Claude session, a teammate, another PC). Update this file whenever the merge state changes. Tasks live in `TODO.md`; this file is the snapshot.

## Nothing open

All of tonight's PRs (#31–#41) are merged into `main` and live on https://map.repo.lv. No open PRs and no unmerged work branches.

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

## Still to do on the VPS (user runs these; SSH as root)

```bash
ssh root@161.97.105.130
# 1. remove the integration-test leftovers (test API, test DB, files)
pkill -f "[m]ap_test-src/src/karte/api/karte_api.py"
sudo -u postgres dropdb map_test
rm -rf /tmp/map_test-src /tmp/map_test-api.log
sudo -u postgres psql -Atc "select datname from pg_database"   # map_test gone; map and aimr_main untouched
# 2. the API restart watcher now also watches udens_limenis.py
cp /srv/hakatons/src/karte/serveris/hakatons-map-api-restart.path /etc/systemd/system/
systemctl daemon-reload && systemctl restart hakatons-map-api-restart.path
```

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
