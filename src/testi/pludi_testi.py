"""/api/pludi atbilžu secības testi bez PostGIS un bez LVĢMC (viltota datubāze un WMS):
PostGIS kopija → LVĢMC WMS + kešs pludi_kesa (7 dienas, novecojis, ja LVĢMC neatbild) → {"zinams": false}.

  uv run --no-project --python 3.12 --with "psycopg[binary]" src/testi/pludi_testi.py
  uv run --no-project --python 3.12 --with "psycopg[binary]" src/testi/pludi_testi.py --serveris 8931 --rezims wms
      īsts karte_api HTTP serveris ar viltotu DB/WMS (curl, Playwright); rezims: postgis | wms | kesa | novecojis | nezinams
"""

import argparse
import gzip
import json
import os
import sys
import tempfile
import threading
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "karte", "api"))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "karte", "db"))
os.environ.setdefault("MAP_DB_DSN", "postgresql://viltots/x")
os.environ.pop("MAP_DB_OWNER_DSN", None)
import psycopg  # noqa: E402

import karte_api as k  # noqa: E402
import pludu_zonas  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

kludas = 0


def parbaude(nos, nosacijums, detalas=""):
    global kludas
    print(("OK   " if nosacijums else "KĻŪDA ") + nos + ("" if nosacijums else f"  ({detalas})"))
    kludas += not nosacijums


# ---------- viltota datubāze un WMS ----------

class Vide:
    def __init__(self):
        self.kopija = []          # [(veids, varbutiba)] — ko PostGIS atrod punktā; None: tabulas nav
        self.kopijas_varb = []    # distinct varbutiba
        self.postgis_kluda = False
        self.kesa = {}            # atslēga → (epoch, atbilde)
        self.wms = "ok"           # ok | kluda | lens
        self.wms_zona = {"pavasara pali": "1"}  # veids → slāņa nr
        self.wms_pieprasijumi = 0

    def vaicat(self, sql, params=(), timeout="10s"):
        if "from pludu_zonas" in sql and "json_agg(distinct" in sql:
            if self.kopija is None:
                raise psycopg.errors.UndefinedTable("relation \"pludu_zonas\" does not exist")
            return self.kopijas_varb or None
        if "from pludu_zonas" in sql:
            if self.postgis_kluda:
                raise psycopg.OperationalError("statement timeout")
            return [{"veids": v, "varbutiba_proc": float(p)} for v, p in self.kopija]
        if "from pludi_kesa" in sql:
            ier = self.kesa.get(params[0])
            return {"atbilde": ier[1], "laiks": ier[0]} if ier else None
        raise AssertionError("negaidīts SQL: " + sql[:80])

    def lejupieladet(self, url, timeout=20):
        self.wms_pieprasijumi += 1
        if self.wms == "kluda":
            raise TimeoutError("timed out")
        if self.wms == "lens":
            time.sleep(3)
            raise TimeoutError("timed out")
        for veids, cels, slani in k.PLUDU_SERVISI:
            if cels in url:
                nr = self.wms_zona.get(veids)
                return json.dumps({"features": [{"layerName": nr}] if nr else []}).encode()
        raise AssertionError(url)


class Savienojums:  # psycopg.connect(DSN) → pludi_kesa ieraksts
    def __init__(self, vide):
        self.vide = vide

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def cursor(self):
        return self

    def execute(self, sql, params=()):
        if "insert into pludi_kesa" in sql:
            self.vide.kesa[params[0]] = (time.time(), json.loads(params[1]))


def uzstadit(vide):
    k.vaicat = vide.vaicat
    k._lejupieladet = vide.lejupieladet
    k.psycopg.connect = lambda *a, **kw: Savienojums(vide)
    with k._kesas_slots:
        k._kesa.clear()
        k._pludu_darbi.clear()
    k._pludu_kluda[0] = 0.0
    k._pludu_kopija.update(ir=None, parbaudits=0.0, varbutibas=[])


def pludi(lat=56.816, lon=24.614, **cits):
    return k.pludi({"lat": [str(lat)], "lon": [str(lon)], **{a: [b] for a, b in cits.items()}})


def testi():
    k.PLUDU_MAX_GAIDIT = 1
    k.PLUDU_KLUDAS_PAUZE = 60

    # a) PostGIS kopija
    v = Vide()
    v.kopija, v.kopijas_varb = [("pavasara pali", "1"), ("ledus sastrēgumi", "10")], [10.0, 1.0]
    uzstadit(v)
    r = pludi()
    parbaude("PostGIS: zona, metode, avots", r["zinams"] and r["zona"] and r["metode"] == "PostGIS kopija"
             and r["avots"] == "lvgmc-pludi-faili" and "_statuss" not in r, r)
    parbaude("PostGIS: varbūtības veselos skaitļos, kopijas kartes [10, 1]",
             r["veidi"][0]["varbutiba_proc"] == 1 and isinstance(r["veidi"][0]["varbutiba_proc"], int)
             and r["varbutibas"] == [10, 1], r)
    parbaude("PostGIS: WMS netiek jautāts", v.wms_pieprasijumi == 0)
    v.kopija = []
    r = pludi()
    parbaude("PostGIS: ārpus zonas → zona false", r["zinams"] and r["zona"] is False and r["veidi"] == [], r)
    v.postgis_kluda, v.wms_zona = True, {}
    r = pludi()
    parbaude("PostGIS kļūda → WMS", r["metode"] == "LVĢMC WMS" and r["zona"] is False and v.wms_pieprasijumi == 3, r)

    # ?wms=1 izlaiž kopiju
    v = Vide()
    v.kopija, v.kopijas_varb = [("pavasara pali", "1")], [10.0, 1.0]
    uzstadit(v)
    r = pludi(lat=56.9, lon=24.1, wms="1")
    parbaude("?wms=1: WMS, nevis kopija", r["metode"] == "LVĢMC WMS", r)

    # b) WMS + kešs
    v = Vide()
    v.kopija = None  # tabulas nav
    uzstadit(v)
    r = pludi()
    parbaude("WMS: zona pavasara pali 1 %", r["metode"] == "LVĢMC WMS" and r["zona"]
             and r["veidi"] == [{"veids": "pavasara pali", "varbutiba_proc": 1}] and r["varbutibas"] == [10, 1, 0.5], r)
    parbaude("WMS: atbilde saglabāta pludi_kesa (4 zīmes)", "56.8160,24.6140" in v.kesa, list(v.kesa))
    n = v.wms_pieprasijumi
    r = pludi(lat=56.81603, lon=24.61398)  # tā pati vieta 4 zīmēs
    parbaude("kešs atmiņā: metode 'kešs no HH:MM', bez WMS", r["metode"].startswith("kešs no ") and len(r["metode"]) == 13
             and v.wms_pieprasijumi == n and not r.get("novecojis"), r)
    with k._kesas_slots:
        k._kesa.clear()  # API pārstartēts: atmiņa tukša, DB kešs paliek
    v.wms = "kluda"
    r = pludi()
    parbaude("kešs no DB pēc pārstartēšanas (LVĢMC neatbild — nav vajadzīgs)", r["zinams"] and r["zona"]
             and r["metode"].startswith("kešs no ") and v.wms_pieprasijumi == n, r)

    # novecojis kešs + LVĢMC neatbild
    with k._kesas_slots:
        k._kesa.clear()
    laiks, atb = v.kesa["56.8160,24.6140"]
    v.kesa["56.8160,24.6140"] = (laiks - 8 * 86400, atb)
    r = pludi()
    parbaude("> 7 dienas + LVĢMC neatbild → pēdējais zināmais, novecojis, no-store",
             r["zinams"] and r["zona"] and r.get("novecojis") and r["iemesls"] == k.PLUDU_NEATBILD
             and r.get("_statuss") == 200 and "." in r["metode"], r)
    t0 = time.monotonic()
    r = pludi()
    parbaude("pēc LVĢMC kļūmes negaida (kešs uzreiz)", time.monotonic() - t0 < 0.5 and r.get("novecojis"), r)

    # c) nekas nav zināms
    t0 = time.monotonic()
    r = pludi(lat=57.1, lon=25.1)
    parbaude("nav keša + LVĢMC neatbild → 200 zinams false (uzreiz pēc nesenas kļūmes)",
             r["zinams"] is False and r.get("_statuss") == 200 and r["iemesls"] == k.PLUDU_NEATBILD
             and r.get("ielade") is True and time.monotonic() - t0 < 0.5, r)
    k._pludu_kluda[0] = 0.0
    r = pludi(lat=57.2, lon=25.2)
    parbaude("nav keša + LVĢMC kļūda (bez iepriekšējas kļūmes) → zinams false", r["zinams"] is False, r)

    # 202 tikai pirmajā gaidīšanā
    v = Vide()
    v.kopija, v.wms = None, "lens"
    uzstadit(v)
    t0 = time.monotonic()
    r = pludi(lat=56.5, lon=25.8)
    parbaude("lēns LVĢMC: 202 'ielādējas' pēc ≤ PLUDU_MAX_GAIDIT s", r.get("_statuss") == 202 and r["ielade"]
             and time.monotonic() - t0 < 2, r)
    time.sleep(3)
    r = pludi(lat=56.5, lon=25.8)
    parbaude("pēc tam (LVĢMC neatbildēja) → zinams false, nevis vēlreiz 202", r["zinams"] is False and r["_statuss"] == 200, r)

    # nepilnīga atbilde (daļa servisu neatbild) — kešā tikai 10 min
    v = Vide()
    v.kopija = None
    uzstadit(v)
    orig = v.lejupieladet

    def dala(url, timeout=20):
        if "556_" in url:
            raise TimeoutError("x")
        return orig(url, timeout)
    k._lejupieladet = dala
    r = pludi(lat=56.7, lon=24.0)
    parbaude("nepilnīga atbilde: nepilnigi true", r["nepilnigi"] and r["metode"] == "LVĢMC WMS", r)
    atsl = "56.7000,24.0000"
    v.kesa[atsl] = (time.time() - 700, v.kesa[atsl][1])
    with k._kesas_slots:
        k._kesa.clear()
    n = v.wms_pieprasijumi
    pludi(lat=56.7, lon=24.0)
    parbaude("nepilnīga atbilde pēc 10 min → jautā LVĢMC vēlreiz", v.wms_pieprasijumi > n)

    # pārslodze: vairāk par PLUDU_MAX_DARBI vienlaicīgām pārbaudēm → uzreiz "nav zināms", nevis rinda
    v = Vide()
    v.kopija, v.wms = None, "lens"
    uzstadit(v)
    k.PLUDU_MAX_GAIDIT = 0.05
    for i in range(k.PLUDU_MAX_DARBI):
        pludi(lat=56.0 + i / 100, lon=24.0)
    t0 = time.monotonic()
    r = pludi(lat=57.5, lon=26.0)
    parbaude("pārslodze → zinams false uzreiz", r["zinams"] is False and time.monotonic() - t0 < 0.5, r)
    time.sleep(3.5)
    k.PLUDU_MAX_GAIDIT = 1

    # pludu_zonas.py: straumēta GeoJSON lasīšana
    with tempfile.TemporaryDirectory() as d:
        f = os.path.join(d, "z.geojson.gz")
        with gzip.open(f, "wt", encoding="utf-8") as g:
            g.write('{"type": "FeatureCollection", "licence": "CC BY-SA 4.0", "features": [\n')
            g.write('{"type":"Feature","properties":{"veids":"pavasara pali","varbutiba":"1"},"geometry":'
                    '{"type":"MultiPolygon","coordinates":[[[[24,56],[24.1,56],[24.1,56.1],[24,56]]]]}},\n')
            g.write('{"type":"Feature","properties":{"veids":"jūras vējuzplūdi","varbutiba":"10"},"geometry":'
                    '{"type":"Polygon","coordinates":[[[21,57],[21.1,57],[21.1,57.1],[21,57]]]}}\n]}\n')
        o = list(pludu_zonas.lasit_objektus(f))
        parbaude("pludu_zonas.lasit_objektus: 2 objekti, īpašības", len(o) == 2 and o[1]["properties"]["veids"] == "jūras vējuzplūdi", o)


REZIMI = ("postgis", "wms", "kesa", "novecojis", "nezinams")


def serveris(ports, rezims):
    """Īsts karte_api HTTP serveris ar viltotu DB un WMS: curl / Playwright katrā režīmā."""
    v = Vide()
    if rezims == "postgis":
        v.kopija, v.kopijas_varb = [("pavasara pali", "1"), ("pavasara pali", "10")], [10.0, 1.0]
    else:
        v.kopija = None
    if rezims in ("kesa", "novecojis"):
        vecums = 8 * 86400 if rezims == "novecojis" else 3600
        for atslega in ("56.8160,24.6140", "56.8149,24.6024"):  # api.html piemērs; Brīvības iela 12, Ogre (VZD)
            v.kesa[atslega] = (time.time() - vecums, {"avots": "lvgmc-pludi", "zona": True,
                               "veidi": [{"veids": "pavasara pali", "varbutiba_proc": 10}], "nepilnigi": False})
    if rezims in ("novecojis", "nezinams"):
        v.wms = "kluda"
    uzstadit(v)
    k.PLUDU_MAX_GAIDIT = 6
    srv = k.ThreadingHTTPServer(("127.0.0.1", ports), k.Apstradatajs)
    print(f"karte_api (viltots, rezims={rezims}) http://127.0.0.1:{ports}/api/pludi", flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--serveris", type=int)
    p.add_argument("--rezims", choices=REZIMI, default="wms")
    a = p.parse_args()
    if a.serveris:
        serveris(a.serveris, a.rezims)
    else:
        testi()
        print(f"\n{'Visi testi izdevās' if not kludas else f'{kludas} kļūdas'}")
        threading.Timer(0.1, lambda: os._exit(1 if kludas else 0)).start()  # fona WMS pavedieni negaida
