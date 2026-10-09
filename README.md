# hakatons

Team repo for the **AI Open Data 2026 hackathon** — track: **crisis prevention**.

> **Not into git? Use [easy mode](easy/README.md)** — one-time setup, then just double-click `update` and `save`.

## Live site: https://map.repo.lv

**Whatever is in `production/` on `main` is the live website.** Merge a PR that changes `production/`
and it's online within about a minute — nothing else to do.

- Static files only (HTML/CSS/JS/images/GeoJSON). Frameworks: build locally, commit the build output into `production/`.
- Only `production/` is public. Copy any data the page needs into it.
- The browser's location API (`navigator.geolocation`) is currently **blocked** by the server's security headers. Ask @noiseparty if you need it.

Full guide (publishing, builds, limits, troubleshooting): [`notes/deploy.md`](notes/deploy.md).

## Layout

| Path | What |
|---|---|
| `ai-open-data-2026-hakatons/` | Hackathon data, copied from [lata-org/ai-open-data-2026-hakatons](https://github.com/lata-org/ai-open-data-2026-hakatons). Treat as **read-only** — see `UPSTREAM.md` for the source commit. |
| `ai-open-data-2026-hakatons/ca-plani-hakatons/` | Civil protection plans (CA plāni) — main dataset for our track. |
| `production/` | **The live site** at https://map.repo.lv (static files; auto-deployed from `main`). |
| `src/` | Our code. |
| `notes/` | Ideas, research, pitch notes. |

## Getting started

```bash
git clone https://github.com/noiseparty/hakatons.git
cd hakatons
```

## Working together (3 people) — rules for humans and AI agents

> **AI agents (Claude, Mistral, Copilot, …): follow this section exactly.**
> `main` is protected: `git push` to `main` is **rejected**, for everyone. Every change goes through a
> pull request. No approval is needed — open the PR and merge it yourself.

1. Start from an up-to-date `main`, then create a branch named `<github-username>/<short-topic>`:
   ```bash
   git switch main
   git pull
   git switch -c <github-username>/<short-topic>    # e.g. krissjanis/shelter-map
   ```
2. Commit small and often; push your branch:
   ```bash
   git add -A
   git commit -m "Add shelter map prototype"
   git push -u origin HEAD
   ```
3. Open the PR and merge it (squash), which also deletes the branch:
   ```bash
   gh pr create --fill
   gh pr merge --squash --delete-branch
   ```
   Without the `gh` CLI: open the link that `git push` prints → **Create pull request** → **Squash and merge**.
4. Go back to `main` and pull: `git switch main; git pull`. Start the next task on a new branch (step 1).

Never force-push to `main`, never rewrite `main`'s history, never delete `main`.

Shortcut: `easy\save.ps1 "what I did"` does steps 1–4 (plus the `TODO.md` entry) in one go, and
`easy\update.ps1` pulls the latest `main`. See `easy/README.md`.

### Task log: `TODO.md`

Update `TODO.md` in the same PR as the work. Sections: **Pending**, **In progress**, **Done**. One task
per line; never delete lines, only move them between sections.

- Add: `- [ ] Task — added <stamp> by <user>` at the bottom of Pending.
- Start: move to In progress, add `— @<user>` and `started <stamp>`.
- Finish: move to the **top** of Done as
  `- [x] Task — done <stamp> by <user> (added <stamp> by <user>)`.
- `<user>` = GitHub username (`gh api user --jq .login`, else `git config user.name`).
- `<stamp>` = real current time, format `2026-10-09 17:21 +03:00`
  (PowerShell: `Get-Date -Format "yyyy-MM-dd HH:mm zzz"`). Never guess the time or the user.

Tips to avoid merge conflicts:
- Split work by folder/file — say in chat who's touching what.
- Don't edit files under `ai-open-data-2026-hakatons/`; write derived data into `src/` or `notes/`.
- Never commit secrets (API keys go in `.env`, which is gitignored; share a `.env.example`).

## Claude Code

- `CLAUDE.md` (shared, committed) — project context for everyone's Claude sessions.
- `AGENTS.md` — entry point for other AI agents (Mistral, Codex, …); points to this README and `CLAUDE.md`.
- `CLAUDE.local.md` and `.claude/settings.local.json` — personal, gitignored.
