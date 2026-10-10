"""Vienreiz ieraksta /api atbildes kartīšu testam (src/testi/kartites.py) uz src/testi/fiksturas/: ≤ 20 secīgi GET uz
map.repo.lv, vieta — Ogres centrs (pārbaužu "mana atrašanās vieta"). Jau ierakstītās netiek prasītas vēlreiz.

    uv run --no-project --python 3.12 src/testi/fiksturas_ierakstit.py
    uv run --no-project --python 3.12 src/demo/lokali.py --port 8097 --fiksturas src/testi/fiksturas
    uv run --no-project --python 3.12 --with playwright src/testi/kartites.py --url http://127.0.0.1:8097
"""
import json
import pathlib
import sys

SAKNE = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SAKNE / "src" / "demo"))
import lokali  # noqa: E402

LAT, LON = 56.8162, 24.614  # Ogre
LL = f"lat={LAT:.5f}&lon={LON:.5f}"
SARAKSTS = [
    "/api/kategorijas", "/api/regioni", "/api/avoti", lokali.OBJEKTI_VISI,
    f"/api/bridinajumi?{LL}", f"/api/prognoze?{LL}", f"/api/adreses/tuvaka?{LL}", f"/api/pasvaldiba?{LL}",
    f"/api/pludi?{LL}", f"/api/udens?{LL}&limit=3", f"/api/noverojumi?{LL}&limit=8", f"/api/augsne?{LL}",
    f"/api/celi?{LL}&r=5000", "/api/satiksme", "/api/meklejumi/top?n=10", "/api/prognozes", "/api/zibens",
]

if __name__ == "__main__":
    lokali.FIKSTURAS = SAKNE / "src" / "testi" / "fiksturas"
    lokali.FIKSTURAS.mkdir(exist_ok=True)
    lokali.IERAKSTIT = 20
    for cels in SARAKSTS:
        atslega = "api/objekti" if cels == lokali.OBJEKTI_VISI else cels.split("?")[0]
        lokali.fikstura(atslega, cels)
    # Ogres robeža (kartē, kad vaicājumā ir vietvārds) un maršruts līdz tuvākajai patvertnei
    regioni = json.loads(lokali.fikstura("/api/regioni", "/api/regioni")[2])
    ogre = next(r["kods"] for r in regioni if r["nosaukums"].startswith("Ogre"))
    lokali.fikstura(f"/api/regioni/{ogre}", f"/api/regioni/{ogre}")
    p = json.loads(lokali.objekti({"kategorijas": ["patvertne"], "lat": [str(LAT)], "lon": [str(LON)], "limit": ["1"]})[2])["features"][0]
    plon, plat = p["geometry"]["coordinates"]
    lokali.fikstura("/api/marsruts", f"/api/marsruts?no={LAT:.5f},{LON:.5f}&uz={plat:.5f},{plon:.5f}")
    print(f"atlikuši ieraksti: {lokali.IERAKSTIT}")
