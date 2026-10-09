"""Augstākās vietas plūdu demo (Ogre): LĢIA digitālais reljefa modelis 20 m (CC BY 4.0) → poligoni ≥ slieksnis m → GeoJSON.

Avots: https://www.lgia.gov.lv/lv/digit%C4%81lais-reljefa-modelis
Lejupielāde (~380 MB 7z, iekšā 4,7 GB teksts "X Y Z", LKS-92 TM / EPSG:3059, augstumi LAS-2000,5):
    https://s3.storage.pub.lvdc.gov.lv/lgia-opendata/citi/dtm/DTM_Latvija_20m.7z
Izpako ar 7-Zip vai py7zr un padod .txt:

    uv run --no-project --with pandas --with numpy --with rasterio --with shapely --with pyproj \
        src/demo/augstumi.py DTM_Latvija_20m.txt --slieksnis 15 --izvade production/demo/augstumi-ogre.geojson
"""
import argparse
import json
import pathlib
import re
import sys

import numpy as np
import pandas as pd
import rasterio.features
from pyproj import Transformer
from rasterio.transform import from_origin
from shapely.geometry import mapping, shape
from shapely.ops import transform as sh_transform, unary_union

SOLIS = 20.0


def izgriezt(dtm, x0, x1, y0, y1):
    dalas = []
    for d in pd.read_csv(dtm, sep=r"\s+", header=None, names=["x", "y", "z"], chunksize=5_000_000, dtype="float64", engine="c"):
        m = (d.x >= x0) & (d.x <= x1) & (d.y >= y0) & (d.y <= y1)
        if m.any():
            dalas.append(d[m])
    return pd.concat(dalas)


def main():
    a = argparse.ArgumentParser()
    a.add_argument("dtm", help="DTM_Latvija_20m.txt vai ar --saglabat izgriezts .npy")
    a.add_argument("--bbox", default="24.53,56.775,24.70,56.86", help="lon_min,lat_min,lon_max,lat_max (WGS84)")
    a.add_argument("--slieksnis", type=float, default=15.0, help="augstums m LAS-2000,5")
    a.add_argument("--min-laukums", type=float, default=20000, help="mazākus poligonus (m²) atmet")
    a.add_argument("--izvade", default="production/demo/augstumi-ogre.geojson")
    a.add_argument("--saglabat", help="izgriezto apgabalu saglabāt .npy (nākamreiz padod to dtm vietā)")
    a.add_argument("--statistika", action="store_true", help="tikai augstumu sadalījums apgabalā")
    args = a.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    lon0, lat0, lon1, lat1 = map(float, args.bbox.split(","))
    uz_lks = Transformer.from_crs(4326, 3059, always_xy=True)
    uz_wgs = Transformer.from_crs(3059, 4326, always_xy=True)
    xs, ys = uz_lks.transform([lon0, lon1, lon0, lon1], [lat0, lat0, lat1, lat1])
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)

    griezums = pathlib.Path(args.dtm)
    if griezums.suffix == ".npy":  # jau izgriezts apgabals (--saglabat)
        p = pd.DataFrame(np.load(griezums), columns=["x", "y", "z"])
    else:
        p = izgriezt(args.dtm, x0, x1, y0, y1)
        if args.saglabat:
            np.save(args.saglabat, p[["x", "y", "z"]].values)
    p = p[(p.x >= x0) & (p.x <= x1) & (p.y >= y0) & (p.y <= y1)]
    print(f"punkti apgabalā: {len(p)}; augstums {p.z.min():.1f}–{p.z.max():.1f} m")
    print("procentiles (5/25/50/75/95):", np.percentile(p.z, [5, 25, 50, 75, 95]).round(1))
    if args.statistika:
        return

    # Režģis: šūnas centrs = punkts (20 m solis)
    kol = np.round((p.x.values - x0) / SOLIS).astype(int)
    rin = np.round((y1 - p.y.values) / SOLIS).astype(int)
    z = np.full((rin.max() + 1, kol.max() + 1), np.nan, dtype="float32")
    z[rin, kol] = p.z.values
    maska = (z >= args.slieksnis).astype("uint8")
    tr = from_origin(x0 - SOLIS / 2, y1 + SOLIS / 2, SOLIS, SOLIS)

    poligoni = [shape(g) for g, v in rasterio.features.shapes(maska, mask=maska.astype(bool), transform=tr) if v == 1]
    kopa = unary_union([g for g in poligoni if g.area >= args.min_laukums]).simplify(15)
    gab = list(getattr(kopa, "geoms", [kopa]))
    gab = [g for g in gab if g.area >= args.min_laukums]
    print(f"poligoni ≥ {args.slieksnis} m: {len(gab)}, kopā {sum(g.area for g in gab) / 1e6:.2f} km²")

    pazime = lambda x, y, z=None: uz_wgs.transform(x, y)
    fc = {
        "type": "FeatureCollection",
        "avots": {"nos": "LĢIA digitālais reljefa modelis 20 m", "url": "https://www.lgia.gov.lv/lv/digit%C4%81lais-reljefa-modelis",
                  "licence": "CC BY 4.0"},
        "slieksnis_m": args.slieksnis,
        "features": [{
            "type": "Feature",
            "properties": {"apraksts": f"Reljefs ≥ {args.slieksnis:g} m virs jūras līmeņa (LAS-2000,5), {g.area / 1e4:.0f} ha. "
                                       "Ēkas un koki nav ņemti vērā; tas ir orientieris, nevis evakuācijas rīkojums."},
            "geometry": mapping(sh_transform(pazime, g)),
        } for g in gab],
    }
    teksts = json.dumps(fc, ensure_ascii=False, separators=(",", ":"))
    # koordinātas 5 zīmes aiz komata (~1 m)
    teksts = re.sub(r"(\d+\.\d{5})\d+", r"\1", teksts)
    pathlib.Path(args.izvade).write_text(teksts, encoding="utf-8")
    print(f"{args.izvade}: {len(teksts) / 1024:.0f} KB")


if __name__ == "__main__":
    main()
