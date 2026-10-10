"""Sabiedriskā transporta pieturas no GTFS (data.gov.lv, CC0) → src/karte/dati/gtfs_<avots>.csv kategorijai pietura.

Pieturas kā evakuācijas savākšanas vietas: nosaukums, cik maršrutu tajā apstājas un kuri (pēc stop_times → trips →
routes), transporta veidi. Pieturas, kurās neapstājas neviens reiss, izlaiž. Avoti (tabula avoti, shema.sql):
  rs-gtfs   Rīgas satiksme, jaunākais ZIP datu kopā marsrutu-saraksti-rigas-satiksme-sabiedriskajam-transportam
  atd-gtfs  Autotransporta direkcija, starppilsētu un vietējās nozīmes autobusi
  vivi-gtfs Autotransporta direkcija, iekšzemes vilcieni (vivi.lv)
Palaišana (lokāli vai VPS, tikai standarta bibliotēka): python src/karte/db/gtfs.py
"""

import collections
import csv
import io
import json
import os
import pathlib
import urllib.request
import zipfile

# HAKATONS_DATI: cita mape (VPS ikdienas atjaunošana raksta /var/lib/hakatons/dati, nevis git kopijā)
DATI = pathlib.Path(os.environ.get("HAKATONS_DATI") or pathlib.Path(__file__).resolve().parents[1] / "dati")
UA = {"User-Agent": "map.repo.lv (AI Open Data 2026 hakatons)"}
CKAN = "https://data.gov.lv/dati/api/3/action/package_show?id="
VEIDI = {"0": "tramvajs", "1": "metro", "2": "vilciens", "3": "autobuss", "4": "prāmis", "11": "trolejbuss",
         "100": "vilciens", "109": "vilciens", "200": "autobuss", "700": "autobuss", "800": "trolejbuss", "900": "tramvajs"}


def lejupieladet(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=300) as r:
        return r.read()


def jaunakais_zip(datu_kopa):
    """Datu kopas jaunākā ZIP resursa saite (Rīgas satiksme katru mēnesi pievieno jaunu failu)."""
    kopa = json.loads(lejupieladet(CKAN + datu_kopa))["result"]
    zipi = [r for r in kopa["resources"] if (r.get("format") or "").lower() == "zip" or r["url"].lower().endswith(".zip")]
    return max(zipi, key=lambda r: r.get("created") or "")["url"]


def tabula(arhivs, vards):
    """GTFS teksta fails kā vārdnīcu saraksts; ATD failos aiz komatiem ir atstarpes."""
    teksts = arhivs.read(vards).decode("utf-8-sig")
    lasitajs = csv.reader(io.StringIO(teksts), skipinitialspace=True)
    galva = [g.strip() for g in next(lasitajs)]
    return [{g: (v or "").strip() for g, v in zip(galva, rinda)} for rinda in lasitajs if rinda]


def pieturas(zip_baiti, avots):
    a = zipfile.ZipFile(io.BytesIO(zip_baiti))
    marsruti = {r["route_id"]: r for r in tabula(a, "routes.txt")}
    reisa_marsruts = {t["trip_id"]: t["route_id"] for t in tabula(a, "trips.txt")}
    pietura_marsruti = collections.defaultdict(set)
    for st in tabula(a, "stop_times.txt"):
        m = reisa_marsruts.get(st["trip_id"])
        if m:
            pietura_marsruti[st["stop_id"]].add(m)
    rindas = []
    for p in tabula(a, "stops.txt"):
        if p.get("location_type") not in ("", "0"):  # stacijas / ieejas: rāda tikai pieturvietas
            continue
        ms = [marsruti[m] for m in pietura_marsruti.get(p["stop_id"], ()) if m in marsruti]
        if not ms or not p.get("stop_lat"):
            continue
        nosaukumi = sorted({m.get("route_short_name") or m.get("route_long_name") or "" for m in ms} - {""},
                           key=lambda x: (len(x), x))
        rindas.append({
            "id": p["stop_id"], "nosaukums": p["stop_name"].strip('"'), "marsruti": len(ms),
            "marsrutu_saraksts": ", ".join(nosaukumi[:12]) + (" …" if len(nosaukumi) > 12 else ""),
            "veidi": ", ".join(sorted({VEIDI.get(m.get("route_type", ""), "cits") for m in ms})),
            "x": p["stop_lon"], "y": p["stop_lat"],
        })
    cels = DATI / f"gtfs_{avots}.csv"
    with open(cels, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["id", "nosaukums", "marsruti", "marsrutu_saraksts", "veidi", "x", "y"],
                           lineterminator="\n")
        w.writeheader()
        w.writerows(sorted(rindas, key=lambda r: r["id"]))
    print(f"{cels.name}: {len(rindas)} pieturas")


if __name__ == "__main__":
    DATI.mkdir(parents=True, exist_ok=True)
    pieturas(lejupieladet(jaunakais_zip("marsrutu-saraksti-rigas-satiksme-sabiedriskajam-transportam")), "rigas_satiksme")
    pieturas(lejupieladet("https://www.atd.lv/sites/default/files/GTFS/gtfs-latvia-lv.zip"), "atd")
    pieturas(lejupieladet("https://vivi.lv/uploads/GTFS.zip"), "vivi")
