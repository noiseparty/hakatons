# Claude Code on a new machine (same setup as the main dev PC)

Everything project-specific travels with the repo. Only a few personal settings live outside it.

## 1. What `git clone` already gives you

| In the repo | What it does |
|---|---|
| `CLAUDE.md` | Project context, product description, commands, team and multi-session rules. Claude reads it automatically. **Don't run `/init`**: it overwrites this file with a generic one (that's what happened on 2026-10-09 on the second PC: `/init` in a folder without the repo produced an empty file). |
| `AGENTS.md` | Same for non-Claude agents (Mistral, Codex, Cursor…). |
| `.claude/skills/` | Project skills: `todo` (TODO.md rules), `vdaa-epakalpojumi` (VDAA e-service guidelines), `celu-kartes-datubaze` (LVC road DB). They point into the kit, so they work after clone. |
| `.claude/settings.json` | Shared permission allowlist (git, gh, uv, pnpm, curl to map.repo.lv…) and deny list (force-push, ssh, secrets). Fewer prompts on every machine. |
| `notes/` | Research, pitch, state of the work (`stavoklis.md`), plan for the last day (`ritdiena.md`). |
| `TODO.md` | Shared task log. |

So on a new PC:

```powershell
git clone https://github.com/noiseparty/hakatons.git
cd hakatons
gh auth login          # once; needed for PRs and for the `todo` skill (gh api user)
claude                 # Claude Code reads CLAUDE.md + .claude/ from here
```

Tools the commands in `CLAUDE.md` expect: `git`, `gh`, `uv` (Python), `pnpm` + Node 24 (only for the kit's Astro site), Playwright via `uv`/`npx` for 375 px tests. Nothing else.

## 2. Personal settings (not in git): `~/.claude/settings.json`

Copy what you want from the main PC's user settings. The parts that matter for this project:

```json
{
  "model": "fable",
  "effortLevel": "xhigh",
  "modelSettings": { "claude-fable-5-1": { "effortLevel": "medium" } },
  "hooks": {
    "Stop": [{ "hooks": [{ "type": "command", "shell": "powershell",
      "command": "(New-Object Media.SoundPlayer 'C:\\Windows\\Media\\chimes.wav').PlaySync()" }] }],
    "Notification": [{ "hooks": [{ "type": "command", "shell": "powershell",
      "command": "(New-Object Media.SoundPlayer 'C:\\Windows\\Media\\notify.wav').PlaySync()" }] }]
  },
  "statusLine": { "type": "command",
    "command": "powershell -NoProfile -Command \"$j = [Console]::In.ReadToEnd() | ConvertFrom-Json; $ctx = $j.usedContextPercent; $n = [math]::Floor($ctx/10); $bar = [string]::new([char]0x2588, $n) + [string]::new([char]0x2591, 10 - $n); Write-Host \\\"$bar ${ctx}% context\\\"\"" }
}
```

Hooks and status line are optional. The main PC also has voice mode on (`/voice`) and no plugins that matter for this repo.

Per-machine, gitignored: `.claude/settings.local.json` (extra personal permissions), `CLAUDE.local.md` (personal notes), `~/.claude/projects/<repo>/memory/` (Claude's own memory; it does not sync, which is why the project facts are in `CLAUDE.md` and `notes/` instead).

## 3. Working with several terminals

Open 2–4 terminals in the repo (or one per git worktree: `git worktree add ..\hakatons-<topic> -b noiseparty/<topic>`), run `claude` in each, and name them with `/rename orchestrator`, `/rename terminal A`, …. Sessions on the same machine can see and message each other (`ListAgents`, `SendMessage`). The rules that worked are in `CLAUDE.md` → "Multi-session". Model guidance: Opus 5.5 for building, Sonnet 5.5 for routine edits, Haiku 5.5 for exploration, at most ~5 agents at once.
