"""Lokāls serveris pārbaudēm: production/ kā statiski faili + /api/* pārsūtīts uz https://map.repo.lv (tikai GET).

    uv run --no-project src/demo/lokali.py [--port 8090] [--flizes http://127.0.0.1:8920]
    → src/testi/parbaude.py --url http://127.0.0.1:8090 ; src/demo/ierices.py --url http://127.0.0.1:8090

--flizes: /api/pludi/flize/* sūta uz lokālu karte_api.py (plūdu flīžu keša pārbaudei bez datubāzes), pārējo — uz map.repo.lv.

--fiksturas DIR: /api/* nesūta uz map.repo.lv, bet atbild no ierakstītām atbildēm (src/testi/fiksturas/): bez slodzes
dzīvajai vietnei, var darbināt simtiem kartīšu (src/testi/kartites.py --url http://127.0.0.1:<port>). Atslēga ir
galapunkta ceļš (vaicājuma parametrus neņem vērā), izņemot:
  /api/objekti   — no viena ierakstīta ?bbox=<visa Latvija>&lat&lon&limit=5000 (pa slāņiem tuvākie): tuvākie pēc
                   kategorijas un attāluma no pieprasījuma lat/lon (attalums_m pārrēķina), vai punkti pieprasītajā bbox;
                   Papildu api_objekti_*.json (pilsētu taisnstūri, src/testi/fiksturas_adreses.py) pievieno kopai;
  /api/adreses   — DIR/adreses/<q>.json (ierakstīti VZD vaicājumi); citam q — ierakstītās adreses, kurās ir visi q
                   vārdi (kā karte_api.py LIKE '%vārds%'); bez DIR/adreses — vienmēr [];
  /api/regioni/X — katram kodam savs fails;
  punkta galapunkti (?lat&lon, marsruts ?no=) — DIR/punkti/<ceļš>__<lat>_<lon>.json, ja tāds ir ≤ 500 m no
                   pieprasījuma; citādi parastā fikstura, bet ar --attalums-km K: 404, ja tās punkts ir tālāk par K km
                   (lai Daugavpils adresei nerāda Ogres ceļu slēgumus).
--ierakstit N: ja fiksturas nav, to vienreiz paņem no map.repo.lv (secīgi, ne vairāk par N GET kopā) un saglabā.
Bez fiksturas un bez atļautiem ierakstiem — 404 {"kluda": "nav fiksturas"} (un rinda konsolē).
"""
import argparse
import functools
import http.server
import json
import os
import math
import pathlib
import re
import threading
import urllib.error
import urllib.parse
import urllib.request

PROD = pathlib.Path(__file__).resolve().parents[2] / "production"
LIVE = "https://map.repo.lv"
FLIZES = None
GALVENES = ("X-Flize", "Cache-Control", "ETag")
FIKSTURAS = None      # pathlib.Path vai None
IERAKSTIT = 0         # cik vēl drīkst ierakstīt no LIVE
OBJEKTI_VISI = "/api/objekti?bbox=20.9,55.6,28.3,58.1&lat=56.81&lon=24.6&limit=5000"
ATTALUMS_KM = None    # punkta fiksturu robeža (--attalums-km)
_slegs = threading.Lock()
_objekti = None


def _fails(cels):
    return FIKSTURAS / (re.sub(r"[^A-Za-z0-9_.-]+", "_", cels.strip("/")) + ".json")


def _live(cels):
    """Viens GET uz map.repo.lv (secīgi, skaitīti). → (statuss, tips, dati)"""
    global IERAKSTIT
    if IERAKSTIT <= 0:
        return None
    IERAKSTIT -= 1
    print(f"ieraksta (atlikuši {IERAKSTIT}): {cels}", flush=True)
    try:
        with urllib.request.urlopen(urllib.request.Request(LIVE + cels, headers={"User-Agent": "lokali-fiksturas"}), timeout=90) as r:
            return r.status, r.headers.get("content-type", "application/json"), r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get("content-type", "application/json"), e.read()


def fikstura(atslega, pilns_cels):
    """Saglabātā atbilde atslēgai (ceļam) vai ierakstīta no LIVE ar pilno ceļu. → (statuss, tips, dati) vai None"""
    f = _fails(atslega)
    with _slegs:
        if f.exists():
            d = json.loads(f.read_text(encoding="utf-8"))
            return d["statuss"], d["tips"], d["dati"].encode("utf-8")
        rez = _live(pilns_cels)
        if rez is None:
            return None
        statuss, tips, dati = rez
        if statuss < 500:
            f.write_text(json.dumps({"cels": pilns_cels, "statuss": statuss, "tips": tips, "dati": dati.decode("utf-8")},
                                    ensure_ascii=False), encoding="utf-8")
        return rez


def _attalums_m(lat1, lon1, lat2, lon2):
    f1, f2 = math.radians(lat1), math.radians(lat2)
    a = math.sin((f2 - f1) / 2) ** 2 + math.cos(f1) * math.cos(f2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2
    return round(12742000 * math.asin(math.sqrt(a)))


def objekti(q):
    global _objekti
    if _objekti is None:
        rez = fikstura("api/objekti", OBJEKTI_VISI)
        if rez is None or rez[0] != 200:
            return None
        visi = {f["id"]: f for f in json.loads(rez[2])["features"]}
        for f in sorted(FIKSTURAS.glob("api_objekti_*.json")):  # pilsētu taisnstūri adrešu pārbaudēm
            visi.update({x["id"]: x for x in json.loads(json.loads(f.read_text(encoding="utf-8"))["dati"])["features"]})
        _objekti = list(visi.values())
    kat = {k for k in ",".join(q.get("kategorijas", [""])).split(",") if k}
    feat = [f for f in _objekti if not kat or f["properties"]["kategorija"] in kat]
    if q.get("kritiskais", [""])[0] == "1":
        feat = [f for f in feat if (f["properties"].get("ipasibas") or {}).get("kritiskais") == "1"]
    if "bbox" in q:
        w, s, e, n = (float(x) for x in q["bbox"][0].split(","))
        feat = [f for f in feat if w <= f["geometry"]["coordinates"][0] <= e and s <= f["geometry"]["coordinates"][1] <= n]
    limit = int(float(q.get("limit", ["5000"])[0]))
    if "lat" in q and "lon" in q:
        lat, lon = float(q["lat"][0]), float(q["lon"][0])
        feat = [{**f, "properties": {**f["properties"], "attalums_m": _attalums_m(lat, lon, f["geometry"]["coordinates"][1],
                                                                                f["geometry"]["coordinates"][0])}} for f in feat]
        feat.sort(key=lambda f: f["properties"]["attalums_m"])
    else:
        feat = [{**f, "properties": {k: v for k, v in f["properties"].items() if k != "attalums_m"}} for f in feat]
    return 200, "application/json", json.dumps({"type": "FeatureCollection", "features": feat[:limit]}, ensure_ascii=False).encode("utf-8")


def vienkarsot(teksts):
    """Kā karte_api._vienkarsot: mazie burti bez garumzīmēm."""
    import unicodedata
    return "".join(c for c in unicodedata.normalize("NFD", teksts.lower()) if not unicodedata.combining(c))


def adreses_atslega(q):
    return re.sub(r"\W+", "_", vienkarsot(q).strip()).strip("_")  # kirilica paliek: "наводнение Rīgas…" ≠ "Rīgas…"


def adreses(q):
    mape = FIKSTURAS / "adreses"
    teksts, limit = q.get("q", [""])[0], int(q.get("limit", ["8"])[0])
    if not mape.is_dir():
        return 200, "application/json", b"[]"
    f = mape / (adreses_atslega(teksts) + ".json")
    if f.exists():
        rindas = json.loads(json.loads(f.read_text(encoding="utf-8"))["dati"])
    else:  # nav ierakstīts: ierakstītās adreses, kurās ir visi vārdi
        vardi = [v for v in re.split(r"[\s,]+", vienkarsot(teksts)) if v]
        visas = {}
        for x in sorted(mape.glob("*.json")):
            for r in json.loads(json.loads(x.read_text(encoding="utf-8"))["dati"]):
                visas[r["kods"]] = r
        rindas = [r for r in visas.values() if all(v in vienkarsot(r["adrese"]) for v in vardi)]
    return 200, "application/json", json.dumps(rindas[:limit], ensure_ascii=False).encode("utf-8")


def _punkts(q):
    if "lat" in q and "lon" in q:
        return float(q["lat"][0]), float(q["lon"][0])
    if "no" in q:  # /api/marsruts?no=lat,lon&uz=…
        lat, lon = q["no"][0].split(",")[:2]
        return float(lat), float(lon)
    return None


def punkta_fikstura(cels, q, pilns_cels):
    """Punkta galapunkts: tuvākā DIR/punkti fikstura ≤ 500 m, citādi parastā (ar --attalums-km — tikai tuvu)."""
    vieta = _punkts(q)
    if vieta is None:
        return fikstura(cels, pilns_cels)
    prefikss = _fails(cels).stem + "__"
    labakais = None
    for f in (FIKSTURAS / "punkti").glob(prefikss + "*.json"):
        lat, lon = (float(x) for x in f.stem[len(prefikss):].split("_"))
        d = _attalums_m(vieta[0], vieta[1], lat, lon)
        if d <= 500 and (labakais is None or d < labakais[0]):
            labakais = d, f
    if labakais:
        d = json.loads(labakais[1].read_text(encoding="utf-8"))
        return d["statuss"], d["tips"], d["dati"].encode("utf-8")
    if ATTALUMS_KM is not None and _fails(cels).exists():
        ierakstits = _punkts(urllib.parse.parse_qs(urllib.parse.urlsplit(
            json.loads(_fails(cels).read_text(encoding="utf-8"))["cels"]).query))
        if ierakstits and _attalums_m(*vieta, *ierakstits) > ATTALUMS_KM * 1000:
            return None
    return fikstura(cels, pilns_cels)


def no_fiksturam(pilns_cels):
    url = urllib.parse.urlsplit(pilns_cels)
    cels, q = url.path.rstrip("/"), urllib.parse.parse_qs(url.query)
    if cels == "/api/objekti":
        rez = objekti(q)
    elif cels == "/api/adreses":
        rez = adreses(q)
    else:
        rez = punkta_fikstura(cels, q, pilns_cels)
    if rez is None:
        print(f"nav fiksturas: {pilns_cels}", flush=True)
        return 404, "application/json", b'{"kluda": "nav fiksturas"}'
    return rez


class Apstradatajs(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def translate_path(self, path):
        # kā Caddy try_files {path} {path}/ {path}.html: /map -> map.html
        f = super().translate_path(path)
        if not os.path.exists(f) and os.path.exists(f + ".html"):
            return f + ".html"
        return f

    def do_GET(self):
        if not self.path.startswith("/api/"):
            return super().do_GET()
        if FIKSTURAS:
            statuss, tips, dati = no_fiksturam(self.path)
            self.send_response(statuss)
            self.send_header("Content-Type", tips)
            self.send_header("Content-Length", str(len(dati)))
            self.end_headers()
            self.wfile.write(dati)
            return
        baze = FLIZES if FLIZES and self.path.startswith("/api/pludi/flize/") else LIVE
        galvenes = {}
        try:
            with urllib.request.urlopen(urllib.request.Request(baze + self.path, headers={"User-Agent": "lokali"}), timeout=60) as r:
                dati, statuss, tips, galvenes = r.read(), r.status, r.headers.get("content-type", "application/json"), r.headers
        except urllib.error.HTTPError as e:
            dati, statuss, tips, galvenes = e.read(), e.code, e.headers.get("content-type", "application/json"), e.headers
        except Exception:  # noqa: BLE001
            dati, statuss, tips = b'{"kluda": "proxy"}', 502, "application/json"
        self.send_response(statuss)
        self.send_header("Content-Type", tips)
        self.send_header("Content-Length", str(len(dati)))
        for g in GALVENES:  # tikai flīzēm (zonas.js lasa X-Flize); pārējām atbildēm kā līdz šim
            if self.path.startswith("/api/pludi/flize/") and galvenes.get(g):
                self.send_header(g, galvenes[g])
        self.end_headers()
        self.wfile.write(dati)

    def do_POST(self):  # skaitīšanu (/api/meklejumi) lokāli nesūtām
        self.send_response(204)
        self.end_headers()


if __name__ == "__main__":
    a = argparse.ArgumentParser()
    a.add_argument("--port", type=int, default=8090)
    a.add_argument("--flizes", help="API plūdu flīzēm, piem. http://127.0.0.1:8920 (lokāls karte_api.py)")
    a.add_argument("--fiksturas", help="mape ar ierakstītām /api atbildēm (piem. src/testi/fiksturas): bez map.repo.lv")
    a.add_argument("--ierakstit", type=int, default=0, help="ar --fiksturas: trūkstošās paņemt no map.repo.lv, ne vairāk par N")
    a.add_argument("--attalums-km", type=float, help="ar --fiksturas: punkta galapunktam 404, ja fikstura ir tālāk par K km")
    arg = a.parse_args()
    FLIZES = arg.flizes
    if arg.fiksturas:
        FIKSTURAS = pathlib.Path(arg.fiksturas).resolve()
        FIKSTURAS.mkdir(parents=True, exist_ok=True)
        IERAKSTIT = arg.ierakstit
        ATTALUMS_KM = arg.attalums_km
    class Serveris(http.server.ThreadingHTTPServer):
        request_queue_size = 128  # noklusētās 5: vairākas pārlūka cilnes vienlaikus — skripti nonāk līdz ERR_NO_BUFFER_SPACE
        allow_reuse_address = False  # Windows: citādi otrs serveris klusi "aizņem" to pašu portu
    Serveris(("127.0.0.1", arg.port), functools.partial(Apstradatajs, directory=str(PROD))).serve_forever()
