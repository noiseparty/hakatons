# CA plans: pointer stubs and unpublished annexes (checked 2026-10-10)

Scan of all `ai-open-data-2026-hakatons/ca-plani-hakatons/markdown/<slug>/` folders for files that only point to another
file (`konvertesanas_riks: norāde uz kopīgo failu …`, "Pilnais konvertētais … pieejams") or have almost no text (< 2 KB body),
plus the municipalities whose plan refers assembly points / accommodation to an annex that is not in the kit
(`nav_publicets` / `dalejs` in `notes/ca-plani-kvalitate.md`). For each, the municipality's plan page (URL from
`originali/<slug>/AVOTS.md`, which follows `pasvaldibas.csv`) was fetched once on 2026-10-10 and its file list compared with the kit.

**Result: no new public annex with assembly points or temporary accommodation was found; 0 points added.**
The only such case was Liepāja + Dienvidkurzeme annex 12, already added in #107.

## Pointer stubs (4 folders)

| Slug | Stub files | Points to | Original published? (page checked) | Points added |
|---|---|---|---|---|
| augsdaugavas-novads | 22 of 24 (the other two: CAK bylaws, council minutes) | `markdown/daugavpils/` | Yes, same plan; [augsdaugavasnovads.lv](https://www.augsdaugavasnovads.lv/lv/civilas-aizsardzibas-plans-augsdaugavas-novada) lists annexes 2, 6, 8 (all already converted in `daugavpils/`). Annex 4 "Pagaidu izmitināšana" is marked restricted. | 0 (assembly points already from table 5.2) |
| dienvidkurzemes-novads | 42 (all files) | `markdown/liepaja/Liepajas-DKN-ST-CAP_2023ATJ.md` | [liepaja.lv](https://www.liepaja.lv/civilas-aizsardzibas-plani/liepajas-valstspilsetas-un-dienvidkurzemes-novada-civilas-aizsardzibas-plans/) lists annexes 1–5, 7, 11–13, 17, 19–29. Kit's `liepaja/` folder only converts the main plan + annex 1. Annex 12 (assembly points 2026) = done in #107. Accommodation annexes 7.1–7.3 are marked restricted. Annex 17 "Patvertnes" is public but lists shelters (already a separate VUGD layer), not assembly/accommodation. [dkn.lv](https://www.dkn.lv/lv/drosiba/civilas-aizsardzibas-plans) has the older 2023 annex 12 (superseded). | 0 |
| jelgavas-novads | 2 (`40_lemuma_pielikums_civilas_aizsardzibas_plans.md`, `jelgava_lv_12_5_pielikums3.md`) | `markdown/jelgava/` | Volumes 1–2 published and converted. Annexes 5–8 (assembly points, accommodation) are not on [jelgava.lv](https://www.jelgava.lv/dokumenti/planosanas-dokumenti/jelgavas-pilsetas-un-jelgavas-novada-sadarbibas-teritorijas-civilas-aizsardzibas-plans/) or [jelgavasnovads.lv](https://www.jelgavasnovads.lv/lv/civila-aizsardziba-operativa-riciba) (only the plan, CAK bylaws, a shelter list and info leaflets). | 0 |
| rezeknes-novads | 10 (all files) | `markdown/rezekne/` | Joint plan fully converted in `rezekne/` (both lists extracted). | 0 (covered by `rezekne`) |

## Near-empty conversions (not pointer stubs)

| Slug | File | Body | What it is | Points added |
|---|---|---:|---|---|
| ventspils | `plans_publiskais_2023.md` | 168 B | Scanned PDF; already OCR'd in `src/karte/dati/ca_plani/ventspils-ocr.md`. Annexes 4–16 (assembly + accommodation) are restricted cover pages. [ventspils.lv](https://www.ventspils.lv/pilsetas-parvalde/publiskie-dokumenti/civilas-aizsardzibas-plans/) has no further plan files. | 0 |
| daugavpils | `lem_164-v001.md`, `lem_901-v001.md` | 167 B | Scanned 2022 version (superseded by the 2026-05 plan) and a 1-page amendment. | 0 |
| madonas-novads | `madona_ca_plans_2021_lemums_534.md` | 168 B | Superseded 2021 plan (scan). | 0 |
| marupes-novads | `1.1_pielikums_applustosas_teritorijas.md` | 166 B | Flood map image. | 0 |
| tukuma-novads | `8.pielikums_kartes_piktogrammas_3.md` | 167 B | Map legend image. | 0 |
| jekabpils-novads | `jekabpils_cap_pielikums1.md` | 2.0 KB | Map annexes (1, 4, 5, 9–11, 14, 16, 18–20) as images; no lists. | 0 |

Other files < 2 KB (Limbaži parish lists, Talsi annexes, Mārupe/Olaine annexes, council decisions) are short but complete
documents; their lists are already extracted.

## Annexes referenced but not in the kit (one page fetch each, 2026-10-10)

| Slug | Annex in plan text | Plan page | Found |
|---|---|---|---|
| aluksnes-novads | 6 (assembly), 10 (accommodation) | [aluksne.lv](https://aluksne.lv/index.php/pasvaldiba/civilas-aizsardzibas-plans/civilas-aizsardzibas-plans/) | Only `CAP_PLANS_2025.pdf` (same as kit) |
| cesu-novads | 12 (assembly), 19 (accommodation, restricted) | [cesis.lv](https://www.cesis.lv/lv/novads/drosiba/civilas-aizsardzibas-plans/) | Plan "bez pielikumiem", CAK bylaws, 2 VUGD leaflets |
| jekabpils-novads | 22 (assembly), 24 (accommodation) | [jekabpils.lv](https://www.jekabpils.lv/lv/civila-aizsardziba) | Plan + annex files 1 and 2 (same as kit) |
| livanu-novads | 7 (assembly) | [livani.lv](https://www.livani.lv/lv/civila-aizsardziba) | Plan + CAK bylaws only |
| siguldas-novads | 9 (assembly), 5 (accommodation, restricted) | [sigulda.lv](https://sigulda.lv/novads/civila-aizsardziba/civilas-aizsardzibas-plans/) | Plan + annex 27 (same as kit) + 2 company plans |
| valmieras-novads | 5 (assembly), 7 (accommodation), "elektroniski" | [valmierasnovads.lv](https://www.valmierasnovads.lv/civila-aizsardziba/) | Public part of plan + CAK bylaws |
| kuldigas-novads | 8.6 (accommodation) | [kuldigasnovads.lv](https://kuldigasnovads.lv/pasvaldiba/civilas-aizsardzibas-plans/) | 2022 plan only (2026 plan not published) |
| madonas-novads | 8 (accommodation) | [madona.lv](https://www.madona.lv/lat/civila-aizsardziba) | Annexes 5 and 10 only (annex 5 already extracted) |
| preilu-novads | 4 (accommodation) | [preili.lv](https://www.preili.lv/lv/civila-aizsardziba) | Plan + CAK bylaws only |
| daugavpils | 4 (accommodation, restricted) | [daugavpils.lv](https://www.daugavpils.lv/drosiba/civilas-aizsardzibas-plans) | Plan `CA-Plans_14.05.pdf` (same as kit) |

## Not covered

- Pages were read as served HTML (no JavaScript). The Drupal sites (jelgavasnovads, jekabpils, livani, preili, dkn) list files
  as `media/N/download` links with file names in the `title` attribute; these were read.
- Council meeting archives were not searched again (the kit's AVOTS.md files record that search from 2026-09-11).
