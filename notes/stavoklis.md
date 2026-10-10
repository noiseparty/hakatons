# Stāvoklis 2026-10-10 02:26 (handoff between sessions and machines)

Status for whoever picks up next (a new Claude session, a teammate, another PC). Update this file whenever the merge state changes. Tasks live in `TODO.md`; this file is the snapshot.

## In progress (no PR yet)

| Branch | Terminal | What |
|---|---|---|
| `noiseparty/satiksmes-zonas` | A | Traffic zones layer in `zonas.js` from `/api/satiksme` (municipality polygons coloured brīvs / lēns / sastrēgums) |
| `noiseparty/satiksme-2` | B | Border waiting-times feed (`ROBEZAS_LAIKS`) + traffic components on the status page |
| `noiseparty/telefoni` | D | Device-matrix test on real phones + backup demo video (`C:\Users\ZX202\kodi\demo-video`) |
| `noiseparty/riski` | E | Risk map for today / tomorrow per region (forecast + warnings + water + soil) |

Demo codes (`production/demo/scenariji.json`): `vejs`, `vetra`, `drons`, `nakts`, `pludi-ogre`, `vetra-2026`, `bez-sakariem`. Link: `https://map.repo.lv/?demo=pludi-ogre` (optional `&regions=<kods>`, e.g. `100003470` = Ogre).

## Merged tonight

| PR | What |
|---|---|
| #43 | stavoklis: batch 2 plan, VPS cleanup done |
| #44 | Public status page https://map.repo.lv/statuss.html + `GET /api/statuss` (checker thread in the API, table `statuss_parbaudes`) |
| #45 | "Biežāk meklētais" under the empty search field + query/click counting (`POST /api/meklejumi`, `GET /api/meklejumi/top`) |
| #46 | "Prognoze / ziņas" feed: LVĢMC place forecasts per novads (3 days) + active warnings, `GET /api/prognozes`, `/api/prognozes/robezas` |
| #47 | Multi-session rules in CLAUDE.md + `TODO.md merge=union` |
| #48 | Flood zones as real areas with borders, LVĢMC warning areas, hatched overlap "paaugstināts risks"; centred warnings banner |
| #49 | Research note `notes/research/05_avoti_parbaude_2026-10-10.md` (geolatvija, NAP, traffic APIs, lightning, senotajs, organisers) |
| #50 | Lightning layer (FMI 30 min, CC BY 4.0; LVĢMC 24 h grid, CC0) + "Nokrišņi un augsne" line (Open-Meteo, CC BY 4.0); `/api/zibens`, `/api/augsne` |
| #51 | Road events layer + "Ceļu satiksme" line (LVC DATEX II via NAP, CC0); `GET /api/celi` |
| #52, #58 | Pitch (`notes/pitch.md`): search-first demo, geolatvija 1.0 → 2.0 slide, criteria 3 and 5; real `?demo=` codes, Ogre high ground ≥23 m, 19 sources |
| #53 | Demo panel: 7 simulated scenarios, `?demo=<kods>`, "SIMULĀCIJA" badge (`notes/demo-scenariji.md`) |
| #54 | "Kas notiks tālāk" block in the result card; all advice in the "Jūs" form |
| #55 | Status page round 2: forecast, FMI lightning, Open-Meteo, LVC roads rows; grey "Nav datu" state |
| #56 | "Datu avoti" panel lists every dataset (19 open + 1 ⚠) with update frequency; accessibility pass, axe-core **0 violations** |
| #57 | stavoklis + ritdiena after batch 2 |
| #59 | Advice texts: sirens → turn on LTV1 / Latvijas Radio (VUGD), LV-ALERT also for weather, spelling LV-ALERT |
| #60 | Mobile: result card as a bottom sheet (`apaksa.js`: peek ≈20 % / half ≈50 % / full ≈92 %), map stays ≥65 % of the screen |
| #61 | `/api/celi` on the real NAP keys + new `GET /api/satiksme` (LVC minute speeds → municipality zones, 77 counter sites, slippery-road stations, border times) |
| #62 | "Svarīgi krīzē" page https://map.repo.lv/info.html: 112, sirens, LV-ALERT levels, LR1 FM frequencies (official list), 72 h checklist, no-network tips; printable |

Batch 1 (#31–#42, night of 2026-10-09/10) is merged too.

## Verified live (2026-10-10 ~02:20)

- `/api/satiksme` 200 in 0.2 s; every feed OK except `robezas` (the border-times feed isn't available yet).
- `/api/celi` returns real events on the user's NAP keys.
- `/api/prognozes` 200 (~4 s, 44 KB, warning first); `/api/statuss` 200 and statuss.html renders.
- `/api/zibens` 200 (0 strikes); `/api/augsne` for Ogre: 56.7 mm in 26 days, "ļoti mitra".
- `/api/meklejumi/top` → 503 until the schema is applied (see VPS step); the dropdown shows built-in examples meanwhile.
- 125 scenarios, each with "Kas notiks tālāk"; 0 "tu" forms in the advice.

**NAP keys on the VPS** (`/etc/hakatons/map.env`): `NAP_API_KEY_NEGADIJUMI`, `NAP_API_KEY_REMONTI`, `NAP_API_KEY_SATIKSME_SLIDENS`, `NAP_API_KEY_UZTURETAJI_SLIDENS`, `NAP_API_KEY_METEO_SLIDENS`, `NAP_API_KEY_SATIKSMES_IEKARTU_MERIJUMI`, `NAP_API_KEY_SATIKSMES_APJOMS_ATRUMS_MIN`, `NAP_API_KEY_ROBEZAS_LAIKS`. Closures and lane closures (`SLEGUMI`, `JOSLAS`) aren't subscribed and are skipped. Which env var maps to which NAP card: `notes/research/nap-satiksme.md`.

## What's live

**Front door:** the "Kas Jums vajadzīgs?" search (LV/RU/EN free text, 125 scenarios, no AI in the product). One query gives one result card. On phones it's a bottom sheet that opens at half: the verdict line first, then one "🧭 Maršruts" button. The card order:
- LVĢMC warnings for the place;
- the decision (e.g. flood zone yes/no at the address);
- facts: nearest river gauge with level + 24 h change, rain and soil (Open-Meteo), road events within ~5 km (LVC);
- nearest places with route links and source + licence: assembly point and temporary accommodation (CA plan page link), shelter, 24/7 hospital, pharmacy;
- the scenario's advice and "Kas notiks tālāk".

An address in the query sets the reference point (e.g. "plūdi Mednieku iela 9 Ogre"). Life-threat queries show a red text line "zvaniet 112". No tel: buttons or links anywhere.

**Everywhere:** LVĢMC warnings banner; "⛅ Prognoze" feed; "Biežāk meklētais"; Demo panel. In "Datu avoti": 19 open + 1 ⚠ sources, links "Vai avoti darbojas?" (statuss.html) and "Svarīgi krīzē" (info.html). Basemap OSM / OpenTopoMap "Reljefs".

**Map layers (live DB `map`):**

| Layer | Objects | Source |
|---|---:|---|
| `patvertne` | 778 | VUGD / 112.lv (⚠ no open licence) |
| `evakuacijas_punkts` | 776 | municipal CA plans (31 municipalities), plan + page per point |
| `izmitinasana` | 579 (104 213 places) | municipal CA plans |
| `neatliekama_24h` | 37 | VM disaster medicine plan, annex 12 |
| `slimnica` | 69 | IeM IC (CC0) |
| `aptieka` | 814 | ZVA (CC0) |
| `policija` | 55 | IeM IC (CC0) |
| `ugunsdzeseji` | 87 | IeM IC (CC0) |
| `bankomats` / `degviela` | 802 / 588 | OpenStreetMap (ODbL) |
| `udens_limenis` | 74 | LVĢMC (CC0), hourly via `hakatons-udens.timer` |

Live overlays without the DB: flood risk zones and warning areas with overlap (LVĢMC), lightning (FMI + LVĢMC grid), road events (LVC), forecast regions (LVĢMC). Traffic zones from `/api/satiksme` are coming with A's layer. Plus 117 regions/cities and 550 685 addresses from VZD (CC BY 4.0).

**API** (`src/karte/api/karte_api.py`): `/api/objekti`, `/api/kategorijas`, `/api/regioni`, `/api/avoti`, `/api/adreses`, `/api/bridinajumi`, `/api/pludi`, `/api/udens`, `/api/prognozes`, `/api/prognozes/robezas`, `/api/zibens`, `/api/augsne`, `/api/celi`, `/api/satiksme`, `/api/meklejumi` (POST), `/api/meklejumi/top`, `/api/statuss`, `/api/veseliba`.

**Pitch:** `notes/pitch.md` and `notes/presentation_ideas.md` (verified Jūrmala error: assembly point #10 Melluži at 56.064 instead of 56.964, ~100 km off, in Lithuania). CA-plan quality report with the 41 coordinate errors: `notes/ca-plani-kvalitate.md`.

## VPS step still pending (the user runs it; SSH as root)

```bash
ssh root@161.97.105.130
cd /srv/hakatons && set -a && . /etc/hakatons/map.env && set +a
psql "$MAP_DB_OWNER_DSN" -q -v ON_ERROR_STOP=1 -f src/karte/db/shema.sql   # meklejumi table (#45), LVC avoti row (#51)
curl -s https://map.repo.lv/api/meklejumi/top     # 200 instead of 503
```

`shema.sql` is **not** applied automatically (`hakatons-udens.path` only runs it when the water-level category is missing). The statuss table creates and migrates itself from the API. NAP keys are done.

## Known gaps

- **Real phones:** D is testing now; until then only Playwright (375×740 emulation). iOS Safari `dvh` + dynamic toolbar and the Android back button with the bottom sheet are the risky parts.
- **Flood WMS upstream** (LVĢMC geo-dpps) answers in 1–30 s; the status page often shows it yellow. Warm the demo addresses right before the pitch.
- **Border waiting times** (`robezas`): the feed doesn't answer yet (B is on it).
- **Traffic free-flow speed** is an estimate (highest speed seen per counter, 80 km/h until 5 readings); speed limits aren't subscribed.
- **Riga public transport live:** no open real-time feed (see `notes/demo-scenariji.md` → "Missing data across scenarios").
- **"Biežāk meklētais"** shows built-in examples until the schema step runs.
- **Unpublished lists:** 10 municipalities don't publish their assembly-point/accommodation lists (Liepāja + Dienvidkurzeme: assembly points found in the official 2026 annex 12).
- **Shelters licence:** 112.lv shelters have no open licence (⚠ in the UI).
- **River-level danger thresholds** (PRIS) need LVĢMC permission, so we show level and trend only.

## Before judging (morning checklist; details in `notes/ritdiena.md`)

- **Freeze `main` 1 h before the pitch:** every merge is live within ~1 min.
- Warm `/api/prognozes` (open the map once), `/api/pludi` for Ogre and the Jūrmala address; open the zones layer on Ogre.
- statuss.html: everything green or explained (flood yellow = slow upstream).
- Two real phones, location allowed AND denied; the 3 pitch deep links (`vetra-2026`, `pludi-ogre`, `nakts`).
- Backup video (D) + screenshots in the slides; print info.html once as a handout.

## How we work (parallel sessions)

Rules are in CLAUDE.md "Multi-session" (#47). Since 2026-10-10 ~02:10 the user's instruction is **no PR reviews**: the owner opens the PR with `origin/main` merged in, sends the orchestrator one line, and the orchestrator merges right away.
- **One git worktree per session**, branch from `origin/main`:
  ```bash
  git fetch
  git worktree add ../hakatons-<topic> -b noiseparty/<topic> origin/main
  git worktree remove ../hakatons-<topic>   # when merged
  ```
- **Shared files:** each PR adds its own delimited section in `karte_api.py` / `shema.sql` and says up front which shared lines it touches (`MARSRUTI`, `main()`, `index.html`, `app.js`). `TODO.md` merges with `merge=union` locally.
- `git worktree list` shows what's still checked out on this PC.
