# Pitch: "Ko Jums vajag?" — map.repo.lv (10 min)

Slides: `production/slaidi.html` (https://map.repo.lv/slaidi.html; ← → keys, N notes, T timer, P or `?print` print view; 13 slides with speaker notes in `<aside class="piezimes">`, planned 9:30). Updated 2026-10-10 05:14 (`noiseparty/slaidi-2`): story order problem → demo (Ogre plūdi, address, 112) → AI extraction / rule-based search / 32 sources → judging criteria → top 5 of 30 gaps → resilience → ask + QR. Screenshots in `production/slaidi/` taken from map.repo.lv on 2026-10-10 ~05:00 (390×844 @2x and 1280×800; the LVĢMC flood WMS was not answering, so the "Plūdu riska zona" row shows the loading bar). The sections below are the long version; where they differ from the slides, the slides win.

## Numbers and which slide they belong to (`production/slaidi.html`)

| Number | Slide | Source |
|---|---|---|
| ~260 000 lietotāju skāra atslēgumi (22.–23.08.2026) | 1 | LSM 26.08.2026, Sadales tīkls (`notes/demo-scenariji.md` §6) |
| 42 plāni · 200–800 lpp. · 1 791 karte kā attēls · 10 pašvaldības nepublicē sarakstus | 2 | `notes/ca-plani-kvalitate.md` |
| Upe Ogre 1,53 m zem CA plāna kritiskā 22,15 m (29. lpp.) · pulcēšanās vieta 542 m (121. lpp.) | 4–5 | screenshots 10.10. ~05:00 (live values change) |
| 776 pulcēšanās + 579 izmitināšanas vietas · 41 koordinātu kļūda · Jūrmala Nr. 10 Lietuvā | 7 | `notes/ca-plani-kvalitate.md`, `notes/presentation_ideas.md` |
| Meklētājs: **129 scenāriji** (`production/scenariji.json`), LV/RU/EN, **96,1 % pareizi uz 609 vaicājumiem**, **91,4 % uz 186 paturētajiem** | 8 | `src/meklesana/testi.py`, run 2026-10-10 05:10 (earlier figures 127 / 95,0 % / 563 / 89,5 % in `notes/klasifikators.md`) |
| **32 atvērto datu avoti + 3 ⚠** (112.lv patvertnes 781, banku bankomāti 845 / 111 kritiskie, LR1 frekvences 16 raidītāji); 2 simulētie neskaitīti | 9 | `src/karte/db/shema.sql` avoti + `production/avoti.js` TIESSAISTE; live panel shows 29 + 1 until the VPS applies shema.sql (#110/#118) |
| 5 no 30 trūkstošajām datu kopām | 11 | `notes/missing_data.md` §1 rows 1–5 |
| LR1 radio karte 16 raidītāji · Meteoalarm rezerve | 12 | #116, #125, #129 |
| 7 vēstuļu melnraksti datu turētājiem (nesūtīti) | 13 | `notes/vestules.md` |
| Slodze: p95 1,1 s pie 50 klientiem (bija 12,4 s), 0 savienojuma kļūdu | Q&A | `notes/slodze.md` (local harness with fake sources) |

Judging criteria → where we answer them: one slide maps all five (slide 10); evidence on slides 4–6 (outcome, phone), 5 (only once), 7–9 (AI + open data), 12 (no dead ends).

---

## 0:00–1:00 · 1. Problēma (hook)

**Slide:** "2026. gada 22.–23. augusts. Vētra. ~260 000 elektrības lietotāju skāra atslēgumi." (verified: LSM 26.08.2026 and Sadales tīkls; ~245 000 at one moment on 23 Aug; sources in `notes/demo-scenariji.md` §6)
Below: "Kur man iet? Vai mana māja ir plūdu zonā? Kur ir siltums un ūdens?"

**Say:** Augusta vētrā elektrības atslēgumi skāra ap 260 000 lietotāju. Viņu pašvaldībai ir civilās aizsardzības plāns — tajā ir rakstīts, kur pulcēties, kur izmitina, kas ir bīstams. Bet neviens to neatrada, jo tas ir 200+ lappušu PDF.

## 1:00–1:45 · 2. Kāpēc tā ir

**Slide:** 42 pašvaldības · 42 dažādi PDF · 200–800 lpp. katrs · 1 791 karte kā attēls, nevis dati.
- 10 pašvaldības pulcēšanās un izmitināšanas vietas publiski **nepublicē** (pielikums "ierobežotas pieejamības" vai nav publicēts).
- Nevienā plānā nav siltuma, ūdens vai pārtikas izdales punktu, nav radio frekvences.

**Say:** Informācija eksistē, bet ne tādā formā, kas cilvēkam palīdz krīzes brīdī — telefonā, ar 5 % baterijas.

## 1:45–2:30 · 3. geolatvija.lv 1.0 → 2.0

**Slide (two columns):**

| geolatvija.lv (1.0) | map.repo.lv (2.0) |
|---|---|
| Katalogs: 282 ģeoprodukti | Viena rinda: "Kas Jums vajadzīgs?" |
| Vispirms sīkdatņu un reklāmas logs | Uzreiz meklēšana, bez reģistrācijas |
| Noklusējumā teritorijas plānojuma slāņi | Noklusējumā: tuvākā droša vieta |
| Nav lēmuma, nav tuvākās patvertnes, nav maršruta | Lēmums + tuvākās vietas + maršruts |
| Plūdi, patvertnes, brīdinājumi — jāatrod pašam | LVĢMC brīdinājumi un plūdu zona pie Jūsu adreses |

Bottom line: "Tie paši oficiālie avoti — data.gov.lv, VZD, LVĢMC, LĢIA, LVC. Katalogs → atbilde."

**Say:** Valstij jau ir ģeoportāls. Tas ir labs plānotājam: 282 datu produkti, ko var atrast un ieslēgt. Krīzē cilvēkam nav laika meklēt katalogā. Mēs ņemam tos pašus oficiālos datus un dodam vienu atbildi.

Facts (headless test 2026-10-10, `notes/research/05_avoti_parbaude_2026-10-10.md` §1): cookie + promo modal first, zoning layers by default, address search gave no result, nothing on floods/shelters/warnings. Say "tas ir rīks plānotājiem", not "tas ir slikts" — VARAM is the organiser.

## 2:30–3:00 · 4. Risinājums

**Slide:** map.repo.lv — "Uzrakstiet, kas notiek un kur. Saņemiet vienu atbildi."
Viena kartīte: LVĢMC brīdinājumi · lēmums (piem., plūdu zona jā/nē pie Jūsu adreses) · fakti (upes līmenis, 24 h izmaiņa, nokrišņi un augsne) · tuvākās vietas ar avotu un licenci · padoms · kas notiks tālāk.

**Say:** Mēs neprasām neko, ko valsts jau zina. Adrese — no VZD adrešu reģistra vai telefona atrašanās vietas. Pārējais — no atvērtajiem datiem un pašvaldību plāniem.

## 3:00–6:00 · 5. LIVE DEMO (telefonā, ekrāns spoguļots)

**Criterion 3 in one sentence (say it, and put it on the slide):** "Soļi ir trīs — vieta, vajadzība, rezultāts — un rezultāta kartīte pati ir kopsavilkums: brīdinājumi → lēmums → fakti → tuvākās vietas → padoms → kas notiks tālāk; krīzē cilvēks neklikšķinās cauri četriem ekrāniem."

Main path (~2 min), scenario **Ogre, plūdi** (Ogres plāns ir pilnīgākais):
1. **Vieta:** "📍 Rādīt tuvākos man" vai adrese meklēšanā (VZD).
2. **Vajadzība:** ierakstu "plūdi Mednieku iela 9 Ogre" (vai pieskaros "Biežāk meklētais" ieteikumam).
3. **Rezultāts — viena kartīte:**
   - LVĢMC brīdinājums šai vietai (ja ir);
   - rinda „Nākamās 24 h”: LVĢMC ikstundas prognoze tuvākajai vietai (temperatūra, nokrišņi, brāzmas) ar riska vārdu, piemēram, „vētra”, un norādi „Prognoze, nevis brīdinājums” (#120);
   - lēmums: adrese ir / nav plūdu riska zonā (LVĢMC kartes); zona kartē kā laukums ar robežu, pārklāšanās ar brīdinājuma apgabalu iesvītrota;
   - tuvākā upes stacija ar līmeni un 24 h izmaiņu; "Nokrišņi un augsne" rinda (Open-Meteo); ceļu notikumi 5 km rādiusā un satiksmes zona (LVC, reāllaikā);
   - tuvākā pulcēšanās vieta un pagaidu izmitināšana ar vietu skaitu un saiti uz CA plāna lappusi; patvertne; 24/7 slimnīca; maršruta saites;
   - padoms scenārijam, pārbaudīts pret VUGD un Aizsardzības ministrijas bukletu „Kā rīkoties krīzes gadījumā” (24 no 127 padomiem pārrakstīti), ar saiti „Avots: VUGD” zem padoma (#117); rinda „Radio krīzē” ar tuvākā LR1 raidītāja frekvenci (#116); "Kas notiks tālāk" (#54); pogas "Dalīties" (saite atver to pašu rezultātu) un "Drukāt" (kartīte ar QR kodu).

Second, 20 s: free text "cilvēks nav pie samaņas" → kartītes augšā sarkana rinda "zvaniet 112". **No buttons, no tel: links** (team decision) — say: "mēs nerādām pogu, mēs pasakām skaidri".

Third, 30 s — demo panel (#53), deep links (open them from a QR or bookmarks, each with the "SIMULĀCIJA" badge):

| Kods | Scenārijs | What to point at |
|---|---|---|
| `?demo=vetra-2026` | 2026-08-22/23 vētras atkārtojums (Bauska) | simulēti elektrības atslēgumu apgabali; reālie bankomāti un DUS tajos |
| `?demo=pludi-ogre` | Ogre, plūdi → augstiene ≥23 m (LĢIA DEM) | kur iet, ja pulcēšanās vieta applūst |
| `?demo=nakts` | Nakts, sagriezta roka (Saulkrasti, 03:00) → 24/7 neatliekamā | viena atbilde, nevis saraksts |
| `?demo=drons-2026` | **Reāls:** droni virs Latgales, Rēzeknes naftas bāze (7.05.2026) | LV-ALERT teksts joslā, slēgtā zona, patvertne ārpus tās; 112.lv pārslodze (LSM) |
| `?demo=bauskas-2026` | **Reāls:** gāzes sprādziens Bauskas ielā 15 (2.01.2026) | lēmums pie adreses „Ēka slēgta”, izmitināšana; 46 evakuēti (LSM) |
| `?demo=ulmana-2026` | **Reāls:** noliktavas ugunsgrēks Pārdaugavā (30.06.2026) | dūmu konuss, vietas ārpus dūmiem; ~380 evakuēti |

Pick 2 of the 7 for the 30 s; the others for questions: `vejs` (dzeltenais, vējš), `vetra` (sarkanais, vētra), `drons` (Rēzekne, 1 km slēgta zona), `bez-sakariem` (bez elektrības un sakariem; `&regions=100003470` = Ogre). Why 23 m and not 15 m: in Ogre the Daugava is at ~17–18 m, so ≥15 m covers 99.6 % of the area (`notes/demo-scenariji.md` §5). Say "simulācija" every time: the data in these is not live.

Fourth, 10 s: map.repo.lv/statuss.html — "katram avotam redzams, vai tas šobrīd darbojas un cik veci ir dati" (criterion 4: no dead ends, honest about outages; row "Datu vecums").

Only if asked, the other things that are live: slāņi **satiksmes zonas** (LVC minūtes ātrumi pa novadiem), **zibens** (FMI, 30 min), **laikapstākļi tagad** (LVĢMC stacijas), **riska karte šodien/rīt** (prognoze + brīdinājumi), **ceļu notikumi**, **noturības punktu kandidāti** (OSM, statuss „nav zināms”); **"Ziņot par bīstamību"** (iedzīvotāju ziņojumi, moderēti); **bezsaistes režīms** un „pievienot sākuma ekrānam”; **balss ievade**; **maršruts, kas apiet slēgtu zonu**; **info.html** (112, sirēnas, LV-ALERT, 72 h; LR1 radio karte ar 16 oficiālajiem raidītājiem, frekvences pārbaudītas ar „Elektronisko sakaru” sarakstu); "▶ Atskaņot" (`?demo=atskanot`) as the hands-free backup; API documentation: map.repo.lv/api.html.

New tonight (#108–#120), one sentence each if asked:
- **Četri jauni OSM slāņi:** īsti dzeramā ūdens punkti (456), bezmaksas Wi-Fi (155), elektroauto uzlāde (392) un veterinārās klīnikas (113), katrs ar avotu un ODbL licenci (#118).
- **Patvertņu statuss:** patvertnēm, pulcēšanās un izmitināšanas vietām viens statusa bloks — siltums, uzlāde, ūdens, Wi-Fi, ģenerators rāda „nav zināms”, ja nav svaigu datu (≤ 6 h), un ietilpība, ratiņkrēsls, dzīvnieki — „nav norādīts”; mēs neizdomājam, ka vieta ir atvērta (#115).
- **Poga „Notīrīt”:** viens pieskāriens notīra meklēšanu, kartīti, saiti un visus filtrus, karte paliek savā vietā (#115).
- **Karte ielādē tikai redzamo:** objekti pēc kartes skata, nevis visa Latvija uzreiz — pirmā ielāde 958 KB → 104 KB (#114).
- **Datora skats:** no 800 px platuma trīs kolonnas — „Situācija tagad”, karte un slāņu atvilktne ar leģendu (#113); telefonā apakšējā lapa ar vilkšanu un cilnēm (#119).
- **Banku bankomāti:** 845 bankomāti, 111 kritiskie (skaidra nauda arī krīzē), ar ⚠, jo saraksta licence nav norādīta (#110).

Backup if venue Wi-Fi fails: screen recording on the laptop + screenshots in the slides.

## 6:00–7:15 · 6. Kā izmantots MI

**Slide:** "MI izlasīja 42 plānus un izvilka 776 pulcēšanās vietas un 579 izmitināšanas vietas (104 213 vietas) — ar atsauci uz lappusi."
- MI aģenti (Claude Code) pārveidoja plānu tabulas un tekstu strukturētos datos; katram ierakstam burtisks citāts no plāna, ko skripts pārbauda.
- Katrs punkts pārbaudīts pret VZD adrešu reģistru un pašvaldības robežu.
- **Atradām kļūdas oficiāli apstiprinātos plānos:** Jūrmalas pulcēšanās vieta Nr. 10 (Melluži) plānā ir Lietuvā — 56,064 vietā 56,964 (~100 km kļūda; pārbaudīts oriģinālajā PDF, lpp. 85, un VZD adrešu reģistrā — sk. `notes/presentation_ideas.md`). Kopā 41 koordinātu kļūda.
- Krīzes meklētājs saprot brīvu tekstu LV/RU/EN: **127 scenāriji**, **95 % pareizi uz 563 vaicājumiem** (bija 77 %; uz neredzētajiem 89,5 %). MI palīdzēja uzrakstīt atslēgvārdus un testus; darbības laikā MI nav — noteikumi, nevis ģenerēts teksts.

**Say:** MI šeit nav čatbots — tas ir auditors. Tas pārvērta dokumentus, ko neviens nelasa, datos, kurus var pārbaudīt — un tas atrada kļūdas, ko neviens nebija pamanījis.

## 7:15–8:30 · 7. Atvērtie dati

**Slide (criterion 5, one line on top):** "32 atvērto datu avoti, katrs ar licenci: CC0, CC BY 4.0, ODbL vai oficiāls dokuments (Autortiesību likuma 6. p.). Trīs izņēmumi atklāti atzīmēti ⚠."

Grid, each with licence:
- **VZD** adrešu reģistrs (CC BY 4.0) · **42 pašvaldību CA plāni** (oficiāls dokuments) · **VM** 24/7 slimnīcas (oficiāls dokuments)
- **IeM IC** ārstniecības iestādes, VP iecirkņi, pašvaldības policija, VUGD depo (CC0) · **ZVA** aptiekas (CC0)
- **LVĢMC** ūdens līmenis, hidroloģiskās prognozes, brīdinājumi, plūdu riska kartes, prognozes apdzīvotām vietām (dienas un ikstundas — viena datu kopa), meteoroloģiskie novērojumi, zibens režģis (CC0) — 7
- **FMI** zibens, pēdējās 30 min (CC BY 4.0) · **Open-Meteo** nokrišņi un augsne (CC BY 4.0) · **LVC** ceļu notikumi un satiksme caur NAP (CC0)
- **VKCP IĢIS** ūdens ņemšanas vietas (CC0) · **GTFS** Rīgas satiksme, ATD autobusi, VIVI vilcieni (CC0) — 3
- **UR** publisko personu un iestāžu saraksts — pašvaldību kontakti (CC0) · **VPVKAC** kontaktpunkti (CC0)
- **OpenStreetMap** (ODbL), 6 slāņi: bankomāti un DUS, noturības punktu kandidāti, dzeramais ūdens, bezmaksas Wi-Fi, elektroauto uzlāde, veterinārās klīnikas · **OpenStreetMap** karšu fons (ODbL) · **OpenTopoMap** reljefs (CC BY-SA)
- ⚠ VUGD/112.lv patvertnes (781) · ⚠ banku bankomātu saraksts (845, Finance Latvia) · ⚠ Latvijas Radio LR1 frekvences (16 raidītāji) — licence nav norādīta
- (extra, demo only, not in the count) **LĢIA** 20 m augstuma modelis (CC BY 4.0), demo scenārijā "Plūdi Ogrē"

Count (authoritative, 2026-10-10 night): **32 open + 3 ⚠**. Sum of the grid: VZD 1 + CA plāni 1 + VM 1 + IeM IC 4 + ZVA 1 + LVĢMC 7 + FMI 1 + Open-Meteo 1 + LVC/NAP 1 (one publisher feed: events, traffic, border wait, slippery roads) + VKCP 1 + GTFS 3 + UR 1 + VPVKAC 1 + OSM 6 + OSM karšu fons 1 + OpenTopoMap 1 = 32. One count = one row in the "Datu avoti" panel (`shema.sql` avoti + `avoti.js` TIESSAISTE); the panel counts the same way and lists the 2 **simulated** prototype sets (water and charging points, marked "SIMULĒTI DATI — prototips") separately, not in the 32. Not counted: LĢIA DEM (demo only), the OSRM route service (OSM data), our own residents' reports (CC BY 4.0). Until the VPS applies `shema.sql` from #110/#118 the live panel shows fewer rows (osm-udens, osm-wifi, osm-ev, osm-vet, bankas-atm missing). Slide version: `production/slaidi.html` slide 10.

**Say:** Katrs punkts kartē rāda savu avotu un licenci. Kur licences nav (patvertnes, banku bankomāti, radio frekvences), mēs to atklāti norādām — un aicinām VUGD to publicēt data.gov.lv. Un statusa lapā redzams, vai katrs avots šobrīd atbild.

## 8:30–9:30 · 8. Kas tālāk / ietekme

**Slide:** Trīs nākamie soļi
1. **Pašvaldībām:** "Plāna kvalitātes pārskats" — kas trūkst, kur kļūdas (41 koordinātu kļūda, 10 pašvaldības bez publiskām pulcēšanās vietām). Var darbināt katru reizi, kad plāns tiek atjaunots.
2. **Iedzīvotājiem:** iekļaut 112 Latvija lietotnē / Latvija.gov.lv (VDAA principi: "tikai vienreiz", 3 soļi, kopsavilkums).
3. **Datu turētājiem:** konkrēti lūgumi ir sagatavoti (`notes/vestules.md`, saraksts map.repo.lv/trukstosie.html): VUGD (patvertnes CC0, LV-ALERT arhīvs), Sadales tīkls (atslēgumi), LVĢMC (sliekšņi, dziļumi), 10 pašvaldības (pielikumi), Rīgas satiksme (GTFS-Realtime), LVC, VARAM/VDAA.

## 9:30–10:00 · 9. Noslēgums

**Slide:** "Katalogs un PDF → atbilde, ko katrs saņem 30 sekundēs." · map.repo.lv · QR kods · komanda.

---

## Demo checklist (before judging)

- [ ] **Freeze `main`** 1 h before judging — every merge goes live within a minute.
- [x] "Kas notiks tālāk" block in the result card (#54).
- [ ] Test the 3 demo deep links (`?demo=vetra-2026`, `?demo=pludi-ogre`, `?demo=nakts`) on a phone.
- [ ] NAP keys set? If not, say so on slide 7 (see the count note).
- [ ] Run the exact demo path on 2 real phones (Android + iPhone), with location allowed AND denied.
- [ ] Record a screen video of the full demo as a backup; put screenshots in the slides.
- [ ] Just before going on stage: map.repo.lv/statuss.html all green (flood WMS is often yellow = slow; warm "plūdi Mednieku iela 9 Ogre" once), address search, warnings banner, water level.
- [ ] Screenshot of the Jūrmala plan page 85 (original PDF) + map with the point in Lithuania vs the real one.
- [ ] Screenshot of geolatvija.lv first screen (cookie + promo modal) for slide 3.
- [ ] QR code to map.repo.lv on the last slide.
- [ ] Decide who speaks which part (3 people: problem + geolatvija + solution / demo / AI + data + next).

## Likely judge questions

- **"Kāpēc ne čatbots?"** Krīzē vajag ātru, pārbaudāmu atbildi ar avotu, nevis ģenerētu tekstu. MI strādā datu sagatavošanā un pārbaudē; atbilde lietotājam ir deterministiska un citē avotu.
- **"Kāpēc nav soļu?"** Soļi ir trīs (vieta → vajadzība → rezultāts); mēs uzbūvējām arī 4 ekrānu versiju un to apzināti aizstājām ar vienu kartīti, jo krīzē cilvēks neklikšķina cauri ekrāniem.
- **"Cik dati ir aktuāli?"** Ūdens līmenis — ik stundu; brīdinājumi un ceļi — ik 5–10 min; zibens — ik minūti; plāni — pēc publicēšanas datuma, rādām plāna lappusi. Statusa lapa rāda katra avota pēdējo pārbaudi.
- **"Kā ar geolatvija.lv?"** Mēs to neaizstājam — tas ir plānotāju rīks un mūsu datu avots. Mēs esam iedzīvotāja skats virs tiem pašiem datiem.
- **"Personas dati?"** Atrašanās vieta paliek telefonā. Meklējumus skaitām tikai bez adresēm un cipariem, bez IP un lietotāja datiem.
- **"Drošība kara laikā?"** Rādām tikai publiski pieejamas vietas; kritiskā infrastruktūra (ģeneratori, apakšstacijas) kartē netiek likta.
- **"Kā pašvaldība to uztur?"** Plāna atjaunošana → tas pats MI process no jauna → pārskats ar izmaiņām un kļūdām. Valsts datus serveris atjauno pats katru nakti (04:30), un statusa lapa rāda datu vecumu.
- **"Kāpēc darbības laikā nav LLM?"** Krīzē atbildei jābūt ātrai, vienādai visiem un pārbaudāmai; LLM var izdomāt adresi vai numuru. MI izmantojām tur, kur var pārbaudīt: 42 plānu izvilkšanai ar citātu un lappusi, meklētāja atslēgvārdiem un testiem (95 % uz 563 vaicājumiem, 89,5 % uz neredzētajiem). Rezultāts strādā arī bez interneta no saglabātajiem datiem, un nav API izmaksu.
- **"Kas notiek, ja LVĢMC (vai cits avots) nedarbojas?"** API rāda pēdējo zināmo vērtību un atjauno fonā (stale-while-revalidate); ja avots nedarbojas, kartīte to pasaka, nevis klusē. map.repo.lv/statuss.html rāda katra avota stāvokli ik 15 min un datu vecumu.
- **"Ziņojumu un meklējumu privātums?"** Ziņojumiem neglabājam IP; vieta glabāta ~100 m, publiski ~1 km; teksti ar saitēm un rupjībām netiek pieņemti; moderators var paslēpt. Meklējumus skaitām tikai bez cipariem un adresēm, bez IP.
- **"Patvertņu licence?"** 112.lv sarakstam licence nav norādīta — kartē tas ir atzīmēts ⚠, un VUGD vēstulē lūdzam to publicēt data.gov.lv ar CC0 un ietilpību, pieejamību, dzīvniekiem un statusu.
- **"Vai izturēs slodzi?"** Savienojumu rinda 5 → 128, kešs bez gaidīšanas: lokālā slodzes testā ar 50 klientiem p95 1,1 s (bija 12,4 s) un 0 savienojuma kļūdu (`notes/slodze.md`). Statiskā lapa ir bez būves soļa. Karte ielādē tikai redzamo apgabalu: 958 KB → 104 KB, tas ir svarīgi lēnā mobilajā tīklā (#114).
- **"Kas ir simulēts?"** Tikai demo scenāriji (zīme „SIMULĀCIJA”) un divi CSV slāņi — dzeramā ūdens un uzlādes punkti (zīme „SIMULĒTI DATI — prototips”). Viss pārējais ir dzīvi atvērtie dati.
- **"Rīgas sabiedriskais transports?"** Atvērts ir tikai statiskais GTFS (CC0) — to rādām kā pieturas. Reāllaika atvērtu datu nav; lūgums Rīgas satiksmei par GTFS-Realtime ar CC0 ir sagatavots (`notes/vestules.md`).
