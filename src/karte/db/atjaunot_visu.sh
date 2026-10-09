#!/usr/bin/env bash
# Kartes datu atjaunošana (VPS): lejupielādē ikdienas avotus un ielādē tos datubāzē `map`; statiskos (repozitorija
# momentuzņēmumus) ielādē tikai, ja fails mainījies kopš pēdējās ielādes. Palaiž hakatons-dati.timer katru dienu 04:30.
#
#   bash src/karte/db/atjaunot_visu.sh               ikdienas režīms (timer): lejupielāde → $HAKATONS_DATI, ielāde
#   bash src/karte/db/atjaunot_visu.sh --visi        bez lejupielādes, visu no src/karte/dati no jauna (ielade_visu.sh)
#   bash src/karte/db/atjaunot_visu.sh --parbaude    tikai izdrukā komandas (var kopā ar --visi)
#
# Ikdienas avotus lejupielādē mapē $HAKATONS_DATI (noklusēti /var/lib/hakatons/dati), nevis git kopijā /srv/hakatons,
# ko sinhronizācija ik minūti atjauno no main. Ielādē tikai tos failus, kas šajā reizē tiešām lejupielādēti.
# ielade.py nedzēš rindas, ja jaunajā failā ir < 90 % no iepriekšējā skaita (iznākuma kods 3 = brīdinājums).
# Viena avota kļūda neaptur pārējos; beigās iznākuma kods 1, ja kāds avots neizdevās (journalctl -u hakatons-dati).
set -uo pipefail
cd "$(dirname "$0")/../../.."

PARBAUDE=0; VISI=0
for a in "$@"; do
  case "$a" in
    --parbaude) PARBAUDE=1 ;;
    --visi) VISI=1 ;;
    *) echo "nezināms arguments: $a" >&2; exit 2 ;;
  esac
done

REPO=src/karte/dati
JAUNI=${HAKATONS_DATI:-/var/lib/hakatons/dati}
export HAKATONS_DATI=$JAUNI   # valsts_dati.py, osm_poi.py, gtfs.py raksta šeit
STAVOKLIS=${HAKATONS_STAVOKLIS:-/var/lib/hakatons/ielades}   # statisko failu sha256 pēc pēdējās ielādes
L="python3 src/karte/db/ielade.py"
KLUDAS=()

darit() {  # komanda vai tās izdruka (--parbaude)
  if [ "$PARBAUDE" = 1 ]; then printf '+ %s\n' "$*"; return 0; fi
  "$@"
}

ieladet() {  # ieladet <avots> <fails> <ielade.py argumenti…>
  local avots=$1 fails=$2; shift 2
  darit $L "$fails" --avots "$avots" "$@"
  local k=$?
  if [ "$k" = 3 ]; then echo "BRĪDINĀJUMS: $avots — fails mazāks par 90 % no iepriekšējā; vecās rindas paliek" >&2
  elif [ "$k" != 0 ]; then KLUDAS+=("$avots"); echo "KĻŪDA: $avots ielāde (kods $k)" >&2; fi
  return 0
}

# Ikdienas avotam: ielādē tikai šajā reizē lejupielādētu failu (jaunāku par sākuma atzīmi); --visi — no repozitorija.
ikdienas() {  # ikdienas <avots> <faila vārds> <ielade.py argumenti…>
  local avots=$1 vards=$2; shift 2
  if [ "$VISI" = 1 ]; then ieladet "$avots" "$REPO/$vards" "$@"; return; fi
  local f="$JAUNI/$vards"
  if [ "$PARBAUDE" = 1 ] || { [ -s "$f" ] && [ "$f" -nt "$SAKUMS" ]; }; then ieladet "$avots" "$f" "$@"
  else KLUDAS+=("$avots"); echo "KĻŪDA: $avots — $vards šoreiz nav lejupielādēts; datubāzē paliek iepriekšējais" >&2; fi
}

# Statiskam avotam (fails repozitorijā): ielādē, ja sha256 atšķiras no pēdējās ielādes; --visi — vienmēr.
statisks() {  # statisks <avots> <fails> <ielade.py argumenti…>
  local avots=$1 f=$2; shift 2
  local sha; sha=$( { [ -f "$f" ] && sha256sum "$f" || echo parbaude; } | cut -d' ' -f1)
  if [ "$VISI" = 0 ] && [ "$(cat "$STAVOKLIS/$avots.sha256" 2>/dev/null)" = "$sha" ]; then
    echo "$avots: nav mainījies, izlaiž"; return
  fi
  local pirms=${#KLUDAS[@]}
  ieladet "$avots" "$f" "$@"
  if [ "${#KLUDAS[@]}" = "$pirms" ] && [ "$PARBAUDE" = 0 ]; then mkdir -p "$STAVOKLIS" && echo "$sha" > "$STAVOKLIS/$avots.sha256"; fi
}

lejupieladet() {  # lejupieladet <nosaukums> <komanda…>; kļūda neaptur pārējo
  if ! darit "${@:2}"; then KLUDAS+=("$1"); echo "KĻŪDA: lejupielāde $*" >&2; fi
}

: "${MAP_DB_OWNER_DSN:?iestati MAP_DB_OWNER_DSN (/etc/hakatons/map.env)}"
SAKUMS=$(mktemp); trap 'rm -f "$SAKUMS" /tmp/ca_plani.$$.geojson' EXIT
[ "$PARBAUDE" = 1 ] || mkdir -p "$JAUNI"

# 0. Shēma (idempotenta; arī jaunas tabulas un avoti.atjaunots)
if [ "$PARBAUDE" = 1 ]; then echo "+ psql \$MAP_DB_OWNER_DSN -f src/karte/db/shema.sql"
else
  psql "$MAP_DB_OWNER_DSN" -q -v ON_ERROR_STOP=1 -f src/karte/db/shema.sql 2>&1 | grep -v NOTICE
  [ "${PIPESTATUS[0]}" = 0 ] || KLUDAS+=(shema)  # psql kods, nevis grep (tukša izvade = labi)
fi

# 1. Lejupielāde (tikai ikdienas režīmā)
if [ "$VISI" = 0 ]; then
  lejupieladet valsts_dati python3 src/karte/db/valsts_dati.py   # ZVA, IeM IC (4), VKCP ūdens ņemšanas vietas
  lejupieladet osm_poi python3 src/karte/db/osm_poi.py           # OSM bankomāti, DUS
  lejupieladet gtfs python3 src/karte/db/gtfs.py                 # pieturas: Rīgas satiksme, ATD, VIVI
fi

# 2. Ikdienas avoti
ikdienas iemic-arstniecibas iemic_arstniecibas_iestades.csv --kategorija slimnica --nosaukums "{nosaukums}" --adrese "{adrese}" --lon x --lat y
ikdienas zva-fdu zva_aptiekas.csv --kategorija aptieka --nosaukums "{nosaukums}" --adrese "{adrese}" --lon x --lat y
ikdienas iemic-vp iemic_vp_iecirkni.csv --kategorija policija --nosaukums "{nosaukums}" --adrese "{adrese}" --lon x --lat y --srid 3059
ikdienas iemic-pp iemic_pasvaldibu_policija.csv --kategorija policija --nosaukums "{nosaukums}" --adrese "{adrese}" --lon x --lat y
ikdienas iemic-vugd iemic_vugd_depo.csv --kategorija ugunsdzeseji --nosaukums "{nosaukums}" --adrese "{adrese}" --lon x --lat y --srid 3059
ikdienas vkcp-udens vkcp_udens_nemsanas_vietas.csv --kategorija udens_nemsana --nosaukums "{nosaukums}" --lon x --lat y --srid 3059
ikdienas osm osm_poi.geojson --nosaukums "{name}" --adrese "{adrese}" --apvienot 35
ikdienas rs-gtfs gtfs_rigas_satiksme.csv --kategorija pietura --nosaukums "{nosaukums}" --lon x --lat y
ikdienas atd-gtfs gtfs_atd.csv --kategorija pietura --nosaukums "{nosaukums}" --lon x --lat y
ikdienas vivi-gtfs gtfs_vivi.csv --kategorija pietura --nosaukums "{nosaukums}" --lon x --lat y

# 3. Statiskie avoti no repozitorija (mainās tikai ar PR): ielādē, ja fails mainījies
statisks vugd-112 $REPO/patvertnes.geojson --kategorija patvertne --id "{_nr}" --nosaukums "{veids}" --adrese "{iela} {nr}, {vieta}" --apvienot 35
statisks vm-24h $REPO/slimnicas_24h.geojson --kategorija neatliekama_24h --id "{nr}" --nosaukums "{nosaukums}" --adrese "{adrese}"
# CA plāni: abi slāņi ir viens avots, tāpēc vienā failā (ca_plani.py vajag kadastra DB, tāpēc to palaiž lokāli un PR)
CA=/tmp/ca_plani.$$.geojson
if [ "$PARBAUDE" = 1 ]; then echo "+ apvienot $REPO/ca_pulcesanas_vietas.geojson + $REPO/ca_izmitinasana.geojson > $CA"
elif ! python3 -c 'import json,sys; f=[x for p in sys.argv[1:] for x in json.load(open(p, encoding="utf-8"))["features"]]; json.dump({"type":"FeatureCollection","features":f},sys.stdout)' \
  $REPO/ca_pulcesanas_vietas.geojson $REPO/ca_izmitinasana.geojson > "$CA"; then
  CA=; KLUDAS+=(ca-plani); echo "KĻŪDA: CA plānu failus neizdevās apvienot" >&2
fi
[ -n "$CA" ] && statisks ca-plani "$CA" --kategorija "{kategorija}" --id "{id}" --nosaukums "{nosaukums}" --adrese "{adrese}"

if [ "$PARBAUDE" = 0 ]; then
  psql "$MAP_DB_OWNER_DSN" -c "select a.kods, a.atjaunots, count(o.id) from avoti a left join objekti o on o.avots = a.kods group by 1, 2 order by 1"
fi
if [ "${#KLUDAS[@]}" -gt 0 ]; then echo "Neizdevās: ${KLUDAS[*]}" >&2; exit 1; fi
echo "Gatavs."
