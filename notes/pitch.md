# Pitch: "Ko Jums vajag?" — map.repo.lv (10 min)

Updated 2026-10-10 for the search-first product (#38) and batch 2 (#44–#51, D's demo PR). Spoken in Latvian; slide text below is what goes on screen. **[D]** = fill in from D's demo PR (`?demo=<kods>` codes); **[gaida]** = only if that PR is merged and live by the freeze.

Judging criteria → where we answer them: 1 concrete outcome (slides 4–5), 2 only once (3, 6), 3 the 3–6 step flow + summary + ending (slide 5, the sentence in bold), 4 works on a phone (live demo + statuss.html), 5 AI + open data (6–7).

---

## 0:00–1:00 · 1. Problēma (hook)

**Slide:** "2026. gada 22.–23. augusts. Vētra. ~277 000 mājsaimniecību bez elektrības."
Below: "Kur man iet? Vai mana māja ir plūdu zonā? Kur ir siltums un ūdens?"

**Say:** Augusta vētrā simtiem tūkstošu cilvēku palika bez elektrības. Viņu pašvaldībai ir civilās aizsardzības plāns — tajā ir rakstīts, kur pulcēties, kur izmitina, kas ir bīstams. Bet neviens to neatrada, jo tas ir 200+ lappušu PDF.

## 1:00–1:45 · 2. Kāpēc tā ir

**Slide:** 42 pašvaldības · 42 dažādi PDF · 200–800 lpp. katrs · 1 791 karte kā attēls, nevis dati.
- 12 pašvaldības pulcēšanās un izmitināšanas vietas publiski **nepublicē** (pielikums "ierobežotas pieejamības" vai nav publicēts).
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
2. **Vajadzība:** ierakstu "plūdi Mednieku iela 9 Ogre" (vai pieskaros "Biežāk meklētais" ieteikumam **[gaida #45]**).
3. **Rezultāts — viena kartīte:**
   - LVĢMC brīdinājums šai vietai (ja ir);
   - lēmums: adrese ir / nav plūdu riska zonā (LVĢMC kartes); zona kartē kā laukums ar robežu, pārklāšanās ar brīdinājuma apgabalu iesvītrota **[gaida #48]**;
   - tuvākā upes stacija ar līmeni un 24 h izmaiņu; "Nokrišņi un augsne" rinda (Open-Meteo) **[gaida #50]**; ceļu slēgumi 5 km rādiusā (LVC) **[gaida #51 + NAP atslēgas]**;
   - tuvākā pulcēšanās vieta un pagaidu izmitināšana ar vietu skaitu un saiti uz CA plāna lappusi; patvertne; 24/7 slimnīca; maršruta saites;
   - padoms scenārijam; "Kas notiks tālāk" **(vēl jāuzbūvē — sk. checklist)**.

Second, 20 s: free text "cilvēks nav pie samaņas" → kartītes augšā sarkana rinda "zvaniet 112". **No buttons, no tel: links** (team decision) — say: "mēs nerādām pogu, mēs pasakām skaidri".

Third, 30 s — demo sidebar **[gaida D]**, deep links (open them from a QR or bookmarks, each with the "SIMULĀCIJA" badge):

| Kods | Scenārijs | What to point at |
|---|---|---|
| `?demo=[D]` | 2026-08-22/23 vētras atkārtojums | brīdinājumi + slēgti ceļi + bez elektrības reģionā |
| `?demo=[D]` | Ogre, plūdi → augstiene ≥15 m (LĢIA DEM) | kur iet, ja pulcēšanās vieta applūst |
| `?demo=[D]` | Nakts, sagriezta roka → 24/7 neatliekamā | viena atbilde, nevis saraksts |

Pick 2 of D's 7 scenarios for the 30 s; keep the rest for questions. Say "simulācija" every time: the data in these is not live.

Fourth, 10 s: map.repo.lv/statuss.html — "katram avotam redzams, vai tas šobrīd darbojas" (criterion 4: no dead ends, honest about outages).

Backup if venue Wi-Fi fails: screen recording on the laptop + screenshots in the slides.

## 6:00–7:15 · 6. Kā izmantots MI

**Slide:** "MI izlasīja 42 plānus un izvilka 730 pulcēšanās vietas un 579 izmitināšanas vietas (104 213 vietas) — ar atsauci uz lappusi."
- MI aģenti (Claude Code) pārveidoja plānu tabulas un tekstu strukturētos datos; katram ierakstam burtisks citāts no plāna, ko skripts pārbauda.
- Katrs punkts pārbaudīts pret VZD adrešu reģistru un pašvaldības robežu.
- **Atradām kļūdas oficiāli apstiprinātos plānos:** Jūrmalas pulcēšanās vieta Nr. 10 (Melluži) plānā ir Lietuvā — 56,064 vietā 56,964 (~100 km kļūda; pārbaudīts oriģinālajā PDF, lpp. 85, un VZD adrešu reģistrā — sk. `notes/presentation_ideas.md`). Kopā 41 koordinātu kļūda.
- Krīzes meklētājs saprot brīvu tekstu LV/RU/EN: 125 scenāriji, bez MI darbības laikā (noteikumi, nevis ģenerēts teksts).

**Say:** MI šeit nav čatbots — tas ir auditors. Tas pārvērta dokumentus, ko neviens nelasa, datos, kurus var pārbaudīt — un tas atrada kļūdas, ko neviens nebija pamanījis.

## 7:15–8:30 · 7. Atvērtie dati

**Slide (criterion 5, one line on top):** "18 atvērti avoti, katrs ar licenci: CC0, CC BY 4.0, ODbL vai oficiāls dokuments (Autortiesību likuma 6. p.). Viens izņēmums atklāti atzīmēts ⚠."

Grid, each with licence:
- **VZD** adrešu reģistrs (CC BY 4.0) · **42 pašvaldību CA plāni** (oficiāls dokuments) · **VM** 24/7 slimnīcas (oficiāls dokuments)
- **IeM IC** ārstniecības iestādes, VP iecirkņi, pašvaldības policija, VUGD depo (CC0) · **ZVA** aptiekas (CC0)
- **LVĢMC** ūdens līmenis, brīdinājumi, plūdu riska kartes, prognozes apdzīvotām vietām (CC0) · zibens režģis (CC0) **[gaida #50]**
- **FMI** zibens, pēdējās 30 min (CC BY 4.0) **[gaida #50]** · **Open-Meteo** nokrišņi un augsne (CC BY 4.0) **[gaida #50]** · **LVC** ceļu slēgumi un negadījumi caur NAP (CC0) **[gaida #51]**
- **OpenStreetMap** bankomāti, DUS, karšu fons (ODbL) · **OpenTopoMap** reljefs (CC BY-SA)
- ⚠ VUGD/112.lv patvertnes (781) — licence nav norādīta
- **LĢIA** 20 m augstuma modelis (CC BY 4.0) **[gaida D]** → 19 avoti

Count rule: 18 = all the above without ⚠ and without LĢIA. If #50/#51 are not merged by the freeze, subtract 4 (→ 14) and drop their rows.

**Say:** Katrs punkts kartē rāda savu avotu un licenci. Kur licences nav (patvertnes), mēs to atklāti norādām — un aicinām VUGD to publicēt data.gov.lv. Un statusa lapā redzams, vai katrs avots šobrīd atbild.

## 8:30–9:30 · 8. Kas tālāk / ietekme

**Slide:** Trīs nākamie soļi
1. **Pašvaldībām:** "Plāna kvalitātes pārskats" — kas trūkst, kur kļūdas (41 koordinātu kļūda, 12 pašvaldības bez publiskām pulcēšanās vietām). Var darbināt katru reizi, kad plāns tiek atjaunots.
2. **Iedzīvotājiem:** iekļaut 112 Latvija lietotnē / Latvija.gov.lv (VDAA principi: "tikai vienreiz", 3 soļi, kopsavilkums).
3. **Reāllaikā:** elektrības atslēgumi (Sadales tīkls), patvertņu statuss — atvērta/pilna; iedzīvotāju ziņojumi par bīstamību (nokritis koks, slēgts ceļš) ar moderāciju.

## 9:30–10:00 · 9. Noslēgums

**Slide:** "Katalogs un PDF → atbilde, ko katrs saņem 30 sekundēs." · map.repo.lv · QR kods · komanda.

---

## Demo checklist (before judging)

- [ ] **Freeze `main`** 1 h before judging — every merge goes live within a minute.
- [ ] **"Kas notiks tālāk" block in the result card** — not built yet; the criterion-3 sentence above names it. If it isn't live by the freeze, drop it from the sentence and slide 4.
- [ ] Fill in the `?demo=` codes from D's PR and test each deep link on a phone.
- [ ] Recount slide 7 against what is merged (see the count rule).
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
- **"Personas dati?"** Atrašanās vieta paliek telefonā. Meklējumus skaitām tikai bez adresēm un cipariem, bez IP un lietotāja datiem **[gaida #45]**.
- **"Drošība kara laikā?"** Rādām tikai publiski pieejamas vietas; kritiskā infrastruktūra (ģeneratori, apakšstacijas) kartē netiek likta.
- **"Kā pašvaldība to uztur?"** Plāna atjaunošana → tas pats MI process no jauna → pārskats ar izmaiņām un kļūdām.
