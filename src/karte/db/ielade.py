"""Ielādē punktu datu kopu tabulā objekti, aizvietojot visu iepriekšējo tā paša avota saturu.

Droši palaist atkārtoti: rindas atjauno pēc (avots, avota_id). Rindas, kuru jaunajā failā nav, dzēš tikai tad, ja
failā ir vismaz 90 % no iepriekšējā skaita (sargs pret tukšu vai pusē pārtrauktu lejupielādi; --atlaut-samazinajumu
to atceļ). Tad iznākuma kods ir 3, un vecās rindas paliek. Pēc ielādes avoti.atjaunots = now().

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
import math
import os
import re
import string
import sys
import unicodedata

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


def _norm(teksts):
    teksts = unicodedata.normalize("NFKD", teksts or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]", "", teksts)


def _sakrit(a, b, pa_dalam=False):
    """Vai teksti nozīmē to pašu: vienādi bez garumzīmēm/pieturzīmēm, viens tukšs vai (adresei) viena
    adreses daļas ir otras apakškopa ("Dikļi, Valmieras novads" ⊂ "Dikļi, Dikļu pagasts, Valmieras novads")."""
    if not a or not b or _norm(a) == _norm(b):
        return True
    if not pa_dalam:
        return False
    da, db = ({_norm(x) for x in t.split(",")} - {""} for t in (a, b))
    return da <= db or db <= da


def apvienot_dublikatus(rindas, metri, srid):
    """Izmet viena avota dublikātus: tā pati kategorija, ≤ metri, saderīgs nosaukums, adrese un (ja ir)
    operator/brand.
    Ja nosaukums un adrese ir burtiski vienādi un punkti nesakrīt (> 1 m), tās ir dažādas ēkas vienā
    adresē (piem. 112.lv patvertnes) un paliek abas. Paliek punkts ar vairāk aizpildītām īpašībām."""

    def attalums(r, s):
        dx, dy = r[8] - s[8], r[9] - s[9]
        if srid == 4326:
            dx *= 111320 * math.cos(math.radians(r[9]))
            dy *= 110540
        return math.hypot(dx, dy)

    def pilniba(r):
        return (bool(r[1]), bool(r[2]), sum(v not in (None, "") for v in r[3].obj.values()))

    ids = sorted(rindas, key=lambda k: pilniba(rindas[k]), reverse=True)
    izmesti = {}
    for i, a in enumerate(ids):
        if a in izmesti:
            continue
        ra = rindas[a]
        for b in ids[i + 1:]:
            rb = rindas[b]
            if b in izmesti or ra[0] != rb[0] or attalums(ra, rb) > metri:
                continue
            if not (_sakrit(ra[1], rb[1]) and _sakrit(ra[2], rb[2], pa_dalam=True)):
                continue
            if not all(_sakrit(ra[3].obj.get(k), rb[3].obj.get(k)) for k in ("operator", "brand")):
                continue  # piem. SEB un Citadele bankomāti vienā vietā bez nosaukuma (OSM)
            if ra[1] and ra[2] and (ra[1], ra[2]) == (rb[1], rb[2]) and attalums(ra, rb) > 1:
                continue
            izmesti[b] = a
    for b, a in izmesti.items():
        rindas[a][3].obj.setdefault("dublikati", []).append(b)
        del rindas[b]
    return len(izmesti)


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
    p.add_argument("--apvienot", type=float, default=0, metavar="M",
                   help="apvienot dublikātus ≤ M metru attālumā (skat. apvienot_dublikatus); noklusēti izslēgts")
    p.add_argument("--atlaut-samazinajumu", action="store_true",
                   help="dzēst trūkstošās rindas arī tad, ja jaunajā failā ir < 90 %% no iepriekšējā skaita")
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
    if args.apvienot:
        print(f"{args.avots}: {apvienot_dublikatus(rindas, args.apvienot, args.srid)} dublikāti apvienoti")

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
        cur.execute("select (select count(*) from objekti where avots = %s), (select count(*) from jauni)", (args.avots,))
        bija, jauni = cur.fetchone()
        sargs = bija > 0 and jauni < 0.9 * bija and not args.atlaut_samazinajumu
        if sargs:  # tukša vai nepilnīga lejupielāde nedrīkst izdzēst slāni
            dzesti = 0
            print(f"{args.avots}: jaunajā failā {jauni} no {bija} (< 90 %); vecās rindas netiek dzēstas", file=sys.stderr)
        else:
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
        # ielādes laiks avotam (Datu avoti panelis, statusa lapas "Datu vecums"); kolonna arī shema.sql
        cur.execute("alter table avoti add column if not exists atjaunots timestamptz")
        if not sargs:  # nepilnīga ielāde nav "atjaunots"
            cur.execute("update avoti set atjaunots = now() where kods = %s", (args.avots,))
    if sargs:
        sys.exit(3)


if __name__ == "__main__":
    main()
