# Easy mode — no git knowledge needed

You only need **two buttons**: `update` and `save`. They live in this `easy` folder.

## One-time setup (about 5 minutes)

1. Press the **Start** button, type `PowerShell` and open it.
2. Copy this line, paste it into PowerShell (right-click pastes) and press **Enter**:
   ```
   irm https://raw.githubusercontent.com/noiseparty/hakatons/main/easy/setup.ps1 | iex
   ```
3. If Windows asks "allow this app to make changes?", click **Yes**.
4. When it asks you to log in to GitHub: copy the code it shows, press **Enter**, paste the code in the
   browser that opens and click **Authorize**.
5. Done. A `hakatons` folder appears on your Desktop. That's the project — work in there.

## Every day

| When | Double-click | What it does |
|---|---|---|
| Before you start working | `easy\update.cmd` | Gets your teammates' latest work. |
| Whenever you finish something (or every hour) | `easy\save.cmd` | Asks "What did you do?" — type one sentence. Your work goes to GitHub, joins the shared version, and is logged with time + your name in `TODO.md`. |

That's it. Save often: small saves almost never clash with teammates.

## If something goes wrong

- A **red message** means it stopped safely. **Nothing is lost.** Read the message — usually it tells
  you what to do — or ask your AI assistant or a teammate.
- "Nothing to save" just means you haven't changed anything since your last save.

## Working with an AI assistant (Mistral, Claude, …)

Open the `hakatons` folder in your AI tool. It reads `AGENTS.md`, which tells it the rules. You can say:

- "Get the latest changes" → it runs `easy\update.ps1`
- "Save my work: added shelter map" → it runs `easy\save.ps1 "added shelter map"`
- "What's left to do?" → it reads `TODO.md`
