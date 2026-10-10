# Slaidi (production/slaidi.html)

Slaidu saturs un stāsts: `notes/pitch.md`. Ekrānuzņēmumi: `production/slaidi/*.webp`.

## Ekrānuzņēmumu atjaunošana

Vienā rindā (no repo saknes), ~6 lapu ielādes no https://map.repo.lv, WebP ≤ 300 KB uzreiz `production/slaidi/`:

```
uv run --no-project --python 3.12 --with playwright --with pillow src/demo/ekrani.py
```

- `--tikai 02,03` atjauno tikai šos kadrus; `--url http://127.0.0.1:8791` ņem citu serveri (piem. `src/demo/lokali.py`); `--izvade <mape>` saglabā citur (pārbaudei, neaizskarot slaidus).
- Kadri: telefons 390×844 @2x (02–06, 08), dators 1280×800 @1 (01), 07 — datora izgriezums @2x. Vaicājumi: "Ogre, plūdi" (01–03), "plūdi Brīvības iela 33 Ogre" (04–05), "cilvēks nav pie samaņas" (06); 07 — "Datu avoti" ieraksts par CA plāniem; 08 — info.html LR1 bloks.
- Skripts gaida, līdz rindai "Plūdu riska zona" ir īsta atbilde (ne "Pārbauda…"), līdz 40 s. Beigās izdrukā tabulu; ja kadrs tomēr rāda ielādes stāvokli, pie tā ir ⚠ — atkārtojiet vēlāk ar `--tikai <nr>` (LVĢMC WMS dažreiz nestrādā), un ar to nekopējiet failus slaidos.
- Ja slaidos mainās failu nosaukumi vai kadri, jāpielāgo `FAILI` un attiecīgā sadaļa `src/demo/ekrani.py`.
- Pēc palaišanas atveriet `production/slaidi.html` (← →) un pārbaudiet, ka kadros nav kursora, "Pārbauda…" un 112 sarkanās rindas aprakstā.
