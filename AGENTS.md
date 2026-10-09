# AGENTS.md

Instructions for AI coding agents (Mistral, Codex, Copilot, Cursor, …) working in this repo.
Claude Code reads `CLAUDE.md`; everyone else starts here.

## Before you do anything

1. Read `README.md` → **"Working together"**: the git workflow and the `TODO.md` format. Follow it exactly.
2. Read `CLAUDE.md` for project context (hackathon track, data kit layout, commands). It applies to all agents.
3. Read `TODO.md` to see what is pending, in progress and done.

## Saving and updating (preferred — teammates are not git experts)

- User says "save", "commit", "push", "upload" or similar → run
  `powershell -NoProfile -ExecutionPolicy Bypass -File easy\save.ps1 "<one-sentence summary of the work>"`.
  It branches, commits, rebases on `main`, logs the task in `TODO.md`, opens a PR and merges it.
- User says "update", "get latest", "pull" → run
  `powershell -NoProfile -ExecutionPolicy Bypass -File easy\update.ps1`.
- If a script prints a red error (e.g. a merge conflict), explain it in plain words and help fix it.
- Don't run the `.cmd` files yourself: they wait for a keypress.

## Hard rules

- `main` is protected. `git push` to `main` is rejected. Work on a branch `<github-username>/<topic>`,
  push it, then `gh pr create --fill` and `gh pr merge --squash --delete-branch`. No approval needed.
- Never force-push, rewrite `main`'s history or delete `main`.
- Update `TODO.md` in the same PR as the work: real timestamp (`Get-Date -Format "yyyy-MM-dd HH:mm zzz"`)
  and the GitHub username (`gh api user --jq .login`). Never guess either.
- Don't edit `ai-open-data-2026-hakatons/` (vendored, read-only). Our code goes in `src/`, notes in `notes/`.
- The repo is public: never commit secrets. Keys go in `.env` or `dati/` (both gitignored).
