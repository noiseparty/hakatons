"""Lokāls serveris pārbaudēm: production/ kā statiski faili + /api/* pārsūtīts uz https://map.repo.lv (tikai GET).

    uv run --no-project src/demo/lokali.py [--port 8090] [--flizes http://127.0.0.1:8920]
    → src/testi/parbaude.py --url http://127.0.0.1:8090 ; src/demo/ierices.py --url http://127.0.0.1:8090

--flizes: /api/pludi/flize/* sūta uz lokālu karte_api.py (plūdu flīžu keša pārbaudei bez datubāzes), pārējo — uz map.repo.lv.
"""
import argparse
import functools
import http.server
import pathlib
import urllib.error
import urllib.request

PROD = pathlib.Path(__file__).resolve().parents[2] / "production"
FLIZES = None
GALVENES = ("X-Flize", "Cache-Control", "ETag")


class Apstradatajs(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        if not self.path.startswith("/api/"):
            return super().do_GET()
        baze = FLIZES if FLIZES and self.path.startswith("/api/pludi/flize/") else "https://map.repo.lv"
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
    arg = a.parse_args()
    FLIZES = arg.flizes
    http.server.ThreadingHTTPServer(("127.0.0.1", arg.port), functools.partial(Apstradatajs, directory=str(PROD))).serve_forever()
