"""Lokāls slodzes tests bez ārējiem avotiem: karte_api.py ar viltotu datubāzi un lēniem viltotiem avotiem, lai redzētu
slēdzenes, keša uzvedību un savienojumu rindu, netraucējot map.repo.lv un LVĢMC/FMI/NAP.

  uv run --no-project --python 3.12 --with httpx --with "psycopg[binary]" src/testi/slodze_lokali.py [karte_api.py ceļš]

Viltojumi: DB vaicājums 20–400 ms (pilns slāņu saraksts 400 ms); brīdinājumi un ūdens līmenis — avots atbild 2 s;
plūdu WMS — vienam punktam 30 s (pārbauda 25 s robežu). Fona pavediens ik 5 s "novecina" kešu (kā beidzies derīgums),
lai redzētu, vai pēc derīguma beigām visi pieprasījumi gaida vienu lejupielādi. Skaita, cik reižu tiešām gāja uz "avotu".
"""

import asyncio
import importlib.util
import os
import sys
import threading
import time
from collections import defaultdict

import httpx

CELS = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..", "karte", "api", "karte_api.py")
PORTS = int(os.environ.get("PORTS", "8941"))
os.environ.setdefault("MAP_DB_DSN", "postgresql://viltots/x")

spec = importlib.util.spec_from_file_location("karte_api_tests", CELS)
k = importlib.util.module_from_spec(spec)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "karte", "db"))  # udens_limenis
spec.loader.exec_module(k)

AVOTS = defaultdict(int)  # cik reižu "avots" izsaukts
VIENLAICIGI = {"db": 0, "db_max": 0}
slots = threading.Lock()


class Kursors:
    def __init__(self):
        self.sql = ""

    def execute(self, sql, params=None):
        if sql.startswith("set "):
            return
        self.sql = sql
        with slots:
            VIENLAICIGI["db"] += 1
            VIENLAICIGI["db_max"] = max(VIENLAICIGI["db_max"], VIENLAICIGI["db"])
        try:
            AVOTS["db"] += 1
            time.sleep(0.4 if "limit %(limit)s" in sql and (params or {}).get("limit", 0) > 1000 else
                       0.1 if "adreses order by" in sql else 0.02)
        finally:
            with slots:
                VIENLAICIGI["db"] -= 1

    def fetchone(self):
        if "from regioni where tips" in self.sql:
            return ("100016688",)
        if "select true" in self.sql:
            return (True,)
        if "FeatureCollection" in self.sql:
            return ({"type": "FeatureCollection", "features": []},)
        return ([],)

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class Savienojums:
    def cursor(self):
        return Kursors()

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


k.psycopg.connect = lambda *a, **kw: Savienojums()


def lens(nos, sek, vertiba):
    def f(*a, **kw):
        AVOTS[nos] += 1
        time.sleep(sek)
        return vertiba
    return f


k._bridinajumi_dati = lens("bridinajumi", 2, [])
k.udens_limenis.stacijas = lens("udens", 2, [])
if hasattr(k, "_hidro_prognozes"):
    k._hidro_prognozes = lens("hidro_prognoze", 1, {})  # nevis data.gov.lv


def pludu_serviss(veids, cels, slani, lat, lon):
    AVOTS["pludi_wms"] += 1
    time.sleep(30 if abs(lat - 56.95) < 0.01 else 1.5)  # Rīgā lēns (pārbauda 25 s robežu)
    return None


k._pludu_serviss = pludu_serviss
k._statuss_cikls = lambda: None


def novecinat():
    while True:
        time.sleep(5)
        with k._kesas_slots:
            for a, (t, v) in list(k._kesa.items()):
                k._kesa[a] = (t - 100000, v)


serveris_kl = getattr(k, "Serveris", k.ThreadingHTTPServer)
srv = serveris_kl(("127.0.0.1", PORTS), k.Apstradatajs)
threading.Thread(target=srv.serve_forever, daemon=True).start()
threading.Thread(target=novecinat, daemon=True).start()

PUNKTI = [(56.8166, 24.6046), (56.9677, 23.7704), (56.9496, 24.1052)]
SLANI = "patvertne,evakuacijas_punkts,izmitinasana,slimnica,aptieka"


def celi(i):
    lat, lon = PUNKTI[i % 3]
    ll = f"lat={lat}&lon={lon}"
    return [("kategorijas", "/api/kategorijas"), ("objekti (visi)", f"/api/objekti?kategorijas={SLANI}&limit=20000"),
            ("objekti (kartīte)", f"/api/objekti?kategorijas=patvertne&{ll}&limit=5"), ("bridinajumi", f"/api/bridinajumi?{ll}"),
            ("udens", f"/api/udens?{ll}&limit=3"), ("pludi", f"/api/pludi?{ll}"), ("adreses/tuvaka", f"/api/adreses/tuvaka?{ll}"),
            ("pasvaldiba", f"/api/pasvaldiba?{ll}")][i % 8]


async def main(klienti=50, ilgums=40):
    rez = defaultdict(list)
    beigas = time.monotonic() + ilgums
    async with httpx.AsyncClient(base_url=f"http://127.0.0.1:{PORTS}", limits=httpx.Limits(max_connections=klienti)) as c:
        async def klients(n):
            i = n
            while time.monotonic() < beigas:
                nos, cels = celi(i)
                i += 7
                t = time.monotonic()
                try:
                    r = await c.get(cels, timeout=40)
                    kods = r.status_code
                except httpx.HTTPError as e:
                    kods = type(e).__name__
                rez[nos].append(((time.monotonic() - t) * 1000, kods))
                await asyncio.sleep(0.05)
        await asyncio.gather(*(klients(n) for n in range(klienti)))
    visi = sorted(m for v in rez.values() for m, _ in v)
    p = lambda v, q: v[min(len(v) - 1, int(q / 100 * (len(v) - 1)))]  # noqa: E731
    print(f"\n{os.path.basename(CELS)}: {klienti} klienti, {ilgums} s, {len(visi)} pieprasījumi, p50 {p(visi, 50):.0f} ms, "
          f"p95 {p(visi, 95):.0f} ms, p99 {p(visi, 99):.0f} ms")
    for nos, v in sorted(rez.items()):
        ms = sorted(m for m, _ in v)
        kodi = defaultdict(int)
        for _, kd in v:
            kodi[kd] += 1
        print(f"  {nos:18} n={len(v):5}  p50 {p(ms, 50):6.0f}  p95 {p(ms, 95):6.0f}  max {ms[-1]:6.0f}  {dict(kodi)}")
    print("  avotu izsaukumi:", dict(AVOTS), "| DB vienlaicīgi max:", VIENLAICIGI["db_max"])
    if hasattr(k, "_statistika"):
        print("  _statistika.kesa:", {a: b for a, b in k._statistika["kesa"].items()})


asyncio.run(main())
