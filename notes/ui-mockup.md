# UI mock-up notes (user, 2026-10-10 ~03:10) — do these LAST

The user built two mock-ups with Google Stitch ("Krīzes karte · map.repo.lv Prototype") and gave these directions. UI element design comes after the night's feature work; the user is doing their own UI work locally in parallel.

## Mobile (liked, adopt the structure)

- **Bottom sheet over the map with snap points** `PEEK (140 px) · HALF (52 %) · FULL (84 %)`, the map stays visible above it. Matches what #60 (`apaksa.js`) already does; align the snap heights and show the three states as pills.
- **Both list and map visible at once**: in HALF the user sees the search bar, the chips and the top of the result while the map still shows the reference point, the flood zone circle and the nearest place markers.
- Sheet content order in the mock-up: search field with search icon → **chips** (Plūdi · Nav elektrības · Evakuācija · Patvertne · Ārsts · Ceļi …) → **tabs** `Rezultāts (Lēmums) · Kartes slāņi · Situācija tagad (LVĢMC)` → summary line "2 oranži · 5 dzelteni · Atjaunots šodien 14:05" → LVĢMC warning card (orange, "Spēkā līdz 12.10. 20:00") → the decision block with a label "APSTIPRINĀTS HIDRO-RISKS" and the verdict "Jūsu norādītā adrese **IR** plūdu riska zonā (1 % varbūtība gadā)" + address + distance to river → two small fact cards side by side (LVĢMC stacija: +2,42 m ▲ +18 cm, 24 h trend; Satiksmes ierobežojumi: Ceļš P5 slēgts, 3,2 km).
- Header: shield logo, "Krīzes karte · LATVIJA · MAP.REPO.LV", **LV / EN / RU toggle**, "Par datiem" button. Below it the red 112 line "Ja apdraudēta dzīvība vai veselība, zvaniet 112." as plain text.
- Map controls on the right: + − locate layers; basemap toggle "Karte | Reljefs" top-left.
- Accessibility and UX of this layout: good; "perhaps some elements might be changed".

## Desktop (concept OK, execution not yet)

- **Three columns**: left = search + result card ("Noskaidrojiet situāciju savā adresē", search field, "Izmantot manu atrašanās vietu", chips, "Kopējā situācija valstī: 2 oranži brīdinājumi · 5 dzelteni", then the LVĢMC card, the decision block, fact cards, "Tuvākās drošās vietas un atbalsts" list with distance, source line "Avots: Ogres novada CA plāns, 14. lpp." and "Maršruts ↗"); centre = map with legend box bottom-left ("Kartes leģenda & simboli"); right = **"Situācija tagad (Latvija)"** panel: hidrometeo brīdinājumi (LVĢMC), upju ūdens līmenis (pieaugums) with sparkline per station, satiksmes ierobežojumi (LVC DATEX II) — closable.
- Header: logo left, centre buttons "Meklēšana & Lēmums" / "Slāņu vadība", right "Par datiem & AI", LV/EN/RU; under it the 112 line and the orange warning strip "ORANŽS BRĪDINĀJUMS · LVĢMC: …" with "Aizvērt".
- Mock-up verdict from the user: "quite squeezed; the map is half visible; on widescreens it will look better; the layout is fine for the data preview; the map in the mock-up is a bad render; the elements are not so eye-catching or good-looking; in theory this could work."

## Open points to decide with the user before building

1. LV/EN/RU toggle appears in both mock-ups; tonight's decision was "no UI toggle, multilingual search only". Revisit when doing the UI.
2. Tabs inside the sheet (Rezultāts / Kartes slāņi / Situācija tagad) would replace today's separate layer panel and Prognoze panel on phones.
3. The right-hand "Situācija tagad" panel on desktop merges today's Prognoze feed, river gauges and LVC events into one column.
4. Element styling (cards, chips, pills, icons) is the part the user wants to improve; keep the structure.

Screenshots of the mock-ups are in the user's chat (not in the repo).
