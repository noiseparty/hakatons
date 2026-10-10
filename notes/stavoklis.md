# Stāvoklis 2026-10-10 06:21 (morning handoff, pitch day)

For the user (noiseparty) after sleeping from ~04:30. Overnight the orchestrator merged **#63–#158** (#111–#158 while you slept); nothing is waiting for review. The site works as it is. The steps below make the live database and server match `main`. Update this file whenever the merge state changes; tasks live in `TODO.md`.

## VPS steps 1–3 (run first, in this order; `src/rits.py` step 7 prints this section)

Log in with `ssh root@161.97.105.130`. Steps 1–3 are the important ones, about 15 minutes in total. Steps 4–9 are in the next section; do them only if there's time. The site works without them.

**1. Daily data refresh.** The timer is not installed (TODO "Rītā" item) or hasn't loaded anything: the live DB still has 730 assembly points (the repo has 776) and lacks the ATM/OSM layers from #110/#118. The units are copied again because #86 changed them. `start` blocks for 5–10 min (Overpass, GTFS). It applies `shema.sql` itself, loads everything, then runs `pludi_siltums.py`. The last line should be `Gatavs.`; the table above it should show `ca-plani` 1355 and `bankas-atm` > 0.

```bash
cd /srv/hakatons
cp src/karte/serveris/hakatons-dati.service src/karte/serveris/hakatons-dati.timer /etc/systemd/system/ && systemctl daemon-reload
systemctl start hakatons-dati.service; journalctl -u hakatons-dati -n 80 --no-pager
systemctl enable --now hakatons-dati.timer
```

**2. Border waiting-times key.** `/api/satiksme` → `kopas.robezas.kluda` = `HTTP 403: Access forbidden!`: NAP rejects the key for dataset cb730ba2 (https://transportdata.gov.lv/card/cb730ba2-6466-45b5-99e4-66b9bde30dae). Check the subscription on that card and paste its key:

```bash
nano /etc/hakatons/map.env          # NAP_API_KEY_ROBEZAS_LAIKS=<key from the cb730ba2 card>
systemctl restart hakatons-map-api
curl -s https://map.repo.lv/api/satiksme | grep -o 'robezas[^}]*'
```

**3. Caddy.** Cache headers (#97), `microphone=(self)` for the "Runāt" voice button (#70, see decisions below), `sw.js` no-cache (#148). Live today: `microphone=()` and no Cache-Control on `sw.js`.

```bash
cp /srv/hakatons/src/karte/serveris/hakatons.caddy /etc/caddy/sites/hakatons.caddy && caddy validate --config /etc/caddy/Caddyfile && systemctl reload caddy
curl -sI https://map.repo.lv/sw.js | grep -i cache-control     # no-cache
curl -sI https://map.repo.lv/app.js | grep -i cache-control    # public, max-age=300
```

## More VPS steps (4–9, in dependency order; `rits.py` doesn't print these)

**4. Only if step 1 printed `KĻŪDA` or `ca-plani` is not 1355.** Reload every layer from the repo snapshots, with no downloads (#107, #110, #118, #106 `vm-24h` row). This runs as `deploy`, so the state files stay writable by the timer.

```bash
cd /srv/hakatons && set -a && . /etc/hakatons/map.env && set +a
psql "$MAP_DB_OWNER_DSN" -q -v ON_ERROR_STOP=1 -f src/karte/db/shema.sql
sudo -E -u deploy HAKATONS_DATI=/var/lib/hakatons/dati HAKATONS_STAVOKLIS=/var/lib/hakatons/ielades bash src/karte/db/atjaunot_visu.sh --visi
curl -s https://map.repo.lv/api/kategorijas | grep -o 'evakuacijas_punkts[^}]*'   # 776
```

**5. Flood tile cache on disk (#131).** Without this the tile cache lives in PrivateTmp and is emptied on every API restart.

```bash
install -d -o deploy -g deploy /var/lib/hakatons/dati/flizes
cp /srv/hakatons/src/karte/serveris/hakatons-map-api.service /etc/systemd/system/ && systemctl daemon-reload
systemctl restart hakatons-map-api
```

**6. Warm the flood answers before the pitch (#131, #151).** The tile warm-up takes 20–60 min the first time; if tiles failed, run it again a minute later. `pludi_siltums.py` fills `pludi_kesa` for every demo address.

```bash
cd /srv/hakatons
nohup python3 src/karte/pludi_silda.py > /tmp/silda.log 2>&1 &
nohup python3 src/karte/pludi_silda.py --vietas ogre --zoom 15-16 > /tmp/silda-ogre.log 2>&1 &
python3 src/karte/db/pludi_siltums.py
tail -3 /tmp/silda.log /tmp/silda-ogre.log
```

**7. Optional: report vote salt and moderation (#84, #122).** Reports work without these; without `MAP_MOD_TOKEN`, moderation (hiding reports) is off.

```bash
echo "MAP_SALT=$(openssl rand -hex 32)" >> /etc/hakatons/map.env
echo "MAP_MOD_TOKEN=$(openssl rand -hex 24)" >> /etc/hakatons/map.env
systemctl restart hakatons-map-api
journalctl -u hakatons-map-api --since -5min | grep -E 'zinojumi:|balsu limits atmiņā'   # empty = tables OK
```

**8. Optional: local flood-zone copy (#151).** The 41.6 MB file is not in git. `/api/pludi` already works without it (LVĢMC WMS + `pludi_kesa` cache + honest `zinams:false`); this removes the LVĢMC dependency. Generate it on the PC (Git Bash, repo root):

```bash
uv run --no-project --with pyshp --with shapely --with pyproj --with numpy src/karte/db/pludu_zonas.py lejupieladet
scp src/karte/dati/pludu_zonas.geojson.gz root@161.97.105.130:/srv/hakatons/src/karte/dati/
```

then on the VPS:

```bash
cd /srv/hakatons && set -a && . /etc/hakatons/map.env && set +a
python3 src/karte/db/pludu_zonas.py ieladet
psql "$MAP_DB_OWNER_DSN" -c "select varbutiba, count(distinct nr), count(*) from pludu_zonas group by 1"
curl -s 'https://map.repo.lv/api/pludi?lat=56.8139&lon=24.6093'     # within 5 min: "metode":"PostGIS kopija"
python3 src/karte/db/pludi_siltums.py
```

**9. Final check.** On https://map.repo.lv/statuss.html, "Slāņu dati" should show 776 assembly points and "Datu avoti" on the map should show 33 · 2 simulated · 2 ⚠.

```bash
curl -s https://map.repo.lv/api/veseliba
```

## Pre-pitch check (one command on the PC)

```powershell
cd C:\Users\ZX202\kodi\hakatons; git checkout main; git pull
uv run --no-project --python 3.12 src/rits.py            # steps 1-4, 6, 7 (~5 min); --video adds step 5
```

Steps: 1 git = origin/main · 2 API (veseliba, bridinajumi, pludi Ogre, udens, prognozes, celi, one flood tile) · 3 `src/testi/parbaude.py` (demo path, 390×844 + 1280×800) · 4 slide screenshots (only if step 2 got a real flood answer) · 5 video (`--video`) · 6 classifier tests · 7 prints the VPS steps above (runs nothing). First run on a PC: `uv run --no-project --with playwright python -m playwright install chromium`.

What red or yellow means:
- **1 BRIDIN:** you're not on main. Run `git checkout main && git pull`.
- **2 pludi BRIDIN:** LVĢMC is slow. The card says so honestly. Re-run VPS step 6 and try again later.
- **2 KLUDA:** an API or VPS problem. Run `journalctl -u hakatons-map-api -n 50`.
- **3 KLUDA:** read the red rows. A front-end bug goes to a terminal; a 503 from an empty table goes back to VPS step 1/4.
- **4 IZLAISTS:** the flood answer wasn't real. Retake later with `src/demo/ekrani.py --tikai 02,03`.
- **6 KLUDA:** a classifier regression. Don't merge more search changes.

**Panic switch** for a phone or laptop showing an old copy: open https://map.repo.lv/?svaigs=1. It removes the service worker and all caches, then reloads. The bottom of `statuss.html` shows the active offline VERSION; it must equal `VERSION` in `production/sw.js` on main (`2026-10-10ci` at 06:21).

## Demo codes (`production/demo/scenariji.json`, 19)

Link: `https://map.repo.lv/?demo=<id>` (optional `&regions=100003470` = Ogre). Hands-free replay of all 19 in panel order: `https://map.repo.lv/?demo=atskanot&ilgums=20` (seconds per step, 5–120; `&saraksts=a,b` for a subset). Every demo shows "SIMULĀCIJA"; say "simulācija" out loud.

Real events (with sources):
- `jekabpils-2023`: ice-jam floods in Jēkabpils · "plūdi Jēkabpils"
- `latgale-2017`: rain floods in Latgale, Rēzekne 123.1 mm/24 h · "plūdi Rēzekne"
- `vetra-2005`: storm "Ervīns" on the Kurzeme coast · "vētra Ventspils"
- `vetra-2026`: storm of 22–23 Aug 2026, replayed with real LVC events · "nav elektrības Bauska"
- `karstums-2021`: heat wave, red warning · "karstums Rīga"
- `brell-2025`: grid without BRELL, if power went out · "nav elektrības Rīgā"
- `drons-2024`: drone falls in Gaigalava · "drons Rēzekne"
- `drons-2026`: drones over Latgale, Rēzekne oil depot · "drons Rēzekne"
- `stikli-2018`: Stiklu bog fire, smoke and evacuation · "meža ugunsgrēks dūmi Talsi"
- `ulmana-2026`: warehouse fire in Pārdaugava (~380 evacuated) · "dūmi no noliktavas Rīga"
- `bauskas-2026`: gas explosion on Bauskas iela 15 · "gāzes smaka Bauskas iela 15 Rīga"
- `meldru-2026`: scrap-metal fire in the Rīga port · "dūmi ugunsgrēks Rīga"
- `ddos-2025`: state e-services down (DDoS) · "nestrādā e-pakalpojumi"

Simulations:
- `vejs`: yellow warning, strong wind · "stiprs vējš Liepāja"
- `vetra`: red warning, storm · "vētra Rīga"
- `drons`: drone sighting in town, 1 km closed zone · "drons Rēzekne"
- `nakts`: cut hand at night, 24/7 emergency · "sagriezta roka asiņo Saulkrasti"
- `pludi-ogre`: Ogre flood, high ground ≥ 23 m · "plūdi Ogre"
- `bez-sakariem`: no power and no mobile network · "nav sakaru un elektrības"

**Pitch path** (`notes/pitch.md` slide 5, on the phone):
1. "plūdi Mednieku iela 9 Ogre": decision at the address, assembly point with the CA-plan page, route.
2. "cilvēks nav pie samaņas": red line "zvaniet 112" (no buttons, no `tel:`).
3. 30 s of the demo panel: two of `vetra-2026`, `pludi-ogre`, `nakts` (or `drons-2026`, `bauskas-2026`, `ulmana-2026`).
4. 10 s of `statuss.html`.

Slides: https://map.repo.lv/slaidi.html (13 slides, ~9:30). Backup video: `C:\Users\ZX202\kodi\demo-video\demo-horizontals.mp4` / `demo-vertikals.mp4`.

## Pitch numbers (checked against the repo 06:21)

| Number | Value | Checked in |
|---|---|---|
| Open data sources | **33 open + 2 ⚠** (112.lv shelters, banks' ATM list) | `notes/pitch.md` count, slide 9 |
| Missing datasets | **35** | `notes/missing_data.md` (rows 1–35) |
| Search scenarios | **129** | `production/scenariji.json` |
| Classifier | **96.2 %** top-1 on 612 queries (held-out 91.4 %), **93.5 %** on 200 typo queries | `src/meklesana/testi.py` run 06:15 |
| CA-plan places | **776** assembly points + **579** temporary accommodation (104 213 places) | `src/karte/dati/ca_*.geojson`, `notes/ca-plani-kvalitate.md` |
| Coordinate errors in official plans | **41** (16 outside the municipality + 25 > 1 km from the plan's own address) | `notes/ca-plani-kvalitate.md` |
| CA plans read | **42** municipalities (41 folders, Ventspils shared); 31 publish lists, 10 don't | same |
| Critical ATMs | **111** of 845 bank ATMs | `src/karte/dati/bankomati_bankas.csv`, `shema.sql` |
| Demo scenarios | **19** (13 real events + 6 simulations) | `production/demo/scenariji.json` |

Correction: slide 8 (`slaidi.html`) and `pitch.md` still say "96,1 % uz 609 vaicājumiem". Today's run gives 96.2 % on 612 (the test set grew by 3). Both are honest; update only if you touch the slides anyway.

## Merged tonight (#63–#158, grouped)

- **UI, phone and desktop:**
  - #73, #139: decision first and the 3-step strip.
  - #119, #150, #158: bottom sheet like the mock-up, popups fit.
  - #113: desktop three columns.
  - #108, #154: SVG sprite icons, marker shapes, 44 px hit areas, nearest-marker tap.
  - #115: Notīrīt. #132: first-visit hint. #137: RU/EN card + switch.
  - #69, #144: Saraksts list view. #80: share/print with QR.
  - #138: accessibility, axe 0 violations.
  - #88, #97, #146: phone fixes and performance (search 3.9 → 1.7 s on Slow 4G).
  - Smaller: #102, #104, #109, #153.
- **Search:**
  - #76, #81, #111, #140: classifier 77 % → 96.2 %, typo tolerance, RU in Latin letters.
  - #70: suggestions and voice input.
  - #117: advice checked against VUGD / AM, source link.
  - #121: skips closed or full places.
- **Data layers and API:**
  - #65: risk map today/tomorrow. #67: traffic zones. #66: fire-water intakes + PT stops.
  - #75: resilience candidates + simulated points. #107: +46 assembly points (776).
  - #110: banks' critical ATMs. #118: OSM water / Wi-Fi / EV / vet.
  - #116, #129: LR1 radio map. #120: next 24 h. #122: lightning feed items.
  - #123: gauge thresholds (Ogre 22.15 m). #124: road-closure zones + 10 % flood shade.
  - #78: routes around closed zones. #82: observed gusts. #127: UR contacts 42/42.
  - #84, #133: Ziņot reports, 5-step flow with summary. #103: Atom + iCal. #114: bbox loading (958 KB → 6–104 KB).
- **Resilience:**
  - #131: flood tile proxy + cache. #151: `/api/pludi` never fails (PostGIS copy → WMS + cache → `zinams:false`).
  - #125: Meteoalarm fallback for warnings.
  - #79, #130, #148: offline mode, SW update toast, `?svaigs=1`.
  - #91: API load hardening. #63: border-feed fallbacks. #86, #77: daily refresh unit.
  - #147: statuss.html external sources + layer counts.
  - #134: hotfix for conflict markers from #133.
- **Docs, pitch, demo:**
  - #71, #74, #135: 13-slide deck, print, QR. #136: 90 s backup video. #142: screenshot retake script.
  - #94, #143: 12 real crises with sources. #105, #156: replay and demo panel presentation-clean.
  - #72, #149, #152: 35 missing datasets + trukstosie.html. #98, #141: Open API docs.
  - #100, #126: honest source count. #106: sources verified. #128: criteria audit.
  - #64, #85, #89, #90, #93, #96, #99, #101, #87: notes and TODO.
- **QA:**
  - #68 `parbaude.py`. #145 `rits.py`.
  - #95, #155: card audit (387 cards on recorded fixtures, no dead ends, a source line for every place).

## Open PRs and running work (06:21)

- **#157** `noiseparty/druka-2`: print on one A4 page in LV/RU/EN, the share link keeps language and decision. Open, not merged.
- Agents still running in locked worktrees, no PR yet: `noiseparty/demo-4`, `noiseparty/kartites-4`, `noiseparty/pitch-cels`. Check with `gh pr list` before freezing `main`.

## Risks and decisions for you

- **LVĢMC flood WMS was unreliable all night.**
  - In place: tile proxy + 30-day cache, `pludi_kesa`, and an honest "nav zināms" in the card.
  - When it answers, retake slide screenshots 02/03 and the video's flood row: `uv run --no-project --python 3.12 --with playwright --with pillow src/demo/ekrani.py --tikai 02,03`, then `uv run --no-project --python 3.12 --with playwright --with pillow --with imageio-ffmpeg src/demo/video.py`, and commit the new `production/slaidi/*.webp` in a PR.
- **Decide:** the reports licence. API and `zinot.js` say CC BY 4.0; the flow brief said CC0.
- **Decide:** the flood files licence. ĢeoLatvija.lv's file page says CC BY-SA 4.0, data.gov.lv says CC0. The `avoti` row uses the stricter CC BY-SA 4.0 and notes the difference.
- **Decide:** the microphone. Caddy step 3 enables the "Runāt" button, which sends audio to Google/Apple speech recognition. To keep it off, change `microphone=(self)` to `microphone=()` in the copied file before the reload.
- **Riga transit live layer:** on hold. It needs your cURL/HAR of saraksti.lv (whether to send the Referer header).
- **Real-phone tests not done.** Everything is tested with Playwright emulation only (375×740, 360×640, 390×844). Do one Android + one iPhone pass: location allowed and denied, the pitch path, "Ziņot".
- **Overnight incidents, no harm done:**
  - One agent force-pushed to its own branch once.
  - #133 left conflict markers in `meklesana.js` live for ~2 min; #134 fixed them. Since then the merge checklist includes `grep '^<<<<<<<'` + `node --check`.
- The live "Datu avoti" panel shows **29 + 1** until VPS step 1 (or 4) loads the new rows. Slides use 33 + 2.
- `/api/meklejumi/top` is 200 now (the `meklejumi` table exists).

---

# Technical state

## What's live

**Front door:** the search "Kas Jums vajadzīgs?" (LV/RU/EN, 129 scenarios, rule-based, no AI at runtime). One query gives one result card. Its order:
- the decision block (flood zone yes/no at the address, or the nearest needed place + one next action);
- LVĢMC warnings;
- "Nākamās 24 h";
- facts: gauge vs CA-plan thresholds, rain/soil, roads;
- nearest places, each with source + licence and CA-plan page links;
- advice with a source link;
- "Kas notiks tālāk".

An address in the query sets the reference point. Life-threat queries put a red "zvaniet 112" line on top. There are no `tel:` links anywhere. On phones the card is a bottom sheet (Mazs/Puse/Pilns); on desktop (≥ 800 px) there are three columns.

**Other pages:**
- `info.html`: 112, sirens, LV-ALERT, LR1 radio map, 72 h checklist.
- `statuss.html`: live sources, caches, layer counts.
- `trukstosie.html`: 35 missing datasets.
- `slaidi.html`: the deck.
- `api.html` + `openapi.json`: every API route.
- `moderacija.html`: reports moderation (needs `MAP_MOD_TOKEN`).

**Map layers in the live DB (`/api/kategorijas`, 06:20):**

| Layer | Count |
|---|---|
| shelters | 778 ⚠ |
| assembly points | 730 (→ 776 after VPS step 1) |
| accommodation | 579 |
| resilience candidates (OSM) | 1 172 |
| 24/7 hospitals | 37 |
| medical institutions | 69 |
| pharmacies | 814 |
| ATMs | 802 (OSM; bank ATMs come with step 1) |
| fuel | 588 |
| police | 55 |
| fire depots | 87 |
| river gauges | 68 |
| fire-water intakes | 1 117 |
| PT stops | 11 960 |
| simulated water / charging points | 100 + 100 |

Still missing until step 1: `bankas-atm`, `osm-udens`, `osm-wifi`, `osm-ev`, `osm-vet`.

Live overlays without the DB:
- LVĢMC flood zones (tile proxy), warnings, forecast regions, observations, lightning (+ FMI);
- LVC road events and closure zones;
- traffic zones;
- the risk map.

**API:** `src/karte/api/karte_api.py`, every route documented at https://map.repo.lv/api.html (generated from `MARSRUTI` by `src/api_docs/sagatavot.py`). It restarts itself when the file changes on `main`.

**NAP keys on the VPS** (`/etc/hakatons/map.env`):
- `NAP_API_KEY_NEGADIJUMI`, `_REMONTI`, `_SATIKSME_SLIDENS`, `_UZTURETAJI_SLIDENS`, `_METEO_SLIDENS`, `_SATIKSMES_IEKARTU_MERIJUMI`, `_SATIKSMES_APJOMS_ATRUMS_MIN`: work.
- `_ROBEZAS_LAIKS`: 403 (VPS step 2).
- `SLEGUMI` and `JOSLAS` aren't subscribed.

Mapping to NAP cards: `notes/research/nap-satiksme.md`.

## How deploy works

- The VPS pulls `main` every minute; `production/` is served as static files, so a merge is live in ~1 min.
- `hakatons-map-api-restart.path` restarts the API when `karte_api.py` changes.
- `shema.sql` is applied by the daily `hakatons-dati.timer` run (04:30) or by hand.
- Data loaders and systemd/Caddy changes are VPS steps that only the user runs.
- Full guide: `notes/deploy.md`.
- Service worker: bump `VERSION` in `production/sw.js` only when `sw.js` or its `SHELL_FAILI` list changes. `uv run --no-project --python 3.12 src/testi/sw_faili.py --parbaudit` checks the list.

## Known gaps

- Real phones (iOS Safari `dvh`, Android back button with the sheet, keyboard in Ziņot step 3).
- 10 municipalities don't publish assembly/accommodation lists.
- Ventspils lists are in restricted annexes.
- Shelters and the banks' ATM list have no open licence (⚠ in the UI).
- River danger thresholds come from the CA plans only (PRIS needs LVĢMC permission).
- The traffic free-flow speed is an estimate.
- There is no open real-time Riga transit feed.
- 4 LR1 transmitters (Alūksne, Limbaži, Lielauce, Skaista) are still placed at the town centre.

## How we work (parallel sessions)

The rules are in `CLAUDE.md` → "Multi-session"; new-PC setup is in `notes/claude-setup.md`. In short:
- One orchestrator plus terminals A–E, each in its own worktree.
- Every terminal hands its brief to one background agent in an isolated worktree.
- The owner opens the PR; the orchestrator merges with the checklist, without reviews.
- Only the user runs VPS steps.
- `git worktree list` shows what's checked out on this PC.
