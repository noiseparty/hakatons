# Krīzes meklēšanas klasifikators: atslēgvārdu paplašināšana un pārbaude (2026-10-10)

**Kā ģenerēts.** Produktā AI nav: `production/klasifikators.js` salīdzina vaicājumu ar vārdu sākumiem
`production/scenariji.json`. Atslēgvārdus papildinājām bezsaistē ar pieciem Claude Opus apakšaģentiem, katrs 25
scenārijiem. Katrs aģents redzēja visus 125 scenārijus ar esošajiem atslēgvārdiem un padomiem un zināja
saskaitīšanas noteikumus (vārda sākums, garumzīmes tiek noņemtas, frāze sver vairāk, kopīgs vārds sver mazāk:
svars / √scenāriju skaits). Uzdevums: ~10 jauni, šim scenārijam raksturīgi vārdi katram. Tie ir LV sarunvalodā
un citos locījumos, ar tipiskām drukas kļūdām, ko prefikss nenoķer, RU un EN; vispārīgi vārdi netika pieņemti.
`src/meklesana/papildinat.py` no 1 844 priekšlikumiem izmeta 65 (dublikāti pēc normalizēšanas, jau esoša prefiksa
sedzti, par īsu, vispārīgi) un 1 779 pielika failam, nepārrakstot roku formatējumu. Tad sekoja kļūdu analīze.
Divi labojumi klasifikatorā: katrs vaicājuma vārds dod punktus tikai vienreiz ("car on fire" neskaita vēlreiz
"on fire" un "fire"), un vienādiem punktiem uzvar garāks atrastais vārda sākums ("бомбоубежищ" pirms "бомб").
Pēc tam ar roku ap 60 atslēgvārdu labojumiem. Izņēmām vispārīgas frāzes, kas pārspēja raksturīgus vārdus
("nevaru atrast", "neko neredz", "kur iet", "tirdzniecības centr", aģentu pievienotos "iekod", "nozaga som").
Kopīgus simptomus ("grūti elpot", "nezinu kur atrodos") ielikām vairākos scenārijos, lai tie sver mazāk.
Pielikām trūkstošos raksturīgos vārdus ("no motora", "ураганный ветер", "in the tunnel", "netek", "cant move").

**Kā pārbaudīts.** `src/meklesana/vaicajumi.json` ir 497 reālistiski vaicājumi (500 ģenerēti, 3 dublikāti
izmesti). Tos rakstīja citi pieci Opus aģenti, kuri atslēgvārdus **neredzēja**, tikai scenārija nosaukumu un
padomu. Sadalījums: 200 parasti LV, 100 RU/EN, 97 ar drukas kļūdām vai bez garumzīmēm, 50 ar adresi vai vietu,
50 divdomīgi. Katram vaicājumam ir `pienemami`: visi scenāriji, kas būtu pareiza pirmā atbilde. `testi.py` tagad
pēc vecajiem 125 testiem un 119 nosaukumiem rāda:
- precizitāti pirmajā vietā pa tipiem;
- cik divdomīgajiem "Vai domājāt" piedāvā vēl kādu pieņemamo un cik skaidrajiem to rāda lieki;
- 20 sliktākos scenārijus pēc F1 (`-v` izdrukā visus kļūdainos).

Zem 90 % tests krīt. Lai skaitlis nebūtu "pielāgots testam", kopa ir sadalīta pēc vaicājuma crc32. 70 % ("dev")
izmantojām labošanai, 30 % ("paturēti", 152) netika skatīti, un tos uzrādām atsevišķi.

**Skaitļi** (pirmā vieta pareiza; vecie 125 testi visu laiku 125/125, beigās arī 119/119 nosaukumi):

| Stāvoklis | Kopā (497) | dev (345) | paturēti (152) |
|---|---:|---:|---:|
| `main` pirms darba | 77,3 % | 75,1 % | 82,2 % |
| + 1 779 ģenerēti atslēgvārdi | 81,3 % | 80,6 % | 83,6 % |
| + vārds skaitās vienreiz, garākais prefikss uzvar | 84,1 % | 83,5 % | 85,5 % |
| + ~60 atslēgvārdu labojumi pēc dev kļūdām | **93,8 %** | 95,7 % | **89,5 %** |

Pa tipiem beigās: LV 94 %, RU/EN 94 %, kļūdas/bez garumzīmēm 93 %, ar vietu 94 %, divdomīgie 96 % (pirms tam
74 / 71 / 85 / 80 / 86 %). "Vai domājāt" slieksni (`vai_domajat_slieksnis` failā `scenariji.json`) nolaidām no
"vairāk par pusi" uz 0,45. Daudzi otrie scenāriji iegūst tieši pusi punktu, tāpēc divdomīgajiem pareizā
alternatīva tagad redzama 26/50 gadījumos (bija 14/50). Cena: skaidrajiem lieka poga 143/447 (bija 90/447).
Krīzē trūkstoša izeja maksā vairāk nekā lieka poga; rādām labāko + līdz 2 alternatīvām. Atlikušās kļūdas lielākoties
ir patiešām tuvi scenāriji (sniegavētra / auto putenī / apmaldījies sniegā, gāzes smaka / gāzes noplūde ēkā).
Faila izmērs: 78 → 113 KB (gzip 23 → 36 KB).

## 2. kārta (2026-10-10 nakts): ātrums, demo notikumi, jauni RU/EN vaicājumi

**Ātrums.** Pārbaudījām ar Playwright 375×740 un 4× palēninātu CPU; laiku mērījām katram taustiņa nospiedumam
(80 ms aizturētais ieteikumu izsaukums). Pirms labojuma: mediāna 10,1 ms, p90 26,5 ms, max 61 ms. Klasifikatora
uzbūve aizņem 27 ms, `klasificet` 1–2 ms; 392 ms ilgais uzdevums ielādē ir karte, ne meklēšana. Lēni bija
neatpazīti vārdi ("elek", "e-paraksts …"), jo tad strādā aptuvenā meklēšana un labošana. Abas salīdzināja vārdu
ar katru atslēgvārdu pilnā Levenšteina matricā, un katrā taustiņā no jauna normalizēja ~3 200 atslēgvārdus.
Labojumi nemaina rezultātu:
- normalizētie atslēgvārdi sagatavoti vienreiz;
- labotie vārdi kešoti (tīra funkcija);
- pirms matricas ātra pārbaude: ar vienu labojumu kāds no pāriem a₀=b₀, a₁=b₁, a₁=b₀, a₀=b₁ sakrīt;
- matricu pārtrauc, tiklīdz rindas minimums > 1.

Pēc tam: mediāna 3,4 ms, p90 9,7 ms, max 28 ms (< 30 ms), tāpēc statisks JSON indekss nav vajadzīgs.

**Demo notikumi un jauni scenāriji.** Astoņi reālie notikumi no demo paneļa:
- BRELL atslēgšanās → `nav_elektribas` ("brell", "энергосистем", "свет пропал");
- droni ar šūnu apraidi → `droni`. "šūnu apraide" vairs nav pie `viltota_trauksme`: tas ir oficiālais kanāls;
  aizdomīgu ziņu atpazīst pēc "vai … ir īsta";
- ledus sastrēgums → `pludi`;
- Stiklu purva kūdras ugunsgrēks → `meza_ugunsgreks` ("purvs deg", "болот", "peat");
- gāzes sprādziens → `spradziens`.

Divu situāciju nebija, tāpēc pievienoti scenāriji (arī `notes/SCENARIJI.md`):
- **#120 "Dūmi no liela ugunsgrēka tuvumā"** (noliktava, osta, metāllūžņi): ejiet iekšā, aizveriet logus,
  izslēdziet ventilāciju, neejiet skatīties;
- **#121 "Valsts e-pakalpojumi nedarbojas"** (eParaksts, Latvija.gov.lv, EDS, DDoS): iestāžu un CERT.LV
  paziņojumi, kodus saitēs no SMS nevadiet, steidzami — pa tālruni vai klātienē.

Vispārīgos vārdus "dūmi nāk" un "smoke coming" pie #120 nelikām: tie pārņēma dūmus kāpņu telpā.

**Jauni vaicājumi un skaitļi.** Opus aģents bez piekļuves atslēgvārdiem uzrakstīja 66 jaunus vaicājumus:
50 RU/EN (16 par demo notikumiem) un 16 LV par demo notikumiem. **Pirms jebkādiem labojumiem tie bija 54/66
= 81,8 %.** Tas ir godīgākais vispārināšanas novērtējums; vājākie ir jauni RU/EN formulējumi. Pēc 11 vārdu
robu aizpildīšanas tie ir 65/66. Kopā tagad 563 vaicājumi, pareizi 95,0 %, un vecie 125/125 un 121/121 testi
zaļi. Sākotnējo 497 vaicājumu paturētie 30 % joprojām nav skatīti: 89,5 %. `testi.py` tagad rāda paturētos
atsevišķi (172, 90,7 %), un `-v` izdrukā tikai dev kļūdas. Ap 20 no tiem 172 ir no jaunajiem 66, kurus mēs
redzējām, tāpēc tīrais skaitlis ir 89,5 %.

**Kas paliek divdomīgs (apzināti nelabots).** Šiem atšķirību nosaka konteksts, nevis vārds, un papildu vārdi tikai
pielāgotos testam. Abas atbildes dod drošu padomu, un otrā parādās "Vai domājāt":
- sniegavētra / auto putenī / apmaldījies sniegā ("blizzard on the highway", "sniegavētra braucu");
- "nezinu kur esmu" bez vietas (mežs / pilsēta / lauki);
- gāzes smaka / gāzes noplūde ēkā ("kāpņu telpā smird pēc gāzes");
- "vējš plēš kokus, kur slēpties" (patvertne ir pieņemama atbilde);
- "bērnam krampji un augsta temperatūra" (medicīna);
- "vecmamma sabruka un neelpo" (sabruk = ēka). Šeit 112 rinda parādās jebkurā gadījumā.

## 3. kārta (2026-10-10 rīts): tuvie pāri un demo vaicājumi

Abus tuvos pārus tomēr salabojām: atšķirību var nolasīt no vārdiem. Gāzei izšķir vieta (kāpņu telpa, pagrabs,
visa māja pret virtuvi un plīti), sniegam — kustība (braucu, šoseja, трасса, driving pret kājām, пешком, on foot;
iestrēdzis pret riteņi buksē).
- **Gāze.** Smakas frāzes ("smird pēc gāz", "пахнет газ", "gas smell" …) tagad ir abiem scenārijiem. Tāpēc tās
  sver 1/√2 un uzvarētāju nenosaka. Ja punkti vienādi, uzvar "Gāzes smaka dzīvoklī" (tas failā ir pirmais), un
  otrs parādās "Vai domājāt". Noplūdei ēkā pievienotas vietas (kāpņu telp, pagrab, visā māj, daudzdzīvokļu,
  подъезд, подвал, stairwell, basement). Smakai dzīvoklī: virtuv, plīt, кухн, kitchen, stove.
- **Sniegs.** "Sniegavētra ceļā" ieguva braukšanas vārdus. "brauc"/"brauk" ir arī pie "Apledojuši ceļi", tāpēc
  tie sver mazāk. "Apmaldījies sniegā" ieguva iešanu kājām un kopīgos "nezinu kur esmu", "заблуд". No "Auto
  iestrēdzis putenī" izņemts "sniegavētr": "sniegavētra" bez "iestrēdzis" nozīmē braukšanu, nevis iestrēgšanu.
- Šos vārdus izmēģinājām un izmetām, jo tie ir pārāk vispārīgi un salauza citus vaicājumus: "uz ceļa", "ceļā",
  "на дороге", "on the road", "dzīvoklī", "apartment", "квартир", "building", "hallway", "kaimiņ", "kāpn".

`vaicajumi.json` papildinājām ar 46 vaicājumiem:
- 14 unikālie demo paneļa vaicājumi (scenāriju ir 16, bet "drons Rēzekne" atkārtojas trīs reizes);
- 32 jauni vaicājumi par abiem pāriem (LV, RU/EN, bez garumzīmēm, ar vietu).

Jaunos rakstījām paši, redzot atslēgvārdus, tāpēc tie nav neatkarīgs novērtējums. Pirms labojumiem pareizi bija
36 no 46.

| Stāvoklis | Kopā (609) | paturēti (186) | sākotnējie 563 | to paturētie (172) |
|---|---:|---:|---:|---:|
| `main` + jaunie vaicājumi | 571 (93,8 %) | 168 (90,3 %) | 535 (95,0 %) | 156 (90,7 %) |
| + atslēgvārdi | **585 (96,1 %)** | **170 (91,4 %)** | 539 (95,7 %) | 156 (90,7 %) |

Salaboti 14 vaicājumi, salauzts neviens. Vecie testi joprojām zaļi: 125/125 un 121/121. Lieka "Vai domājāt" poga
skaidrajiem vaicājumiem parādās biežāk: 182 → 189 no 548.
