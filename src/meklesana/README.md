# Krīzes meklēšana "Ko tev vajag?"

Lietotājs uzraksta vajadzību brīvi (LV/RU/EN, ar vai bez garumzīmēm): "patvertne Ogrē", "bērnam augsta
temperatūra", "нужен врач". Pārlūks bez AI un bez servera nosaka scenāriju, vai rādīt "Zvanīt 112", un vietu,
tad katrā scenārija slānī parāda 3 tuvākās vietas (caur esošo `/api/objekti`). Teksts nekur netiek sūtīts.

| Fails | Kas tajā |
|---|---|
| `production/scenariji.json` | **Noteikumi**: scenāriji → atslēgvārdi → kartes kategorijas → padoms; dzīvības draudu frāzes; citvalodu vietvārdi. Formāts aprakstīts faila `_apraksts`. |
| `production/klasifikators.js` | Teksts → `{scenariji, zvanit112, vieta}`. Vārdu sākumi, viena burta kļūdas, latviskās vietvārdu formas (Ogrē, Cēsīs, Talsos, Ventspilī). |
| `production/meklesana.js` | Meklēšanas lauks, ātrās pogas, rezultāti un to rādīšana kartē. Lieto `app.js` globālos. |
| `src/meklesana/testi.json` | Vaicājums → sagaidāmais scenārijs / 112 / vieta. |

Vieta: vietvārds vaicājumā → tava atrašanās vieta → izvēlētais reģions (no tā centra). Bez vietas lūdz to noteikt.
Saite ar vaicājumu: `https://map.repo.lv/?q=patvertne%20Ogrē`.

## Paplašināšana

- **Jauns vārds**, ko neatpazīst: pievieno to scenārija `atslegvardi` un rindu `testi.json`.
- **Jauns slānis** (piem., ūdens punkti, siltuma punkti): pievieno kategorijas kodu scenārija `kategorijas`.
  Kamēr slānis nav kartē, to vienkārši izlaiž, tāpēc to var ierakstīt jau iepriekš.
- **Jauns scenārijs** (plūdi, elektrības pārtraukums, ķīmiska noplūde…): jauns objekts `scenariji` ar
  `atslegvardi`, `kategorijas`, `padoms`; `atra_poga`, ja tam jābūt pogai.
- Reāllaika dati (incidenti, bankomātu darbība) nāk caur `objekti` ar `derigs_lidz`, tāpēc meklēšana tos redz pati.

## Pārbaude

```bash
uv run --no-project --python 3.12 --with quickjs src/meklesana/testi.py
```

Node nav vajadzīgs (JS izpilda QuickJS). Vietvārdu pārbaudei reģionus ņem no map.repo.lv.
