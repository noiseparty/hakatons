#!/usr/bin/env bash
# Pašvaldību un pilsētu robežas no VZD adrešu reģistra (aw_shp.zip, CC-BY-4.0) → tabula regioni.
# Palaišana (VPS): set -a; . /etc/hakatons/map.env; set +a; bash src/karte/db/regioni.sh
# Vajag: curl, unzip, shp2pgsql (pakete postgis), psql.
set -euo pipefail

URL=https://data.gov.lv/dati/dataset/6b06a7e8-dedf-4705-a47b-2a7c51177473/resource/b643b1b3-223f-4394-9beb-18524f8b0b82/download/aw_shp.zip
DIR=${MAP_CACHE:-/var/lib/hakatons-map}
: "${MAP_DB_OWNER_DSN:?iestati MAP_DB_OWNER_DSN (/etc/hakatons/map.env)}"

mkdir -p "$DIR"
curl -sSfL -z "$DIR/aw_shp.zip" -o "$DIR/aw_shp.zip" "$URL"
unzip -o -q "$DIR/aw_shp.zip" 'Novadi.*' 'Pilsetas.*' -d "$DIR/aw_shp"

psql "$MAP_DB_OWNER_DSN" -q -v ON_ERROR_STOP=1 -c 'drop schema if exists stg cascade; create schema stg'
# Faili ir LKS-2020 TM; ielādējam kā LKS-92 TM (3059), starpība kartei nav būtiska (cm).
for t in Novadi Pilsetas; do
  shp2pgsql -c -s 3059 -W UTF-8 "$DIR/aw_shp/$t.shp" "stg.${t,,}" 2>/dev/null | psql "$MAP_DB_OWNER_DSN" -q -v ON_ERROR_STOP=1 >/dev/null
done

psql "$MAP_DB_OWNER_DSN" -q -v ON_ERROR_STOP=1 <<'SQL'
begin;
create temp table jauni on commit drop as
select kods::bigint::text as kods, nullif(atrib, '') as atvk, regexp_replace(nosaukums, ' nov\.$', ' novads') as nosaukums,
       case when t = 'novads' then 'novads'
            when vkur_cd = 100000000 then 'valstspilseta'
            else 'pilseta' end as tips,
       case when t = 'pilseta' and vkur_cd <> 100000000 then vkur_cd::bigint::text end as novads_kods,
       st_multi(st_collectionextract(st_makevalid(st_transform(geom, 4326)), 3)) as geom
from (select 'novads' as t, * from stg.novadi union all select 'pilseta', * from stg.pilsetas) s
where statuss = 'EKS';

delete from regioni where kods not in (select kods from jauni);
insert into regioni (kods, atvk, nosaukums, tips, novads_kods, geom, geom_vienk, atjaunots)
select kods, atvk, nosaukums, tips, novads_kods, geom,
       st_multi(st_collectionextract(st_makevalid(st_simplifypreservetopology(geom, 0.0005)), 3)), now()
from jauni
on conflict (kods) do update set
  atvk = excluded.atvk, nosaukums = excluded.nosaukums, tips = excluded.tips,
  novads_kods = excluded.novads_kods, geom = excluded.geom, geom_vienk = excluded.geom_vienk,
  atjaunots = now();

-- robežas mainījušās → piesaistām visus punktus no jauna
update objekti set geom = geom;
commit;
drop schema stg cascade;
SQL

psql "$MAP_DB_OWNER_DSN" -Atc "select tips, count(*) from regioni group by 1 order by 1"
