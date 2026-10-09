"""Ūdens līmenis LVĢMC hidroloģiskajās stacijās → GeoJSON ielādei ar ielade.py (slānis udens_limenis).

Avots: LVĢMC "Hidrometeoroloģiskie novērojumi", data.gov.lv, CC0 1.0:
  hidro_stacijas.csv          stacijas (GEOGR1 = lon, GEOGR2 = lat, ELEVATION = posteņa "0", m LAS-2000,5)
  hidro_operativie_dati.csv   pēdējās 48 h, katru stundu; LIMEN = ūdens līmenis cm virs posteņa "0",
                              WTEMD = ūdens temperatūra °C. Laiks UTC, vērtība par stundu pirms tā.
Bīstamības līmeņi (PRIS) nav atvērtie dati, tāpēc te netiek lietoti.

Palaišana (VPS, katru stundu — udens_limenis.sh, hakatons-udens.timer):
  python3 src/karte/db/udens_limenis.py /tmp/udens_limenis.geojson
"""

import csv
import io
import json
import sys
import urllib.request
from datetime import datetime, timedelta, timezone

KOPA = "https://data.gov.lv/dati/dataset/40d80be5-0c09-47c4-80f3-fad4bec19f33/resource"
STACIJAS = KOPA + "/93fd5e2c-20c4-496e-a920-ff29bda20383/download/hidro_stacijas.csv"
DATI = KOPA + "/de5f06e9-6f44-497d-8ec2-72a2483608e8/download/hidro_operativie_dati.csv"
DERIGS_H = 6  # vecāks mērījums kartē vairs netiek rādīts (API filtrē pēc derigs_lidz)


def lasit(url, timeout=60):
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return list(csv.DictReader(io.StringIO(r.read().decode("utf-8-sig"))))


def laiks(teksts):
    return datetime.strptime(teksts, "%Y.%m.%d %H:%M:%S").replace(tzinfo=timezone.utc)


def stacijas(timeout=60):
    """GeoJSON features: pēdējais līmenis katrā stacijā. Lieto arī karte_api.py (/api/udens)."""
    merijumi = {}  # (stacija, parametrs) -> {laiks: vērtība}
    for r in lasit(DATI, timeout):
        if r["ABBREVIATION"] in ("LIMEN", "WTEMD") and r["VALUE"].strip():
            try:
                vertiba = float(r["VALUE"])
            except ValueError:  # viena bojāta vērtība nedrīkst apturēt visu ielādi
                continue
            merijumi.setdefault((r["STATION_ID"], r["ABBREVIATION"]), {})[laiks(r["DATETIME"])] = vertiba

    features = []
    for s in lasit(STACIJAS, timeout):
        limenis = merijumi.get((s["STATION_ID"], "LIMEN"))
        if not limenis or not s["GEOGR1"] or not s["GEOGR2"]:
            continue
        pedejais = max(limenis)
        cm = limenis[pedejais]
        pirms24 = limenis.get(pedejais - timedelta(hours=24))
        temp = merijumi.get((s["STATION_ID"], "WTEMD"), {})
        nulle = float(s["ELEVATION"]) if s["ELEVATION"].strip() else None
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [float(s["GEOGR1"]), float(s["GEOGR2"])]},
            "properties": {
                "stacija": s["STATION_ID"],
                "nosaukums": s["NAME"],
                "limenis_cm": round(cm),
                "limenis_m": round(nulle + cm / 100, 2) if nulle is not None else None,
                "nulle_m": nulle,
                "izmaina_24h_cm": round(cm - pirms24) if pirms24 is not None else None,
                "udens_temp": temp[max(temp)] if temp else None,
                "laiks": pedejais.isoformat().replace("+00:00", "Z"),
                "derigs_lidz": (pedejais + timedelta(hours=DERIGS_H)).isoformat(),
            },
        })
    return features


def main(izeja):
    features = stacijas()
    with open(izeja, "w", encoding="utf-8") as f:
        json.dump({"type": "FeatureCollection", "features": features}, f, ensure_ascii=False)
    jaunakais = max((f["properties"]["laiks"] for f in features), default="—")
    print(f"{len(features)} stacijas ar ūdens līmeni, jaunākais mērījums {jaunakais}", file=sys.stderr)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "udens_limenis.geojson")
