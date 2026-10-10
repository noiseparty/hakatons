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
| `db/adreses.sh` | ~550 000 spēkā esošas ēku adreses ar koordinātām no VZD adrešu reģistra (`aw_eka.csv`, CC BY 4.0) → tabula `adreses`, meklēšanai `/api/adreses`. |
| `db/ielade.py` | Ielādē GeoJSON vai CSV (lat/lon) kā vienu **avotu**; atkārtota ielāde aizvieto šī avota saturu. |
| `db/valsts_dati.py` | Valsts atvērtie dati no data.gov.lv (CC0): ārstniecības iestādes, VP iecirkņi, pašvaldību policija, VUGD depo (IeM IC), aptiekas (ZVA) → `dati/*.csv`. |
| `db/osm_poi.py` | OpenStreetMap (ODbL; valsts datu nav), katram slānim savs Overpass vaicājums un avots: bankomāti un DUS → `dati/osm_poi.geojson` (`osm`); dzeramā ūdens punkti → `osm_udens.geojson` (`osm-udens`, kategorija `udens_punkts` kopā ar simulētajiem); bezmaksas Wi-Fi → `osm_wifi.geojson` (`osm-wifi`); elektroauto uzlāde → `osm_ev.geojson` (`osm-ev`); veterinārās klīnikas → `osm_vet.geojson` (`osm-vet`). |
| `db/ielade_visu.sh` | Ielādē visus avotus no jauna (shēma + visi `ielade.py` izsaukumi). |
| `db/udens_limenis.py`, `.sh` | Ūdens līmenis 74 LVĢMC hidroloģiskajās stacijās (data.gov.lv, CC0), katru stundu: `hakatons-udens.timer` (:45) un `.path` (pēc izmaiņām main). Mērījums vecāks par 6 h netiek rādīts (`derigs_lidz`). |
| `dati/` | Ielādējamie faili (avota momentuzņēmumi). Nav publiski. |
| `db/ca_plani.py` | Pašvaldību CA plānu pulcēšanās vietas (`evakuacijas_punkts`) un pagaidu izmitināšanas vietas (`izmitinasana`) → `dati/ca_pulcesanas_vietas.geojson`, `dati/ca_izmitinasana.geojson`. Ievade: AI izvilkums `dati/ca_plani/<slug>.json` (katrs ieraksts ar burtisku citātu no plāna, ko skripts pārbauda); lappuse no `<!-- lpp. N -->`, koordinātas pārbaudītas pret novada robežu un VZD adrešu reģistru. Kvalitāte: `notes/ca-plani-kvalitate.md`. Palaišana lokāli: `uv run --no-project --with shapely --with pyproj src/karte/db/ca_plani.py` (vajag `kadastrs.db`). |
| `db/slimnicas_24h.py` | 37 slimnīcas ar 24/7 neatliekamo palīdzību (VM 04.03.2026. rīkojums, Valsts katastrofu medicīnas plāna 12. pielikums) → `dati/slimnicas_24h.geojson`. Koordinātas no VZD adrešu reģistra (`aw_eka.csv`), PSKUS un RAKUS — uzņemšanas ieeja no OSM. Adreses pārbaudītas; `atseviski_dati/hospitals.csv` koordinātas bija aptuvenas (līdz 118 km nobīde), tāpēc netiek lietotas. |
| `api/karte_api.py` | API (Python standarta bibliotēka + psycopg). Galapunkti aprakstīti faila sākumā. |
| `/api/bridinajumi`, `/api/udens` | Bez datubāzes: LVĢMC brīdinājumi (data.gov.lv CSV), ūdens līmenis (tas pats `udens_limenis.py`). Kešs API atmiņā; avots nepieejams → pēdējā zināmā vērtība vai 503. Darbojas uzreiz pēc sapludināšanas (API pārstartējas pats). |
| `/api/pludi` | Vai adrese ir plūdu riska zonā: a) PostGIS `pludu_zonas` (ja ir rindas, ~10 ms) → b) LVĢMC WMS GetFeatureInfo (lēns, mēdz neatbildēt) ar kešu `pludi_kesa` (4 zīmes ≈ 10 m, 7 dienas; LVĢMC neatbild → arī vecāks, `novecojis: true`) → c) 200 `{"zinams": false}`. Atbildē `metode`: „PostGIS kopija” / „LVĢMC WMS” / „kešs no HH:MM”. `?wms=1` izlaiž a). Testi bez DB: `src/testi/pludi_testi.py`. |
| `db/pludu_zonas.py` | LVĢMC 3. cikla plūdu riska zonas (10 % un 1 %; pavasara pali, ledus sastrēgumi, jūras vējuzplūdi) no ĢeoLatvija.lv SHP failiem (ģeoprodukts 361, CC BY-SA 4.0). `lejupieladet` (lokāli, `uv run --no-project --with pyshp --with shapely --with pyproj --with numpy`, ~15 min) → `dati/pludu_zonas.geojson.gz` (41,6 MB, 57 589 objekti — virs 40 MB, tāpēc nav git: scp uz VPS); `ieladet` (VPS, atjaunot_visu.sh, ja fails mainījies) → PostGIS `pludu_zonas` (ST_MakeValid + ST_Subdivide). |
| `db/pludi_siltums.py` | Demo adresēm (`production/demo/scenariji.json`, `src/testi/parbaude.py`) piepilda `pludi_kesa` caur vietējo API (`?wms=1`) un salīdzina ar kopiju; atjaunot_visu.sh beigās. |
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
python src/karte/db/osm_poi.py          # OSM bankomāti, DUS, ūdens, Wi-Fi, EV, veterināri → dati/ (lokāli; tad PR)
bash src/karte/db/ielade_visu.sh        # VPS: shēma + visi avoti datubāzē
bash src/karte/db/regioni.sh            # VPS: robežas (reizi mēnesī pietiek)
bash src/karte/db/adreses.sh            # VPS: adrešu meklēšana (reizi mēnesī pietiek)
systemctl start hakatons-udens.service  # VPS: ūdens līmenis tagad (citādi katru stundu pats)
```

`ielade.py` papildus: `--srid 3059` (LKS-92 TM koordinātas), `--kodejums cp1257`, `--atdalitajs ";"`.
`--apvienot 35` izmet viena avota dublikātus ≤ 35 m (tā pati kategorija, saderīgs nosaukums/adrese/operator/brand, garumzīmes neņem vērā); izmesto ID paliek īpašībā `dublikati`. Lieto patvertnēm un OSM.

## API izmaiņas

`karte_api.py` izmaiņas nonāk produkcijā pašas: pēc PR sapludināšanas sinhronizācija atjauno failu,
un `hakatons-map-api-restart.path` pārstartē servisu. Žurnāls: `journalctl -u hakatons-map-api`.
