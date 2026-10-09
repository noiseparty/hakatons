# Karte: datubāze un API (map.repo.lv)

```
pārlūks (production/index.html + app.js)
   │  GET /api/...
   ▼
Caddy (map.repo.lv) ──/api/*──► karte_api.py :8920 (hakatons-map-api.service, lietotājs deploy)
                                     │  lietotājs map_api (tikai lasīšana)
                                     ▼
                           PostgreSQL 16 + PostGIS, datubāze `map` (VPS, tikai localhost)
                                     ▲  lietotājs map (īpašnieks)
                           db/regioni.sh, db/ielade.py (palaiž uz VPS)
```

| Mape | Saturs |
|---|---|
| `db/shema.sql` | Tabulas `regioni`, `kategorijas`, `avoti`, `objekti` + trigeris, kas punktam pieraksta pašvaldību un pilsētu. Slāņi un **datu avoti ar licencēm** definēti šeit. |
| `db/regioni.sh` | 35 novadi, 7 valstspilsētas, 75 pilsētas no VZD adrešu reģistra (`aw_shp.zip`). |
| `db/ielade.py` | Ielādē GeoJSON vai CSV (lat/lon) kā vienu **avotu**; atkārtota ielāde aizvieto šī avota saturu. |
| `db/valsts_dati.py` | Valsts atvērtie dati no data.gov.lv (CC0): ārstniecības iestādes, VP iecirkņi, pašvaldību policija, VUGD depo (IeM IC), aptiekas (ZVA) → `dati/*.csv`. |
| `db/osm_poi.py` | Tikai bankomāti un DUS no OpenStreetMap (ODbL; valsts datu nav) → `dati/osm_poi.geojson`. |
| `db/ielade_visu.sh` | Ielādē visus avotus no jauna (shēma + visi `ielade.py` izsaukumi). |
| `dati/` | Ielādējamie faili (avota momentuzņēmumi). Nav publiski. |
| `db/slimnicas_24h.py` | 37 slimnīcas ar 24/7 neatliekamo palīdzību (VM 04.03.2026. rīkojums, Valsts katastrofu medicīnas plāna 12. pielikums) → `dati/slimnicas_24h.geojson`. Koordinātas no VZD adrešu reģistra (`aw_eka.csv`), PSKUS un RAKUS — uzņemšanas ieeja no OSM. Adreses pārbaudītas; `atseviski_dati/hospitals.csv` koordinātas bija aptuvenas (līdz 118 km nobīde), tāpēc netiek lietotas. |
| `api/karte_api.py` | API (Python standarta bibliotēka + psycopg). Galapunkti aprakstīti faila sākumā. |
| `serveris/` | Caddy un systemd failu kopijas, kas uzstādītas VPS. |

Paroles: `/etc/hakatons/map.env` uz VPS (`MAP_DB_OWNER_DSN`, `MAP_DB_DSN`), nekad repozitorijā.

## Datu avotu noteikumi

Kartē drīkst izmantot **tikai atvērtos datus**: avots ar atvērtu licenci (CC0, CC BY, ODbL) vai oficiāls
dokuments, kas nav autortiesību objekts (Autortiesību likuma 6. pants), iegūts caur oficiālu lejupielādi vai API,
kura noteikumi to atļauj. Katrs avots ir tabulā `avoti` (licence, izdevējs, datu kopas saite, ieguves URL),
`objekti.avots` uz to atsaucas obligāti (FK), un karte to rāda sadaļā "Datu avoti" un katra punkta logā.

Izņēmums ar komandas lēmumu (2026-10-09): **patvertnes no 112.lv** (licence nav norādīta) paliek kartē,
atzīmētas ar ⚠ (`avoti.atverts = false`). Fona karte: OpenStreetMap flīzes (ODbL, flīžu lietošanas noteikumi).

## Jaunas datu kopas pievienošana

0. Pārbaudi licenci un ieguves noteikumus; pievieno rindu tabulā `avoti` (`db/shema.sql`). Bez tās ielāde atsakās.
1. Pārveido datus uz GeoJSON (punkti, WGS-84) vai CSV ar `lat`/`lon` kolonnām un ieliec `dati/`.
   Ja ir tikai adreses, tās jāģeokodē (VZD adrešu reģistrs, `aw_eka.csv`, satur koordinātas).
2. Ja vajag jaunu slāni, pievieno rindu `kategorijas` blokā `db/shema.sql` (grupa: `patvertnes`,
   `infrastruktura`, `incidenti` vai jauna; karte to parādīs automātiski).
3. Saglabā (PR → main), tad uz VPS:

```bash
ssh vps
cd /srv/hakatons && set -a && . /etc/hakatons/map.env && set +a
psql "$MAP_DB_OWNER_DSN" -f src/karte/db/shema.sql            # ja mainījās kategorijas
python3 src/karte/db/ielade.py src/karte/dati/<fails> --avots <avots> --kategorija <kods> \
    --id "{<id lauks>}" --nosaukums "{<lauks>}" --adrese "{iela} {nr}, {pilseta}"
```

Incidentiem pievieno `--derigs-lidz "{<beigu laiks>}"`; pēc tā laika API tos vairs nerāda.

Visu esošo avotu atjaunošana:

```bash
python src/karte/db/valsts_dati.py      # data.gov.lv CSV → dati/ (lokāli; tad PR)
python src/karte/db/osm_poi.py          # OSM bankomāti, DUS → dati/ (lokāli; tad PR)
bash src/karte/db/ielade_visu.sh        # VPS: shēma + visi avoti datubāzē
bash src/karte/db/regioni.sh            # VPS: robežas (reizi mēnesī pietiek)
```

`ielade.py` papildus: `--srid 3059` (LKS-92 TM koordinātas), `--kodejums cp1257`, `--atdalitajs ";"`.
`--apvienot 35` izmet viena avota dublikātus ≤ 35 m (tā pati kategorija, saderīgs nosaukums/adrese/operator/brand, garumzīmes neņem vērā); izmesto ID paliek īpašībā `dublikati`. Lieto patvertnēm un OSM.

## API izmaiņas

`karte_api.py` izmaiņas nonāk produkcijā pašas: pēc PR sapludināšanas sinhronizācija atjauno failu,
un `hakatons-map-api-restart.path` pārstartē servisu. Žurnāls: `journalctl -u hakatons-map-api`.
