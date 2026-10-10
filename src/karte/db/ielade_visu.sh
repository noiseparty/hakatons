#!/usr/bin/env bash
# Ielādē visus kartes punktu avotus no repozitorija momentuzņēmumiem (src/karte/dati) datubāzē `map` (VPS), no jauna.
# Komandu saraksts ir vienā vietā: atjaunot_visu.sh (ikdienas atjaunošana, hakatons-dati.timer). Šis ir tā režīms --visi:
# bez lejupielādes, visi avoti neatkarīgi no tā, vai fails mainījies. Avotu licences un saites: tabula avoti (shema.sql).
# Palaišana (VPS): cd /srv/hakatons && set -a && . /etc/hakatons/map.env && set +a && bash src/karte/db/ielade_visu.sh
exec bash "$(dirname "$0")/atjaunot_visu.sh" --visi "$@"
