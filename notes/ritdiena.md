# Plan for the final day (Saturday 2026-10-10)

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
7. VPS soļu saraksts no `TODO.md` (neatzīmētās "VPS…" rindas) un `notes/stavoklis.md`, kopējams blokos; nekas netiek palaists.

Goal: win. That means four things in this order: **the pitch lands**, **the phone demo cannot fail**, **every judging criterion is visibly ticked**, **the map looks calm and professional**. Everything else is optional.

Updated 2026-10-10 02:26. Almost everything is merged (`notes/stavoklis.md` has the list). Open: A traffic zones layer, B border feed + status rows, D real-phone matrix + backup video, E risk map.

## Now → morning: land what's open

1. Merge A, B, E as their PRs come (no reviews; owner merges main first). Hard-reload map.repo.lv on the phone after each merge.
2. **User on the VPS:** run `shema.sql` once (`meklejumi` table; commands in `notes/stavoklis.md`). Check `/api/meklejumi/top` returns 200.
3. D finishes the device matrix and the **backup screen video** (`C:\Users\ZX202\kodi\demo-video`). Fix whatever the real phones break, especially the bottom sheet on iOS Safari and the Android back button.
4. Print `info.html` once as a handout for the judges (optional, it shows "works without the internet").

## Freeze (1 h before the pitch)

- **One-command check** (morning and right before going on stage; also warms the caches): `uv run --no-project --python 3.12 --with playwright --with httpx src/testi/parbaude.py [--url https://map.repo.lv] [--screenshots ekr]` — API facts + demo path at 390×844 and 1280×800, red/green table, exit 1 on red.

- No merges after the freeze. Every merge is live within ~1 min.
- Warm the slow upstreams:
  - open map.repo.lv once (forecast cache);
  - search "plūdi Mednieku iela 9 Ogre" and the Jūrmala address (flood WMS, ~10 min cache);
  - open the zones layer on Ogre.
- Check statuss.html. Everything should be green or explained: flood yellow = slow upstream, border times grey/red = feed not available yet.
- Two real phones (Android Chrome + iOS Safari), location allowed AND denied. Run the exact demo path plus the 3 deep links `?demo=vetra-2026`, `?demo=pludi-ogre`, `?demo=nakts`.
- Backup video open in a tab, screenshots in the slides (Jūrmala plan p. 85 vs map; geolatvija.lv first screen).

## Mobile UI principles (for any last polish)

- **Map first, chrome last.** On a phone the map takes ≥ 65 % of the viewport; results in the bottom sheet (#60: peek / half / full).
- **Result card = decision first.** Verdict line, one primary action (route), facts and sources below, "Kas notiks tālāk" last.
- **Touch targets ≥ 44 px, text ≥ 16 px, contrast ≥ 4.5:1** (axe-core: 0 violations after #56); no hover-only interactions; no horizontal scroll.
- **Loading and errors are visible**: "nav datu" rows instead of silence.
- Desktop: map left, result card right (≈ 400 px), same components.

## Judging criteria checklist (what the judges must see in 10 minutes)

| Criterion | Where it is shown | Status |
|---|---|---|
| 1 Concrete outcome | Verdict line in the result card / bottom sheet (flood zone yes/no, nearest safe place with route) | ✅ live |
| 2 Only once | Address from VZD or the phone; everything else from registers; source + licence on every place; "Datu avoti" lists all 19 + 1 | ✅ live |
| 3 Flow 3–6 steps, summary, "what next" | Location → need → result; the card is the summary; "Kas notiks tālāk" (#54). Say the sentence from `notes/pitch.md` slide 5 | ✅ live |
| 4 Works on a phone, no dead ends | Bottom sheet (#60); geolocation denied / API down paths show a next step; statuss.html; info.html prints for offline | ✅ live; real-phone matrix → D |
| 5 AI + open data | AI extracted 1 355 places (776 + 579) from 42 plans with citations and found 41 errors; 19 open sources, each with licence | ✅ pitch slides 6–7 |

## Pitch (`notes/pitch.md`)

- Hook: August 2026 storm, **~260 000 customers** affected by power cuts (~245 000 at one moment on 23 Aug, LSM / Sadales tīkls); the plan existed, nobody could use it.
- geolatvija.lv 1.0 → 2.0: a catalogue of 282 products vs one answer from the same official sources (tone: "rīks plānotājiem", VARAM is the organiser).
- Demo: "plūdi Mednieku iela 9 Ogre" on the phone (bottom sheet); "cilvēks nav pie samaņas" → red "zvaniet 112" line; 30 s of the demo panel (2 scenarios, say "simulācija"); 10 s of statuss.html.
- AI as auditor, not chatbot: the Jūrmala "in Lithuania" point is the story. Show the PDF page and the map side by side.
- Close: what a municipality gets (its plan's errors on Monday morning) and what a resident gets (one line, one answer).
- Rehearse twice with a timer. Have the backup video open in a tab.

## Nice to have, only if the above is done

- Lightning item in the Prognoze feed.
- Server-side tile cache for the slow flood WMS.
- Sadales tīkls outage layer (needs permission; otherwise mention as next step).
- Riga public transport live: email Rīgas satiksme for a GTFS-RT licence (see `notes/demo-scenariji.md`).
- "Ziņot par bīstamību" community reports (lacukarte pattern, moderated).
- Offline mode (service worker + cached area data).
