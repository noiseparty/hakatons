# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Context

Team repo (3 people) for the VARAM/LATA AI Open Data hackathon 2026 (Oct 9–10, 2026), **crisis-management track**. Deliverable: a published, mobile-usable prototype + 10-min pitch. Judging criteria (from the upstream README): concrete outcome for the user (decision/status, not just "thanks"), "only once" (don't ask for what registers/open data already know — each open dataset used is a plus), a 3–6 step flow with summary before submit, works on a phone with no dead ends, clear story of how AI and which open datasets were used.

Almost all source material is in **Latvian**; file and folder names, script CLI args and JSON fields are Latvian too (e.g. `avoti` = sources, `dati` = data, `vietne` = website, `sagatavot` = prepare, `atjaunot` = refresh).

## Repo layout

- `ai-open-data-2026-hakatons/` — vendored copy of the organisers' starter kit (source commit in `UPSTREAM.md`). **Treat as read-only**; put derived data and our code in `src/` (and notes in `notes/`) so upstream can be re-copied without conflicts.
  - `ca-plani-hakatons/` — our track's kit (see below).
  - `vdaa-epakalpojumi/` — VDAA guidelines for Latvija.gov.lv e-services (15 principles, UX/UI, architecture, `07-atbilstibas-audita-kontrolsaraksts.md` audit checklist). `SKILL.md` there is a ready-made agent skill.
- `src/`, `notes/` — our work.
- `src/karte/` — the map's PostGIS database `map` on the VPS (schema, loaders, data snapshots) and its API, served at `map.repo.lv/api/*` (everything else on map.repo.lv is static files from `production/`). Adding a dataset: `src/karte/README.md`.
- `.claude/skills/` — thin wrappers (`vdaa-epakalpojumi`, `celu-kartes-datubaze`) that point to the kit's own `SKILL.md` files in place, so their relative paths keep working; plus `todo` for maintaining `TODO.md`.

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

`tools/` download/search scripts optionally use `ZENROWS_API_KEY`; `convert.py` needs pandoc and LibreOffice (`C:\Program Files\LibreOffice\program\soffice.exe` on Windows). No tests or linters exist in the kit.

## Team workflow

- Never commit to `main` directly: branch as `<name>/<topic>`, push, open a PR (details in `README.md`).
- Dev machines are Windows (PowerShell); `.gitattributes` normalizes to LF.
- Secrets go in `.env` / `dati/` (gitignored). The repo is public.
- `TODO.md` is the shared task log (pending / in progress / done, each with timestamp and GitHub username). Follow the `todo` skill (`.claude/skills/todo/SKILL.md`): after finishing a piece of work, mark its task done and add follow-ups in the same commit; never guess the time or user, get them from `Get-Date` and `gh api user --jq .login`.
