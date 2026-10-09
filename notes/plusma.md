# "Mana adrese krīzē": 4 soļu plūsma (uzbūvēta 2026-10-10)

Sākumlapa map.repo.lv (`production/plusma.js`, `plusma.json`); karte ir otrais režīms (`#/karte`, poga "🗺 Karte").
Mērķis: vērtēšanas kritēriji: konkrēts rezultāts (lēmums), "tikai vienreiz" (neprasām to, ko zina reģistri),
3–6 soļi ar kopsavilkumu un "kas notiks tālāk", strādā telefonā bez strupceļiem.

1. **Kur Jūs atrodaties?** Atrašanās vieta vai adrese (VZD, `/api/adreses`). Ja atrašanās vieta liegta vai adrešu
   meklēšana nestrādā: pilsēta vai novads (tekstā vai sarakstā, VZD robežas), nekad neapstājamies.
2. **Kas notiek?** 4 lielas pogas (plūdi, vētra / nav elektrības, evakuācija, sirēna / ķīmiska noplūde) + "Cits" ar
   brīvu tekstu → scenārijs (`klasifikators.js`, bez AI). Dzīvības draudu frāzes → sarkana "Zvanīt 112" uzreiz.
   Ja tekstā ir cita vieta ("nav elektrības Jelgavā"), piedāvā to.
3. **Jūsu situācija.** Bērni, kustību ierobežojumi, mājdzīvnieki, nav transporta. Neobligāti, var izlaist.
4. **Kopsavilkums.** Ko norādījāt (ar "Labot") → **lēmums** (plūdiem pēc plūdu zonas adresē) → fakti par vietu
   (LVĢMC brīdinājumi, plūdu riska zona, tuvākās upes līmenis) → tuvākās vietas (pulcēšanās un izmitināšana no CA
   plāniem, ja nav — patvertne; patvertne; 24/7 slimnīca; aptieka), katrai avots → padomi (+ pēc 3. soļa) →
   "Kas notiks tālāk" → drukāt / saglabāt (localStorage + service worker bezsaistei), skatīt kartē, atsauksme.

Brīdinājumu josla (LVĢMC) ir visas lietotnes augšā; pēc vietas izvēles rāda tikai tos, kas attiecas uz to.

Atvērtie dati plūsmā: VZD (adreses, robežas), LVĢMC (brīdinājumi, plūdu riska kartes, ūdens līmenis), pašvaldību
CA plāni (pulcēšanās, izmitināšana), VUGD/112.lv (patvertnes), VM (24/7 slimnīcas), ZVA (aptiekas), OSM (fons).

Pārbaudīts 375 px (Playwright): "Ogre, plūdi"; atrašanās vieta liegta → adrese Rīgā; "nav elektrības Jelgavā";
"cilvēks nav pie samaņas" → 112; `/api/adreses` 404 → pilsēta; "Skatīt kartē" ar plūdu slāni.
