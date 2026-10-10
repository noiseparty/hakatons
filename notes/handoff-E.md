# Handoff — terminal E (2026-10-10, parked)

**Done (merged or open):** #46 prognozes, #50 zibens/augsne, #54 Kas notiks tālāk + Jūs, #60 bottom sheet, #65 riska karte, #68 parbaude.py, #70 search suggestions/typos/voice, #75 noturības + simulated layers, #78 routes around zones, #80 share/print, #82 observations, #97 performance + OG, #108 icons/shapes, #109 blank-tap fix.
**Finished (this branch, PR open, not merged):** "Notīrīt" button in the search bar (sprite `aizvert`, Esc in an empty field) + shared status block `ObjektaStatuss.statusaBloks` for shelters / evacuation / accommodation / resilience points. Merged main up to #111; sw.js VERSION `2026-10-10h-notirit`.
**Next steps:** none for this feature. Notīrīt does not call `Apaksa.aizvert` (does not exist; the sheet follows `#rezultati` hidden). Region filter is reset without `radtRegionu()` so the map view stays. Overlay toggles are cleared generically (`.kat.parklajums input:checked` + `change` event), so new overlay layers are covered automatically.
**Pitfalls:**
- #108 (icons) is merged; the button uses `<svg class="ik"><use href="ikonas/ikonas.svg#aizvert">`, no emoji.
- `production/sw.js` VERSION must change whenever its SHELL list changes; new JS files go into SHELL_FAILI.
- Sprite ids are Latvian (`brid`, `vejs`, `pludi`, `vieta`, `uzmanibu`…); see the comments in `ikonas/ikonas.svg`.
- Layers start OFF on load; tests must enable them first. The LVĢMC flood WMS can hang, so wait for `domcontentloaded` (even `load` timed out with `?q=plūdi Ogrē`), not `networkidle`.
- `/api/pludi` may answer 202 while still checking.
