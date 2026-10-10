# Pitch: "Ko Jums vajag?" — map.repo.lv (10 min)

Slides: `production/slaidi.html` (https://map.repo.lv/slaidi.html; ← → keys, N notes, T timer; screenshots: D's phone shots as WebP in `production/slaidi/` (40–78 KB each, from `C:\Users\ZX202\kodi\demo-video`); slide 11 "Trūkstošie dati" from `notes/missing_data.md`, full list at https://map.repo.lv/trukstosie.html). Updated 2026-10-10 for the search-first product (#38) and batch 2 (#44–#54); everything below is merged and live. **[NAP]** = shown only once the NAP keys are set on the VPS. Spoken in Latvian; slide text below is what goes on screen.

Judging criteria → where we answer them: 1 concrete outcome (slides 4–5), 2 only once (3, 6), 3 the 3–6 step flow + summary + ending (slide 5, the sentence in bold), 4 works on a phone (live demo + statuss.html), 5 AI + open data (6–7).

---

## 0:00–1:00 · 1. Problēma (hook)

**Slide:** "2026. gada 22.–23. augusts. Vētra. ~260 000 elektrības lietotāju skāra atslēgumi." (verified: LSM 26.08.2026 and Sadales tīkls; ~245 000 at one moment on 23 Aug; sources in `notes/demo-scenariji.md` §6)
Below: "Kur man iet? Vai mana māja ir plūdu zonā? Kur ir siltums un ūdens?"

**Say:** Augusta vētrā elektrības atslēgumi skāra ap 260 000 lietotāju. Viņu pašvaldībai ir civilās aizsardzības plāns — tajā ir rakstīts, kur pulcēties, kur izmitina, kas ir bīstams. Bet neviens to neatrada, jo tas ir 200+ lappušu PDF.

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
2. **Vajadzība:** ierakstu "plūdi Mednieku iela 9 Ogre" (vai pieskaros "Biežāk meklētais" ieteikumam).
3. **Rezultāts — viena kartīte:**
   - LVĢMC brīdinājums šai vietai (ja ir);
   - lēmums: adrese ir / nav plūdu riska zonā (LVĢMC kartes); zona kartē kā laukums ar robežu, pārklāšanās ar brīdinājuma apgabalu iesvītrota;
   - tuvākā upes stacija ar līmeni un 24 h izmaiņu; "Nokrišņi un augsne" rinda (Open-Meteo); ceļu slēgumi 5 km rādiusā (LVC) **[NAP]**;
   - tuvākā pulcēšanās vieta un pagaidu izmitināšana ar vietu skaitu un saiti uz CA plāna lappusi; patvertne; 24/7 slimnīca; maršruta saites;
   - padoms scenārijam; "Kas notiks tālāk" (#54).

Second, 20 s: free text "cilvēks nav pie samaņas" → kartītes augšā sarkana rinda "zvaniet 112". **No buttons, no tel: links** (team decision) — say: "mēs nerādām pogu, mēs pasakām skaidri".

Third, 30 s — demo panel (#53), deep links (open them from a QR or bookmarks, each with the "SIMULĀCIJA" badge):

| Kods | Scenārijs | What to point at |
|---|---|---|
| `?demo=vetra-2026` | 2026-08-22/23 vētras atkārtojums (Bauska) | simulēti elektrības atslēgumu apgabali; reālie bankomāti un DUS tajos |
| `?demo=pludi-ogre` | Ogre, plūdi → augstiene ≥23 m (LĢIA DEM) | kur iet, ja pulcēšanās vieta applūst |
| `?demo=nakts` | Nakts, sagriezta roka (Saulkrasti, 03:00) → 24/7 neatliekamā | viena atbilde, nevis saraksts |

Pick 2 of the 7 for the 30 s; the others for questions: `vejs` (dzeltenais, vējš), `vetra` (sarkanais, vētra), `drons` (Rēzekne, 1 km slēgta zona), `bez-sakariem` (bez elektrības un sakariem; `&regions=100003470` = Ogre). Why 23 m and not 15 m: in Ogre the Daugava is at ~17–18 m, so ≥15 m covers 99.6 % of the area (`notes/demo-scenariji.md` §5). Say "simulācija" every time: the data in these is not live.

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

**Slide (criterion 5, one line on top):** "20 avoti: 19 atvērti, katrs ar licenci: CC0, CC BY 4.0, ODbL vai oficiāls dokuments (Autortiesību likuma 6. p.). Viens izņēmums atklāti atzīmēts ⚠."

Grid, each with licence:
- **VZD** adrešu reģistrs (CC BY 4.0) · **42 pašvaldību CA plāni** (oficiāls dokuments) · **VM** 24/7 slimnīcas (oficiāls dokuments)
- **IeM IC** ārstniecības iestādes, VP iecirkņi, pašvaldības policija, VUGD depo (CC0) · **ZVA** aptiekas (CC0)
- **LVĢMC** ūdens līmenis, brīdinājumi, plūdu riska kartes, prognozes apdzīvotām vietām (CC0) · zibens režģis (CC0)
- **FMI** zibens, pēdējās 30 min (CC BY 4.0) · **Open-Meteo** nokrišņi un augsne (CC BY 4.0) · **LVC** ceļu slēgumi un negadījumi caur NAP (CC0)
- **OpenStreetMap** bankomāti un DUS (ODbL) · **OpenStreetMap** karšu fons (ODbL) · **OpenTopoMap** reljefs (CC BY-SA)
- ⚠ VUGD/112.lv patvertnes (781) — licence nav norādīta
- (extra, demo only, not in the count) **LĢIA** 20 m augstuma modelis (CC BY 4.0), demo scenārijā "Plūdi Ogrē"

Count: **19 open + 1 ⚠ = 20**, exactly as the "Datu avoti" panel shows them (#56; OSM POIs and the OSM basemap are two rows there, LĢIA is demo-only). Slide version: `production/slaidi.html` slide 10.

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
- **"Kā pašvaldība to uztur?"** Plāna atjaunošana → tas pats MI process no jauna → pārskats ar izmaiņām un kļūdām.
