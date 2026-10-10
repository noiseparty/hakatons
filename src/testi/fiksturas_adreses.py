"""Fiksturas adrešu kartīšu testam (notes/kartites-4.md): 8 adreses × /api/adreses, /pludi, /udens, /prognoze,
/bridinajumi (+ /pasvaldiba, /augsne, /noverojumi) bez slodzes map.repo.lv.

    uv run --no-project --python 3.12 --with "psycopg[binary]" src/testi/fiksturas_adreses.py [--dzivie 14]

Dzīvi (map.repo.lv, secīgi, ne vairāk par --dzivie GET; jau ierakstītos neprasa vēlreiz):
  /api/adreses?q=…&limit=1 — katra adrese tā, kā to sūta meklesana.js (bez komatiem), un "iela 99 Ogre" (variants, ko
                             meklesana.js mēģina neesošai "Nekāda iela 99, Ogre"); VZD adrešu tabula ir tikai VPS;
  /api/objekti?bbox=<pilsēta ±0,12° × ±0,2°>&lat&lon&limit=5000 — 5 pilsētām ārpus Ogres (Ogres kopa jau ir
                             api_objekti.json, bet tālāk par ~30–190 km tajā nav pieturu, aptieku, bankomātu u.c.).
Lokāli (karte_api.py funkcijas, bez DB; tās pašas atvērto datu adreses, ko lieto VPS):
  /api/bridinajumi (LVĢMC data.gov.lv; bez Meteoalarm rezerves), /api/prognoze (LVĢMC ikstundas prognoze),
  /api/udens (LVĢMC novērojumi + udens_slieksni.json), /api/pludi (LVĢMC WMS, kā VPS bez PostGIS kopijas),
  /api/augsne (Open-Meteo), /api/noverojumi (LVĢMC), /api/pasvaldiba (src/karte/dati/pasvaldibas.json; pašvaldība pēc
  /api/regioni taisnstūra: valstspilsēta, ja punkts tajā, citādi mazākais novads — VPS to nosaka pēc robežas).
Punkti: atrastās adreses un neatrasto adrešu vietvārda centrs (reģiona taisnstūra vidus, kā meklesana.js centrs()).
Rezultāts: src/testi/fiksturas/adreses/*.json, punkti/*.json, api_objekti_<pilsēta>.json (lokali.py --fiksturas).
"""
import argparse
import json
import pathlib
import sys
import time
import urllib.parse

SAKNE = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SAKNE / "src" / "demo"))
sys.path.insert(0, str(SAKNE / "src" / "karte" / "api"))
import lokali  # noqa: E402

FIKS = SAKNE / "src" / "testi" / "fiksturas"
ADRESES = ["Brīvības iela 12, Ogre", "Mednieku iela 9, Ogre", "Lielā iela 1, Jelgava", "Rīgas iela 5, Daugavpils",
           "Jūras iela 3, Ventspils", "Baznīcas iela 2, Cēsis", "Nekāda iela 99, Ogre", "Skolas iela 4a, Rēzekne"]
PAPILDU_VARIANTI = ["iela 99 Ogre"]  # meklesana.js mēģina īsākas virknes ap numuru (sk. atrastAdresi)
OGRE = (56.8162, 24.614)
JSON = "application/json; charset=utf-8"


def saglabat(fails, cels, statuss, dati):
    fails.parent.mkdir(parents=True, exist_ok=True)
    fails.write_text(json.dumps({"cels": cels, "statuss": statuss, "tips": JSON, "dati": dati}, ensure_ascii=False),
                     encoding="utf-8")


def dzivais(cels, fails):
    if fails.exists():
        return json.loads(json.loads(fails.read_text(encoding="utf-8"))["dati"])
    rez = lokali._live(cels)
    if rez is None:
        raise SystemExit(f"dzīvo GET limits beidzies: {cels}")
    statuss, _tips, dati = rez
    saglabat(fails, cels, statuss, dati.decode("utf-8"))
    return json.loads(dati)


def pasvaldiba_bbox(lat, lon):
    regioni = json.loads(json.loads((FIKS / "api_regioni.json").read_text(encoding="utf-8"))["dati"])
    ieks = [r for r in regioni if r["tips"] in ("valstspilseta", "novads") and r["bbox"][0] <= lon <= r["bbox"][2]
            and r["bbox"][1] <= lat <= r["bbox"][3]]
    ieks.sort(key=lambda r: (r["tips"] != "valstspilseta", (r["bbox"][2] - r["bbox"][0]) * (r["bbox"][3] - r["bbox"][1])))
    return ieks[0]["kods"] if ieks else None


def lokalie(lat, lon):
    import karte_api as k
    q = {"lat": [f"{lat:.5f}"], "lon": [f"{lon:.5f}"]}
    ll = f"lat={lat:.5f}&lon={lon:.5f}"
    k._lvgmc_stavoklis["ar_bridinajumiem"] = time.time()  # Meteoalarm rezerve vajag DB (novads pēc robežas) — ne šeit
    darbi = {
        "/api/bridinajumi": (ll, lambda: k.bridinajumi(q)),
        "/api/prognoze": (ll, lambda: k.prognoze(q)),
        "/api/udens": (ll + "&limit=3", lambda: k.udens({**q, "limit": ["3"]})),
        "/api/noverojumi": (ll + "&limit=8", lambda: k.noverojumi({**q, "limit": ["8"]})),
        "/api/augsne": (ll, lambda: k.augsne(q)),
        "/api/pludi": (ll, lambda: pludi(k, q)),
        "/api/pasvaldiba": (ll, lambda: pasvaldiba(k, lat, lon)),
    }
    for cels, (vaic, f) in darbi.items():
        fails = FIKS / "punkti" / f"{lokali._fails(cels).stem}__{lat:.5f}_{lon:.5f}.json"
        if fails.exists():
            continue
        try:
            atb, statuss = f(), 200
        except k.Kluda as e:
            atb, statuss = {"kluda": str(e)}, e.statuss
        if isinstance(atb, dict) and "_statuss" in atb:
            statuss = atb.pop("_statuss")
        saglabat(fails, f"{cels}?{vaic}", statuss, json.dumps(atb, ensure_ascii=False, default=str))
        print(f"  {cels}: {statuss}", flush=True)


def pludi(k, q):
    for _ in range(4):  # pirmā WMS pārbaude var atbildēt 202 (turpinās fonā)
        atb = k.pludi({**q, "wms": ["1"]})
        if atb.get("_statuss") != 202:
            return atb
        time.sleep(10)
    return atb


def pasvaldiba(k, lat, lon):
    kods = pasvaldiba_bbox(lat, lon)
    vaicat, k.vaicat = k.vaicat, lambda *_a, **_k: kods  # tikai šim izsaukumam: kods pēc taisnstūra, ne PostGIS
    try:
        return k.pasvaldiba({"lat": [str(lat)], "lon": [str(lon)]})
    finally:
        k.vaicat = vaicat


if __name__ == "__main__":
    a = argparse.ArgumentParser()
    a.add_argument("--dzivie", type=int, default=14, help="ne vairāk par N GET uz map.repo.lv")
    arg = a.parse_args()
    lokali.FIKSTURAS = FIKS
    lokali.IERAKSTIT = arg.dzivie
    punkti, neatrastas = {}, []
    for adr in ADRESES + PAPILDU_VARIANTI:
        q = " ".join(adr.replace(",", " ").split())  # kā meklesana.js: komati → atstarpes
        cels = "/api/adreses?" + urllib.parse.urlencode({"q": q, "limit": 1})
        rez = dzivais(cels, FIKS / "adreses" / f"{lokali.adreses_atslega(q)}.json")
        print(f"{adr}: {rez[0]['adrese'] + ' ' + str((rez[0]['lat'], rez[0]['lon'])) if rez else 'nav atrasta'}", flush=True)
        if rez:
            punkti[rez[0]["kods"]] = (float(rez[0]["lat"]), float(rez[0]["lon"]), adr.split(", ")[-1])
        elif adr in ADRESES:
            neatrastas.append(adr.split(", ")[-1])
    for lat, lon, pilseta in punkti.values():
        if lokali._attalums_m(lat, lon, *OGRE) > 20000:
            slug = lokali.adreses_atslega(pilseta)
            bbox = f"{lon - 0.2:.2f},{lat - 0.12:.2f},{lon + 0.2:.2f},{lat + 0.12:.2f}"
            fails = FIKS / f"api_objekti_{slug}.json"
            if not fails.exists():
                d = dzivais(f"/api/objekti?bbox={bbox}&lat={lat:.5f}&lon={lon:.5f}&limit=5000", fails)
                print(f"objekti {pilseta}: {len(d['features'])}{' (apgriezts)' if d.get('apgriezts') else ''}", flush=True)
    # Neatrastām adresēm kartīte rāda pēc vietvārda: punkts = reģiona taisnstūra centrs (kā meklesana.js centrs())
    regioni = json.loads(json.loads((FIKS / "api_regioni.json").read_text(encoding="utf-8"))["dati"])
    for pilseta in neatrastas:
        r = next((r for r in regioni if r["nosaukums"] == pilseta), None)
        if r:
            punkti["centrs " + pilseta] = ((r["bbox"][1] + r["bbox"][3]) / 2, (r["bbox"][0] + r["bbox"][2]) / 2, pilseta)
    for lat, lon, pilseta in punkti.values():
        print(f"lokāli {pilseta} {lat:.5f},{lon:.5f}", flush=True)
        lokalie(lat, lon)
    print(f"atlikuši dzīvie GET: {lokali.IERAKSTIT}")
