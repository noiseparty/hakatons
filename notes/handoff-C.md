# Handoff — terminal C (2026-10-10 night), branch `noiseparty/radio-karte` (WIP, not a PR yet)

**Done tonight (merged or open):** #44/#55 status page, #62 info.html, #69 Saraksts, #77/#86 daily refresh, #84 Ziņot, #90 Ventspils OCR, #93 letters (drafts only, never send), #96 pitch, #100 honest count + footer, #101 TODO cleanup, #102 Ziņot in header, #106 sources (NMPD 24/7 URL, UR contacts for 42 municipalities, Meteoalarm verdict, research/01 fixes), #107 Liepāja/DKN +46 points (730 → 776).

**Radio map (branch `noiseparty/radio-karte`, PR opened 2026-10-10 ~04:40):** LR1 map on info.html is done.
- `src/info/lr1_frekvences.json`: the 16 sites on latvijasradio.lsm.lv/lv/par-mums/frekvences/ (not 25-30: Ulbroka, Cēsis, Jelgava, Madona, Talsi etc. are not LR1 sites there). All 22 frequencies match the regulator list https://www.esakari.lv/lv/fm-apraides-staciju-saraksts (Lielauce = "AUCE") and lv.wikipedia.
- Coordinates: 10 at OSM tower objects (Rīga, Liepāja, Daugavpils, Cesvaine, Māle, Dundaga, Rēzekne, Viesīte, Kuldīga "Raidstacija", Aizpurve mast 0.7 km from the Medņeva-parish hamlet); 6 approximate at town/village centre (Valmiera, Ventspils, Alūksne, Limbaži, Lielauce, Skaista), drawn as hollow dots and explained in the caption. Per-entry `koord_avots`/`koord_url`/`parbaudits`.
- Generator: two-line labels (place / frequencies), `etikete` offsets tuned at 375 px; `production/lr1.json` added to the sw.js shell.
- Next: pin the 6 approximate sites when a second source confirms the towers (TODO).

**Advice review should check:** sirens = turn on LTV1/LR1 (VUGD, booklet p. 5), air raid = shelter (p. 19); LV-ALERT levels (yellow includes weather); 72 h water 3 l/adult/day (4 l in heat); 112 wording; no tel: links; "Jūs" form; keep keywords; run `src/meklesana/testi.py` (must stay green).

**Also open:** TODO "check every markdown/<slug>/ for pointer stubs whose PDF is published" (that's how Liepāja/DKN was missed).
