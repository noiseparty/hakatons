#!/usr/bin/env bash
# Ūdens līmenis (LVĢMC, data.gov.lv, CC0) → objekti, avots lvgmc-hidro. Palaiž hakatons-udens.timer katru stundu.
# Ar roku (VPS): cd /srv/hakatons && set -a && . /etc/hakatons/map.env && set +a && bash src/karte/db/udens_limenis.sh
set -euo pipefail
cd "$(dirname "$0")/../../.."
: "${MAP_DB_OWNER_DSN:?iestati MAP_DB_OWNER_DSN (/etc/hakatons/map.env)}"
# pirmajā reizē pēc sapludināšanas slānis un avots vēl nav datubāzē
if [ -z "$(psql "$MAP_DB_OWNER_DSN" -Atc "select 1 from kategorijas where kods = 'udens_limenis'")" ]; then
  psql "$MAP_DB_OWNER_DSN" -q -v ON_ERROR_STOP=1 -f src/karte/db/shema.sql 2>&1 | grep -v NOTICE || true
fi

F=$(mktemp --suffix=.geojson)
trap 'rm -f "$F"' EXIT

python3 src/karte/db/udens_limenis.py "$F"
python3 src/karte/db/ielade.py "$F" --avots lvgmc-hidro --kategorija udens_limenis \
    --id "{stacija}" --nosaukums "{nosaukums}" --derigs-no "{laiks}" --derigs-lidz "{derigs_lidz}"
