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
| `db/shema.sql` | Tabulas `regioni`, `kategorijas`, `objekti` + trigeris, kas punktam pieraksta pašvaldību un pilsētu. Kategorijas (slāņi) definētas šeit. |
| `db/regioni.sh` | 35 novadi, 7 valstspilsētas, 75 pilsētas no VZD adrešu reģistra (`aw_shp.zip`). |
| `db/ielade.py` | Ielādē GeoJSON vai CSV (lat/lon) kā vienu **avotu**; atkārtota ielāde aizvieto šī avota saturu. |
| `db/osm_poi.py` | Bankomāti, aptiekas, slimnīcas, policija, ugunsdzēsēji, DUS no OpenStreetMap → `dati/osm_poi.geojson`. |
| `dati/` | Ielādējamie faili (avota momentuzņēmumi). Nav publiski. |
| `api/karte_api.py` | API (Python standarta bibliotēka + psycopg). Galapunkti aprakstīti faila sākumā. |
| `serveris/` | Caddy un systemd failu kopijas, kas uzstādītas VPS. |

Paroles: `/etc/hakatons/map.env` uz VPS (`MAP_DB_OWNER_DSN`, `MAP_DB_DSN`), nekad repozitorijā.

## Jaunas datu kopas pievienošana

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

Esošie avoti:

```bash
python3 src/karte/db/ielade.py src/karte/dati/patvertnes.geojson --avots vugd-112 --kategorija patvertne \
    --id "{_nr}" --nosaukums "{veids}" --adrese "{iela} {nr}, {vieta}"
python3 src/karte/db/ielade.py src/karte/dati/osm_poi.geojson --avots osm --nosaukums "{name}" --adrese "{adrese}"
bash src/karte/db/regioni.sh      # robežas (reizi mēnesī pietiek)
```

## API izmaiņas

`karte_api.py` izmaiņas nonāk produkcijā pašas: pēc PR sapludināšanas sinhronizācija atjauno failu,
un `hakatons-map-api-restart.path` pārstartē servisu. Žurnāls: `journalctl -u hakatons-map-api`.
