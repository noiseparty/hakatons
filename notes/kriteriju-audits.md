# Kritēriju audits pirms pitch (2026-10-10, ~04:50)

Pārbaude: dzīvā vietne https://map.repo.lv, Playwright (Chromium, 375 x 740, mobilais režīms), viens pārlūks, parastas lapu atvēršanas. Vaicājumi: "Ogre, plūdi", "Brīvības iela 12, Ogre, plūdi", "cilvēks nav pie samaņas", "nav elektrības Rēzekne", "redzu dronu", "bankomāts Liepāja"; "Ziņot" plūsma līdz (bet ne ieskaitot) "Nosūtīt"; info.html, statuss.html, trukstosie.html, api.html. Nekas nav labots. Skala 0-3 (3 = žūrija neko nepamanīs).

## Skaitļi (izmērīti)

| Rādītājs | Vērtība |
|---|---|
| Datu avoti ar licenci | 25 paneļa galvenē (saraksts 29 rindas); `/api/avoti` 22 ieraksti, 21 ar licenci un licences saiti |
| Bez atvērtas licences | 1: VUGD/112.lv patvertnes, "Licence nav norādīta", atzīmēts ⚠ |
| Licenču sadalījums `/api/avoti` | CC0 13, CC BY 1, ODbL 2 (+1 ODbL/CC BY-SA), oficiāls dokuments 2, simulēti CC0 2 |
| Scenāriji `production/scenariji.json` | 129 (slaidos un `notes/pitch.md` 127, CLAUDE.md 119: jāsaskaņo) |
| Slāņi ieslēgti pēc noklusējuma | 0 (16 kategoriju + 5 pārklājumu izvēles rūtiņas, neviena nav atzīmēta; 0 marķieru pēc ielādes). Redzama tikai LVĢMC brīdinājumu josla un "Demo" mala |
| `tel:` saites | 0 visās lapās (numuri tikai kā teksts) |
| Horizontāla ritināšana 375 px | nav nevienā lapā |

## Vērtējums pa kritērijiem

| # | Kritērijs | Punkti | Īsi |
|---|---|---|---|
| 1 | Konkrēts rezultāts | 2 | Ir lēmums un tuvākās vietas, bet adreses plūdu "jā/nē" bieži neizdodas (1. sprauga) |
| 2 | Tikai vienreiz, katrs datu avots ir pluss | 3 | Adrese no VZD, vieta no GPS, nekas netiek prasīts divreiz; 25 avoti ar licenci un CA plāna lappusi |
| 3 | Plūsma 3-6 soļi, kopsavilkums, noslēgums | 2 | Galvenā plūsma ir viena kartīte, soļi nav redzami; "Ziņot" ir 3 ekrāni ar kopsavilkumu |
| 4 | Darbojas telefonā, bez strupceļiem | 2 | Strādā, nav ritjoslu, bet ārējais plūdu serviss krīt, reizēm JS kļūda |
| 5 | MI un dati | 2 | Dati redzami lapā, MI stāsts ir tikai slaidos (slaidos 3, lapā 1) |
| 6 | VDAA kontrolsaraksts (A-K) | 2 | Satura/UX daļa stipra, ietvara un tehniskā daļa prototipam nav piemērojama |

## Ko vietne dara šodien (pa vaicājumiem)

- **"Ogre, plūdi"**: sarkana rinda "zvaniet 112", LVĢMC brīdinājums, nākamās 24 h, plūdu zona "Nē: nav applūstošā teritorijā (10 %, 1 %, 0,5 %)", upe Ogre 20,62 m, 1,53 m zem CA plāna kritiskā 22,15 m (plāna lpp. 29, 31), 7 dienu prognoze, nokrišņi un augsne, satiksme, padoms, "Kas notiks tālāk", Dalīties, Drukāt. Katram blokam avots un licence. Labs, pilns piemērs.
- **"Brīvības iela 12, Ogre, plūdi"**: VZD atrod adresi, kartīte tāda pati + pulcēšanās vieta (CA plāna lpp. 121, 159 m), izmitināšana (1000 vietas, lpp. 123), tuvākā patvertne 157 m ar maršrutu 290 m / 4 min, 24/7 slimnīca. Taču plūdu zona rādīja "Neizdevās pārbaudīt. Plūdu zonas redzamas kartē" 3 no 3 mēģinājumiem (`/api/pludi` 503, statuss.html: "Traucējumi"); pirmajā mēģinājumā rezultāts bija pavisam tukšs (skat. 7. spraugu).
- **"cilvēks nav pie samaņas"**: lielā rinda "Izklausās, ka apdraudēta dzīvība. Zvaniet 112 tūlīt", bez pogas, padoms, "Kas notiks tālāk" (NMPD), poga "Noteikt manu atrašanās vietu". Bez vietas nav tuvākās slimnīcas.
- **"nav elektrības Rēzekne"**: brīdinājums, prognoze, padoms, 3 noturības punktu kandidāti ar "Statuss nav apstiprināts", tad SIMULĒTI uzlādes punkti (ar zīmi "SIMULĒTI DATI - PROTOTIPS"). Satiksme: "nav mērījumu".
- **"redzu dronu"**: tikai padoms un "Kas notiks tālāk"; lūdz pievienot adresi vai noteikt vietu, nav ne lēmuma, ne vietas.
- **"bankomāts Liepāja"**: 3 bankomāti ar attālumu un maršrutu (OSM, ODbL), pašvaldības kontakts, "Vai domājāt: Kartes un maksājumi nedarbojas".
- **"Ziņot"** (galvenes poga): 1. ekrāns: tips (5 varianti) + apraksts (200 zīmes) + vieta (GPS vai klikšķis kartē) + brīdinājums par personas datiem; "Tālāk: pārbaudīt" bez tipa vai vietas dod kļūdu ("Izvēlieties, kas noticis" / "Izvēlieties vietu"); GPS atteikums dod "Norādiet vietu kartē" (nav strupceļa). 2. ekrāns "Pārbaudiet ziņojumu": kopsavilkums (Kas / Apraksts / Vieta) un "Labot" / "Nosūtīt". 3. ekrāns "Paldies!" ar "Uz karti". **Kopsavilkums pirms iesniegšanas IR** (B.11), bet nav soļu joslas "1/3" un pēc nosūtīšanas nav statusa vai atsauksmes saites. Serverī ir ierobežojumi (apraksts <= 200, stundas limiti).
- **info.html** (112, sirēnas, LV-ALERT, LR1, 72 h, drukājama), **statuss.html** (avotu stāvoklis, vecums, 7 dienu %; augšā sarkani "Nedarbojas: Robežu gaidīšanas laiks"), **trukstosie.html** (25 trūkstošās kopas), **api.html** (25 galapunkti, OpenAPI): visi ielādējas, bez horizontālas ritināšanas.

## Spraugas, ko žūrija pamanīs (pēc ietekmes)

1. **Adreses plūdu lēmums atkarīgs no lēna ārējā servisa.** Galvenais demo ("Brīvības iela 12, Ogre, plūdi") 3/3 reizes rādīja "Neizdevās pārbaudīt". Labojums: servera kešs/priekšsildīšana vai plūdu poligonu kopija PostGIS ar `ST_Intersects`. Faili: `src/karte/api/karte_api.py` (`/api/pludi`), `production/meklesana.js` (TODO "tile proxy" jau ir).
2. **Lēmums telefonā ir zem ekrāna malas.** Pusatvērtā loksnē kartīte sākas ar 112 rindu, brīdinājumu un prognozi; "Plūdu riska zona" atrodas ~800 px no augšas pie 740 px ekrāna. Labojums: kartītes pirmā rinda = lēmums (jā/nē + tuvākā vieta), brīdinājums un prognoze zem tā vai kā čips. Faili: `production/meklesana.js`, `production/apaksa.js`, `production/stils.css`.
3. **Soļi nav redzami.** Kritērijs 3 prasa 3-6 soļus un noslēgumu; galvenā plūsma izskatās kā 1 solis (pitch to skaidro vārdos). Labojums: 3 soļu josla zem meklēšanas (Vieta, Vajadzība, Rezultāts) un "Solis 1/3" "Ziņot" dialogā. Faili: `production/index.html`, `production/meklesana.js`, `production/zinot.js`.
4. **MI stāsts nav lapā.** Ne `index.html`, ne `info.html` neizskaidro, ka pulcēšanās vietas izvilka MI no 42 plāniem un atrada 41 koordinātu kļūdu. Labojums: rindiņa "Kā tas tapa" panelī "Datu avoti" un zīme pie CA plāna vietām "izvilkts ar MI, oriģināls pārbaudāms lpp. N". Faili: `production/avoti.js`, `production/meklesana.js`, `production/info.html`.
5. **Vaicājumi bez vietas beidzas ar padomu.** "cilvēks nav pie samaņas" un "redzu dronu" nerāda tuvāko slimnīcu vai patvertni, kamēr lietotājs nenospiež "Noteikt manu atrašanās vietu". Labojums: ja atļauja jau dota, vai pēc vienas pieskāriena, ieslēgt GPS un rādīt nākamo bloku. Faili: `production/meklesana.js`, `production/app.js` (`atrastMani`).
6. **Simulēti dati īsta vaicājuma kartītē.** "nav elektrības Rēzekne" starp īstiem kandidātiem rāda SIMULĒTUS uzlādes punktus (ar zīmi, bet krīzē maldinoši). Labojums: simulētos rādīt tikai demo režīmā (`?demo=`). Faili: `production/meklesana.js`, kategorijas definīcija `src/karte/db/`.
7. **Neregulāra JS kļūda un tukšs rezultāts.** Vienā no ~10 ielādēm `krizesMeklesana is not defined` (`production/app.js` ~580: `/api/*` atbilde pienāk pirms `meklesana.js`), un tajā reizē meklēšana atdeva tukšu rezultātu. Labojums: `DOMContentLoaded` vai `window.krizesMeklesana?.sakt` ap izsaukumu. Fails: `production/app.js` (TODO jau ir).
8. **Skaitļu neatbilstība.** statuss.html: 730 pulcēšanās vietas, slaidi un pitch: 776; scenāriji 129 pret 127 slaidos. Labojums: skaitli ģenerēt no DB/JSON vai saskaņot tekstu. Faili: `production/slaidi.html`, `notes/pitch.md`.
9. **"Jūs" forma un lapas pārpalikumi.** Marķiera padoms "Tu esi šeit" (`production/app.js` 145) pārkāpj "Jūs" formu (C.5); trukstosie.html sākumā redzams izstrādes teksts ("Avoti: notes/research/02, 04, 05...", "1 bez atvērtas licences , kā arī..." ar liekām atstarpēm). Labojums: "Jūs esat šeit"; notīrīt ievadteksta ģenerēšanu. Faili: `production/app.js`, `production/trukstosie.html` (ģenerē `src/trukstosie/`).
10. **Nav valodu slēdža un lietotāja novērtējuma.** Meklēšana saprot LV/RU/EN, bet saskarne ir tikai LV (G.2); nav atsauksmes saites (K.1). Labojums: rindiņa "Vai tas palīdzēja?" ar saiti uz formu; RU/EN vismaz info.html. Faili: `production/index.html`, `production/info.html`.
11. **Trokšņa rindas.** Sarkanā "zvaniet 112" ir augšējā joslā un kartītes augšā arī plūdu vaicājumā, tāpēc īstā dzīvības draudu rinda neizceļas; statusa lapas augšā sarkans "Nedarbojas: Robežu gaidīšanas laiks" izskatās kā avārija (ieteikums: pelēks "nav pieejams"). Faili: `production/meklesana.js`, `production/statuss.js`.

## VDAA kontrolsaraksts (Bloki A-K), īsi

- **A Bizness: atbilst.** A.1 lēmums (plūdu zona, tuvākā vieta, maršruts), A.4 katrs vaicājums sākas no tīra stāvokļa, A.5 prasa tikai vietu. A.6: kartīte "Ogre, plūdi" ir gara (56 saites), bet bez tehniskiem laukiem.
- **B Soļi: daļēji.** B.1/B.2 galvenajā plūsmā nav soļu joslas (3. sprauga); B.4 "Ziņot" validācija ir; B.5 strupceļu nav (GPS atteikums, tukša forma); **B.10-B.11 "Ziņot" kopsavilkums un "Labot"/"Nosūtīt" ir**; B.16 modāļos nav ligzdotu logu.
- **C Saturs: lielākoties.** "Jūs" forma (izņemot "Tu esi šeit"), kļūdu teksti ar risinājumu, termini "plūdu zona", "pulcēšanās vieta" konsekventi.
- **D, E UI:** radio (tips), pogas/saites; horizontālu ritjoslu nav; fokusa kontūra 3 px; agrākā axe-core pārbaude 0 pārkāpumu (šoreiz neatkārtota). Latvija.gov.lv dizaina SDK (E.8, F.1) nav lietots: prototips ir Leaflet ar savu stilu.
- **F Tehniskā:** F.2 servera validācija ir (`karte_api.py` ziņojumi, DB `check`); F.3 VZD adrešu meklētājs ir (`/api/adreses`); F.5 `<dialog>`, nevis `alert()`.
- **G, H:** JSON REST un OpenAPI ir (`api.html`, `openapi.json`); BFF nav pilnībā: pārlūks tieši izsauc `geo-dpps.viss.gov.lv` (plūdu WMS), tā pati vājā vieta kā 1. spraugā; SLA <= 3 s: pirmais saturs ātri, pilna kartīte atkarīga no 15+ pieprasījumiem.
- **I Drošība:** teksti tiek ekranēti (`esc()`), saites ziņojumos tiek noraidītas; "Ziņot" ir anonīms ar IP hash limitu.
- **J, K:** VIRSIS kartīte un novērtējuma komponente nav (prototips nav Latvija.gov.lv e-pakalpojums); K.1 skat. 10. spraugu.

## Pirms demo

- Sasildīt "plūdi Mednieku iela 9 Ogre" un pārbaudīt statuss.html (plūdu serviss); ja traucējumi, demo balstīt uz "Ogre, plūdi" (centrā "Nē" strādāja) un `?demo=pludi-ogre`.
- Pitch teikums par 3 soļiem (vieta, vajadzība, rezultāts) paliek, bet tas nostiprinās, ja 3. sprauga tiek aizvērta.
