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
  GET /api/pludi?lat=..&lon=..         vai vieta ir plūdu riska zonā (LVĢMC 3. cikla kartes, WMS GetFeatureInfo)
  GET /api/udens?lat=..&lon=..&limit=3 tuvākās LVĢMC hidroloģiskās stacijas ar ūdens līmeni un izmaiņu 24 h
  GET /api/veseliba                    pārbaude
  POST /api/meklejumi {vaicajums, atpazits, klikskis}
                                       biežāk meklētā skaitītājs (tikai atpazīti vaicājumi, bez lietotāja datiem); 204
  GET /api/meklejumi/top?n=3           biežāk meklētie pēdējās 14 dienās (kešs 60 s)

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
    tagad = _riga_tagad()
    rez = []
    for b in _kesots("bridinajumi", 600, _bridinajumi_dati):
        if b["lidz"] and b["lidz"] < tagad:
            continue
        rez.append({
            **{k: v for k, v in b.items() if k != "poligoni"},
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
    return {"avots": "lvgmc-hidro", "stacijas": rez[:limit]}


def veseliba(_q):
    return {"ok": vaicat("select true")}


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


MARSRUTI = [
    (re.compile(r"^/api/kategorijas/?$"), kategorijas, 300),
    (re.compile(r"^/api/avoti/?$"), avoti, 300),
    (re.compile(r"^/api/regioni/?$"), regioni, 3600),
    (re.compile(r"^/api/regioni/([^/]+)$"), regions, 3600),
    (re.compile(r"^/api/objekti/?$"), objekti, 60),
    (re.compile(r"^/api/adreses/?$"), adreses, 3600),
    (re.compile(r"^/api/bridinajumi/?$"), bridinajumi, 300),
    (re.compile(r"^/api/pludi/?$"), pludi, 3600),
    (re.compile(r"^/api/udens/?$"), udens, 600),
    (re.compile(r"^/api/veseliba/?$"), veseliba, 0),
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
    ThreadingHTTPServer(("127.0.0.1", ports), Apstradatajs).serve_forever()


if __name__ == "__main__":
    main()
