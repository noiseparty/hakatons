"""/api/plusma.xml un /api/kalendars.ics testi ar viltotiem datiem (bez datubāzes un ārējiem avotiem).

  uv run --no-project --python 3.12 --with "psycopg[binary]" --with feedparser --with icalendar src/testi/abonet_testi.py
"""

import os
import sys
import threading
import urllib.request
from datetime import datetime, timedelta, timezone

import feedparser
import icalendar

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "karte", "api"))
os.environ.setdefault("MAP_DB_DSN", "postgresql://viltots/x")
import karte_api as k  # noqa: E402

kludas = 0


def parbaude(nos, nosacijums):
    global kludas
    print(("ok    " if nosacijums else "KĻŪDA ") + nos)
    kludas += 0 if nosacijums else 1


OGRE = "100016688"
rit = (k._riga_tagad().date() + timedelta(days=1)).isoformat()
tagad = datetime.now(timezone.utc)
k.regioni = lambda _q: [{"kods": OGRE, "nosaukums": "Ogres novads", "bbox": [24.2, 56.6, 25.2, 57.0]},
                        {"kods": "100003003", "nosaukums": "Rīga", "bbox": [23.9, 56.85, 24.35, 57.09]}]
k.prognozes = lambda _q: {
    "prognoze_mainita": "Fri, 09 Oct 2026 20:43:14 GMT",
    "zinas": [{"veids": "bridinajums", "id": "28210", "paradiba": "Vējš", "virsraksts": "Dzeltens brīdinājums: vējš (Latvija), līdz 10.10. 06:00",
               "teksts": "Brāzmās līdz 20–24 m/s; koki, vadi; uzmanieties.", "regioni": [OGRE, "100003003"]},
              {"veids": "bridinajums", "id": "28999", "paradiba": "Lietus", "virsraksts": "Oranžs brīdinājums: lietus (Kurzeme)",
               "teksts": "Daudz lietus", "regioni": ["100016333"]},
              {"veids": "prognoze", "virsraksts": "x", "teksts": "y", "regioni": [OGRE]}],
    "regioni": {OGRE: {"nosaukums": "Ogres novads", "dienas": {rit: {"brazmas": 17.4, "brazmas_vieta": "Ikšķile", "nokrisni": 3,
                                                                       "laiks": "apmācies, vējains"}}},
                "100003003": {"nosaukums": "Rīga", "dienas": {rit: {"brazmas": 9, "nokrisni": 2}}}},
}
k.bridinajumi = lambda _q: {"bridinajumi": [{"id": "28210", "krasa": "Dzeltens", "no": "2026-10-09T14:00:00", "lidz": "2026-10-10T06:00:00",
                                             "riski": "ESI INFORMĒTS par stipru vēju!"}]}
k.udens_limenis.stacijas = lambda timeout=20: [
    {"properties": {"stacija": "HD073401", "nosaukums": "Ogre", "limenis_cm": 80, "izmaina_24h_cm": 25, "laiks": tagad.isoformat()},
     "geometry": {"coordinates": [24.64, 56.81]}},
    {"properties": {"stacija": "HD073999", "nosaukums": "Venta", "limenis_cm": 50, "izmaina_24h_cm": 30, "laiks": tagad.isoformat()},
     "geometry": {"coordinates": [21.6, 57.4]}},
    {"properties": {"stacija": "HD073418", "nosaukums": "Stariņi", "limenis_cm": -30, "izmaina_24h_cm": 2, "laiks": tagad.isoformat()},
     "geometry": {"coordinates": [24.61, 56.87]}}]
k.celu_notikumi_visi = lambda: [("negadijums", [{"id": "NG1", "nosaukums": "Šķērslis uz ceļa", "cels": "A6", "apraksts": "Nokrituši koki",
                                                 "lat": 56.82, "lon": 24.57, "no": (tagad - timedelta(hours=1)).isoformat(), "lidz": None}]),
                                ("remonts", [{"id": "RM1", "nosaukums": "Ceļa būvdarbi", "lat": 56.82, "lon": 24.6, "no": None, "lidz": None}])]
k.zibens = lambda _q: {"zibeni": [{"lat": 56.8, "lon": 24.6}, {"lat": 56.9, "lon": 24.7}, {"lat": 57.5, "lon": 22}],
                       "lidz": tagad.isoformat()}


def vaicat_nav(*a, **kw):
    raise k.psycopg.OperationalError("nav datubāzes")  # _punkti_regiona → bbox rezerve


k.vaicat = vaicat_nav

# Atom
r = k.plusma({"regions": [OGRE]})
f = feedparser.parse(r["_saturs"])
parbaude("Atom: feedparser bez kļūdām (bozo=0)", f.bozo == 0 and f.version == "atom10")
ids = [e.id for e in f.entries]
print("      ieraksti:", [e.title for e in f.entries])
parbaude("Atom: brīdinājums Ogrei ir, Kurzemes nav", "tag:map.repo.lv,2026:bridinajums:28210" in ids and not any("28999" in i for i in ids))
parbaude("Atom: rītdienas prognoze (brāzmas 17 m/s)", f"tag:map.repo.lv,2026:prognoze:{OGRE}:{rit}" in ids)
parbaude("Atom: upe Ogre (+25 cm) ir, Venta (cits novads) un Stariņi (+2) nav",
         any(":udens:HD073401:" in i for i in ids) and not any("HD073999" in i or "HD073418" in i for i in ids))
parbaude("Atom: negadījums ir, remontdarbi nav", "tag:map.repo.lv,2026:celi:NG1" in ids and not any("RM1" in i for i in ids))
parbaude("Atom: zibens 2 izlādes novadā", any(":zibens:" in i for i in ids) and any("2 izlādes" in e.title for e in f.entries))
parbaude("Atom: avots un licence katrā ierakstā", all("Avots:" in e.summary and ("CC0" in e.summary or "CC BY" in e.summary) for e in f.entries))
parbaude("Atom: feed <updated> = jaunākais ieraksts", f.feed.updated == max(e.updated for e in f.entries))
k._kesa.clear()
f2 = feedparser.parse(k.plusma({"regions": ["0040000"]})["_saturs"])  # ATVK
parbaude("Atom: ATVK 0040000 = tas pats novads, tie paši stabilie id", f2.feed.id == f.feed.id and [e.id for e in f2.entries] == ids)
fl = feedparser.parse(k.plusma({})["_saturs"])
parbaude("Atom: visa Latvija — abi brīdinājumi", sum(":bridinajums:" in e.id for e in fl.entries) == 2)
try:
    k.plusma({"regions": ["nav;kods"]})
    parbaude("nederīgs regions → 400", False)
except k.Kluda as e:
    parbaude("nederīgs regions → 400", e.statuss == 400)

# iCalendar
ics = k.kalendars({"regions": [OGRE]})["_saturs"]
cal = icalendar.Calendar.from_ical(ics)
ev = [c for c in cal.walk("VEVENT")]
parbaude("ICS: icalendar nolasa, 1 notikums (tikai brīdinājumi)", len(ev) == 1)
s, e = ev[0].decoded("DTSTART"), ev[0].decoded("DTEND")
parbaude("ICS: laiki UTC, 14:00 Rīgā = 11:00 UTC", s.tzinfo is not None and s.utcoffset() == timedelta(0) and s.hour == 11 and e > s)
parbaude("ICS: stabils UID", str(ev[0]["UID"]) == f"28210-{OGRE}@map.repo.lv")
parbaude("ICS: rindas ≤ 75 okteti, CRLF", all(len(x.encode()) <= 75 for x in ics.split("\r\n")) and "\r\n" in ics)
parbaude("ICS: apraksts ar avotu un 112", "Avots" in str(ev[0]["DESCRIPTION"]) and "112" in str(ev[0]["DESCRIPTION"]))

# HTTP: satura tips, CORS
srv = k.Serveris(("127.0.0.1", 8971), k.Apstradatajs)
threading.Thread(target=srv.serve_forever, daemon=True).start()
r = urllib.request.urlopen(f"http://127.0.0.1:8971/api/plusma.xml?regions={OGRE}", timeout=10)
parbaude("HTTP: Atom satura tips, CORS, kešs 300 s", r.headers["Content-Type"].startswith("application/atom+xml")
         and r.headers["Access-Control-Allow-Origin"] == "*" and "max-age=300" in r.headers["Cache-Control"])
r = urllib.request.urlopen(f"http://127.0.0.1:8971/api/kalendars.ics?regions={OGRE}", timeout=10)
parbaude("HTTP: text/calendar", r.headers["Content-Type"].startswith("text/calendar"))
srv.shutdown()

print(f"\n{'VISI TESTI IZIET' if not kludas else f'{kludas} KĻŪDAS'}")
sys.exit(1 if kludas else 0)
