# Scenāriju padomu pārbaude pret oficiālajiem avotiem (2026-10-10)

Pārbaudīts katra scenārija `padoms` laukā `production/scenariji.json` (127 scenāriji) un `talak_gimenes`
("Kas notiks tālāk") pret VUGD, Aizsardzības ministrijas bukleta un Gaso norādēm.

**Rezultāts: 24 no 127 padomiem mainīti, 29 scenārijiem pievienots `padomu_avots`** (24 mainītie + 5, kas jau
atbilda: `koks_pari_celam`, `dumi_kapnes`, `hipotermija`, `nav_siltuma`, `udens_celas`). `talak_gimenes` pārskatīts,
nemainīts (atbilst avotiem). Atslēgvārdi (`atslegvardi`) nav aiztikti.

Kartītē avots rādās kā maza saite "Avots: VUGD" zem padoma (`padomuAvots()` failā `production/meklesana.js`,
nosaukums no saites domēna: vugd.gov.lv → VUGD, sargs.lv → Aizsardzības ministrija, lsm.lv → LSM (Gaso skaidrojums)).

## Noteikumi, kurus ievērojām

- Oficiālā secība (piem., ugunsgrēkā vispirms ārā, tad 112; plūdos negaidīt paziņojumu, ja ūdens draud).
- Padoms ≤ 5 īsiem teikumiem, "Jūs" forma, 112 kā vienkāršs teksts (nekādu `tel:` saišu), bez emocijzīmēm.
- Kur avots kaut ko nesaka (piem., "20 m no degoša auto"), apgalvojumu izņēmām, nevis atstājām nepamatotu.

## Avoti

- VUGD drošības padomi: https://www.vugd.gov.lv/lv/drosibas-padomi, apakšlapas:
  [plūdi](https://www.vugd.gov.lv/lv/pludi), [stiprs vējš, negaiss](https://www.vugd.gov.lv/lv/stiprs-vejs-negaiss),
  [elektrības padeve](https://www.vugd.gov.lv/lv/elektribas-padeve), [apkure](https://www.vugd.gov.lv/lv/apkure),
  [ugunsgrēks](https://www.vugd.gov.lv/lv/ka-rikoties-ugunsgreka-gadijuma), [degošs auto](https://www.vugd.gov.lv/lv/ka-rikoties-ja-aizdegusies-automasina),
  [meža ugunsgrēks](https://www.vugd.gov.lv/lv/ka-rikoties-meza-ugunsgreka-gadijuma), [gaisa apdraudējums](https://www.vugd.gov.lv/lv/kur-patverties-gaisa-apdraudejuma-laika),
  [vispārīgi ieteikumi](https://www.vugd.gov.lv/lv/visparigi-ieteikumi-iedzivotajiem), [ķīmiska / radiācijas avārija](https://www.vugd.gov.lv/lv/bistamu-kimisko-vielu-noplude-vai-radiacijas-avarija),
  [ūdens un ledus](https://www.vugd.gov.lv/lv/drosiba-uz-udens), [mežs](https://www.vugd.gov.lv/lv/dosanas-uz-mezu),
  [zvans 112](https://www.vugd.gov.lv/lv/ka-rikoties-kad-zvani-uz-talruna-numuru-112).
- Aizsardzības ministrija, buklets "Kā rīkoties krīzes gadījumā" (papildinātā redakcija 2024):
  https://www.sargs.lv/lv/buklets-ka-rikoties-krizes-gadijuma (PDF: https://www.sargs.lv/sites/default/files/2025-02/Buklets_K%C4%81%20r%C4%ABkoties%20kr%C4%ABzes%20gad%C4%ABjum%C4%81.pdf)
  — sirēnas (TV, radio, lsm.lv), evakuācija (13. lpp.), 72 h soma (10.–11. lpp.), apšaude (19. lpp.), ķīmiskais / kodolapdraudējums (20. lpp.).
- Gāze: LSM intervija ar Gaso (2026-01-16): https://www.lsm.lv/raksts/dzive-stils/ikdienai/16.01.2026-kapec-gazes-nopludes-laika-nedrikst-zvanit-durvju-zvanu-ikdieniski-jautajumi-par-gazi.a630312/
  (gaso.lv lapa atbildēja HTTP 403).

## Piezīmes

- VUGD ledus lapā joprojām minēts ātrās palīdzības numurs 113 (novecojis); mēs rakstām tikai 112.
- Sadales tīkla bojājumu numuram VUGD lapā ir 80 200 404; īsais 8404 arī darbojas, bet tekstos lietojam lapā norādīto.
- Medicīnas scenāriji (sirdslēkme, insults u.c.), satiksmes un kārtības scenāriji nav VUGD / AM lapu tvērumā;
  tos izlasījām, acīmredzamu kļūdu neatradām, bet pret NMPD / CSDD / VP avotiem nesalīdzinājām (iespējamais nākamais solis).
- Testa vidē (lokāls `http.server` bez API) atradām jau esošu sacensību: ja `/api/*` atbild ļoti ātri ar kļūdu,
  `app.js` izsauc `krizesMeklesana.sakt` pirms `meklesana.js` ielādes ("krizesMeklesana is not defined"). Tas nav šī PR labojums.

## Tabula

| Kods | Scenārijs | Mainīts | Kas | Avots |
|---|---|---|---|---|
| `patvertne` | Patvertne | **jā** | Sirēnas → LTV1 / Latvijas Radio; šūnu apraides ziņu izlasīt visu; divu sienu princips, tālāk no stikla | https://www.vugd.gov.lv/lv/kur-patverties-gaisa-apdraudejuma-laika |
| `medicina` | Medicīniskā palīdzība | nē | ārpus tvēruma (nav atbilstošas VUGD / AM lapas); teksts izlasīts, acīmredzamu kļūdu nav | — |
| `zales` | Zāles | nē | ārpus tvēruma (nav atbilstošas VUGD / AM lapas); teksts izlasīts, acīmredzamu kļūdu nav | — |
| `ugunsgreks` | Ugunsgrēks | **jā** | Secība kā VUGD: vispirms ārā (mantas neglābt), durvis ciet, kāpnes; 112, kad drošībā, nenolikt klausuli; neatgriezties | https://www.vugd.gov.lv/lv/ka-rikoties-ugunsgreka-gadijuma |
| `policija` | Policija un drošība | nē | ārpus tvēruma (nav atbilstošas VUGD / AM lapas); teksts izlasīts, acīmredzamu kļūdu nav | — |
| `degviela` | Degviela | nē | ārpus tvēruma (nav atbilstošas VUGD / AM lapas); teksts izlasīts, acīmredzamu kļūdu nav | — |
| `nauda` | Skaidra nauda | nē | ārpus tvēruma (nav atbilstošas VUGD / AM lapas); teksts izlasīts, acīmredzamu kļūdu nav | — |
| `apmaldijies_meza` | Apmaldījies mežā | **jā** | Nomierināties, neklīst; 112 negaidot tumsu; orientieri, meža kvartāla nr., koordinātes (lietotne „112 Latvija”); vērot glābējus. Izņemts apgalvojums „dispečers var noteikt atrašanās vietu” | https://www.vugd.gov.lv/lv/dosanas-uz-mezu |
| `pazudis_pilseta` | Apmaldījies pilsētā | nē | ārpus tvēruma (nav atbilstošas VUGD / AM lapas); teksts izlasīts, acīmredzamu kļūdu nav | — |
| `pazudis_lauku` | Apmaldījies ārpus apdzīvotām vietām | nē | ārpus tvēruma (nav atbilstošas VUGD / AM lapas); teksts izlasīts, acīmredzamu kļūdu nav | — |
| `pazudis_berns` | Pazudis bērns | nē | ārpus tvēruma (nav atbilstošas VUGD / AM lapas); teksts izlasīts, acīmredzamu kļūdu nav | — |
| `pazudis_vecs` | Pazudis gados vecs cilvēks | nē | ārpus tvēruma (nav atbilstošas VUGD / AM lapas); teksts izlasīts, acīmredzamu kļūdu nav | — |
| `apmaldijies_sniega` | Apmaldījies sniegā | nē | ārpus tvēruma (nav atbilstošas VUGD / AM lapas); teksts izlasīts, acīmredzamu kļūdu nav | — |
| `migla` | Apmaldījies biezā miglā | nē | ārpus tvēruma (nav atbilstošas VUGD / AM lapas); teksts izlasīts, acīmredzamu kļūdu nav | — |
| `nogriezies_no_grupas` | Atpalicis no grupas pārgājienā | nē | ārpus tvēruma (nav atbilstošas VUGD / AM lapas); teksts izlasīts, acīmredzamu kļūdu nav | — |
| `ieslegts_telpa` | Ieslēgts telpā (pagrabs, noliktava) | nē | ārpus tvēruma (nav atbilstošas VUGD / AM lapas); teksts izlasīts, acīmredzamu kļūdu nav | — |
| `pazudis_reljefa` | Apmaldījies kalnos vai stāvā reljefā | nē | ārpus tvēruma (nav atbilstošas VUGD / AM lapas); teksts izlasīts, acīmredzamu kļūdu nav | — |
| `pazudis_pie_udens` | Apmaldījies pie ezera vai upes | nē | ārpus tvēruma (nav atbilstošas VUGD / AM lapas); teksts izlasīts, acīmredzamu kļūdu nav | — |
| `tumsa` | Tumsa pārsteigusi ārpus mājām | nē | ārpus tvēruma (nav atbilstošas VUGD / AM lapas); teksts izlasīts, acīmredzamu kļūdu nav | — |
| `arzemes` | Apmaldījies ārzemēs | nē | ārpus tvēruma (nav atbilstošas VUGD / AM lapas); teksts izlasīts, acīmredzamu kļūdu nav | — |
| `medibas_senes` | Apmaldījies, sēņojot vai medībās | nē | ārpus tvēruma (nav atbilstošas VUGD / AM lapas); teksts izlasīts, acīmredzamu kļūdu nav | — |
| `autoavarija` | Smaga autoavārija | nē | ārpus tvēruma (nav atbilstošas VUGD / AM lapas); teksts izlasīts, acīmredzamu kļūdu nav | — |
| `deg_auto` | Deg automašīna | **jā** | Pievienota rokas bremze; „20 m” izņemts (VUGD attālumu nenorāda); pārsegu „pilnībā neatvērt”, nevis „neatvērt” | https://www.vugd.gov.lv/lv/ka-rikoties-ja-aizdegusies-automasina |
| `auto_udeni` | Automašīna iebraukusi ūdenī | nē | ārpus tvēruma (nav atbilstošas VUGD / AM lapas); teksts izlasīts, acīmredzamu kļūdu nav | — |
| `auto_gravi` | Auto noslīdējis grāvī | nē | ārpus tvēruma (nav atbilstošas VUGD / AM lapas); teksts izlasīts, acīmredzamu kļūdu nav | — |
| `auto_neiet` | Auto neiedarbojas | nē | ārpus tvēruma (nav atbilstošas VUGD / AM lapas); teksts izlasīts, acīmredzamu kļūdu nav | — |
| `elektromobilis` | Izlādējies elektromobilis | nē | ārpus tvēruma (nav atbilstošas VUGD / AM lapas); teksts izlasīts, acīmredzamu kļūdu nav | — |
| `bloketa_soseja` | Bloķēts ceļš vai šoseja | nē | ārpus tvēruma (nav atbilstošas VUGD / AM lapas); teksts izlasīts, acīmredzamu kļūdu nav | — |
| `koks_pari_celam` | Koks pāri ceļam | nē | atbilst oficiālajai lapai (avots pievienots) | https://www.vugd.gov.lv/lv/stiprs-vejs-negaiss |
| `vads_pari_celam` | Elektrības vads uz ceļa | **jā** | Sadales tīkla numurs kā VUGD lapā (80 200 404); „neļaut tuvoties citiem” | https://www.vugd.gov.lv/lv/elektribas-padeve |
| `auto_putena` | Auto iestrēdzis putenī | nē | ārpus tvēruma (nav atbilstošas VUGD / AM lapas); teksts izlasīts, acīmredzamu kļūdu nav | — |
| `dizelis_aizsalis` | Aizsalusi dīzeļdegviela | nē | ārpus tvēruma (nav atbilstošas VUGD / AM lapas); teksts izlasīts, acīmredzamu kļūdu nav | — |
| `riepa` | Pārsprāgusi riepa | nē | ārpus tvēruma (nav atbilstošas VUGD / AM lapas); teksts izlasīts, acīmredzamu kļūdu nav | — |
| `velo_moto` | Velosipēda vai motocikla avārija | nē | ārpus tvēruma (nav atbilstošas VUGD / AM lapas); teksts izlasīts, acīmredzamu kļūdu nav | — |
| `transports_apstajies` | Sabiedriskais transports apstājies | nē | ārpus tvēruma (nav atbilstošas VUGD / AM lapas); teksts izlasīts, acīmredzamu kļūdu nav | — |
| `meza_ugunsgreks` | Meža vai lauku ugunsgrēks | **jā** | Virziens: perpendikulāri uguns izplatībai (nevis vējam); brīdināt citus; ja nevar aiziet — ūdenī / mitras drēbes, pie zemes | https://www.vugd.gov.lv/lv/ka-rikoties-meza-ugunsgreka-gadijuma |
| `ugunsgreks_dzivokli` | Ugunsgrēks dzīvoklī vai mājā | **jā** | Durvju pārbaude ar roku; 112 kad drošībā; aizdūmotā gadījumā — spraugas, zīmes pie loga; augstāk par 1. stāvu nelēkt | https://www.vugd.gov.lv/lv/ka-rikoties-ugunsgreka-gadijuma |
| `spradziens` | Dzirdēts sprādziens | **jā** | AM: pagrabs / patvertne, divu sienu princips; ārā nogulties un sargāt galvu | https://www.sargs.lv/lv/buklets-ka-rikoties-krizes-gadijuma |
| `deg_kaimini` | Deg kaimiņu ēka | nē | ārpus tvēruma (nav atbilstošas VUGD / AM lapas); teksts izlasīts, acīmredzamu kļūdu nav | — |
| `kula` | Kūlas ugunsgrēks | nē | ārpus tvēruma (nav atbilstošas VUGD / AM lapas); teksts izlasīts, acīmredzamu kļūdu nav | — |
| `dumi_kapnes` | Dūmi kāpņu telpā | nē | atbilst oficiālajai lapai (avots pievienots) | https://www.vugd.gov.lv/lv/ka-rikoties-ugunsgreka-gadijuma |
| `dumi_ara` | Dūmi no liela ugunsgrēka tuvumā | nē | ārpus tvēruma (nav atbilstošas VUGD / AM lapas); teksts izlasīts, acīmredzamu kļūdu nav | — |
| `gazes_smarza` | Gāzes smaka dzīvoklī | **jā** | Gaso: neko neieslēgt UN neizslēgt (dzirkstele), nesmēķēt, nepieskarties skaitītājam, gaidīt ārā | https://www.lsm.lv/raksts/dzive-stils/ikdienai/16.01.2026-kapec-gazes-nopludes-laika-nedrikst-zvanit-durvju-zvanu-ikdieniski-jautajumi-par-gazi.a630312/ |
| `eka_sagruvusi` | Ēka daļēji sagruvusi | nē | ārpus tvēruma (nav atbilstošas VUGD / AM lapas); teksts izlasīts, acīmredzamu kļūdu nav | — |
| `sniegavetra` | Sniegavētra ceļā | nē | ārpus tvēruma (nav atbilstošas VUGD / AM lapas); teksts izlasīts, acīmredzamu kļūdu nav | — |
| `apsaldejums` | Apsaldējums | nē | ārpus tvēruma (nav atbilstošas VUGD / AM lapas); teksts izlasīts, acīmredzamu kļūdu nav | — |
| `hipotermija` | Hipotermija (pārsalšana) | nē | atbilst oficiālajai lapai (avots pievienots) | https://www.vugd.gov.lv/lv/drosiba-uz-udens |
| `karstums` | Karstuma dūriens | nē | ārpus tvēruma (nav atbilstošas VUGD / AM lapas); teksts izlasīts, acīmredzamu kļūdu nav | — |
| `negaiss` | Pērkona negaiss atklātā vietā | **jā** | VUGD secība: ēka/auto; telpās atvienot ierīces, nē dušai, tālāk no logiem; uz ūdens — krastā; klajumā grāvis; ne zem nojumēm | https://www.vugd.gov.lv/lv/stiprs-vejs-negaiss |
| `ledus_celi` | Apledojuši ceļi | nē | ārpus tvēruma (nav atbilstošas VUGD / AM lapas); teksts izlasīts, acīmredzamu kļūdu nav | — |
| `pludi` | Plūdi | **jā** | VUGD secība: negaidīt paziņojumu; evakuācija ar somu un mājdzīvniekiem, atslēgt elektrību, gāzi un apkuri, logi/durvis ciet, pulcēšanās vieta; ja nevar — augšējais stāvs/bēniņi + 112 | https://www.vugd.gov.lv/lv/pludi |
| `vetra_jumts` | Vētra norāvusi jumtu vai koku | nē | ārpus tvēruma (nav atbilstošas VUGD / AM lapas); teksts izlasīts, acīmredzamu kļūdu nav | — |
| `aukstuma_vilnis` | Aukstums, mājā nav siltuma | **jā** | VUGD apkures lapa: aizklāt logus, ēst sātīgi, nelietot alkoholu (nesasilda) | https://www.vugd.gov.lv/lv/apkure |
| `ledainas_ietves` | Paklupis uz ledus | nē | ārpus tvēruma (nav atbilstošas VUGD / AM lapas); teksts izlasīts, acīmredzamu kļūdu nav | — |
| `sniegs_no_jumta` | Sniegs vai lāstekas krīt no jumta | nē | ārpus tvēruma (nav atbilstošas VUGD / AM lapas); teksts izlasīts, acīmredzamu kļūdu nav | — |
| `viesulvetra` | Viesuļvētra | nē | ārpus tvēruma (nav atbilstošas VUGD / AM lapas); teksts izlasīts, acīmredzamu kļūdu nav | — |
| `sirdslekme` | Sirdslēkme | nē | ārpus tvēruma (nav atbilstošas VUGD / AM lapas); teksts izlasīts, acīmredzamu kļūdu nav | — |
| `insults` | Insults | nē | ārpus tvēruma (nav atbilstošas VUGD / AM lapas); teksts izlasīts, acīmredzamu kļūdu nav | — |
| `anafilakse` | Smaga alerģiska reakcija | nē | ārpus tvēruma (nav atbilstošas VUGD / AM lapas); teksts izlasīts, acīmredzamu kļūdu nav | — |
| `luzums` | Lūzums | nē | ārpus tvēruma (nav atbilstošas VUGD / AM lapas); teksts izlasīts, acīmredzamu kļūdu nav | — |
| `satricinajums` | Smadzeņu satricinājums | nē | ārpus tvēruma (nav atbilstošas VUGD / AM lapas); teksts izlasīts, acīmredzamu kļūdu nav | — |
| `saindesanas_partika` | Saindēšanās ar pārtiku | nē | ārpus tvēruma (nav atbilstošas VUGD / AM lapas); teksts izlasīts, acīmredzamu kļūdu nav | — |
| `tvana_gaze` | Tvana gāze (oglekļa monoksīds) | nē | ārpus tvēruma (nav atbilstošas VUGD / AM lapas); teksts izlasīts, acīmredzamu kļūdu nav | — |
| `astma` | Astmas lēkme | nē | ārpus tvēruma (nav atbilstošas VUGD / AM lapas); teksts izlasīts, acīmredzamu kļūdu nav | — |
| `diabets` | Zems cukura līmenis (diabēts) | nē | ārpus tvēruma (nav atbilstošas VUGD / AM lapas); teksts izlasīts, acīmredzamu kļūdu nav | — |
| `krampji` | Krampju lēkme | nē | ārpus tvēruma (nav atbilstošas VUGD / AM lapas); teksts izlasīts, acīmredzamu kļūdu nav | — |
| `asinosana` | Stipra asiņošana | nē | ārpus tvēruma (nav atbilstošas VUGD / AM lapas); teksts izlasīts, acīmredzamu kļūdu nav | — |
| `aizrijies` | Aizrijies | nē | ārpus tvēruma (nav atbilstošas VUGD / AM lapas); teksts izlasīts, acīmredzamu kļūdu nav | — |
| `kars` | Karš: rīcība pēc civilās aizsardzības plāna | **jā** | AM: saglabāt mieru, pildīt NBS un dienestu rīkojumus; ziņas par padošanos = viltus ziņas; LTV1 / LR / lsm.lv | https://www.sargs.lv/lv/buklets-ka-rikoties-krizes-gadijuma |
| `gaisa_trauksme` | Gaisa trauksme | **jā** | VUGD: oranžā līmeņa ziņa → rīkoties uzreiz; divu sienu princips, tālāk no stikla un lifta; ārā aizsegs; auto nav patvērums; palikt līdz atcelšanai | https://www.vugd.gov.lv/lv/kur-patverties-gaisa-apdraudejuma-laika |
| `militarpersonas` | Nezināmi bruņoti cilvēki vai militārpersonas | nē | ārpus tvēruma (nav atbilstošas VUGD / AM lapas); teksts izlasīts, acīmredzamu kļūdu nav | — |
| `savieni` | Šāvieni tuvumā | nē | ārpus tvēruma (nav atbilstošas VUGD / AM lapas); teksts izlasīts, acīmredzamu kļūdu nav | — |
| `droni` | Droni virs apdzīvotas vietas | **jā** | VUGD: bez aizsega nogulties un sargāt galvu; nokritušu dronu nepārvietot, brīdināt citus; nepublicēt vietu un foto | https://www.vugd.gov.lv/lv/kur-patverties-gaisa-apdraudejuma-laika |
| `evakuacija` | Evakuācijas rīkojums | **jā** | AM secība: noklausīties paziņojumu un pierakstīt galamērķi; soma + ID; ierīces izslēgt, logi, durvis; dienestu maršruts; bez auto uz pulcēšanās vietu; paziņot tuviniekiem | https://www.sargs.lv/lv/buklets-ka-rikoties-krizes-gadijuma |
| `robeza_slegta` | Robeža slēgta | nē | ārpus tvēruma (nav atbilstošas VUGD / AM lapas); teksts izlasīts, acīmredzamu kļūdu nav | — |
| `nav_sakaru_gimene` | Nav ziņu no tuviniekiem | nē | ārpus tvēruma (nav atbilstošas VUGD / AM lapas); teksts izlasīts, acīmredzamu kļūdu nav | — |
| `begli` | Bēgļi: reģistrācija un palīdzība | nē | ārpus tvēruma (nav atbilstošas VUGD / AM lapas); teksts izlasīts, acīmredzamu kļūdu nav | — |
| `piesarnojums` | Radiācija vai ķīmisks piesārņojums | **jā** | AM: mitrs audums uz mutes ārā, prom šķērsām vējam; apģērbu noņemt, mazgāties ar ziepēm; radiācijas gadījumā iekšā ≥ 24 h, tikai iepakota pārtika | https://www.sargs.lv/lv/buklets-ka-rikoties-krizes-gadijuma |
| `nemieri` | Nekārtības ielās | nē | ārpus tvēruma (nav atbilstošas VUGD / AM lapas); teksts izlasīts, acīmredzamu kļūdu nav | — |
| `aizdomiga_uzvediba` | Aizdomīga uzvedība apkārtnē | nē | ārpus tvēruma (nav atbilstošas VUGD / AM lapas); teksts izlasīts, acīmredzamu kļūdu nav | — |
| `kautins` | Kautiņš pasākumā | nē | ārpus tvēruma (nav atbilstošas VUGD / AM lapas); teksts izlasīts, acīmredzamu kļūdu nav | — |
| `terorisms` | Teroristisks uzbrukums | nē | ārpus tvēruma (nav atbilstošas VUGD / AM lapas); teksts izlasīts, acīmredzamu kļūdu nav | — |
| `asaru_gaze` | Asaru vai kairinoša gāze | nē | ārpus tvēruma (nav atbilstošas VUGD / AM lapas); teksts izlasīts, acīmredzamu kļūdu nav | — |
| `iebruceji` | Iebrucēji mājā | nē | ārpus tvēruma (nav atbilstošas VUGD / AM lapas); teksts izlasīts, acīmredzamu kļūdu nav | — |
| `laupisana` | Laupīšana uz ielas | nē | ārpus tvēruma (nav atbilstošas VUGD / AM lapas); teksts izlasīts, acīmredzamu kļūdu nav | — |
| `panika_tc` | Panika tirdzniecības centrā | nē | ārpus tvēruma (nav atbilstošas VUGD / AM lapas); teksts izlasīts, acīmredzamu kļūdu nav | — |
| `draudi_skola` | Draudi skolā | nē | ārpus tvēruma (nav atbilstošas VUGD / AM lapas); teksts izlasīts, acīmredzamu kļūdu nav | — |
| `telefona_baterija` | Izlādējas telefons | nē | ārpus tvēruma (nav atbilstošas VUGD / AM lapas); teksts izlasīts, acīmredzamu kļūdu nav | — |
| `nav_elektribas` | Ilgstoši nav elektrības | **jā** | VUGD secība: pārbaudīt vai tikai savā mājā → Sadales tīkls 80 200 404; atvienot ierīces; 112 tikai ja apdraudēta dzīvība; sveces uzmanīgi (nevis aizliegtas) | https://www.vugd.gov.lv/lv/elektribas-padeve |
| `nav_udens` | Nav ūdens | nē | ārpus tvēruma (nav atbilstošas VUGD / AM lapas); teksts izlasīts, acīmredzamu kļūdu nav | — |
| `nav_siltuma` | Ziemā nav apkures | nē | atbilst oficiālajai lapai (avots pievienots) | https://www.vugd.gov.lv/lv/apkure |
| `lifts` | Iesprūdis liftā | nē | ārpus tvēruma (nav atbilstošas VUGD / AM lapas); teksts izlasīts, acīmredzamu kļūdu nav | — |
| `gazes_nopludes_eka` | Gāzes noplūde ēkā | **jā** | „Neslēdziet elektrību” → „neko neieslēdziet un neizslēdziet” (Gaso) | https://www.lsm.lv/raksts/dzive-stils/ikdienai/16.01.2026-kapec-gazes-nopludes-laika-nedrikst-zvanit-durvju-zvanu-ikdieniski-jautajumi-par-gazi.a630312/ |
| `kimiska_avarija` | Ķīmiska avārija rūpnīcā | **jā** | VUGD: telpā ar mazāk logu; ārā aizsegt muti, prom šķērsām vējam ≥ 800 m, neiet cauri dūmiem; atgriezties tikai ar atļauju | https://www.vugd.gov.lv/lv/bistamu-kimisko-vielu-noplude-vai-radiacijas-avarija |
| `vilciena_avarija` | Vilciena avārija | nē | ārpus tvēruma (nav atbilstošas VUGD / AM lapas); teksts izlasīts, acīmredzamu kļūdu nav | — |
| `tunelis` | Ugunsgrēks tunelī | nē | ārpus tvēruma (nav atbilstošas VUGD / AM lapas); teksts izlasīts, acīmredzamu kļūdu nav | — |
| `lidmasina` | Lidmašīnas avārijas nosēšanās | nē | ārpus tvēruma (nav atbilstošas VUGD / AM lapas); teksts izlasīts, acīmredzamu kļūdu nav | — |
| `kugis` | Prāmja vai kuģa avārija | nē | ārpus tvēruma (nav atbilstošas VUGD / AM lapas); teksts izlasīts, acīmredzamu kļūdu nav | — |
| `nav_sakaru` | Mobilo sakaru tīkls nedarbojas | nē | ārpus tvēruma (nav atbilstošas VUGD / AM lapas); teksts izlasīts, acīmredzamu kļūdu nav | — |
| `ielauzies_ledu` | Cilvēks iekritis ledainā ūdenī | **jā** | VUGD: līdz ielūzumam neiet, mest virvi no 2–5 m, izvilkt rāpus; slapjās drēbes nost, sildīt pakāpeniski, silts salds dzēriens bez alkohola | https://www.vugd.gov.lv/lv/drosiba-uz-udens |
| `ledus_lust` | Ledus lūst zem kājām | **jā** | VUGD: ielūstot — sauc palīgā un 112, nomierināt elpošanu, ledus irbuļi, rāpus līdz krastam; pēc tam pie ārsta | https://www.vugd.gov.lv/lv/drosiba-uz-udens |
| `straume` | Straume aiznes peldētāju | **jā** | VUGD: saglabāt mieru, galva virs ūdens; uz krastu, kad straume vājāka | https://www.vugd.gov.lv/lv/drosiba-uz-udens |
| `slikst` | Cilvēks slīkst | **jā** | VUGD: 112 ar precīzu vietu un piebraukšanu; sagaidīt glābējus un parādīt vietu | https://www.vugd.gov.lv/lv/drosiba-uz-udens |
| `laiva` | Apgāzusies laiva | nē | ārpus tvēruma (nav atbilstošas VUGD / AM lapas); teksts izlasīts, acīmredzamu kļūdu nav | — |
| `udens_celas` | Ūdens ceļas pagrabā vai telpā | nē | atbilst oficiālajai lapai (avots pievienots) | https://www.vugd.gov.lv/lv/pludi |
| `kartes_nedarbojas` | Kartes un maksājumi nedarbojas | nē | ārpus tvēruma (nav atbilstošas VUGD / AM lapas); teksts izlasīts, acīmredzamu kļūdu nav | — |
| `viltus_zinas` | Viltus ziņas un dezinformācija | nē | ārpus tvēruma (nav atbilstošas VUGD / AM lapas); teksts izlasīts, acīmredzamu kļūdu nav | — |
| `viltota_trauksme` | Aizdomīgs trauksmes ziņojums | nē | ārpus tvēruma (nav atbilstošas VUGD / AM lapas); teksts izlasīts, acīmredzamu kļūdu nav | — |
| `datu_noplude` | Nozagti dati vai identitāte | nē | ārpus tvēruma (nav atbilstošas VUGD / AM lapas); teksts izlasīts, acīmredzamu kļūdu nav | — |
| `e_pakalpojumi` | Valsts e-pakalpojumi nedarbojas | nē | ārpus tvēruma (nav atbilstošas VUGD / AM lapas); teksts izlasīts, acīmredzamu kļūdu nav | — |
| `partika_beigusies` | Veikalos nav pārtikas | nē | ārpus tvēruma (nav atbilstošas VUGD / AM lapas); teksts izlasīts, acīmredzamu kļūdu nav | — |
| `degvielas_trukums` | Degvielas trūkums | nē | ārpus tvēruma (nav atbilstošas VUGD / AM lapas); teksts izlasīts, acīmredzamu kļūdu nav | — |
| `aptiekas_tuksas` | Aptiekās nav zāļu | nē | ārpus tvēruma (nav atbilstošas VUGD / AM lapas); teksts izlasīts, acīmredzamu kļūdu nav | — |
| `suni` | Uzbrūk suņi | nē | ārpus tvēruma (nav atbilstošas VUGD / AM lapas); teksts izlasīts, acīmredzamu kļūdu nav | — |
| `savvalas_dzivnieki` | Mežacūka, lācis vai alnis tuvumā | nē | ārpus tvēruma (nav atbilstošas VUGD / AM lapas); teksts izlasīts, acīmredzamu kļūdu nav | — |
| `cuska` | Čūskas kodums | nē | ārpus tvēruma (nav atbilstošas VUGD / AM lapas); teksts izlasīts, acīmredzamu kļūdu nav | — |
| `liellopi` | Izbēguši liellopi | nē | ārpus tvēruma (nav atbilstošas VUGD / AM lapas); teksts izlasīts, acīmredzamu kļūdu nav | — |
| `iesprudis_saurums` | Cilvēks iesprūdis (grava, aka, šahta) | nē | ārpus tvēruma (nav atbilstošas VUGD / AM lapas); teksts izlasīts, acīmredzamu kļūdu nav | — |
| `troksnis_kaimins` | Kaimiņš trokšņo | nē | ārpus tvēruma (nav atbilstošas VUGD / AM lapas); teksts izlasīts, acīmredzamu kļūdu nav | — |
| `huligani` | Huligāni uz ielas | nē | ārpus tvēruma (nav atbilstošas VUGD / AM lapas); teksts izlasīts, acīmredzamu kļūdu nav | — |
| `aizsalusas_caurules` | Aizsalušas caurules | nē | ārpus tvēruma (nav atbilstošas VUGD / AM lapas); teksts izlasīts, acīmredzamu kļūdu nav | — |
| `kanalizacija` | Kanalizācija nestrādā | nē | ārpus tvēruma (nav atbilstošas VUGD / AM lapas); teksts izlasīts, acīmredzamu kļūdu nav | — |
| `lifts_nedarbojas` | Lifts nedarbojas | nē | ārpus tvēruma (nav atbilstošas VUGD / AM lapas); teksts izlasīts, acīmredzamu kļūdu nav | — |
| `izsists_logs` | Izsists logs | nē | ārpus tvēruma (nav atbilstošas VUGD / AM lapas); teksts izlasīts, acīmredzamu kļūdu nav | — |
| `auto_sabojajies` | Auto sabojājies ceļa malā | nē | ārpus tvēruma (nav atbilstošas VUGD / AM lapas); teksts izlasīts, acīmredzamu kļūdu nav | — |
| `trauma_var_kusteties` | Trauma: var kustēties | nē | ārpus tvēruma (nav atbilstošas VUGD / AM lapas); teksts izlasīts, acīmredzamu kļūdu nav | — |
| `trauma_nevar_kusteties` | Trauma: nevar kustēties | nē | ārpus tvēruma (nav atbilstošas VUGD / AM lapas); teksts izlasīts, acīmredzamu kļūdu nav | — |
