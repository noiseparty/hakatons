# Stāvoklis 2026-10-10 02:09 (handoff between sessions and machines)

Status for whoever picks up next (a new Claude session, a teammate, another PC). Update this file whenever the merge state changes. Tasks live in `TODO.md`; this file is the snapshot.

## Open and in progress (batch 2)

| PR / branch | Terminal | What | State |
|---|---|---|---|
| #48 `noiseparty/zonas` | A | Flood zones as real areas with borders, warning areas, hatched overlap "paaugstināts risks"; centred warnings banner | review fixes + `git merge main` |
| #53 `noiseparty/demo` | D | "Demo" panel: 7 simulated scenarios with `?demo=<kods>` deep links, "SIMULĀCIJA" badge, "Beigt demo" | `git merge main` |
| #55 `noiseparty/statuss-2` | C | Status page round 2: forecast, FMI lightning, Open-Meteo, LVC roads rows; grey "Nav datu" state; review follow-ups | in review |
| `noiseparty/avoti-panelis` | B | "Datu avoti" panel complete (forecast, FMI, Open-Meteo, LVC) + accessibility pass | in progress, no PR yet |
| `noiseparty/apaksa` | E | Mobile: result card as a bottom sheet over the map | in progress, no PR yet |

Demo codes (from `production/demo/scenariji.json` on `origin/noiseparty/demo`): `vejs`, `vetra`, `drons`, `nakts`, `pludi-ogre`, `vetra-2026`, `bez-sakariem`. Link: `https://map.repo.lv/?demo=pludi-ogre` (optional `&regions=<kods>`).

## Merged tonight (batch 2)

| PR | What |
|---|---|
| #43 | stavoklis: batch 2 plan, VPS cleanup done |
| #44 | Public status page https://map.repo.lv/statuss.html + `GET /api/statuss` (checker thread in the API, table `statuss_parbaudes`) |
| #45 | "Biežāk meklētais" under the empty search field + query/click counting (`POST /api/meklejumi`, `GET /api/meklejumi/top`) |
| #46 | "Prognoze / ziņas" feed: LVĢMC place forecasts per novads (3 days) + active warnings, `GET /api/prognozes`, `/api/prognozes/robezas` |
| #47 | Multi-session rules in CLAUDE.md (owner self-merges on the user's word) + `TODO.md merge=union` |
| #49 | Research note `notes/research/05_avoti_parbaude_2026-10-10.md` (geolatvija, NAP, traffic APIs, lightning, senotajs, organisers) |
| #50 | Lightning layer (FMI, last 30 min, CC BY 4.0; LVĢMC 24 h grid, CC0) + "Nokrišņi un augsne" line (Open-Meteo, CC BY 4.0); `GET /api/zibens`, `/api/augsne` |
| #51 | Road closures / accidents / works / slippery road layer + "Ceļu satiksme" line (LVC DATEX II via NAP, CC0); `GET /api/celi` |
| #52 | Pitch rewrite (`notes/pitch.md`): search-first demo, geolatvija 1.0 → 2.0 slide, criteria 3 and 5 |
| #54 | "Kas notiks tālāk" block in the result card; all scenario advice in the "Jūs" form |

Batch 1 (#31–#42, night of 2026-10-09/10) is merged too.

## Verified live (2026-10-10 ~02:00)

- `/api/prognozes` 200 (~4 s, 44 KB, warning first); `/api/statuss` 200 and statuss.html renders.
- `/api/zibens` 200 (0 strikes); `/api/augsne` for Ogre: 56.7 mm in 26 days, "ļoti mitra".
- `/api/celi` → `konfigurets: false` (no NAP keys yet, see VPS steps).
- `/api/meklejumi/top` → 503 until the schema is applied (see VPS steps); the dropdown shows built-in examples meanwhile.
- 125 scenarios, each with "Kas notiks tālāk"; 0 "tu" forms left in the advice.

## What's live

**Front door:** the "Kas Jums vajadzīgs?" search in the header (LV/RU/EN free text, 125 scenarios, no AI in the product). One query gives one result card, in this order:
- LVĢMC warnings for the place;
- the decision (e.g. flood zone yes/no at the address);
- facts: nearest river gauge with level + 24 h change, rain and soil (Open-Meteo), road events within ~5 km (once NAP keys are set);
- nearest places with route links and source + licence: assembly point and temporary accommodation (CA plan page link), shelter, 24/7 hospital, pharmacy;
- the scenario's advice and "Kas notiks tālāk".

An address in the query sets the reference point (e.g. "plūdi Mednieku iela 9 Ogre"). Life-threat queries show a red text line "zvaniet 112". No tel: buttons or links anywhere.

**Everywhere:** LVĢMC warnings banner; "⛅ Prognoze" feed button (bottom sheet on phones); "Biežāk meklētais" on the empty search field. Basemap OSM / OpenTopoMap "Reljefs". Link in "Datu avoti": "Vai avoti darbojas?" → statuss.html.

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

Live overlays without the DB: flood risk zones (LVĢMC WMS), lightning (FMI + LVĢMC grid), road events (LVC, empty until keys), forecast regions and warning areas (LVĢMC). Plus 117 regions/cities and 550 685 addresses from VZD (CC BY 4.0).

**API** (`src/karte/api/karte_api.py`): `/api/objekti`, `/api/kategorijas`, `/api/regioni`, `/api/avoti`, `/api/adreses`, `/api/bridinajumi`, `/api/pludi`, `/api/udens`, `/api/prognozes`, `/api/prognozes/robezas`, `/api/zibens`, `/api/augsne`, `/api/celi`, `/api/meklejumi` (POST), `/api/meklejumi/top`, `/api/statuss`, `/api/veseliba`.

**Pitch:** `notes/pitch.md` (10-min script, demo path, judge Q&A) and `notes/presentation_ideas.md` (verified Jūrmala error: assembly point #10 Melluži at 56.064 instead of 56.964, ~100 km off, in Lithuania). CA-plan quality report with the 41 coordinate errors: `notes/ca-plani-kvalitate.md`.

## VPS steps for the user (SSH as root; a Claude session can't write to the VPS)

```bash
ssh root@161.97.105.130
cd /srv/hakatons && set -a && . /etc/hakatons/map.env && set +a
# 1. schema: meklejumi table (#45), LVC avoti row (#51), statuss constraint with nav_datu (#55, after merge)
psql "$MAP_DB_OWNER_DSN" -q -v ON_ERROR_STOP=1 -f src/karte/db/shema.sql
curl -s https://map.repo.lv/api/meklejumi/top     # 200 instead of 503
```

2. **NAP keys for the road layer.**
   1. Register at transportdata.gov.lv as "DATU ŅĒMĒJS".
   2. Press ABONĒT on the 5 datasets: closures, accidents, lane closures, road works, slippery road. Card IDs are in `NAP_KOPAS` in `karte_api.py`.
   3. Add `NAP_API_KEY_SLEGUMI`, `NAP_API_KEY_NEGADIJUMI`, `NAP_API_KEY_JOSLAS`, `NAP_API_KEY_REMONTI` and `NAP_API_KEY_SLIDENS` to `/etc/hakatons/map.env`.
   4. Run `systemctl restart hakatons-map-api`.
   5. Check `curl -s https://map.repo.lv/api/celi | head -c 200`, which should show `"konfigurets":true`. The status page row "Ceļu slēgumi" turns from grey to green.

`shema.sql` is **not** applied automatically (`hakatons-udens.path` only runs it when the water-level category is missing). The statuss table creates and migrates itself from the API.

## Known gaps

- **No real-phone test yet** (only Playwright at 375 px).
- **Flood WMS upstream** (LVĢMC geo-dpps) answers in 1–30 s. The status page often shows it yellow ("atbild lēni"). Warm the demo addresses right before the pitch.
- **Road layer empty** until the NAP keys are set; the parser is tested only against a hand-written DATEX II fixture.
- **"Biežāk meklētais"** shows built-in examples until the schema step runs.
- **"Datu avoti" panel** doesn't list the forecast, FMI and Open-Meteo yet (B is on it); each popup/line shows its own source and licence.
- **Unpublished lists:** 12 municipalities don't publish their assembly-point/accommodation lists. When the nearest point is >10 km away, the result says it's in another municipality.
- **Shelters licence:** 112.lv shelters have no open licence (⚠ in the UI).
- **River-level danger thresholds** (PRIS) need LVĢMC permission, so we show level and trend only.

## Before judging (morning checklist; details in `notes/ritdiena.md`)

- **Freeze `main` 1 h before the pitch:** every merge is live within ~1 min.
- Warm `/api/prognozes` (open the map once), `/api/pludi` for Ogre ("plūdi Mednieku iela 9 Ogre") and the Jūrmala address; open the zones layer on Ogre.
- statuss.html: everything green or explained (flood yellow = slow, roads grey = no keys).
- Two real phones (Android + iPhone), location allowed AND denied.
- Demo deep links `?demo=<kods>` (codes above) tested on a phone.
- Backup screen video + screenshots in the slides.

## How we work (parallel sessions)

Rules are in CLAUDE.md "Multi-session" (#47). Summary:
- **One git worktree per session**, branch from `origin/main`:
  ```bash
  git fetch
  git worktree add ../hakatons-<topic> -b noiseparty/<topic> origin/main
  git worktree remove ../hakatons-<topic>   # when merged
  ```
- **The owner merges its own PR** once the user has said so (the user also has an allow rule for `gh pr merge`). Before merging: `git merge main`, re-test, `gh pr merge N --squash --delete-branch`.
- **API/schema PRs** (`karte_api.py`, `shema.sql`) get a ~5 min subagent review from the orchestrator first. Front-end-only PRs are self-checked (Playwright 375×740, no JS errors, no `tel:`, "Jūs").
- **Shared files:** each PR adds its own delimited section in `karte_api.py` / `shema.sql` and says up front which shared lines it touches (`MARSRUTI`, `main()`, `index.html`, `app.js`). `TODO.md` merges with `merge=union` locally.
- `git worktree list` shows what's still checked out on this PC.
