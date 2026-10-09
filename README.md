# hakatons

Team repo for the **AI Open Data 2026 hackathon** — track: **crisis prevention**.

## Layout

| Path | What |
|---|---|
| `ai-open-data-2026-hakatons/` | Hackathon data, copied from [lata-org/ai-open-data-2026-hakatons](https://github.com/lata-org/ai-open-data-2026-hakatons). Treat as **read-only** — see `UPSTREAM.md` for the source commit. |
| `ai-open-data-2026-hakatons/ca-plani-hakatons/` | Civil protection plans (CA plāni) — main dataset for our track. |
| `src/` | Our code. |
| `notes/` | Ideas, research, pitch notes. |

## Getting started

```bash
git clone https://github.com/noiseparty/hakatons.git
cd hakatons
```

## Working together (3 people)

1. **Never commit straight to `main`.** Pull first, then branch:
   ```bash
   git switch main
   git pull
   git switch -c <your-name>/<short-topic>    # e.g. rihards/shelter-map
   ```
2. Commit small and often; push your branch:
   ```bash
   git add -A
   git commit -m "Add shelter map prototype"
   git push -u origin HEAD
   ```
3. Open a Pull Request on GitHub; a teammate gives a quick look and merges.
4. After a merge, everyone runs `git switch main; git pull` and rebases/merges into their branch.

Tips to avoid merge conflicts:
- Split work by folder/file — say in chat who's touching what.
- Don't edit files under `ai-open-data-2026-hakatons/`; write derived data into `src/` or `notes/`.
- Never commit secrets (API keys go in `.env`, which is gitignored; share a `.env.example`).

## Claude Code

- `CLAUDE.md` (shared, committed) — project context for everyone's Claude sessions.
- `CLAUDE.local.md` and `.claude/settings.local.json` — personal, gitignored.
