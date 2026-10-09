# Prod deploy: map.repo.lv

Whatever is in `production/` on `main` is the live site at https://map.repo.lv, served as static files.
Merge a PR and the change is live within about a minute. Nothing to run, no secrets in the repo.

How it works (on the VPS, 161.97.105.130):

- `hakatons-sync.timer` runs `hakatons-sync.service` every 60 s as the `deploy` user:
  `git fetch origin main && git reset --hard origin/main` in `/srv/hakatons` (public repo, HTTPS, no key).
- Caddy (`/etc/caddy/sites/hakatons.caddy`) serves `/srv/hakatons/production` with `file_server`;
  `/foo` also tries `/foo/` and `/foo.html`. HTTPS via Let's Encrypt, automatic.
- Logs: `journalctl -u hakatons-sync` (pulls), `/var/log/caddy/hakatons.log` (requests).

Only static files are served, so a build step (e.g. the Astro site in `vietne/`, `pnpm build` → `dist/`)
must run locally, with its output committed into `production/`. Nothing outside `production/` is public.
