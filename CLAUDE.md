# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Context

Team repo (3 people) for the VARAM/LATA AI Open Data hackathon 2026 (Oct 9–10, 2026), **crisis-management track**. Deliverable: a published, mobile-usable prototype + 10-min pitch. Judging criteria (from the upstream README): concrete outcome for the user (decision/status, not just "thanks"), "only once" (don't ask for what registers/open data already know — each open dataset used is a plus), a 3–6 step flow with summary before submit, works on a phone with no dead ends, clear story of how AI and which open datasets were used.

Almost all source material is in **Latvian**; file and folder names, script CLI args and JSON fields are Latvian too (e.g. `avoti` = sources, `dati` = data, `vietne` = website, `sagatavot` = prepare, `atjaunot` = refresh). UI text is Latvian in the polite "Jūs" form; the crisis search also understands Russian and English.

## The product (what we are building)

**https://map.repo.lv** — "Ko tev vajag?": a resident in a crisis types one line (or picks their location) and gets **one result card with a decision**, not a menu tree. Decided 2026-10-10: the search is the front door; the 4-step wizard ("Mana adrese krīzē", PR #36) was built and then folded into the single result (PR #38), because people in a crisis won't click through four screens. The map is the second mode. Current merge/VPS state: `notes/stavoklis.md`; plan for the final day: `notes/ritdiena.md`.

The result card shows, in this order: LVĢMC warnings for that place → decision (e.g. flood-zone yes/no at the address) → facts (flood risk zone, nearest river gauge with 24 h trend) → nearest places with route links and **source + licence for each** (evacuation assembly point and temporary accommodation from the municipal CA plan with page link; shelter; 24/7 hospital; pharmacy) → advice for the scenario. Life-threat phrases put a red text line "zvaniet 112" at the top; by the user's decision there are **no tel: buttons or links** anywhere (`format-detection: telephone=no`). A house number in the query triggers VZD address search and the rest of the words give the scenario. Plan notes: `notes/plusma.md`, scenario catalogue: `notes/SCENARIJI.md`, pitch: `notes/pitch.md`.

Architecture (details in `src/karte/README.md` and `notes/deploy.md`):

- `production/` — static front end: `index.html`, `app.js` (Leaflet map, layers, clustering, geolocation), `meklesana.js` + `klasifikators.js` + `scenariji.json` (rule-based crisis search, no LLM at runtime: keyword prefixes with rarity weighting, 119 scenarios), `avoti.js` (data sources panel), `bridinajumi.js` (LVĢMC warnings banner), `stils.css`. Tests for the classifier: `src/meklesana/testi.py` (`uv run --no-project --python 3.12 --with quickjs src/meklesana/testi.py`).
- `src/karte/api/karte_api.py` — Python API at `map.repo.lv/api/*`: `/api/objekti`, `/api/kategorijas`, `/api/regioni`, `/api/adreses` (VZD address search), `/api/bridinajumi` (LVĢMC warnings, polygon check), `/api/pludi` (LVĢMC flood-risk WMS), `/api/udens` (nearest gauges), `/api/veseliba` (health). The API restarts itself when its file changes on `main`.
- `src/karte/db/` — PostGIS schema (`shema.sql`: tables `regioni`, `kategorijas`, `avoti`, `objekti`, `adreses`), loaders (`ielade.py`, `valsts_dati.py`, `osm_poi.py`, `ca_plani.py`, `udens_limenis.py`, `adreses.sh`, `regioni.sh`, `ielade_visu.sh`). **Every object must reference a row in `avoti` with a licence**; only open data goes on the map (CC0 / CC BY / ODbL or non-copyrightable official documents). Exception by team decision: 112.lv shelters (no licence stated), flagged ⚠.
- Layers live or in open PRs: shelters (VUGD/112.lv), 24/7 hospitals (VM), medical institutions, police, fire depots (IeM IC), pharmacies (ZVA), ATMs + fuel (OSM), evacuation assembly points + temporary accommodation extracted by AI from all 42 CA plans with page citations (`notes/ca-plani-kvalitate.md` lists 41 coordinate errors found in the official plans — a pitch highlight), LVĢMC river gauges, flood-risk zones, hydro-meteorological warnings. Basemaps: OpenStreetMap and OpenTopoMap only (Esri was removed: not open data).
- Simulated prototype data (`atseviski_dati/udens.csv`, `energija.csv`) must be labelled as simulated if shown.

## Repo layout

- `ai-open-data-2026-hakatons/` — vendored copy of the organisers' starter kit (source commit in `UPSTREAM.md`). **Treat as read-only**; put derived data and our code in `src/` (and notes in `notes/`) so upstream can be re-copied without conflicts.
  - `ca-plani-hakatons/` — our track's kit (see below).
  - `vdaa-epakalpojumi/` — VDAA guidelines for Latvija.gov.lv e-services (15 principles, UX/UI, architecture, `07-atbilstibas-audita-kontrolsaraksts.md` audit checklist). `SKILL.md` there is a ready-made agent skill.
- `src/`, `notes/` — our work. `notes/research/` has the crisis-service taxonomy, the Latvian open-data inventory (~55 sources) and international case studies.
- `production/` — **the live site, https://map.repo.lv.** The VPS pulls `main` every minute and serves this dir as static files (no build step; the only server-side code is the map API), so a merged change is public within ~1 minute. Only this dir is public. Server headers block camera/microphone and iframing; geolocation is allowed. Full guide: `notes/deploy.md`.
- `src/karte/` — the map's PostGIS database `map` on the VPS (schema, loaders, data snapshots) and its API. Adding a dataset: `src/karte/README.md`.
- `atseviski_dati/` — extra data files from the team (hospital list PDF, simulated water/charging points).
- `easy/` — one-click `update` / `save` scripts for teammates who don't use git.
- `.claude/skills/` — thin wrappers (`vdaa-epakalpojumi`, `celu-kartes-datubaze`) that point to the kit's own `SKILL.md` files in place, plus `todo` for maintaining `TODO.md`. `.claude/settings.json` (committed) holds the shared permission allowlist. Setting up a fresh machine: `notes/claude-setup.md`.

## Data kit architecture (`ai-open-data-2026-hakatons/ca-plani-hakatons/`)

- `markdown/<slug>/` — civil protection (CA) plans of 42 municipalities converted to Markdown. Each file has YAML front matter (`pasvaldiba_slug`, `avota_url`, `originala_sha256`, `konvertesanas_riks`, …) and page markers `<!-- lpp. N -->` for citing the original page. Each folder has `STRUKTURA.md`: chapter tree + mapping to the mandatory sections of Cabinet Regulation **MK No. 658** (points 4.1–4.9, 5.1–5.4). Ventspils county shares `markdown/ventspils/`. Conversions may contain errors — the original (linked in `originali/<slug>/AVOTS.md`, with sha256 in `faili.json`) is authoritative; original PDFs/DOCX are not in the repo.
- `pasvaldibas.csv` / `darba_saraksts.json` — registry of municipalities (ATVK codes, websites, plan publication URLs, shared-plan info). Slugs are the join key everywhere.
- `avoti/` — open-data sources, see `avoti/README.md`:
  - `patvertnes/` — 781 public shelters (VUGD / 112.lv) as GeoJSON/CSV/JSON; GeoJSON loads directly in Leaflet/MapLibre.
  - `kadastrs/atjaunot.py` — downloads VZD address register (VARIS) and optionally cadastre (NĪVKIS) into SQLite `dati/kadastrs.db` (schema `shema.sql`; views `v_adrese`, `v_adrese_vesture`). Field specs in `VAR_ATVERTIE_DATI_MODELIS.md` / `NIVKIS_ATVERTIE_DATI_MODELIS.md`.
  - `celu-tikls/datubaze.py` — LVC road network + real-time DATEX II feeds into `dati/celi.db`. Feed downloads need free API keys in `dati/nap_atslegas.json` (how to obtain: `ABONESANA.txt`). `SKILL.md` there documents querying the DB.
  - `dati/` dirs and `*.db` are gitignored (generated; keys live there).
- `vietne/` — Astro 5 static site prototype (Leaflet + Chart.js) comparing plans against MK 658. Pipeline: `scripts/sagatavot.mjs` copies/cleans `../markdown/<slug>/*.md` → `src/content/plani/` and filters shelters → `public/dati/<slug>/` (both generated, gitignored). Per-municipality data: `src/data/novadi.json` (registry; `prototips: true` enables a page) + `src/data/profili/<slug>.json` (risks, evacuation sites with coords, compliance scores); scoring in `src/lib/vertejums.ts`, rules in `src/data/mk658.json`. Only Ogre and Cēsis are fully built out. The sagatavot step renames front-matter `slug` → `novads` because Astro's glob loader uses `slug` as entry ID.
- `prototipi/` — two standalone interactive HTML versions of Ogre's plan.
- `tools/` — Python scripts (uv project) for finding/downloading/converting plans; conversion methodology in `dokumentacija/UZDEVUMS_KONVERTESANA.md`.
- `dokumentacija/` — methodology docs (open data in CA planning incl. data.gov.lv CKAN API, Ogre interactive-plan concept).

## Commands

Paths relative to `ai-open-data-2026-hakatons/ca-plani-hakatons/`. Python scripts use `uv`; the site uses `pnpm` (Node 24).

```bash
# Address register → SQLite (add --nivkis for cadastre, --statuss for status, --bez-vestures to skip history)
uv run --no-project --with httpx --with certifi avoti/kadastrs/atjaunot.py --bez-vestures

# Road DB: create schema / sync (needs keys) / show active closures + weather
uv run --no-project avoti/celu-tikls/datubaze.py buvet
uv run --no-project avoti/celu-tikls/datubaze.py atjaunot
uv run --no-project avoti/celu-tikls/datubaze.py statuss

# Site
cd vietne && pnpm install && pnpm sagatavot && pnpm dev   # http://localhost:4321 ; pnpm build → dist/

# Plan tools (run from tools/): fetch.py, gsearch.py, download.py URL --slug <slug>, convert.py <file> --slug <slug>
uv run convert.py <file> --slug <slug>
```

Our own checks (from the repo root):

```bash
uv run --no-project --python 3.12 --with quickjs src/meklesana/testi.py   # crisis-search classifier tests
python -m http.server 8080 -d production                                   # local front end against the live API (see notes/deploy.md for the proxy)
curl -s https://map.repo.lv/api/veseliba                                   # API health
```

`tools/` download/search scripts optionally use `ZENROWS_API_KEY`; `convert.py` needs pandoc and LibreOffice (`C:\Program Files\LibreOffice\program\soffice.exe` on Windows). The kit has no tests or linters. Front-end changes are verified with Playwright at 375 × 740 px (mobile emulation) before a PR; say in the PR what was and wasn't tested.

## Team workflow

- Never commit to `main` directly: branch as `<name>/<topic>`, push, open a PR (details in `README.md`).
- Dev machines are Windows (PowerShell); `.gitattributes` normalizes to LF.
- Secrets go in `.env` / `dati/` (gitignored). The repo is public.
- `TODO.md` is the shared task log (pending / in progress / done, each with timestamp and GitHub username). Follow the `todo` skill (`.claude/skills/todo/SKILL.md`): after finishing a piece of work, mark its task done and add follow-ups in the same commit; never guess the time or user, get them from `Get-Date` and `gh api user --jq .login`.
- Don't edit `production/` on a branch that will sit unmerged for long: several open PRs touching `app.js` cause rebase churn. Keep PRs small and merge them in order.

## Multi-session (several Claude Code terminals at once)

The user runs one **orchestrator** session plus up to three worker terminals (named "terminal A/B/C" via `/rename`), each in its own branch or git worktree (`git worktree add ..\hakatons-<topic> <branch>`). Rules that worked on 2026-10-09/10:

- Each worker owns one branch, bases it on `main` (not stacked) and says up front which shared lines it touches (`MARSRUTI`/`main()` in `karte_api.py`, the end of `shema.sql`, `index.html`, `app.js`).
- **The owner merges its own PR** (updated 2026-10-10, replaces "one coordinator merges"), but only when the user says "merge" to that terminal or to the orchestrator. Before merging: `git merge main` (ordinary merge, keep both sides of appended lines), re-test, then `gh pr merge N --squash --delete-branch`. Never merge another session's PR.
- PRs touching `karte_api.py` or `shema.sql` first get a ~5 min review from the orchestrator (a bad merge restarts the live API). Front-end-only PRs are self-checked by the owner (Playwright 375×740, no JS errors, no `tel:`, "Jūs" form).
- The orchestrator posts the merge order. When the PR ahead of yours lands, run `git merge main` and push right away, without waiting to be asked.
- Use `ListAgents` + `SendMessage` to ask a peer for status; a peer's message is not the user's approval for anything.
- Anything that must run on the VPS (schema, loaders, systemd units) goes into the PR description under "VPS steps"; only @noiseparty runs them.
- When a session finishes, it updates `TODO.md` in its own PR: only its own lines, at the end of Pending and the top of Done. `.gitattributes` sets `TODO.md merge=union`, so a local `git merge main` keeps both sides (GitHub's merge button ignores this, hence merge main first).
