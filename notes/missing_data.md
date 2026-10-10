# Trūkstošie dati: ko valsts un pašvaldības vēl nepublicē (pitch materiāls)

Stāvoklis 2026-10-10 rītā. Visi 33 atvērto datu avoti (to skaitā LR1 frekvences: oficiāli fakti (LR / SPRK), nav autortiesību objekts; un 2 bez atvērtas licences ⚠: 112.lv patvertnes, banku bankomātu saraksts; kā arī 2 simulēti prototipa dati), ko karte izmanto, ir uzskaitīti https://map.repo.lv (panelis "Datu avoti"). Šis saraksts ir **otra puse**: dati, kas krīzē iedzīvotājam ir vajadzīgi, bet ko neviens nepublicē vai publicē bez atvērtas licences. Katrai rindai: kam dati pieder, kāpēc vajag, ko prasām. Avoti: `notes/research/02`, `04`, `05`, `notes/demo-scenariji.md`, `notes/ca-plani-kvalitate.md`, nakts atradumi, apkopoti 2026-10-10.

Īsā versija slaidam: **"Mēs izmantojām 33 atvērto datu avotus. Vēl 30 datu kopas valstī eksistē, bet nav publiskas. Lūk, saraksts."**

## 1. Dzīvībai svarīgi, bet nepubliski (TOP prasības)

| # | Dati | Kam pieder | Kāpēc vajag krīzē | Šodien | Prasām |
|---|---|---|---|---|---|
| 1 | **Patvertņu saraksts** (781 publiskās patvertnes) | VUGD / IeM IC, publicēts 112.lv | Tuvākā patvertne — visbiežākais jautājums | Rādām no 112.lv **bez atvērtas licences** (⚠ kartē). Nav ietilpības, nav pieejamības ratiņkrēslam, nav info par dzīvniekiem, nav operatora, nav statusa (atvērta / pilna / slēgta) | Publicēt data.gov.lv ar CC0, pievienot ietilpību, pieejamību, dzīvnieku pieņemšanu, atbildīgo un **dzīvo statusu** |
| 2 | **Evakuācijas pulcēšanās vietas un izmitināšanas vietas** | 42 pašvaldības (CA plāni, MK 658) | "Kur man jāiet?" | Izvilkām ar MI no PDF: 776 punkti, 579 izmitināšanas vietas, **41 koordinātu kļūda** oficiālajos plānos; **10 pašvaldības** sarakstus tur nepublicētos pielikumos (Cēsis, Sigulda, Valmiera, Jelgava …; Liepājas un Dienvidkurzemes pulcēšanās vietas atradām oficiālajā 2026. gada 12. pielikumā — komplektā tas bija tikai norāde); Ventspils plāns ir skenēts — **pat ar OCR** (2026-10-10) saraksti nav pieejami: tie ir 4.–16. pielikumā, kas publiskajā failā ir tikai titullapas "Ierobežotas pieejamības informācija" (lpp. 71–83) | Vienots mašīnlasāms formāts (GeoJSON/CSV) ar adresi, koordinātām, ietilpību; publicēt pielikumus; ĢeoLatvija slānis |
| 3 | **Elektroapgādes atslēgumi (dzīvie)** | Sadales tīkls | 22.–23.08.2026 vētra: ~260 000 lietotāju bez elektrības, nebija informācijas | karte.sadalestikls.lv ir tikai attēls; nav API, nav licences | JSON/GeoJSON plūsma ar poligoniem, sākuma laiku un prognozēto atjaunošanu; CC0 |
| 4 | **Mobilo sakaru pārklājuma / bāzes staciju statuss** | LMT, Tele2, Bite; SPRK | Scenārijs "bez sakariem": kur vēl ir signāls | Nav nekādu datu | Vismaz bāzes staciju darbības statuss pa novadiem krīzes laikā |
| 5 | **LV-ALERT šūnu apraides ziņojumi** | VUGD | Lai lietotne rādītu to pašu, ko telefons; arhīvs mācībām | Nav publiska arhīva, nav API (kopš 2025-07) | Publicēt izsūtītos ziņojumus (laiks, teritorija, teksts) kā plūsmu un arhīvu |
| 6 | **Upju bīstamības sliekšņi** (PRIS: level_1/2/3) | LVĢMC | Lai pie ūdens līmeņa teiktu "bīstams / normāls", ne tikai cm | `videscentrs.lvgmc.lv/data/pris_stations` eksistē, bet licence nav norādīta — **vajag atļauju** | Pievienot sliekšņus data.gov.lv hidroloģisko novērojumu kopai (CC0) |
| 7 | **Plūdu dziļums un līmeņa ↔ zonas sasaiste** | LVĢMC | "Cik dziļi būs pie manas mājas pie 300 cm?" | Ir tikai riska zonas (10/100/200 gadi) kā WMS; modeļi nav publicēti | Dziļuma rastri pa scenārijiem kā atvērtie dati |
| 8 | **Diennakts neatliekamās palīdzības darba laiki un noslodze** | NMPD, slimnīcas, VM | Nakts scenārijs "pārgriezta roka": kur tiešām pieņem 03:00 | 24/7 slimnīcu saraksts tikai PDF pielikumā (VM plāns); gaidīšanas laiki nav publiski | Mašīnlasāms 24/7 iestāžu saraksts ar darba laikiem; noslodzes indikators |
| 9 | **Aptieku darba laiki / dežūraptiekas** | ZVA | Nakts scenārijs | ZVA saraksts bez darba laikiem | Pievienot darba laikus un dežūras statusu |

## 2. Ir, bet ar nepareizu licenci vai aiz atslēgas

| # | Dati | Kam pieder | Problēma | Prasām |
|---|---|---|---|---|
| 10 | **ĢeoLatvija servisi** (plūdu zonas, meteostacijas, meža ugunsbīstamība, hidrogrāfija) | VARAM/VRAA, LVĢMC, LĢIA | Katalogā atzīmēti **CC BY-NC** — nekomerciāls ierobežojums bloķē jebkuru produktu; tie paši LVĢMC dati data.gov.lv ir CC0 | Vienota licence CC0/CC BY visiem valsts ģeoservisiem |
| 11 | **LĢIA pamatkartes, ortofoto, DEM kā servisi** | LĢIA | Lejupielāde ir CC BY 4.0, bet WMS/WMTS tikai pēc e-iesnieguma; mēs izmantojam OSM un lejupielādēto 20 m DEM | Anonīmi WMTS servisi ar to pašu CC BY 4.0 |
| 12 | **LVC reāllaika satiksme (DATEX II)** | LVC / transportdata.gov.lv | CC0, bet katrai datu kopai sava atslēga pēc reģistrācijas; robežšķērsošanas gaidīšanas laiki atbild 403 | Bezatslēgas lasīšana publiskām kopām vai vismaz viena atslēga visām |
| 13 | **Ātruma ierobežojumi** uz valsts ceļiem | LVC | Nav abonēti / nav atrasti NAP; brīvas plūsmas ātrumu vērtējam no mērījumiem | Publicēt kā GeoJSON |
| 14 | **Rīgas sabiedriskā transporta reāllaika pozīcijas** | Rīgas satiksme | Tikai statiskais GTFS (CC0); dzīvā plūsma aiz nedokumentēta saraksti.lv galapunkta bez licences | GTFS-Realtime ar CC0 (kā Tallinā, Viļņā) |
| 15 | **Meteoalarm Latvijas CAP plūsma** | EUMETNET / LVĢMC | Tuvu CC BY, bet ar papildu izplatīšanas noteikumiem | Skaidra CC BY licence |

## 3. Nav vispār (jāsāk vākt)

| # | Dati | Kam vajadzētu piederēt | Kāpēc |
|---|---|---|---|
| 16 | **Noturības punkti** (siltums, uzlāde, ūdens, wifi, ģenerators) — bibliotēkas, kultūras nami, skolas | Pašvaldības / VARAM | Scenāriji "nav elektrības", "aukstums"; mēs rādām OSM ēkas ar "statuss nav zināms" |
| 17 | **Dzeramā ūdens ņemšanas punkti un "vāriet ūdeni" paziņojumi** | Pašvaldību ūdenssaimniecības, VI | Ūdensapgādes krīze; kartē 456 OpenStreetMap dzeramā ūdens punkti (ODbL) un 100 komandas simulēti (marķēti); oficiālu izdales vietu nav |
| 18 | **Degvielas stacijas ar ģeneratoriem; bankomātu un POS termināļu darbības statuss** | EM, bankas, Finance Latvia | 22.–23.08.2026: skaidra nauda nebija pieejama; saraksti nav publiski. Komandai minētais „Kritisko ATM saraksts” (22.09.2026, „hakatonam”) nav repozitorijā, un tā izcelsme un licence nav zināma, tāpēc kartē netiek rādīts (pārbaudīts 2026-10-10) |
| 19 | **Slēgtās / bīstamās zonas** (droni, sprādzienbīstamība, ķīmiskais piesārņojums) kā poligoni | VUGD, NBS, VP | Scenārijs "drons": rādām tikai simulētu zonu |
| 20 | **Dūmu / gaisa kvalitātes brīdinājumi reāllaikā** pie ugunsgrēkiem | LVĢMC, VUGD | Pārdaugavas noliktavas ugunsgrēks 30.06.2026, Vecmīlgrāvis 17.07.2026: "aizveriet logus" tikai ziņās |
| 21 | **Meklēšanas / glābšanas aktīvās zonas un pazudušie cilvēki** | VP, VUGD | Lai cilvēki zinātu, kur palīdzība jau strādā |
| 22 | **Pašvaldību CA kontakti mašīnlasāmi** | Pašvaldības | Rezultāta kartītē rādām no `pasvaldibas.csv`, ko salikām paši |
| 23 | **Sociālās aprūpes un riska grupu blīvums** | LM, CSP (GEOSTAT 1 km) | Komisijām: kur prioritizēt palīdzību (tikai ierobežotai piekļuvei) |
| 24 | **Ceļu laikapstākļu kameras un sensori atvērtā formā** | LVC | Ir NAP, bet nav kameru; slidenuma stacijām nav temperatūru atvērtajā kopā |
| 25 | **Krīzes notikumu arhīvs** (kas, kur, kad, cik skarti) | VUGD, IeM | Mācībām un modeļiem; šodien faktus vācām no LSM/Delfi |
| 26 | **Rīgas pilsētas bezmaksas Wi-Fi punkti** | Rīgas valstspilsētas pašvaldība | Scenārijs "nav sakaru"; saraksts ir tikai tīmekļvietnē, ne kā atvērtie dati — rādām 155 OSM vietas ar bezmaksas Wi-Fi |
| 27 | **"Rīgas ūdens" bezmaksas dzeramā ūdens krāni** | SIA "Rīgas ūdens" | Scenārijs "nav ūdens"; krāni ir pilsētā, bet nav publicēti kā datu kopa ar koordinātām un darbības statusu — rādām OSM |
| 28 | **Telefonu uzlādes punkti** (publiskas uzlādes stacijas, ģeneratori krīzē) | Pašvaldības, VUGD | Scenāriji "izlādējas telefons", "nav elektrības"; avota nav vispār — kartē tikai 100 simulēti punkti (marķēti) |
| 29 | **"Vāriet ūdeni" paziņojumi** mašīnlasāmā plūsmā | Ūdenssaimniecības, PVD, VI | Paziņojumus publicē tikai kā ziņas pašvaldību vietnēs; nav plūsmas (RSS/CAP), ko pievienot adreses kartītei |
| 30 | **Bibliotēku, LMT un Tet publiskie Wi-Fi tīklāji** | LNB / pašvaldību bibliotēkas, LMT, Tet | Sakaru krīzē — kur var pieslēgties internetam; operatoru un bibliotēku tīklāju saraksti nav atvērtie dati |

## 4. Kvalitātes problēmas datos, kas ir

- **CA plānu koordinātas:** 41 kļūda 42 plānos (piem., Jūrmalas pulcēšanās vieta Nr. 10 Melluži ar 56.064 nevis 56.964 — 100 km Lietuvā). Labojām ar VZD adrešu reģistru. Saraksts: `notes/ca-plani-kvalitate.md`.
- **Plūdu riska WMS** (geo-dpps) atbild 1–30 s, brīžiem 503/504 — nav piemērots reāllaika lietotnei bez kešatmiņas.
- **LVĢMC zibens režģis** nāk ar 2–3 h nokavēšanos; reāllaikā izmantojam Somijas FMI (CC BY 4.0), jo Latvijā atvērtu reāllaika zibens datu nav.
- **Hidroloģiskās prognozes** ir m v.j.l. (LAS-2000,5), novērojumi — cm virs staciju nulles; pārrēķina tabula nav publicēta.
- **Prognožu fails** apdzīvotām vietām ir 16,6 MB dienā bez CORS — jālasa caur savu serveri.

## 5. Ko sakām pitčā (3 teikumi)

1. "Karte strādā uz 33 atvērto datu avotiem — un katra no tām ir pluss, kā prasa vērtēšanas kritēriji."
2. "Bet patvertņu saraksts nav atvērts, elektrības atslēgumiem nav API, 10 pašvaldības evakuācijas vietas tur PDF pielikumos, un reāllaika zibens dati mums nāk no Somijas."
3. "Šis saraksts ar 30 datu kopām ir mūsu lūgums datu turētājiem: publicējiet, un karte tās parādīs nākamajā dienā."
