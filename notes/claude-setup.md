# Claude Code on the other PC (same setup as the main dev PC)

Updated 2026-10-10 06:21. Everything project-specific travels with the repo: `CLAUDE.md`, `.claude/skills/`, `.claude/settings.json` (shared allow/deny list), `notes/`, `TODO.md`. **Don't run `/init`**: it overwrites `CLAUDE.md`. Only the tools and the personal permission list below are per machine.

## 1. Clone and tools (PowerShell)

```powershell
winget install Git.Git GitHub.cli astral-sh.uv OpenJS.NodeJS.LTS   # skip what's installed; Node 22 or newer
cd C:\Users\$env:USERNAME\kodi
git clone https://github.com/noiseparty/hakatons.git
cd hakatons
gh auth login                                   # GitHub.com, HTTPS, browser; needed for PRs and the todo skill
uv python install 3.12
uv run --no-project --with playwright python -m playwright install chromium   # for parbaude.py / ekrani.py / video.py
uv run --no-project --python 3.12 --with quickjs src/meklesana/testi.py       # smoke test: classifier tests pass
claude
```

Node is only needed for `node --check` on `production/*.js` in the merge checklist (and Node 24 + pnpm for the kit's Astro site, which we don't use).

## 2. Permissions (user level, once per PC)

In Claude Code: `/permissions` → Allow → add each rule → choose **User settings**:

```
Bash(python *)
Bash(python3 *)
Bash(node *)
Bash(npx *)
Bash(tesseract *)
Bash(gh pr merge *)
Bash(gh pr edit *)
Bash(git merge *)
Bash(git worktree *)
Bash(git push -u origin noiseparty/*)
Bash(git push origin HEAD:noiseparty/*)
Bash(curl *)
WebFetch(domain:*)
```

Or paste them into `%USERPROFILE%\.claude\settings.json` (merge with what's there):

```json
{
  "permissions": {
    "allow": [
      "Bash(python *)", "Bash(python3 *)", "Bash(node *)", "Bash(npx *)", "Bash(tesseract *)",
      "Bash(gh pr merge *)", "Bash(gh pr edit *)", "Bash(git merge *)", "Bash(git worktree *)",
      "Bash(git push -u origin noiseparty/*)", "Bash(git push origin HEAD:noiseparty/*)",
      "Bash(curl *)", "WebFetch(domain:*)"
    ]
  }
}
```

If `/permissions` rejects `WebFetch(domain:*)`, add plain `WebFetch` (all domains) instead. The repo's deny list still blocks force-push, pushes to `main`, `git reset --hard` and reading `.env` / `dati/`. Then press **Shift+Tab** until the footer shows **auto mode**: fewer prompts, but the classifier still stops VPS writes and force-pushes.

Optional personal settings (sounds on Stop/Notification, context status line, model) are in the main PC's `~/.claude/settings.json`; they don't matter for the repo.

## 3. Terminals and worktrees

One orchestrator plus up to five worker terminals. Each terminal works in its own worktree, so the terminals never share a checkout:

```powershell
cd C:\Users\$env:USERNAME\kodi\hakatons
git fetch origin
git worktree add ..\hakatons-<topic> -b noiseparty/<topic> origin/main
cd ..\hakatons-<topic>; claude          # then: /rename terminal A   (… B, C, D, E; the main one: /rename orchestrator)
git worktree remove ..\hakatons-<topic> # after the PR is merged
```

## 4. Orchestrator brief (paste into the orchestrator session)

> You are the orchestrator for the map.repo.lv hackathon repo. Rules (CLAUDE.md "Multi-session"):
> 1. Split the work into independent tasks, one per terminal (A–E). Each task gets one branch from `origin/main` and says up front which shared lines it touches (`karte_api.py` `MARSRUTI`/`main()`, end of `shema.sql`, `index.html`, `app.js`, `sw.js` VERSION).
> 2. Every terminal (and you, for your own queue) hands its brief **verbatim to ONE background Agent** (`isolation: "worktree"`, fresh context), waits, and relays only "PR number + ≤ 5 lines". Contexts stay small; nobody does the work in the terminal itself.
> 3. The owner opens the PR (body: what, tested / not tested, shared lines, "VPS steps"). **The orchestrator merges; there are no reviews.** Never merge another session's work you haven't checked with the list below.
> 4. VPS steps (schema, loaders, systemd, Caddy, `map.env`) are written in the PR body; **only the user runs them**. No emails, no force-push, no load on map.repo.lv (single curls are fine).
> 5. Merge procedure for PR N:
>    - In a temp worktree: `git fetch origin`, check out the PR branch, `git merge origin/main` (ordinary merge, keep both sides of appended lines). For `sw.js`, take main's block and set a fresh VERSION.
>    - `grep -rl '^<<<<<<<' production src notes TODO.md` must print nothing.
>    - `node --check` on every `production/*.js`.
>    - `sw.js` VERSION is unique (differs from main), and `uv run --no-project --python 3.12 src/testi/sw_faili.py --parbaudit` passes.
>    - Commit, push to the PR branch, `gh pr merge N --squash --delete-branch`.
>    - ~1 min later, from a clean worktree on `origin/main`: `uv run --no-project --python 3.12 --with playwright --with httpx src/testi/parbaude.py --url https://map.repo.lv`. If it's red, hotfix at once.
> 6. Anything that needs the user goes into the orchestrator chat, not only a worker terminal. Keep `notes/stavoklis.md` current after each batch.

## 5. How to start the morning (10 lines)

1. `cd C:\Users\$env:USERNAME\kodi\hakatons; git checkout main; git pull`
2. Read the top of `notes/stavoklis.md` (what merged, decisions, VPS steps).
3. `ssh root@161.97.105.130` → VPS steps 1–3 from `notes/stavoklis.md`.
4. `uv run --no-project --python 3.12 src/rits.py`: the table should be green (flood yellow = slow LVĢMC).
5. Make the three decisions (reports licence, flood-files licence, microphone).
6. Start `claude`, `/rename orchestrator`, paste the brief from §4.
7. Open terminals A–E only for real fixes; one worktree and one background agent each.
8. Real-phone pass (Android + iPhone) on the pitch path; `?svaigs=1` if a phone shows an old copy.
9. Rehearse with `slaidi.html` (N notes, T timer); backup video in `C:\Users\ZX202\kodi\demo-video\`.
10. Freeze `main` at T − 60 min; run `src/rits.py` once more.
