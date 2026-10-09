#!/usr/bin/env bash
# Adrešu meklēšanai: spēkā esošās ēku adreses ar koordinātām no VZD adrešu reģistra (aw_eka.csv, CC-BY-4.0) → tabula adreses.
# Palaišana (VPS): set -a; . /etc/hakatons/map.env; set +a; bash src/karte/db/adreses.sh
# Vajag: curl, psql. Tabula un indekss: shema.sql. Reizi mēnesī pietiek.
set -euo pipefail

URL=https://data.gov.lv/dati/dataset/6b06a7e8-dedf-4705-a47b-2a7c51177473/resource/a510737a-18ce-400f-ad4b-04fce5228272/download/aw_eka.csv
DIR=${MAP_CACHE:-/var/lib/hakatons-map}
: "${MAP_DB_OWNER_DSN:?iestati MAP_DB_OWNER_DSN (/etc/hakatons/map.env)}"

mkdir -p "$DIR"
curl -sSfL -z "$DIR/aw_eka.csv" -o "$DIR/aw_eka.csv" "$URL"

psql "$MAP_DB_OWNER_DSN" -q -v ON_ERROR_STOP=1 <<SQL
begin;
create temp table stg (kods text, tips_cd text, statuss text, apstipr text, apst_pak text, vkur_cd text, vkur_tips text,
  nosaukums text, sort_nos text, atrib text, pnod_cd text, dat_sak text, dat_mod text, dat_beig text, for_build text,
  plan_adr text, std text, koord_x text, koord_y text, dd_n text, dd_e text) on commit drop;
\copy stg from '$DIR/aw_eka.csv' with (format csv, header true, encoding 'UTF8')

truncate adreses;
insert into adreses (kods, adrese, meklesanai, geom)
select kods, std, lower(unaccent(std)), st_setsrid(st_makepoint(dd_e::float8, dd_n::float8), 4326)
from stg
where statuss = 'EKS' and dd_n <> '' and dd_e <> '' and std <> '';
commit;
analyze adreses;
SQL

psql "$MAP_DB_OWNER_DSN" -Atc "select count(*) || ' adreses' from adreses"
