# Prod deploy: map.repo.lv

**Whatever is in `production/` on `main` is the live site at https://map.repo.lv.**
Merge a PR that changes `production/` and it is live within about a minute. There is nothing to run,
nothing to upload and no secrets involved.

## Publishing a change

1. Put the finished files in `production/` (`index.html` is the home page).
2. Save as usual: `easy\save.ps1 "what I did"`, or branch → PR → squash-merge (see `README.md`).
3. Wait ~1 minute and reload https://map.repo.lv (hard reload: Ctrl+F5).

Taking the site down or rolling back = a PR that changes `production/` back. Never edit files on the server.

## What gets served

- Only static files: HTML, CSS, JS, images, GeoJSON/JSON, fonts. The one exception is the map API at
  `/api/*` (see below); anything else dynamic must happen in the browser (or call an outside API).
- Only `production/` is public. The rest of the repo (data kit, `src/`, `notes/`) is **not** reachable
  through map.repo.lv, so copy any data the page needs into `production/` (e.g. `production/dati/patvertnes.geojson`).
- Clean URLs work: `/par` serves `production/par.html` or `production/par/index.html`.
- A missing file gives a plain-text 404. There is no single-page-app fallback to `index.html`, so use
  hash routing (`#/step-2`) or real files per page.
- Use **relative** paths (`./app.js`, `dati/x.geojson`) or paths from the root (`/app.js`). The site lives
  at the domain root, so no base path is needed.
- HTTPS only; `http://` redirects to `https://`. Certificate is Let's Encrypt, renewed automatically.

## Building a framework app (Astro, Vite, …)

The server does not build anything. Build on your machine and commit the **output** into `production/`:

```powershell
# example: the kit's Astro site
cd ai-open-data-2026-hakatons\ca-plani-hakatons\vietne
pnpm install; pnpm sagatavot; pnpm build          # → dist\
robocopy dist ..\..\..\production /MIR             # replace production\ with the build
```

`/MIR` deletes files in `production\` that aren't in `dist\`, which is what you want for a build, but
check `git status` before saving. Keep source code in `src/`, and only build output in `production/`.

## Known limits (security headers sent on every response)

| Header | Effect on our app |
|---|---|
| `Permissions-Policy: camera=(), microphone=(), geolocation=(self)` | "Use my location" works on map.repo.lv; camera and microphone are blocked. |
| `X-Frame-Options: DENY` | The site can't be embedded in an `<iframe>` on another site. Linking to it is fine. |
| `Strict-Transport-Security` | Browsers always use HTTPS. |

Loading Leaflet/MapLibre, map tiles, fonts or APIs from other domains (CDNs, OpenStreetMap, data.gov.lv)
works. There is no Content-Security-Policy restricting it.

## How it works (for whoever administers the VPS)

VPS `161.97.105.130` (Ubuntu 24.04, Caddy). Root SSH by key only; teammates don't need server access.

- `hakatons-sync.timer` runs `hakatons-sync.service` every 60 s as the `deploy` user:
  `git fetch origin main && git reset --hard origin/main` in `/srv/hakatons` (public repo over HTTPS, no key).
- Caddy (`/etc/caddy/sites/hakatons.caddy`) serves `/srv/hakatons/production` with `file_server`
  and `import common` (the security headers above). DNS: `map.repo.lv` A → `161.97.105.130`.
- Logs: `journalctl -u hakatons-sync` (pulls), `/var/log/caddy/hakatons.log` (requests).
- Force a pull now: `systemctl start hakatons-sync.service`. Check what's live:
  `sudo -u deploy git -C /srv/hakatons log --oneline -1`.

## Troubleshooting

- **Change not showing after 2 minutes:** check the PR is actually merged into `main` (not just pushed to a
  branch), and that the files are under `production/`. Then hard-reload (Ctrl+F5).
- **404 "nothing published yet":** that URL has no file in `production/`. Check the spelling and capitalisation
  (the server is case-sensitive: `Karte.html` ≠ `karte.html`).
- **Works locally, broken live:** usually an absolute path to your own disk (`C:\...`) or a file outside
  `production/`. Open the browser dev tools (F12) → Console/Network to see which file 404s.

## Map API (`/api/*`)

`/api/*` is proxied to the map API (`src/karte/api/karte_api.py`, `hakatons-map-api.service`
on 127.0.0.1:8920), which reads the PostGIS database `map`. It also follows `main`: a change to
`karte_api.py` restarts the service automatically. Data is loaded into the DB by hand on the VPS;
how-to in `src/karte/README.md`. Credentials live only in `/etc/hakatons/map.env` on the VPS.

`map.repo.lv` allows `geolocation=(self)` (the shared Caddy `common` block blocks it for other sites).
The live Caddy and systemd files are copied in `src/karte/serveris/`; keep them in sync when changing the server.

## Daily data refresh (`hakatons-dati.timer`)

Every day at 04:30 (Europe/Riga) `hakatons-dati.service` runs `src/karte/db/atjaunot_visu.sh`. It:

1. applies `shema.sql` (idempotent, so new tables and columns land without a manual step);
2. downloads the daily sources into **`/var/lib/hakatons/dati`**, never into the git checkout `/srv/hakatons` (the minute sync would fight with it):
   - `valsts_dati.py`: ZVA pharmacies, IeM IC hospitals, police, VUGD depots, VKCP water intakes;
   - `osm_poi.py`: OSM ATMs and fuel;
   - `gtfs.py`: Rīgas satiksme, ATD and VIVI stops;
3. loads every source downloaded **in this run** with `ielade.py`. If a download fails, the database keeps yesterday's rows, and the run ends with exit code 1;
4. reloads the static snapshots from the repo (112.lv shelters, VM 24/7 hospitals, CA plans) only when the file changed (sha256 kept in `/var/lib/hakatons/ielades/`). `ca_plani.py` itself needs the cadastre DB, so it still runs locally and its GeoJSON comes in by PR.

`ielade.py` is safe to re-run:
- it upserts by `(avots, avota_id)`;
- it deletes rows missing from the new file **only if the file has ≥ 90 %** of the previous count. Otherwise it keeps the old rows and exits with 3, which the script reports as a warning;
- `--atlaut-samazinajumu` overrides the guard for a deliberate shrink;
- every successful load writes `avoti.atjaunots`. The "Datu avoti" panel shows it per source, and the status page has a "Datu vecums" row that is red when a daily source is older than 48 h.

```bash
systemctl list-timers hakatons-dati.timer                 # next run
journalctl -u hakatons-dati -n 100                        # last run
systemctl start hakatons-dati.service                     # run now
sudo -u deploy bash -c 'cd /srv/hakatons && set -a && . /etc/hakatons/map.env && set +a && bash src/karte/db/atjaunot_visu.sh --parbaude'   # dry run
```

A full reload from the repo snapshots (no download) is still `bash src/karte/db/ielade_visu.sh`, which is `atjaunot_visu.sh --visi`.
