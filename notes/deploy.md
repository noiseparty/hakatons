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

- Only static files: HTML, CSS, JS, images, GeoJSON/JSON, fonts. No PHP, Node or Python runs on the server,
  and there is no database. Anything dynamic must happen in the browser (or call an outside API).
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
| `Permissions-Policy: camera=(), microphone=(), geolocation=()` | **The browser's location API is blocked**: `navigator.geolocation` fails. Camera and microphone too. If the prototype needs "use my location", ask @noiseparty to allow it for map.repo.lv (one-line server change). |
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
