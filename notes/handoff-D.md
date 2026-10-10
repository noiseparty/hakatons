# Handoff, terminal D → next session (noiseparty/ui-mobile, WIP, 2026-10-10 ~04:00)

**Done (phone ≤ 800 px only; desktop unchanged and checked):**
- `apaksa.js`: the sheet is always visible on phones; snap 140 px / 52 % / 84 %; pills Mazs/Puse/Pilns; `#apaksa-meklet` slot; the verdict line falls back to the LVĢMC summary.
- `sheet.js` (new):
  - moves `#meklet-forma`, `#panelis`, `#statuss` and `#prognozes` into the sheet on phones and back on desktop;
  - topic chips; summary line from `/api/bridinajumi`;
  - tabs Rezultāts / Kartes slāņi / Situācija tagad (forecast feed + 5 gauges from `/api/udens` + LVC events from `/api/celi`, around the map centre).
- `index.html`: shield logo, subtitle, "Par datiem" → `statuss.html` (LV/EN/RU only as a comment), 112 line, `#slani-poga`, `sheet.js`. `sw.js` VERSION `2026-10-10d-lapa` + `sheet.js` in the shell list.
- `stils.css`: phone block at the end. Map controls: Karte|Reljefs top-left; layers and ◎ first on the right; the Demo tab on the left edge. One-line banners.
- `src/testi/parbaude.py`: the demo step waits for `domcontentloaded` + the card (not networkidle), so `?demo=pludi-ogre` takes 2.5 s.

**Half-done / red in `parbaude.py` (phone):** the "Prognoze", "Riska karte" and "Datu avoti" steps time out. They click `.prog-poga` and `#panelis-poga`, which on phones now live in the sheet tabs. Update those steps to use `#cilne-situacija` / `#cilne-slani`, or keep visible proxies. The `/api/pludi` Jūrmala 202/25 s is server-side.

**Next 3 steps:**
1. Fix those 3 parbaude steps, then re-run: `uv run --no-project src/demo/lokali.py --port 8091` + `parbaude.py --url http://127.0.0.1:8091`.
2. Apply the user's Stitch reference (`notes/mockup/mobile.*`) and the shared CSS variable names from A (`--zils-primars`, `--pelks-1/2/3`, `--sarkans`, `--dzeltens-tumss`, `--zals`, `--radiuss-karte`, `--radiuss-pogas`): warning card, decision block, fact cards, skeleton loading.
3. Native drag: velocity snap, rubber-band, inner scroll only in FULL. Safe-area insets. In HALF, fitBounds must keep the reference point and nearest place above the sheet (`atstarpes()` in `demo.js`, `zimetKarte()` in `meklesana.js` → paddingBottomRight = `Apaksa.augstums()`).

**Pitfalls:**
- Bump `sw.js` VERSION when the SHELL list changes.
- Playwright on localhost needs `service_workers="block"`, or `sw.js` bypasses the `/api` proxy and everything 404s.
- The LVĢMC WMS must start after `load` (`demo.js` already does this).
- `data-darbiba="saraksts"` is owned by `saraksts.js`.
- Don't touch icons (E) or `meklesana.js` (A).
- Screenshots: `C:\Users\ZX202\kodi\ui-mobile-ekr\`.
