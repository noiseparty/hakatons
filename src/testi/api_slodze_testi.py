"""karte_api.py slodzes labojumu testi (bez datubāzes un ārējiem avotiem).

  uv run --no-project --python 3.12 --with "psycopg[binary]" src/testi/api_slodze_testi.py
"""

import json
import os
import sys
import threading
import time
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "karte", "api"))
os.environ.setdefault("MAP_DB_DSN", "postgresql://viltots/x")
import karte_api as k  # noqa: E402

kludas = 0


def parbaude(nos, nosacijums):
    global kludas
    print(("ok    " if nosacijums else "KĻŪDA ") + nos)
    kludas += 0 if nosacijums else 1


# 1) _kesots: svaiga vērtība no kešas; novecojusi — uzreiz vecā, atjaunošana fonā (vienreiz); kļūda — paliek vecā
izsaukumi = []


def avots():
    izsaukumi.append(time.time())
    time.sleep(0.5)
    return len(izsaukumi)


v1 = k._kesots("tests", 60, avots)
parbaude("pirmais izsaukums iet uz avotu un gaida", v1 == 1 and len(izsaukumi) == 1)
parbaude("svaiga vērtība no kešas", k._kesots("tests", 60, avots) == 1 and len(izsaukumi) == 1)
with k._kesas_slots:
    k._kesa["tests"] = (time.time() - 120, 1)  # derīgums beidzies
t = time.time()
rez = [k._kesots("tests", 60, avots) for _ in range(5)]
parbaude("novecojusi: atgriež veco uzreiz (< 0,1 s), negaida avotu", rez == [1] * 5 and time.time() - t < 0.1)
time.sleep(0.8)
parbaude("novecojusi: fonā atjaunots tieši vienreiz", len(izsaukumi) == 2 and k._kesots("tests", 60, avots) == 2)


def lauzts():
    raise OSError("avots nav pieejams")


with k._kesas_slots:
    k._kesa["tests"] = (time.time() - 120, 2)
parbaude("kļūda fonā: paliek vecā vērtība", k._kesots("tests", 60, lauzts) == 2)
time.sleep(0.2)
parbaude("kļūda fonā: nākamais mēģinājums pēc ~1 min (vērtība skaitās svaiga)", k._kesots("tests", 60, avots) == 2)
try:
    k._kesots("cits", 60, lauzts)
    parbaude("bez vērtības un ar kļūdu: Kluda 503", False)
except k.Kluda as e:
    parbaude("bez vērtības un ar kļūdu: Kluda 503", e.statuss == 503)

# 2) _LRU: derīguma laiks un izmešana
lru = k._LRU(2, 0.3)
n = []
lru.iegut("a", lambda: n.append(1) or "A")
lru.iegut("a", lambda: n.append(1) or "A")
parbaude("LRU: otrais izsaukums no atmiņas", len(n) == 1)
lru.iegut("b", lambda: "B")
lru.iegut("c", lambda: "C")
parbaude("LRU: vecākais izmests, kad > 2", "a" not in lru.dati and len(lru.dati) == 2)
time.sleep(0.35)
lru.iegut("c", lambda: n.append(1) or "C2")
parbaude("LRU: pēc derīguma beigām rēķina no jauna", lru.dati["c"][1] == "C2")

# 3) pludi: lēns WMS → 202 pēc PLUDU_MAX_GAIDIT, rezultāts vēlāk kešā
k.PLUDU_MAX_GAIDIT = 1
k._pludu_serviss = lambda veids, cels, slani, lat, lon: time.sleep(2) or None
t = time.time()
r = k.pludi({"lat": ["56.9"], "lon": ["24.1"]})
parbaude("pludi: 202 'ielādējas' ~1 s, nevis 2+ s", r.get("_statuss") == 202 and r.get("ielade") and time.time() - t < 1.5)
time.sleep(1.5)
r = k.pludi({"lat": ["56.9"], "lon": ["24.1"]})
parbaude("pludi: nākamais pieprasījums — gatavs rezultāts no kešas", r.get("zona") is False and "_statuss" not in r)

# 4) DB: vienlaicīgu vaicājumu robeža → 503, nevis bezgalīga gaidīšana
k._db_sloti = threading.BoundedSemaphore(1)
k._db_sloti.acquire()
t = time.time()
k.psycopg.connect = lambda *a, **kw: (_ for _ in ()).throw(AssertionError("nedrīkst pieslēgties"))
orig = k._db_sloti.acquire
k._db_sloti.acquire = lambda timeout=None: orig(timeout=0.2)
try:
    k.vaicat("select 1")
    parbaude("DB pārslodze: 503", False)
except k.Kluda as e:
    parbaude("DB pārslodze: 503", e.statuss == 503)

# 5) serveris: gaidīšanas rinda, neparedzēta kļūda → JSON 500
parbaude("serveris: request_queue_size ≥ 128", k.Serveris.request_queue_size >= 128 and k.Serveris.daemon_threads)
k.MARSRUTI.insert(0, (k.re.compile(r"^/api/testa-kluda$"), lambda q: 1 / 0, 0))
srv = k.Serveris(("127.0.0.1", 8951), k.Apstradatajs)
threading.Thread(target=srv.serve_forever, daemon=True).start()
try:
    urllib.request.urlopen("http://127.0.0.1:8951/api/testa-kluda", timeout=5)
    parbaude("neparedzēta kļūda: 500 JSON", False)
except urllib.error.HTTPError as e:
    parbaude("neparedzēta kļūda: 500 JSON", e.code == 500 and "kluda" in json.loads(e.read()))
k.MARSRUTI.insert(0, (k.re.compile(r"^/api/testa-202$"), lambda q: {"_statuss": 202, "ielade": True}, 0))
r = urllib.request.urlopen("http://127.0.0.1:8951/api/testa-202", timeout=5)
parbaude("_statuss: 202 un bez _statuss laukā, no-store", r.status == 202 and json.loads(r.read()) == {"ielade": True}
         and r.headers["Cache-Control"] == "no-store")
srv.shutdown()

print(f"\n{'VISI TESTI IZIET' if not kludas else f'{kludas} KĻŪDAS'}")
sys.exit(1 if kludas else 0)
