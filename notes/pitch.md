# Pitch: "Mana adrese krīzē" (10 min)

Draft 2026-10-09. Numbers marked **[A]** come from the CA-plan extraction (`notes/ca-plani-kvalitate.md`) — fill in when it lands. Spoken in Latvian; slide text below is what goes on screen.

Judging criteria → where we answer them: concrete outcome (slides 4–5), only once (3, 6), 3–6 step flow (4), works on a phone (live demo), AI + open data (6–7).

---

## 0:00–1:00 · 1. Problēma (hook)

**Slide:** "2026. gada 22. augusts. Vētra. ~277 000 mājsaimniecību bez elektrības."
Below: "Kur man iet? Vai mana māja ir plūdu zonā? Kur ir siltums un ūdens?"

**Say:** Augusta vētrā simtiem tūkstošu cilvēku palika bez elektrības. Viņu pašvaldībai ir civilās aizsardzības plāns — tajā ir rakstīts, kur pulcēties, kur izmitina, kas ir bīstams. Bet neviens to neatrada, jo tas ir 200+ lappušu PDF.

## 1:00–2:00 · 2. Kāpēc tā ir

**Slide:** 42 pašvaldības · 42 dažādi PDF · 200–800 lpp. katrs · 1 791 karte kā attēls, nevis dati.
- Cēsīs, Jelgavā, Liepājā pulcēšanās vietas publiski **nav pieejamas** (pielikums "ierobežotas pieejamības" vai nepublicēts).
- Nevienā plānā nav siltuma, ūdens vai pārtikas izdales punktu, nav radio frekvences.

**Say:** Informācija eksistē, bet ne tādā formā, kas cilvēkam palīdz krīzes brīdī — telefonā, ar 5% baterijas.

## 2:00–3:00 · 3. Risinājums

**Slide:** map.repo.lv — "Ievadiet adresi. Saņemiet savu krīzes karti."
Viena lapa: Jūsu pulcēšanās vieta · patvertne · izmitināšana · plūdu zona · upes līmenis · brīdinājumi · 24/7 slimnīca · ko darīt tālāk.

**Say:** Mēs neko neprasām, ko valsts jau zina. Adrese — no VZD adrešu reģistra vai telefona. Pārējais — no atvērtajiem datiem un pašvaldību plāniem.

## 3:00–6:00 · 4–5. LIVE DEMO (telefonā, ekrāns spoguļots)

Scenario: **Ogre, plūdi** (Daugava, Ķeguma HES augšpus — Ogres plāns ir pilnīgākais).
1. *Kur Jūs atrodaties?* → ierakstu "Ogre, Brīvības iela …" (VZD autocomplete).
2. *Kas notiek?* → "Plūdi".
3. *Jūsu situācija* → "kustību ierobežojumi", "mājdzīvnieks".
4. *Kopsavilkums* → pulcēšanās vieta X m (avots: Ogres CA plāns, lpp. N), izmitināšana ar vietu skaitu, plūdu zona jā/nē, Daugavas līmenis pret kritisko atzīmi, LVĢMC brīdinājums, padoms "zvaniet 112 un lūdziet palīdzību evakuācijā", maršruts, "Saglabāt karti" (strādā bez interneta).

Second, 30 s: free text "cilvēks nav pie samaņas" → uzreiz sarkana poga **Zvanīt 112**. Shows no dead ends and life-first.

Backup if venue Wi-Fi fails: screen recording on the laptop (record it tomorrow morning!) + screenshots in the slides.

## 6:00–7:30 · 6. Kā izmantots MI

**Slide:** "MI izlasīja 42 plānus un izvilka [A] vietas — ar atsauci uz lappusi."
- MI aģenti (Claude Code) pārveidoja plānu tabulas un tekstu strukturētos datos: pulcēšanās vietas, izmitināšana ar ietilpību.
- Katrs punkts pārbaudīts pret VZD adrešu reģistru un pašvaldības robežu.
- **Atradām kļūdas oficiāli apstiprinātos plānos:** Jūrmalas pulcēšanās vieta Nr. 10 (Melluži) — platums 56,064 (pareizi ≈ 56,96, ~100 km kļūda) **[A: + citas]**.
- Krīzes meklētājs saprot brīvu tekstu LV/RU/EN: 125 scenāriji, 122 testi.

**Say:** MI šeit nav čatbots — tas ir auditors. Tas pārvērta dokumentus, ko neviens nelasa, datos, kurus var pārbaudīt — un tas atrada kļūdas, ko neviens nebija pamanījis.

## 7:30–8:30 · 7. Atvērtie dati

**Slide:** logo/name grid, each with licence:
VZD adrešu reģistrs (CC BY) · pašvaldību CA plāni (42) · VUGD/112.lv patvertnes (781) · LVĢMC ūdens līmeņi + brīdinājumi (CC0) · plūdu riska zonas · VM 24/7 slimnīcas · IeM IC ārstniecības iestādes, policija, VUGD depo (CC0) · ZVA aptiekas (CC0) · OpenStreetMap.

**Say:** Katrs punkts kartē rāda savu avotu un licenci. Kur licences nav (patvertnes), mēs to atklāti norādām — un aicinām VUGD to publicēt data.gov.lv.

## 8:30–9:30 · 8. Kas tālāk / ietekme

**Slide:** Trīs nākamie soļi
1. **Pašvaldībām:** "Plāna kvalitātes pārskats" — kas trūkst, kur kļūdas ([A] kļūdas, N pašvaldības bez publiskām pulcēšanās vietām). Var darbināt katru reizi, kad plāns tiek atjaunots.
2. **Iedzīvotājiem:** iekļaut 112 Latvija lietotnē / Latvija.gov.lv (VDAA principi jau ievēroti: vienreiz, 4 soļi, kopsavilkums).
3. **Reāllaikā:** elektrības atslēgumi (Sadales tīkls), ceļu slēgumi (LVC), patvertņu statuss — atvērta/pilna.

## 9:30–10:00 · 9. Noslēgums

**Slide:** "Plāns, ko neviens nelasa → atbilde, ko katrs saņem 30 sekundēs." · map.repo.lv · QR kods · komanda.

---

## Demo checklist (morning of Oct 10)

- [ ] **Freeze `main`** 1 h before judging — every merge goes live within a minute.
- [ ] Run the exact demo path on 2 real phones (Android + iPhone), with location allowed AND denied.
- [ ] Record a screen video of the full demo as a backup; put screenshots in the slides.
- [ ] Check `/api/veseliba`, address search, water level, warnings banner just before going on stage.
- [ ] Fill in all **[A]** numbers from `notes/ca-plani-kvalitate.md`; double-check the Jūrmala error against the original PDF (`originali/jurmala/AVOTS.md`) so we can say it with confidence.
- [ ] QR code to map.repo.lv on the last slide.
- [ ] Decide who speaks which part (3 people: problem+solution / demo / AI+data+next).

## Likely judge questions

- **"Kāpēc ne chatbots?"** Krīzē vajag ātru, pārbaudāmu atbildi ar avotu, nevis ģenerētu tekstu. MI strādā datu sagatavošanā un pārbaudē; atbilde lietotājam ir deterministiska un citē avotu.
- **"Cik dati ir aktuāli?"** Ūdens līmenis — ik stundu; brīdinājumi — kešoti; plāni — pēc publicēšanas datuma, rādām plāna versiju un lappusi.
- **"Personas dati?"** Neko neglabājam; atrašanās vieta paliek telefonā; karte saglabāta tikai pārlūkā (localStorage). Plānos esošos privātos tālruņus neizmantojam.
- **"Drošība kara laikā?"** Rādām tikai publiski pieejamas vietas; kritiskā infrastruktūra (ģeneratori, apakšstacijas) kartē netiek likta.
- **"Kā pašvaldība to uztur?"** Plāna atjaunošana → tas pats MI process no jauna → pārskats ar izmaiņām un kļūdām.
