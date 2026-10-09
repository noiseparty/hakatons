"""Ielādē punktu datu kopu tabulā objekti, aizvietojot visu iepriekšējo tā paša avota saturu.

Ievade: GeoJSON (Point) vai CSV ar koordinātu kolonnām (WGS-84). Citus formātus (Excel, XML,
API, adreses bez koordinātām) vispirms pārveido uz vienu no šiem, skat. src/karte/README.md.

Laukus aizpilda ar Python formāta šabloniem no īpašībām, piem. --adrese "{iela} {nr}, {vieta}".
Visas īpašības tiek saglabātas arī ipasibas (jsonb) un parādās API.

Palaišana (VPS):
  set -a; . /etc/hakatons/map.env; set +a
  python3 src/karte/db/ielade.py src/karte/dati/patvertnes.geojson --avots vugd-112 \
      --kategorija patvertne --id "{objectid}" --nosaukums "{veids}" --adrese "{iela} {nr}, {vieta}"
"""

import argparse
import csv
import json
import os
import string
import sys

import psycopg
from psycopg.types.json import Jsonb


class _Tukss(dict):
    def __missing__(self, key):
        return ""


def aizpildit(sablons, ipasibas):
    if not sablons:
        return None
    vertibas = _Tukss({k: ("" if v is None else v) for k, v in ipasibas.items()})
    teksts = string.Formatter().vformat(sablons, (), vertibas)
    teksts = " ".join(teksts.split()).strip(" ,;-")
    return teksts or None


def lasit(cels, args):
    """Atgriež (ipasibas, lon, lat) katram punktam."""
    if cels.lower().endswith(".csv"):
        with open(cels, encoding=args.kodejums, newline="") as f:
            for rinda in csv.DictReader(f, delimiter=args.atdalitajs):
                try:
                    lon = float(rinda[args.lon].replace(",", "."))
                    lat = float(rinda[args.lat].replace(",", "."))
                except (KeyError, ValueError):
                    continue
                yield rinda, lon, lat
        return
    with open(cels, encoding="utf-8-sig") as f:
        gj = json.load(f)
    for i, fea in enumerate(gj.get("features", [])):
        geom = fea.get("geometry") or {}
        if geom.get("type") != "Point":
            continue
        ipasibas = dict(fea.get("properties") or {})
        if "id" in fea and "id" not in ipasibas:
            ipasibas["id"] = fea["id"]
        ipasibas.setdefault("_nr", i)
        lon, lat = geom["coordinates"][:2]
        yield ipasibas, float(lon), float(lat)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("fails")
    p.add_argument("--avots", required=True, help="avota identifikators, piem. vugd-112, osm")
    p.add_argument("--kategorija", default="{kategorija}", help="kategorijas kods vai šablons")
    p.add_argument("--id", default="{id}", help="unikāls ID avota ietvaros (šablons); noklusēti {id}")
    p.add_argument("--nosaukums", help="šablons")
    p.add_argument("--adrese", help="šablons")
    p.add_argument("--derigs-no", help="šablons ar ISO laiku (incidentiem)")
    p.add_argument("--derigs-lidz", help="šablons ar ISO laiku (incidentiem)")
    p.add_argument("--lat", default="lat", help="CSV kolonna")
    p.add_argument("--lon", default="lon", help="CSV kolonna")
    p.add_argument("--atdalitajs", default=",", help="CSV atdalītājs")
    p.add_argument("--kodejums", default="utf-8-sig", help="CSV kodējums, piem. cp1257")
    p.add_argument("--srid", type=int, default=4326, help="koordinātu sistēma, piem. 3059 (LKS-92 TM: lon=x, lat=y)")
    p.add_argument("--dsn", default=os.environ.get("MAP_DB_OWNER_DSN"))
    args = p.parse_args()
    if not args.dsn:
        sys.exit("Nav MAP_DB_OWNER_DSN (skat. /etc/hakatons/map.env)")

    rindas = {}
    for ipasibas, lon, lat in lasit(args.fails, args):
        if args.srid == 4326 and not (20 < lon < 29 and 55 < lat < 59):
            continue  # ārpus Latvijas vai sajauktas koordinātas (citām sistēmām pārbauda datubāzē)
        avota_id = aizpildit(args.id, ipasibas) or str(ipasibas.get("_nr"))
        ipasibas.pop("_nr", None)
        rindas[avota_id] = (
            aizpildit(args.kategorija, ipasibas),
            aizpildit(args.nosaukums, ipasibas),
            aizpildit(args.adrese, ipasibas),
            Jsonb(ipasibas),
            args.avots,
            avota_id,
            aizpildit(args.derigs_no, ipasibas),
            aizpildit(args.derigs_lidz, ipasibas),
            lon,
            lat,
        )
    if not rindas:
        sys.exit("Failā nav neviena derīga punkta Latvijā; nekas netika mainīts.")

    with psycopg.connect(args.dsn) as conn, conn.cursor() as cur:
        cur.execute("create temp table jauni (like objekti including defaults) on commit drop")
        cur.execute("alter table jauni alter column geom type geometry")
        with cur.copy(
            "copy jauni (kategorija, nosaukums, adrese, ipasibas, avots, avota_id, derigs_no, derigs_lidz, geom)"
            " from stdin"
        ) as copy:
            for r in rindas.values():
                copy.write_row((*r[:8], f"SRID={args.srid};POINT({r[8]} {r[9]})"))
        cur.execute("update jauni set geom = st_transform(geom, 4326)")
        cur.execute("delete from jauni where not st_intersects(geom, st_makeenvelope(20, 55, 29, 59, 4326))")
        cur.execute("select distinct j.avots from jauni j left join avoti a on a.kods = j.avots where a.kods is null")
        if cur.fetchall():
            sys.exit(f"Avots {args.avots!r} nav tabulā avoti. Pievieno to shema.sql (avoti) ar licenci un saiti.")
        cur.execute(
            "select distinct j.kategorija from jauni j left join kategorijas k on k.kods = j.kategorija where k.kods is null"
        )
        nezinamas = [r[0] for r in cur.fetchall()]
        if nezinamas:
            sys.exit(f"Nezināmas kategorijas: {nezinamas}. Pievieno tās shema.sql (kategorijas).")
        cur.execute("delete from objekti where avots = %s and avota_id not in (select avota_id from jauni)", (args.avots,))
        dzesti = cur.rowcount
        cur.execute(
            """insert into objekti (kategorija, nosaukums, adrese, ipasibas, avots, avota_id, derigs_no, derigs_lidz, geom)
               select kategorija, nosaukums, adrese, ipasibas, avots, avota_id, derigs_no, derigs_lidz, geom from jauni
               on conflict (avots, avota_id) do update set
                 kategorija = excluded.kategorija, nosaukums = excluded.nosaukums, adrese = excluded.adrese,
                 ipasibas = excluded.ipasibas, derigs_no = excluded.derigs_no, derigs_lidz = excluded.derigs_lidz,
                 geom = excluded.geom, atjaunots = now()"""
        )
        print(f"{args.avots}: {cur.rowcount} ielādēti, {dzesti} dzēsti")


if __name__ == "__main__":
    main()
