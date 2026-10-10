"""Lokāls serveris pārbaudēm: production/ kā statiski faili + /api/* pārsūtīts uz https://map.repo.lv (tikai GET).

    uv run --no-project src/demo/lokali.py [--port 8090]
    → src/testi/parbaude.py --url http://127.0.0.1:8090 ; src/demo/ierices.py --url http://127.0.0.1:8090
"""
import argparse
import functools
import http.server
import pathlib
import urllib.error
import urllib.request

PROD = pathlib.Path(__file__).resolve().parents[2] / "production"


class Apstradatajs(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        if not self.path.startswith("/api/"):
            return super().do_GET()
        try:
            with urllib.request.urlopen(urllib.request.Request("https://map.repo.lv" + self.path, headers={"User-Agent": "lokali"}), timeout=60) as r:
                dati, statuss, tips = r.read(), r.status, r.headers.get("content-type", "application/json")
        except urllib.error.HTTPError as e:
            dati, statuss, tips = e.read(), e.code, e.headers.get("content-type", "application/json")
        except Exception:  # noqa: BLE001
            dati, statuss, tips = b'{"kluda": "proxy"}', 502, "application/json"
        self.send_response(statuss)
        self.send_header("Content-Type", tips)
        self.send_header("Content-Length", str(len(dati)))
        self.end_headers()
        self.wfile.write(dati)

    def do_POST(self):  # skaitīšanu (/api/meklejumi) lokāli nesūtām
        self.send_response(204)
        self.end_headers()


if __name__ == "__main__":
    a = argparse.ArgumentParser()
    a.add_argument("--port", type=int, default=8090)
    port = a.parse_args().port
    http.server.ThreadingHTTPServer(("127.0.0.1", port), functools.partial(Apstradatajs, directory=str(PROD))).serve_forever()
