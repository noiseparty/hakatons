# Vēstules datu turētājiem (melnraksti, gatavi sūtīšanai)

Sagatavots 2026-10-10. Katra vēstule ir vienā lappusē: ko lūdzam, kāpēc (viens krīzes piemērs no mūsu demo) un kādā formātā. Pamatojums un pilns saraksts: `notes/missing_data.md` → https://map.repo.lv/trukstosie.html. Adreses: tabula beigās (tikai iestāžu vispārējās adreses no to tīmekļvietnēm). Pirms sūtīšanas ierakstiet komandas kontaktu vietā **[komandas e-pasts]**.

Kopīgā paraksta daļa (visām vēstulēm):

> Ar cieņu,
> map.repo.lv komanda — VARAM / LATA „AI atvērto datu” hakatons 2026, krīžu vadības virziens
> Prototips: https://map.repo.lv · trūkstošo datu saraksts: https://map.repo.lv/trukstosie.html · pirmkods: https://github.com/noiseparty/hakatons
> Kontakts: [komandas e-pasts]

---

## 1. VUGD — patvertņu saraksts un LV-ALERT arhīvs

**Kam:** Valsts ugunsdzēsības un glābšanas dienests · **Temats:** Lūgums publicēt patvertņu sarakstu un LV-ALERT ziņojumus kā atvērtos datus

Labdien!

Hakatonā izveidojām karti https://map.repo.lv. Iedzīvotājs ieraksta, kas notiek un kur, un saņem vienu atbildi: tuvākā patvertne, pulcēšanās vieta, 24/7 slimnīca, brīdinājumi. „Tuvākā patvertne” ir visbiežākais jautājums. Šobrīd rādām 781 patvertni no 112.lv kartes, bet ar brīdinājumu „licence nav norādīta”, jo saraksts nav publicēts kā atvērtie dati.

**Lūdzam:**
1. Publicēt publisko patvertņu sarakstu portālā **data.gov.lv** ar **CC0** licenci (CSV un GeoJSON, WGS-84). Papildus pašreizējai adresei un ēkas veidam lūdzam laukus: **ietilpība** (cilvēki), **piekļūstamība ar ratiņkrēslu** (jā/nē), **vai pieņem mājdzīvniekus**, **atbildīgā iestāde** un, ja iespējams, **statuss** (atvērta / pilna / slēgta) kā atsevišķa, bieži atjaunota datne vai API.
2. Publicēt izsūtītos **LV-ALERT** šūnu apraides ziņojumus (laiks, līmenis, teritorija, teksts, „draudi beigušies”) kā plūsmu (CAP XML / Atom) un arhīvu, lai kartes un lietotnes varētu rādīt to pašu, ko tālrunis, un lai tos varētu izmantot mācībām.

**Kāpēc:** mūsu demo scenārijā „sarkanais brīdinājums: vētra” karte parāda tuvāko patvertni, bet nevar pateikt, vai tur ir vieta, vai var ienākt ar ratiņkrēslu un vai var ņemt līdzi suni. Tieši šos jautājumus cilvēki uzdod.

---

## 2. Sadales tīkls — elektroapgādes atslēgumi

**Kam:** AS „Sadales tīkls” · **Temats:** Lūgums publicēt elektroapgādes atslēgumu datus mašīnlasāmā formā

Labdien!

Hakatonā izveidojām krīzes karti https://map.repo.lv. 2026. gada 22.–23. augusta vētrā atslēgumi skāra ap 260 000 lietotāju. Iedzīvotāji meklēja, kur ir elektrība, siltums un iespēja uzlādēt telefonu. Jūsu atslēgumu karte ir publiska, bet nav pieejama kā dati ar licenci, tāpēc to nevar parādīt citās kartēs un lietotnēs.

**Lūdzam:** publicēt neplānoto (un plānoto) atslēgumu plūsmu **GeoJSON** vai JSON API formātā ar laukiem: atslēguma **teritorija** (poligons vai adrešu saraksts), **sākuma laiks**, **prognozētais atjaunošanas laiks**, skarto lietotāju skaits, statuss. Ar atvērtu licenci (**CC0** vai CC BY 4.0) un atjaunošanu vismaz ik 15 minūtes.

**Kāpēc:** demo scenārijā „vētras 22.–23.08.2026 atkārtojums” mums atslēgumu apgabali ir jāsimulē. Ar Jūsu datiem karte rādītu īstos apgabalus un tuvāko vietu ārpus tiem, kur ir elektrība (bankomāts, DUS, sasilšanas vieta).

---

## 3. LVĢMC — upju bīstamības sliekšņi, plūdu dziļumi, līmeņu pārrēķins, licences

**Kam:** VSIA „Latvijas Vides, ģeoloģijas un meteoroloģijas centrs” · **Temats:** Lūgums par hidroloģisko datu papildināšanu atvērtajos datos

Labdien!

Krīzes kartē https://map.repo.lv izmantojam LVĢMC atvērtos datus (CC0): ūdens līmeni 74 stacijās, brīdinājumus, prognozes, plūdu riska kartes. Paldies par tiem! Četras lietas palīdzētu iedzīvotājam saņemt lēmumu, nevis tikai skaitli:

1. **Bīstamības sliekšņi** (PRIS: level_1/2/3) katrai hidroloģiskajai stacijai, pievienoti data.gov.lv hidroloģisko novērojumu kopai ar CC0. Šobrīd tie ir pieejami tikai bez licences.
2. **Plūdu dziļuma rastri** pa scenārijiem (10 %, 1 %, 0,5 %) kā atvērtie dati. Šobrīd ir tikai applūstošo teritoriju robežas.
3. **Pārrēķina tabula** starp staciju nulli (cm) un m LAS-2000,5 (prognozes ir m v.j.l., novērojumi cm virs posteņa nulles).
4. Vienota **CC0** licence arī ĢeoLatvija.lv ģeoservisiem (WMS/WFS), kas katalogā atzīmēti CC BY-NC, lai gan tie paši dati data.gov.lv ir CC0.

**Kāpēc:** demo „Plūdi Ogrē” iedzīvotājs redz Daugavas līmeni un 24 h izmaiņu, bet nevar uzzināt, vai tas ir bīstami un cik dziļš ūdens būs pie viņa mājas.

**Formāts:** CSV/JSON datu kopā data.gov.lv (sliekšņi, pārrēķins), GeoTIFF (dziļumi).

---

## 4. Pašvaldības — evakuācijas pulcēšanās un pagaidu izmitināšanas vietas

**Kam:** 12 pašvaldības (tabula zemāk; kopīgie plāni — vienai pašvaldībai) · **Temats:** Lūgums publicēt evakuācijas pulcēšanās un izmitināšanas vietas kā atvērtos datus

Labdien!

Hakatonā ar MI izlasījām visu 42 pašvaldību civilās aizsardzības plānus un izvilkām 730 pulcēšanās vietas un 579 pagaidu izmitināšanas vietas, katrai ar plāna lappusi. Tās ir kartē https://map.repo.lv. Jūsu pašvaldības plānā šīs vietas ir pielikumos, kas nav publicēti vai ir atzīmēti kā ierobežotas pieejamības (sk. tabulu). Tāpēc iedzīvotājs, kas karti atver krīzē, saņem tuvāko vietu kaimiņu pašvaldībā.

**Lūdzam:** publicēt vismaz **pulcēšanās vietu** sarakstu (pēc būtības tās ir publiskas vietas, uz kurām jāatnāk ikvienam), ja iespējams arī **pagaidu izmitināšanas vietas**, kā **CSV vai GeoJSON**, piemēram, data.gov.lv vai pašvaldības vietnē. Lauki: nosaukums, adrese, koordinātas (WGS-84), ietilpība (cilvēki), gultas, ēdināšana (jā/nē), piekļūstamība ar ratiņkrēslu. Ja daļa ziņu ir jāierobežo (piem., resursi, kontaktpersonas), lūdzam publicēt pārējo.

**Kāpēc:** demo „Plūdi Ogrē” iedzīvotājs uzreiz redz, kur jāiet, ar maršrutu un saiti uz plāna lappusi. Jūsu iedzīvotājiem šīs atbildes šobrīd nav.

| Pašvaldība | Kas plānā norādīts | Stāvoklis |
|---|---|---|
| Alūksnes novads | 6. pielikums (pulcēšanās), 7. (iespējamās evakuācijas vietas), 10. (izmitināšana; 7.7. sadaļā minēts 9.) | pielikumi nav publicēti |
| Cēsu novads | 12. pielikums (pulcēšanās), 19. (izmitināšana, „Ierobežota pieejamība”) | publicēts plāns „bez pielikumiem” |
| Jelgavas valstspilsēta un Jelgavas novads (kopīgs plāns, 2 sējumi) | pilsēta: 5. (pulcēšanās), 7. (izmitināšana); novads: 6. un 8. | pielikumi nav publicēti |
| Jēkabpils novads | 22. pielikums (pulcēšanās), 24. (izmitināšana, ēdināšana) | publicēti tikai daži citi pielikumi |
| Liepājas valstspilsēta un Dienvidkurzemes novads (kopīgs plāns) | 12. pielikums (pulcēšanās; 6.2. nodaļā tabula nav), 7. (izmitināšana, ~35 000 vietu) | pielikumi nav publicēti |
| Līvānu novads | 7. pielikums (pulcēšanās; „koordinātas tiek paziņotas atsevišķi”) | pielikumi nav publicēti |
| Siguldas novads | 9. pielikums (pulcēšanās; sarakstā publisks), 5. (izmitināšana, ierobežota) | publicēts tikai 27. pielikums |
| Valmieras novads | 5. pielikums (pulcēšanās), 7. (izmitināšana), abi „(elektroniski)” | pielikumi nav publicēti |
| Ventspils valstspilsēta un Ventspils novads (kopīgs plāns) | 4.–16. pielikums (pa pagastiem; 14. — Ventspils pilsēta), plāna 48. un 50. lpp. | publiskajā failā tikai titullapas „Ierobežotas pieejamības informācija” |

Ventspils vēstulē var pievienot: „Plāna 3.1.4. sadaļā (PDF 48. lpp.) teikts: „Pulcēšanās vietām jābūt pieejamām jebkuram iedzīvotājam.” Lūdzam tās arī publicēt.”

---

## 5. Rīgas satiksme — reāllaika sabiedriskā transporta dati

**Kam:** RP SIA „Rīgas satiksme” · **Temats:** Lūgums publicēt GTFS-Realtime datus ar atvērtu licenci

Labdien!

Paldies, ka maršrutu saraksti jau ir publicēti data.gov.lv kā GTFS ar CC0. Krīzes kartē https://map.repo.lv tos izmantojam pieturu slānim.

**Lūdzam:** publicēt arī reāllaika datus **GTFS-Realtime** formātā: **VehiclePositions**, **TripUpdates**, **ServiceAlerts**. Ar **CC0** licenci un dokumentētu piekļuves adresi (bez atslēgas vai ar vienu bezmaksas atslēgu). Šobrīd reāllaika pozīcijas redzamas saraksti.lv, bet bez dokumentācijas un licences, tāpēc citi tās nevar izmantot.

**Kāpēc:** vētrā vai evakuācijas laikā iedzīvotājiem ir jāzina, kuri maršruti kursē un kur ir sastrēgumi. ServiceAlerts ļautu kartē uzreiz parādīt slēgtās līnijas.

---

## 6. LVC — publiskās plūsmas bez atslēgām, ātruma ierobežojumi, temperatūras

**Kam:** VSIA „Latvijas Valsts ceļi” · **Temats:** Lūgums par Nacionālā piekļuves punkta datu pieejamību

Labdien!

Krīzes kartē https://map.repo.lv rādām LVC ceļu notikumus un satiksmi no transportdata.gov.lv (DATEX II, CC0). Paldies par atvērto licenci!

**Lūdzam:**
1. Publiskām CC0 datu kopām (ceļu notikumi, slidenums, satiksmes mērījumi) atļaut **lasīšanu bez atslēgas** vai vismaz ar **vienu atslēgu visām kopām**. Šobrīd katrai kopai vajag atsevišķu abonementu.
2. Publicēt **ātruma ierobežojumus** uz valsts autoceļiem (GeoJSON vai DATEX II), lai satiksmes ātrumu varētu salīdzināt ar atļauto.
3. Slidenuma datu kopās pievienot **ceļa un gaisa temperatūru** no ceļu meteostacijām.
4. Pārbaudīt **robežšķērsošanas gaidīšanas laika** kopu: tā mums neatbild (403 / nav datu).

**Kāpēc:** ziemas vai vētras demo scenārijā kartei jāpasaka „ceļš ir slidens, -3 °C, satiksme stāv”, nevis tikai „ir notikums”.

---

## 7. VARAM / VDAA — vienota atvērta licence ĢeoLatvija.lv

**Kam:** Viedās administrācijas un reģionālās attīstības ministrija; Valsts digitālās attīstības aģentūra (agrāk VRAA) · **Temats:** Ierosinājums par vienotu atvērtu licenci ĢeoLatvija.lv ģeoservisiem

Labdien!

Hakatona komanda izveidoja krīzes karti https://map.repo.lv uz tiem pašiem oficiālajiem datiem, kas ir ĢeoLatvija.lv: VZD, LVĢMC, LĢIA, LVC. Pamanījām, ka daudzi ĢeoLatvija.lv servisi katalogā ir atzīmēti **CC BY-NC**: plūdu riska kartes, meteostacijas, meža ugunsbīstamība. Tie paši LVĢMC dati data.gov.lv ir **CC0**. LĢIA pamatkartes un ortofoto lejupielādei ir CC BY 4.0, bet kā WMS/WMTS servisi pieejami tikai pēc e-iesnieguma.

**Ierosinām:**
1. Visiem valsts ģeoservisiem ĢeoLatvija.lv lietot vienotu atvērtu licenci (**CC0** vai **CC BY 4.0**), kas atbilst data.gov.lv.
2. LĢIA pamatkartes, ortofoto un augstuma modeli piedāvāt kā **anonīmus WMTS** servisus ar to pašu CC BY 4.0.

**Kāpēc:** nekomerciālās izmantošanas ierobežojums neļauj šos servisus izmantot nevienā produktā, arī pašvaldību vai NVO krīzes rīkos. Mūsu demo „Plūdi Ogrē, augstiene ≥23 m” LĢIA augstuma modelis bija jālejupielādē un jāapstrādā pašiem.

---

## Adreses (iestāžu vispārējās e-pasta adreses no to tīmekļvietnēm)

| Kam | Adrese | Avots (iestādes lapa) | Pārbaude |
|---|---|---|---|
| VUGD | pasts@vugd.gov.lv | https://www.vugd.gov.lv/lv/iestades-kontakti | ✓ redzēts lapā |
| AS „Sadales tīkls” | st@sadalestikls.lv | https://sadalestikls.lv/lv/kontakti | ⚠ **jāpārbauda pirms sūtīšanas** (lapa neatvērās automātiski; adrese no meklētāja kopsavilkuma) |
| LVĢMC | lvgmc@lvgmc.lv | https://videscentrs.lvgmc.lv/lapas/kontakti | ⚠ **jāpārbauda pirms sūtīšanas** (lapa ir JavaScript lietotne; „Birojs” adrese no meklētāja kopsavilkuma) |
| Rīgas satiksme | info@rigassatiksme.lv | https://www.rigassatiksme.lv/lv/kontakti/ | ✓ vispārējā adrese (e-parakstītiem dokumentiem: sekretariats@rigassatiksme.lv) |
| LVC | lvceli@lvceli.lv | https://lvceli.lv/kontakti/ | ✓ vispārējā adrese |
| VARAM | pasts@varam.gov.lv | https://www.varam.gov.lv/lv/kontakti | ✓ |
| VDAA (agrāk VRAA; vraa.gov.lv pāradresē uz vdaa.gov.lv) | pasts@vdaa.gov.lv | https://www.vdaa.gov.lv/lv/kontakti | ✓ |
| Alūksnes novada pašvaldība | dome@aluksne.lv | https://aluksne.lv/index.php/pasvaldiba/kontakti/ | ✓ |
| Cēsu novada pašvaldība | dome@cesunovads.lv | https://www.cesis.lv/lv/sazinies-ar-pasvaldibu/ | ✓ |
| Jelgavas valstspilsētas pašvaldība | pasts@jelgava.lv | https://www.jelgava.lv/lv/kontakti | ✓ |
| Jelgavas novada pašvaldība | dome@jelgavasnovads.lv | https://www.jelgavasnovads.lv/lv/kontakti | ✓ |
| Jēkabpils novada pašvaldība | pasts@jekabpils.lv | https://www.jekabpils.lv/lv/iestades-kontakti | ✓ (lapas URL secināts) |
| Liepājas valstspilsētas pašvaldība | pasts@liepaja.lv | https://www.liepaja.lv/kontakti/ | ✓ |
| Dienvidkurzemes novada pašvaldība | pasts@dkn.lv | https://www.dkn.lv/lv/dienvidkurzemes-novada-pasvaldiba | ✓ (lapas URL secināts) |
| Līvānu novada pašvaldība | pasts@livani.lv | https://www.livani.lv/lv/iestades-kontakti | ✓ (lapas URL secināts) |
| Siguldas novada pašvaldība | pasts@sigulda.lv | https://www.sigulda.lv/kontakti | ✓ |
| Valmieras novada pašvaldība | pasts@valmierasnovads.lv | https://izglitiba.valmierasnovads.lv/kontakti/ | ⚠ **jāpārbauda** (galvenajā kontaktu lapā e-pasta nav, tikai e-adrese) |
| Ventspils valstspilsētas pašvaldība | dome@ventspils.lv | https://www.ventspils.lv/lv/kontakti | ✓ (lapas strukturētajos datos) |
| Ventspils novada pašvaldība | info@ventspilsnd.lv | https://www.ventspilsnovads.lv/lv/ventspils-novada-pasvaldiba | ✓ (domēns ventspilsnd.lv; lapas URL secināts) |

Adreses pārbaudītas 2026-10-10 iestāžu tīmekļvietnēs (tikai vispārējās adreses, bez personu vārdiem). Oficiālu iesniegumu valsts un pašvaldību iestādēm var sūtīt arī uz **e-adresi** (latvija.gov.lv), ja komandai tāda ir.
