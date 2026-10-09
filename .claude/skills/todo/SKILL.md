---
name: todo
description: >-
  Maintain the team task list in TODO.md (pending / in progress / done, with timestamps and who did
  what). Use when the user asks to add, claim, finish or review tasks, asks "what's left / what's
  done", and after completing any meaningful piece of work in this repo.
---

`TODO.md` at the repo root is the team's shared task log. Three people edit it on separate branches,
so keep edits small and line-based.

## Get the stamp first

Never guess the time or the person; run these:

```powershell
Get-Date -Format "yyyy-MM-dd HH:mm zzz"      # e.g. 2026-10-09 17:13 +03:00
gh api user --jq .login                       # GitHub username; if gh fails: git config user.name
```

(bash: `date "+%Y-%m-%d %H:%M %:z"`.) Use the GitHub username, not a real name or email.

## Format

One task per line, in exactly one section. Never delete lines, only move them between sections.

```markdown
## Pending
- [ ] Short imperative task — added 2026-10-09 17:13 +03:00 by noiseparty

## In progress
- [ ] Short imperative task — @krissjanis — added 2026-10-09 17:13 +03:00 by noiseparty; started 2026-10-09 18:00 +03:00

## Done
- [x] Short imperative task — done 2026-10-09 19:30 +03:00 by krissjanis (added 2026-10-09 17:13 +03:00 by noiseparty)
```

- **Add:** append to the bottom of `## Pending`.
- **Claim / start:** move the line to the bottom of `## In progress`, add `@<login>` and `started <stamp>`.
- **Finish:** move to the **top** of `## Done` (newest first), tick `[x]`, write `done <stamp> by <login>`,
  and keep the original `added …` in parentheses. Optionally append a PR/commit ref, e.g. `(#12)`.
- **Drop:** move to `## Done` as `- [x] ~~task~~ — dropped <stamp> by <login>: <reason>`.
- Keep descriptions to one line; put details in `notes/` and link them.

## When to update

- After finishing work in a session, mark the matching task done (add it as done if it wasn't listed)
  and add any follow-ups you discovered to Pending. Do this in the same commit/PR as the work.
- When the user asks "what's left", read TODO.md and summarise Pending and In progress by owner.

On a merge conflict in TODO.md, keep both sides' lines; then make sure each task appears only once,
in its latest state.
