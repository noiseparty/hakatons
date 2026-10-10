"""Plūdu zonu flīžu iesildīšana: pieprasa /api/pludi/flize/... demo vietām, lai API diska kešā (karte_api.py,
$HAKATONS_DATI/flizes) tās jau būtu, kad kartē ieslēdz plūdu slāni. LVĢMC WMS atbild 5–30 s uz flīzi; API uz augšu
laiž ≤ 4 reizē, tāpēc šeit noklusēti 3 (viens slots paliek lietotājiem). Palaist no rīta (~10–30 min pirmo reizi,
pēc tam sekundes — viss no kešas, 30 dienas).

    python3 src/karte/pludi_silda.py [--url https://map.repo.lv] [--zoom 10-14] [--vienlaicigi 3] [--vietas ogre,jurmala,riga]

--zoom ir kartes (Leaflet) tālummaiņa, kā lietotājs to redz; flīze ir 512 px, tāpēc API z = kartes z − 1.
Tikai standarta bibliotēka. Izvade: skaits pa X-Flize veidiem (kesa, jauna, veca, tukss, aiznemts, kluda).
"""
import argparse
import math
import sys
import time
import urllib.error
import urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

VIETAS = {  # [dienvidi, rietumi, ziemeļi, austrumi]
    "ogre": (56.78, 24.50, 56.88, 24.72),       # Ogre + Ogres upes grīva (demo "plūdi Mednieku iela 9 Ogre")
    "jurmala": (56.93, 23.45, 57.01, 23.97),    # Jūrmala no Ķemeriem līdz Lielupei
    "riga": (56.86, 23.93, 57.09, 24.33),       # Rīga
}
PAKAS = {  # tas pats, kas karte_api.py PLUDU_PAKAS / zonas.js wms[].robezas
    "pali": (55.76, 20.88, 57.67, 27.92),
    "ledus": (56.38, 23.95, 56.64, 26.01),
    "juras": (56.06, 20.84, 57.88, 24.49),
}


def flize_xy(lat, lon, z):
    n = 1 << z
    x = int((lon + 180) / 360 * n)
    y = int((1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n)
    return min(max(x, 0), n - 1), min(max(y, 0), n - 1)


def xyz_bbox_4326(z, x, y):
    n = 1 << z

    def platums(yy):
        return math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * yy / n))))
    return (platums(y + 1), x / n * 360 - 180, platums(y), (x + 1) / n * 360 - 180)


def saraksts(vietas, zoom_no, zoom_lidz):
    flizes = set()
    for v in vietas:
        d, r, zi, a = VIETAS[v]
        for karte_z in range(zoom_no, zoom_lidz + 1):
            z = karte_z - 1
            x0, y0 = flize_xy(zi, r, z)
            x1, y1 = flize_xy(d, a, z)
            for x in range(x0, x1 + 1):
                for y in range(y0, y1 + 1):
                    fd, fr, fz, fa = xyz_bbox_4326(z, x, y)
                    for paka, (pd, pr, pz, pa) in PAKAS.items():
                        if not (fd > pz or fz < pd or fr > pa or fa < pr):
                            flizes.add((paka, z, x, y))
    return sorted(flizes, key=lambda f: (f[1], f[0], f[2], f[3]))


def iegut(url, meginajumi=6):
    """→ X-Flize veids. 'aiznemts' (API rinda pilna) — mēģina vēlreiz pēc 3, 6, 9 … s."""
    for reize in range(meginajumi):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "map.repo.lv pludi_silda.py"})
            with urllib.request.urlopen(req, timeout=60) as r:
                r.read()
                veids = r.headers.get("X-Flize") or "?"
        except urllib.error.HTTPError as e:
            if e.code == 404 and "json" in (e.headers.get("Content-Type") or ""):
                return "nav-galapunkta"
            veids = e.headers.get("X-Flize") or f"http-{e.code}"
        except Exception:  # noqa: BLE001 — taimauts, savienojums
            veids = "savienojums"
        if veids != "aiznemts":
            return veids
        time.sleep(3 * (reize + 1))
    return "aiznemts"


def main():
    a = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    a.add_argument("--url", default="https://map.repo.lv")
    a.add_argument("--zoom", default="10-14", help="kartes tālummaiņa no-līdz (noklusēti 10-14)")
    a.add_argument("--vienlaicigi", type=int, default=3)
    a.add_argument("--vietas", default=",".join(VIETAS))
    arg = a.parse_args()
    zoom_no, _, zoom_lidz = arg.zoom.partition("-")
    zoom_no, zoom_lidz = int(zoom_no), int(zoom_lidz or zoom_no)
    vietas = [v.strip() for v in arg.vietas.split(",") if v.strip()]
    if not all(v in VIETAS for v in vietas):
        sys.exit("vietas: " + ", ".join(VIETAS))
    flizes = saraksts(vietas, zoom_no, zoom_lidz)
    print(f"{len(flizes)} flīzes ({', '.join(vietas)}; kartes z{zoom_no}–{zoom_lidz}), {arg.vienlaicigi} reizē → {arg.url}")
    sakums, skaits, kopa = time.time(), Counter(), 0
    with ThreadPoolExecutor(max_workers=max(1, arg.vienlaicigi)) as darbi:
        nakotne = {darbi.submit(iegut, f"{arg.url.rstrip('/')}/api/pludi/flize/{p}/{z}/{x}/{y}.png"): (p, z, x, y)
                   for p, z, x, y in flizes}
        for n in as_completed(nakotne):
            veids = n.result()
            skaits[veids] += 1
            kopa += 1
            if veids == "nav-galapunkta":
                darbi.shutdown(cancel_futures=True)
                sys.exit("API vēl nav /api/pludi/flize (vecāka karte_api.py versija)")
            if kopa % 25 == 0 or kopa == len(flizes):
                print(f"  {kopa}/{len(flizes)}  {time.time() - sakums:5.0f} s  " + ", ".join(f"{k} {v}" for k, v in sorted(skaits.items())))
    labas = skaits["kesa"] + skaits["jauna"] + skaits["tukss"] + skaits["veca"]
    print(f"Gatavs {time.time() - sakums:.0f} s: kešā {labas}/{len(flizes)}"
          + (f"; neizdevās {len(flizes) - labas} — palaidiet vēlreiz (neizdevušās API 60 s neprasa)" if labas < len(flizes) else ""))
    return 0 if labas else 1


if __name__ == "__main__":
    sys.exit(main())
