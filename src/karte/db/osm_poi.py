"""Interešu punkti no OpenStreetMap (Overpass API, ODbL) → src/karte/dati/osm_poi.geojson.

Palaišana (lokāli vai VPS, tikai standarta bibliotēka):
  python src/karte/db/osm_poi.py
Pēc tam ielāde (VPS):
  python3 src/karte/db/ielade.py src/karte/dati/osm_poi.geojson --avots osm \
      --nosaukums "{name}" --adrese "{adrese}"
Jaunu kategoriju pievieno KATEGORIJAS un shema.sql (tabula kategorijas).
"""

import json
import pathlib
import sys
import time
import urllib.parse
import urllib.request

# kategorijas kods → OSM tags
KATEGORIJAS = {
    "bankomats": ("amenity", "atm"),
    "aptieka": ("amenity", "pharmacy"),
    "slimnica": ("amenity", "hospital"),
    "policija": ("amenity", "police"),
    "ugunsdzeseji": ("amenity", "fire_station"),
    "degviela": ("amenity", "fuel"),
}
SERVERI = ["https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter"]
LAUKI = ["name", "operator", "brand", "opening_hours", "phone", "website", "atm", "dispensing", "emergency"]
IZEJA = pathlib.Path(__file__).resolve().parents[1] / "dati" / "osm_poi.geojson"


def vaicajums():
    filtri = "".join(f'nwr["{k}"="{v}"](area.lv);' for k, v in KATEGORIJAS.values())
    return f'[out:json][timeout:180];area["ISO3166-1"="LV"][admin_level=2]->.lv;({filtri});out center tags;'


def lejupieladet(q):
    dati = urllib.parse.urlencode({"data": q}).encode()
    for url in SERVERI:
        for meginajums in range(3):
            try:
                req = urllib.request.Request(url, data=dati, headers={"User-Agent": "map.repo.lv (hakatons)"})
                with urllib.request.urlopen(req, timeout=200) as r:
                    return json.load(r)
            except Exception as e:  # noqa: BLE001 - mēģinām nākamo serveri
                print(f"{url}: {e}", file=sys.stderr)
                time.sleep(5 * (meginajums + 1))
    sys.exit("Overpass nav pieejams")


def main():
    pec_taga = {v: k for k, v in KATEGORIJAS.items()}
    features = []
    for el in lejupieladet(vaicajums())["elements"]:
        tagi = el.get("tags", {})
        kategorija = next((pec_taga[(k, tagi[k])] for k in ("amenity",) if (k, tagi.get(k)) in pec_taga), None)
        punkts = el if el["type"] == "node" else el.get("center")
        if not kategorija or not punkts:
            continue
        iela = " ".join(x for x in (tagi.get("addr:street"), tagi.get("addr:housenumber")) if x)
        adrese = ", ".join(x for x in (iela, tagi.get("addr:city")) if x)
        ipasibas = {"kategorija": kategorija, "id": f"{el['type']}/{el['id']}", "adrese": adrese}
        ipasibas.update({k: tagi[k] for k in LAUKI if k in tagi})
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [round(punkts["lon"], 6), round(punkts["lat"], 6)]},
            "properties": ipasibas,
        })
    features.sort(key=lambda f: f["properties"]["id"])
    IZEJA.parent.mkdir(parents=True, exist_ok=True)
    IZEJA.write_text(
        json.dumps({"type": "FeatureCollection", "features": features}, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    skaits = {}
    for f in features:
        skaits[f["properties"]["kategorija"]] = skaits.get(f["properties"]["kategorija"], 0) + 1
    print(IZEJA, skaits)


if __name__ == "__main__":
    main()
