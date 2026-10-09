# Plan for the final day (Saturday 2026-10-10)

Goal: win. That means four things in this order: **the pitch lands**, **the phone demo cannot fail**, **every judging criterion is visibly ticked**, **the map looks calm and professional**. Everything else is optional.

Updated 2026-10-10 02:09: batch 2 is mostly merged (`notes/stavoklis.md` has the list). The open work is below.

## Now → morning: land what's open

1. Merge in order as each is ready: #55 (status round 2, in review), #48 (zones, A), #53 (demo panel, D). Then B's "Datu avoti" PR and E's mobile bottom sheet. Hard-reload map.repo.lv on the phone after each merge.
2. **User on the VPS** (commands in `notes/stavoklis.md` → "VPS steps"):
   1. Run `shema.sql` once (meklejumi table, LVC avoti row, statuss constraint).
   2. Add the NAP keys to `map.env` and restart the API.
3. After the VPS steps, check:
   - `/api/meklejumi/top` returns 200;
   - `/api/celi` shows `konfigurets: true`;
   - statuss.html "Ceļu slēgumi" is green.
4. Fill the `?demo=[D]` placeholders in `notes/pitch.md` from #53. The codes are `vejs`, `vetra`, `drons`, `nakts`, `pludi-ogre`, `vetra-2026` and `bez-sakariem`. Note that the Ogre higher-ground threshold is **≥23 m**, not ≥15 m (see `notes/demo-scenariji.md`).
5. **Record a screen capture of the phone demo** as the backup for bad venue Wi-Fi.

## Freeze (1 h before the pitch)

- No merges after the freeze. Every merge is live within ~1 min.
- Warm the slow upstreams:
  - open map.repo.lv once (forecast cache);
  - search "plūdi Mednieku iela 9 Ogre" and the Jūrmala address (flood WMS, ~10 min cache);
  - open the zones layer on Ogre.
- Check statuss.html. Everything should be green or explained: flood yellow = slow upstream, roads grey = no keys.
- Two real phones (Android Chrome + iOS Safari), location allowed AND denied. Run the exact demo path plus 2 demo deep links.
- Backup video open in a tab, screenshots in the slides (Jūrmala plan p. 85 vs map; geolatvija.lv first screen).

## Mobile UI principles (for E's bottom sheet and any last polish)

- **Map first, chrome last.** On a phone the map takes ≥ 65 % of the viewport. One search field at the top, one floating action ("📍 tuvākie man"), results as a **bottom sheet** (collapsed: one line with the decision; half: list; full: details).
- **Result card = decision first.** First line is the verdict in plain words; facts and sources below; max 3 nearest places per layer; "Kas notiks tālāk" last.
- **Touch targets ≥ 44 px, text ≥ 16 px, contrast ≥ 4.5:1**; no hover-only interactions; no horizontal scroll.
- **Loading and errors are visible**: skeleton lines while the flood WMS answers; "nav datu" rows instead of silence.
- **Safe-area insets**, `100dvh` not `100vh`, `enterkeyhint="search"`.
- Desktop: map left, result card right (≈ 400 px), same components.

## Judging criteria checklist (what the judges must see in 10 minutes)

| Criterion | Where it is shown | Status |
|---|---|---|
| 1 Concrete outcome | Decision line in the result card (flood zone yes/no, nearest safe place with route) | ✅ live |
| 2 Only once | Address from VZD or the phone; everything else from registers; source + licence on every place | ✅ live; "Datu avoti" panel completion → B |
| 3 Flow 3–6 steps, summary, "what next" | Location → need → result; the card is the summary; "Kas notiks tālāk" block (#54). Say the sentence from `notes/pitch.md` slide 5 | ✅ live |
| 4 Works on a phone, no dead ends | Live phone demo; geolocation denied / API down paths show a next step; statuss.html shows each source's state | real-phone test still open; bottom sheet → E |
| 5 AI + open data | AI extracted 1 309 places from 42 plans with citations and found 41 errors; 18 open sources, each with licence (14 if #50/#51 weren't live) | ✅ pitch slides 6–7 |

## Pitch (`notes/pitch.md`)

- Hook: August 2026 storm, 277 000 households without power; the plan existed, nobody could use it.
- geolatvija.lv 1.0 → 2.0: a catalogue of 282 products vs one answer from the same official sources (tone: "rīks plānotājiem", VARAM is the organiser).
- Demo: "plūdi Mednieku iela 9 Ogre" on the phone; "cilvēks nav pie samaņas" → red "zvaniet 112" line; 30 s of the demo panel (2 scenarios, say "simulācija"); 10 s of statuss.html.
- AI as auditor, not chatbot: the Jūrmala "in Lithuania" point is the story. Show the PDF page and the map side by side.
- Close: what a municipality gets (its plan's errors on Monday morning) and what a resident gets (one line, one answer).
- Rehearse twice with a timer. Have the backup video open in a tab.

## Nice to have, only if the above is done

- Lightning item in the Prognoze feed.
- Server-side tile cache for the slow flood WMS.
- Sadales tīkls outage layer (needs permission; otherwise mention as next step).
- "Ziņot par bīstamību" community reports (lacukarte pattern, moderated).
- WCAG quick pass: labels, focus order, list view as map alternative (B's accessibility pass covers part).
