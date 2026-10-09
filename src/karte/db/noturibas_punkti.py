"""Noturības punktu kandidāti no OpenStreetMap (Overpass API, ODbL) → src/karte/dati/noturibas_punkti.geojson.

Noturības punkts = publiska ēka, kur krīzē (ilgstošs elektrības, siltuma, sakaru vai ūdens pārtraukums) varētu
sasildīties, uzlādēt telefonu, iegūt ūdeni un informāciju: bibliotēkas, kultūras / tautas nami, pašvaldību ēkas, skolas.
Tie ir tikai KANDIDĀTI: neviena pašvaldība nav apstiprinājusi, ka ēkā ir siltums, uzlāde, ūdens, wifi vai ģenerators,
tāpēc visas pazīmes ir "nav zināms" un statusa laiks (last_updated) ir tukšs; karte raksta "statuss nav apstiprināts".

Palaišana (lokāli vai VPS, tikai standarta bibliotēka):
  python src/karte/db/noturibas_punkti.py
Ielāde (VPS; avots osm-noturiba un kategorija noturibas_punkts ir shema.sql):
  python3 src/karte/db/ielade.py src/karte/dati/noturibas_punkti.geojson --avots osm-noturiba \
      --kategorija noturibas_punkts --nosaukums "{name}" --adrese "{adrese}" --apvienot 35
"""

import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from osm_poi import lejupieladet  # noqa: E402  (tie paši Overpass serveri un atkārtojumi)

# OSM amenity → veids latviski
VEIDI = {
    "library": "Bibliotēka",
    "community_centre": "Kultūras / tautas nams",
    "townhall": "Pašvaldības ēka",
    "school": "Skola",
}
# Pazīmes, ko pašvaldība varētu apstiprināt (research: notes/research/01_crisis_services_taxonomy.md)
PAZIMES = ["siltums", "uzlade", "udens", "wifi", "generators"]
LAUKI = ["name", "operator", "opening_hours", "website", "wheelchair", "building", "amenity"]
IZEJA = pathlib.Path(__file__).resolve().parents[1] / "dati" / "noturibas_punkti.geojson"
# Skolas: tikai vispārizglītojošās (nosaukumā "skola", "ģimnāzija", "licejs"…) un ne privātas — OSM "school" ietver arī
# valodu kursus un autoskolas, kas nav piemērotas patvēruma vietas.
SKOLA = re.compile(r"(skola|ģimnāzij|licej|tehnikum|koledž)", re.IGNORECASE)
NE_SKOLA = re.compile(r"(auto|valodu|dejas|deju|mūzikas studij|kursi|privāt)", re.IGNORECASE)


def vaicajums():
    filtri = "".join(f'nwr["amenity"="{a}"]["name"](area.lv);' for a in VEIDI)
    return f'[out:json][timeout:180];area["ISO3166-1"="LV"][admin_level=2]->.lv;({filtri});out center tags;'


def main():
    features = []
    for el in lejupieladet(vaicajums())["elements"]:
        tagi = el.get("tags", {})
        veids = VEIDI.get(tagi.get("amenity"))
        punkts = el if el["type"] == "node" else el.get("center")
        if not veids or not punkts:
            continue
        if tagi.get("operator:type") == "private" or tagi.get("access") == "private":
            continue
        if tagi.get("amenity") == "school" and (not SKOLA.search(tagi.get("name", "")) or NE_SKOLA.search(tagi.get("name", ""))):
            continue
        iela = " ".join(x for x in (tagi.get("addr:street"), tagi.get("addr:housenumber")) if x)
        adrese = ", ".join(x for x in (iela, tagi.get("addr:city") or tagi.get("addr:place")) if x)
        ipasibas = {"kategorija": "noturibas_punkts", "id": f"{el['type']}/{el['id']}", "adrese": adrese, "veids": veids,
                    "statuss": {p: "nav zināms" for p in PAZIMES}, "last_updated": None}
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
        skaits[f["properties"]["veids"]] = skaits.get(f["properties"]["veids"], 0) + 1
    print(IZEJA, len(features), skaits)


if __name__ == "__main__":
    main()
