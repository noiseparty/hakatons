# Handoff — terminal C (2026-10-10 night), branch `noiseparty/radio-karte` (WIP, not a PR yet)

**Done tonight (merged or open):** #44/#55 status page, #62 info.html, #69 Saraksts, #77/#86 daily refresh, #84 Ziņot, #90 Ventspils OCR, #93 letters (drafts only, never send), #96 pitch, #100 honest count + footer, #101 TODO cleanup, #102 Ziņot in header, #106 sources (NMPD 24/7 URL, UR contacts for 42 municipalities, Meteoalarm verdict, research/01 fixes), #107 Liepāja/DKN +46 points (730 → 776).

**Half-done (this branch):** LR1 radio map for info.html.
- Generator: `src/info/radio_karte.py` → writes the SVG into `production/info.html` between `<!-- radio-karte:sākums/beigas -->` and writes `production/lr1.json`. Run: `python src/info/radio_karte.py`.
- Outline: `src/info/latvija_robeza.json` (built from map.repo.lv/api/regioni, VZD CC BY 4.0) — done.
- **Missing: `src/info/lr1_frekvences.json`** — keys `avots_url`, `nolasits`, `raiditaji: [{vieta, lr1: ["90.7"], lat, lon, etikete: [dx, dy]}]`. Frequencies = official list (latvijasradio.lsm.lv/lv/par-mums/frekvences/, as in info.html: Rīga 90,7, Liepāja 107,1 …). **Transmitter coordinates were being researched (LVRTC sites; Aizpurve/Māle are ambiguous village names) — don't guess; use town centres only for unambiguous towns and say so in the caption.**
- `production/info.css`: map styles added. `production/meklesana.js`: "Radio krīzē: LR1 … FM (tuvākais raidītājs …)" line in "Kas notiks tālāk", reads `lr1.json` — needs the JSON before it shows a frequency (falls back to a link).
- Next: write the JSON, run the generator, Playwright 375×740 + 1280×800 (labels must not overlap: tune `etikete` offsets; check print), merge main, PR.

**Advice review should check:** sirens = turn on LTV1/LR1 (VUGD, booklet p. 5), air raid = shelter (p. 19); LV-ALERT levels (yellow includes weather); 72 h water 3 l/adult/day (4 l in heat); 112 wording; no tel: links; "Jūs" form; keep keywords; run `src/meklesana/testi.py` (must stay green).

**Also open:** TODO "check every markdown/<slug>/ for pointer stubs whose PDF is published" (that's how Liepāja/DKN was missed).
