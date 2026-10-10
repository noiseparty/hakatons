# Pieejamība (2026-10-10)

Second accessibility pass (the first one, 2026-10-10 02:09, added focus rings, contrast fixes, aria-hidden icons, reduced
motion in CSS and Escape on the forecast panel). This pass: automated axe-core run on every page and the main states,
keyboard-only walk, and the open TODO item "on phones the map comes before the panel visually but after it in Tab order".

Method: Playwright (Chromium) + `@axe-core/playwright`, tags `wcag2a wcag2aa wcag21a wcag21aa best-practice`, viewports
375 × 740 (mobile emulation, touch) and 1280 × 800, local server `src/demo/lokali.py`. `/api/*` answers fetched once and
then replayed from disk (no load on map.repo.lv); map tiles and the flood WMS blocked, so axe saw no background images.
Scripts: `src/testi/pieejamiba/axe.mjs` and `tastatura.mjs` (how to run: comment at the top of each).

## axe-core: violations (affected elements) before → after

| Page / state | 375 before | 375 after | 1280 before | 1280 after |
|---|---|---|---|---|
| index: empty | 1 moderate | 0 | 1 moderate | 0 |
| index: "Ogre, plūdi" result card | 2 moderate | 0 | **2 serious** + 1 moderate | 0 |
| index: popup opened from Saraksts | 2 moderate | 0 | **2 serious** + 1 moderate | 0 |
| index: Saraksts dialog | 0 | 0 | 0 | 0 |
| index: Datu avoti panel | 1 moderate | 0 | 1 moderate | 0 |
| index: Ziņot step 1 | 0 | 0 | 0 | 0 |
| info.html | 0 | 0 | 0 | 0 |
| statuss.html | 0 | 0 | 0 | 0 |
| trukstosie.html | 0 | 0 | 0 | 0 |
| slaidi.html | 9 moderate | 0 | 7 moderate | 0 |

No critical violations before or after. What they were:

- **serious, color-contrast** (desktop card): source lines (`.avots-rinda`, e.g. "Avots: …" under advice) `#78716c` on the
  card grey `#eef2f6` = 4.26:1. Same hue, darker: `#6d6762` (4.96:1 on `#eef2f6`, 5.58:1 on white).
- **moderate, region**: the "zvaniet 112" line (phone `.zvanit-josla`, desktop `.dv-112`) was outside any landmark → now
  `role="region" aria-label="Ārkārtas palīdzība"`.
- **moderate, heading-order** (phone): in the bottom sheet the card's `h3` came straight after the page `h1` (the
  "Meklēšanas rezultāts" `h2` stays in the hidden desktop panel) → hidden `h2` in the sheet's Rezultāts and Situācija tabs.
- **slaidi.html**: no `main`, no `h1` on the first slide → slides wrapped in `main`, visually hidden `h1`.

## Keyboard and screen reader changes (not visible to axe)

New `production/pieejamiba.js` (loaded right after Leaflet, before app.js), plus small edits:

- **Tab order on the phone**: the bottom sheet (search + result card) was the last element in the DOM, so Tab went
  header → every map control → sheet. The sheet now sits before `<main>` in the DOM (it is `position: fixed`, so nothing
  moves visually; its z-index went 1000 → 1001 to stay above the Leaflet controls). Order now: skip links → header →
  sheet (handle, Mazs/Puse/Pilns, search, topics, tabs, card) → map → map buttons. Desktop already had search → card → map.
- **Skip links** "Uz meklēšanu" / "Uz karti" (first Tab stop, hidden until focused).
- **Map markers are not Tab stops** (`L.Marker` `keyboard: false`): hundreds of icons each took a Tab press. Every
  marker is reachable through **Saraksts** (layers panel and the result card) → "Rādīt kartē".
- **Popup opened from the keyboard** (Saraksts, card rows): focus moves into the popup, Escape closes it and focus goes
  back to where it came from; the Leaflet close button gets a Latvian label ("Aizvērt logu").
- **Bottom sheet in "Pilns"** (84 % of the screen) is `role="dialog" aria-modal="true"`: Tab cycles inside it, Escape
  drops it to "Puse" and focuses the handle. In Mazs/Puse it stays a `region` and the map is reachable.
- **Reduced motion**: CSS already turned off transitions; now Leaflet also pans/zooms/flies without animation when the
  system asks for less motion (`prefers-reduced-motion: reduce`).
- Warning banner: explicit `aria-live="polite"` next to `role="status"`; the result card already had it.
- Already fine and unchanged: labels on icon-only buttons (#, Ziņot, Notīrīt, Runāt, locate, layers, zoom, sheet handle
  with the verdict in its label), native `<dialog>` for Saraksts / Ziņot / Kas jauns / Par datiem (focus trap + Escape
  built in), visible 3 px focus ring.

Keyboard walk (`tastatura.mjs`, both viewports, with `reducedMotion: reduce`): skip links work; search field before
map; no marker is a Tab stop; Enter on "Ogre, plūdi" → card (aria-live) → Tab to "Saraksts" → "Rādīt kartē" → focus in
popup → Escape closes it → focus back on "Saraksts"; phone sheet "Pilns" keeps focus inside and Escape → "Puse"; no
`tel:` links; no JS errors. Classifier tests (`src/meklesana/testi.py`) unchanged and passing.

## What remains

- **Real screen reader test** (TODO "Rītā"): TalkBack on Android Chrome, VoiceOver on iPhone Safari, NVDA + Chrome on
  Windows. Walk: open the page → swipe to the search → "Ogre, plūdi" → is the card read out once (not twice) and in a
  sensible order (112 line → warning → decision → places)? → Saraksts → "Rādīt kartē" → popup → close. axe cannot judge
  how the long aria-live card sounds; if it is too chatty, announce only the verdict line and leave the card non-live.
- `#karte` has `role="application"` (Leaflet keyboard panning); screen-reader users may get stuck in application mode on
  the map. Check with NVDA; if it is a problem, drop the role and keep `aria-label`.
- Touch gestures on the sheet (drag) have button equivalents (handle, Mazs/Puse/Pilns), but VoiceOver users should
  confirm the handle's label ("Atvērt lapu: …") is understandable.
- Not tested: Firefox/Safari engines, 200 % text zoom / 320 px width reflow, Windows high-contrast mode, api.html and
  moderacija.html (not in the brief), states with live layers (zibens, ceļi, ziņojumi) switched on.
