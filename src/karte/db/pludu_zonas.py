"""Plūdu riska zonas (LVĢMC 3. cikla applūstošās teritorijas 2026–2031) → lokāla kopija PostGIS tabulā pludu_zonas.

Kāpēc: /api/pludi līdz šim jautāja LVĢMC WMS (geo-dpps.viss.gov.lv) katrai adresei; serviss mēdz atbildēt 1–30 s
vai nemaz (2026-10-10 naktī: taimauti). Ar lokālu kopiju atbilde "vai adrese ir plūdu zonā" ir ~10 ms un nav
atkarīga no LVĢMC servisa.

Avots: ĢeoLatvija.lv ģeoprodukts 361 "3. cikla Latvijas plūdu postījumu vietu un plūdu riska kartes" (LVĢMC),
SHP faili (LKS-92 TM, EPSG:3059): pavasara pali, ledus sastrēgumi, jūras vējuzplūdi; atkārtošanās varbūtība
10 % (…_010_…), 1 % (…_100_…), 0,5 % (…_200_…). Faila lapā licence: CC BY-SA 4.0 (data.gov.lv kopā norādīts CC0 1.0).
Tie paši dati, ko rāda WMS slāņi PLUDU_SERVISI failā karte_api.py.

Divi soļi:

  1) lejupieladet (lokāli; vajag pyshp, shapely, pyproj):
       uv run --no-project --with pyshp --with shapely --with pyproj src/karte/db/pludu_zonas.py lejupieladet
     Lejupielādē 3 ZIP (~200 MB; atsākas no vietas, kur pārtrūka; 5 mēģinājumi, 60 s taimauts pieprasījumam) mapē
     --zip (noklusēti <tmp>/pludu_zonas_zip), vienkāršo kontūras (--pielaide 2 m), pārvērš uz WGS-84 (5 zīmes ≈ 1 m)
     un raksta src/karte/dati/pludu_zonas.geojson.gz (viens objekts rindā; tad PR). Noklusēti tikai 10 % un 1 %
     varbūtība (ar 0,5 % fails būtu > 40 MB); ~15 min.

  2) ieladet (VPS; tikai standarta bibliotēka + psycopg, ģeometriju apstrādā PostGIS):
       python3 src/karte/db/pludu_zonas.py ieladet [fails]
     Ielādē jaunā tabulā, sadala lielos poligonus (ST_Subdivide, ātrai ST_Intersects) un vienā transakcijā aizvieto
     pludu_zonas. Ja jaunajā failā ir < 90 % no iepriekšējā objektu skaita — atsakās (iznākuma kods 3), ja vien nav
     --piespiedu. Atjauno avoti.atjaunots avotam lvgmc-pludi-faili. Palaiž atjaunot_visu.sh, ja fails mainījies.
"""

import argparse
import gzip
import io
import json
import os
import re
import sys
import tempfile
import time
import urllib.request
import zipfile
from datetime import datetime, timezone

SAKNE = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
FAILS = os.path.join(SAKNE, "src", "karte", "dati", "pludu_zonas.geojson.gz")
AVOTS = "lvgmc-pludi-faili"
GEOPRODUKTS = "https://geolatvija.lv/api/v1/public/geoproducts/361"
GEOPRODUKTA_LAPA = "https://geolatvija.lv/main?geoProductId=361"
LICENCE = "CC BY-SA 4.0"
# Rezerve, ja ĢeoLatvija API nedod sarakstu: faila vārds → glabātuves saite (2026-09-18 versija)
ZIP_REZERVE = {
    "Pavasara_pali_3_cikls.zip": "https://geolatvija.lv/api/v1/storage/fa533609-3acc-4969-97d8-57e419578272",
    "Ledus_pludi_3_cikls.zip": "https://geolatvija.lv/api/v1/storage/b82375af-f20a-455a-b21d-d139e40b8e08",
    "Juras_pludi_3_cikls.zip": "https://geolatvija.lv/api/v1/storage/fdd15d06-10ce-4d3a-8cf5-8dfb4b094772",
}
VEIDI = {"Pavasara_pali": "pavasara pali", "Pavasara_pali_Salaca": "pavasara pali",
         "Ledus_pludi": "ledus sastrēgumi", "Juras_pludi": "jūras vējuzplūdi"}
VARBUTIBAS = {"010": "10", "100": "1", "200": "0.5"}  # atkārtošanās periods gados → varbūtība gadā, %
SHP_VARDS = re.compile(r"^(?P<veids>Pavasara_pali(?:_Salaca)?|Ledus_pludi|Juras_pludi)_(?P<p>010|100|200)_3_cikls\.shp$")
TAIMAUTS = 60
MEGINAJUMI = 5
UA = {"User-Agent": "map.repo.lv (hakatons, src/karte/db/pludu_zonas.py)"}


# ---------- 1) lejupielāde un pārveide (lokāli) ----------

def _pieprasit(url, galvenes=None):
    return urllib.request.urlopen(urllib.request.Request(url, headers={**UA, **(galvenes or {})}), timeout=TAIMAUTS)


def zip_saraksts():
    """{faila vārds: URL} no ĢeoLatvija publiskā API; ja tas neatbild — ZIP_REZERVE."""
    for meginajums in range(MEGINAJUMI):
        try:
            with _pieprasit(GEOPRODUKTS) as r:
                dati = json.load(r)
            faili = {a["displayName"]: a["url"] for f in dati.get("files", []) for a in f.get("attachments", [])
                     if a.get("displayName", "").endswith(".zip") and a.get("url")}
            if faili:
                return faili
        except Exception as e:  # noqa: BLE001
            print(f"  ĢeoLatvija API: {e} (mēģinājums {meginajums + 1})", file=sys.stderr)
            time.sleep(2 * (meginajums + 1))
    print("  ĢeoLatvija API nedod failu sarakstu — lieto zināmās saites", file=sys.stderr)
    return dict(ZIP_REZERVE)


def lejupieladet_zip(url, merkis):
    """Lejupielādē ar atsākšanu (HTTP Range) un mēģinājumiem; derīgu ZIP neielādē vēlreiz."""
    if os.path.exists(merkis) and zipfile.is_zipfile(merkis):
        print(f"  {os.path.basename(merkis)}: jau ir ({os.path.getsize(merkis) / 1e6:.0f} MB)")
        return
    dala = merkis + ".dala"
    for meginajums in range(MEGINAJUMI):
        jau = os.path.getsize(dala) if os.path.exists(dala) else 0
        try:
            with _pieprasit(url, {"Range": f"bytes={jau}-"} if jau else None) as r:
                if jau and r.status != 206:  # serveris neatbalsta Range — no sākuma
                    jau = 0
                with open(dala, "ab" if jau else "wb") as f:
                    while True:
                        gabals = r.read(1 << 20)
                        if not gabals:
                            break
                        f.write(gabals)
            if zipfile.is_zipfile(dala):
                os.replace(dala, merkis)
                print(f"  {os.path.basename(merkis)}: {os.path.getsize(merkis) / 1e6:.0f} MB")
                return
            raise OSError("fails nav derīgs ZIP")
        except Exception as e:  # noqa: BLE001
            print(f"  {os.path.basename(merkis)}: {e} (mēģinājums {meginajums + 1}/{MEGINAJUMI})", file=sys.stderr)
            if "ZIP" in str(e) and os.path.exists(dala):
                os.remove(dala)
            time.sleep(3 * (meginajums + 1))
    raise SystemExit(f"Neizdevās lejupielādēt {url}")


def _slanis(lasitajs, pielaide, cipari, wgs):
    """Viens SHP slānis → (virsotnes pirms, pēc, [MultiPolygon WGS-84]) — vektorizēti (shapely 2).

    Nevis shape(__geo_interface__) + make_valid + simplify katram objektam: jūras slānī ir objekti ar 160 000
    virsotnēm un 12 000 gredzeniem, kam tas ilgst minūtes. Tā vietā: katru gredzenu vienkāršo atsevišķi
    (Douglas-Peucker, pielaide m), ESRI virziens nosaka ārējo (pulksteņrādītāja virzienā) vai caurumu, caurumu
    piesaista mazākajam tā paša objekta ārējam gredzenam, kas satur tā pirmo punktu (STRtree). Ģeometrija var
    nebūt pilnīgi derīga (gredzeni vienkāršoti neatkarīgi) — ielādē to izlabo ST_MakeValid.
    """
    import numpy as np
    import shapely

    koord, gredzena_nr, objekta_nr = [], [], []
    g = 0
    for i, forma in enumerate(lasitajs.iterShapes()):
        if not forma.points:
            continue
        p = np.asarray(forma.points, dtype=float)
        robezas = list(forma.parts) + [len(p)]
        for a, b in zip(robezas[:-1], robezas[1:]):
            if b - a >= 4:
                koord.append(p[a:b])
                gredzena_nr.append(np.full(b - a, g))
                objekta_nr.append(i)
                g += 1
    if not koord:
        return 0, 0, []
    koord, gredzena_nr, objekta_nr = np.concatenate(koord), np.concatenate(gredzena_nr), np.asarray(objekta_nr)
    pirms = len(koord)

    linijas = shapely.simplify(shapely.linestrings(koord, indices=gredzena_nr), pielaide, preserve_topology=False)
    k, idx = shapely.get_coordinates(linijas, return_index=True)
    skaits = np.bincount(idx, minlength=len(linijas))
    labi = skaits >= 4                                      # sabrukuši gredzeni (< ~pielaide plati) izkrīt
    tur = labi[idx]
    k, idx = k[tur], idx[tur]
    jauns_nr = np.cumsum(labi) - 1                          # gredzenu numuri bez izkritušajiem
    lks = shapely.linearrings(k, indices=jauns_nr[idx])
    objekta_nr = objekta_nr[labi]
    caurums = shapely.is_ccw(lks)                           # ESRI: ārējie — pulksteņrādītāja virzienā
    laukums = shapely.area(shapely.polygons(lks))
    arejs = ~caurums & (laukums >= 1)                       # < 1 m² — rastra atlikums

    k = wgs(k)
    k = np.round(k, cipari)
    ringi = shapely.linearrings(k, indices=jauns_nr[idx])
    pec = len(k)

    ar_idx = np.flatnonzero(arejs)
    cr_idx = np.flatnonzero(caurums)
    piederiba = {}  # ārējā gredzena nr → [caurumu nr]
    if len(cr_idx) and len(ar_idx):
        koks = shapely.STRtree(shapely.polygons(ringi[ar_idx]))
        pirmie = shapely.get_point(ringi[cr_idx], 0)
        cauri, ari = koks.query(pirmie, predicate="intersects")
        labakais = {}
        for c, a in zip(cauri, ari):
            ci, ai = cr_idx[c], ar_idx[a]
            if objekta_nr[ci] != objekta_nr[ai]:
                continue
            if ci not in labakais or laukums[ai] < laukums[labakais[ci]]:
                labakais[ci] = ai
        for ci, ai in labakais.items():
            piederiba.setdefault(ai, []).append(ci)

    poligoni, pol_objekts = [], []
    for ai in ar_idx:
        poligoni.append(shapely.Polygon(ringi[ai], [ringi[c] for c in piederiba.get(ai, ())]))
        pol_objekts.append(objekta_nr[ai])
    if not poligoni:
        return pirms, pec, []
    pol_objekts = np.asarray(pol_objekts)
    kartiba = np.argsort(pol_objekts, kind="stable")
    _, grupas = np.unique(pol_objekts[kartiba], return_inverse=True)
    multi = shapely.multipolygons(np.asarray(poligoni, dtype=object)[kartiba], indices=grupas)
    return pirms, pec, list(multi)


def parveidot(zip_mape, pielaide, cipari, varbutibas, izvade):
    import numpy as np
    import shapefile  # pyshp
    from pyproj import Transformer
    from shapely.geometry import mapping

    uz_wgs = Transformer.from_crs(3059, 4326, always_xy=True)

    def wgs(xy):
        lon, lat = uz_wgs.transform(xy[:, 0], xy[:, 1])
        return np.column_stack([lon, lat])

    skaits, punkti_pirms, punkti_pec = 0, 0, 0
    tmp = izvade + ".tmp"
    with gzip.open(tmp, "wt", encoding="utf-8", compresslevel=9) as out:
        galva = {"type": "FeatureCollection", "name": "pludu_zonas",
                 "avots": "LVĢMC, 3. cikla Latvijas plūdu postījumu vietu un plūdu riska kartes (2026–2031)",
                 "datu_kopa": GEOPRODUKTA_LAPA, "licence": LICENCE,
                 "apstrade": f"src/karte/db/pludu_zonas.py: vienkāršots {pielaide} m (LKS-92 TM), WGS-84, {cipari} zīmes",
                 "izveidots": datetime.now(timezone.utc).isoformat(timespec="seconds")}
        out.write(json.dumps(galva, ensure_ascii=False)[:-1] + ', "features": [\n')
        pirmais = True
        for zip_fails in sorted(os.listdir(zip_mape)):
            if not zip_fails.endswith(".zip"):
                continue
            with zipfile.ZipFile(os.path.join(zip_mape, zip_fails)) as z:
                for vards in sorted(z.namelist()):
                    m = SHP_VARDS.match(os.path.basename(vards))
                    if not m or VARBUTIBAS[m["p"]] not in varbutibas:
                        continue
                    pamats = vards[:-4]
                    lasitajs = shapefile.Reader(shp=io.BytesIO(z.read(pamats + ".shp")),
                                                shx=io.BytesIO(z.read(pamats + ".shx")),
                                                dbf=io.BytesIO(z.read(pamats + ".dbf")))
                    veids, varb = VEIDI[m["veids"]], VARBUTIBAS[m["p"]]
                    sakums, n0 = time.monotonic(), skaits
                    pirms, pec, multi = _slanis(lasitajs, pielaide, cipari, wgs)
                    punkti_pirms, punkti_pec = punkti_pirms + pirms, punkti_pec + pec
                    ipasibas = {"veids": veids, "varbutiba": varb, "slanis": os.path.basename(pamats)}
                    for g in multi:
                        f = {"type": "Feature", "properties": ipasibas, "geometry": mapping(g)}
                        out.write(("" if pirmais else ",\n") + json.dumps(f, ensure_ascii=False, separators=(",", ":")))
                        pirmais = False
                        skaits += 1
                    print(f"  {os.path.basename(pamats)}: {skaits - n0} objekti ({veids}, {varb} %), "
                          f"{time.monotonic() - sakums:.0f} s", flush=True)
        out.write("\n]}\n")
    os.replace(tmp, izvade)
    print(f"{izvade}: {skaits} poligoni, virsotnes {punkti_pirms} → {punkti_pec}, {os.path.getsize(izvade) / 1e6:.1f} MB")


# ---------- 2) ielāde PostGIS (VPS) ----------

SHEMA = """
create table if not exists pludu_zonas (
  id        bigserial primary key,
  nr        int not null,             -- avota poligona nr. failā; lielie poligoni sadalīti vairākās rindās
  veids     text not null,            -- pavasara pali | ledus sastrēgumi | jūras vējuzplūdi
  varbutiba text not null,
  geom      geometry(MultiPolygon, 4326) not null
);
create index if not exists pludu_zonas_geom_idx on pludu_zonas using gist (geom);
grant select on pludu_zonas to map_api;
"""  # tas pats bloks ir src/karte/db/shema.sql


def lasit_objektus(fails):
    """Straumē GeoJSON, ko raksta parveidot (viens objekts rindā), — bez visa faila ielādes atmiņā."""
    with gzip.open(fails, "rt", encoding="utf-8") as f:
        for rinda in f:
            rinda = rinda.strip().rstrip(",")
            if rinda.startswith('{"type":"Feature"'):
                yield json.loads(rinda)


def ieladet(fails, dsn, piespiedu):
    import psycopg

    with psycopg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute(SHEMA)
        cur.execute("select count(distinct nr) from pludu_zonas")  # avota poligoni (rindas ir to gabali)
        iepr = cur.fetchone()[0]
        conn.commit()  # shēma atsevišķi: garajā ielādes transakcijā pludu_zonas netiek bloķēta līdz pašām beigām
        cur.execute("drop table if exists pludu_zonas_jauns")
        # sava secība (ne "like … including defaults": vecās tabulas secība pazūd kopā ar to)
        cur.execute("""create table pludu_zonas_jauns (id bigserial primary key, nr int not null, veids text not null,
                       varbutiba text not null, geom geometry(MultiPolygon, 4326) not null)""")
        cur.execute("create temp table pludu_ievade (nr int, veids text, varbutiba text, gj text) on commit drop")
        n = 0
        with cur.copy("copy pludu_ievade (nr, veids, varbutiba, gj) from stdin") as cp:
            for f in lasit_objektus(fails):
                p = f["properties"]
                cp.write_row((n, p["veids"], p["varbutiba"], json.dumps(f["geometry"], separators=(",", ":"))))
                n += 1
        if n == 0:
            raise SystemExit(f"{fails}: nav neviena objekta")
        if iepr and n < 0.9 * iepr and not piespiedu:
            print(f"BRĪDINĀJUMS: {n} objekti < 90 % no iepriekšējiem {iepr}; tabula netiek aizvietota (--piespiedu)",
                  file=sys.stderr)
            conn.rollback()
            return 3
        # ST_MakeValid → tikai poligoni → gabali ≤ 256 virsotnes (ST_Intersects pret lielu upes poligonu ir lēns)
        cur.execute("""
            insert into pludu_zonas_jauns (nr, veids, varbutiba, geom)
            select nr, veids, varbutiba, st_multi(gabals)
            from (select nr, veids, varbutiba,
                         st_subdivide(st_collectionextract(st_makevalid(st_setsrid(st_geomfromgeojson(gj), 4326)), 3),
                                      256) as gabals
                  from pludu_ievade) g
            where not st_isempty(gabals)""")
        cur.execute("select count(*) from pludu_zonas_jauns")
        gabali = cur.fetchone()[0]
        cur.execute("create index on pludu_zonas_jauns using gist (geom)")
        cur.execute("analyze pludu_zonas_jauns")
        cur.execute("drop table pludu_zonas")
        cur.execute("alter table pludu_zonas_jauns rename to pludu_zonas")
        cur.execute("alter index pludu_zonas_jauns_geom_idx rename to pludu_zonas_geom_idx")
        cur.execute("grant select on pludu_zonas to map_api")
        cur.execute("update avoti set atjaunots = now() where kods = %s", (AVOTS,))
    print(f"pludu_zonas: {n} poligoni → {gabali} gabali")
    return 0


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="darbiba", required=True)
    lj = sub.add_parser("lejupieladet", help="ĢeoLatvija SHP → src/karte/dati/pludu_zonas.geojson.gz (lokāli)")
    lj.add_argument("--zip", default=os.path.join(tempfile.gettempdir(), "pludu_zonas_zip"), help="ZIP mape (kešs)")
    lj.add_argument("--pielaide", type=float, default=2.0, help="vienkāršošana, m (noklusēti 2: 41,6 MB, 57 589 objekti)")
    lj.add_argument("--cipari", type=int, default=5, help="koordinātu zīmes aiz komata (5 ≈ 1 m)")
    lj.add_argument("--varbutibas", default="10,1", help="kuras varbūtības, %% (noklusēti 10,1; ar 0.5 fails > 40 MB)")
    lj.add_argument("--izvade", default=FAILS)
    il = sub.add_parser("ieladet", help="geojson.gz → PostGIS pludu_zonas (VPS)")
    il.add_argument("fails", nargs="?", default=FAILS)
    il.add_argument("--dsn", default=os.environ.get("MAP_DB_OWNER_DSN"))
    il.add_argument("--piespiedu", action="store_true", help="aizvietot arī tad, ja objektu ir < 90 %% no iepriekšējā")
    a = p.parse_args()
    for straume in (sys.stdout, sys.stderr):  # Windows konsole: garumzīmes
        straume.reconfigure(encoding="utf-8", errors="replace")

    if a.darbiba == "lejupieladet":
        os.makedirs(a.zip, exist_ok=True)
        saraksts = zip_saraksts()
        for vards in ZIP_REZERVE:
            url = saraksts.get(vards) or ZIP_REZERVE[vards]
            lejupieladet_zip(url, os.path.join(a.zip, vards))
        parveidot(a.zip, a.pielaide, a.cipari, set(a.varbutibas.split(",")), a.izvade)
        return 0
    if not a.dsn:
        sys.exit("Nav MAP_DB_OWNER_DSN (skat. /etc/hakatons/map.env)")
    return ieladet(a.fails, a.dsn, a.piespiedu)


if __name__ == "__main__":
    sys.exit(main())
