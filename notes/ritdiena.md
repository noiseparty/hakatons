# Plan for the final day (Saturday 2026-10-10)

Goal: win. That means four things in this order: **the pitch lands**, **the phone demo cannot fail**, **every judging criterion is visibly ticked**, **the map looks calm and professional**. Everything else is optional.

## Morning: ship what exists (first ~1.5 h)

1. Look at http://localhost:8080 (integration build) on a laptop and on a phone (same Wi-Fi, use the laptop's IP, or `ngrok`/`cloudflared` tunnel). Try the demo queries: "Ogre, plūdi", "Brīvības 15 Ogre", "nav elektrības Jelgavā", "cilvēks nav pie samaņas", "patvertne Rīgā".
2. OK the merges one by one: #33 → #34 → #35 → #36 → #37 → #38 → #32 → #31 (`notes/stavoklis.md` has the VPS steps per PR). After each merge: hard-reload map.repo.lv on the phone.
3. Terminal A loads the CA-plan points; check "Drošās vietas tuvumā" shows a real assembly point for Ogre.
4. Consolidated `TODO.md` pass; tear down the test DB and worktrees (terminal C).
5. **Record a screen capture of the phone demo** as the backup for bad venue Wi-Fi.

## Then: mobile UI polish (the biggest visible win)

Principles (from Leaflet/MapLibre practice, Google Maps, Apple Maps, 112-style apps, VDAA UX guidelines):

- **Map first, chrome last.** On a phone the map should take ≥ 65 % of the viewport. One search field at the top, one floating action ("📍 tuvākie man"), results as a **bottom sheet** that the user drags up (collapsed: one line with the decision; half: list; full: details). No sidebar on phones.
- **One primary action per screen.** Search → result card. Layer toggles, data sources, region filter go behind one "Slāņi" button, closed by default.
- **Result card = decision first.** First line is the verdict in plain words ("Jūs neesat plūdu riska zonā", "Tuvākā pulcēšanās vieta: Ogres stacija, 400 m"). Facts and sources below, collapsible. Max 3 nearest places per layer.
- **Markers:** one colour per group (shelters red, health purple, safety blue, water/environment teal), simple glyph icons, cluster at low zoom, never more than one visible layer group by default (shelters). Selected marker gets a larger pin; the map pans so the marker is above the sheet, not under it.
- **Touch targets ≥ 44 px, text ≥ 16 px, contrast ≥ 4.5:1**; no hover-only interactions; no horizontal scroll.
- **Loading and errors are visible**: skeleton lines in the card while the flood WMS answers; "nav datu" rows instead of silence.
- **Safe-area insets** (iPhone notch/home bar), `100dvh` not `100vh`, no 300 ms tap delay, address input `enterkeyhint="search"`, `inputmode` set.
- Basemap: OSM default; "Reljefs" only as a toggle. Keep attribution, but small.
- Desktop: map left, result card right (≈ 400 px), same components.

Concrete tasks (one terminal each, Opus for the sheet, Sonnet for the rest):
- Bottom-sheet results panel for phones (replace `#panelis` on < 768 px).
- Result card redesign: verdict line, grouped sections, source chips, collapsible details.
- Marker icon set + legend; selected-marker state; pan-to-above-sheet.
- Skeleton loading states; warm flood WMS cache for demo addresses.
- Real-phone pass: Android Chrome + iOS Safari, geolocation prompt, print/share.

## Judging criteria checklist (what the judges must see in 10 minutes)

| Criterion | Where it is shown | Status |
|---|---|---|
| 1 Concrete outcome | Verdict line in the result card ("zone yes/no", nearest safe place) | after #38 |
| 2 Only once | Address from VZD/phone, everything else from registers; data-sources panel with licences | yes |
| 3 Flow 3–6 steps, summary, "what next" | Search → result → "Kas notiks tālāk" + route/plan link. Say explicitly: one query replaces four screens; the card is the summary | add "Kas notiks tālāk" block to the card |
| 4 Works on a phone, no dead ends | Live phone demo; geolocation denied / API down paths show a next step | real-phone test |
| 5 AI + open data | AI extracted 1 309 places from 42 plans with citations and found 41 errors; 11 open datasets, each with licence | pitch slides 6–7 |

## Pitch (notes/pitch.md, PR #31)

- Hook: August 2026 storm, 277 000 households without power; the plan existed, nobody could use it.
- Demo path: Ogre floods on the phone, then "cilvēks nav pie samaņas" → red 112 line.
- AI as auditor, not chatbot: the Jūrmala "in Lithuania" point is the story. Show the PDF page and the map side by side.
- Open data slide: logos + licences; the shelters' missing licence as a call to action to VUGD.
- Close: what a municipality gets (a Monday-morning dashboard of its plan's errors) and what a resident gets (one line, one answer).
- Rehearse twice with a timer. Have the backup video open in a tab.

## Nice to have, only if the above is done

- LVĢMC warnings banner shown also in map mode (already in #38, verify).
- "Jūs" form in all scenario advice texts.
- Sadales tīkls outage layer (needs permission; otherwise mention as next step).
- WCAG quick pass: labels, focus order, list view as map alternative.
