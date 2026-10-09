# Krīzes meklēšana "Ko tev vajag?"

Lietotājs uzraksta vajadzību brīvi (LV/RU/EN, ar vai bez garumzīmēm): "patvertne Ogrē", "bērnam augsta
temperatūra", "нужен врач". Pārlūks bez AI un bez servera nosaka scenāriju, vai rādīt "Zvanīt 112", un vietu,
tad katrā scenārija slānī parāda 3 tuvākās vietas (caur esošo `/api/objekti`). Teksts nekur netiek sūtīts.

Scenāriji ir divos līmeņos: 7 **vajadzības** (patvertne, ārsts, zāles, ugunsgrēks, policija, degviela, nauda —
ātrās pogas) un 119 **situācijas** no `notes/SCENARIJI.md` (`nr` = tā numurs), katrai savs padoms, slāņi un 112.
Rāda labāko; tuvus variantus piedāvā kā "Vai domāji…?". Situācijai bez kartes datiem (apmaldījies mežā,
čūskas kodums) rāda tikai padomu un 112. Retāki atslēgvārdi sver vairāk (svars / √scenāriju skaits), katrs
vaicājuma vārds scenārijam dod punktus vienreiz.

SCENARIJI.md #72 ("Imigrantu pūlis") un #73 ("Netipiski cilvēki") apzināti nav ieviesti tādā formā: tie vērtētu
cilvēkus pēc izcelsmes vai izskata. Bīstamu rīcību sedz #71 (nekārtības), "Aizdomīga uzvedība" (#73, pēc rīcības),
#75, #112.

| Fails | Kas tajā |
|---|---|
| `production/scenariji.json` | **Noteikumi**: scenāriji → atslēgvārdi → kartes kategorijas → padoms; dzīvības draudu frāzes; citvalodu vietvārdi. Formāts aprakstīts faila `_apraksts`. |
| `production/klasifikators.js` | Teksts → `{scenariji, zvanit112, vieta}`. Vārdu sākumi, viena burta kļūdas, latviskās vietvārdu formas (Ogrē, Cēsīs, Talsos, Ventspilī). |
| `production/meklesana.js` | Meklēšanas lauks, ātrās pogas, rezultāti un to rādīšana kartē. Lieto `app.js` globālos. |
| `src/meklesana/testi.json` | Vaicājums → sagaidāmais scenārijs / 112 / vieta. |
| `src/meklesana/vaicajumi.json` | 497 reālistiski vaicājumi (LV, RU/EN, kļūdas, vietas, divdomīgi) → pieņemamie scenāriji; `testi.py` mēra precizitāti (mērķis ≥ 90 %). Metode: `notes/klasifikators.md`. |
| `src/meklesana/papildinat.py` | Filtrē un pievieno ģenerētos atslēgvārdus / apvieno ģenerēto vaicājumu kopu. |

Vieta: vietvārds vaicājumā → tava atrašanās vieta → izvēlētais reģions (no tā centra). Bez vietas lūdz to noteikt.
Saite ar vaicājumu: `https://map.repo.lv/?q=patvertne%20Ogrē`.

## Paplašināšana

- **Jauns vārds**, ko neatpazīst: pievieno to scenārija `atslegvardi` un rindu `testi.json`.
- **Jauns slānis** (piem., ūdens punkti, siltuma punkti): pievieno kategorijas kodu scenārija `kategorijas`.
  Kamēr slānis nav kartē, to vienkārši izlaiž, tāpēc to var ierakstīt jau iepriekš.
- **Jauns scenārijs**: rinda `notes/SCENARIJI.md` + objekts `scenariji.json` ar `nr`, `grupa`, `atslegvardi`,
  `kategorijas`, `padoms`, `zvanit112`. Izvairies no vispārīgiem vārdiem (palīdzība, ceļš, ūdens): tie
  sasaista nesaistītus vaicājumus; lieto frāzes ("deg dzīvokl"), ja vārds viens pats ir pārāk plašs.
- Reāllaika dati (incidenti, bankomātu darbība) nāk caur `objekti` ar `derigs_lidz`, tāpēc meklēšana tos redz pati.

## Pārbaude

```bash
uv run --no-project --python 3.12 --with quickjs src/meklesana/testi.py
```

Pārbauda `testi.json` un to, ka katra `notes/SCENARIJI.md` scenārija nosaukums atrod savu scenāriju.
Jaunu scenāriju pievienojot SCENARIJI.md, pievieno to arī `scenariji.json` (ar to pašu `nr`).

Node nav vajadzīgs (JS izpilda QuickJS). Vietvārdu pārbaudei reģionus ņem no map.repo.lv.
