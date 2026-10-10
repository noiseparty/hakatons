"""Punkti no OpenStreetMap (Overpass API, ODbL, © OpenStreetMap līdzstrādnieki) → src/karte/dati/.

Tikai tām kategorijām, kurām nav valsts atvērto datu (aptiekas, slimnīcas, policija, VUGD nāk no data.gov.lv:
valsts_dati.py).
  osm_poi.geojson    bankomāti, DUS (avots osm)
  osm_udens.geojson  dzeramā ūdens punkti: amenity=drinking_water, man_made=water_tap, natural=spring ar
                     drinking_water=yes, amenity=water_point (avots osm-udens; kategorija udens_punkts, kopā ar
                     simulētajiem sim-udens, kas paliek marķēti)
  osm_wifi.geojson   bezmaksas Wi-Fi: internet_access=wlan un internet_access:fee=no (avots osm-wifi)
  osm_ev.geojson     elektroauto uzlādes stacijas: amenity=charging_station (avots osm-ev)
  osm_vet.geojson    veterinārās klīnikas: amenity=veterinary (avots osm-vet)
Katram slānim savs Overpass vaicājums (timeout 60 s, vienu reizi atkārto, pauze starp vaicājumiem); viena slāņa kļūda
neaptur pārējos, beigās iznākuma kods 1.

Palaišana (lokāli vai VPS, tikai standarta bibliotēka):
  python src/karte/db/osm_poi.py                         visi faili
  python src/karte/db/osm_poi.py udens_punkts veterinars tikai šie slāņi (osm = bankomāti un DUS)
Pēc tam ielāde (VPS; komandas arī atjaunot_visu.sh):
  python3 src/karte/db/ielade.py src/karte/dati/osm_poi.geojson --avots osm --nosaukums "{name}" --adrese "{adrese}" --apvienot 35
  python3 src/karte/db/ielade.py src/karte/dati/osm_udens.geojson --avots osm-udens --nosaukums "{nosaukums}" --adrese "{adrese}" --apvienot 35
Jaunu kategoriju pievieno SLANI un shema.sql (tabulas kategorijas un avoti).
"""

import json
import os
import pathlib
import sys
import time
import urllib.parse
import urllib.request

# kategorijas kods → OSM tags (osm_poi.geojson, avots osm)
KATEGORIJAS = {
    "bankomats": ("amenity", "atm"),
    "degviela": ("amenity", "fuel"),
}
# Overpass apgabals no OSM relācijas 72594 (Latvija): ātrāk nekā area["ISO3166-1"="LV"], ko serveri noslodzē atbild ar 504
LATVIJA = 3600000000 + 72594
SERVERI = ["https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter"]
LAUKI = ["name", "operator", "brand", "opening_hours", "phone", "website", "atm", "dispensing", "emergency"]
# HAKATONS_DATI: cita mape (VPS ikdienas atjaunošana raksta /var/lib/hakatons/dati, nevis git kopijā)
MAPE = pathlib.Path(os.environ.get("HAKATONS_DATI") or pathlib.Path(__file__).resolve().parents[1] / "dati")
IZEJA = MAPE / "osm_poi.geojson"

# Atsevišķi slāņi: kategorija → fails, Overpass filtri, saglabājamie tagi, nosaukums, ja OSM tā nav
SLANI = {
    "udens_punkts": {
        "fails": "osm_udens.geojson",
        "filtri": ['nwr["amenity"="drinking_water"]', 'nwr["man_made"="water_tap"]',
                   'nwr["natural"="spring"]["drinking_water"="yes"]', 'nwr["amenity"="water_point"]'],
        "lauki": ["name", "operator", "opening_hours", "seasonal", "drinking_water", "fee", "access", "description",
                  "amenity", "man_made", "natural"],
    },
    "wifi_punkts": {
        "fails": "osm_wifi.geojson",
        "filtri": ['nwr["internet_access"="wlan"]["internet_access:fee"="no"]'],
        "lauki": ["name", "operator", "brand", "opening_hours", "website", "internet_access:ssid", "amenity", "shop",
                  "tourism", "leisure", "office"],
    },
    "ev_uzlade": {
        "fails": "osm_ev.geojson",
        "filtri": ['nwr["amenity"="charging_station"]'],
        "lauki": ["name", "operator", "network", "brand", "opening_hours", "capacity", "fee", "access", "authentication:app",
                  "socket:type2", "socket:type2_combo", "socket:chademo", "socket:type2:output", "socket:type2_combo:output",
                  "socket:chademo:output", "motorcar"],
    },
    "veterinars": {
        "fails": "osm_vet.geojson",
        "filtri": ['nwr["amenity"="veterinary"]'],
        "lauki": ["name", "operator", "opening_hours", "website", "emergency"],
    },
}
# Wi-Fi vietas veids (pēc OSM taga), ja nav nosaukuma
WIFI_VEIDI = {"library": "Bibliotēka", "cafe": "Kafejnīca", "restaurant": "Restorāns", "fast_food": "Ēstuve",
              "bar": "Bārs", "pub": "Krogs", "hotel": "Viesnīca", "guest_house": "Viesu nams", "fuel": "DUS",
              "townhall": "Pašvaldības ēka", "community_centre": "Kultūras nams", "bus_station": "Autoosta"}


def vaicajums(filtri=None, timeout=180):
    if filtri is None:
        filtri = [f'nwr["{k}"="{v}"]' for k, v in KATEGORIJAS.values()]
    saturs = "".join(f"{f}(area.lv);" for f in filtri)
    return f'[out:json][timeout:{timeout}];area(id:{LATVIJA})->.lv;({saturs});out center tags;'


def lejupieladet(q, meginajumi=3, timeout=200, iziet=True):
    """Overpass vaicājums; katrs serveris līdz `meginajumi` reizēm. Neizdodas: iziet (sys.exit) vai None."""
    dati = urllib.parse.urlencode({"data": q}).encode()
    for url in SERVERI:
        for meginajums in range(meginajumi):
            try:
                req = urllib.request.Request(url, data=dati, headers={"User-Agent": "map.repo.lv (hakatons)"})
                with urllib.request.urlopen(req, timeout=timeout) as r:
                    return json.load(r)
            except Exception as e:  # noqa: BLE001 - mēģinām vēlreiz / nākamo serveri
                print(f"{url}: {e}", file=sys.stderr)
                time.sleep(5 * (meginajums + 1))
    if iziet:
        sys.exit("Overpass nav pieejams")
    return None


def lejupieladet_slani(q):
    """Viens slānis: 60 s Overpass laika limits, viens atkārtojums (otrs serveris)."""
    dati = urllib.parse.urlencode({"data": q}).encode()
    for i, url in enumerate(SERVERI[:2]):
        try:
            req = urllib.request.Request(url, data=dati, headers={"User-Agent": "map.repo.lv (hakatons)"})
            with urllib.request.urlopen(req, timeout=90) as r:
                d = json.load(r)
            if not d.get("elements"):  # laika limits ar HTTP 200 vai serverim vēl nav apgabala: mēģina nākamo
                raise RuntimeError(d.get("remark") or "0 elementu")
            return d
        except Exception as e:  # noqa: BLE001
            print(f"{url}: {e}", file=sys.stderr)
            if i == 0:
                time.sleep(10)
    return None


def adrese(tagi):
    iela = " ".join(x for x in (tagi.get("addr:street"), tagi.get("addr:housenumber")) if x)
    return ", ".join(x for x in (iela, tagi.get("addr:city") or tagi.get("addr:place")) if x)


def punkts(el):
    p = el if el["type"] == "node" else el.get("center")
    return [round(p["lon"], 6), round(p["lat"], 6)] if p else None


def rakstit(fails, features):
    features.sort(key=lambda f: f["properties"]["id"])
    fails.parent.mkdir(parents=True, exist_ok=True)
    fails.write_text(
        json.dumps({"type": "FeatureCollection", "features": features}, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )


def nosaukums(kategorija, t):
    """Latvisks nosaukums kartītei, ja OSM nav name (lielākajai daļai ūdens krānu un uzlādes staciju)."""
    if kategorija == "udens_punkts":
        if t.get("natural") == "spring":
            veids = "Avots (dzeramais ūdens)"
        elif t.get("amenity") == "water_point":
            veids = "Ūdens ņemšanas punkts"
        elif t.get("man_made") == "water_tap":
            veids = "Ūdens krāns"
        else:
            veids = "Dzeramā ūdens krāns"
        return f"{veids}: {t['name']}" if t.get("name") else veids
    if kategorija == "wifi_punkts":
        veids = next((WIFI_VEIDI[t[k]] for k in ("amenity", "tourism") if t.get(k) in WIFI_VEIDI), None)
        return t.get("name") or (f"{veids} (bezmaksas Wi-Fi)" if veids else "Bezmaksas Wi-Fi")
    if kategorija == "ev_uzlade":
        kas = t.get("name") or t.get("network") or t.get("operator") or t.get("brand")
        return f"Elektroauto uzlāde: {kas}" if kas else "Elektroauto uzlādes stacija"
    if kategorija == "veterinars":
        return t.get("name") or "Veterinārā klīnika"
    return t.get("name")


def derigs(kategorija, t):
    if t.get("access") in ("private", "no") or t.get("disused") == "yes":
        return False
    if kategorija == "udens_punkts" and t.get("drinking_water") in ("no", "conditional"):
        return False  # tehniskais ūdens (kapsētas, dārzi)
    return True


def slanis(kategorija):
    s = SLANI[kategorija]
    d = lejupieladet_slani(vaicajums(s["filtri"], timeout=60))
    if d is None:
        print(f"KĻŪDA: {kategorija} — Overpass neatbildēja; {s['fails']} nav mainīts", file=sys.stderr)
        return False
    features = []
    for el in d["elements"]:
        t = el.get("tags", {})
        koord = punkts(el)
        if not koord or not derigs(kategorija, t):
            continue
        ipasibas = {"kategorija": kategorija, "id": f"{el['type']}/{el['id']}", "nosaukums": nosaukums(kategorija, t),
                    "adrese": adrese(t)}
        ipasibas.update({k: t[k] for k in s["lauki"] if k in t})
        features.append({"type": "Feature", "geometry": {"type": "Point", "coordinates": koord}, "properties": ipasibas})
    if not features:
        print(f"KĻŪDA: {kategorija} — 0 punktu; {s['fails']} nav mainīts", file=sys.stderr)
        return False
    rakstit(MAPE / s["fails"], features)
    print(MAPE / s["fails"], kategorija, len(features))
    return True


def pamata():
    """Bankomāti un DUS (viens vaicājums, kā līdz šim) → osm_poi.geojson."""
    pec_taga = {v: k for k, v in KATEGORIJAS.items()}
    features = []
    d = lejupieladet(vaicajums(), iziet=False)
    if d is None:
        print(f"KĻŪDA: osm — Overpass neatbildēja; {IZEJA.name} nav mainīts", file=sys.stderr)
        return False
    for el in d["elements"]:
        tagi = el.get("tags", {})
        kategorija = next((pec_taga[(k, tagi[k])] for k in ("amenity",) if (k, tagi.get(k)) in pec_taga), None)
        koord = punkts(el)
        if not kategorija or not koord:
            continue
        ipasibas = {"kategorija": kategorija, "id": f"{el['type']}/{el['id']}", "adrese": adrese(tagi)}
        ipasibas.update({k: tagi[k] for k in LAUKI if k in tagi})
        features.append({"type": "Feature", "geometry": {"type": "Point", "coordinates": koord}, "properties": ipasibas})
    rakstit(IZEJA, features)
    skaits = {}
    for f in features:
        skaits[f["properties"]["kategorija"]] = skaits.get(f["properties"]["kategorija"], 0) + 1
    print(IZEJA, skaits)
    return True


def main():
    izveletie = sys.argv[1:] or ["osm", *SLANI]
    nezinami = [x for x in izveletie if x != "osm" and x not in SLANI]
    if nezinami:
        sys.exit(f"nezināms slānis: {nezinami}; der: osm {' '.join(SLANI)}")
    kludas = []
    for i, x in enumerate(izveletie):
        if i:
            time.sleep(5)  # Overpass: ne vairāk par vienu vaicājumu vienlaikus, īsa pauze starp tiem
        if not (pamata() if x == "osm" else slanis(x)):
            kludas.append(x)
    if kludas:
        sys.exit(f"Neizdevās: {' '.join(kludas)}")


if __name__ == "__main__":
    main()
