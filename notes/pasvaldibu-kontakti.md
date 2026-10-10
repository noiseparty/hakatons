# Pašvaldību kontakti rezultāta kartītē

Statuss 2026-10-10. Ielāde: `src/karte/db/pasvaldibas.py` -> `src/karte/dati/pasvaldibas.json` -> `/api/pasvaldiba` -> `production/meklesana.js` (`pasvaldibaDati`).

## Avoti

| Avots | Ko dod | Licence | Datums | Aptvērums |
|---|---|---|---|---|
| Uzņēmumu reģistrs, "Publisko personu un iestāžu saraksts" (data.gov.lv `public-persons-institutions`, atjauno katru dienu) | pašvaldības e-pasts, tālrunis, adrese, tīmekļvietne | CC0 1.0 | katru dienu (ielāde 2026-10-10) | **42/42** (arī 7 valstspilsētas un Ventspils novads); visiem ir tālrunis, e-pasts, adrese |
| VPVKAC kontakti (data.gov.lv `vpvkac-kontakti`, resurss "VPVKAC KONTAKTI 2023-11", CSV) | klientu apkalpošanas centra adrese un tālrunis | CC0 1.0 | 2023-11-08 (jaunākā versija; iepriekšējā 2022-08) | **18/42**: tikai tad, ja novada centra pilsētai ir savs VPVKAC |

## Lēmums

Variants (a): UR saraksts jau sedz visas 42 pašvaldības ar tālruni, e-pastu un adresi, tāpēc 2022. gada VPVKAC saraksts vairs nav kartītes pamatavots.

- Tas aizstāts ar jaunāko CKAN versiju (2023-11). Datu kopā `vpvkac-kontakti` jaunākas versijas nav (metadati mainīti 2023-12-11).
- VPVKAC nu rāda kā atsevišķu rindu "Klientu apkalpošanas centrs: adrese, tālrunis" un tikai tad, ja centrs ir novada centra pilsētā. Iepriekš izvēlējās jebkuru novada centru, kas varēja būt cita pilsēta nekā iedzīvotāja (piem. Ogrei būtu parādīta Ikšķile).
- Rīgai, Daugavpilij, Jūrmalai, Liepājai, Rēzeknei, Ventspilij un Ventspils novadam sarakstā centru nav (arī 2023-11 versijā nav valstspilsētu un Ventspils novada); kartīte rāda tikai UR kontaktus.
- 2023-11 CSV ir ~14 MB (tukšas rindas līdz Excel 1 048 576. rindai); ielāde ir viens GET, parsēšana ~2 s.
- Datu kopā `valsts-iestazu-pakalpojumi-vpvkac-klientu-apkalposanas-centros` (CC0, 2026-06) ir pakalpojumu saraksts, nevis kontakti.

## Ko rāda kartīte

1. Pašvaldības nosaukums, CA plāns, tīmekļvietne, tālrunis un e-pasts (UR) kā teksts, bez `tel:` saitēm.
2. Pašvaldības adrese (UR).
3. Klientu apkalpošanas centrs (VPVKAC), ja ir.
4. Avotu rinda: CA plāni, "Uzņēmumu reģistrs, publisko personu saraksts · CC0", "VPVKAC kontakti, 2023-11 · CC0" (tikai kad VPVKAC rinda ir redzama).

## Atjaunošana

`uv run --no-project src/karte/db/pasvaldibas.py` (nevajag openpyxl), tad `pasvaldibas.json` iekļauj commit. Shēma un VPS ielādes nav jāmaina.
