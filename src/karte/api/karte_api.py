"""map.repo.lv API: lasa datubāzi `map` un atgriež JSON / GeoJSON. Caddy to pieslēdz zem /api/.

Galapunkti:
  GET /api/kategorijas                 slāņi ar objektu skaitu un to avotiem
  GET /api/avoti                       datu avoti: izdevējs, licence, saites, skaits, ielādes laiks
  GET /api/regioni                     pašvaldības un pilsētas (bez ģeometrijas, ar bbox)
  GET /api/regioni/<kods>              reģiona robeža (GeoJSON Feature, vienkāršota)
  GET /api/objekti?kategorijas=a,b&regions=<kods>&lat=..&lon=..&limit=..
                                       punkti (GeoJSON); ar lat/lon sakārtoti pēc attāluma
  GET /api/adreses?q=brivibas 15 ogre&limit=8
                                       adrešu meklēšana (VZD); bez garumzīmēm, pēc vārdu daļām
  GET /api/bridinajumi?lat=..&lon=..   LVĢMC hidrometeoroloģiskie brīdinājumi (spēkā esošie); ar lat/lon —
                                       vai brīdinājums attiecas uz šo vietu (attiecas)
                                       ?poligoni=1 — arī brīdinājumu apgabali [[lat, lon], ...] (zonas.js)
  GET /api/pludi?lat=..&lon=..         vai vieta ir plūdu riska zonā (LVĢMC 3. cikla kartes, WMS GetFeatureInfo)
  GET /api/udens?lat=..&lon=..&limit=3 tuvākās LVĢMC hidroloģiskās stacijas ar ūdens līmeni un izmaiņu 24 h
                                       + prognoze 7 dienām (LVĢMC hidroloģiskās prognozes, kešs 1 h)
  GET /api/adreses/tuvaka?lat=..&lon=.. tuvākā VZD adrese (≤ 300 m) atrašanās vietai
  GET /api/pasvaldiba?lat=..&lon=..    pašvaldība punktā: CA plāns, tīmekļvietne, VPVKAC tālrunis (teksts)
  GET /api/prognozes                   "Prognoze / ziņas": LVĢMC prognozes apdzīvotām vietām (3 dienas) apkopotas pa
                                       novadiem + spēkā esošie brīdinājumi ar poligoniem; ziņu lente pa plānošanas reģioniem
  GET /api/prognozes/robezas           novadu un valstspilsētu robežas (vienkāršotas) kartes iekrāsošanai
  GET /api/zibens                      zibens pēdējās 30 min (FMI, CC BY 4.0) + LVĢMC 24 h zibens režģis (CC0, kavējas 2–3 h)
  GET /api/augsne?lat=..&lon=..        nokrišņi pēdējās 26 dienās + augsnes mitrums (Open-Meteo, CC BY 4.0; nav brīdinājums)
  GET /api/marsruts?no=lat,lon&uz=lat,lon&veids=kajam|auto&izvairities=c:lat,lon,r|lat,lon;lat,lon;…
                                       maršruts (FOSSGIS OSRM, OSM ODbL), kas apiet zonas un spēkā esošus LVC slēgumus
  GET /api/veseliba                    pārbaude
  GET /api/celi?bbox=..|lat=..&lon=..&r=5000
                                       ceļu slēgumi, negadījumi, remontdarbi, slidens ceļš (LVC DATEX II caur NAP, CC0)
  GET /api/satiksme                    satiksme pa zonām (pašvaldības), slidenā ceļa vietas, robežu gaidīšana (NAP, CC0)
  POST /api/meklejumi {vaicajums, atpazits, klikskis}
                                       biežāk meklētā skaitītājs (tikai atpazīti vaicājumi, bez lietotāja datiem); 204
  GET /api/meklejumi/top?n=3           biežāk meklētie pēdējās 14 dienās (kešs 60 s)
  GET /api/statuss                     statusa lapa: vietnes, API un datu avotu stāvoklis, 24 h pa 15 min, 7 dienu pieejamība

Brīdinājumi, plūdi un ūdens līmenis nāk tieši no atvērto datu avotiem (bez datubāzes), kešoti atmiņā.

Palaišana: MAP_DB_DSN=postgresql://map_api:...@127.0.0.1/map python3 karte_api.py [ports]
Tikai standarta bibliotēka + psycopg 3 (Ubuntu: python3-psycopg).
"""

import csv
import io
import json
import math
import os
import re
import sys
import threading
import time
import unicodedata
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

import psycopg

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "db"))
import udens_limenis  # noqa: E402  (src/karte/db/udens_limenis.py)

DSN = os.environ.get("MAP_DB_DSN", "")
MAX_LIMIT = 20000
KODS = re.compile(r"^[A-Za-z0-9_-]{1,40}$")


class Kluda(Exception):
    def __init__(self, statuss, teksts):
        super().__init__(teksts)
        self.statuss = statuss


def vaicat(sql, params=(), timeout="10s"):
    with psycopg.connect(DSN, connect_timeout=5) as conn, conn.cursor() as cur:
        cur.execute(f"set statement_timeout = '{timeout}'")
        cur.execute(sql, params)
        rinda = cur.fetchone()
        return rinda[0] if rinda else None


def kategorijas(_q):
    return vaicat(
        """select coalesce(json_agg(k order by kartiba, nosaukums), '[]') from (
             select k.kods, k.nosaukums, k.grupa, k.krasa, k.kartiba, count(o.id)::int as skaits,
                    coalesce(array_agg(distinct o.avots) filter (where o.avots is not null), '{}') as avoti
             from kategorijas k left join objekti o on o.kategorija = k.kods
               and (o.derigs_lidz is null or o.derigs_lidz > now())
             group by k.kods) k"""
    )


def avoti(_q):
    return vaicat(
        """select coalesce(json_agg(a order by a.kartiba), '[]') from (
             select a.kods, a.nosaukums, a.izdevejs, a.licence, a.licences_url, a.atverts, a.datu_kopa_url,
                    a.lejupielade, a.lietojums, a.piezime, a.kartiba,
                    (select count(*) from objekti o where o.avots = a.kods)::int as skaits,
                    (select max(atjaunots) from objekti o where o.avots = a.kods) as ieladets
             from avoti a) a"""
    )


def regioni(_q):
    return vaicat(
        """select coalesce(json_agg(r order by r.nosaukums), '[]') from (
             select kods, nosaukums, tips, novads_kods,
                    json_build_array(round(st_xmin(b)::numeric, 5), round(st_ymin(b)::numeric, 5),
                                     round(st_xmax(b)::numeric, 5), round(st_ymax(b)::numeric, 5)) as bbox
             from (select *, st_envelope(geom)::box2d as b from regioni) x) r"""
    )


def regions(kods):
    if not KODS.match(kods):
        raise Kluda(400, "nederīgs kods")
    rez = vaicat(
        """select json_build_object('type', 'Feature', 'id', kods,
                  'properties', json_build_object('kods', kods, 'nosaukums', nosaukums, 'tips', tips),
                  'geometry', st_asgeojson(geom_vienk, 5)::json)
           from regioni where kods = %s""",
        (kods,),
    )
    if rez is None:
        raise Kluda(404, "reģions nav atrasts")
    return rez


def _skaitlis(q, vards, min_v, max_v):
    if vards not in q:
        return None
    try:
        v = float(q[vards][0])
    except ValueError:
        raise Kluda(400, f"{vards}: nav skaitlis") from None
    if not min_v <= v <= max_v:
        raise Kluda(400, f"{vards}: ārpus robežām")
    return v


def objekti(q):
    kategorijas_ = [k for k in ",".join(q.get("kategorijas", [""])).split(",") if k]
    if any(not KODS.match(k) for k in kategorijas_):
        raise Kluda(400, "nederīga kategorija")
    regions_ = q.get("regions", [""])[0]
    if regions_ and not KODS.match(regions_):
        raise Kluda(400, "nederīgs reģions")
    lat = _skaitlis(q, "lat", -90, 90)
    lon = _skaitlis(q, "lon", -180, 180)
    if (lat is None) != (lon is None):
        raise Kluda(400, "vajag gan lat, gan lon")
    limit = int(_skaitlis(q, "limit", 1, MAX_LIMIT) or 5000)

    lieto_vietu = lat is not None
    return vaicat(
        """with x as (
             select o.id, o.kategorija, o.nosaukums, o.adrese, o.ipasibas, o.avots,
                    o.pasvaldiba_kods, o.pilseta_kods, o.geom,
                    case when %(vieta)s then round(st_distance(o.geom::geography,
                         st_setsrid(st_makepoint(%(lon)s, %(lat)s), 4326)::geography))::int end as attalums_m
             from objekti o
             where (o.derigs_lidz is null or o.derigs_lidz > now())
               and (cardinality(%(kat)s::text[]) = 0 or o.kategorija = any(%(kat)s::text[]))
               and (%(reg)s = '' or o.pasvaldiba_kods = %(reg)s or o.pilseta_kods = %(reg)s)
             order by case when %(vieta)s then o.geom <-> st_setsrid(st_makepoint(%(lon)s, %(lat)s), 4326) end,
                      o.id
             limit %(limit)s)
           select json_build_object('type', 'FeatureCollection', 'features', coalesce(json_agg(
                    json_build_object('type', 'Feature', 'id', id,
                      'geometry', st_asgeojson(geom, 6)::json,
                      'properties', json_build_object('kategorija', kategorija, 'nosaukums', nosaukums,
                        'adrese', adrese, 'avots', avots, 'pasvaldiba', pasvaldiba_kods, 'pilseta', pilseta_kods,
                        'attalums_m', attalums_m, 'ipasibas', ipasibas))
                    order by attalums_m nulls last, id), '[]'))
           from x""",
        {"vieta": lieto_vietu, "lat": lat or 0, "lon": lon or 0, "kat": kategorijas_, "reg": regions_, "limit": limit},
    )


def _vienkarsot(teksts):
    """Mazie burti bez garumzīmēm, kā adreses.meklesanai (lower(unaccent(...)))."""
    return "".join(c for c in unicodedata.normalize("NFD", teksts.lower()) if not unicodedata.combining(c))


def adreses(q):
    vardi = [v for v in re.split(r"[\s,]+", _vienkarsot(q.get("q", [""])[0][:100])) if v][:6]
    if not any(len(v) >= 3 for v in vardi):
        raise Kluda(400, "q: vajag vismaz vienu vārdu ar 3+ burtiem")
    limit = int(_skaitlis(q, "limit", 1, 20) or 8)
    raksti = ["%" + re.sub(r"([\\%_])", r"\\\1", v) + "%" for v in vardi]
    # mājas numurs ("15" → "15", "15A"; ne "115", "k-15" vai "LV-5015") — augstāk sarakstā
    numuri = [r"(^|\s)" + v + r"[a-z]?(,|\s|$)" for v in vardi if v.isdigit()]
    return vaicat(
        f"""select coalesce(json_agg(a), '[]') from (
              select kods, adrese, round(st_y(geom)::numeric, 6) as lat, round(st_x(geom)::numeric, 6) as lon
              from adreses
              where {" and ".join(["meklesanai like %s"] * len(raksti))}
              order by meklesanai ~ all(%s::text[]) desc, meklesanai like %s desc,
                       similarity(meklesanai, %s) desc, length(adrese), adrese
              limit %s) a""",
        (*raksti, numuri, vardi[0] + "%", " ".join(vardi), limit),
        timeout="2s",
    )


# ---- Ārējie atvērtie dati bez datubāzes: lejupielāde + kešs atmiņā ----

_kesa = {}
_kesas_slots = threading.Lock()
_atslegu_sloti = {}  # atslēga → Lock: vienlaicīgi pieprasījumi gaida vienu lejupielādi


def _kesots(atslega, sekundes, funkcija):
    """Atgriež kešoto vērtību; ja avots nav pieejams, labāk novecojusi nekā nekāda (un nākamais mēģinājums
    pēc minūtes, nevis katrā pieprasījumā). sekundes var būt funkcija (vērtība → sekundes)."""
    ilgums = sekundes if callable(sekundes) else (lambda _v: sekundes)

    def no_kesas():
        with _kesas_slots:
            ieraksts = _kesa.get(atslega)
        return ieraksts, bool(ieraksts) and time.time() - ieraksts[0] < ilgums(ieraksts[1])

    ieraksts, svaigs = no_kesas()
    if svaigs:
        return ieraksts[1]
    with _kesas_slots:
        slots = _atslegu_sloti.setdefault(atslega, threading.Lock())
    with slots:
        ieraksts, svaigs = no_kesas()
        if svaigs:
            return ieraksts[1]
        try:
            vertiba = funkcija()
        except Exception as e:  # tīkls, formāts
            if ieraksts:
                with _kesas_slots:
                    _kesa[atslega] = (time.time() - ilgums(ieraksts[1]) + 60, ieraksts[1])
                return ieraksts[1]
            if isinstance(e, Kluda):
                raise
            raise Kluda(503, "avots pašlaik nav pieejams") from e
        with _kesas_slots:
            if len(_kesa) > 20000:
                _kesa.clear()
                _atslegu_sloti.clear()
            _kesa[atslega] = (time.time(), vertiba)
        return vertiba


def _lejupieladet(url, timeout=20):
    pieprasijums = urllib.request.Request(url, headers={"User-Agent": "map.repo.lv (hakatons, karte_api.py)"})
    with urllib.request.urlopen(pieprasijums, timeout=timeout) as r:
        return r.read()


def _vieta(q, obligata=True):
    lat = _skaitlis(q, "lat", 55, 59)
    lon = _skaitlis(q, "lon", 20, 29)
    if (lat is None) != (lon is None) or (obligata and lat is None):
        raise Kluda(400, "vajag lat un lon (Latvijā)")
    return lat, lon


def _attalums_m(lat1, lon1, lat2, lon2):
    f1, f2 = math.radians(lat1), math.radians(lat2)
    a = math.sin((f2 - f1) / 2) ** 2 + math.cos(f1) * math.cos(f2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2
    return round(2 * 6371000 * math.asin(math.sqrt(a)))


# LVĢMC "Hidrometeoroloģiskie brīdinājumi", data.gov.lv, CC0 1.0. Laiks — Latvijas vietējais.
BRIDINAJUMI = "https://data.gov.lv/dati/dataset/c971bd44-5a51-46fb-9343-495fb1006287/resource"
BRIDINAJUMI_META = BRIDINAJUMI + "/59c111fb-8c9a-4a63-8284-0a64a2920681/download/bridinajumu_metadata.csv"
BRIDINAJUMI_POLIGONI = BRIDINAJUMI + "/01dc7d3c-34e5-4cc3-8f1a-aaf022872a02/download/bridinajumu_poligoni.csv"
BRIDINAJUMU_LIMENI = {"dzeltens": 1, "oranžs": 2, "oranzs": 2, "sarkans": 3}


def _riga_tagad():
    try:
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo("Europe/Riga")).replace(tzinfo=None)
    except Exception:  # bez tzdata (Windows): vasaras laiks UTC+3, ziemā UTC+2 (aptuveni)
        utc = datetime.now(timezone.utc)
        return (utc + timedelta(hours=3 if 3 < utc.month < 11 else 2)).replace(tzinfo=None)


def _csv(url):
    return list(csv.DictReader(io.StringIO(_lejupieladet(url).decode("utf-8-sig"))))


def _lv_laiks(teksts):
    return datetime.strptime(teksts, "%Y.%m.%d %H:%M:%S") if teksts.strip() else None


def _bridinajumi_dati():
    poligoni = {}  # brīdinājums -> poligons -> [(npk, lat, lon)]
    for r in _csv(BRIDINAJUMI_POLIGONI):
        poligoni.setdefault(r["WEATHER_WARNING_EV_ID"], {}).setdefault(r["POLIGON_ID"], []).append(
            (int(r["NPK"]), float(r["LAT"]), float(r["LON"])))
    saraksts = []
    for r in _csv(BRIDINAJUMI_META):
        saraksts.append({
            "id": r["WEATHER_WARNING_EV_ID"],
            "nr": r["WARNING_NO"],
            "krasa": r["INTENSITY_LV"].strip(),
            "limenis": BRIDINAJUMU_LIMENI.get(r["INTENSITY_LV"].strip().lower(), 1),
            "paradiba": r["PARADIBA"].strip(),
            "regioni": r["REGIONS"].strip(),
            "no": _lv_laiks(r["TIME_FROM"]),
            "lidz": _lv_laiks(r["TIME_TILL"]),
            "teksts": r["TEKSTS_LV"].strip(),
            "riski": r["RISKS_LV"].strip(),
            "poligoni": [[(lat, lon) for _, lat, lon in sorted(p)]
                         for p in poligoni.get(r["WEATHER_WARNING_EV_ID"], {}).values()],
        })
    return saraksts


def _punkts_poligona(lat, lon, poligons):
    iekša = False
    j = len(poligons) - 1
    for i in range(len(poligons)):
        (yi, xi), (yj, xj) = poligons[i], poligons[j]
        if (yi > lat) != (yj > lat) and lon < (xj - xi) * (lat - yi) / (yj - yi) + xi:
            iekša = not iekša
        j = i
    return iekša


def bridinajumi(q):
    lat, lon = _vieta(q, obligata=False)
    ar_poligoniem = q.get("poligoni", [""])[0] == "1"  # zonas.js zīmē brīdinājumu apgabalus kartē
    tagad = _riga_tagad()
    rez = []
    for b in _kesots("bridinajumi", 600, _bridinajumi_dati):
        if b["lidz"] and b["lidz"] < tagad:
            continue
        rez.append({
            **{k: v for k, v in b.items() if k != "poligoni" or ar_poligoniem},
            "no": b["no"].isoformat() if b["no"] else None,
            "lidz": b["lidz"].isoformat() if b["lidz"] else None,
            "attiecas": any(_punkts_poligona(lat, lon, p) for p in b["poligoni"]) if lat is not None else None,
        })
    rez.sort(key=lambda b: (-b["limenis"], b["no"] or ""))
    return {"avots": "lvgmc-bridinajumi", "laiks_lv": tagad.isoformat(timespec="minutes"), "bridinajumi": rez}


# Plūdu riska zonas: LVĢMC "3. cikla Latvijas plūdu postījumu vietu un plūdu riska kartes" (2026–2031), CC0 1.0,
# WMS caur ĢeoLatvija.lv (geo-dpps.viss.gov.lv). Slāņa nr → atkārtošanās varbūtība gadā, %.
PLUDU_WMS = "https://geo-dpps.viss.gov.lv/api/DPPSPackage/client/"
PLUDU_SERVISI = [
    ("pavasara pali", "3._cikla_L_557_7iFPTq/b7ad025f-833a-4b4f-a845-d5cec9d24092", {"3": 10, "2": 10, "1": 1, "0": 0.5}),
    ("ledus sastrēgumi", "3._cikla_L_558_jIS73E/3322e012-8cb3-4a4c-8acf-a467e25a17b3", {"2": 10, "1": 1, "0": 0.5}),
    ("jūras vējuzplūdi", "3._cikla_L_556_karVbb/cc6f2ed3-dbfb-42d0-98e1-4d9f10f57fea", {"2": 10, "1": 1, "0": 0.5}),
]
_pludu_pavedieni = ThreadPoolExecutor(max_workers=6)
_pludu_rinda = [0]  # cik WMS pieprasījumu gaida vai iet; virs PLUDU_MAX_RINDA — 503, nevis bezgalīga rinda
PLUDU_MAX_RINDA = 30


def _pludu_serviss(veids, cels, slani, lat, lon):
    d = 0.0002  # ~20 m
    parametri = {
        "service": "WMS", "version": "1.3.0", "request": "GetFeatureInfo", "styles": "", "crs": "EPSG:4326",
        "layers": ",".join(slani), "query_layers": ",".join(slani), "info_format": "application/geojson",
        "bbox": f"{lat - d},{lon - d},{lat + d},{lon + d}", "width": 11, "height": 11, "i": 5, "j": 5,
        "feature_count": 10,
    }
    url = PLUDU_WMS + cels + "?" + "&".join(f"{k}={v}" for k, v in parametri.items())
    atrasti = json.loads(_lejupieladet(url, timeout=25)).get("features", [])
    varbutibas = [slani[f["layerName"]] for f in atrasti if f.get("layerName") in slani]
    return {"veids": veids, "varbutiba_proc": max(varbutibas)} if varbutibas else None


def pludi(q):
    lat, lon = _vieta(q)
    lat, lon = round(lat, 3), round(lon, 3)  # ~100 × 60 m; kešs pēc tā (mazāk pieprasījumu uz geo-dpps)

    def gatavs(_d):
        with _kesas_slots:
            _pludu_rinda[0] -= 1

    def parbaudit():
        with _kesas_slots:
            if _pludu_rinda[0] + len(PLUDU_SERVISI) > PLUDU_MAX_RINDA:
                raise Kluda(503, "plūdu pārbaude pārslogota, mēģiniet pēc brīža")
            _pludu_rinda[0] += len(PLUDU_SERVISI)
        darbi = [_pludu_pavedieni.submit(_pludu_serviss, v, c, s, lat, lon) for v, c, s in PLUDU_SERVISI]
        for d in darbi:
            d.add_done_callback(gatavs)
        veidi, kludas = [], 0
        for d in darbi:
            try:
                r = d.result()
            except Exception:
                kludas += 1
                continue
            if r:
                veidi.append(r)
        if kludas == len(darbi):
            raise RuntimeError("neviens plūdu WMS neatbild")
        veidi.sort(key=lambda v: -v["varbutiba_proc"])
        return {"avots": "lvgmc-pludi", "zona": bool(veidi), "veidi": veidi, "nepilnigi": kludas > 0}

    # serviss mēdz atbildēt 1–30 s (taimauts 25 s); ja kāds neatbildēja, atbilde ir nepilnīga un to kešojam tikai 10 min
    return _kesots(("pludi", lat, lon), lambda v: 600 if v["nepilnigi"] else 86400, parbaudit)


def udens(q):
    lat, lon = _vieta(q)
    limit = int(_skaitlis(q, "limit", 1, 10) or 3)
    stacijas = _kesots("udens", 900, lambda: udens_limenis.stacijas(timeout=20))
    tagad = datetime.now(timezone.utc)
    rez = []
    for f in stacijas:
        p = f["properties"]
        slon, slat = f["geometry"]["coordinates"]
        laiks = datetime.fromisoformat(p["laiks"].replace("Z", "+00:00"))
        rez.append({**p, "lat": slat, "lon": slon, "attalums_m": _attalums_m(lat, lon, slat, slon),
                    "vecs": tagad - laiks > timedelta(hours=udens_limenis.DERIGS_H)})
    rez.sort(key=lambda s: s["attalums_m"])
    rez = rez[:limit]
    prognozes = {}
    if time.time() - _hidro_kluda[0] > 300:  # pēc kļūdas bez kešas 5 min nemēģina (lai /api/udens nekavējas)
        try:
            prognozes = _kesots("hidro_prognoze", 3600, _hidro_prognozes)
        except Kluda:
            _hidro_kluda[0] = time.time()
    for st in rez:
        st["prognoze"] = _hidro_prognoze_stacijai(prognozes.get(st["stacija"]), st)
    return {"avots": "lvgmc-hidro", "stacijas": rez}


# ---- Hidroloģiskā prognoze (LVĢMC "Hidroloģiskās prognozes", data.gov.lv, CC0): 14 dienas, katrai stacijai
# ūdens līmeņa procentiles (m LAS-2000,5). Pārrēķins uz cm virs posteņa "0": (m − nulle_m) × 100. ----
HIDRO_PROGNOZE = ("https://data.gov.lv/dati/dataset/5d9b0379-c0b8-4ce9-9094-7c30b5502433/resource/"
                  "a967bf11-139f-4040-84d6-ce7c68006a8b/download/hidro_forecast.csv")
HIDRO_PROGNOZE_DIENAS = 7
_hidro_kluda = [0.0]


def _hidro_prognozes():
    """stacija → {datums: (V95, V75, mediāna, V25, V5)} ūdens līmenim (UDLIM), m."""
    rez = {}
    for r in _csv(HIDRO_PROGNOZE):
        if r["PARAM"] != "UDLIM":
            continue
        try:
            vertibas = tuple(float(r[k]) for k in ("V95", "V75", "MEDIANA", "V25", "V5"))
        except (KeyError, ValueError):
            continue
        rez.setdefault(r["STATION_ID"], {})[r["DATUMS"][:10]] = vertibas
    return rez


def _hidro_prognoze_stacijai(dienas, st):
    """Prognoze pēc HIDRO_PROGNOZE_DIENAS dienām: mediāna un joslas cm (ja zināma posteņa nulle), izmaiņa un virziens
    pēc modeļa (starpība nav atkarīga no nulles)."""
    if not dienas:
        return None
    sodien = _riga_tagad().date()
    merka = (sodien + timedelta(days=HIDRO_PROGNOZE_DIENAS)).isoformat()
    datumi = sorted(dienas)
    merkis = merka if merka in dienas else (datumi[-1] if datumi[-1] < merka else None)
    sakums = sodien.isoformat() if sodien.isoformat() in dienas else datumi[0]
    if not merkis:
        return None
    v95, v75, med, v25, v5 = dienas[merkis]
    nulle = st.get("nulle_m")
    cm = (lambda m: round((m - nulle) * 100)) if nulle is not None else None
    # virziens pēc paša modeļa trajektorijas (mediāna pēc 7 dienām pret šodienu): salīdzinot ar mērījumu, iejauktos
    # modeļa nobīde (prognoze izdota iepriekšējā dienā), un "kāpj" varētu nozīmēt tikai to
    izmaina = round((med - dienas[sakums][2]) * 100)
    return {
        "datums": merkis, "dienas": (datetime.fromisoformat(merkis).date() - sodien).days,
        "mediana_cm": cm(med) if cm else None, "josla_50_cm": [cm(v75), cm(v25)] if cm else None,
        "josla_90_cm": [cm(v95), cm(v5)] if cm else None,
        "izmaina_cm": izmaina, "virziens": "kāpj" if izmaina >= 5 else "krīt" if izmaina <= -5 else "stabils",
        "avots": "lvgmc-hidro-prognoze",
    }


# ---- Prognoze / ziņas: /api/prognozes, /api/prognozes/robezas ----
# LVĢMC "Meteoroloģiskās prognozes apdzīvotām vietām" (data.gov.lv, CC0 1.0): 6427 vietas, 7 dienas. Vietas
# piesaistām novadam / valstspilsētai (PostGIS, tuvākais reģions), apkopojam pa dienām un izceļam to, kas
# pārsniedz mūsu sliekšņus (tuvināti LVĢMC brīdinājumu kritērijiem; tie NAV oficiāli brīdinājumi).
PROGNOZES = "https://data.gov.lv/dati/dataset/01519599-fd66-4d60-8735-51b1c294c417/resource"
PROGNOZU_VIETAS = PROGNOZES + "/f692fae6-99cd-4bee-95ec-f158a595873a/download/cities.csv"
PROGNOZU_DIENAS = PROGNOZES + "/4b8172da-9ea3-4206-81fe-d7023a6a1f78/download/forecast_cities_day.csv"
PROGNOZU_KODI = PROGNOZES + "/cd79bc98-b956-41f3-b428-5a2a11693784/download/weather_codes.csv"
PROGNOZU_AVOTS = {
    "nosaukums": "LVĢMC meteoroloģiskās prognozes apdzīvotām vietām", "licence": "CC0 1.0",
    "url": "https://data.gov.lv/dati/lv/dataset/meteorologiskas-prognozes-apdzivotam-vietam-jaunaka-datu-kopa",
}
BRIDINAJUMU_AVOTS = {
    "nosaukums": "LVĢMC hidrometeoroloģiskie brīdinājumi", "licence": "CC0 1.0",
    "url": "https://data.gov.lv/dati/lv/dataset/hidrometeorologiskie-bridinajumi",
}
# Plānošanas reģioni (MK 22.06.2021. noteikumi Nr. 418): novadi un valstspilsētas pēc nosaukuma regioni tabulā
PLANOSANAS_REGIONI = {
    "Kurzemē": ["Dienvidkurzemes novads", "Kuldīgas novads", "Saldus novads", "Talsu novads", "Tukuma novads",
                "Ventspils novads", "Liepāja", "Ventspils"],
    "Zemgalē": ["Aizkraukles novads", "Bauskas novads", "Dobeles novads", "Jelgavas novads", "Jēkabpils novads",
                "Jelgava"],
    "Vidzemē": ["Alūksnes novads", "Cēsu novads", "Gulbenes novads", "Limbažu novads", "Madonas novads",
                "Ogres novads", "Smiltenes novads", "Valkas novads", "Valmieras novads"],
    "Latgalē": ["Augšdaugavas novads", "Balvu novads", "Krāslavas novads", "Līvānu novads", "Ludzas novads",
                "Preiļu novads", "Rēzeknes novads", "Daugavpils", "Rēzekne"],
    "Rīgā un Pierīgā": ["Rīga", "Jūrmala", "Ādažu novads", "Ķekavas novads", "Mārupes novads", "Olaines novads",
                        "Ropažu novads", "Salaspils novads", "Saulkrastu novads", "Siguldas novads"],
}
# (parametrs, slieksnis, līmenis): 0 — ievērībai, 1 — ~ LVĢMC dzeltenais, 2 — ~ oranžais, 3 — ~ sarkanais
PROGNOZU_SLIEKSNI = {
    "brazmas": [(15, 0), (20, 1), (25, 2), (33, 3)],    # diennakts maks. brāzmas, m/s
    "nokrisni": [(10, 0), (15, 1), (30, 2), (50, 3)],   # diennakts nokrišņu summa, mm
    "karstums": [(27, 0), (30, 1), (33, 2)],             # maks. temperatūra, °C
    "sals": [(0, 0), (-20, 1), (-25, 2), (-30, 3)],      # min. temperatūra, °C (≤)
}
NEDELAS_DIENAS = ["pirmdien", "otrdien", "trešdien", "ceturtdien", "piektdien", "sestdien", "svētdien"]


def _prognozu_vietas():
    """CITY_ID → (nosaukums, lat, lon, reģiona kods). Reģions — novads vai valstspilsēta, kurā vieta ir (vai tuvākais)."""
    vietas = [r for r in _csv(PROGNOZU_VIETAS) if r["LAT"] and r["LON"]]
    piesaiste = vaicat(
        """select coalesce(json_object_agg(p.id, r.kods), '{}') from unnest(%s::text[], %s::float8[], %s::float8[])
             as p(id, lat, lon)
           cross join lateral (select kods from regioni where tips in ('novads', 'valstspilseta')
                               order by geom <-> st_setsrid(st_makepoint(p.lon, p.lat), 4326) limit 1) r""",
        ([v["CITY_ID"] for v in vietas], [float(v["LAT"]) for v in vietas], [float(v["LON"]) for v in vietas]),
        timeout="30s",
    )
    return {v["CITY_ID"]: (v["NOSAUKUMS"], float(v["LAT"]), float(v["LON"]), piesaiste.get(v["CITY_ID"]))
            for v in vietas}


def _prognozu_regioni():
    rindas = vaicat(
        """select coalesce(json_agg(json_build_object('kods', kods, 'nosaukums', nosaukums, 'bbox', json_build_array(
                  round(st_xmin(geom)::numeric, 4), round(st_ymin(geom)::numeric, 4),
                  round(st_xmax(geom)::numeric, 4), round(st_ymax(geom)::numeric, 4)))), '[]')
           from regioni where tips in ('novads', 'valstspilseta')""")
    pr = {n: p for p, nosaukumi in PLANOSANAS_REGIONI.items() for n in nosaukumi}
    return {r["kods"]: {**r, "planosanas_regions": pr.get(r["nosaukums"])} for r in rindas}


def _prognozu_dati():
    vietas = _kesots("prognozu_vietas", 86400, _prognozu_vietas)
    lauki = {"14": "brazmas", "17": "nokrisni", "15": "tmax", "16": "tmin", "18": "varbutiba", "20": "ikona"}
    vertibas = {}  # (datums, reģions) → lauks → [(vērtība, vietas nosaukums)]
    pieprasijums = urllib.request.Request(PROGNOZU_DIENAS, headers={"User-Agent": "map.repo.lv (hakatons, karte_api.py)"})
    with urllib.request.urlopen(pieprasijums, timeout=60) as atbilde:
        mainits = atbilde.headers.get("Last-Modified")
        # 16,6 MB: lasa plūsmā, nevis visu tekstu atmiņā
        for r in csv.DictReader(io.TextIOWrapper(atbilde, encoding="utf-8-sig")):
            lauks = lauki.get(r["PARA_ID"])
            vieta = vietas.get(r["CITY_ID"])
            if not lauks or not vieta or not vieta[3] or not r["VERTIBA"]:
                continue
            vertibas.setdefault((r["DATUMS"][:10], vieta[3]), {}).setdefault(lauks, []).append(
                (float(r["VERTIBA"]), vieta[0]))
    kopsavilkums = {}  # datums → reģions → rādītāji
    for (datums, kods), v in vertibas.items():
        def maks(lauks):
            return max(v.get(lauks, []), default=(None, None))
        ikonas = [int(x) for x, _ in v.get("ikona", [])]
        kopsavilkums.setdefault(datums, {})[kods] = {
            "brazmas": maks("brazmas")[0], "brazmas_vieta": maks("brazmas")[1],
            "nokrisni": maks("nokrisni")[0], "nokrisni_vieta": maks("nokrisni")[1],
            "tmax": maks("tmax")[0], "tmin": min(v.get("tmin", []), default=(None, None))[0],
            "varbutiba": maks("varbutiba")[0],
            "ikona": max(set(ikonas), key=ikonas.count) if ikonas else None,
            "vietas": len(v.get("tmax", [])),
        }
    try:
        kodi = {r["DIENA"]: r["APRAKSTS"] for r in _kesots("prognozu_kodi", 86400, lambda: _csv(PROGNOZU_KODI))}
    except Kluda:
        kodi = {}
    for regioni_ in kopsavilkums.values():
        for k in regioni_.values():
            k["laiks"] = kodi.get(str(k["ikona"]))
    return {"kopsavilkums": kopsavilkums, "mainits": mainits}


def _limenis(veids, vertiba):
    if vertiba is None:
        return None
    rez = None
    for slieksnis, limenis in PROGNOZU_SLIEKSNI[veids]:
        if (vertiba <= slieksnis) if veids == "sals" else (vertiba >= slieksnis):
            rez = limenis
    return rez


def _dienas_nosaukums(datums, sodien):
    d = datetime.strptime(datums, "%Y-%m-%d").date()
    starpiba = (d - sodien).days
    return "Šodien" if starpiba == 0 else "Rīt" if starpiba == 1 else "Parīt" if starpiba == 2 else \
        NEDELAS_DIENAS[d.weekday()].capitalize()


def _bbox(regioni_, kodi):
    kastes = [regioni_[k]["bbox"] for k in kodi if k in regioni_]
    return [min(b[0] for b in kastes), min(b[1] for b in kastes), max(b[2] for b in kastes), max(b[3] for b in kastes)] \
        if kastes else None


def _skaitlis_lv(x):
    return f"{x:.0f}" if abs(x) >= 10 or x == int(x) else f"{x:.1f}".replace(".", ",")


def _prognozu_zinas(dati, regioni_, sodien, dienas):
    """Ziņas pa plānošanas reģioniem: katrai dienai un parādībai — viena ziņa ar visiem skartajiem novadiem."""
    zinas = []
    paradibas = [
        ("brazmas", "brazmas", "Vējš", lambda v: f"brāzmas līdz {_skaitlis_lv(v)} m/s"),
        ("nokrisni", "nokrisni", "Nokrišņi", lambda v: f"nokrišņi līdz {_skaitlis_lv(v)} mm diennaktī"),
        ("karstums", "tmax", "Karstums", lambda v: f"gaisa temperatūra līdz +{_skaitlis_lv(v)} °C"),
        ("sals", "tmin", "Sals", lambda v: f"naktī {'salna, ' if v > -5 else 'sals, '}līdz {_skaitlis_lv(v)} °C"),
    ]
    for datums in dienas:
        diena = _dienas_nosaukums(datums, sodien)
        regionu_dati = dati["kopsavilkums"].get(datums, {})
        for veids, lauks, paradiba, apraksts in paradibas:
            for pr, nosaukumi in PLANOSANAS_REGIONI.items():
                skarti = []
                for kods, r in regioni_.items():
                    if r["planosanas_regions"] != pr or kods not in regionu_dati:
                        continue
                    lim = _limenis(veids, regionu_dati[kods][lauks])
                    if lim is not None:
                        skarti.append((lim, regionu_dati[kods][lauks], kods))
                if not skarti:
                    continue
                limenis = max(s[0] for s in skarti)
                ekstrems = (min if veids == "sals" else max)(s[1] for s in skarti)
                kodi = [s[2] for s in sorted(skarti, key=lambda s: s[1], reverse=veids != "sals")]
                vieta_lauks = {"brazmas": "brazmas_vieta", "nokrisni": "nokrisni_vieta"}.get(lauks)
                virsotne = next((regionu_dati[k] for k in kodi if regionu_dati[k][lauks] == ekstrems), {})
                nosaukumi_ = [regioni_[k]["nosaukums"].replace(" novads", " nov.") for k in kodi]
                zinas.append({
                    "veids": "prognoze", "paradiba": paradiba, "limenis": limenis, "datums": datums, "diena": diena,
                    "virsraksts": f"{diena} {pr} {apraksts(ekstrems)}",
                    "teksts": ("Visvairāk: " + virsotne[vieta_lauks] + ". " if vieta_lauks and virsotne.get(vieta_lauks)
                               else "") + "Skartie: " + ", ".join(nosaukumi_[:6]) +
                              (f" un vēl {len(nosaukumi_) - 6}" if len(nosaukumi_) > 6 else "") +
                              ("" if nosaukumi_[min(len(nosaukumi_), 6) - 1].endswith(".") and len(nosaukumi_) <= 6 else "."),
                    "regioni": kodi, "bbox": _bbox(regioni_, kodi), "avots": PROGNOZU_AVOTS,
                })
    return zinas


def _vienkarsot_liniju(punkti, pielaide=0.01):
    """Ramera–Duglasa–Pekera vienkāršošana (pielaide grādos, ~1 km). Brīdinājums "Latvija" ir ~42 000 virsotņu."""
    if len(punkti) < 4:
        return punkti
    paturet = {0, len(punkti) - 1}
    darbi = [(0, len(punkti) - 1)]
    while darbi:
        a, b = darbi.pop()
        (y1, x1), (y2, x2) = punkti[a], punkti[b]
        garums = math.hypot(x2 - x1, y2 - y1)
        talakais, max_d = None, pielaide
        for i in range(a + 1, b):
            y, x = punkti[i]
            d = abs((x2 - x1) * (y1 - y) - (x1 - x) * (y2 - y1)) / garums if garums else math.hypot(x - x1, y - y1)
            if d > max_d:
                talakais, max_d = i, d
        if talakais is not None:
            paturet.add(talakais)
            darbi += [(a, talakais), (talakais, b)]
    return [punkti[i] for i in sorted(paturet)]


def _bridinajumu_skartie(b, vietas):
    """Brīdinājuma vienkāršotie poligoni un novadi, kuros ir kāda prognožu vieta poligonā (kešots pēc id)."""
    def aprekinat():
        poligoni = [_vienkarsot_liniju(p) for p in b["poligoni"]]
        return poligoni, sorted({v[3] for v in vietas.values() if v[3] and any(
            _punkts_poligona(v[1], v[2], p) for p in poligoni)})
    return _kesots(("bridinajuma_novadi", b["id"], len(vietas)), 86400, aprekinat)


def _bridinajumu_zinas(regioni_, vietas, tagad):
    zinas, poligoni = [], []
    for b in _kesots("bridinajumi", 600, _bridinajumi_dati):
        if b["lidz"] and b["lidz"] < tagad:
            continue
        b_poligoni, skarti = _bridinajumu_skartie(b, vietas)
        punkti = [x for p in b_poligoni for x in p]
        lidz = b["lidz"].strftime("%d.%m. %H:%M") if b["lidz"] else None
        zinas.append({
            "veids": "bridinajums", "id": b["id"], "paradiba": b["paradiba"], "limenis": b["limenis"],
            "datums": (b["no"] or tagad).strftime("%Y-%m-%d"), "diena": None,
            "virsraksts": f"{b['krasa']} brīdinājums: {b['paradiba'].lower()}" +
                          (f" ({b['regioni']})" if b["regioni"] else "") + (f", līdz {lidz}" if lidz else ""),
            "teksts": b["teksts"], "regioni": skarti,
            "bbox": [min(p[1] for p in punkti), min(p[0] for p in punkti), max(p[1] for p in punkti),
                     max(p[0] for p in punkti)] if punkti else _bbox(regioni_, skarti),
            "avots": BRIDINAJUMU_AVOTS,
        })
        poligoni += [{"id": b["id"], "limenis": b["limenis"], "paradiba": b["paradiba"],
                      "poligons": [[round(lat, 4), round(lon, 4)] for lat, lon in p]} for p in b_poligoni]
    return zinas, poligoni


# Riska karte: līmenis 0–3 katram novadam šodien un rīt. HEURISTIKA, nevis oficiāls vērtējums:
# max(LVĢMC brīdinājuma krāsa, brāzmu un nokrišņu prognoze) + 1 par zibeni pēdējās 30 min (tikai šodien)
# + 1 par slidenu ceļu (LVC, tikai šodien, ja dati jau ir kešā); ne vairāk par 3.
RISKA_BRAZMAS = [(15, 1), (20, 2), (25, 3)]   # diennakts maks. brāzmas, m/s
RISKA_NOKRISNI = [(15, 1), (30, 2)]           # diennakts nokrišņu summa, mm
RISKA_LIMENI = {0: "nav", 1: "paaugstināts", 2: "augsts", 3: "ļoti augsts"}
ZIBENS_AVOTS_ISS = {"nosaukums": "FMI zibens dati", "licence": "CC BY 4.0", "url": "https://en.ilmatieteenlaitos.fi/open-data"}
LVC_AVOTS_ISS = {"nosaukums": "LVC satiksmes informācija (NAP)", "licence": "CC0 1.0",
                 "url": "https://www.transportdata.gov.lv/lv/card/f3204a64-3dc3-4ed6-b6f0-872f58500735"}
PR_NOMINATIVS = {"Kurzemē": "Kurzeme", "Zemgalē": "Zemgale", "Vidzemē": "Vidzeme", "Latgalē": "Latgale",
                 "Rīgā un Pierīgā": "Rīga un Pierīga"}


def _pec_sliekshna(vertiba, sliekshni):
    lim = 0
    for robeza, l in sliekshni:
        if vertiba is not None and vertiba >= robeza:
            lim = l
    return lim


def _tuvaka_vieta_regions(vietas):
    """(lat, lon) → reģiona kods pēc tuvākās prognožu vietas (režģis 0,1°, lai nav 6427 salīdzinājumu katram punktam)."""
    rezgis = {}
    for _n, la, lo, kods in vietas.values():
        if kods:
            rezgis.setdefault((round(la, 1), round(lo, 1)), []).append((la, lo, kods))

    def atrast(lat, lon):
        kandidati = [v for dy in (-0.1, 0, 0.1) for dx in (-0.1, 0, 0.1)
                     for v in rezgis.get((round(lat + dy, 1), round(lon + dx, 1)), [])]
        if not kandidati:
            return None
        return min(kandidati, key=lambda v: (v[0] - lat) ** 2 + ((v[1] - lon) * 0.55) ** 2)[2]
    return atrast


def _riski(dati, regioni_, vietas, tagad, dienas):
    """{kods: {"sodien": n, "rit": n, "iemesli": [{diena, limenis, teksts, avots, klat}]}} pirmajām divām dienām."""
    atslegas = list(zip(["sodien", "rit"], dienas[:2]))
    riski = {k: {"sodien": 0, "rit": 0, "iemesli": []} for k in regioni_}

    def pievienot(kods, diena, limenis, teksts, avots, klat=False):
        r = riski.get(kods)
        if r is None:
            return
        r[diena] = min(3, r[diena] + limenis) if klat else max(r[diena], limenis)
        r["iemesli"].append({"diena": diena, "limenis": limenis, "teksts": teksts, "avots": avots, "klat": klat})

    # LVĢMC brīdinājumi: līmenis dienām, kuras pārklāj brīdinājuma laiks
    try:
        for b in _kesots("bridinajumi", 600, _bridinajumi_dati):
            if b["lidz"] and b["lidz"] < tagad:
                continue
            _p, skarti = _bridinajumu_skartie(b, vietas)
            for diena, datums in atslegas:
                d0 = datetime.strptime(datums, "%Y-%m-%d")
                if (b["no"] and b["no"] >= d0 + timedelta(days=1)) or (b["lidz"] and b["lidz"] < d0):
                    continue
                for kods in skarti:
                    pievienot(kods, diena, b["limenis"], f"LVĢMC {b['krasa'].lower()} brīdinājums: {b['paradiba'].lower()}",
                              BRIDINAJUMU_AVOTS)
    except Kluda:
        pass
    # Prognoze: (bez zibens/ceļiem) brāzmas un nokrišņi; prognoze aprēķina "klat" pirms zibens, lai max darbojas pareizi
    for diena, datums in atslegas:
        for kods, r in dati["kopsavilkums"].get(datums, {}).items():
            lim = _pec_sliekshna(r["brazmas"], RISKA_BRAZMAS)
            if lim:
                pievienot(kods, diena, lim, f"brāzmas līdz {_skaitlis_lv(r['brazmas'])} m/s" +
                          (f" ({r['brazmas_vieta']})" if r.get("brazmas_vieta") else ""), PROGNOZU_AVOTS)
            lim = _pec_sliekshna(r["nokrisni"], RISKA_NOKRISNI)
            if lim:
                pievienot(kods, diena, lim, f"nokrišņi līdz {_skaitlis_lv(r['nokrisni'])} mm" +
                          (f" ({r['nokrisni_vieta']})" if r.get("nokrisni_vieta") else ""), PROGNOZU_AVOTS)
    if vietas:
        atrast = _tuvaka_vieta_regions(vietas)
        # Zibens pēdējās 30 min (FMI) — tikai šodien, +1
        try:
            skaits = {}
            for z in _kesots("zibens_fmi", 60, _fmi_zibens)["zibeni"]:
                kods = atrast(z["lat"], z["lon"])
                if kods:
                    skaits[kods] = skaits.get(kods, 0) + 1
            for kods, n in skaits.items():
                pievienot(kods, "sodien", 1, f"zibens pēdējās {ZIBENS_MIN} min: {n}", ZIBENS_AVOTS_ISS, klat=True)
        except Kluda:
            pass
        # Slidens ceļš (LVC) — tikai šodien, +1; tikai no kešas, lai prognoze negaida NAP
        with _kesas_slots:
            ieraksts = _kesa.get(("celi", "slidens"))
        skaits = {}
        for n in (ieraksts[1] if ieraksts else None) or []:
            kods = atrast(n["lat"], n["lon"])
            if kods:
                skaits[kods] = skaits.get(kods, 0) + 1
        for kods, n in skaits.items():
            pievienot(kods, "sodien", 1, f"slidens ceļš: {n} {'vieta' if n % 10 == 1 and n % 100 != 11 else 'vietas'}",
                      LVC_AVOTS_ISS, klat=True)
    for r in riski.values():
        r["iemesli"].sort(key=lambda i: (i["diena"] != "sodien", i["klat"], -i["limenis"]))
    return riski


def _risku_zinas(riski, regioni_, dienas, sodien):
    """Ziņa lentes augšā katrai dienai: plānošanas reģioni ar paaugstinātu risku un galvenais iemesls."""
    zinas = []
    for diena, datums in zip(["sodien", "rit"], dienas[:2]):
        pa_pr = {}  # plānošanas reģions → [maks. līmenis, galvenais iemesls, novadi]
        for kods, r in riski.items():
            if r[diena] < 1:
                continue
            pr = regioni_[kods]["planosanas_regions"]
            pr = PR_NOMINATIVS.get(pr, regioni_[kods]["nosaukums"])
            iemesli = [i for i in r["iemesli"] if i["diena"] == diena]
            galvenais = next((i for i in iemesli if not i["klat"]), iemesli[0] if iemesli else None)
            esosais = pa_pr.setdefault(pr, [0, None, []])
            esosais[2].append(kods)
            if r[diena] > esosais[0]:
                esosais[0], esosais[1] = r[diena], galvenais
        if not pa_pr:
            continue
        seciba = sorted(pa_pr.items(), key=lambda x: -x[1][0])
        nos = _dienas_nosaukums(datums, sodien)
        dalas = [pr + (f" ({re.sub(r' [(].*[)]$', '', v[1]['teksts'])})" if v[1] else "") for pr, v in seciba]
        kodi = [k for _pr, v in seciba for k in v[2]]
        zinas.append({
            "veids": "riski", "paradiba": "Risks", "limenis": seciba[0][1][0], "datums": datums, "diena": nos,
            "virsraksts": f"{nos} paaugstināts risks: " + ", ".join(dalas),
            "teksts": f"Novadi ar paaugstinātu risku: {len(kodi)}. Riska karte apvieno LVĢMC brīdinājumus, prognozi, "
                      "zibeni un slidenus ceļus; tas ir mūsu aprēķins, nevis oficiāls brīdinājums.",
            "regioni": kodi, "bbox": _bbox(regioni_, kodi), "avots": PROGNOZU_AVOTS,
        })
    return zinas


def prognozes(_q):
    return _kesots("prognozes_atbilde", 300, _prognozes)


def _prognozes():
    tagad = _riga_tagad()
    try:
        regioni_ = _kesots("prognozu_regioni", 86400, _prognozu_regioni)
    except Kluda:  # bez DB: brīdinājumi vēl var tikt parādīti
        regioni_ = {}
    try:
        vietas = _kesots("prognozu_vietas", 86400, _prognozu_vietas)
    except Kluda:
        vietas = {}
    try:
        dati = _kesots("prognozes", 1800, _prognozu_dati)
    except Kluda:
        dati = {"kopsavilkums": {}, "mainits": None}
    try:
        bridinajumu_zinas, poligoni = _bridinajumu_zinas(regioni_, vietas, tagad)
    except Kluda:
        bridinajumu_zinas, poligoni = [], []
    if not dati["kopsavilkums"] and not bridinajumu_zinas and not poligoni:
        raise Kluda(503, "prognozes pašlaik nav pieejamas")
    sodien = tagad.date()
    dienas = [d for d in sorted(dati["kopsavilkums"]) if d >= sodien.isoformat()][:3]
    riski = _riski(dati, regioni_, vietas, tagad, dienas)
    zinas = _risku_zinas(riski, regioni_, dienas, sodien) + bridinajumu_zinas + \
        _prognozu_zinas(dati, regioni_, sodien, dienas)
    # Ja dienā nekas nepārsniedz sliekšņus — viena mierīga ziņa, lai lente nav tukša
    for datums in dienas:
        if any(z["datums"] == datums and z["limenis"] >= 1 for z in zinas):
            continue
        r = dati["kopsavilkums"][datums].values()
        def robeza(f, lauks):
            return f((x[lauks] for x in r if x[lauks] is not None), default=None)
        tmin, tmax, brazmas, nokrisni = robeza(min, "tmin"), robeza(max, "tmax"), robeza(max, "brazmas"), robeza(max, "nokrisni")
        if None in (tmin, tmax, brazmas, nokrisni):
            continue
        zinas.append({
            "veids": "kopsavilkums", "paradiba": "Laiks", "limenis": 0, "datums": datums,
            "diena": _dienas_nosaukums(datums, sodien),
            "virsraksts": f"{_dienas_nosaukums(datums, sodien)} Latvijā bīstami laika apstākļi nav gaidāmi",
            "teksts": f"Temperatūra {_skaitlis_lv(tmin)}…{_skaitlis_lv(tmax)} °C, "
                      f"brāzmas līdz {_skaitlis_lv(brazmas)} m/s, nokrišņi līdz {_skaitlis_lv(nokrisni)} mm.",
            "regioni": [], "bbox": None, "avots": PROGNOZU_AVOTS,
        })
    zinas.sort(key=lambda z: (z["veids"] != "riski", z["veids"] != "bridinajums", z["datums"], -z["limenis"],
                              z["virsraksts"]))
    return {
        "laiks_lv": tagad.isoformat(timespec="minutes"),
        "prognoze_mainita": dati["mainits"],
        "dienas": [{"datums": d, "nosaukums": _dienas_nosaukums(d, sodien)} for d in dienas],
        "zinas": zinas,
        "regioni": {k: {"nosaukums": r["nosaukums"], "planosanas_regions": r["planosanas_regions"],
                        "dienas": {d: dati["kopsavilkums"][d].get(k) for d in dienas}} for k, r in regioni_.items()},
        "bridinajumu_poligoni": poligoni,
        "sliekshni": PROGNOZU_SLIEKSNI,
        "riski": riski,
        "riska_dienas": {"sodien": dienas[0] if dienas else None, "rit": dienas[1] if len(dienas) > 1 else None},
        "riska_limeni": RISKA_LIMENI,
    }


def prognozu_robezas(_q):
    """Novadu un valstspilsētu robežas, stipri vienkāršotas (~500 m), lai telefonā ielādējas ātri."""
    return _kesots("prognozu_robezas", 86400, lambda: vaicat(
        """select json_build_object('type', 'FeatureCollection', 'features', coalesce(json_agg(json_build_object(
                  'type', 'Feature', 'id', kods, 'properties', json_build_object('kods', kods, 'nosaukums', nosaukums),
                  'geometry', st_asgeojson(st_simplifypreservetopology(geom_vienk, 0.004), 3)::json)), '[]'))
           from regioni where tips in ('novads', 'valstspilseta')""", timeout="20s"))


# ---- /Prognoze / ziņas ----


# ---- Zibens un augsne: /api/zibens, /api/augsne ----
# Zibens: FMI (Ilmatieteen laitos) atvērtie dati, WFS, CC BY 4.0 — pēdējās 30 min. Papildus LVĢMC 24 h zibens režģis
# (data.gov.lv, CC0; 5×5 km šūnas, kavējas ~2–3 h). Blitzortung NAV atļauts (licence to aizliedz).
FMI_ZIBENS = ("https://opendata.fmi.fi/wfs?service=WFS&version=2.0.0&request=getFeature"
              "&storedquery_id=fmi::observations::lightning::simple&bbox=20.8,55.6,28.3,58.1"
              "&parameters=peak_current&starttime={no}&endtime={lidz}")
ZIBENS_AVOTS = {"nosaukums": "Ilmatieteen laitos (FMI) atvērtie dati", "licence": "CC BY 4.0",
                "url": "https://en.ilmatieteenlaitos.fi/open-data"}
LVGMC_ZIBENS = ("https://data.gov.lv/dati/dataset/1936ed28-16df-4588-819e-8a5143a50c81/resource/"
                "a264bfb4-f52f-41f7-93fc-04214f4a2b5b/download/zibens_rezgis_operativie_dati.csv")
LVGMC_ZIBENS_AVOTS = {"nosaukums": "LVĢMC telpiskie novērojumi (zibens režģis, 24 h)", "licence": "CC0 1.0",
                      "url": "https://data.gov.lv/dati/lv/dataset/telpiskie-hidrometeorologiskie-noverojumi"}
ZIBENS_MIN = 30


def _fmi_zibens():
    import xml.etree.ElementTree as ET
    lidz = datetime.now(timezone.utc).replace(microsecond=0)
    no = lidz - timedelta(minutes=ZIBENS_MIN)
    url = FMI_ZIBENS.format(no=no.strftime("%Y-%m-%dT%H:%M:%SZ"), lidz=lidz.strftime("%Y-%m-%dT%H:%M:%SZ"))
    sakne = ET.fromstring(_lejupieladet(url, timeout=10))
    if not sakne.tag.endswith("}FeatureCollection"):  # piem., ows:ExceptionReport ar HTTP 200
        raise Kluda(503, "FMI atbilde nav derīga")
    ns = {"BsWfs": "http://xml.fmi.fi/schema/wfs/2.0", "gml": "http://www.opengis.net/gml/3.2"}
    zibeni = {}  # (pos, laiks) → zibens: vairāki elementi (parametri) dalās vienā punktā un laikā
    for e in sakne.iter("{http://xml.fmi.fi/schema/wfs/2.0}BsWfsElement"):
        pos, laiks = e.findtext(".//gml:pos", "", ns).split(), e.findtext("BsWfs:Time", "", ns)
        if len(pos) != 2 or not laiks:
            continue
        try:
            lat, lon = float(pos[0]), float(pos[1])
        except ValueError:
            continue
        if not (55 <= lat <= 59 and 20 <= lon <= 29):
            continue
        z = zibeni.setdefault((tuple(pos), laiks), {"lat": lat, "lon": lon, "laiks": laiks, "strava": None})
        if e.findtext("BsWfs:ParameterName", "", ns) == "peak_current":
            try:
                z["strava"] = float(e.findtext("BsWfs:ParameterValue", "", ns))
            except ValueError:
                pass
    return {"no": no.isoformat(), "lidz": lidz.isoformat(), "zibeni": sorted(zibeni.values(), key=lambda z: z["laiks"])}


def _lvgmc_zibens():
    sunas, pedejais = {}, None
    for r in _csv(LVGMC_ZIBENS):
        pedejais = max(pedejais or r["LAIKS"], r["LAIKS"])
        try:
            skaits = int(float(r["TOTAL"] or 0))
        except ValueError:
            continue
        if skaits > 0:
            s = sunas.setdefault((r["LAT"], r["LON"]), {"lat": round(float(r["LAT"]), 4), "lon": round(float(r["LON"]), 4),
                                                         "skaits": 0, "pedejais": None})
            s["skaits"] += skaits
            s["pedejais"] = max(s["pedejais"] or r["LAIKS"], r["LAIKS"])
    return {"lidz_lv": pedejais, "sunas": list(sunas.values())}


def zibens(_q):
    try:
        fmi = _kesots("zibens_fmi", 60, _fmi_zibens)
    except Kluda:
        fmi = None
    try:
        rezgis = _kesots("zibens_lvgmc", 900, _lvgmc_zibens)
    except Kluda:
        rezgis = None
    if fmi is None and rezgis is None:
        raise Kluda(503, "zibens dati pašlaik nav pieejami")
    return {
        "minutes": ZIBENS_MIN,
        "zibeni": fmi["zibeni"] if fmi else None, "skaits": len(fmi["zibeni"]) if fmi else None,
        "no": fmi and fmi["no"], "lidz": fmi and fmi["lidz"], "avots": ZIBENS_AVOTS,
        "rezgis_24h": rezgis, "rezgis_avots": LVGMC_ZIBENS_AVOTS,
    }


# Augsne: Open-Meteo (CC BY 4.0, bezmaksas nekomerciālai lietošanai, <10 000 pieprasījumu dienā). Konteksts, NAV brīdinājums.
OPEN_METEO = ("https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=precipitation_sum"
              "&hourly=soil_moisture_3_to_9cm&past_days=26&forecast_days=3&timezone=Europe%2FRiga")
AUGSNES_AVOTS = {"nosaukums": "Open-Meteo", "licence": "CC BY 4.0", "url": "https://open-meteo.com/"}
# Heuristika (nav oficiāla skala): augsnes mitrums 3–9 cm, m³/m³. Latvijas māla/smilšmāla augsnēm piesātinājums
# ir ~0,40–0,45, smiltīm ~0,30, tāpēc sliekšņi ir rupji: < 0,20 sausa, < 0,35 mitra, ≥ 0,35 ļoti mitra (gandrīz piesātināta).
AUGSNES_SLIEKSNI = [(0.20, "sausa"), (0.35, "mitra")]
AUGSNES_MAX_STUNDA = 300  # Open-Meteo pieprasījumi stundā no šī procesa (bezmaksas limits <10 000 dienā); kešotās atbildes — vienmēr
_augsnes_skaititajs = [0, 0]  # [stunda, pieprasījumi]


def augsne(q):
    lat, lon = _vieta(q)
    lat, lon = round(lat, 2), round(lon, 2)  # ~1 km; kešs pēc tā

    def iegut():
        stunda = int(time.time() // 3600)
        with _kesas_slots:
            if _augsnes_skaititajs[0] != stunda:
                _augsnes_skaititajs[:] = [stunda, 0]
            if _augsnes_skaititajs[1] >= AUGSNES_MAX_STUNDA:
                raise Kluda(503, "augsnes dati pašlaik nav pieejami")
            _augsnes_skaititajs[1] += 1
        d = json.loads(_lejupieladet(OPEN_METEO.format(lat=lat, lon=lon), timeout=10))
        sodien = _riga_tagad().strftime("%Y-%m-%d")
        dienas = list(zip(d["daily"]["time"], d["daily"]["precipitation_sum"]))
        pagatne = [v for t, v in dienas if t < sodien and v is not None]
        nakotne = [v for t, v in dienas if t >= sodien and v is not None]
        stunda = _riga_tagad().strftime("%Y-%m-%dT%H:00")
        mitrums = None
        for t, v in zip(d["hourly"]["time"], d["hourly"]["soil_moisture_3_to_9cm"]):
            if t <= stunda and v is not None:
                mitrums = v
        stavoklis = None if mitrums is None else next(
            (n for robeza, n in AUGSNES_SLIEKSNI if mitrums < robeza), "ļoti mitra")
        return {
            "nokrisni_pagatne_mm": round(sum(pagatne), 1), "dienas_pagatne": len(pagatne),
            "nokrisni_prognoze_mm": round(sum(nakotne), 1), "dienas_prognoze": len(nakotne),
            "augsnes_mitrums": mitrums, "augsne": stavoklis, "avots": AUGSNES_AVOTS,
        }

    return _kesots(("augsne", lat, lon), 3600, iegut)


# ---- /Zibens un augsne ----


# ---- Maršruts, kas apiet slēgtās zonas: GET /api/marsruts ----
# Maršrutētājs: FOSSGIS OSRM (routing.openstreetmap.de; tas pats, ko lieto openstreetmap.org "Ceļa norādes"), dati
# OpenStreetMap (ODbL). router.project-osrm.org demo prot tikai auto profilu, tāpēc kājāmgājējiem — FOSSGIS. Lietošana
# ir viegla: viens pieprasījums vienlaikus, taimauts 8 s, kešs 10 min pēc noapaļotiem punktiem un zonām.
# Zonas: ?izvairities=c:lat,lon,r|lat,lon;lat,lon;... (aplis metros vai poligons) + spēkā esošie LVC ceļu slēgumi 20 km
# rādiusā (tikai no /api/celi kešas). Ja neviena no ≤ 3 alternatīvām neapiet zonas, mēģina caur punktiem ap zonu;
# ja arī tas neizdodas — taisna līnija ar norādi "nav droša maršruta".
MARSRUTA_SERVERI = {"kajam": "https://routing.openstreetmap.de/routed-foot/route/v1/driving/",
                    "auto": "https://routing.openstreetmap.de/routed-car/route/v1/driving/"}
MARSRUTA_AVOTS = {"nosaukums": "FOSSGIS OSRM (routing.openstreetmap.de), OpenStreetMap dati", "licence": "ODbL 1.0",
                  "url": "https://routing.openstreetmap.de/about.html"}
_marsruta_slots = threading.Lock()
CELA_SLEGUMA_BUFERIS_M = 30


def _zonas_no_teksta(teksts):
    zonas = []
    for dala in [x for x in (teksts or "").split("|") if x][:6]:
        try:
            if dala.startswith("c:"):
                lat, lon, r = (float(v) for v in dala[2:].split(","))
                if 55 <= lat <= 59 and 20 <= lon <= 29 and 10 <= r <= 20000:
                    zonas.append({"tips": "aplis", "centrs": (lat, lon), "r": r})
            else:
                punkti = [tuple(float(v) for v in p.split(",")) for p in dala.split(";") if p][:80]
                if len(punkti) >= 3 and all(55 <= a <= 59 and 20 <= b <= 29 for a, b in punkti):
                    zonas.append({"tips": "poligons", "punkti": punkti})
        except ValueError:
            raise Kluda(400, "izvairities: c:lat,lon,r vai lat,lon;lat,lon;…, atdalītas ar |") from None
    return zonas


def _attalums_lidz_nogrieznim(p, a, b):
    """Metri no punkta p līdz nogrieznim a–b (vietējā plaknē)."""
    kx = 111320 * math.cos(math.radians(p[0]))
    ax, ay, bx, by, px, py = a[1] * kx, a[0] * 110540, b[1] * kx, b[0] * 110540, p[1] * kx, p[0] * 110540
    dx, dy = bx - ax, by - ay
    t = 0 if dx == dy == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - ax - t * dx, py - ay - t * dy)


def _zona(z, p):
    if z["tips"] == "aplis":
        return _attalums_m(p[0], p[1], *z["centrs"]) <= z["r"]
    if z["tips"] == "linija":
        return any(_attalums_lidz_nogrieznim(p, a, b) <= CELA_SLEGUMA_BUFERIS_M for a, b in zip(z["punkti"], z["punkti"][1:]))
    return _punkts_poligona(p[0], p[1], z["punkti"])


def _celu_slegumu_zonas(no):
    with _kesas_slots:
        ieraksts = _kesa.get(("celi", "slegums"))
    zonas = []
    tagad = datetime.now(timezone.utc)
    for n in (ieraksts[1] if ieraksts else None) or []:
        punkti = n.get("linija") or [(n["lat"], n["lon"])]
        sakums, beigas = _datex_laiks(n.get("no")), _datex_laiks(n.get("lidz"))
        if (sakums and sakums > tagad) or (beigas and beigas < tagad):
            continue
        if min(_attalums_m(no[0], no[1], la, lo) for la, lo in punkti) > 20000:
            continue
        zonas.append({"tips": "linija", "punkti": [tuple(p) for p in punkti] if len(punkti) > 1 else [tuple(punkti[0])] * 2,
                      "nosaukums": n.get("nosaukums") or "Ceļa slēgums"})
    return zonas[:30]


def _skart_zonas(koord, zonas):
    """Zonas, kurās maršruts iebrauc. Ja sākums (vai galamērķis) ir zonā, sākuma (beigu) posms tajā ir atļauts — no
    zonas jāiziet; aizliegts ir tajā atgriezties. Punktus starp virsotnēm pārbauda ik ~25 m."""
    blivi = []
    for a, b in zip(koord, koord[1:]):
        n = max(1, int(_attalums_m(a[0], a[1], b[0], b[1]) // 25))
        blivi += [(a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n) for i in range(n)]
    blivi.append(koord[-1])
    skartas = []
    for z in zonas:
        iek = [_zona(z, p) for p in blivi]
        i, j = 0, len(iek)
        while i < j and iek[i]:
            i += 1
        while j > i and iek[j - 1]:
            j -= 1
        # iziešana no zonas (vai ieiešana galamērķī) nedrīkst iet tuvāk zonas centram par 100 m — nevis cauri tai
        centrs = z["centrs"] if z["tips"] == "aplis" else             (sum(p[0] for p in z["punkti"]) / len(z["punkti"]), sum(p[1] for p in z["punkti"]) / len(z["punkti"]))             if z["tips"] == "poligons" else None
        cauri = False
        if centrs:
            att = [_attalums_m(p[0], p[1], *centrs) for p in blivi]
            cauri = (i and min(att[:i]) < att[0] - 100) or (j < len(att) and min(att[j:]) < att[-1] - 100)
        if any(iek[i:j]) or cauri:
            skartas.append(z)
    return skartas


def _osrm(veids, punkti, alternativas):
    url = MARSRUTA_SERVERI[veids] + ";".join(f"{lon:.6f},{lat:.6f}" for lat, lon in punkti) + \
        f"?overview=full&geometries=geojson&steps=false&alternatives={'3' if alternativas else 'false'}"
    if not _marsruta_slots.acquire(timeout=10):
        raise Kluda(503, "maršrutētājs aizņemts, mēģiniet pēc brīža")
    try:
        d = json.loads(_lejupieladet(url, timeout=8))
    finally:
        _marsruta_slots.release()
    if d.get("code") != "Ok":
        raise RuntimeError(d.get("code"))
    return [{"koord": [(lat, lon) for lon, lat in r["geometry"]["coordinates"]], "attalums_m": round(r["distance"]),
             "ilgums_s": round(r["duration"])} for r in d["routes"]]


def _apvedceli(z, no, uz):
    """Starppunkti ap zonu: aplim — abās pusēs perpendikulāri virzienam no→uz (1,35 r); poligonam — paplašinātā bbox stūri."""
    if z["tips"] == "aplis":
        (clat, clon), r = z["centrs"], z["r"] * 1.35
        kx = 111320 * math.cos(math.radians(clat))
        dx, dy = (uz[1] - no[1]) * kx, (uz[0] - no[0]) * 110540
        garums = math.hypot(dx, dy) or 1
        nx, ny = -dy / garums, dx / garums
        return [(clat + s * ny * r / 110540, clon + s * nx * r / kx) for s in (1, -1)]
    lats = [p[0] for p in z["punkti"]]
    lons = [p[1] for p in z["punkti"]]
    dl, dn = (max(lats) - min(lats)) * 0.2 + 0.002, (max(lons) - min(lons)) * 0.2 + 0.003
    return [(min(lats) - dl, min(lons) - dn), (min(lats) - dl, max(lons) + dn),
            (max(lats) + dl, min(lons) - dn), (max(lats) + dl, max(lons) + dn)]


def marsruts(q):
    def punkts(vards):
        try:
            lat, lon = (float(v) for v in q.get(vards, [""])[0].split(","))
        except ValueError:
            raise Kluda(400, f"{vards}=lat,lon") from None
        if not (55 <= lat <= 59 and 20 <= lon <= 29):
            raise Kluda(400, f"{vards}: ārpus Latvijas")
        return round(lat, 4), round(lon, 4)
    no, uz = punkts("no"), punkts("uz")
    veids = q.get("veids", ["kajam"])[0]
    if veids not in MARSRUTA_SERVERI:
        raise Kluda(400, "veids: kajam vai auto")
    if _attalums_m(*no, *uz) > 60000:
        raise Kluda(400, "pārāk tālu (> 60 km)")
    teksts = q.get("izvairities", [""])[0][:4000]
    zonas = _zonas_no_teksta(teksts) + _celu_slegumu_zonas(no)

    def aprekinat():
        alt = _osrm(veids, [no, uz], True)
        izvele, apiet = None, False
        skartas_pirmaja = _skart_zonas(alt[0]["koord"], zonas) if zonas else []
        for r in alt:
            if not zonas or not _skart_zonas(r["koord"], zonas):
                izvele, apiet = r, r is not alt[0] or False
                break
        if not izvele and skartas_pirmaja:
            kandidati = []
            for via in _apvedceli(skartas_pirmaja[0], no, uz)[:4]:
                try:
                    r = _osrm(veids, [no, via, uz], False)[0]
                except (Kluda, RuntimeError, OSError, ValueError):
                    continue
                if not _skart_zonas(r["koord"], zonas):
                    kandidati.append(r)
            if kandidati:
                izvele, apiet = min(kandidati, key=lambda r: r["attalums_m"]), True
        if izvele:
            return {"dross": True, "apiet_zonu": apiet or bool(skartas_pirmaja), "veids": veids,
                    "no_zonas": any(_zona(z, no) for z in zonas if z["tips"] != "linija"),
                    "attalums_m": izvele["attalums_m"], "ilgums_s": izvele["ilgums_s"],
                    "koord": [[round(a, 5), round(b, 5)] for a, b in _vienkarsot_liniju(izvele["koord"], 0.00004)],
                    "zonas": len(zonas), "avots": MARSRUTA_AVOTS}
        return {"dross": False, "apiet_zonu": False, "veids": veids, "attalums_m": _attalums_m(*no, *uz), "ilgums_s": None,
                "koord": [list(no), list(uz)], "zonas": len(zonas), "avots": MARSRUTA_AVOTS,
                "piezime": "Nav droša maršruta bez slēgtās zonas — izvairieties no tās un sekojiet dienestu norādēm."}

    atslega = ("marsruts", veids, no, uz, teksts, len(zonas))
    return _kesots(atslega, 600, aprekinat)


# ---- /Maršruts ----


def veseliba(_q):
    return {"ok": vaicat("select true")}


# ---- Ceļu slēgumi un negadījumi: GET /api/celi (LVC DATEX II caur NAP transportdata.gov.lv, CC0) ----
# Katrai NAP datu kopai sava bezmaksas atslēga (abonē "Datu ņēmēja" kontā); VPS: /etc/hakatons/map.env.
# Bez atslēgas kopu izlaiž; bez nevienas — tukšs saraksts ar "avots nav konfigurēts".

import xml.etree.ElementTree as ET  # noqa: E402

NAP_BAZE = os.environ.get("NAP_BAZE", "https://www.transportdata.gov.lv")
NAP_KOPAS = [  # (vides mainīgais ar atslēgu, notikuma tips, NAP kartīte); kopas bez atslēgas izlaiž
    ("NAP_API_KEY_SLEGUMI", "slegums", "75611a36-e66b-40cf-af2c-69db48c278cf"),
    ("NAP_API_KEY_NEGADIJUMI", "negadijums", "e8659cdd-9372-41fd-8b28-e7c742895bdd"),
    ("NAP_API_KEY_JOSLAS", "joslas_slegums", "82e20567-7e0d-4f58-8040-77d6fcb32899"),
    ("NAP_API_KEY_REMONTI", "remonts", "35fa5c41-90ce-4b74-a4a3-08216d470134"),
    ("NAP_API_KEY_SATIKSME_SLIDENS", "slidens", "f3204a64-3dc3-4ed6-b6f0-872f58500735"),     # Satiksmes informācijas centrs
    ("NAP_API_KEY_UZTURETAJI_SLIDENS", "slidens", "6749e127-7520-4790-8d6a-ad4a0270d1fe"),   # ceļu uzturētāju ziņojumi
    ("NAP_API_KEY_METEO_SLIDENS", "slidens", "46cd2e45-33b7-492c-a163-a9dd5508ede4"),        # meteostaciju dati
]
# Ierakstiem bez teksta (piem., negadījumu plūsmā ir tikai kodi): nosaukums pēc DATEX tipa un apraksts no kodiem
CELU_XSI_NOS = {"EnvironmentalObstruction": "Šķērslis uz ceļa", "Accident": "Negadījums",
                "VehicleObstruction": "Transportlīdzeklis uz ceļa", "AnimalPresenceObstruction": "Dzīvnieki uz ceļa",
                "GeneralObstruction": "Šķērslis uz ceļa", "PoorEnvironmentConditions": "Slikti laikapstākļi",
                "WeatherRelatedRoadConditions": "Slidens ceļš", "NonWeatherRelatedRoadConditions": "Slikts ceļa segums",
                "ConstructionWorks": "Ceļa būvdarbi", "MaintenanceWorks": "Ceļa uzturēšanas darbi",
                "RoadOrCarriagewayOrLaneManagement": "Satiksmes ierobežojums"}
DATEX_KODI_LV = {
    "fallenTrees": "nokrituši koki", "flooding": "applūdums", "rockfalls": "akmeņu nogruvums", "landslips": "zemes nogruvums",
    "objectOnTheRoad": "priekšmets uz ceļa", "obstructionOnTheRoad": "šķērslis uz ceļa", "accident": "negadījums",
    "brokenDownVehicle": "salūzis transportlīdzeklis", "vehicleOnFire": "deg transportlīdzeklis",
    "ice": "apledojums", "blackIce": "melnais ledus", "snowOnTheRoad": "sniegs uz ceļa", "packedSnow": "piebraukts sniegs",
    "freezingRain": "lijums", "frost": "sarma", "slushOnRoad": "šķīdonis", "wetIcyRoad": "mitrs, apledojis ceļš",
    "surfaceWater": "ūdens uz ceļa", "looseChippings": "birstošas šķembas", "oilOnRoad": "eļļa uz ceļa",
    "potholes": "bedres", "roadSurfaceInPoorCondition": "slikts segums", "constructionWork": "būvdarbi",
    "maintenanceWork": "uzturēšanas darbi", "roadPartiallyObstructed": "ceļš daļēji aizšķērsots",
    "lanesPartiallyObstructed": "joslas daļēji aizšķērsotas", "roadBlocked": "ceļš slēgts",
    "carriagewayBlocked": "brauktuve slēgta", "lanesBlocked": "joslas slēgtas",
}
CELU_KODU_LAUKI = ("environmentalObstructionType", "accidentType", "vehicleObstructionType", "obstructionType",
                   "weatherRelatedRoadConditionType", "nonWeatherRelatedRoadConditionType", "constructionWorkType",
                   "roadMaintenanceType", "trafficConstrictionType")
CELU_TIPI = {"slegums": "Ceļš slēgts", "negadijums": "Negadījums", "joslas_slegums": "Slēgta josla",
             "remonts": "Ceļa remontdarbi", "slidens": "Slidens ceļš"}
CELA_NR = re.compile(r"\b([APV]\d{1,4})\b")
XSI_TIPS = "{http://www.w3.org/2001/XMLSchema-instance}type"
_celu_pavedieni = ThreadPoolExecutor(max_workers=16)  # arī /api/satiksme kopām
_celu_kludas = {}  # vides mainīgais → laiks: pēc kļūdas bez kešas nākamais mēģinājums pēc minūtes


def _datex_visi(el, vards):
    """Pēcteči ar doto lokālo vārdu (ET.iter neprot {*})."""
    return (e for e in el.iter() if e is not el and e.tag.rsplit("}", 1)[-1] == vards)


def _datex_teksts(el, vards):
    return next((e.text.strip() for e in _datex_visi(el, vards) if e.text and e.text.strip()), None)


def _datex_laiks(teksts):
    if not teksts:
        return None
    try:
        t = datetime.fromisoformat(teksts.replace("Z", "+00:00"))
    except ValueError:
        return None
    return t if t.tzinfo else t.replace(tzinfo=timezone.utc)


def _datex_apraksts(sit):
    """generalPublicComment teksts latviski (ja ir), citādi pirmais."""
    vertibas = [(e.get("lang") or "", (e.text or "").strip())
                for k in _datex_visi(sit, "generalPublicComment") for e in _datex_visi(k, "value")]
    vertibas = [v for v in vertibas if v[1]]
    return next((t for l, t in vertibas if l.lower() == "lv"), vertibas[0][1] if vertibas else None)


def _datex_punkti(el):
    punkti = []
    for p in _datex_visi(el, "openlrCoordinates"):
        lat, lon = _datex_teksts(p, "latitude"), _datex_teksts(p, "longitude")
        try:
            punkti.append((round(float(lat), 5), round(float(lon), 5)))
        except (TypeError, ValueError):
            continue
    if not punkti:  # citi DATEX vietas veidi (pointCoordinates)
        for p in _datex_visi(el, "pointCoordinates"):
            try:
                punkti.append((round(float(_datex_teksts(p, "latitude")), 5), round(float(_datex_teksts(p, "longitude")), 5)))
            except (TypeError, ValueError):
                continue
    return punkti


def _datex_ieraksti(sakne):
    """SituationPublication ieraksti vispārīgā formā (celi un satiksme no tiem veido savus objektus)."""
    ieraksti = []
    for sit in _datex_visi(sakne, "situationRecord"):
        if _datex_teksts(sit, "validityStatus") == "suspended":
            continue
        punkti = _datex_punkti(sit)
        if not punkti or not all(55 <= la <= 59 and 20 <= lo <= 29 for la, lo in punkti):
            continue
        kodi = {v: _datex_teksts(sit, v) for v in CELU_KODU_LAUKI}
        ieraksti.append({
            "id": sit.get("id"), "xsi": (sit.get(XSI_TIPS) or "").split(":")[-1], "punkti": punkti,
            "apraksts": _datex_apraksts(sit), "kodi": {k: v for k, v in kodi.items() if v},
            "atrums_ierob": _datex_teksts(sit, "temporarySpeedLimit"),
            "kavejums_s": _datex_teksts(sit, "delayTimeValue"),
            "cela_temp": _datex_teksts(sit, "roadSurfaceTemperature"), "gaisa_temp": _datex_teksts(sit, "airTemperature"),
            "virziens": _datex_teksts(sit, "directionBound") or _datex_teksts(sit, "alertCDirectionCoded"),
            "no": _datex_teksts(sit, "overallStartTime"), "lidz": _datex_teksts(sit, "overallEndTime"),
            "laiks": _datex_teksts(sit, "situationRecordVersionTime") or _datex_teksts(sit, "overallStartTime"),
        })
    return ieraksti


def _kodu_apraksts(ier):
    dalas = [DATEX_KODI_LV.get(v, v) for v in ier["kodi"].values()]
    if ier.get("atrums_ierob"):
        dalas.append(f"ātruma ierobežojums {ier['atrums_ierob']} km/h")
    teksts = ", ".join(dict.fromkeys(dalas))
    return teksts[:1].upper() + teksts[1:] if teksts else None


def _celu_notikums(ier, tips):
    punkti = ier["punkti"]
    apraksts = ier["apraksts"] or _kodu_apraksts(ier)
    cels = CELA_NR.search(apraksts or "")
    if len(punkti) > 60:  # līnija kartē: pietiek ar ~60 punktiem
        punkti = punkti[:: math.ceil(len(punkti) / 60)] + [punkti[-1]]
    nosaukums = CELU_TIPI[tips] if tips in ("slegums", "joslas_slegums") else CELU_XSI_NOS.get(ier["xsi"], CELU_TIPI[tips])
    return {
        "id": ier["id"], "tips": tips, "nosaukums": nosaukums,
        "apraksts": (apraksts or "")[:600] or None, "cels": cels.group(1) if cels else None,
        "lat": punkti[0][0], "lon": punkti[0][1], "linija": punkti if len(punkti) > 1 else None,
        "no": ier["no"], "lidz": ier["lidz"],
    }


def _datex_notikumi(saturs, tips):
    return [_celu_notikums(i, tips) for i in _datex_ieraksti(ET.fromstring(saturs))]


_NAP_GALVENES = {"Content-Type": "application/json", "User-Agent": "map.repo.lv (hakatons, karte_api.py)"}
_nap_kludas_teksts = {}  # vides mainīgais → pēdējās kļūdas īss apraksts (bez atslēgas); /api/satiksme kopas.kluda
_nap_faila_id = {}       # vides mainīgais → faila id, ja "1" neder (no metadata/file/info)


def _nap_pieprasit(atslega, kermenis):
    pieprasijums = urllib.request.Request(NAP_BAZE + "/api/v1/get/file/download-file", method="POST",
                                          data=json.dumps(kermenis).encode(), headers={"x-api-key": atslega, **_NAP_GALVENES})
    with urllib.request.urlopen(pieprasijums, timeout=10) as r:
        if r.status == 204:  # piem., slidens ceļš vasarā
            return b""
        saturs = r.read(10_000_001)
    if len(saturs) > 10_000_000:
        raise ValueError("NAP atbilde lielāka par 10 MB")
    return saturs


def _nap_lejupieladet(atslega, mainigais=None):
    """NAP download-file: baiti (parasti DATEX XML) vai b"" (204). ≤ 10 MB, taimauts 10 s. Ja file_id "1" ar xml
    neder (4xx, izņemot nederīgu atslēgu), faila id ņem no metadata/file/info un mēģina arī bez format."""
    import urllib.error
    faila_id = _nap_faila_id.get(mainigais, "1")
    try:
        return _nap_pieprasit(atslega, {"file_id": faila_id, "format": "xml"})
    except urllib.error.HTTPError as e:
        if e.code in (401, 403) or e.code >= 500:
            raise
    info = urllib.request.Request(NAP_BAZE + "/api/v1/metadata/file/info", headers={"x-api-key": atslega, **_NAP_GALVENES})
    with urllib.request.urlopen(info, timeout=10) as r:
        faili = json.loads(r.read(1_000_000)).get("files") or []
    if faili:
        faila_id = str(faili[0]["file_id"])
        if mainigais:
            _nap_faila_id[mainigais] = faila_id
    try:
        return _nap_pieprasit(atslega, {"file_id": faila_id, "format": "xml"})
    except urllib.error.HTTPError as e:
        if e.code in (401, 403) or e.code >= 500:
            raise
    return _nap_pieprasit(atslega, {"file_id": faila_id})


def _nap_kludas_apraksts(e):
    import urllib.error
    if isinstance(e, urllib.error.HTTPError):
        try:
            teksts = json.loads(e.read(2000)).get("response_text", "")
        except Exception:
            teksts = ""
        return f"HTTP {e.code}" + (f": {str(teksts)[:120]}" if teksts else "")
    if isinstance(e, ET.ParseError):
        return f"atbilde nav XML ({e})"[:160]
    return f"{type(e).__name__}: {e}"[:160]


def _nap_parsets(saturs):
    """Viena kopa → {ieraksti, vietas, merijumi} neatkarīgi no publikācijas veida (parsē vienreiz kešam)."""
    if not saturs:
        return {"ieraksti": [], "vietas": {}, "merijumi": []}
    if saturs.lstrip()[:1] in (b"{", b"["):  # dažas kopas dod JSON (ne DATEX)
        return {"ieraksti": [], "vietas": {}, "merijumi": [], "json": json.loads(saturs)}
    sakne = ET.fromstring(saturs)
    return {"ieraksti": _datex_ieraksti(sakne), "vietas": _datex_vietas(sakne), "merijumi": _datex_merijumi(sakne)}


def _nap_kopa(mainigais, sekundes):
    """Kopas parsētie dati no kešas (stale-on-error); bez kešas pēc kļūdas minūti nemēģina. Kluda, ja nav."""
    atslega = os.environ.get(mainigais, "").strip()
    with _kesas_slots:
        pedeja_kluda = _celu_kludas.get(mainigais, 0)
        ieraksts = _kesa.get(("nap", mainigais))
    if not ieraksts and time.time() - pedeja_kluda < 60:
        raise Kluda(503, "avots nav pieejams")
    def ielade():
        try:
            dati = _nap_parsets(_nap_lejupieladet(atslega, mainigais))
        except Exception as e:
            _nap_kludas_teksts[mainigais] = _nap_kludas_apraksts(e)
            raise
        _nap_kludas_teksts.pop(mainigais, None)
        return dati

    try:
        return _kesots(("nap", mainigais), sekundes, ielade)
    except Kluda:
        with _kesas_slots:
            _celu_kludas[mainigais] = time.time()
        raise


def _nap_vairakas(kopas, termins_s=12):
    """[(mainigais, sekundes)] paralēli → {mainigais: dati | None}; konfigurētās vien, kopējais termiņš 12 s."""
    darbi = {m: _celu_pavedieni.submit(_nap_kopa, m, sek) for m, sek in kopas if os.environ.get(m, "").strip()}
    termins = time.monotonic() + termins_s
    rez = {}
    for m, d in darbi.items():
        try:
            rez[m] = d.result(timeout=max(0.0, termins - time.monotonic()))
        except Exception:  # arī termiņš: lēnā kopa turpina fonā un nākamajā pieprasījumā būs kešā
            rez[m] = None
    return rez


def celu_notikumi_visi():
    """[(tips, notikumi | None)] konfigurētajām kopām; None — kopa nav pieejama. Arī statusa lapai."""
    dati = _nap_vairakas([(v, 300) for v, _t, _k in NAP_KOPAS])
    rez = []
    for v, t, _k in NAP_KOPAS:
        if v in dati:
            d = dati[v]
            rez.append((t, None if d is None else [_celu_notikums(i, t) for i in d["ieraksti"]]))
    return rez


def celi(q):
    lat, lon = _vieta(q, obligata=False)
    attalums_max = _skaitlis(q, "r", 100, 100000)
    bbox = q.get("bbox", [""])[0]
    if bbox:
        try:
            x1, y1, x2, y2 = (float(v) for v in bbox.split(","))
        except ValueError:
            raise Kluda(400, "bbox: minLon,minLat,maxLon,maxLat") from None
    kopas = celu_notikumi_visi()
    if not kopas:
        return {"avots": "lvc-nap", "konfigurets": False, "piezime": "avots nav konfigurēts", "notikumi": []}
    tagad = datetime.now(timezone.utc)
    notikumi, redzeti = [], set()
    for _t, saraksts in kopas:
        for n in saraksts or []:
            if (n["tips"], n["id"]) in redzeti:
                continue
            redzeti.add((n["tips"], n["id"]))
            no, lidz = _datex_laiks(n["no"]), _datex_laiks(n["lidz"])
            if lidz and lidz < tagad:
                continue
            if bbox and not (x1 <= n["lon"] <= x2 and y1 <= n["lat"] <= y2):
                continue
            n = {**n, "aktivs": not no or no <= tagad, "no": no.isoformat(timespec="seconds") if no else None,
                 "lidz": lidz.isoformat(timespec="seconds") if lidz else None}
            if lat is not None:
                n["attalums_m"] = min(_attalums_m(lat, lon, la, lo) for la, lo in (n["linija"] or [(n["lat"], n["lon"])]))
                if attalums_max and n["attalums_m"] > attalums_max:
                    continue
            notikumi.append(n)
    seciba = list(CELU_TIPI)  # slēgumi un negadījumi pirmie
    notikumi.sort(key=lambda n: (n.get("attalums_m", 0), not n["aktivs"], seciba.index(n["tips"]), n["no"] or ""))
    return {"avots": "lvc-nap", "konfigurets": True, "notikumi": notikumi,
            "nepieejami": sorted({t for t, s in kopas if s is None})}


# ---- Satiksme zonās: GET /api/satiksme (LVC caur NAP transportdata.gov.lv, CC0) ----
# Zonas = pašvaldības (regioni, ST_Contains) vai ~10 km režģis, ja datubāze nav pieejama. Katrā zonā satiksmes
# uzskaites iekārtu minūšu ātrums pret brīvas plūsmas ātrumu (novērtējums: lielākais šajā procesā redzētais vidējais
# ātrums iekārtā, kamēr nav ≥ 5 mērījumu — 80 km/h). Slidenā ceļa vietas un robežu gaidīšanas laiks no citām kopām.
# Lauku atbilstība: notes/research/nap-satiksme.md.

SATIKSME_KOPAS = [  # (kods, vides mainīgais, keša sekundes, NAP kartīte, nosaukums)
    ("vietas", "NAP_API_KEY_SATIKSMES_IEKARTU_MERIJUMI", 21600, "fef717ac-c832-49b2-8589-521084cdb595",
     "Satiksmes uzskaites iekārtu atrašanās vietas"),
    ("merijumi", "NAP_API_KEY_SATIKSMES_APJOMS_ATRUMS_MIN", 120, "ed1f0d2c-6ad8-4823-b132-71fc69993d1c",
     "Satiksmes intensitāte un ātrums valsts autoceļos (minūtes dati)"),
    ("slidens_meteo", "NAP_API_KEY_METEO_SLIDENS", 300, "46cd2e45-33b7-492c-a163-a9dd5508ede4",
     "Īslaicīgi slidens ceļš (meteostaciju dati)"),
    ("slidens_uzturetaji", "NAP_API_KEY_UZTURETAJI_SLIDENS", 300, "6749e127-7520-4790-8d6a-ad4a0270d1fe",
     "Īslaicīgi slidens ceļš (ceļu uzturētāju ziņojumi)"),
    ("slidens_sic", "NAP_API_KEY_SATIKSME_SLIDENS", 300, "f3204a64-3dc3-4ed6-b6f0-872f58500735",
     "Īslaicīgi slidens ceļš (Satiksmes informācijas centrs)"),
    ("robezas", "NAP_API_KEY_ROBEZAS_LAIKS", 300, "cb730ba2-6466-45b5-99e4-66b9bde30dae",
     "Robežšķērsošanas gaidīšanas laiks"),
]
SATIKSMES_LIMENI = ["brīvs", "lēns", "sastrēgums", "nav datu"]
SLIDENI_KODI = {"ice", "blackIce", "snowOnTheRoad", "packedSnow", "freezingRain", "frost", "slushOnRoad", "wetIcyRoad",
                "icyPatches", "snowDrifts", "freezingOfWetRoads", "rime"}
_satiksme_brivs = {}    # iekārtas id → [lielākais redzētais vidējais ātrums, mērījumu skaits]
_satiksme_zonas = {}    # iekārtas id → zona (vietas nemainās; DB vaicā tikai jaunām)


def _skaitlis_vai_none(teksts):
    try:
        return float(teksts)
    except (TypeError, ValueError):
        return None


def _lv_koord(lat, lon):
    """(lat, lon) Latvijā; paraugos mēdz būt samainītas vietām."""
    if lat is None or lon is None:
        return None
    if 20 <= lat <= 29 and 55 <= lon <= 59:
        lat, lon = lon, lat
    return (round(lat, 5), round(lon, 5)) if 55 <= lat <= 59 and 20 <= lon <= 29 else None


def _datex_vietas(sakne):
    """MeasurementSiteTablePublication: iekārtas id → {lat, lon, nosaukums}."""
    vietas = {}
    for v in _datex_visi(sakne, "measurementSite"):
        lat, lon = None, None
        for k in list(_datex_visi(v, "coordinatesForDisplay")) + list(_datex_visi(v, "pointCoordinates")):
            lat, lon = _skaitlis_vai_none(_datex_teksts(k, "latitude")), _skaitlis_vai_none(_datex_teksts(k, "longitude"))
            break
        ll = _lv_koord(lat, lon)
        if v.get("id") and ll:
            nos = next((e.text.strip() for n in _datex_visi(v, "measurementSiteName") for e in _datex_visi(n, "value")
                        if e.text and e.text.strip()), None)
            vietas[v.get("id")] = {"lat": ll[0], "lon": ll[1], "nosaukums": nos}
    return vietas


def _datex_merijumi(sakne):
    """MeasuredDataPublication: katrai iekārtai vidējais ātrums (km/h, svērts ar plūsmu), plūsma (transp./h), laiks."""
    rez = []
    for sm in _datex_visi(sakne, "siteMeasurements"):
        ref = next(_datex_visi(sm, "measurementSiteReference"), None)
        sid = ref.get("id") if ref is not None else None
        if not sid:
            continue
        atrumi, plusmas = [], []
        for e in _datex_visi(sm, "averageVehicleSpeed"):
            v = _skaitlis_vai_none(_datex_teksts(e, "speed"))
            if v is not None and 0 < v < 200:
                skaits = _skaitlis_vai_none(e.get("numberOfInputValuesUsed")) or 1
                atrumi.append((v, skaits))
        for e in _datex_visi(sm, "vehicleFlow"):
            v = _skaitlis_vai_none(_datex_teksts(e, "vehicleFlowRate"))
            if v is not None and v >= 0:
                plusmas.append(v)
        ilgumi = [_skaitlis_vai_none(_datex_teksts(e, "duration")) for e in _datex_visi(sm, "travelTime")]
        laiks = _datex_teksts(next(_datex_visi(sm, "measurementTimeDefault"), sm), "timeValue") \
            or _datex_teksts(sm, "measurementTimeDefault")
        ll = _lv_koord(*(lambda k: (_skaitlis_vai_none(_datex_teksts(k, "latitude")),
                                    _skaitlis_vai_none(_datex_teksts(k, "longitude"))) if k is not None else (None, None))(
            next(_datex_visi(sm, "pointCoordinates"), None)))
        svars = sum(n for _, n in atrumi)
        rez.append({
            "id": sid, "laiks": laiks,
            "atrums": round(sum(v * n for v, n in atrumi) / svars, 1) if svars else None,
            "plusma_h": round(sum(plusmas)) if plusmas else None,
            "ilgums_s": next((i for i in ilgumi if i is not None), None),
            "lat": ll[0] if ll else None, "lon": ll[1] if ll else None,
        })
    return rez


def _satiksmes_limenis(atrums, brivs):
    if atrums is None or not brivs:
        return 3
    attieciba = atrums / brivs
    return 0 if attieciba >= 0.75 else 1 if attieciba >= 0.5 else 2


def _brivais_atrums(sid, atrums):
    with _kesas_slots:
        ieraksts = _satiksme_brivs.setdefault(sid, [0.0, 0])
        if atrums is not None:
            ieraksts[0] = max(ieraksts[0], min(atrums, 130.0))
            ieraksts[1] += 1
        return round(ieraksts[0], 1) if ieraksts[1] >= 5 and ieraksts[0] >= 30 else 80.0


def _rezga_zona(lat, lon):
    i, j = math.floor(lat / 0.09), math.floor(lon / 0.15)  # ~10 × 9 km
    return {"kods": f"rezgis_{i}_{j}", "nosaukums": "~10 km kvadrāts", "tips": "rezgis",
            "bbox": [round(j * 0.15, 5), round(i * 0.09, 5), round((j + 1) * 0.15, 5), round((i + 1) * 0.09, 5)]}


def _satiksmes_zonas(vietas):
    """iekārtas id → zona {kods, nosaukums, tips, bbox}; pašvaldība no regioni, citādi režģis."""
    jaunas = [(sid, v) for sid, v in vietas.items() if sid not in _satiksme_zonas]
    if jaunas:
        try:
            atrastas = vaicat(
                """select coalesce(json_object_agg(p.id, json_build_object('kods', r.kods, 'nosaukums', r.nosaukums,
                          'bbox', json_build_array(round(st_xmin(r.b)::numeric, 5), round(st_ymin(r.b)::numeric, 5),
                                                   round(st_xmax(r.b)::numeric, 5), round(st_ymax(r.b)::numeric, 5))))
                          filter (where r.kods is not null), '{}')
                   from unnest(%s::text[], %s::float8[], %s::float8[]) as p(id, lat, lon)
                   left join lateral (select kods, nosaukums, st_envelope(geom)::box2d as b from regioni
                                      where tips in ('novads', 'valstspilseta')
                                        and st_contains(geom, st_setsrid(st_makepoint(p.lon, p.lat), 4326))
                                      limit 1) r on true""",
                ([s for s, _ in jaunas], [v["lat"] for _, v in jaunas], [v["lon"] for _, v in jaunas]), timeout="5s")
            with _kesas_slots:
                for sid, v in jaunas:
                    z = atrastas.get(sid)
                    _satiksme_zonas[sid] = {**z, "tips": "regions"} if z else _rezga_zona(v["lat"], v["lon"])
        except psycopg.Error:
            return {sid: _satiksme_zonas.get(sid) or _rezga_zona(v["lat"], v["lon"]) for sid, v in vietas.items()}
    return {sid: _satiksme_zonas[sid] for sid in vietas}


def _satiksmes_punkti_un_zonas(vietas_dati, merijumi_dati):
    vietas = dict(vietas_dati["vietas"]) if vietas_dati else {}
    if merijumi_dati:
        vietas.update(merijumi_dati["vietas"])  # ja minūšu kopā ir arī vietu tabula
        for m in merijumi_dati["merijumi"]:  # mērījums ar savām koordinātām, bet bez vietu tabulas
            if m["id"] not in vietas and m["lat"] is not None:
                vietas[m["id"]] = {"lat": m["lat"], "lon": m["lon"], "nosaukums": None}
    merijumi = {m["id"]: m for m in (merijumi_dati or {}).get("merijumi", [])}
    zonas_pec_id = _satiksmes_zonas(vietas)
    punkti, zonas = [], {}
    for sid, v in vietas.items():
        m = merijumi.get(sid, {})
        brivs = _brivais_atrums(sid, m.get("atrums"))
        limenis = _satiksmes_limenis(m.get("atrums"), brivs)
        z = zonas_pec_id[sid]
        punkti.append({"id": sid, "lat": v["lat"], "lon": v["lon"], "nosaukums": v["nosaukums"], "zona": z["kods"],
                       "atrums": m.get("atrums"), "atrums_brivs": brivs, "plusma_h": m.get("plusma_h"),
                       "limenis": limenis, "limenis_teksts": SATIKSMES_LIMENI[limenis], "laiks": m.get("laiks")})
        zonas.setdefault(z["kods"], {**z, "punkti": []})["punkti"].append(punkti[-1])
    rez = []
    for z in zonas.values():
        ar_datiem = [p for p in z.pop("punkti") if p["atrums"] is not None]
        svari = [max(p["plusma_h"] or 0, 1) for p in ar_datiem]
        if ar_datiem:
            vid = sum(p["atrums"] * s for p, s in zip(ar_datiem, svari)) / sum(svari)
            brivs = sum(p["atrums_brivs"] * s for p, s in zip(ar_datiem, svari)) / sum(svari)
            limenis = _satiksmes_limenis(vid, brivs)
        else:
            vid, brivs, limenis = None, None, 3
        rez.append({**z, "limenis": limenis, "limenis_teksts": SATIKSMES_LIMENI[limenis],
                    "atrums_vid": round(vid, 1) if vid is not None else None,
                    "atrums_brivs": round(brivs, 1) if brivs is not None else None,
                    "plusma_h": sum(p["plusma_h"] or 0 for p in ar_datiem) if ar_datiem else None,
                    "merijumi": len(ar_datiem), "iekartas": sum(1 for p in punkti if p["zona"] == z["kods"]),
                    "laiks": max((p["laiks"] for p in ar_datiem if p["laiks"]), default=None)})
    rez.sort(key=lambda z: (z["limenis"] == 3, -z["limenis"], z["nosaukums"] or ""))
    return punkti, rez


def _satiksmes_stacijas(kopas):
    rez, redzeti = [], set()
    for kods, dati in kopas:
        for i in (dati or {}).get("ieraksti", []):
            if (kods, i["id"]) in redzeti:
                continue
            redzeti.add((kods, i["id"]))
            slidens = i["xsi"] == "WeatherRelatedRoadConditions" or bool(SLIDENI_KODI & set(i["kodi"].values()))
            rez.append({"id": i["id"], "lat": i["punkti"][0][0], "lon": i["punkti"][0][1],
                        "nosaukums": _kodu_apraksts(i) or CELU_XSI_NOS.get(i["xsi"], "Ceļa apstākļi"),
                        "slidens": slidens, "cela_temp": _skaitlis_vai_none(i["cela_temp"]),
                        "gaisa_temp": _skaitlis_vai_none(i["gaisa_temp"]), "laiks": i["laiks"], "avots": kods})
    return rez


def _json_robezas(obj):
    """JSON atbildē: katrs objekts ar platumu/garumu un gaidīšanas laiku (min vai s pēc lauka nosaukuma)."""
    rez = []

    def lauks(d, *dalas):
        return next((v for k, v in d.items() if any(x in k.lower() for x in dalas)), None)

    def staiga(o):
        if isinstance(o, list):
            for x in o:
                staiga(x)
        elif isinstance(o, dict):
            lat, lon = _skaitlis_vai_none(lauks(o, "lat")), _skaitlis_vai_none(lauks(o, "lon", "lng"))
            ll = _lv_koord(lat, lon)
            gaid = next(((k, _skaitlis_vai_none(v)) for k, v in o.items()
                         if any(x in k.lower() for x in ("wait", "gaid", "delay", "queue", "time")) and
                         _skaitlis_vai_none(v) is not None), None)
            if ll and gaid:
                minutes = gaid[1] / 60 if any(x in gaid[0].lower() for x in ("sec", "_s")) else gaid[1]
                rez.append({"id": str(lauks(o, "id") or len(rez)), "lat": ll[0], "lon": ll[1],
                            "nosaukums": str(lauks(o, "name", "nosauk", "title") or "Robežšķērsošanas vieta"),
                            "virziens": lauks(o, "direction", "virzien"), "gaidisana_min": round(minutes),
                            "laiks": lauks(o, "updated", "timestamp", "laiks", "date")})
            for v in o.values():
                if isinstance(v, (list, dict)):
                    staiga(v)
    staiga(obj)
    return rez


def _satiksmes_robezas(dati):
    """Robežpunkti: situāciju ieraksti ar kavējumu (delayTimeValue, s) vai mērījumi ar travelTime/duration (s)."""
    if not dati:
        return []
    if "json" in dati:
        return _json_robezas(dati["json"])
    rez = []
    for i in dati["ieraksti"]:
        s = _skaitlis_vai_none(i["kavejums_s"])
        rez.append({"id": i["id"], "lat": i["punkti"][0][0], "lon": i["punkti"][0][1],
                    "nosaukums": i["apraksts"] or _kodu_apraksts(i) or "Robežšķērsošanas vieta", "virziens": i["virziens"],
                    "gaidisana_min": round(s / 60) if s is not None else None, "laiks": i["laiks"]})
    for m in dati["merijumi"]:
        v = dati["vietas"].get(m["id"]) or ({"lat": m["lat"], "lon": m["lon"], "nosaukums": None} if m["lat"] else None)
        if v:
            rez.append({"id": m["id"], "lat": v["lat"], "lon": v["lon"], "nosaukums": v["nosaukums"] or "Robežšķērsošanas vieta",
                        "virziens": None, "gaidisana_min": round(m["ilgums_s"] / 60) if m["ilgums_s"] is not None else None,
                        "laiks": m["laiks"]})
    return rez


def _satiksme_dati():
    dati = _nap_vairakas([(m, sek) for _k, m, sek, _c, _n in SATIKSME_KOPAS])
    pec_koda = {k: dati.get(m) for k, m, *_ in SATIKSME_KOPAS}
    punkti, zonas = _satiksmes_punkti_un_zonas(pec_koda["vietas"], pec_koda["merijumi"])
    return {
        "avots": "lvc-nap", "laiks": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "kopas": {k: {"konfigurets": m in dati, "pieejams": dati.get(m) is not None,
                      "kluda": _nap_kludas_teksts.get(m) if m in dati else None, "nosaukums": n,
                      "datu_kopa_url": f"https://transportdata.gov.lv/card/{c}", "licence": "CC0 1.0",
                      "licences_url": "https://creativecommons.org/publicdomain/zero/1.0/"}
                  for k, m, _s, c, n in SATIKSME_KOPAS},
        "zonas": zonas, "punkti": punkti,
        "stacijas": _satiksmes_stacijas([(k, pec_koda[k]) for k in ("slidens_meteo", "slidens_uzturetaji", "slidens_sic")]),
        "robezas": _satiksmes_robezas(pec_koda["robezas"]),
        "piezime": "Līmenis: vidējais ātrums pret brīvas plūsmas ātrumu iekārtā (≥ 75 % brīvs, ≥ 50 % lēns, citādi "
                   "sastrēgums). Brīvas plūsmas ātrums ir novērtējums, nevis atļautais ātrums.",
    }


def _satiksme_debug():
    """Katras kopas neapstrādātās atbildes sākums (2 KB) — tikai ar MAP_DEBUG=1 (VPS env), atslēgas netiek rādītas."""
    rez = {}
    for k, m, *_ in SATIKSME_KOPAS + [(f"celi_{t}", v) for v, t, _c in NAP_KOPAS]:
        atslega = os.environ.get(m, "").strip()
        if not atslega:
            rez[k] = {"konfigurets": False}
            continue
        try:
            saturs = _nap_lejupieladet(atslega, m)
            rez[k] = {"konfigurets": True, "baiti": len(saturs), "faila_id": _nap_faila_id.get(m, "1"),
                      "sakums": saturs[:2048].decode("utf-8", "replace")}
        except Exception as e:
            rez[k] = {"konfigurets": True, "kluda": _nap_kludas_apraksts(e)}
    return rez


def satiksme(q):
    if q.get("debug", [""])[0] == "1" and os.environ.get("MAP_DEBUG", "").strip() == "1":
        return {"debug": _satiksme_debug()}
    return _kesots("satiksme", 60, _satiksme_dati)


# ---- Biežāk meklētais: POST /api/meklejumi, GET /api/meklejumi/top (tabula meklejumi, shema.sql) ----
# Glabā tikai normalizētu vaicājumu un skaitītājus (bez IP vai citiem lietotāja datiem).

MEKLEJUMI_MINUTE = 60          # ierakstu skaits minūtē visam procesam; pārējos klusi izmet
MEKLEJUMI_DIENAS = 14
_meklejumi_slots = threading.Lock()
_meklejumi_logs = [0.0, 0]     # [minūtes sākums, ierakstu skaits tajā]


def _meklejums_normalizets(teksts):
    """Mazie burti, viena atstarpe; None, ja nav ko skaitīt (tukšs, >100 zīmes vai ar cipariem — adrese)."""
    if not isinstance(teksts, str):
        return None
    t = " ".join(teksts.lower().split())
    if not t or len(t) > 100 or re.search(r"\d", t) or not re.search(r"\w", t):
        return None
    return t


def _meklejumi_atlauts():
    with _meklejumi_slots:
        tagad = time.time()
        if tagad - _meklejumi_logs[0] >= 60:
            _meklejumi_logs[:] = [tagad, 0]
        if _meklejumi_logs[1] >= MEKLEJUMI_MINUTE:
            return False
        _meklejumi_logs[1] += 1
        return True


def meklejumi_pievienot(dati):
    """{vaicajums, atpazits: true, klikskis?: bool}. Skaita tikai atpazītus vaicājumus; vienmēr 204."""
    if not isinstance(dati, dict) or dati.get("atpazits") is not True:
        return
    vaicajums = _meklejums_normalizets(dati.get("vaicajums"))
    if not vaicajums or not _meklejumi_atlauts():
        return
    klikskis = dati.get("klikskis") is True
    with psycopg.connect(DSN, connect_timeout=5) as conn, conn.cursor() as cur:
        cur.execute("set statement_timeout = '2s'")
        cur.execute(
            """insert into meklejumi (vaicajums, skaits, klikski) values (%(v)s, %(s)s, %(k)s)
               on conflict (vaicajums) do update set skaits = meklejumi.skaits + %(s)s,
                 klikski = meklejumi.klikski + %(k)s, pedejais = now()""",
            {"v": vaicajums, "s": 0 if klikskis else 1, "k": 1 if klikskis else 0},
        )


def meklejumi_top(q):
    n = int(_skaitlis(q, "n", 1, 10) or 3)

    def ielade():
        return vaicat(
            """select coalesce(json_agg(vaicajums order by skaits desc, klikski desc, pedejais desc), '[]') from (
                 select vaicajums, skaits, klikski, pedejais from meklejumi
                 where pedejais > now() - make_interval(days => %s)
                 order by skaits desc, klikski desc, pedejais desc limit 10) m""",
            (MEKLEJUMI_DIENAS,),
            timeout="2s",
        )

    return {"vaicajumi": _kesots("meklejumi_top", 60, ielade)[:n]}


# ==== Statuss (production/statuss.html) — sākums ====
# Fona pavediens API procesā ik 15 min pārbauda vietni, API/DB un katru datu avotu (visas pārbaudes reizē, katrai
# ≤ 10 s; pieprasījumus tas nebloķē) un ieraksta vienu rindu par katru komponentu tabulā statuss_parbaudes.
# Raksta ar MAP_DB_OWNER_DSN (tabulu izveido pats, ja shēma vēl nav palaista), glabā 8 dienas. Ja rakstīt nevar,
# vēsture ir tikai atmiņā līdz pārstartēšanai. GET /api/statuss: stāvoklis + pēdējie 96 intervāli + pieejamība 7 dienās.

STATUSS_DSN = os.environ.get("MAP_DB_OWNER_DSN", "")
STATUSS_VIETNE = os.environ.get("STATUSS_VIETNE", "https://map.repo.lv/")
STATUSS_OSM_FLIZE = "https://tile.openstreetmap.org/7/72/39.png"  # Latvija; viena flīze ik 15 min
STATUSS_INTERVALS = 15 * 60
STATUSS_TAIMAUTS = 10
STATUSS_JOSLAS = 96  # 24 h
STATUSS_SHEMA = """
create table if not exists statuss_parbaudes (
  id         bigserial primary key,
  komponents text not null,
  laiks      timestamptz not null default now(),
  stavoklis  text not null,
  zinojums   text,
  ilgums_ms  int
);
create index if not exists statuss_parbaudes_laiks_idx on statuss_parbaudes (laiks);
-- nav_datu: avots vēl nav ielādēts vai nav konfigurēts (pelēks, neskaitās pieejamībā)
alter table statuss_parbaudes drop constraint if exists statuss_parbaudes_stavoklis_check;
alter table statuss_parbaudes add constraint statuss_parbaudes_stavoklis_check
  check (stavoklis in ('darbojas', 'traucejumi', 'nedarbojas', 'nav_datu'));
grant select on statuss_parbaudes to map_api;
"""  # tas pats bloks ir src/karte/db/shema.sql

_CC0 = ("CC0 1.0", "https://creativecommons.org/publicdomain/zero/1.0/")
STATUSS_KOMPONENTI = [  # kods, nosaukums, apraksts, avots (nosaukums, datu kopa, licence, licences saite)
    ("vietne", "Karte (map.repo.lv)", "Vai lapa atveras", ("map.repo.lv pirmkods", "https://github.com/noiseparty/hakatons", None, None)),
    ("api", "API un datubāze", "Kartes objekti, slāņi un avoti", None),
    ("adreses", "Adrešu meklēšana", "VZD adrešu reģistrs kartes datubāzē",
     ("VZD Valsts adrešu reģistra atvērtie dati", "https://data.gov.lv/dati/lv/dataset/varis-atvertie-dati",
      "CC BY 4.0", "https://creativecommons.org/licenses/by/4.0/")),
    ("bridinajumi", "LVĢMC brīdinājumi", "data.gov.lv datne ir pieejama un nolasāma",
     ("LVĢMC hidrometeoroloģiskie brīdinājumi", "https://data.gov.lv/dati/lv/dataset/hidrometeorologiskie-bridinajumi", *_CC0)),
    ("pludi", "Plūdu riska zonas", "LVĢMC karšu serviss (ĢeoLatvija.lv)",
     ("LVĢMC 3. cikla plūdu riska kartes",
      "https://data.gov.lv/dati/lv/dataset/3-cikla-latvijas-pldu-postjumu-vietu-un-pldu-riska-kartes1", *_CC0)),
    ("udens", "Ūdens līmenis upēs", "Jaunākā LVĢMC mērījuma vecums",
     ("LVĢMC hidroloģiskie operatīvie dati", "https://data.gov.lv/dati/lv/dataset/hidrometeorologiskie-noverojumi", *_CC0)),
    ("ca_plani", "Evakuācijas un izmitināšanas vietas", "No pašvaldību civilās aizsardzības plāniem",
     ("Pašvaldību CA plāni", "https://github.com/lata-org/ai-open-data-2026-hakatons/tree/main/ca-plani-hakatons",
      "Oficiāls dokuments, nav autortiesību objekts", "https://likumi.lv/ta/id/5138-autortiesibu-likums")),
    ("patvertnes", "Patvertnes", "VUGD / 112.lv patvertņu saraksts kartes datubāzē",
     ("Publiskās patvertnes (112.lv)", "https://www.112.lv/lv/patvertnes", "Licence nav norādīta", None)),
    ("prognozes", "Laika prognoze", "Cik sena ir LVĢMC prognoze kartes lentē",
     ("LVĢMC meteoroloģiskās prognozes apdzīvotām vietām",
      PROGNOZU_AVOTS["url"], *_CC0)),
    ("zibens", "Zibens (pēdējās 30 min)", "FMI zibens novērojumi Latvijas apgabalā",
     ("Ilmatieteen laitos (FMI) atvērtie dati", "https://en.ilmatieteenlaitos.fi/open-data",
      "CC BY 4.0", "https://creativecommons.org/licenses/by/4.0/")),
    ("augsne", "Nokrišņi un augsnes mitrums", "Open-Meteo modeļa dati (pārbaude: Ogre)",
     ("Open-Meteo", "https://open-meteo.com/", "CC BY 4.0", "https://creativecommons.org/licenses/by/4.0/")),
    ("celi", "Ceļu slēgumi un negadījumi", "LVC DATEX II caur Nacionālo piekļuves punktu",
     ("LVC ceļu notikumi (transportdata.gov.lv)", "https://transportdata.gov.lv/card/75611a36-e66b-40cf-af2c-69db48c278cf",
      *_CC0)),
    ("satiksme", "Satiksme zonās", "LVC satiksmes uzskaites iekārtas: vietas un minūtes ātrums",
     ("LVC satiksmes intensitāte un ātrums (transportdata.gov.lv)",
      "https://transportdata.gov.lv/card/ed1f0d2c-6ad8-4823-b132-71fc69993d1c", *_CC0)),
    ("robezas", "Robežu gaidīšanas laiks", "LVC robežšķērsošanas vietu gaidīšanas laiks",
     ("LVC robežšķērsošanas gaidīšanas laiks (transportdata.gov.lv)",
      "https://transportdata.gov.lv/card/cb730ba2-6466-45b5-99e4-66b9bde30dae", *_CC0)),
    ("osm", "Karšu fons (OpenStreetMap)", "Vai kartes attēli ielādējas",
     ("OpenStreetMap", "https://www.openstreetmap.org/copyright", "ODbL 1.0", "https://opendatacommons.org/licenses/odbl/1-0/")),
]
STATUSS_SMAGUMS = {"nav_datu": -1, "darbojas": 0, "traucejumi": 1, "nedarbojas": 2}
STATUSS_PROGNOZE_VECA_H = 24  # LVĢMC prognozi atjauno vairākas reizes dienā


def _sekundes(ms):
    return f"{ms / 1000:.1f}".replace(".", ",") + " s"


def _skaits(n, viens, vairaki):  # 1, 21, 31… → vienskaitlis (bet ne 11)
    return f"{n} {viens if n % 10 == 1 and n % 100 != 11 else vairaki}"


def _laiks_pirms(sekundes):
    return f"{round(sekundes / 60)} min" if sekundes < 5400 else f"{round(sekundes / 3600)} h"


def _parb_vietne():
    lapa = _lejupieladet(STATUSS_VIETNE, timeout=STATUSS_TAIMAUTS).decode("utf-8", "replace")
    return ("darbojas", None) if "Krīzes karte" in lapa else ("nedarbojas", "Lapa atveras, bet tās saturs nav pareizs")


def _parb_api():
    n = vaicat("select count(*)::int from objekti where derigs_lidz is null or derigs_lidz > now()", timeout="5s")
    return ("darbojas", _skaits(n, "objekts", "objekti") + " kartē") if n else ("nedarbojas", "Datubāzē nav neviena objekta")


def _parb_adreses():
    atrastas = adreses({"q": ["brivibas iela 1 riga"]})
    return ("darbojas", None) if atrastas else ("nedarbojas", "Pārbaudes adrese netika atrasta")


def _parb_bridinajumi():
    tagad, speka = _riga_tagad(), 0
    for url, kolonnas in ((BRIDINAJUMI_META, {"WEATHER_WARNING_EV_ID", "INTENSITY_LV", "TIME_FROM", "TIME_TILL"}),
                          (BRIDINAJUMI_POLIGONI, {"WEATHER_WARNING_EV_ID", "POLIGON_ID", "LAT", "LON"})):
        lasitajs = csv.DictReader(io.StringIO(_lejupieladet(url, timeout=STATUSS_TAIMAUTS).decode("utf-8-sig")))
        rindas = list(lasitajs)
        if not kolonnas <= set(lasitajs.fieldnames or ()):
            return "nedarbojas", "Datnes formāts ir mainījies"
        if url == BRIDINAJUMI_META:
            speka = sum(1 for r in rindas if not (_lv_laiks(r["TIME_TILL"]) or tagad) < tagad)
    return "darbojas", "Spēkā " + _skaits(speka, "brīdinājums", "brīdinājumi") if speka else "Spēkā esošu brīdinājumu nav"


def _parb_pludi():
    # tas pats GetFeatureInfo kā _pludu_serviss, bet ar STATUSS_TAIMAUTS (tur 25 s); Ogre, derīga ir arī "nav zonā"
    _veids, cels, slani = PLUDU_SERVISI[0]
    lat, lon, d = 56.816, 24.605, 0.0002
    parametri = {
        "service": "WMS", "version": "1.3.0", "request": "GetFeatureInfo", "styles": "", "crs": "EPSG:4326",
        "layers": ",".join(slani), "query_layers": ",".join(slani), "info_format": "application/geojson",
        "bbox": f"{lat - d},{lon - d},{lat + d},{lon + d}", "width": 11, "height": 11, "i": 5, "j": 5,
        "feature_count": 10,
    }
    url = PLUDU_WMS + cels + "?" + "&".join(f"{k}={v}" for k, v in parametri.items())
    try:
        atbilde = _lejupieladet(url, timeout=STATUSS_TAIMAUTS)
    except Exception as e:
        if _statuss_kluda(e).startswith("Neatbildēja"):  # lēns, bet strādājošs serviss (mēdz atbildēt 1–30 s)
            return "traucejumi", f"Neatbildēja {STATUSS_TAIMAUTS} s laikā (serviss mēdz atbildēt lēni)"
        raise
    if "features" not in json.loads(atbilde):
        return "nedarbojas", "Atbildes formāts nav nolasāms"
    return "darbojas", None


def _parb_prognozes():
    # bez jauna lejupielādes pieprasījuma: tikai /api/prognozes kešs (16,6 MB datne; to ielādē kartes atvēršana)
    from email.utils import parsedate_to_datetime
    with _kesas_slots:
        ieraksts = _kesa.get("prognozes")
    if not ieraksts:
        return "nav_datu", "Kopš API pārstartēšanas prognoze vēl nav ielādēta"
    mainits = ieraksts[1].get("mainits")
    if not mainits:
        return "traucejumi", "Prognozes datnei nav norādīts atjaunošanas laiks"
    vecums = (datetime.now(timezone.utc) - parsedate_to_datetime(mainits)).total_seconds()
    zinojums = f"Prognoze atjaunota pirms {_laiks_pirms(max(vecums, 0))}"
    return ("traucejumi" if vecums > STATUSS_PROGNOZE_VECA_H * 3600 else "darbojas"), zinojums


def _parb_udens():
    n, vecums = vaicat("""select json_build_array(count(*), extract(epoch from now() - max(derigs_no))::int)
                          from objekti where kategorija = 'udens_limenis'""", timeout="5s")
    if not n or vecums is None:
        return "nedarbojas", "Datubāzē nav mērījumu"
    zinojums = f"{_skaits(n, 'stacija', 'stacijas')}, jaunākais mērījums pirms {_laiks_pirms(max(vecums, 0))}"
    return ("traucejumi" if vecums > udens_limenis.DERIGS_H * 3600 else "darbojas"), zinojums


def _parb_ca_plani():
    skaits = vaicat("""select coalesce(json_object_agg(kategorija, n), '{}') from (
                         select kategorija, count(*)::int n from objekti where avots = 'ca-plani' group by 1) x""",
                    timeout="5s")
    p, i = skaits.get("evakuacijas_punkts", 0), skaits.get("izmitinasana", 0)
    zinojums = f"{_skaits(p, 'pulcēšanās vieta', 'pulcēšanās vietas')}, {_skaits(i, 'izmitināšanas vieta', 'izmitināšanas vietas')}"
    return ("darbojas" if p and i else "traucejumi" if p or i else "nedarbojas"), zinojums


def _parb_patvertnes():
    n = vaicat("select count(*)::int from objekti where kategorija = 'patvertne'", timeout="5s")
    return ("darbojas", _skaits(n, "patvertne", "patvertnes")) if n else ("nedarbojas", "Datubāzē nav patvertņu")


def _parb_osm():
    if not _lejupieladet(STATUSS_OSM_FLIZE, timeout=STATUSS_TAIMAUTS).startswith(b"\x89PNG"):
        return "nedarbojas", "Atbilde nav kartes attēls"
    return "darbojas", None


def _parb_zibens():
    # caur to pašu kešu kā /api/zibens (60 s): ne vairāk FMI pieprasījumu kā kartei
    dati = _kesots("zibens_fmi", 60, _fmi_zibens)
    vecums = (datetime.now(timezone.utc) - datetime.fromisoformat(dati["lidz"])).total_seconds()
    if vecums > 300:  # _kesots atdeva veco vērtību: FMI neatbild
        return "nedarbojas", f"FMI neatbild; pēdējie dati pirms {_laiks_pirms(vecums)}"
    n = len(dati["zibeni"])
    return "darbojas", (_skaits(n, "zibens", "zibeņi") + " Latvijā" if n else "Pēdējās 30 min zibens nav reģistrēts")


_statuss_augsne = [None, 0.0]  # [pēdējā atbilde, kad tā parādījās]: _kesots kļūdas gadījumā atdod veco vērtību


def _parb_augsne():
    # caur /api/augsne kešu (1 h vienai vietai): viens Open-Meteo pieprasījums stundā
    dati = augsne({"lat": ["56.82"], "lon": ["24.6"]})
    if dati is not _statuss_augsne[0]:
        _statuss_augsne[:] = [dati, time.time()]
    vecums = time.time() - _statuss_augsne[1]
    if vecums > 2 * 3600:  # kešs ir 1 h; ja atbilde 2 h nav mainījusies, Open-Meteo neatbild
        return "nedarbojas", f"Open-Meteo neatbild; pēdējie dati pirms {_laiks_pirms(vecums)}"
    if dati["augsne"] is None:
        return "traucejumi", "Augsnes mitruma vērtības nav"
    return "darbojas", f"Ogrē augsne {dati['augsne']}, {dati['dienas_pagatne']} dienās {_skaitlis_lv(dati['nokrisni_pagatne_mm'])} mm"


def _parb_celi():
    # tās pašas kopas un kešs (5 min) kā /api/celi; bez NAP atslēgām avots nav konfigurēts — pelēks, nevis sarkans
    kopas = celu_notikumi_visi()
    if not kopas:
        return "nav_datu", "Avots vēl nav pieslēgts (nav NAP atslēgu)"
    nepieejamas = sum(n is None for _, n in kopas)
    if nepieejamas == len(kopas):
        return "nedarbojas", "Neviena LVC datu kopa neatbild"
    tagad = datetime.now(timezone.utc)

    def speka(x):  # kā celi(): sācies un nav beidzies (celu_notikumi_visi dod rindas bez "aktivs")
        no, lidz = _datex_laiks(x.get("no")), _datex_laiks(x.get("lidz"))
        return (not no or no <= tagad) and (not lidz or lidz >= tagad)
    aktivi = sum(1 for _, n in kopas if n for x in n if speka(x))
    zinojums = "Spēkā " + _skaits(aktivi, "notikums", "notikumi") if aktivi else "Spēkā esošu notikumu nav"
    if nepieejamas:
        return "traucejumi", f"{zinojums}; {nepieejamas} no {len(kopas)} datu kopām neatbild"
    return "darbojas", zinojums


def _parb_satiksme():
    # tas pats kešs kā /api/satiksme; bez atslēgām — pelēks
    d = satiksme({})
    vietas, merijumi = d["kopas"]["vietas"], d["kopas"]["merijumi"]
    if not (vietas["konfigurets"] and merijumi["konfigurets"]):
        return "nav_datu", "Nav konfigurēts (nav NAP atslēgu)"
    if not merijumi["pieejams"]:
        return "nedarbojas", "Ātruma dati neatbild" + (f" ({merijumi['kluda']})" if merijumi["kluda"] else "")
    ar_datiem = [z for z in d["zonas"] if z["limenis"] != 3]
    if not ar_datiem:
        return "traucejumi", "Nevienā zonā nav jaunu mērījumu"
    lenas = sum(1 for z in ar_datiem if z["limenis"] >= 1)
    zinojums = f"{_skaits(len(ar_datiem), 'zona', 'zonas')} ar datiem" + (f", {lenas} ar lēnu satiksmi vai sastrēgumu" if lenas else "")
    return ("darbojas" if vietas["pieejams"] else "traucejumi"), zinojums


def _parb_robezas():
    d = satiksme({})
    k = d["kopas"]["robezas"]
    if not k["konfigurets"]:
        return "nav_datu", "Nav konfigurēts (nav NAP atslēgas)"
    if not k["pieejams"]:
        return "nedarbojas", "Datu kopa neatbild" + (f" ({k['kluda']})" if k["kluda"] else "")
    n = len(d["robezas"])
    return ("darbojas", _skaits(n, "robežpunkts", "robežpunkti")) if n else ("traucejumi", "Atbilde ir, bet robežpunktu nav")


# kods → (pārbaude, virs cik ms "atbild lēni")
STATUSS_PARBAUDES = {
    "vietne": (_parb_vietne, 5000), "api": (_parb_api, 3000), "adreses": (_parb_adreses, 2500),
    "bridinajumi": (_parb_bridinajumi, 8000), "pludi": (_parb_pludi, 8000), "udens": (_parb_udens, 3000),
    "ca_plani": (_parb_ca_plani, 3000), "patvertnes": (_parb_patvertnes, 3000), "prognozes": (_parb_prognozes, 1000),
    "zibens": (_parb_zibens, 8000), "augsne": (_parb_augsne, 8000), "celi": (_parb_celi, 8000),
    "satiksme": (_parb_satiksme, 8000), "robezas": (_parb_robezas, 8000),
    "osm": (_parb_osm, 5000),
}


def _statuss_kluda(e):
    import socket
    import urllib.error
    if isinstance(e, urllib.error.HTTPError):
        return f"Avots atbild ar kļūdu (HTTP {e.code})"
    if isinstance(e, (TimeoutError, socket.timeout)) or isinstance(getattr(e, "reason", None), (TimeoutError, socket.timeout)):
        return f"Neatbildēja {STATUSS_TAIMAUTS} s laikā"
    if isinstance(e, urllib.error.URLError):
        return "Avots nav sasniedzams"
    if isinstance(e, psycopg.Error):
        return "Datubāze nav pieejama"
    if isinstance(e, Kluda):
        return str(e)
    if isinstance(e, (ValueError, KeyError, TypeError)):
        return "Atbildes formāts nav nolasāms"
    return f"Kļūda ({type(e).__name__})"


_statuss_atmina = []  # [(komponents, laiks, stavoklis, zinojums, ilgums_ms)] — šī procesa pārbaudes (ja DB nav)
_statuss_tabula = [False]  # vai STATUSS_SHEMA jau palaista šajā procesā


def _statuss_parbaudit_visu():
    laiks = datetime.now(timezone.utc)

    def viena(funkcija, leni_ms):
        sakums = time.monotonic()
        try:
            stavoklis, zinojums = funkcija()
        except Exception as e:
            stavoklis, zinojums = "nedarbojas", _statuss_kluda(e)
        ms = round((time.monotonic() - sakums) * 1000)
        if stavoklis == "darbojas" and ms > leni_ms:
            stavoklis, zinojums = "traucejumi", f"Atbild lēni ({_sekundes(ms)})"
        return stavoklis, zinojums or f"Atbild {_sekundes(ms)}", ms

    pavedieni = ThreadPoolExecutor(max_workers=len(STATUSS_PARBAUDES))
    darbi = {kods: pavedieni.submit(viena, *p) for kods, p in STATUSS_PARBAUDES.items()}
    pavedieni.shutdown(wait=False)  # kas nav beidzis līdz termiņam, beigsies pats (ar savu taimautu)
    termins = time.monotonic() + STATUSS_TAIMAUTS + 2
    rindas = []
    for kods, darbs in darbi.items():
        try:
            rindas.append((kods, laiks, *darbs.result(timeout=max(0.0, termins - time.monotonic()))))
        except Exception:  # termiņš
            # plūdu WMS mēdz atbildēt 1–30 s; lēns, bet strādājošs serviss — traucējumi, nevis "nedarbojas"
            stavoklis = "traucejumi" if kods == "pludi" else "nedarbojas"
            rindas.append((kods, laiks, stavoklis, f"Neatbildēja {STATUSS_TAIMAUTS} s laikā", None))

    with _kesas_slots:
        _statuss_atmina.extend(rindas)
        robeza = laiks - timedelta(days=8)
        _statuss_atmina[:] = [r for r in _statuss_atmina if r[1] > robeza]
        _kesa.pop("statuss", None)
    if not STATUSS_DSN:
        return
    try:
        with psycopg.connect(STATUSS_DSN, connect_timeout=5) as conn, conn.cursor() as cur:
            cur.execute("set statement_timeout = '10s'")
            if not _statuss_tabula[0]:
                cur.execute(STATUSS_SHEMA)
                _statuss_tabula[0] = True
            cur.executemany("""insert into statuss_parbaudes (komponents, laiks, stavoklis, zinojums, ilgums_ms)
                               values (%s, %s, %s, %s, %s)""", rindas)
            cur.execute("delete from statuss_parbaudes where laiks < now() - interval '8 days'")
    except psycopg.Error as e:
        print(f"statuss: neizdevās saglabāt: {e}", file=sys.stderr)


def _statuss_cikls():
    time.sleep(5)  # lai serveris paspēj sākt
    while True:
        try:
            _statuss_parbaudit_visu()
        except Exception as e:  # pavediens nedrīkst apstāties
            print(f"statuss: {e!r}", file=sys.stderr)
        time.sleep(STATUSS_INTERVALS - time.time() % STATUSS_INTERVALS + 20)  # :00:20, :15:20, …


def _statuss_dati():
    tagad = datetime.now(timezone.utc)
    rindas = {}
    try:
        no_db = vaicat("""select coalesce(json_agg(json_build_array(komponents, laiks, stavoklis, zinojums, ilgums_ms)
                                            order by laiks), '[]')
                          from statuss_parbaudes where laiks > now() - interval '7 days'""", timeout="5s")
        for k, iso, s, z, ms in no_db:
            laiks = datetime.fromisoformat(iso)
            rindas[(k, laiks.replace(microsecond=0))] = (k, laiks, s, z, ms)
    except Exception as e:  # tabulas vēl nav vai DB nav pieejama — rāda šī procesa pārbaudes
        print(f"statuss: vēsturi neizdevās nolasīt: {e!r}", file=sys.stderr)
    robeza = tagad - timedelta(days=7)
    with _kesas_slots:
        for r in _statuss_atmina:
            if r[1] > robeza:
                rindas.setdefault((r[0], r[1].replace(microsecond=0)), r)

    pec_komponenta = {}
    for r in sorted(rindas.values(), key=lambda r: r[1]):
        pec_komponenta.setdefault(r[0], []).append(r)
    sis = int(tagad.timestamp()) // STATUSS_INTERVALS
    komponenti = []
    for kods, nosaukums, apraksts, avots in STATUSS_KOMPONENTI:
        parbaudes = pec_komponenta.get(kods, [])
        sliktakais = {}  # intervāla nr → sliktākais stāvoklis tajā
        for _, laiks, s, _z, _ms in parbaudes:
            nr = int(laiks.timestamp()) // STATUSS_INTERVALS
            if STATUSS_SMAGUMS[s] >= STATUSS_SMAGUMS.get(sliktakais.get(nr), -1):
                sliktakais[nr] = s
        pedeja = parbaudes[-1] if parbaudes else None
        if pedeja is None:
            stavoklis, zinojums = "nav_datu", "Vēl nav pārbaudīts"
        elif tagad - pedeja[1] > timedelta(seconds=2.5 * STATUSS_INTERVALS):
            stavoklis, zinojums = "nav_datu", f"Pēdējā pārbaude pirms {_laiks_pirms((tagad - pedeja[1]).total_seconds())}"
        else:
            stavoklis, zinojums = pedeja[2], pedeja[3]
        ar_datiem = [s for s in sliktakais.values() if s != "nav_datu"]
        komponenti.append({
            "kods": kods, "nosaukums": nosaukums, "apraksts": apraksts,
            "avots": dict(zip(("nosaukums", "url", "licence", "licences_url"), avots)) if avots else None,
            "stavoklis": stavoklis, "zinojums": zinojums,
            "parbaudits": pedeja[1].isoformat(timespec="seconds") if pedeja else None,
            "ilgums_ms": pedeja[4] if pedeja else None,
            "joslas": [{"sakums": datetime.fromtimestamp(nr * STATUSS_INTERVALS, timezone.utc).isoformat(),
                        "stavoklis": None if sliktakais.get(nr) == "nav_datu" else sliktakais.get(nr)} for nr in range(sis - STATUSS_JOSLAS + 1, sis + 1)],
            "pieejamiba_7d": round(100 * sum(s != "nedarbojas" for s in ar_datiem) / len(ar_datiem), 2)
            if ar_datiem else None,
        })
    return {"laiks": tagad.isoformat(timespec="seconds"), "intervals_min": STATUSS_INTERVALS // 60,
            "komponenti": komponenti}


def statuss(_q):
    return _kesots("statuss", 60, _statuss_dati)

# ==== Statuss — beigas ====



# ---- Rezultāta kartītei: tuvākā adrese GPS punktam un pašvaldības uzziņa ----

def adreses_tuvaka(q):
    """Tuvākā VZD adrese (≤ 300 m) atrašanās vietai: "Jūsu atrašanās vieta: ~Brīvības iela 15, Ogre"."""
    lat, lon = _vieta(q)
    return vaicat(
        """select coalesce((select json_build_object('adrese', adrese, 'kods', kods, 'attalums_m', d) from (
             select adrese, kods, round(st_distance(geom::geography,
                    st_setsrid(st_makepoint(%(lon)s, %(lat)s), 4326)::geography))::int as d
             from adreses order by geom <-> st_setsrid(st_makepoint(%(lon)s, %(lat)s), 4326) limit 1) a
           where d <= 300), '{}'::json)""",
        {"lat": lat, "lon": lon}, timeout="2s")


PASVALDIBAS_FAILS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "dati", "pasvaldibas.json")


def _pasvaldibas_dati():
    with open(PASVALDIBAS_FAILS, encoding="utf-8") as f:
        return json.load(f)


def pasvaldiba(q):
    """Pašvaldība punktā (regioni: novads vai valstspilsēta) + CA plāns, tīmekļvietne un VPVKAC kontakts
    (src/karte/db/pasvaldibas.py → src/karte/dati/pasvaldibas.json)."""
    lat, lon = _vieta(q)
    kods = vaicat("""select kods from regioni where tips in ('novads', 'valstspilseta')
                     and st_contains(geom, st_setsrid(st_makepoint(%s, %s), 4326)) limit 1""", (lon, lat), timeout="2s")
    if not kods:
        raise Kluda(404, "vieta nav nevienā pašvaldībā")
    dati = _kesots("pasvaldibas", 3600, _pasvaldibas_dati).get(kods)
    if not dati:
        raise Kluda(404, "pašvaldības dati nav atrasti")
    return {"kods": kods, **dati, "avoti": [
        {"nosaukums": "CA plāni hakatonam (pašvaldību tīmekļvietnes)", "licence": "Oficiāls dokuments",
         "url": "https://github.com/lata-org/ai-open-data-2026-hakatons/tree/main/ca-plani-hakatons"},
        {"nosaukums": "VPVKAC paplašinātā tīkla kontaktpunkti (2022)", "licence": "CC0 1.0",
         "url": "https://data.gov.lv/dati/lv/dataset/vpvkac-kontakti"}]}


MARSRUTI = [
    (re.compile(r"^/api/kategorijas/?$"), kategorijas, 300),
    (re.compile(r"^/api/avoti/?$"), avoti, 300),
    (re.compile(r"^/api/regioni/?$"), regioni, 3600),
    (re.compile(r"^/api/regioni/([^/]+)$"), regions, 3600),
    (re.compile(r"^/api/objekti/?$"), objekti, 60),
    (re.compile(r"^/api/adreses/?$"), adreses, 3600),
    (re.compile(r"^/api/adreses/tuvaka/?$"), adreses_tuvaka, 3600),
    (re.compile(r"^/api/pasvaldiba/?$"), pasvaldiba, 3600),
    (re.compile(r"^/api/bridinajumi/?$"), bridinajumi, 300),
    (re.compile(r"^/api/pludi/?$"), pludi, 3600),
    (re.compile(r"^/api/udens/?$"), udens, 600),
    (re.compile(r"^/api/prognozes/?$"), prognozes, 300),
    (re.compile(r"^/api/prognozes/robezas/?$"), prognozu_robezas, 86400),
    (re.compile(r"^/api/zibens/?$"), zibens, 60),
    (re.compile(r"^/api/augsne/?$"), augsne, 3600),
    (re.compile(r"^/api/marsruts/?$"), marsruts, 600),
    (re.compile(r"^/api/veseliba/?$"), veseliba, 0),
    (re.compile(r"^/api/celi/?$"), celi, 120),
    (re.compile(r"^/api/satiksme/?$"), satiksme, 60),
    (re.compile(r"^/api/statuss/?$"), statuss, 60),
    (re.compile(r"^/api/meklejumi/top/?$"), meklejumi_top, 60),
]
POST_MARSRUTI = [
    (re.compile(r"^/api/meklejumi/?$"), meklejumi_pievienot),
]


class Apstradatajs(BaseHTTPRequestHandler):
    server_version = "karte-api"

    def do_GET(self):
        url = urlparse(self.path)
        q = parse_qs(url.query)
        for raksts, funkcija, kesot in MARSRUTI:
            m = raksts.match(url.path)
            if not m:
                continue
            try:
                rez = funkcija(*m.groups()) if m.groups() else funkcija(q)
                return self._atbilde(200, rez, kesot)
            except Kluda as e:
                return self._atbilde(e.statuss, {"kluda": str(e)}, 0)
            except psycopg.Error as e:
                self.log_error("db: %s", e)
                return self._atbilde(503, {"kluda": "datubāze nav pieejama"}, 0)
        self._atbilde(404, {"kluda": "nav šāda galapunkta"}, 0)

    def do_POST(self):
        cels = urlparse(self.path).path
        funkcija = next((f for r, f in POST_MARSRUTI if r.match(cels)), None)
        if funkcija is None:
            return self._atbilde(404, {"kluda": "nav šāda galapunkta"}, 0)
        try:
            garums = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            garums = -1
        if not 0 <= garums <= 2000:
            return self._atbilde(413, {"kluda": "pārāk garš pieprasījums"}, 0)
        try:
            funkcija(json.loads(self.rfile.read(garums) or b"{}"))
        except (ValueError, UnicodeDecodeError):
            pass  # nederīgs JSON — neskaitām
        except psycopg.Error as e:
            self.log_error("db: %s", e)  # statistika nav svarīgāka par meklēšanu: tik un tā 204
        self.send_response(204)
        self.send_header("Cache-Control", "no-store")
        self.end_headers()

    def _atbilde(self, statuss, dati, kesot):
        teksts = dati if isinstance(dati, str) else json.dumps(dati, ensure_ascii=False, separators=(",", ":"))
        b = teksts.encode()
        self.send_response(statuss)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(b)))
        self.send_header("Cache-Control", f"public, max-age={kesot}" if kesot else "no-store")
        self.end_headers()
        self.wfile.write(b)


def main():
    if not DSN:
        sys.exit("Nav MAP_DB_DSN")
    ports = int(sys.argv[1]) if len(sys.argv) > 1 else 8920
    threading.Thread(target=_statuss_cikls, name="statuss", daemon=True).start()
    ThreadingHTTPServer(("127.0.0.1", ports), Apstradatajs).serve_forever()


if __name__ == "__main__":
    main()
