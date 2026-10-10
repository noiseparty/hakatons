# Plan for the final day (Saturday 2026-10-10)

Updated 2026-10-10 06:21. Everything up to #158 is merged. What happened overnight, the VPS commands and the decisions you need to make are in `notes/stavoklis.md` (top section).

Goal: win. In this order: **the pitch lands**, **the phone demo can't fail**, **every judging criterion is visibly ticked**, **the map looks calm**. Everything else is optional.

## Viena komanda no rīta

```powershell
cd C:\Users\ZX202\kodi\hakatons
uv run --no-project --python 3.12 src/rits.py            # soļi 1-4, 6, 7
uv run --no-project --python 3.12 src/rits.py --video    # + rezerves video (~2 min)
uv run --no-project --python 3.12 src/rits.py --soli 1,2 [--url https://map.repo.lv]
```

Soļi pa vienam, viens pārlūks, bez paralēlas slodzes; skripts neko nemaina. Beigās tabula (solis, rezultāts, sekundes, ko darīt, ja nav zaļš); exit 1 tikai pie KLUDA.

1. `git fetch` un vai checkout sakrīt ar origin/main (citā zarā: brīdinājums, nevis kļūda).
2. API: veseliba, bridinajumi, pludi (Ogre), udens, prognozes, celi un viena plūdu flīze; pludi `nepilnigi` vai 504 = dzeltens (LVĢMC lēns).
3. `src/testi/parbaude.py` (API fakti + demo ceļš 390×844 un 1280×800), ~2 min.
4. `src/demo/ekrani.py` slaidu kadri, tikai ja 2. solis redzēja īstu plūdu atbildi, citādi izlaists.
5. `src/demo/video.py` (tikai ar `--video`).
6. Klasifikatora testi (`src/meklesana/testi.py`).
7. VPS soļu saraksts no `TODO.md` (neatzīmētās "VPS…" rindas) un `notes/stavoklis.md` (sadaļa "VPS steps 1–3"), kopējams blokos; nekas netiek palaists.

## Morning plan (07:30 → pitch)

The pitch time isn't in the repo; check the organisers' schedule. T = pitch time.

| When | What | Done when |
|---|---|---|
| 07:30 | On the PC: `git checkout main; git pull`, then `uv run --no-project --python 3.12 src/rits.py --soli 1,2` (~1 min) | you see what's green before touching the VPS |
| 07:35 | **VPS steps 1–3** from `notes/stavoklis.md` (data refresh + timer, border key, Caddy), ~15 min. Start step 6 (flood warm-up) in the background right after | step 1 ends with `Gatavs.`; `curl -s https://map.repo.lv/api/veseliba` is `"ok":true` |
| 07:55 | Full check: `uv run --no-project --python 3.12 src/rits.py` (~5 min) | table all green, or only "pludi BRIDIN" (slow LVĢMC) |
| 08:05 | Make the three decisions (`notes/stavoklis.md` → "Risks and decisions"): reports licence, flood-files licence, microphone. Tell the orchestrator; it lands any text change as one PR | decisions written in TODO.md |
| 08:15 | Orchestrator merges what's still open (#157 print, and the running `demo-4`, `kartites-4`, `pitch-cels` if they're green). Set the freeze time = T − 60 min | `gh pr list` empty or parked |
| 08:30 | **Real phones** (Android Chrome + iPhone Safari): the pitch path, location allowed AND denied, open `?svaigs=1` once, one "Ziņot" up to the summary (submit only if you want), `?demo=vetra-2026`, `?demo=pludi-ogre`, `?demo=nakts` | no dead end; screenshots of anything odd go to a terminal |
| 09:00 | If `rits.py` step 2 shows a real flood answer: retake slides 02/03 (`uv run --no-project --python 3.12 --with playwright --with pillow src/demo/ekrani.py --tikai 02,03`) and the video (`uv run --no-project --python 3.12 src/rits.py --soli 5`), commit `production/slaidi/*.webp` in a PR | the slide shows "Plūdu riska zona", not a loading bar |
| 09:30 | **Rehearsal 1** with https://map.repo.lv/slaidi.html: ←/→ to move, **N** speaker notes, **T** timer (target 9:30), **F** fullscreen. Assign speakers per slide (problem + geolatvija / demo / AI + data + next) | under 10:00 |
| 10:15 | **Rehearsal 2**, with the live phone demo mirrored. Print backups: `https://map.repo.lv/slaidi.html?print` → PDF (13 pages), `info.html` once as a handout | PDF on the laptop and a USB stick |
| T − 60 | **Freeze `main`**: no merges (each merge is live in ~1 min). Run `src/rits.py` once more (it also warms the caches) | green table |
| T − 15 | On the demo phone, search "plūdi Mednieku iela 9 Ogre" once (warms the flood answer); open `statuss.html`; keep the `?demo=` bookmarks ready; slides open on the laptop. Backup video open in a tab: `C:\Users\ZX202\kodi\demo-video\demo-horizontals.mp4` (vertical: `demo-vertikals.mp4`, captions `captions.srt`) | everything open, phone charged, screen mirroring tested |
| T | Pitch | |

**If something breaks on stage:**
- An old copy on the phone: open `https://map.repo.lv/?svaigs=1`.
- A slow or broken live search: use `https://map.repo.lv/?demo=atskanot&ilgums=20` (hands-free replay of all 19 demos).
- The network fails: play the backup video.
- Flood shows "nav zināms": say "LVĢMC serviss šobrīd neatbild, mēs to pasakām godīgi" and move on.

## Judging criteria checklist (what the judges must see in 10 minutes)

| Criterion | Where it is shown | Status |
|---|---|---|
| 1 Concrete outcome | Decision block first in the card (flood zone yes/no at the address, or nearest place + one next action) | ✅ live (#139) |
| 2 Only once | Address from VZD or the phone; everything else from registers; source + licence on every place; 33 open + 2 ⚠ sources | ✅ live (the panel says 29 + 1 until VPS step 1) |
| 3 Flow 3–6 steps, summary, "what next" | 3-step strip (place → need → result); the card is the summary; "Kas notiks tālāk"; Ziņot is a 5-step flow with a summary before submit (#133) | ✅ live |
| 4 Works on a phone, no dead ends | Bottom sheet, 44 px targets, 387/387 cards without dead ends (#155), offline mode, `?svaigs=1` | ✅ emulated; real phones at 08:30 |
| 5 AI + open data | AI extracted 1 355 places (776 + 579) from 42 plans with page citations and found 41 coordinate errors; rule-based search 96 %; 33 open sources | ✅ slides 6–9 |

## Pitch (`notes/pitch.md`, `production/slaidi.html`)

- **Hook:** the 22–23 Aug 2026 storm left **~260 000 customers** without power (LSM / Sadales tīkls). The plan existed; nobody could use it.
- **geolatvija.lv 1.0 → 2.0:** 282 catalogue products vs one answer from the same official sources (tone: "rīks plānotājiem", VARAM is the organiser).
- **Demo:**
  - "plūdi Mednieku iela 9 Ogre" on the phone;
  - "cilvēks nav pie samaņas" → red "zvaniet 112";
  - 30 s of the demo panel (say "simulācija");
  - 10 s of statuss.html.
- **AI as auditor, not chatbot:** the Jūrmala assembly point "in Lithuania" (plan p. 85 vs the map).
- **Close:** a municipality gets its plan's errors on Monday morning; a resident gets one line, one answer.
