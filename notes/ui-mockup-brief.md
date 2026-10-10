# UI rework brief — for an AI mockup generator

> Paste everything below the line into the mockup AI. It is self-contained.

---

## 1. What you are designing

**Krīzes karte** (https://map.repo.lv) — a nation-wide public crisis website for Latvia. A resident types one line ("plūdi Ogrē", "nav elektrības Brīvības 15 Ogre") or shares their location and immediately gets **one result card with a decision**, plus an **interactive map dashboard** that tracks weather warnings, river levels, road traffic events, crisis alerts and safe places across the whole country.

Two modes, one page:

1. **Search (front door)** — one input, one answer. This is what most people in a crisis use.
2. **Map dashboard** — country-wide situational view: layers, filters, a live "situation now" panel.

Audience: every resident of Latvia, any age, often stressed, often on a cheap phone with weak signal. Secondary: municipal staff and journalists who use the map dashboard on desktop.

Design the mockup as **static HTML + CSS** (vanilla JS only where interaction must be shown). Deliver: mobile 375 × 740 and desktop 1440 × 900 for each screen in section 5.

## 2. Look and feel

You choose the visual style. Hard requirements:

- **Official and sleek.** It must read as a state service (think gov.uk, latvija.gov.lv, Estonian eesti.ee), not a startup landing page or a gaming HUD. Calm, confident, dense where useful, generous whitespace elsewhere.
- **Light theme by default.** Optional dark theme via `prefers-color-scheme`, but light is the primary design.
- **Nothing bright or flashy.** No neon, no gradients on large surfaces, no glassmorphism, no glow, no animated backgrounds, no illustrations or stock photos. Colour carries meaning, not decoration.
- **Distinct colour schemes.** Each of these must be instantly distinguishable from each other, in muted/desaturated tones that still pass WCAG AA contrast on white:
  - **Brand/UI chrome** — one restrained primary (e.g. deep navy, slate blue or dark teal). A Latvian carmine (≈ `#9E3039`) may appear as a thin accent only (a header rule, a logo mark), never as the action colour, because red is reserved for danger.
  - **Severity scale** for warnings (LVĢMC uses yellow / orange / red levels): 4 steps — info, yellow, orange, red. Use toned-down ochre / burnt orange / brick red, not traffic-light primaries. Every level also gets a text label and an icon shape, never colour alone.
  - **Map layer categories** — ~12 categories (list in section 4), grouped into 4 families with a hue family each: *safe places* (teals/greens), *health* (purples/plums), *infrastructure & services* (blues/greys), *hazards & traffic* (ambers/browns). Within a family, vary lightness. Marker shape differs per family too (circle, square, diamond, triangle) so it works for colour-blind users.
  - **Data status** — live / stale / simulated / unavailable each with its own neutral treatment (e.g. a small dot + label).
- Define everything as CSS custom properties in one `:root` block so the palette can be swapped. Name the tokens in English (`--color-primary`, `--sev-orange`, `--layer-shelter` …).
- Typography: **system font stack only** (`system-ui, -apple-system, "Segoe UI", Roboto, sans-serif`), tabular numerals for distances, times and water levels. Clear hierarchy: one large decision line per card, then small facts.
- Icons: inline SVG, single-colour, 1.5 px stroke style, one consistent set. No emoji in the final design (the current site uses emoji; replace them).

## 3. Performance budget ("must load light")

- No web fonts, no CSS framework, no icon font, no images except inline SVG.
- HTML + CSS of the shell ≤ 50 KB uncompressed; the map library (Leaflet 1.9, already used) is the only third-party dependency.
- First screen (search box + 112 line + current warnings) must render and be usable **before** the map loads. The map loads lazily below/behind it.
- No layout shift when the warnings banner or results arrive — reserve space or animate in from a fixed slot.
- Works with JS failing for the map: a clear text message, never a blank area.

## 4. Content and data (use real labels, Latvian, polite "Jūs" form)

All UI text is Latvian, polite form ("Jums", "Uzrakstiet", "Pārbaudiet"). The search also accepts Russian and English input, but the UI language is Latvian (add a small LV / EN / RU switch in the header for the mockup).

**Map layers** (name — count — source/licence):

| Family | Layer | ~Count | Source |
|---|---|---|---|
| Safe places | Publiskās patvertnes | 778 | VUGD / 112.lv (⚠ licence not stated — show a small warning mark) |
| Safe places | Evakuācijas pulcēšanās vietas | 730 | Municipal civil-protection plans, with page citation |
| Safe places | Pagaidu izmitināšanas vietas | 579 | Municipal civil-protection plans, with page citation |
| Health | Neatliekamā palīdzība 24/7 | 37 | Veselības ministrija |
| Health | Slimnīcas un ārstniecības iestādes | 69 | IeM IC |
| Health | Aptiekas | 814 | ZVA |
| Infrastructure | Policija | 55 | IeM IC |
| Infrastructure | Ugunsdzēsēji (VUGD depo) | 87 | IeM IC |
| Infrastructure | Bankomāti / Degvielas uzpildes stacijas | 800+ each | OpenStreetMap (ODbL) |
| Hazards | Plūdu riska zonas (area overlay, 10 % / 1 % / 0,5 %) | — | LVĢMC |
| Hazards | Upju un ezeru ūdens līmenis (gauges, 24 h trend arrow) | ~60 | LVĢMC |
| Hazards | Hidrometeoroloģiskie brīdinājumi (area polygons by severity) | live | LVĢMC |
| Traffic | Ceļu slēgumi, remontdarbi, satiksmes negadījumi, ceļa apstākļi | live | LVC / National Access Point, DATEX II |

**Every place and every fact shows its source and licence** in small text (e.g. "Avots: LVĢMC · CC BY 4.0"). This is a judging criterion; make it look tidy, not like a footnote dump.

**Emergency rule (non-negotiable):** there are **no `tel:` links, no "Call 112" buttons** anywhere. Instead a single red text line: "Ja apdraudēta dzīvība vai veselība, zvaniet 112." When the query sounds life-threatening, this line moves to the very top of the result in a stronger style (still text, not a button). Add `<meta name="format-detection" content="telephone=no">`.

## 5. Screens to produce

### 5.1 Home / search (mobile first)
- Header: small state-service style wordmark "Krīzes karte" + "Latvija", language switch, link "Par datiem".
- Big single input: placeholder "Kas notiek un kur? Piem.: plūdi Ogrē". Primary button "Meklēt". Secondary: "Izmantot manu atrašanās vietu".
- 4–6 quick chips under the input: Plūdi · Nav elektrības · Evakuācija · Patvertne · Ārsts · Ceļi.
- **Situation strip** under it: current country-wide warnings count by severity ("2 oranži, 5 dzelteni brīdinājumi"), data freshness ("Atjaunots 14:05").
- The 112 text line.
- Below the fold (desktop: right side): map preview, which opens the map dashboard.

### 5.2 Result card (the core of the product)
One card, in this exact order:
1. **Warnings for this place** (LVĢMC), severity-coloured left rule + label + valid-until time.
2. **Decision line**, large: e.g. "Jūsu adrese **ir** plūdu riska zonā (1 % varbūtība gadā)." or "**Nav** plūdu riska zonā." Strong yes/no treatment that does not rely on colour only.
3. **Facts** row: flood zone; nearest river gauge with value, 24 h trend arrow and timestamp; road events nearby (e.g. "Ceļš P5 slēgts 3 km attālumā").
4. **Nearest places** list: evacuation point, temporary accommodation, shelter, 24/7 hospital, pharmacy — each with distance, address, "Maršruts" link (opens external maps), source + licence, and for CA-plan items "Pašvaldības CA plāns, 12. lpp.".
5. **What to do now** — 3–5 short advice bullets for the scenario.
6. Footer actions: "Rādīt kartē", "Kopīgot", "Jauna meklēšana".

Show these states too: loading (skeleton, no spinner-only), address found but no scenario ("Uzrakstiet arī, kas notiek…"), not understood (with "Vai domājāt:" suggestion chips), life-threat query (112 line on top), data unavailable for one block (that block says so, the rest still works).

### 5.3 Map dashboard (desktop 1440 × 900, and mobile)
- **Desktop:** left panel 340 px (search + layers + region filter), full-height map centre, collapsible right panel "Situācija tagad" with live feeds:
  - Weather warnings list (severity, area, time window).
  - Rivers rising: top gauges by 24 h change, mini sparkline.
  - Traffic: active closures / incidents, grouped by road number.
  - Each item click → map flies to it and opens its popup.
- **Mobile:** full-screen map; bottom sheet with three snap heights (peek: search + warning count; half: layers or situation; full: list). Floating controls: zoom, my location, basemap toggle (Karte / Reljefs — OpenStreetMap and OpenTopoMap only).
- Layer panel: grouped by the 4 families, each layer row = shape/colour marker, name, count badge, toggle. Group-level toggle. Disabled layers greyed with reason ("Dati nav pieejami").
- Region filter: "Visa Latvija" or one of 43 municipalities.
- Map styling: muted basemap (slightly desaturated tiles via CSS filter is fine), clustered markers with count, warning polygons as translucent fills with a hatched pattern for red, flood zones in a soft blue with two opacities for 10 % / 1 %.
- Marker popup: title, category, address, distance, source + licence, route link, last updated.
- Legend that matches the layer panel exactly.

### 5.4 Warnings banner
A thin full-width strip under the header when there are warnings for the user's area or the country. Severity colour + icon + one line + "Skatīt". Dismissable for the session, never covers the search input.

### 5.5 Data sources ("Par datiem")
A clean page/panel listing every dataset: name, publisher, licence, update frequency, last update, record count, link. Mark simulated data with a visible "Simulēti dati" tag. One short paragraph on how AI was used (civil-protection plans of all 42 municipalities were read by AI to extract evacuation and accommodation sites with page citations; 41 coordinate errors were found in the official plans). The search itself is rule-based, no AI at runtime.

### 5.6 Optional: "Ziņot par situāciju" (report) flow — mark as concept
A 4-step flow on mobile: 1) what is happening (chips + text), 2) where (pre-filled from location/address — don't ask again), 3) photo optional / details, 4) **summary before submit** with an edit link per step. After submit: a status screen with a reference number and what happens next ("Pašvaldības dežurants redzēs ziņojumu…"), not just "Paldies". Label it clearly as a prototype.

## 6. Accessibility and usability

- WCAG 2.1 AA: contrast ≥ 4.5:1 for text, visible focus ring, full keyboard path, `aria-live` on results.
- Touch targets ≥ 44 × 44 px. Body text ≥ 16 px on mobile.
- No dead ends: every empty/error state offers a next action.
- Works in portrait at 320 px wide without horizontal scroll.
- Respect `prefers-reduced-motion`; animations ≤ 200 ms, only for sheet/panel movement.
- Times in Latvian format (14:05, 10.10.2026), decimal comma (1,4 m).

## 7. Deliverables

1. A single `index.html` + `style.css` (+ minimal `demo.js` if needed) showing all screens, or one HTML file per screen.
2. The palette as a token table: name, hex, usage, contrast ratio on white.
3. A short note (≤ 10 lines) on the chosen style and why it fits a national crisis service.

Use realistic sample data (Ogre, Rīga, Jēkabpils, Daugava river, road A6 / P5) so the mockup reads as real. Don't add features that need data we don't have (no live crowd reports on the map, no chat, no AI assistant bubble).
