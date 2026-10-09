#!/usr/bin/env bash
# Ielādē visus kartes punktu avotus datubāzē `map` (VPS). Katrs avots aizvieto savu iepriekšējo saturu.
# Avotu licences un saites: tabula avoti (shema.sql). Jaunu failu lejupielāde: valsts_dati.py, osm_poi.py.
# Palaišana (VPS): cd /srv/hakatons && set -a && . /etc/hakatons/map.env && set +a && bash src/karte/db/ielade_visu.sh
set -euo pipefail
cd "$(dirname "$0")/../../.."
D=src/karte/dati
L="python3 src/karte/db/ielade.py"

psql "$MAP_DB_OWNER_DSN" -q -v ON_ERROR_STOP=1 -f src/karte/db/shema.sql 2>&1 | grep -v NOTICE || true

$L $D/patvertnes.geojson --avots vugd-112 --kategorija patvertne --id "{_nr}" --nosaukums "{veids}" --adrese "{iela} {nr}, {vieta}"
$L $D/slimnicas_24h.geojson --avots vm-24h --kategorija neatliekama_24h --id "{nr}" --nosaukums "{nosaukums}" --adrese "{adrese}"
$L $D/iemic_arstniecibas_iestades.csv --avots iemic-arstniecibas --kategorija slimnica --nosaukums "{nosaukums}" --adrese "{adrese}" --lon x --lat y
$L $D/zva_aptiekas.csv --avots zva-fdu --kategorija aptieka --nosaukums "{nosaukums}" --adrese "{adrese}" --lon x --lat y
$L $D/iemic_vp_iecirkni.csv --avots iemic-vp --kategorija policija --nosaukums "{nosaukums}" --adrese "{adrese}" --lon x --lat y --srid 3059
$L $D/iemic_pasvaldibu_policija.csv --avots iemic-pp --kategorija policija --nosaukums "{nosaukums}" --adrese "{adrese}" --lon x --lat y
$L $D/iemic_vugd_depo.csv --avots iemic-vugd --kategorija ugunsdzeseji --nosaukums "{nosaukums}" --adrese "{adrese}" --lon x --lat y --srid 3059
$L $D/osm_poi.geojson --avots osm --nosaukums "{name}" --adrese "{adrese}"

psql "$MAP_DB_OWNER_DSN" -c "select o.avots, a.licence, o.kategorija, count(*) from objekti o join avoti a on a.kods = o.avots group by 1, 2, 3 order by 1, 3"
