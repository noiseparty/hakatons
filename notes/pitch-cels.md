# Pitch path walkthrough (2026-10-10 06:00–06:30, after ~45 merges)

The exact demo path from `notes/pitch.md` §5, walked as the presenter will:

- phone 390×844, DPR 3, touch, `lv-LV`, Europe/Riga
- desktop 1920×1080

Geolocation was granted and **simulated** at Ogre centre (56.8162, 24.6140), so no real location appears anywhere.

## Runs

- **Local:** `production/` from this branch. `/api/*` was faked from recorded fixtures: 456 responses, each URL fetched from map.repo.lv at most once and then replayed. Fixture misses (a new map bbox, flood tiles) return 503. Those are fake-server artefacts and are not counted as errors. The walk ran on the phone and on desktop, before and after the fixes, and again after `git merge origin/main`.
- **Live:** one sequential phone walk against https://map.repo.lv with one browser, no retries. Ziņot stopped at the summary and no report was submitted. The walk did not block the anonymous search-count POST `/api/meklejumi`, so the live pass added about 6 searches to "Biežāk meklētais". `src/testi/parbaude.py` blocks that POST, and this walk should too next time.

Script and screenshots live outside the repo: `%TEMP%\pitch-cels\skripti\cels.py` (checks reused from `src/testi/parbaude.py`), `%TEMP%\pitch-cels\{lokali7,lokali6,live}\*.png`. Screenshot names are `<ierice>_<nr>_<solis>.png`.

## What each step checks

- No JS errors (`pageerror`, console errors, HTTP ≥ 400).
- No `tel:` links.
- No "undefined", "null", "NaN" or "[object Object]" in visible text.
- No "tu/tev" forms and no emoji.
- No horizontal scroll.
- No clipped text: overflow hidden, ellipsis or line-clamp with the content bigger than the box, or text past the right edge.
- The decision block (`#rez-galvenais` / `.draudi`) is fully inside the viewport.
- Phone tap targets are at least 44 px.

## Result

| # | Step | Phone (live) | Desktop (local) | Screenshot |
|---|---|---|---|---|
| 1 | Fresh load → first-visit chips | OK: 3 chips "Ogre, plūdi", "nav elektrības Rēzekne", "cilvēks nav pie samaņas". The theme row scrolls sideways ("Ārsts" past the edge; this is intended) | OK | `telefons_01_svaiga-iel-de-pirm-skata-ipi.png` |
| 2 | "Ogre, plūdi" (chip): decision first, step strip | OK: step 2 "Atbilde" active, decision "Plūdu riska zona: Nē" above the fold, LVĢMC warning (dzeltens, vējš) in the banner and the card. **Issue:** the map centre (Ogre) sits at the top edge of the "Puse" sheet, so the map shows Kalnāji/Aizupes and Ogre is hidden (see TODO) | OK | `telefons_02_ogre-pl-di-l-mums.png` |
| 3 | 24 h, gauge with threshold, assembly point with "izvilkts ar MI", route links | OK: "Nākamās 24 h (Ogre) … bez būtiskiem riskiem", gauge "Ogre (1,9 km): 56 cm, 24 h ↑ +1 cm" with threshold text, assembly point "Ogres pilsētas dzelzceļa stacija · 812 m" with "izvilkts ar MI … lpp. 121", Google Maps / Waze / OSM | OK | `telefons_03_…`, `telefons_04_…` |
| 4 | "Brīvības iela 12, Ogre, plūdi" | OK: VZD address, "Plūdu riska zona: Nē … (10 %, 1 % un 0,5 % kartes)", stored LVĢMC answer with its time. The LVĢMC banner is cut to one line with "…" (it is a `<details>`, and tapping it opens the full text) | OK | `telefons_05_…` |
| 5 | "cilvēks nav pie samaņas" | OK: red "Zvaniet 112 tūlīt" block at the top of the card, no button or link, nearest 24/7 "Ogres rajona slimnīca · 1,2 km". The location button is not shown because the place is already known from step 4; tapping "Rādīt tuvākos man" keeps the same answer | OK | `telefons_06_…`, `telefons_07_…` |
| 6 | RU "нет света Резекне" | OK: card in Russian, Rēzekne, nearest resilience-point candidate 359 m, advice "на латышском языке (официальный источник)" | OK | `telefons_08_…` |
| 7 | Ziņot 1→4/5 (summary, not sent) | OK: 1 type → 2 "Kur?" → (my location) 3 → 4 summary with "Labot" and data sources, "Nosūtīt" present but not pressed. **Fixed:** "Izmantot manu atrašanās vietu" in step 2 was 41 px tall | OK | `telefons_09…12_…` |
| 8 | Saraksts (Patvertnes) | OK: "10 vietas skatā", layer chips including Patvertnes, source and licence on each row. **Fixed:** layer chips were 40 px tall | OK | `telefons_13_…` |
| 9 | Datu avoti → "Kā tas tapa" | OK: 29 sources, the "Kā tas tapa" block (MI story) | OK | `telefons_14_…` |
| 10 | Prognoze tab + risk map (šodien) | OK: phone tab "Situācija tagad" (LVĢMC observation, risk-map item), legend "paaugstināts / augsts / ļoti augsts". Desktop: the "Prognoze" pill is hidden while the "Slāņu vadība" drawer is open; close the drawer first (see TODO) | OK after closing the drawer | `telefons_15_…`, `telefons_16_…`, `dators_15_prognoze.png` |
| 11 | `?demo=vetra-2026`, 2 steps | OK: SIMULĀCIJA badges (9), Bauska zones, "Atskaņot visus pēc kārtas". Clipped on live: the demo header title `b.demo-galvene-nos` (244 > 195 px) and the red simulated banner summary (ellipsis, `<details>`). Left alone because demo.js is owned by another session (TODO) | OK | `telefons_17_…`, `telefons_18_…` |
| 12 | info.html, radio map | OK: LR1 map present (SVG with title and description) | OK | `telefons_19_…` |
| 13 | statuss.html | OK. The page honestly shows "Nedarbojas: Robežu gaidīšanas laiks" (border waiting times source) | OK | `telefons_20_…` |
| 14 | Offline reload | OK: SW controls the page, "Nav interneta — rādām pēdējos saglabātos datus", saved card "Saglabāts rezultāts (…)", last-results buttons. **Fixed:** those buttons were 28 px tall | OK | `telefons_21_…` |

Live and local gave the same answers at every step. There were no JS errors, no `tel:` and no undefined/null/NaN on either device.

## Fixed in this PR (production/stils.css only)

- `.saraksts-cips`: `min-height` 40 → 44 px (Saraksts layer chips).
- `.bezsakaru button`: `min-height: 44px` (offline bar "Pēdējie rezultāti" buttons, were 28 px).
- `.zinot-saturs button.otra`: `min-height: 44px` (Ziņot step 2 "Izmantot manu atrašanās vietu", was 41 px).

## Left as TODO

- Phone: after "Ogre, plūdi" (and on first load with geolocation) the place the answer is about lies under the top edge of the "Puse" sheet. The map should centre the point in the visible area above the sheet (sheet.js / meklesana.js map fit). Popup placement is being changed by another session right now.
- Desktop: the "Prognoze · N" pill and the "Šodien / Rīt" risk switch are hidden while the "Slāņu vadība" drawer is open. Presenter: close the drawer before showing the forecast.
- Demo (demo.js/demo.css, another session): the phone demo header title `b.demo-galvene-nos` is clipped ("Vētra 22.–23.08.2026 (atkārtoj…").
- Desktop 1920 px: the search placeholder is cut at "Kas Jums vajadzīgs? P…" because the input sits next to the mic and "Meklēt" buttons. Cosmetic.
