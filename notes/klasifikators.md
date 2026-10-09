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
