# atseviski_dati — komandas sagatavotie / simulētie dati

Mapes mērķis: atsevišķi punktu dati krīzes kartei (map.repo.lv), kas nav hakatona
datu komplektā (`ai-open-data-2026-hakatons/` ir tikai lasāms).

## Faili

| Fails | Saturs | Kategorija kartē (`kategorijas` kods) |
|---|---|---|
| `udens.csv` | 100 publiskas brīvpieejas ūdens ņemšanas vietas | `udens_punkts` |
| `energija.csv` | 100 publiskie brīvpieejas mobilo ierīču uzlādes punkti | `uzlades_stacija` |

## SVARĪGI — dati ir SIMULĒTI

Abas datu kopas ir izdomāti (ģenerēti) prototipa izstrādei: adreses, nosaukumi,
darba laiki un atrašanas vietas (pilsētu centru tuvumā ar izkliedi) nav reāli.
Pirms publiskas rādīšanas produkcijā tās jāaizstāj ar reāliem atvērtajiem datiem
(piem., OSM `amenity=drinking_water` / `amenity=charging_station`, pašvaldību dati).

## Formāts

CSV (UTF-8), WGS-84 koordinātas `lat`/`lon` kolonnās — atbilst `src/karte/db/ielade.py`
ielādētājam. Pārējās kolonnas kļūst par objekta īpašībām (`ipasibas`) un redzamas API.

- `udens.csv`: `id, nosaukums, adrese, vieta, veids, darba_laiks, lat, lon`
  (`veids`: publisks ūdens bruninis / piepildes krāns uz ūdensvada / dzeramā ūdens uzpildes vieta)
- `energija.csv`: `id, nosaukums, adrese, vieta, veids, darba_laiks, ligzdas, lat, lon`
  (`veids`: publiskais uzlādes punkts / ātrās uzlādes punkts; `ligzdas` — ligzdu skaits)

## Ielāde kartē (VPS)

Pirms ielādes `avoti` tabulā (`src/karte/db/shema.sql`) jāpievieno avots ar kodiem
`sim-udens` un `sim-energija` (izdevējs: komanda, licence: simulēti dati, nav publiski
izmantojami ārpus prototipa). Tad:

```bash
set -a; . /etc/hakatons/map.env; set +a
python3 src/karte/db/ielade.py atseviski_dati/udens.csv \
    --avots sim-udens --kategorija udens_punkts --id "{id}" \
    --nosaukums "{nosaukums}" --adrese "{adrese}"
python3 src/karte/db/ielade.py atseviski_dati/energija.csv \
    --avots sim-energija --kategorija uzlades_stacija --id "{id}" \
    --nosaukums "{nosaukums}" --adrese "{adrese}"
```
