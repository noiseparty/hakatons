# Presentation ideas

Ideas and verified facts for the pitch (`notes/pitch.md`). Add new ideas here; move them into the script once agreed.

## Jūrmala: an assembly point in Lithuania

**Slide line:**
> "Jūrmalas oficiālajā CA plānā pulcēšanās vieta Melluži ir Lietuvā — 100 km no Jūrmalas. Mūsu MI pārbaude to atrada 2 sekundēs."
>
> ("In Jūrmala's official civil protection plan, the Melluži assembly point is in Lithuania, 100 km from Jūrmala. Our AI check found it in 2 seconds.")

⚠ "2 sekundēs" has not been measured. Before the pitch, either time the check in `src/karte/db/ca_plani.py`, or say "automātiski" (automatically) instead.

**Verified facts (2026-10-10):**
- **Source:** Jūrmalas pilsētas sadarbības teritorijas civilās aizsardzības plāns, approved by Jūrmala council decision No. 4 of 27.01.2022. It is still the published version, and its four-year term ran out in January 2026.
- **Original PDF:** https://dokumenti.jurmala.lv/docs/l22/x/L0004_pielikums.pdf. Its sha256 `9102d87c…8875a98f` matches the organisers' kit (`originali/jurmala/faili.json`), so this is the same file the kit converted, not an altered copy.
- **The error:** page 85, table 4.2 "Evakuācijas pulcēšanās vietas", No. 10: *"Melluži · Dubultu prospekts 105 pie viesnīcas „Liesma" · 56.064556 / 23.735869"*.
- **The correct position:** the VZD address register has Dubultu prospekts 105, Jūrmala (code 101711450) at **56.964552 / 23.735869**. The longitude is identical, so it is a one-digit typo (56.**9**64… written as 56.**0**64…).
- **How far off:** about 100 km south, in Lithuania, south of Joniškis. The other 22 points in the same table are all at 56.92–56.99°N.
- **How we found it:** every point taken from a plan is tested against its municipality boundary and against the VZD address register. The Melluži point fell 96 km outside Jūrmala. It is one of 41 coordinate errors found across the plans (details: `notes/ca-plani-kvalitate.md`).
- **On our map:** it is placed at the correct VZD position, flagged as a plan error, and the original value from the plan is kept.

**How to show it:**
- A screenshot of page 85 of the original PDF, with row 10 highlighted, next to a map showing the plan's point in Lithuania and the correct point in Melluži.
- Tone: constructive ("this is why plans should be data, not PDFs"), not "Jūrmala got it wrong". Judges from VARAM may know the people who wrote the plan.
- Optional follow-up: offer Jūrmala the list of errors as a free plan-quality report. That is the "municipalities" next step on slide 8.
