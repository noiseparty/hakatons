# Handoff — terminal E (2026-10-10, parked)

**Done (merged or open):** #46 prognozes, #50 zibens/augsne, #54 Kas notiks tālāk + Jūs, #60 bottom sheet, #65 riska karte, #68 parbaude.py, #70 search suggestions/typos/voice, #75 noturības + simulated layers, #78 routes around zones, #80 share/print, #82 observations, #97 performance + OG, #108 icons/shapes, #109 blank-tap fix.
**Half-done (this branch, WIP, untested):** "Notīrīt" button in the search bar + shared status block for shelters/evacuation/accommodation/resilience points (`objekta-statuss.js`). The agent was stopped mid-way: check `git diff origin/main` here, finish, then test (Playwright 375 + 1280, parbaude.py, testi.py).
**Next steps:** finish the spec in the orchestrator's messages (Notīrīt: clear field, card, sheet, URL params, Demo.beigt(), layers back off, refocus; Esc in an empty field; statusaBloks: 5 flags "nav zināms" + shelters' ietilpība / ratiņkrēsls / dzīvnieki "nav norādīts", 6-h freshness).
**Pitfalls:**
- #108 (icons) was NOT on origin/main when this branch was cut (main top = #109). This WIP uses plain ✕, not `Ik()`. After #108 lands, merge main and switch to `Ik('aizvert')`. Add the sprite id via `src/ikonas/spraits.py` (Lucide 'x'), and add no emoji: parbaude.py flags them.
- `production/sw.js` VERSION must change whenever its SHELL list changes; new JS files go into SHELL_FAILI.
- Sprite ids are Latvian (`brid`, `vejs`, `pludi`, `vieta`, `uzmanibu`…); see the comments in `ikonas/ikonas.svg`.
- Layers start OFF on load; tests must enable them first. The LVĢMC flood WMS can hang, so wait for `load`, not `networkidle`.
- `/api/pludi` may answer 202 while still checking.
