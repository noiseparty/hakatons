"""/api/pludi/flize/<paka>/<z>/<x>/<y>.png testi: XYZ → bbox, diska kešs, rinda, neveiksmju kešs, ETag/304.
Bez datubāzes; LVĢMC WMS aizstāts ar viltotu (ar --tiessaiste — arī viena īsta Ogres flīze no geo-dpps.viss.gov.lv).

  uv run --no-project --python 3.12 --with "psycopg[binary]" src/testi/pludu_flizes_testi.py [--tiessaiste]
"""

import math
import os
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
DATI = tempfile.mkdtemp(prefix="flizes-testi-")
os.environ["HAKATONS_DATI"] = DATI
os.environ.setdefault("MAP_DB_DSN", "postgresql://viltots/x")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "karte", "api"))
import karte_api as k  # noqa: E402

kludas = 0


def parbaude(nos, nosacijums, detalas=""):
    global kludas
    print(("ok    " if nosacijums else "KĻŪDA ") + nos + (f"  ({detalas})" if detalas and not nosacijums else ""))
    kludas += 0 if nosacijums else 1


def tuvu(a, b, tol=1e-6):
    return all(abs(x - y) <= tol * max(1.0, abs(y)) for x, y in zip(a, b))


# ---------- 1. XYZ → bbox (zināmas vērtības) ----------
O = 20037508.342789244
parbaude("z0 = visa pasaule (3857)", tuvu(k.xyz_bbox_3857(0, 0, 0), (-O, -O, O, O)))
parbaude("z1 0/0 = ziemeļrietumu ceturksnis (3857)", tuvu(k.xyz_bbox_3857(1, 0, 0), (-O, 0, 0, O)))
parbaude("z2 1/1 (3857)", tuvu(k.xyz_bbox_3857(2, 1, 1), (-O / 2, 0, 0, O / 2)))
parbaude("z1 1/1 (4326) = dienvidaustrumi līdz -85.0511°",
         tuvu(k.xyz_bbox_4326(1, 1, 1), (-85.0511287798066, 0, 0, 180)), k.xyz_bbox_4326(1, 1, 1))
# Ogre (56.8166, 24.6072), z13: x = floor((lon + 180) / 360 · 2^13) = 4655, y = 2517 (OSM slippy map formula)
lat, lon, z = 56.8166, 24.6072, 13
x = int((lon + 180) / 360 * 2 ** z)
y = int((1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * 2 ** z)
parbaude("Ogre z13 → flīze 4655/2517", (x, y) == (4655, 2517), (x, y))
d, r, zi, a = k.xyz_bbox_4326(z, x, y)
parbaude("Ogre ir savas z13 flīzes robežās", d <= lat <= zi and r <= lon <= a, (d, r, zi, a))
parbaude("z13 flīzes platums 360/8192°", abs((a - r) - 360 / 8192) < 1e-12)
minx, miny, maxx, maxy = k.xyz_bbox_3857(z, x, y)
uz_4326 = (math.degrees(math.atan(math.sinh(miny / 6378137.0))), math.degrees(minx / 6378137.0),
           math.degrees(math.atan(math.sinh(maxy / 6378137.0))), math.degrees(maxx / 6378137.0))
parbaude("3857 un 4326 bbox sakrīt (inversā Merkatora projekcija)", tuvu(uz_4326, (d, r, zi, a), 1e-9), (uz_4326, (d, r, zi, a)))
parbaude("z13 flīzes mala 3857: 4891.97 m", abs((maxx - minx) - 2 * O / 8192) < 1e-6 and abs(maxx - minx - 4891.97) < 0.01)

# ---------- 2. Kešs un rinda ar viltotu WMS ----------
PNG = k.TUKSA_FLIZE[:-12] + b"viltots" + k.TUKSA_FLIZE[-12:]  # sākas ar PNG parakstu
izsaukumi = []
rezims = {"kluda": False, "aizture": 0.0}


def viltots(url, timeout=20):
    izsaukumi.append(url)
    if rezims["aizture"]:
        time.sleep(rezims["aizture"])
    if rezims["kluda"]:
        raise urllib.error.HTTPError(url, 504, "Gateway Time-out", None, None)
    return PNG


ISTS = k._lejupieladet
k._lejupieladet = viltots
PALI = ("pali", "13", "4655", "2517")

s, dati, veids, kes = k.pludu_flize(*PALI)
parbaude("pirmā reize: no WMS (jauna, 200, max-age 86400)", (s, veids, kes) == (200, "jauna", 86400) and dati == PNG, (s, veids))
parbaude("WMS pieprasījums: GetMap EPSG:3857, 512 px, slānis 1, caurspīdīgs",
         all(p in izsaukumi[-1] for p in ("request=GetMap", "crs=EPSG:3857", "width=512", "height=512", "layers=1",
                                          "transparent=TRUE", "3._cikla_L_557_7iFPTq")), izsaukumi[-1])
cels = os.path.join(DATI, "flizes", "pali", "13", "4655", "2517.png")
parbaude("flīze ierakstīta diskā zem $HAKATONS_DATI/flizes", os.path.exists(cels), cels)
n = len(izsaukumi)
s, dati, veids, _ = k.pludu_flize(*PALI)
parbaude("otrā reize: no diska (kesa), WMS netiek prasīts", veids == "kesa" and len(izsaukumi) == n and dati == PNG)

s, dati, veids, kes = k.pludu_flize("ledus", "13", "4655", "2517")  # Ogre ir ārpus ledus sastrēgumu pārklājuma
parbaude("ārpus paketes pārklājuma: 1×1 bez WMS (tukss)", (veids, dati, kes) == ("tukss", k.TUKSA_FLIZE, 86400) and len(izsaukumi) == n)
s, dati, veids, kes = k.pludu_flize("pali10", "13", "4655", "2517")
parbaude("10 % paka pali10: slāņi 2,3 no pavasara palu WMS", veids == "jauna" and "layers=2,3&" in izsaukumi[-1]
         and "3._cikla_L_557" in izsaukumi[-1], izsaukumi[-1])
k.pludu_flize("juras10", "13", "4636", "2512")
parbaude("10 % paka juras10: slānis 2 no jūras vējuzplūdu WMS", "layers=2&" in izsaukumi[-1] and "3._cikla_L_556" in izsaukumi[-1], izsaukumi[-1])

for slikts in [("nav", "13", "1", "1"), ("pali", "3", "1", "1"), ("pali", "13", "8192", "1")]:
    try:
        k.pludu_flize(*slikts)
        parbaude(f"nederīga flīze {slikts} → 404", False)
    except k.Kluda as e:
        parbaude(f"nederīga flīze {'/'.join(slikts)} → 404", e.statuss == 404)

rezims["kluda"] = True
JURAS = ("juras", "13", "4636", "2512")  # Jūrmala
s, dati, veids, kes = k.pludu_flize(*JURAS)
parbaude("WMS 504: 502 + 1×1, no-store (kluda)", (s, veids, kes, dati) == (502, "kluda", 0, k.TUKSA_FLIZE), (s, veids))
n = len(izsaukumi)
s, _, veids, _ = k.pludu_flize(*JURAS)
parbaude("neveiksmju kešs: 60 s to pašu flīzi WMS neprasa", veids == "kluda" and len(izsaukumi) == n)

# novecojusi flīze: WMS neatbild → atdodam veco
vecs = time.time() - k.FLIZU_TTL - 10
os.utime(cels, (vecs, vecs))
s, dati, veids, kes = k.pludu_flize(*PALI)
parbaude("novecojusi + WMS kļūda → veca flīze (200, 1 h)", (s, veids, kes, dati) == (200, "veca", 3600, PNG), (s, veids))
rezims["kluda"] = False
k._flizu_neveiksmes.clear()
s, dati, veids, _ = k.pludu_flize(*PALI)
parbaude("novecojusi + WMS atbild → jauna", veids == "jauna")

# ne-PNG (WMS ServiceException) = kļūda
k._lejupieladet = lambda url, timeout=20: b"<?xml version='1.0'?><ServiceExceptionReport/>"
s, _, veids, _ = k.pludu_flize("pali", "12", "2327", "1258")
parbaude("WMS atbild ar XML, nevis PNG → kluda", (s, veids) == (502, "kluda"))
k._lejupieladet = viltots

# rinda: visi 4 sloti aizņemti → pēc FLIZU_GAIDIT_RINDA s 1×1 ar no-store
k.FLIZU_GAIDIT_RINDA = 0.3
for _ in range(4):
    k._flizu_sloti.acquire()
t0 = time.time()
s, dati, veids, kes = k.pludu_flize("pali", "12", "2328", "1258")
parbaude("4 pieprasījumi jau iet → aiznemts (200, 1×1, no-store) pēc ≤ rindas laika",
         (s, veids, kes, dati) == (200, "aiznemts", 0, k.TUKSA_FLIZE) and time.time() - t0 < 1.5, (veids, time.time() - t0))
for _ in range(4):
    k._flizu_sloti.release()
k.FLIZU_GAIDIT_RINDA = 5

# viena flīze vienlaikus no 5 pieprasījumiem → WMS tikai vienreiz
rezims["aizture"] = 0.5
n = len(izsaukumi)
rez = []
pavedieni = [threading.Thread(target=lambda: rez.append(k.pludu_flize("pali", "12", "2329", "1258"))) for _ in range(5)]
for p in pavedieni:
    p.start()
for p in pavedieni:
    p.join()
rezims["aizture"] = 0.0
parbaude("5 vienlaicīgi pieprasījumi vienai flīzei → 1 WMS pieprasījums, visi saņem PNG",
         len(izsaukumi) - n == 1 and all(r[1] == PNG and r[0] == 200 for r in rez), (len(izsaukumi) - n, [r[2] for r in rez]))

# ≤ 4 vienlaicīgi uz WMS
aktivi, max_aktivi, slots = [0], [0], threading.Lock()


def skaitosais(url, timeout=20):
    with slots:
        aktivi[0] += 1
        max_aktivi[0] = max(max_aktivi[0], aktivi[0])
    time.sleep(0.3)
    with slots:
        aktivi[0] -= 1
    return PNG


k._lejupieladet = skaitosais
pavedieni = [threading.Thread(target=k.pludu_flize, args=("pali", "11", str(1158 + i), "629")) for i in range(10)]
for p in pavedieni:
    p.start()
for p in pavedieni:
    p.join()
parbaude("10 dažādas flīzes → uz WMS ne vairāk kā 4 reizē", max_aktivi[0] == 4, max_aktivi[0])
k._lejupieladet = viltots

# tīrīšana: robeža → izdzēš vecākās
mape = os.path.join(DATI, "flizes")
faili = []
for i in range(6):
    c = os.path.join(mape, "pali", "9", "300", f"{i}.png")
    os.makedirs(os.path.dirname(c), exist_ok=True)
    with open(c, "wb") as f:
        f.write(b"x" * 1000)
    os.utime(c, (time.time() - 1000 + i, time.time() - 1000 + i))
    faili.append(c)
sens = os.path.join(mape, "pali", "9", "300", "sens.png")
with open(sens, "wb") as f:
    f.write(b"x")
os.utime(sens, (time.time() - 2 * k.FLIZU_TTL - 5,) * 2)
cits = sum(os.path.getsize(os.path.join(s_, n_)) for s_, _, nn in os.walk(mape) for n_ in nn if not n_.startswith("sens"))
k.FLIZU_MAX_BAITI = cits - 2500  # jāizdzēš vismaz 3 no 6 testa failiem (90 % robeža)
kopa = k._flizu_tirit(mape)
parbaude("tīrīšana: > 2 × TTL vecā izdzēsta", not os.path.exists(sens))
parbaude("tīrīšana: izmērs ≤ 90 % no robežas, vecākās dzēstas pirmās",
         kopa <= k.FLIZU_MAX_BAITI * 0.9 and not os.path.exists(faili[0]) and os.path.exists(faili[-1]), (kopa, [os.path.exists(f) for f in faili]))
k.FLIZU_MAX_BAITI = 500 * 1024 * 1024

# ---------- 3. HTTP: galvenes, ETag → 304, HEAD ----------
serveris = k.Serveris(("127.0.0.1", 0), k.Apstradatajs)
threading.Thread(target=serveris.serve_forever, daemon=True).start()
BAZE = f"http://127.0.0.1:{serveris.server_address[1]}"


def iegut(cels, **galvenes):
    try:
        with urllib.request.urlopen(urllib.request.Request(BAZE + cels, headers=galvenes), timeout=10) as r:
            return r.status, dict(r.headers), r.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read()


s, g, b = iegut("/api/pludi/flize/pali/13/4655/2517.png")
parbaude("HTTP 200 image/png, max-age 86400, ETag, X-Flize, CORS",
         s == 200 and g.get("Content-Type") == "image/png" and g.get("Cache-Control") == "public, max-age=86400"
         and g.get("ETag") and g.get("X-Flize") == "kesa" and g.get("Access-Control-Allow-Origin") == "*" and b == PNG, (s, g))
s2, g2, b2 = iegut("/api/pludi/flize/pali/13/4655/2517.png", **{"If-None-Match": g.get("ETag", "")})
parbaude("If-None-Match → 304 bez satura", s2 == 304 and b2 == b"", (s2, len(b2)))
rezims["kluda"] = True
s, g, b = iegut("/api/pludi/flize/juras/13/4637/2512.png")
rezims["kluda"] = False
parbaude("HTTP kļūda: 502, no-store, bez ETag", s == 502 and g.get("Cache-Control") == "no-store" and "ETag" not in g, (s, g))
s, g, b = iegut("/api/pludi/flize/nav/13/1/1.png")
parbaude("HTTP nezināma paka → 404 JSON", s == 404 and "json" in g.get("Content-Type", ""), (s, g))
req = urllib.request.Request(BAZE + "/api/pludi/flize/pali/13/4655/2517.png", method="HEAD")
with urllib.request.urlopen(req, timeout=10) as r:
    parbaude("HEAD → 200 bez satura", r.status == 200 and r.read() == b"")
serveris.shutdown()

# ---------- 4. Īsts LVĢMC WMS (pēc izvēles) ----------
if "--tiessaiste" in sys.argv:
    k._lejupieladet = ISTS
    k._flizu_neveiksmes.clear()
    t0 = time.time()
    s, dati, veids, _ = k.pludu_flize("pali", "13", "4654", "2517")
    print(f"      īsts WMS: {s} {veids} {len(dati)} B, {time.time() - t0:.1f} s")
    parbaude("īsts WMS: Ogres flīze ir PNG", dati.startswith(b"\x89PNG") and veids in ("jauna", "kesa"), veids)

print("\n" + ("Visi testi izdevās." if not kludas else f"{kludas} kļūdas."))
sys.exit(1 if kludas else 0)
