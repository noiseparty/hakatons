"""map.repo.lv API: lasa datubāzi `map` un atgriež JSON / GeoJSON. Caddy to pieslēdz zem /api/.

Galapunkti:
  GET /api/kategorijas                 slāņi ar objektu skaitu un to avotiem
  GET /api/avoti                       datu avoti: izdevējs, licence, saites, skaits, ielādes laiks
  GET /api/regioni                     pašvaldības un pilsētas (bez ģeometrijas, ar bbox)
  GET /api/regioni/<kods>              reģiona robeža (GeoJSON Feature, vienkāršota)
  GET /api/objekti?kategorijas=a,b&regions=<kods>&lat=..&lon=..&limit=..[&kritiskais=1]
                                       punkti (GeoJSON); ar lat/lon sakārtoti pēc attāluma
  GET /api/objekti?bbox=minLon,minLat,maxLon,maxLat&kategorijas=..[&regions=..&lat=..&lon=..&limit=..]
                                       kartes skats: tikai punkti taisnstūrī, īsās īpašības (tikai tās, ko rāda logā),
                                       ≤ 5000; ja vairāk — vienmērīga izlase pa slāņiem un "apgriezts": true
  GET /api/adreses?q=brivibas 15 ogre&limit=8
                                       adrešu meklēšana (VZD); bez garumzīmēm, pēc vārdu daļām
  GET /api/bridinajumi?lat=..&lon=..   LVĢMC hidrometeoroloģiskie brīdinājumi (spēkā esošie); ar lat/lon —
                                       vai brīdinājums attiecas uz šo vietu (attiecas)
                                       ?poligoni=1 — arī brīdinājumu apgabali [[lat, lon], ...] (zonas.js)
                                       LVĢMC nav pieejams > 15 min vai > 15 min tukšs → rezerves avots Meteoalarm
                                       (CAP/Atom, kešs 5 min): tā pati forma + "rezerves": true, "atruna", "izdots"
  GET /api/pludi?lat=..&lon=..[&wms=1] vai vieta ir plūdu riska zonā (LVĢMC 3. cikla kartes): PostGIS kopija
                                       (pludu_zonas) → LVĢMC WMS ar kešu pludi_kesa (7 d) → {"zinams": false}
  GET /api/udens?lat=..&lon=..&limit=3 tuvākās LVĢMC hidroloģiskās stacijas ar ūdens līmeni un izmaiņu 24 h
                                       + prognoze 7 dienām (LVĢMC hidroloģiskās prognozes, kešs 1 h)
                                       + slieksnis, kritiskais (m LAS), statuss normāls|paaugstināts|kritisks
                                       stacijām ar slieksni CA plānā (src/karte/db/udens_slieksni.json), citām null
  GET /api/adreses/tuvaka?lat=..&lon=.. tuvākā VZD adrese (≤ 300 m) atrašanās vietai
  GET /api/pasvaldiba?lat=..&lon=..    pašvaldība punktā: CA plāns, tīmekļvietne, VPVKAC tālrunis (teksts)
  GET /api/prognozes                   "Prognoze / ziņas": LVĢMC prognozes apdzīvotām vietām (3 dienas) apkopotas pa
                                       novadiem + spēkā esošie brīdinājumi ar poligoniem; ziņu lente pa plānošanas reģioniem
                                       + "zibens" ziņa katram novadam ar zibeni pēdējās 30 min (FMI, CC BY 4.0; kešs 60 s)
  GET /api/prognozes/robezas           novadu un valstspilsētu robežas (vienkāršotas) kartes iekrāsošanai
  GET /api/zibens                      zibens pēdējās 30 min (FMI, CC BY 4.0) + LVĢMC 24 h zibens režģis (CC0, kavējas 2–3 h)
  GET /api/augsne?lat=..&lon=..        nokrišņi pēdējās 26 dienās + augsnes mitrums (Open-Meteo, CC BY 4.0; nav brīdinājums)
  GET /api/marsruts?no=lat,lon&uz=lat,lon&veids=kajam|auto&izvairities=c:lat,lon,r|lat,lon;lat,lon;…
                                       maršruts (FOSSGIS OSRM, OSM ODbL), kas apiet zonas un spēkā esošus LVC slēgumus
  GET /api/noverojumi[?lat=..&lon=..&limit=..]  laikapstākļi tagad: LVĢMC staciju jaunākās brāzmas, vējš, temperatūra, nokrišņi
  GET /api/veseliba                    pārbaude
  GET /api/celi?bbox=..|lat=..&lon=..&r=5000
                                       ceļu slēgumi, negadījumi, remontdarbi, slidens ceļš (LVC DATEX II caur NAP, CC0)
  GET /api/satiksme                    satiksme pa zonām (pašvaldības), slidenā ceļa vietas, robežu gaidīšana (NAP, CC0)
  POST /api/meklejumi {vaicajums, atpazits, klikskis}
                                       biežāk meklētā skaitītājs (tikai atpazīti vaicājumi, bez lietotāja datiem); 204
  GET /api/meklejumi/top?n=3           biežāk meklētie pēdējās 14 dienās (kešs 60 s)
  GET /api/plusma.xml[?regions=<kods|ATVK>]  Atom plūsma: brīdinājumi, rītdienas prognoze, upes, ceļi, zibens (kešs 5 min)
  GET /api/kalendars.ics[?regions=..]  brīdinājumi kā iCalendar notikumi (kalendāra lietotnēm)
  GET /api/statuss                     statusa lapa: vietnes, API un datu avotu stāvoklis, 24 h pa 15 min, 7 dienu pieejamība

Brīdinājumi un ūdens līmenis nāk tieši no atvērto datu avotiem (bez datubāzes), kešoti atmiņā; plūdu zonas —
no PostGIS kopijas (pludu_zonas), ja tās nav — no LVĢMC WMS ar kešu datubāzē (pludi_kesa).

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
import urllib.parse
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


DB_VIENLAICIGI = int(os.environ.get("MAP_DB_VIENLAICIGI", "16"))
_db_sloti = threading.BoundedSemaphore(DB_VIENLAICIGI)
_statistika = {"db_vaicajumi": 0, "db_parslodze": 0, "kesa": {}}  # /api/veseliba?statistika=1


def vaicat(sql, params=(), timeout="10s"):
    # ≤ DB_VIENLAICIGI vaicājumi reizē; ja 10 s neatbrīvojas — 503, nevis savienojumu lavīna uz Postgres
    if not _db_sloti.acquire(timeout=10):
        _statistika["db_parslodze"] += 1
        raise Kluda(503, "serveris pārslogots, mēģiniet pēc brīža")
    try:
        _statistika["db_vaicajumi"] += 1
        with psycopg.connect(DSN, connect_timeout=5) as conn, conn.cursor() as cur:
            cur.execute(f"set statement_timeout = '{timeout}'")
            cur.execute(sql, params)
            rinda = cur.fetchone()
            return rinda[0] if rinda else None
    finally:
        _db_sloti.release()


class _LRU:
    """Mazs atmiņas kešs ar derīguma laiku (sekundes) un ierakstu skaita robežu; vecākos izmet."""
    def __init__(self, max_ieraksti, sekundes):
        from collections import OrderedDict
        self.dati, self.max, self.sek, self.slots = OrderedDict(), max_ieraksti, sekundes, threading.Lock()

    def iegut(self, atslega, funkcija):
        with self.slots:
            ieraksts = self.dati.get(atslega)
            if ieraksts and time.time() - ieraksts[0] < self.sek:
                self.dati.move_to_end(atslega)
                return ieraksts[1]
        vertiba = funkcija()
        with self.slots:
            self.dati[atslega] = (time.time(), vertiba)
            self.dati.move_to_end(atslega)
            while len(self.dati) > self.max:
                self.dati.popitem(last=False)
        return vertiba


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
                    (select max(atjaunots) from objekti o where o.avots = a.kods) as ieladets,
                    -- pēdējā veiksmīgā ielāde (ielade.py); caur to_jsonb, lai darbojas arī pirms kolonnas pievienošanas
                    (to_jsonb(a) ->> 'atjaunots')::timestamptz as atjaunots
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
    kritiskais = q.get("kritiskais", [""])[0] == "1"  # tikai kritiskie (banku bankomāti: skaidra nauda arī krīzē)
    bbox = _skata_bbox(q)
    if bbox:
        limit = min(limit, BBOX_MAX)
    atslega = (tuple(sorted(kategorijas_)), regions_, None if lat is None else round(lat, 5),
               None if lon is None else round(lon, 5), limit, kritiskais, bbox)
    if bbox:
        return _objektu_kesa.iegut(atslega, lambda: _objekti_skata(kategorijas_, regions_, lat, lon, limit, bbox,
                                                                   kritiskais))
    return _objektu_kesa.iegut(atslega, lambda: _objekti_vaicat(kategorijas_, regions_, lat, lon, limit, kritiskais))


_objektu_kesa = _LRU(64, 30)

# Kartes skats (?bbox=): augšējā robeža un ipasibas atslēgas, ko rāda punkta logs un saraksts (production/app.js
# popupSaturs, objekta-statuss.js, saraksts.js). Pārējās (citāti, plāna faila ceļi, VZD kodi…) kartei nav vajadzīgas;
# rezultāta kartīte un ārējie lietotāji bez bbox saņem pilnās īpašības kā līdz šim.
BBOX_MAX = 5000
BBOX_SOLIS = 100  # taisnstūri paplašina līdz 0,01° režģim: tuvi skati dala vienu keša ierakstu
SKATA_IPASIBAS = [
    "limenis_cm", "limenis_m", "izmaina_24h_cm", "udens_temp", "laiks", "piezime", "opening_hours", "darba_laiks",
    "veids", "ligzdas", "operator", "brand", "phone", "komentars", "marsruti", "veidi", "marsrutu_saraksts",
    "apzimejums", "plans_url", "lpp", "statuss", "last_updated",
    "kritiskais", "bankas", "skaits", "iemaksas", "pieejamiba_24h",  # bankomāti (marķieris un logs)
]


def _skata_bbox(q):
    if "bbox" not in q:
        return None
    try:
        w, s, e, n = (float(x) for x in q["bbox"][0].split(","))
    except ValueError:
        raise Kluda(400, "bbox: vajag minLon,minLat,maxLon,maxLat") from None
    if not (-180 <= w < e <= 180 and -90 <= s < n <= 90):
        raise Kluda(400, "bbox: ārpus robežām")
    return (math.floor(w * BBOX_SOLIS) / BBOX_SOLIS, math.floor(s * BBOX_SOLIS) / BBOX_SOLIS,
            math.ceil(e * BBOX_SOLIS) / BBOX_SOLIS, math.ceil(n * BBOX_SOLIS) / BBOX_SOLIS)


def _objekti_skata(kategorijas_, regions_, lat, lon, limit, bbox, kritiskais=False):
    """Punkti taisnstūrī. Ja to ir vairāk par limit — pa slāņiem pārmaiņus (rn), lai retie slāņi (24/7 slimnīcas)
    netiek izspiesti ar pieturām: katrā slānī tuvākie (ar lat/lon) vai pseidonejauša, bet stabila izlase.
    Atgriež gatavu JSON tekstu: kešā aizņem mazāk atmiņas nekā Python objekti."""
    lieto_vietu = lat is not None
    w, s, e, n = bbox
    return vaicat(
        """with x as (
             select o.id, o.kategorija, o.nosaukums, o.adrese, o.avots, o.ipasibas, o.derigs_no, o.derigs_lidz, o.geom,
                    case when %(vieta)s then round(st_distance(o.geom::geography,
                         st_setsrid(st_makepoint(%(lon)s, %(lat)s), 4326)::geography))::int end as attalums_m,
                    row_number() over (partition by o.kategorija order by
                         case when %(vieta)s then o.geom <-> st_setsrid(st_makepoint(%(lon)s, %(lat)s), 4326) end,
                         (o.id * 2654435761) %% 4294967296, o.id) as rn
             from objekti o
             where st_intersects(o.geom, st_makeenvelope(%(w)s, %(s)s, %(e)s, %(n)s, 4326))
               and (o.derigs_lidz is null or o.derigs_lidz > now())
               and (cardinality(%(kat)s::text[]) = 0 or o.kategorija = any(%(kat)s::text[]))
               and (%(reg)s = '' or o.pasvaldiba_kods = %(reg)s or o.pilseta_kods = %(reg)s)
               and (not %(krit)s or o.ipasibas->>'kritiskais' = '1')),
           y as (select * from x order by rn, kategorija, id limit %(limit)s + 1),
           z as (select * from y order by rn, kategorija, id limit %(limit)s)
           select json_build_object('type', 'FeatureCollection',
                    'apgriezts', (select count(*) from y) > %(limit)s,
                    'features', coalesce((select json_agg(
                      json_build_object('type', 'Feature', 'id', id,
                        'geometry', json_build_object('type', 'Point', 'coordinates',
                          json_build_array(round(st_x(geom)::numeric, 5), round(st_y(geom)::numeric, 5))),
                        'properties', json_strip_nulls(json_build_object('kategorija', kategorija,
                          'nosaukums', nosaukums, 'adrese', adrese, 'avots', avots, 'attalums_m', attalums_m,
                          'derigs_no', derigs_no, 'derigs_lidz', derigs_lidz,
                          'ipasibas', (select coalesce(jsonb_object_agg(key, value), '{}') from jsonb_each(ipasibas)
                                       where key = any(%(ipas)s::text[])))))
                      order by attalums_m nulls last, id) from z), '[]'))::text""",
        {"vieta": lieto_vietu, "lat": lat or 0, "lon": lon or 0, "kat": kategorijas_, "reg": regions_,
         "limit": limit, "w": w, "s": s, "e": e, "n": n, "ipas": SKATA_IPASIBAS, "krit": kritiskais},
        timeout="8s",
    )


def _objekti_vaicat(kategorijas_, regions_, lat, lon, limit, kritiskais=False):
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
               and (not %(krit)s or o.ipasibas->>'kritiskais' = '1')
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
        {"vieta": lieto_vietu, "lat": lat or 0, "lon": lon or 0, "kat": kategorijas_, "reg": regions_, "limit": limit,
         "krit": kritiskais},
        timeout="8s",
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
    st = _statistika["kesa"].setdefault(atslega[0] if isinstance(atslega, tuple) else atslega,
                                        {"no_kesas": 0, "uz_avotu": 0, "novecojusi": 0, "gaidija": 0})
    if svaigs:
        st["no_kesas"] += 1
        return ieraksts[1]
    with _kesas_slots:
        slots = _atslegu_sloti.setdefault(atslega, threading.Lock())
    if ieraksts:
        # stale-while-revalidate: lietotājs negaida avotu; atjauno viens fona pavediens (ja jau atjauno — nekas)
        st["novecojusi"] += 1
        if slots.acquire(blocking=False):
            threading.Thread(target=_kesot_fona, args=(atslega, slots, funkcija, ilgums, st), daemon=True).start()
        return ieraksts[1]
    if slots.locked():
        st["gaidija"] += 1
    with slots:
        ieraksts, svaigs = no_kesas()
        if svaigs:
            return ieraksts[1]
        try:
            st["uz_avotu"] += 1
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


def _kesot_fona(atslega, slots, funkcija, ilgums, st):
    """Novecojušas vērtības atjaunošana fonā (slots jau paņemts). Kļūda: paliek vecā vērtība, nākamais mēģinājums pēc minūtes."""
    try:
        st["uz_avotu"] += 1
        vertiba = funkcija()
        with _kesas_slots:
            _kesa[atslega] = (time.time(), vertiba)
    except Exception:  # noqa: BLE001
        with _kesas_slots:
            ieraksts = _kesa.get(atslega)
            if ieraksts:
                _kesa[atslega] = (time.time() - ilgums(ieraksts[1]) + 60, ieraksts[1])
    finally:
        slots.release()


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
    _lvgmc_stavoklis["ok"] = time.time()  # rezerves avotam (Meteoalarm): kad LVĢMC pēdējo reizi atbildēja
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
    try:
        lvgmc, lvgmc_kluda = _kesots("bridinajumi", 600, _bridinajumi_dati), None
    except Kluda as e:  # LVĢMC nav pieejams un kešā nekā nav: mēģina Meteoalarm
        lvgmc, lvgmc_kluda = [], e
    for b in lvgmc:
        if b["lidz"] and b["lidz"] < tagad:
            continue
        rez.append({
            **{k: v for k, v in b.items() if k != "poligoni" or ar_poligoniem},
            "no": b["no"].isoformat() if b["no"] else None,
            "lidz": b["lidz"].isoformat() if b["lidz"] else None,
            "attiecas": any(_punkts_poligona(lat, lon, p) for p in b["poligoni"]) if lat is not None else None,
        })
    rez.sort(key=lambda b: (-b["limenis"], b["no"] or ""))
    sekundes = time.time()
    if rez:
        _lvgmc_stavoklis["ar_bridinajumiem"] = sekundes
    lvgmc_nav = lvgmc_kluda is not None or sekundes - (_lvgmc_stavoklis["ok"] or 0) > REZERVES_PEC
    if lvgmc_nav or (not rez and sekundes - _lvgmc_stavoklis["ar_bridinajumiem"] > REZERVES_PEC):
        rezerves = _meteoalarm_atbilde(lat, lon, ar_poligoniem, tagad, lvgmc_nav)
        if rezerves is not None:
            _lvgmc_stavoklis["rezerves"] = sekundes
            return rezerves
    if lvgmc_kluda is not None:
        raise lvgmc_kluda
    _lvgmc_stavoklis["rezerves"] = None
    return {"avots": "lvgmc-bridinajumi", "laiks_lv": tagad.isoformat(timespec="minutes"), "bridinajumi": rez}


# ---- Rezerves avots: Meteoalarm (EUMETNET) Latvijas CAP/Atom plūsma ----
# Tie paši LVĢMC brīdinājumi (CAP sūtītājs www.lvgmc.lv), bet caur Meteoalarm. /api/bridinajumi to lieto tikai tad, ja
# LVĢMC data.gov.lv datne > 15 min nav pieejama vai > 15 min nerāda nevienu brīdinājumu (un Meteoalarm rāda).
# Noteikumi (notes/research/04, "Meteoalarm redistribution terms"): ~CC BY 4.0; jānosauc LVĢMC, jārāda izdošanas laiks,
# saite uz meteoalarm.org un atruna; teksts nemainīts; kavējums ≤ 10 min (kešs 5 min + HTTP 5 min). Vietu pārbauda pēc CAP
# <polygon> (Meteoalarm pievieno apgabalu robežas); ja CAP neizdevās ielādēt — pēc pašvaldības (areaDesc ↔ regioni).
METEOALARM_ATOM = os.environ.get("METEOALARM_ATOM", "https://feeds.meteoalarm.org/feeds/meteoalarm-legacy-atom-latvia")
METEOALARM_AVOTS = "Meteoalarm (EUMETNET), ar atsauci"
METEOALARM_URL = "https://www.meteoalarm.org"
METEOALARM_ATRUNA = ("Time delays between this website and the www.meteoalarm.org website are possible. For the most "
                     "up-to-date awareness information as published by the participating National Meteorological and "
                     "Hydrological Services, please refer to www.meteoalarm.org.")
METEOALARM_TAIMAUTS = 8
# Meteoalarm: kavējums "never > 10 min". Kešs 5 min + /api/bridinajumi HTTP kešs 5 min (MARSRUTI) = ≤ 10 min
METEOALARM_KESS = 300
METEOALARM_MAX_CAP = 20  # CAP ziņojumu vienā atjaunošanā (parasti 5–10)
REZERVES_PEC = 15 * 60
_lvgmc_stavoklis = {"ok": None, "ar_bridinajumiem": time.time(), "rezerves": None}
METEOALARM_LIMENI = {"yellow": 1, "orange": 2, "red": 3}
METEOALARM_KRASAS = {1: "Dzeltens", 2: "Oranžs", 3: "Sarkans"}
METEOALARM_VEIDI = {  # CAP awareness_type numurs → parādība latviski
    "1": "Vējš", "2": "Sniegs, apledojums", "3": "Pērkona negaiss", "4": "Migla", "5": "Karstums", "6": "Sals",
    "7": "Krasta parādības", "8": "Meža ugunsbīstamība", "9": "Lavīnas", "10": "Lietus", "12": "Plūdi",
    "13": "Lietus, plūdi",
}
METEOALARM_VEIDI_EN = {  # Atom <cap:event> "Yellow Wind Warning" (ja CAP neizdevās ielādēt) → tas pats latviski
    "wind": "1", "snowice": "2", "thunderstorm": "3", "thunderstorms": "3", "fog": "4", "hightemperature": "5",
    "lowtemperature": "6", "coastalevent": "7", "forestfire": "8", "avalanches": "9", "avalanche": "9", "rain": "10",
    "flooding": "12", "flood": "12", "rainflood": "13",
}
CAP_NS = "{urn:oasis:names:tc:emergency:cap:1.2}"
ATOM_NS = "{http://www.w3.org/2005/Atom}"


def _xml_teksts(el, vards):
    x = el.find(vards) if el is not None else None
    return (x.text or "").strip() if x is not None else ""


def _cap_laiks(teksts):
    """CAP/ISO laiks ar joslu → Latvijas vietējais bez joslas (kā LVĢMC laukos); nederīgs → None."""
    try:
        dt = datetime.fromisoformat((teksts or "").strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        return dt
    try:
        from zoneinfo import ZoneInfo
        return dt.astimezone(ZoneInfo("Europe/Riga")).replace(tzinfo=None)
    except Exception:  # noqa: BLE001  bez tzdata (Windows): kā _riga_tagad
        utc = dt.astimezone(timezone.utc)
        return (utc + timedelta(hours=3 if 3 < utc.month < 11 else 2)).replace(tzinfo=None)


def _cap_zinojums(url):
    """Viens CAP ziņojums: latviskā <info> (ja ir), līmenis, parādība, apgabali, atsauces uz aizstātajiem ziņojumiem."""
    import xml.etree.ElementTree as ET
    c = lambda el, v: _xml_teksts(el, CAP_NS + v)  # noqa: E731
    alert = ET.fromstring(_lejupieladet(url, timeout=METEOALARM_TAIMAUTS))
    infos = alert.findall(CAP_NS + "info")
    info = next((i for i in infos if c(i, "language").lower().startswith("lv")), infos[0] if infos else None)
    if info is None:
        return None
    param = {c(p, "valueName"): c(p, "value") for p in info.findall(CAP_NS + "parameter")}
    limenis = [x.strip().lower() for x in param.get("awareness_level", "").split(";")]
    veids = [x.strip() for x in param.get("awareness_type", "").split(";")]
    apgabali = [(c(a, "areaDesc"), [c(g, "value") for g in a.findall(CAP_NS + "geocode") if c(g, "valueName") == "EMMA_ID"])
                for a in info.findall(CAP_NS + "area")]
    poligoni = []  # CAP <polygon>: "lat,lon lat,lon …" (Meteoalarm pievieno pašvaldību robežas)
    for a in info.findall(CAP_NS + "area"):
        for p in a.findall(CAP_NS + "polygon"):
            try:
                punkti = [(float(x), float(y)) for x, y in (pari.split(",") for pari in (p.text or "").split())]
            except ValueError:
                continue
            if len(punkti) > 2:
                poligoni.append(punkti)
    return {
        "id": c(alert, "identifier"), "msgType": c(alert, "msgType"), "status": c(alert, "status"), "sent": c(alert, "sent"),
        "aizstaj": [r.split(",")[1] for r in c(alert, "references").split() if r.count(",") >= 2],
        "limenis": METEOALARM_LIMENI.get(limenis[1] if len(limenis) > 1 else ""),
        "paradiba": METEOALARM_VEIDI.get(veids[0]) or (veids[1] if len(veids) > 1 else ""),
        "notikums": c(info, "event"), "teksts": c(info, "description"),
        "onset": c(info, "onset") or c(info, "effective"), "expires": c(info, "expires"),
        "apgabali": [a for a, _ in apgabali if a], "emma": sorted({e for _, ee in apgabali for e in ee}), "lv": True,
        "poligoni": poligoni,
    }


def _meteoalarm_dati():
    """Atom plūsma → spēkā esošie CAP ziņojumi. Katru CAP lejupielādē vienreiz (latviskais teksts); ja neizdodas —
    paliek Atom lauki (angliski, bez apraksta). Aizstātos (CAP references) un atsauktos (Cancel) izmet."""
    import xml.etree.ElementTree as ET
    c = lambda el, v: _xml_teksts(el, CAP_NS + v)  # noqa: E731
    feed = ET.fromstring(_lejupieladet(METEOALARM_ATOM, timeout=METEOALARM_TAIMAUTS))
    tagad_utc = datetime.now(timezone.utc)
    pec_cap = {}  # CAP saite → Atom dati (viens CAP ziņojums ir vairākos Atom ierakstos — pa apgabalam)
    for e in feed.findall(ATOM_NS + "entry"):
        cap_url = next((l.get("href") for l in e.findall(ATOM_NS + "link") if l.get("type") == "application/cap+xml"), None)
        if not cap_url or c(e, "status") not in ("", "Actual") or c(e, "message_type") == "Cancel":
            continue
        beigas = _cap_laiks(c(e, "expires"))
        if beigas and beigas < _cap_laiks(tagad_utc.isoformat()):
            continue
        notikums = c(e, "event")
        vardi = notikums.split()  # "Orange Wind Warning"
        a = pec_cap.setdefault(cap_url, {
            "id": c(e, "identifier") or cap_url, "msgType": c(e, "message_type"), "status": "Actual", "sent": c(e, "sent"),
            "aizstaj": [], "limenis": METEOALARM_LIMENI.get(vardi[0].lower() if vardi else ""),
            "paradiba": METEOALARM_VEIDI.get(METEOALARM_VEIDI_EN.get(re.sub(r"[^a-z]", "", "".join(vardi[1:-1]).lower()), ""))
            or (" ".join(vardi[1:-1]) if len(vardi) > 2 else notikums), "notikums": notikums, "teksts": "",
            "onset": c(e, "onset") or c(e, "effective"), "expires": c(e, "expires"), "apgabali": [], "emma": [], "lv": False,
            "poligoni": [],
        })
        apgabals = c(e, "areaDesc")
        if apgabals and apgabals not in a["apgabali"]:
            a["apgabali"].append(apgabals)
        geo = e.find(CAP_NS + "geocode")  # tā bērni Atom plūsmā ir Atom vārdtelpā
        if geo is not None and _xml_teksts(geo, ATOM_NS + "valueName") == "EMMA_ID":
            emma = _xml_teksts(geo, ATOM_NS + "value")
            if emma and emma not in a["emma"]:
                a["emma"].append(emma)
    urls = sorted(pec_cap, key=lambda u: pec_cap[u]["sent"], reverse=True)[:METEOALARM_MAX_CAP]
    zinojumi = []
    if urls:
        pavedieni = ThreadPoolExecutor(max_workers=6)
        darbi = {u: pavedieni.submit(_cap_zinojums, u) for u in urls}
        pavedieni.shutdown(wait=False)
        termins = time.monotonic() + METEOALARM_TAIMAUTS + 2
        for u in urls:
            try:
                z = darbi[u].result(timeout=max(0.0, termins - time.monotonic()))
            except Exception:  # noqa: BLE001  CAP nav pieejams vai nav nolasāms: paliek Atom dati
                z = None
            zinojumi.append({**(z or pec_cap[u]), "url": u})
    aizstati = {i for z in zinojumi for i in z["aizstaj"]}
    saraksts = []
    for z in zinojumi:
        if z["id"] in aizstati or z["msgType"] == "Cancel" or z["status"] not in ("", "Actual"):
            continue
        limenis = z["limenis"] or 1
        saraksts.append({
            "id": z["id"], "nr": "", "krasa": METEOALARM_KRASAS[limenis], "limenis": limenis,
            "paradiba": z["paradiba"] or z["notikums"], "notikums": z["notikums"], "regioni": ", ".join(z["apgabali"]),
            "apgabali": z["apgabali"], "emma_id": z["emma"], "no": _cap_laiks(z["onset"]), "lidz": _cap_laiks(z["expires"]),
            "izdots": _cap_laiks(z["sent"]), "teksts": z["teksts"], "riski": "", "latviski": z["lv"], "cap_url": z["url"],
            "poligoni": z["poligoni"],
        })
    return {"ielasits": time.time(), "bridinajumi": saraksts}


def _novada_atslega(nosaukums, novads):
    """'Ogres novads' / 'Rīga' / 'Rīgas valstspilsēta' → ('ogre', novads?) CAP areaDesc salīdzināšanai ar regioni.
    Citi apgabali ('Rīgas līča dienvidu daļa', jūras rajoni) → None: tie nav pašvaldības."""
    vardi = (nosaukums or "").strip().lower().split()
    if not vardi or len(vardi) > 2 or (len(vardi) == 2 and vardi[1] not in ("novads", "valstspilsēta", "valstspilseta", "municipality")):
        return None
    vards = re.sub(r"[^a-z]", "", unicodedata.normalize("NFKD", vardi[0]).encode("ascii", "ignore").decode())
    return (vards[:-1] if vards.endswith("s") else vards), bool(novads)


def _vietas_novads(lat, lon):
    """Pašvaldība punktā (regioni) kā _novada_atslega; DB nav pieejama → None (attiecas nav zināms)."""
    try:
        rinda = _punktu_kesa.iegut(("novads_nosaukums", round(lat, 4), round(lon, 4)), lambda: vaicat(
            """select json_build_array(nosaukums, tips) from regioni where tips in ('novads', 'valstspilseta')
               and st_contains(geom, st_setsrid(st_makepoint(%s, %s), 4326)) limit 1""", (lon, lat), timeout="2s"))
    except Exception:  # noqa: BLE001
        return None
    return (_novada_atslega(rinda[0], rinda[1] == "novads") if rinda else None) or ("", False)


def _meteoalarm_atbilde(lat, lon, ar_poligoniem, tagad, lvgmc_nav):
    """/api/bridinajumi atbilde no Meteoalarm (tā pati forma + rezerves: true) vai None: Meteoalarm nav pieejams vai
    (kamēr LVĢMC atbild) arī tas nerāda nevienu brīdinājumu."""
    try:
        dati = _kesots("meteoalarm", METEOALARM_KESS, _meteoalarm_dati)
    except Exception:  # noqa: BLE001
        return None
    vieta = False  # pašvaldība punktā: tikai, ja kādam brīdinājumam nav poligonu (Atom bez CAP)
    rez = []
    for b in dati["bridinajumi"]:
        if b["lidz"] and b["lidz"] < tagad:
            continue
        attiecas = None
        if lat is not None and b["poligoni"]:
            attiecas = any(_punkts_poligona(lat, lon, p) for p in b["poligoni"])
        elif lat is not None:
            if vieta is False:
                vieta = _vietas_novads(lat, lon)
            if vieta is not None:
                attiecas = bool(vieta[0]) and any(_novada_atslega(a, a.lower().endswith(("novads", "municipality"))) == vieta
                                                   for a in b["apgabali"])
        rez.append({**{k: v for k, v in b.items() if k != "poligoni" or ar_poligoniem},
                    "no": b["no"].isoformat() if b["no"] else None, "lidz": b["lidz"].isoformat() if b["lidz"] else None,
                    "izdots": b["izdots"].isoformat() if b["izdots"] else None, "attiecas": attiecas})
    if not rez and not lvgmc_nav:
        return None
    rez.sort(key=lambda b: (-b["limenis"], b["no"] or ""))
    return {"avots": METEOALARM_AVOTS, "rezerves": True, "izdevejs": "LVĢMC (caur Meteoalarm)",
            "licence": "CC BY 4.0 (Meteoalarm noteikumi)", "url": METEOALARM_URL, "atruna": METEOALARM_ATRUNA,
            "ielasits": datetime.fromtimestamp(dati["ielasits"], timezone.utc).isoformat(timespec="seconds"),
            "laiks_lv": tagad.isoformat(timespec="minutes"), "bridinajumi": rez}


def _rezerves_aktivs():
    """Vai /api/bridinajumi pēdējās 20 min atbildēja no Meteoalarm (statusa lapai, /api/veseliba)."""
    t = _lvgmc_stavoklis["rezerves"]
    return bool(t) and time.time() - t < 20 * 60


def _bridinajumu_salidzinajums():
    """/api/veseliba: spēkā esošo brīdinājumu skaits LVĢMC pret Meteoalarm, tikai no keša (nebloķē).
    Ja Meteoalarm kešā nav vai tas novecojis — atjauno fonā (_kesots: viens pavediens)."""
    tagad, sekundes = _riga_tagad(), time.time()
    with _kesas_slots:
        lv, ma = _kesa.get("bridinajumi"), _kesa.get("meteoalarm")
        slots = _atslegu_sloti.get("meteoalarm")
    if (not ma or sekundes - ma[0] > METEOALARM_KESS) and not (slots and slots.locked()):
        def atjaunot():
            try:
                _kesots("meteoalarm", METEOALARM_KESS, _meteoalarm_dati)
            except Exception:  # noqa: BLE001  nav pieejams: salīdzinājumā paliek null
                pass
        threading.Thread(target=atjaunot, daemon=True).start()

    def speka(saraksts):
        return sum(1 for b in saraksts if not (b["lidz"] and b["lidz"] < tagad))
    ok = _lvgmc_stavoklis["ok"]
    return {"lvgmc": speka(lv[1]) if lv else None, "meteoalarm": speka(ma[1]["bridinajumi"]) if ma else None,
            "lvgmc_atbildeja": datetime.fromtimestamp(ok, timezone.utc).isoformat(timespec="seconds") if ok else None,
            "rezerves_aktivs": _rezerves_aktivs()}


# Plūdu riska zonas: LVĢMC "3. cikla Latvijas plūdu postījumu vietu un plūdu riska kartes" (2026–2031).
# /api/pludi atbild šādā secībā (lai demo un krīzē atbilde nekad nav "neizdevās"):
#   a) PostGIS tabula pludu_zonas: lokāla kopija no ĢeoLatvija.lv SHP failiem (src/karte/db/pludu_zonas.py), ja tajā
#      ir rindas — ~10 ms, nav atkarīga no LVĢMC servisa;
#   b) citādi LVĢMC WMS GetFeatureInfo (geo-dpps.viss.gov.lv; mēdz atbildēt 1–30 s vai nemaz) ar pastāvīgu kešu
#      pludi_kesa (koordinātas 4 zīmes ≈ 10 m; derīgs 7 dienas; ja LVĢMC neatbild — arī vecāks, ar "novecojis");
#   c) nekas nav zināms → 200 {"zinams": false, "iemesls": …}, nevis 503 — kartīte to pasaka godīgi.
# Atbildē "avots" (avoti.kods) un "metode": "PostGIS kopija" / "LVĢMC WMS" / "kešs no HH:MM".
# ?wms=1 — izlaist a) (pludi_siltums.py: piepilda kešu un salīdzina ar kopiju). Slāņa nr → varbūtība gadā, %.
PLUDU_WMS = "https://geo-dpps.viss.gov.lv/api/DPPSPackage/client/"
PLUDU_SERVISI = [
    ("pavasara pali", "3._cikla_L_557_7iFPTq/b7ad025f-833a-4b4f-a845-d5cec9d24092", {"3": 10, "2": 10, "1": 1, "0": 0.5}),
    ("ledus sastrēgumi", "3._cikla_L_558_jIS73E/3322e012-8cb3-4a4c-8acf-a467e25a17b3", {"2": 10, "1": 1, "0": 0.5}),
    ("jūras vējuzplūdi", "3._cikla_L_556_karVbb/cc6f2ed3-dbfb-42d0-98e1-4d9f10f57fea", {"2": 10, "1": 1, "0": 0.5}),
]
PLUDU_AVOTI = {  # avoti.kods → kartītes avota rinda
    "lvgmc-pludi-faili": {"nosaukums": "LVĢMC plūdu riska kartes 2026–2031 (ĢeoLatvija.lv faili)", "licence": "CC BY-SA 4.0",
                          "url": "https://geolatvija.lv/main?geoProductId=361"},
    "lvgmc-pludi": {"nosaukums": "LVĢMC plūdu riska kartes 2026–2031", "licence": "CC0 1.0",
                    "url": "https://data.gov.lv/dati/lv/dataset/3-cikla-latvijas-pldu-postjumu-vietu-un-pldu-riska-kartes1"},
}
PLUDU_WMS_VARBUTIBAS = [10, 1, 0.5]  # kuras kartes WMS pārbauda (atbildē "varbutibas")
PLUDU_TAIMAUTS = 20         # s, viens WMS pieprasījums
PLUDU_MAX_GAIDIT = 6        # s: lietotājs gaida ne ilgāk (sw.js tīkla taimauts ir 8 s); tad 202 un pārbaude turpinās fonā
PLUDU_MAX_DARBI = 8         # vienlaicīgas WMS pārbaudes (katra = 3 pieprasījumi); vairāk — kā "neatbild"
PLUDU_KLUDAS_PAUZE = 60     # s: pēc LVĢMC kļūmes negaidām to vēlreiz — uzreiz kešs vai "nav zināms" (pārbaude iet fonā)
PLUDU_KESA_DERIGA = 7 * 86400
PLUDU_KESA_NEPILNIGA = 600  # daļa karšu neatbildēja: tādu atbildi pēc 10 min jautā vēlreiz
PLUDU_NEATBILD = "LVĢMC plūdu karte šobrīd neatbild"
PLUDI_SHEMA = """
create table if not exists pludi_kesa (
  atslega text primary key,
  atbilde jsonb not null,
  laiks   timestamptz not null default now()
);
grant select, insert, update on pludi_kesa to map_api;
"""  # tas pats bloks ir src/karte/db/shema.sql
_pludu_pavedieni = ThreadPoolExecutor(max_workers=6)
_pludu_gaidisana = ThreadPoolExecutor(max_workers=PLUDU_MAX_DARBI)
_pludu_darbi = {}                 # atslēga → Future: viena WMS pārbaude vietai vienlaikus
_pludu_kluda = [0.0]              # pēdējās LVĢMC kļūmes laiks
_pludu_kopija = {"ir": None, "parbaudits": 0.0, "varbutibas": []}  # vai pludu_zonas ir rindas (pārbauda ik 5 min)


def _pludu_serviss(veids, cels, slani, lat, lon):
    d = 0.0002  # ~20 m
    parametri = {
        "service": "WMS", "version": "1.3.0", "request": "GetFeatureInfo", "styles": "", "crs": "EPSG:4326",
        "layers": ",".join(slani), "query_layers": ",".join(slani), "info_format": "application/geojson",
        "bbox": f"{lat - d},{lon - d},{lat + d},{lon + d}", "width": 11, "height": 11, "i": 5, "j": 5,
        "feature_count": 10,
    }
    url = PLUDU_WMS + cels + "?" + "&".join(f"{k}={v}" for k, v in parametri.items())
    atrasti = json.loads(_lejupieladet(url, timeout=PLUDU_TAIMAUTS)).get("features", [])
    varbutibas = [slani[f["layerName"]] for f in atrasti if f.get("layerName") in slani]
    return {"veids": veids, "varbutiba_proc": max(varbutibas)} if varbutibas else None


def _pludu_proc(v):
    v = float(v)
    return int(v) if v.is_integer() else v


def _riga_laiks(sekundes):
    try:
        from zoneinfo import ZoneInfo
        return datetime.fromtimestamp(sekundes, ZoneInfo("Europe/Riga"))
    except Exception:  # bez tzdata (Windows): kā _riga_tagad
        utc = datetime.fromtimestamp(sekundes, timezone.utc)
        return utc + timedelta(hours=3 if 3 < utc.month < 11 else 2)


def _pludu_kopija_ir():
    tagad = time.time()
    if _pludu_kopija["ir"] is not None and tagad - _pludu_kopija["parbaudits"] < 300:
        return _pludu_kopija["ir"]
    try:  # kuras varbūtības kopijā ir (pludu_zonas.py noklusēti 10 % un 1 %)
        varbutibas = vaicat("select json_agg(distinct varbutiba::float8) from pludu_zonas", timeout="5s") or []
    except (psycopg.Error, Kluda):  # tabulas vēl nav (shēma nav palaista) vai DB nav — tad WMS
        varbutibas = []
    varbutibas = sorted((_pludu_proc(v) for v in varbutibas), reverse=True)
    _pludu_kopija.update(ir=bool(varbutibas), parbaudits=tagad, varbutibas=varbutibas)
    return bool(varbutibas)


def _pludi_postgis(lat, lon):
    rindas = vaicat("""
        select coalesce(json_agg(json_build_object('veids', veids, 'varbutiba_proc', v) order by v desc, veids), '[]')
        from (select veids, max(varbutiba::float8) as v from pludu_zonas
              where st_intersects(geom, st_setsrid(st_makepoint(%s, %s), 4326)) group by veids) t""",
                    (lon, lat), timeout="3s")
    veidi = [{"veids": r["veids"], "varbutiba_proc": _pludu_proc(r["varbutiba_proc"])} for r in rindas]
    return {"avots": "lvgmc-pludi-faili", "avota_info": PLUDU_AVOTI["lvgmc-pludi-faili"], "zinams": True,
            "zona": bool(veidi), "veidi": veidi, "nepilnigi": False, "metode": "PostGIS kopija",
            "varbutibas": _pludu_kopija["varbutibas"]}


def _pludu_kesa_lasit(atslega):
    """(laiks, atbilde) no atmiņas vai pludi_kesa; None, ja nav."""
    with _kesas_slots:
        ieraksts = _kesa.get(("pludi", atslega))
    if ieraksts:
        return ieraksts
    try:
        r = vaicat("""select json_build_object('atbilde', atbilde, 'laiks', extract(epoch from laiks))
                      from pludi_kesa where atslega = %s""", (atslega,), timeout="2s")
    except (psycopg.Error, Kluda):
        return None
    if not r:
        return None
    ieraksts = (float(r["laiks"]), r["atbilde"])
    with _kesas_slots:
        _kesa[("pludi", atslega)] = ieraksts
    return ieraksts


def _pludu_kesa_rakstit(atslega, atbilde):
    with _kesas_slots:
        _kesa[("pludi", atslega)] = (time.time(), atbilde)
    if not DSN:
        return
    try:
        with psycopg.connect(DSN, connect_timeout=5) as conn, conn.cursor() as cur:
            cur.execute("set statement_timeout = '3s'")
            cur.execute("""insert into pludi_kesa (atslega, atbilde, laiks) values (%s, %s::jsonb, now())
                           on conflict (atslega) do update set atbilde = excluded.atbilde, laiks = excluded.laiks""",
                        (atslega, json.dumps(atbilde, ensure_ascii=False)))
    except psycopg.Error as e:
        print(f"pludi: kešu neizdevās saglabāt ({atslega}): {e}", file=sys.stderr)


def _pludu_wms(atslega, lat, lon):
    """Visi 3 WMS paralēli; ja neatbild neviens — izņēmums. Veiksmīgu atbildi saglabā kešā (arī DB)."""
    darbi = [_pludu_pavedieni.submit(_pludu_serviss, v, c, s, lat, lon) for v, c, s in PLUDU_SERVISI]
    veidi, kludas = [], 0
    for d in darbi:
        try:
            r = d.result()
        except Exception:  # noqa: BLE001  taimauts, 503, formāts
            kludas += 1
            continue
        if r:
            veidi.append(r)
    if kludas == len(darbi):
        _pludu_kluda[0] = time.time()
        raise RuntimeError("neviens plūdu WMS neatbild")
    veidi.sort(key=lambda v: -v["varbutiba_proc"])
    atbilde = {"avots": "lvgmc-pludi", "zona": bool(veidi), "veidi": veidi, "nepilnigi": kludas > 0}
    _pludu_kesa_rakstit(atslega, atbilde)
    return atbilde


def _pludu_darbs(atslega, lat, lon):
    """Esošā vai jauna WMS pārbaude šai vietai (Future); None, ja jau iet PLUDU_MAX_DARBI pārbaudes."""
    with _kesas_slots:
        darbs = _pludu_darbi.get(atslega)
        if darbs and not darbs.done():
            return darbs
        if sum(1 for d in _pludu_darbi.values() if not d.done()) >= PLUDU_MAX_DARBI:
            return None
        darbs = _pludu_gaidisana.submit(_pludu_wms, atslega, lat, lon)
        _pludu_darbi[atslega] = darbs

    def beigas(_d):
        with _kesas_slots:
            if _pludu_darbi.get(atslega) is darbs:
                del _pludu_darbi[atslega]
    darbs.add_done_callback(beigas)
    return darbs


def _pludu_no_kesas(ieraksts, novecojis):
    laiks, atbilde = ieraksts
    lv, sodien = _riga_laiks(laiks), _riga_laiks(time.time())
    kad = lv.strftime("%H:%M") if lv.date() == sodien.date() else lv.strftime("%d.%m. %H:%M")
    r = {**atbilde, "avota_info": PLUDU_AVOTI["lvgmc-pludi"], "zinams": True, "metode": f"kešs no {kad}",
         "varbutibas": PLUDU_WMS_VARBUTIBAS,
         "laiks": datetime.fromtimestamp(laiks, timezone.utc).isoformat(timespec="seconds")}
    if novecojis:  # LVĢMC neatbild: pēdējā zināmā atbilde; pārlūks to nekešo (no-store)
        r.update(novecojis=True, iemesls=PLUDU_NEATBILD, _statuss=200)
    return r


def _pludu_nezinams():
    # "ielade": true — vecā meklesana.js (pirms šīs versijas) to rāda kā "atbild lēni", nevis kā "nē"
    return {"_statuss": 200, "avots": "lvgmc-pludi", "avota_info": PLUDU_AVOTI["lvgmc-pludi"], "zinams": False,
            "iemesls": PLUDU_NEATBILD, "zona": None, "veidi": [], "metode": None, "ielade": True}


def pludi(q):
    lat, lon = _vieta(q)
    if (q.get("wms") or [""])[0] != "1" and _pludu_kopija_ir():
        try:
            return _pludi_postgis(lat, lon)
        except (psycopg.Error, Kluda) as e:  # DB lēna vai nav: tālāk WMS / kešs
            print(f"pludi: PostGIS neizdevās: {e}", file=sys.stderr)
    lat, lon = round(lat, 4), round(lon, 4)  # ~10 m; kešs pēc tā
    atslega = f"{lat:.4f},{lon:.4f}"
    ieraksts = _pludu_kesa_lasit(atslega)
    if ieraksts:
        vecums = time.time() - ieraksts[0]
        if vecums < (PLUDU_KESA_NEPILNIGA if ieraksts[1].get("nepilnigi") else PLUDU_KESA_DERIGA):
            return _pludu_no_kesas(ieraksts, novecojis=False)

    darbs = _pludu_darbs(atslega, lat, lon)
    nesen_kluda = time.time() - _pludu_kluda[0] < PLUDU_KLUDAS_PAUZE
    if darbs is None or (nesen_kluda and not darbs.done()):
        # pārslogots vai LVĢMC tikko neatbildēja: negaidām — kešs vai "nav zināms" (pārbaude, ja sākta, iet fonā)
        return _pludu_no_kesas(ieraksts, novecojis=True) if ieraksts else _pludu_nezinams()
    try:
        atbilde = darbs.result(timeout=PLUDU_MAX_GAIDIT)
    except (TimeoutError, concurrent.futures.TimeoutError):
        if ieraksts:
            return _pludu_no_kesas(ieraksts, novecojis=True)
        # pirmā gaidīšana: 202, pārbaude turpinās fonā; kartīte jautā vēlreiz pēc 10 s
        return {"_statuss": 202, "ielade": True, "zinojums": "Plūdu kartes ielādējas, mēģiniet pēc 10 s."}
    except Exception:  # noqa: BLE001  LVĢMC neatbild
        return _pludu_no_kesas(ieraksts, novecojis=True) if ieraksts else _pludu_nezinams()
    return {**atbilde, "avota_info": PLUDU_AVOTI["lvgmc-pludi"], "zinams": True, "metode": "LVĢMC WMS",
            "varbutibas": PLUDU_WMS_VARBUTIBAS}


def _pludi_shema():
    """API startā: izveido pludi_kesa, ja tās nav (ar MAP_DB_OWNER_DSN); kļūda neaptur API."""
    if not STATUSS_DSN:
        return
    try:
        with psycopg.connect(STATUSS_DSN, connect_timeout=5) as conn, conn.cursor() as cur:
            cur.execute("set statement_timeout = '10s'")
            cur.execute(PLUDI_SHEMA)
    except psycopg.Error as e:
        print(f"pludi: kešu tabulu neizdevās izveidot: {e}", file=sys.stderr)


import concurrent.futures  # noqa: E402


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
        rez.append({**p, **udens_limenis.ar_slieksni(p), "lat": slat, "lon": slon,
                    "attalums_m": _attalums_m(lat, lon, slat, slon),
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
    s = udens_limenis.slieksni().get(st.get("stacija"))
    return {
        "mediana_m": round(med, 2), "statuss": udens_limenis.statuss(med, s),
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
# + 1 par slidenu ceļu (LVC, tikai šodien, ja dati jau ir kešā) + 1 par ledu LVĢMC brīdinājuma tekstā
# + 1 / + 2 par upes līmeni paaugstināts / kritisks (udens_slieksni.json, sliekšņi no CA plāniem); ne vairāk par 3.
RISKA_BRAZMAS = [(15, 1), (20, 2), (25, 3)]   # diennakts maks. brāzmas, m/s
RISKA_NOKRISNI = [(15, 1), (30, 2)]           # diennakts nokrišņu summa, mm
RISKA_LIMENI = {0: "nav", 1: "paaugstināts", 2: "augsts", 3: "ļoti augsts"}
RISKA_NOVEROTAS_BRAZMAS = 20  # m/s stacijā (svaigs mērījums) → +1 šodien
NOVEROJUMU_ZINAS_BRAZMAS = 15  # m/s: ziņa lentes augšā "Šobrīd brāzmas līdz …"
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


LEDUS_VARDI = re.compile(r"\bledus\b|\bledū\b|\bledu\b|vižņ", re.IGNORECASE)
UDENS_AVOTA_URL = "https://data.gov.lv/dati/lv/dataset/hidrometeorologiskie-noverojumi"
UPJU_STATUSA_LIMENIS = {"paaugstināts": 1, "kritisks": 2}


def _min_ledu(b):
    """Vai brīdinājuma parādībā / tekstā / riskos minēts ledus (ledus iešana, ledus sastrēgumi, vižņi)."""
    return bool(LEDUS_VARDI.search(" ".join(b.get(k) or "" for k in ("paradiba", "teksts", "riski"))))


def _m_lv(x):
    return f"{x:.2f}".replace(".", ",")


def _upju_iemesli(stacijas, hidro, atrast, atslegas):
    """Riska kartes iemesli no upju līmeņa: [(reģiona kods, diena, +1/+2, teksts, avots)]. Tikai stacijas ar slieksni
    (udens_slieksni.json) un svaigu mērījumu; "rit" pēc LVĢMC prognozes mediānas rītdienai, ja tā ir, citādi pēc
    mērījuma (upes līmenis dienas laikā mainās lēni)."""
    slieksni = udens_limenis.slieksni()
    rez = []
    for f in stacijas or []:
        p = f.get("properties") or {}
        s = slieksni.get(p.get("stacija"))
        lim = p.get("limenis_m")
        if not s or lim is None:
            continue
        try:
            laiks = datetime.fromisoformat(p["laiks"].replace("Z", "+00:00"))
        except (KeyError, ValueError, AttributeError):
            continue
        if datetime.now(timezone.utc) - laiks > timedelta(hours=udens_limenis.DERIGS_H):
            continue
        lon, lat = f["geometry"]["coordinates"]
        kods = atrast(lat, lon)
        if not kods:
            continue
        ko = "Ezera" if "ezer" in (s.get("vieta") or "").lower() else "Upes"
        avots = {"nosaukums": f"LVĢMC ūdens līmenis; slieksnis: {(s.get('avots') or {}).get('nosaukums', 'CA plāns')}"
                              + (f", {s['avots']['lpp']} lpp." if (s.get("avots") or {}).get("lpp") else ""),
                 "licence": "CC0 1.0", "url": UDENS_AVOTA_URL}
        vieta = s.get("vieta") or p.get("nosaukums")
        for diena, datums in atslegas:
            vertiba, prognoze = lim, False
            if diena != "sodien":
                med = (hidro.get(p["stacija"]) or {}).get(datums)
                if med:
                    vertiba, prognoze = med[2], True
            st = udens_limenis.statuss(vertiba, s)
            if st not in UPJU_STATUSA_LIMENIS:
                continue
            rez.append((kods, diena, UPJU_STATUSA_LIMENIS[st],
                        f"{ko} līmenis {'pēc prognozes ' if prognoze else ''}{st}: {vieta} {_m_lv(vertiba)} m "
                        f"(kritiskais {_m_lv(s['kritiskais_m'])} m)", avots))
    return rez


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
    ledus = {}  # (kods, diena) → parādība: brīdinājumā minēts ledus (ledus iešana, sastrēgumi, vižņi); +1 pēc prognozes
    try:
        for b in _kesots("bridinajumi", 600, _bridinajumi_dati):
            if b["lidz"] and b["lidz"] < tagad:
                continue
            _p, skarti = _bridinajumu_skartie(b, vietas)
            ar_ledu = _min_ledu(b)
            for diena, datums in atslegas:
                d0 = datetime.strptime(datums, "%Y-%m-%d")
                if (b["no"] and b["no"] >= d0 + timedelta(days=1)) or (b["lidz"] and b["lidz"] < d0):
                    continue
                for kods in skarti:
                    pievienot(kods, diena, b["limenis"], f"LVĢMC {b['krasa'].lower()} brīdinājums: {b['paradiba'].lower()}",
                              BRIDINAJUMU_AVOTS)
                    if ar_ledu:
                        ledus.setdefault((kods, diena), b["paradiba"])
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
    # Ledus no jau ielādēto brīdinājumu teksta (bez jauna pieprasījuma): +1 tajās dienās, kuras brīdinājums aptver
    for (kods, diena), paradiba in ledus.items():
        pievienot(kods, diena, 1, f"ledus (LVĢMC brīdinājums: {paradiba.lower()})", BRIDINAJUMU_AVOTS, klat=True)
    if vietas:
        atrast = _tuvaka_vieta_regions(vietas)
        # Upju līmenis pret sliekšņiem (udens_slieksni.json): +1 paaugstināts, +2 kritisks; šodien pēc mērījuma,
        # rīt pēc LVĢMC hidroloģiskās prognozes mediānas (ja nav — pēc mērījuma)
        try:
            stacijas = _kesots("udens", 900, lambda: udens_limenis.stacijas(timeout=20))
            try:
                hidro = _kesots("hidro_prognoze", 3600, _hidro_prognozes) if time.time() - _hidro_kluda[0] > 300 else {}
            except Kluda:
                _hidro_kluda[0], hidro = time.time(), {}
            for kods, diena, limenis, teksts, avots in _upju_iemesli(stacijas, hidro, atrast, atslegas):
                pievienot(kods, diena, limenis, teksts, avots, klat=True)
        except Kluda:
            pass
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
        # Novērotās brāzmas (LVĢMC stacijas, ne vecākas par 3 h) — tikai šodien, +1
        try:
            for st in _noverojumi_svaigi():
                if st["vecs"] or (st.get("brazmas") or 0) < RISKA_NOVEROTAS_BRAZMAS:
                    continue
                kods = atrast(st["lat"], st["lon"])
                if kods:
                    pievienot(kods, "sodien", 1, f"novērotas brāzmas {_skaitlis_lv(st['brazmas'])} m/s ({st['nosaukums']})",
                              NOVEROJUMU_AVOTS, klat=True)
        except Kluda:
            pass
    for r in riski.values():
        r["iemesli"].sort(key=lambda i: (i["diena"] != "sodien", i["klat"], -i["limenis"]))
    return riski


def _noverojumu_zinas(regioni_, vietas):
    """"Šobrīd brāzmas līdz 24 m/s (Kolka, 10:20)", ja kādā stacijā svaigs mērījums ≥ 15 m/s."""
    stipras = sorted((s_ for s_ in _noverojumi_svaigi() if not s_["vecs"] and (s_.get("brazmas") or 0) >= NOVEROJUMU_ZINAS_BRAZMAS),
                     key=lambda s_: -s_["brazmas"])
    if not stipras:
        return []
    m = stipras[0]
    laiks_lv = datetime.fromisoformat(m["laiks"].replace("Z", "+00:00"))
    try:
        from zoneinfo import ZoneInfo
        laiks_lv = laiks_lv.astimezone(ZoneInfo("Europe/Riga"))
    except Exception:
        laiks_lv = laiks_lv + timedelta(hours=3 if 3 < laiks_lv.month < 11 else 2)
    atrast = _tuvaka_vieta_regions(vietas) if vietas else (lambda *_a: None)
    kodi = sorted({k for k in (atrast(s_["lat"], s_["lon"]) for s_ in stipras) if k})
    citas = ", ".join(f"{s_['nosaukums']} {_skaitlis_lv(s_['brazmas'])}" for s_ in stipras[1:5])
    return [{
        "veids": "noverojums", "paradiba": "Vējš", "limenis": _pec_sliekshna(m["brazmas"], RISKA_BRAZMAS),
        "datums": laiks_lv.strftime("%Y-%m-%d"), "diena": "Šobrīd",
        "virsraksts": f"Šobrīd brāzmas līdz {_skaitlis_lv(m['brazmas'])} m/s ({m['nosaukums']}, {laiks_lv.strftime('%H:%M')})",
        "teksts": f"LVĢMC stacijās ar brāzmām no {NOVEROJUMU_ZINAS_BRAZMAS} m/s: {len(stipras)}" + (f" (arī {citas} m/s)." if citas else "."),
        "regioni": kodi, "bbox": [m["lon"] - 0.3, m["lat"] - 0.2, m["lon"] + 0.3, m["lat"] + 0.2], "avots": NOVEROJUMU_AVOTS,
    }]


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
                      "zibeni, slidenus ceļus un upju līmeni; tas ir mūsu aprēķins, nevis oficiāls brīdinājums.",
            "regioni": kodi, "bbox": _bbox(regioni_, kodi), "avots": PROGNOZU_AVOTS,
        })
    return zinas


ZIBENS_ZINAS_NOVADI = 6  # vairāk novadu ar zibeni — pārējie vienā ziņā "Zibens vēl N novados"


def _izlades(n):
    return f"{n} izlāde" if n % 10 == 1 and n % 100 != 11 else f"{n} izlādes"


def _zibens_zinas():
    """Ziņa lentē katram novadam, kurā pēdējās 30 min ir ≥ 1 zibens (FMI, CC BY 4.0), oranžā līmenī. Tikai no kešotajiem
    datiem: tas pats "zibens_fmi" (60 s) kā /api/zibens, prognožu vietas un novadi (24 h) — jaunu pieprasījumu avotiem nav."""
    try:
        regioni_ = _kesots("prognozu_regioni", 86400, _prognozu_regioni)
        vietas = _kesots("prognozu_vietas", 86400, _prognozu_vietas)
        zibeni = _kesots("zibens_fmi", 60, _fmi_zibens)["zibeni"]
    except Kluda:
        return []
    if not zibeni or not vietas or not regioni_:
        return []
    atrast = _tuvaka_vieta_regions(vietas)
    pa_novadiem = {}
    for z in zibeni:
        kods = atrast(z["lat"], z["lon"])
        if kods in regioni_:
            pa_novadiem.setdefault(kods, []).append(z)
    if not pa_novadiem:
        return []
    try:
        from zoneinfo import ZoneInfo
        riga = ZoneInfo("Europe/Riga")
    except Exception:  # bez tzdata
        riga = timezone(timedelta(hours=3 if 3 < datetime.now().month < 11 else 2))

    def pulkstenis(iso):
        try:
            return datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(riga).strftime("%H:%M")
        except ValueError:
            return ""
    sodien = _riga_tagad().date().isoformat()
    seciba = sorted(pa_novadiem.items(), key=lambda x: (-len(x[1]), regioni_[x[0]]["nosaukums"]))
    zinas = []
    for kods, z in seciba[:ZIBENS_ZINAS_NOVADI if len(seciba) <= ZIBENS_ZINAS_NOVADI else ZIBENS_ZINAS_NOVADI - 1]:
        pedeja = pulkstenis(max(x["laiks"] for x in z))
        zinas.append({
            "veids": "zibens", "paradiba": "Zibens", "limenis": 2, "datums": sodien, "diena": "Šobrīd",
            "vieta": regioni_[kods]["nosaukums"],
            "virsraksts": f"Zibens: {_izlades(len(z))} pēdējās {ZIBENS_MIN} min (FMI, CC BY 4.0)",
            "teksts": (f"Pēdējā izlāde {pedeja}. " if pedeja else "") + "Negaisa laikā palieciet telpās vai automašīnā, turieties prom no kokiem, atklātām vietām un ūdens.",
            "regioni": [kods], "bbox": _bbox(regioni_, [kods]), "avots": ZIBENS_AVOTS,
        })
    if len(seciba) > ZIBENS_ZINAS_NOVADI:
        citi = seciba[ZIBENS_ZINAS_NOVADI - 1:]
        kodi = [k for k, _z in citi]
        nosaukumi = [regioni_[k]["nosaukums"].replace(" novads", " nov.") for k in kodi]
        zinas.append({
            "veids": "zibens", "paradiba": "Zibens", "limenis": 2, "datums": sodien, "diena": "Šobrīd",
            "vieta": f"vēl {len(kodi)} novados",
            "virsraksts": f"Zibens: {_izlades(sum(len(z) for _k, z in citi))} pēdējās {ZIBENS_MIN} min (FMI, CC BY 4.0)",
            "teksts": "Skartie: " + ", ".join(nosaukumi[:8]) + (f" un vēl {len(nosaukumi) - 8}." if len(nosaukumi) > 8
                                                                else "" if nosaukumi[-1].endswith(".") else "."),
            "regioni": kodi, "bbox": _bbox(regioni_, kodi), "avots": ZIBENS_AVOTS,
        })
    return zinas


def prognozes(_q):
    atbilde = _kesots("prognozes_atbilde", 300, _prognozes)
    # Zibens ziņas ar zibens kešas ritmu (60 s), nevis prognozes (5 min); lentē uzreiz aiz "Šobrīd brāzmas"
    try:
        zibens_zinas = _kesots("prognozes_zibens", 60, _zibens_zinas)
    except Exception:  # noqa: BLE001 — zibens nav obligāts: lente strādā bez tā
        zibens_zinas = []
    if not zibens_zinas:
        return atbilde
    zinas = atbilde["zinas"]
    i = sum(1 for z in zinas if z["veids"] == "noverojums")
    return {**atbilde, "zinas": zinas[:i] + zibens_zinas + zinas[i:]}


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
    try:
        noverojumu_zinas = _noverojumu_zinas(regioni_, vietas)
    except Kluda:
        noverojumu_zinas = []
    zinas = noverojumu_zinas + _risku_zinas(riski, regioni_, dienas, sodien) + bridinajumu_zinas + \
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
    zinas.sort(key=lambda z: (z["veids"] != "noverojums", z["veids"] != "riski", z["veids"] != "bridinajums", z["datums"], -z["limenis"],
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


# ---- Laikapstākļi tagad: GET /api/noverojumi (LVĢMC meteoroloģiskie operatīvie dati, data.gov.lv, CC0) ----
# 34 stacijas, katru stundu, pēdējās 48 h; laiks UTC (kā hidroloģiskajiem datiem), vērtības jau m/s, °C, mm.
# Katrai stacijai jaunākais: brāzmas (stundas maks. HWSMX, citādi termiņa WPGST), vidējais vējš (HWNDS / WNS10),
# virziens (HWDAV / WNDD10), temperatūra (TDRY / HTDRY), nokrišņi stundā (HPRAB). Vecāks par 3 h — "vecs".
NOVEROJUMI = "https://data.gov.lv/dati/dataset/40d80be5-0c09-47c4-80f3-fad4bec19f33/resource"
NOVEROJUMI_DATI = NOVEROJUMI + "/17460efb-ae99-4d1d-8144-1068f184b05f/download/meteo_operativie_dati.csv"
NOVEROJUMI_STACIJAS = NOVEROJUMI + "/c32c7afd-0d05-44fd-8b24-1de85b4bf11d/download/meteo_stacijas.csv"
NOVEROJUMU_AVOTS = {"nosaukums": "LVĢMC hidrometeoroloģiskie novērojumi (meteoroloģiskie operatīvie dati)", "licence": "CC0 1.0",
                    "url": "https://data.gov.lv/dati/lv/dataset/hidrometeorologiskie-noverojumi"}
NOVEROJUMI_VECS_H = 3
# lauks → (parametri pēc prioritātes, robežas)
NOVEROJUMU_LAUKI = {
    "brazmas": (("HWSMX", "WPGST"), (0, 70)), "vejs": (("HWNDS", "WNS10"), (0, 60)),
    "virziens": (("HWDAV", "WNDD10"), (0, 360)), "temp": (("TDRY", "HTDRY"), (-50, 50)), "nokrisni_1h": (("HPRAB",), (0, 250)),
}


def _noverojumu_dati():
    stacijas = {}
    for r in _csv(NOVEROJUMI_STACIJAS):
        try:
            stacijas[r["STATION_ID"]] = (r["NAME"].strip(), float(r["GEOGR2"]), float(r["GEOGR1"]))
        except (KeyError, ValueError):
            continue
    parametri = {p: lauks for lauks, (ps, _r) in NOVEROJUMU_LAUKI.items() for p in ps}
    jaunakie = {}  # (stacija, parametrs) → (laiks, vērtība)
    for n, r in enumerate(csv.DictReader(io.StringIO(_lejupieladet(NOVEROJUMI_DATI, timeout=30).decode("utf-8-sig")))):
        if n > 300000:  # ierobežota apstrāde: datne parasti ~35 000 rindu
            break
        lauks = parametri.get(r.get("ABBREVIATION"))
        if not lauks or r.get("STATION_ID") not in stacijas:
            continue
        try:
            laiks = datetime.strptime(r["DATETIME"], "%Y.%m.%d %H:%M:%S").replace(tzinfo=timezone.utc)
            vertiba = float(r["VALUE"])
        except (KeyError, ValueError):
            continue
        apaksa, augsa = NOVEROJUMU_LAUKI[lauks][1]
        if not apaksa <= vertiba <= augsa:
            continue
        atslega = (r["STATION_ID"], r["ABBREVIATION"])
        if atslega not in jaunakie or laiks > jaunakie[atslega][0]:
            jaunakie[atslega] = (laiks, vertiba)
    rez = []
    for sid, (nos, lat, lon) in stacijas.items():
        s_ = {"id": sid, "nosaukums": nos, "lat": lat, "lon": lon}
        laiki = []
        for lauks, (ps, _r) in NOVEROJUMU_LAUKI.items():
            # jaunākais no parametriem; vienādam laikam — pirmais prioritātē
            kandidati = [(jaunakie[(sid, p)], -i) for i, p in enumerate(ps) if (sid, p) in jaunakie]
            if kandidati:
                (laiks, v), _ = max(kandidati, key=lambda k: (k[0][0], k[1]))
                s_[lauks] = round(v, 1)
                laiki.append(laiks)
        if laiki:
            s_["laiks"] = max(laiki).isoformat().replace("+00:00", "Z")
            rez.append(s_)
    return {"stacijas": rez, "ieladets": datetime.now(timezone.utc).isoformat(timespec="seconds")}


def _noverojumi_svaigi():
    tagad = datetime.now(timezone.utc)
    dati = _kesots("noverojumi", 600, _noverojumu_dati)
    return [{**s_, "vecs": tagad - datetime.fromisoformat(s_["laiks"].replace("Z", "+00:00")) > timedelta(hours=NOVEROJUMI_VECS_H)}
            for s_ in dati["stacijas"]]


def noverojumi(q):
    lat, lon = _vieta(q, obligata=False)
    limit = int(_skaitlis(q, "limit", 1, 100) or 100)
    stacijas = _noverojumi_svaigi()
    if lat is not None:
        stacijas = sorted(({**s_, "attalums_m": _attalums_m(lat, lon, s_["lat"], s_["lon"])} for s_ in stacijas),
                          key=lambda s_: s_["attalums_m"])
    svaigas = [s_ for s_ in stacijas if not s_["vecs"] and s_.get("brazmas") is not None]
    maks = max(svaigas, key=lambda s_: s_["brazmas"], default=None)
    return {"avots": NOVEROJUMU_AVOTS, "vecs_h": NOVEROJUMI_VECS_H, "stacijas": stacijas[:limit],
            "maks_brazmas": {k: maks[k] for k in ("nosaukums", "brazmas", "laiks", "lat", "lon")} if maks else None}


# ---- /Laikapstākļi tagad ----


def veseliba(q):
    rez = {"ok": vaicat("select true", timeout="2s")}
    try:  # LVĢMC pret Meteoalarm (rezerves avots): spēkā esošo brīdinājumu skaits, tikai no keša
        rez["bridinajumi"] = _bridinajumu_salidzinajums()
    except Exception as e:  # noqa: BLE001
        rez["bridinajumi"] = {"kluda": type(e).__name__}
    if q.get("statistika", [""])[0] == "1":
        rez["statistika"] = {**_statistika, "db_vienlaicigi": DB_VIENLAICIGI, "pavedieni": threading.active_count()}
    return rez


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
    ("noverojumi", "Laikapstākļi tagad", "LVĢMC meteoroloģisko staciju jaunākā mērījuma vecums",
     ("LVĢMC hidrometeoroloģiskie novērojumi", NOVEROJUMU_AVOTS["url"], *_CC0)),
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
    ("datu_vecums", "Datu vecums", "Ikdienas avotu (ZVA, IeM IC, VKCP, OSM: bankomāti, DUS, noturības punkti, ūdens, Wi-Fi, EV uzlāde, veterināri; GTFS) pēdējā ielāde; hakatons-dati.timer 04:30",
     ("Panelis „Datu avoti” kartē", "https://map.repo.lv/", None, None)),
]
# Ikdienas atjaunošanas avoti (atjaunot_visu.sh); vecāks par 48 h — nedarbojas, par 30 h — traucējumi
STATUSS_IKDIENAS_AVOTI = ("zva-fdu", "iemic-arstniecibas", "iemic-vp", "iemic-pp", "iemic-vugd", "vkcp-udens",
                          "osm", "osm-noturiba", "osm-udens", "osm-wifi", "osm-ev", "osm-vet",
                          "rs-gtfs", "atd-gtfs", "vivi-gtfs")
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


def _parb_noverojumi():
    # caur to pašu kešu kā /api/noverojumi (10 min)
    stacijas = _noverojumi_svaigi()
    svaigas = [s_ for s_ in stacijas if not s_["vecs"]]
    if not stacijas:
        return "nav_datu", "Nav nevienas stacijas datu"
    jaunakais = max(datetime.fromisoformat(s_["laiks"].replace("Z", "+00:00")) for s_ in stacijas)
    vecums = (datetime.now(timezone.utc) - jaunakais).total_seconds()
    teksts = f"{len(svaigas)}/{len(stacijas)} stacijas ar svaigiem datiem; jaunākais mērījums pirms {_laiks_pirms(vecums)}"
    return ("darbojas" if vecums < NOVEROJUMI_VECS_H * 3600 else "traucejumi"), teksts


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



def _parb_datu_vecums():
    # avoti.atjaunots raksta ielade.py; to_jsonb — lai pirms kolonnas pievienošanas būtu "nav datu", nevis kļūda
    rindas = vaicat("""select coalesce(json_agg(json_build_array(kods,
                         extract(epoch from now() - (to_jsonb(a) ->> 'atjaunots')::timestamptz)::int)), '[]')
                       from avoti a where kods = any(%s)""", (list(STATUSS_IKDIENAS_AVOTI),), timeout="5s")
    vecumi = {k: v for k, v in rindas if v is not None}
    if not vecumi:
        return "nav_datu", "Ikdienas atjaunošana vēl nav palaista (hakatons-dati.timer)"
    trukst = [k for k, _ in rindas if k not in vecumi]
    veci = sorted((k for k, v in vecumi.items() if v > 48 * 3600), key=lambda k: -vecumi[k])
    vecakais = max(vecumi.values())
    if veci:
        return "nedarbojas", f"Vecāki par 48 h: {', '.join(veci)} (vecākais pirms {_laiks_pirms(vecakais)})"
    if vecakais > 30 * 3600 or trukst:
        return "traucejumi", (f"Nav ielādēti: {', '.join(trukst)}" if trukst
                              else f"Vecākais avots ielādēts pirms {_laiks_pirms(vecakais)}")
    return "darbojas", f"{_skaits(len(vecumi), 'avots', 'avoti')} atjaunoti; vecākais pirms {_laiks_pirms(vecakais)}"


# kods → (pārbaude, virs cik ms "atbild lēni")
STATUSS_PARBAUDES = {
    "vietne": (_parb_vietne, 5000), "api": (_parb_api, 3000), "adreses": (_parb_adreses, 2500),
    "bridinajumi": (_parb_bridinajumi, 8000), "pludi": (_parb_pludi, 8000), "udens": (_parb_udens, 3000),
    "ca_plani": (_parb_ca_plani, 3000), "patvertnes": (_parb_patvertnes, 3000), "prognozes": (_parb_prognozes, 1000),
    "zibens": (_parb_zibens, 8000), "noverojumi": (_parb_noverojumi, 8000), "augsne": (_parb_augsne, 8000), "celi": (_parb_celi, 8000),
    "satiksme": (_parb_satiksme, 8000), "robezas": (_parb_robezas, 8000),
    "osm": (_parb_osm, 5000), "datu_vecums": (_parb_datu_vecums, 3000),
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
            **({"rezerves": {"nosaukums": METEOALARM_AVOTS, "url": METEOALARM_URL}}
               if kods == "bridinajumi" and _rezerves_aktivs() else {}),
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
    return _punktu_kesa.iegut(("tuvaka", round(lat, 4), round(lon, 4)), lambda: vaicat(
        """select coalesce((select json_build_object('adrese', adrese, 'kods', kods, 'attalums_m', d) from (
             select adrese, kods, round(st_distance(geom::geography,
                    st_setsrid(st_makepoint(%(lon)s, %(lat)s), 4326)::geography))::int as d
             from adreses order by geom <-> st_setsrid(st_makepoint(%(lon)s, %(lat)s), 4326) limit 1) a
           where d <= 300), '{}'::json)""",
        {"lat": lat, "lon": lon}, timeout="2s"))


_punktu_kesa = _LRU(2000, 3600)


PASVALDIBAS_FAILS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "dati", "pasvaldibas.json")


def _pasvaldibas_dati():
    with open(PASVALDIBAS_FAILS, encoding="utf-8") as f:
        return json.load(f)


def pasvaldiba(q):
    """Pašvaldība punktā (regioni: novads vai valstspilsēta) + CA plāns, tīmekļvietne, UR kontakti un VPVKAC kontakts
    (src/karte/db/pasvaldibas.py → src/karte/dati/pasvaldibas.json)."""
    lat, lon = _vieta(q)
    kods = _punktu_kesa.iegut(("pasvaldiba", round(lat, 4), round(lon, 4)), lambda: vaicat(
        """select kods from regioni where tips in ('novads', 'valstspilseta')
           and st_contains(geom, st_setsrid(st_makepoint(%s, %s), 4326)) limit 1""", (lon, lat), timeout="2s"))
    if not kods:
        raise Kluda(404, "vieta nav nevienā pašvaldībā")
    dati = _kesots("pasvaldibas", 3600, _pasvaldibas_dati).get(kods)
    if not dati:
        raise Kluda(404, "pašvaldības dati nav atrasti")
    return {"kods": kods, **dati, "avoti": [
        {"nosaukums": "CA plāni hakatonam (pašvaldību tīmekļvietnes)", "licence": "Oficiāls dokuments",
         "url": "https://github.com/lata-org/ai-open-data-2026-hakatons/tree/main/ca-plani-hakatons"},
        {"nosaukums": "Uzņēmumu reģistrs: publisko personu un iestāžu saraksts", "licence": "CC0 1.0",
         "url": "https://data.gov.lv/dati/dataset/public-persons-institutions"},
        {"nosaukums": "VPVKAC kontakti (2023-11)", "licence": "CC0 1.0",
         "url": "https://data.gov.lv/dati/lv/dataset/vpvkac-kontakti"}]}


# ==== Ziņojumi: iedzīvotāju ziņojumi par bīstamību (production/zinot.js, moderacija.html) — sākums ====
# Pēc lacukarte.lv parauga (notes/research/05 §5): ziņojums = tips + īss teksts + vieta. Glabā vietu ~100 m precizitātē
# (3 zīmes aiz komata), publiski rāda ~1 km (2 zīmes). IP un citus personas datus neglabā (balsu limitam — tikai IP
# jaucējvērtību ar sāli MAP_SALT, ne ilgāk par 2 h). Rāda pēdējās 7 dienas,
# statuss jauns/redzams; paslēpj, ja apstrīdējuši vairāk nekā apstiprinājuši + 2. Licence: CC BY 4.0.
# Tabulu izveido API startā ar MAP_DB_OWNER_DSN (shēma VPS netiek palaista pati); tas pats bloks ir shema.sql.
# Moderācija: MAP_MOD_TOKEN (vides mainīgais) — POST ķermenī, nevis URL; bez tā moderācija ir izslēgta.

ZINOJUMU_TIPI = {"koks": "Nokritis koks", "cels": "Neizbraucams ceļš", "elektriba": "Bojāta elektrolīnija",
                 "udens": "Applūdums", "cits": "Cita bīstamība"}
ZINOJUMI_DIENAS = 7
ZINOJUMI_MINUTE = 10    # jauni ziņojumi minūtē (viss process)
ZINOJUMU_BALSIS_MINUTE = 60
ZINOJUMA_BALSIS_STUNDA = 20  # balsis vienam ziņojumam stundā (visi kopā)
IP_BALSIS_STUNDA = 30        # balsis no vienas IP stundā (visiem ziņojumiem kopā)
ZINOJUMI_LICENCE = {"nosaukums": "Iedzīvotāju ziņojumi (map.repo.lv)", "licence": "CC BY 4.0",
                    "licences_url": "https://creativecommons.org/licenses/by/4.0/"}
ZINOJUMI_ATRUNA = "Iedzīvotāju ziņojumi, nav oficiāla informācija, CC BY 4.0. Ja apdraudēta dzīvība, zvaniet 112."
ZINOJUMI_SHEMA = """
create table if not exists zinojumi (
  id         bigserial primary key,
  tips       text not null check (tips in ('koks', 'cels', 'elektriba', 'udens', 'cits')),
  apraksts   text not null default '' check (length(apraksts) <= 200),
  lat        numeric(6, 3) not null check (lat between 55 and 59),
  lon        numeric(6, 3) not null check (lon between 20 and 29),
  laiks      timestamptz not null default now(),
  apstiprina int not null default 0,
  apstrid    int not null default 0,
  statuss    text not null default 'jauns' check (statuss in ('jauns', 'redzams', 'slepts'))
);
create index if not exists zinojumi_laiks_idx on zinojumi (laiks);
grant select, insert on zinojumi to map_api;
grant update (apstiprina, apstrid, statuss) on zinojumi to map_api;
grant usage on sequence zinojumi_id_seq to map_api;
-- Balsu limits (apstiprinu / apstrīdu): ziņojums + IP jaucējvērtība ar sāli (ne pati IP), glabā ≤ 2 h
create table if not exists zinojumu_balsis (
  zinojums bigint not null,
  ip_hash  text not null,
  laiks    timestamptz not null default now()
);
create index if not exists zinojumu_balsis_zinojums_idx on zinojumu_balsis (zinojums, laiks);
create index if not exists zinojumu_balsis_ip_idx on zinojumu_balsis (ip_hash, laiks);
create index if not exists zinojumu_balsis_laiks_idx on zinojumu_balsis (laiks);
grant select, insert, delete on zinojumu_balsis to map_api;
"""  # tas pats bloks ir src/karte/db/shema.sql
# Teksti ar saitēm un rupjībām netiek pieņemti (vienkāršs filtrs; moderators var paslēpt pārējo)
_ZINOJUMU_AIZLIEGTS = re.compile(
    r"https?:|www\.|\.(com|lv|ru|net|org)\b|<|>"
    r"|\b(pis[aiut]\w*|pizd\w*|bļa\w*|blja\w*|hui\w*|huj\w*|fuck\w*|shit\w*|bitch\w*|"
    r"хуй\w*|хуе\w*|пизд\w*|бля\w*|сука\w*|ебат\w*|еба\w*)", re.I)
_zinojumi_slots = threading.Lock()
_zinojumi_logi = {"jauni": [0.0, 0], "balsis": [0.0, 0]}


def _zinojumi_shema():
    """API startā: izveido tabulu, ja tās nav (ar MAP_DB_OWNER_DSN); kļūda neaptur API."""
    if not STATUSS_DSN:
        return
    try:
        with psycopg.connect(STATUSS_DSN, connect_timeout=5) as conn, conn.cursor() as cur:
            cur.execute("set statement_timeout = '10s'")
            cur.execute(ZINOJUMI_SHEMA)
    except psycopg.Error as e:
        print(f"zinojumi: tabulu neizdevās izveidot: {e}", file=sys.stderr)


def _zinojumi_atlauts(kas, cik):
    with _zinojumi_slots:
        logs, tagad = _zinojumi_logi[kas], time.time()
        if tagad - logs[0] >= 60:
            logs[:] = [tagad, 0]
        if logs[1] >= cik:
            return False
        logs[1] += 1
        return True


_pieprasijums = threading.local()  # do_POST ieliek klienta IP (.ip); galapunkti to nesaņem kā argumentu
_balsis_atmina = {}  # rezerve, ja DB tabulas nav: ("z", id) / ("ip", hash) → [laiki]
_BALSU_SALS = os.environ.get("MAP_SALT", "") or "map.repo.lv-zinojumu-balsis-2026"


def _ip_hash(ip):
    """IP → HMAC-SHA256 ar sāli (MAP_SALT), 32 heks. zīmes; pati IP netiek glabāta."""
    import hmac
    return hmac.new(_BALSU_SALS.encode(), (ip or "?").encode(), "sha256").hexdigest()[:32]


def _balsu_limits_atmina(zid, ip_hash):
    tagad = time.time()
    with _zinojumi_slots:
        if len(_balsis_atmina) > 20000:
            for k in [k for k, v in _balsis_atmina.items() if not v or tagad - v[-1] > 3600]:
                del _balsis_atmina[k]
        z = _balsis_atmina.setdefault(("z", zid), [])
        ip = _balsis_atmina.setdefault(("ip", ip_hash), [])
        z[:] = [t for t in z if tagad - t < 3600]
        ip[:] = [t for t in ip if tagad - t < 3600]
        if len(z) >= ZINOJUMA_BALSIS_STUNDA:
            return "zinojums"
        if len(ip) >= IP_BALSIS_STUNDA:
            return "ip"
        z.append(tagad)
        ip.append(tagad)
    return None


def _balsu_limits(zid, ip_hash):
    """None — balsi drīkst skaitīt (un tā ir pierakstīta); "zinojums" / "ip" — stundas limits sasniegts.
    Datubāzē (tabula zinojumu_balsis), lai limits paliek pēc API pārstartēšanas; ja tabulas nav — atmiņā."""
    try:
        with psycopg.connect(DSN, connect_timeout=5) as conn, conn.cursor() as cur:
            cur.execute("set statement_timeout = '3s'")
            cur.execute("""select (select count(*) from zinojumu_balsis where zinojums = %s and laiks > now() - interval '1 hour'),
                                  (select count(*) from zinojumu_balsis where ip_hash = %s and laiks > now() - interval '1 hour')""",
                        (zid, ip_hash))
            z, ip = cur.fetchone()
            if z >= ZINOJUMA_BALSIS_STUNDA:
                return "zinojums"
            if ip >= IP_BALSIS_STUNDA:
                return "ip"
            cur.execute("delete from zinojumu_balsis where laiks < now() - interval '2 hours'")
            cur.execute("insert into zinojumu_balsis (zinojums, ip_hash) values (%s, %s)", (zid, ip_hash))
            return None
    except psycopg.Error as e:
        print(f"zinojumi: balsu limits atmiņā ({e.__class__.__name__})", file=sys.stderr)
        return _balsu_limits_atmina(zid, ip_hash)


def _zinojumi_db(sql, params=()):
    """Rakstīšana kā map_api (insert / update tikai atļautajās kolonnās)."""
    try:
        with psycopg.connect(DSN, connect_timeout=5) as conn, conn.cursor() as cur:
            cur.execute("set statement_timeout = '3s'")
            cur.execute(sql, params)
            return cur.fetchone()
    except psycopg.Error as e:
        print(f"zinojumi: {e}", file=sys.stderr)
        raise Kluda(503, "ziņojumus pašlaik nevar saglabāt") from None


def zinojumi(q):
    """GET /api/zinojumi?bbox=minLon,minLat,maxLon,maxLat[&dienas=1..7] — publiskie ziņojumi, vieta ~1 km."""
    dienas = int(_skaitlis(q, "dienas", 1, ZINOJUMI_DIENAS) or ZINOJUMI_DIENAS)
    bbox = q.get("bbox", [""])[0]
    try:
        x1, y1, x2, y2 = (float(v) for v in bbox.split(",")) if bbox else (20, 55, 29, 59)
    except ValueError:
        raise Kluda(400, "bbox: minLon,minLat,maxLon,maxLat") from None
    try:
        saraksts = vaicat(
            """select coalesce(json_agg(json_build_object('id', id, 'tips', tips, 'apraksts', apraksts,
                      'lat', round(lat, 2), 'lon', round(lon, 2), 'laiks', laiks, 'apstiprina', apstiprina,
                      'apstrid', apstrid, 'statuss', statuss) order by laiks desc), '[]')
               from zinojumi
               where statuss in ('jauns', 'redzams') and apstrid <= apstiprina + 2
                 and laiks > now() - make_interval(days => %s)
                 and lon between %s and %s and lat between %s and %s""",
            (dienas, x1, x2, y1, y2), timeout="2s")
    except psycopg.Error:
        saraksts = None  # tabulas vēl nav vai DB nav pieejama
    return {"avots": ZINOJUMI_LICENCE, "atruna": ZINOJUMI_ATRUNA, "dienas": dienas, "tipi": ZINOJUMU_TIPI,
            "pieejams": saraksts is not None, "zinojumi": saraksts or []}


def zinojumi_pievienot(dati):
    """POST /api/zinojumi {tips, apraksts, lat, lon} → 201 {id, …}."""
    if not isinstance(dati, dict):
        raise Kluda(400, "vajag JSON objektu")
    tips = dati.get("tips")
    if tips not in ZINOJUMU_TIPI:
        raise Kluda(400, "nezināms ziņojuma tips")
    apraksts = " ".join(str(dati.get("apraksts") or "").split())
    if len(apraksts) > 200:
        raise Kluda(400, "apraksts: ne garāks par 200 zīmēm")
    if _ZINOJUMU_AIZLIEGTS.search(apraksts):
        raise Kluda(400, "apraksts: bez saitēm un rupjībām")
    try:
        lat, lon = round(float(dati.get("lat")), 3), round(float(dati.get("lon")), 3)
    except (TypeError, ValueError):
        raise Kluda(400, "vajag lat un lon") from None
    if not (55 <= lat <= 59 and 20 <= lon <= 29):
        raise Kluda(400, "vieta nav Latvijā")
    if not _zinojumi_atlauts("jauni", ZINOJUMI_MINUTE):
        raise Kluda(429, "pārāk daudz ziņojumu, mēģiniet pēc minūtes")
    rinda = _zinojumi_db("insert into zinojumi (tips, apraksts, lat, lon) values (%s, %s, %s, %s) returning id, laiks",
                         (tips, apraksts, lat, lon))
    return 201, {"id": rinda[0], "tips": tips, "apraksts": apraksts, "lat": round(lat, 2), "lon": round(lon, 2),
                 "laiks": rinda[1].isoformat(), "apstiprina": 0, "apstrid": 0, "statuss": "jauns"}


def _moderators(dati):
    import hmac
    gaidits = os.environ.get("MAP_MOD_TOKEN", "")
    dots = str(dati.get("token") or "") if isinstance(dati, dict) else ""
    if not gaidits or not hmac.compare_digest(dots.encode(), gaidits.encode()):
        raise Kluda(403, "nav moderatora tiesību")


def zinojumi_darbiba(dati, zid, darbiba):
    """POST /api/zinojumi/<id>/apstiprinat|apstridet (visi) un /slept|radit (moderators, {token})."""
    if darbiba in ("slept", "radit"):
        _moderators(dati)
        rinda = _zinojumi_db("update zinojumi set statuss = %s where id = %s returning id, statuss",
                             ("slepts" if darbiba == "slept" else "redzams", int(zid)))
    else:
        if not _zinojumi_atlauts("balsis", ZINOJUMU_BALSIS_MINUTE):
            raise Kluda(429, "pārāk daudz balsojumu, mēģiniet pēc minūtes")
        limits = _balsu_limits(int(zid), _ip_hash(getattr(_pieprasijums, "ip", "")))
        if limits == "zinojums":
            raise Kluda(429, "par šo ziņojumu stundas laikā jau nobalsots daudz reižu, mēģiniet vēlāk")
        if limits == "ip":
            raise Kluda(429, "no Jūsu tīkla stundas laikā jau ir daudz balsu, mēģiniet vēlāk")
        kolonna = "apstiprina" if darbiba == "apstiprinat" else "apstrid"
        rinda = _zinojumi_db(f"update zinojumi set {kolonna} = {kolonna} + 1 where id = %s and statuss <> 'slepts'"
                             " returning apstiprina, apstrid", (int(zid),))
    if rinda is None:
        raise Kluda(404, "ziņojums nav atrasts")
    return 200, ({"id": rinda[0], "statuss": rinda[1]} if darbiba in ("slept", "radit")
                 else {"id": int(zid), "apstiprina": rinda[0], "apstrid": rinda[1]})


def zinojumi_moderacija(dati):
    """POST /api/zinojumi/moderacija {token} → pēdējās 30 dienas, arī paslēptie, vieta ~100 m."""
    _moderators(dati)
    rindas = _zinojumi_db(
        """select coalesce(json_agg(json_build_object('id', id, 'tips', tips, 'apraksts', apraksts, 'lat', lat,
                  'lon', lon, 'laiks', laiks, 'apstiprina', apstiprina, 'apstrid', apstrid, 'statuss', statuss)
                  order by laiks desc), '[]')
           from zinojumi where laiks > now() - interval '30 days'""")
    return 200, {"zinojumi": rindas[0], "tipi": ZINOJUMU_TIPI}

# ==== Ziņojumi — beigas ====


# ---- Abonēšana bez lietotnes: GET /api/plusma.xml (Atom 1.0) un /api/kalendars.ics (iCalendar) ----
# Pašvaldībai (?regions=<VZD kods vai ATVK>) vai visai Latvijai: LVĢMC brīdinājumi, rītdienas prognoze (brāzmas ≥ 15 m/s
# vai nokrišņi ≥ 15 mm), upes, kas 24 h kāpušas > 10 cm, LVC slēgumi un negadījumi, zibens pēdējās 30 min. Viss no tiem
# pašiem kešotajiem datiem, ko rāda karte; plūsma kešota 5 min. <id> ir stabili (tas pats notikums — tas pats id).

import email.utils  # noqa: E402
import xml.etree.ElementTree as _ET  # noqa: E402

ABONET_VIETNE = "https://map.repo.lv/"
ABONET_BRAZMAS, ABONET_NOKRISNI, ABONET_UDENS_CM = 15, 15, 10
_CC0_AVOTS = ("CC0 1.0", "https://creativecommons.org/publicdomain/zero/1.0/")


def _abonet_regions(q):
    """(kods, nosaukums) vai (None, "Latvija"); pieņem VZD kodu (regioni.kods) vai pašvaldības ATVK."""
    vertiba = q.get("regions", [""])[0].strip()
    if not vertiba:
        return None, "Latvija"
    if not KODS.match(vertiba):
        raise Kluda(400, "regions: VZD kods vai ATVK")
    pasv = _kesots("pasvaldibas", 3600, _pasvaldibas_dati)
    kods = next((k for k, v in pasv.items() if v.get("atvk") == vertiba), vertiba)
    vardi = _kesots("regionu_vardi", 3600, lambda: {r["kods"]: r for r in regioni({})})
    if kods not in vardi:
        raise Kluda(404, "reģions nav atrasts")
    return kods, vardi[kods]["nosaukums"]


def _punkti_regiona(kods, punkti):
    """[(lat, lon)] → [bool]: vai punkts ir reģionā (PostGIS); bez datubāzes — pēc reģiona bbox."""
    if not punkti or kods is None:
        return [True] * len(punkti)
    try:
        return vaicat("""select coalesce(json_agg(st_contains(r.geom, st_setsrid(st_makepoint(p.lon, p.lat), 4326)) order by p.n), '[]')
                         from regioni r, unnest(%s::float8[], %s::float8[]) with ordinality as p(lat, lon, n)
                         where r.kods = %s""", ([a for a, _ in punkti], [b for _, b in punkti], kods), timeout="5s")
    except (psycopg.Error, Kluda):
        bbox = _kesots("regionu_vardi", 3600, lambda: {r["kods"]: r for r in regioni({})})[kods]["bbox"]
        return [bbox[1] <= a <= bbox[3] and bbox[0] <= b <= bbox[2] for a, b in punkti]


def _riga_uz_utc(teksts):
    """LVĢMC vietējais laiks (bez zonas) → UTC datetime."""
    if not teksts:
        return None
    t = datetime.fromisoformat(teksts)
    if t.tzinfo:
        return t.astimezone(timezone.utc)
    try:
        from zoneinfo import ZoneInfo
        return t.replace(tzinfo=ZoneInfo("Europe/Riga")).astimezone(timezone.utc)
    except Exception:  # bez tzdata: vasarā UTC+3, ziemā UTC+2 (aptuveni)
        return (t - timedelta(hours=3 if 3 < t.month < 11 else 2)).replace(tzinfo=timezone.utc)


def _abonet_ieraksti(kods, nosaukums):
    """Plūsmas ieraksti: [{id, virsraksts, teksts, laiks (UTC), saite, avots: (nosaukums, url, licence), no, lidz}]."""
    vietne = ABONET_VIETNE + (f"?regions={kods}" if kods else "")
    rez = []
    prog = prognozes({})
    br = {b["id"]: b for b in bridinajumi({})["bridinajumi"]}
    for z in prog["zinas"]:
        if z["veids"] != "bridinajums" or (kods and kods not in z.get("regioni", [])):
            continue
        b = br.get(z.get("id"), {})
        no, lidz = _riga_uz_utc(b.get("no")), _riga_uz_utc(b.get("lidz"))
        rez.append({"id": f"tag:map.repo.lv,2026:bridinajums:{z.get('id')}", "virsraksts": z["virsraksts"],
                    "teksts": z["teksts"] + (("\n\n" + b["riski"]) if b.get("riski") else ""), "laiks": no or datetime.now(timezone.utc),
                    "saite": vietne, "no": no, "lidz": lidz, "krasa": b.get("krasa"), "paradiba": z.get("paradiba"),
                    "avots": ("LVĢMC hidrometeoroloģiskie brīdinājumi", "https://data.gov.lv/dati/lv/dataset/hidrometeorologiskie-bridinajumi", "CC0 1.0")})
    # rītdienas prognoze
    rit = (_riga_tagad().date() + timedelta(days=1)).isoformat()
    try:
        mainita = email.utils.parsedate_to_datetime(prog.get("prognoze_mainita")) if prog.get("prognoze_mainita") else None
    except (TypeError, ValueError):
        mainita = None
    prog_avots = ("LVĢMC meteoroloģiskās prognozes apdzīvotām vietām",
                  "https://data.gov.lv/dati/lv/dataset/meteorologiskas-prognozes-apdzivotam-vietam-jaunaka-datu-kopa", "CC0 1.0")
    regioni_prog = {kods: prog["regioni"].get(kods)} if kods else prog["regioni"]
    for rk, r in regioni_prog.items():
        d = (r or {}).get("dienas", {}).get(rit)
        if not d:
            continue
        dalas = []
        if (d.get("brazmas") or 0) >= ABONET_BRAZMAS:
            dalas.append(f"brāzmas līdz {round(d['brazmas'])} m/s ({d.get('brazmas_vieta') or ''})".replace(" ()", ""))
        if (d.get("nokrisni") or 0) >= ABONET_NOKRISNI:
            dalas.append(f"nokrišņi līdz {round(d['nokrisni'])} mm ({d.get('nokrisni_vieta') or ''})".replace(" ()", ""))
        if dalas:
            rez.append({"id": f"tag:map.repo.lv,2026:prognoze:{rk}:{rit}", "virsraksts": f"Rīt {r['nosaukums']}: " + ", ".join(dalas),
                        "teksts": f"{d.get('laiks') or ''}. Prognoze nav oficiāls brīdinājums.".lstrip(". "),
                        "laiks": mainita or datetime.now(timezone.utc), "saite": ABONET_VIETNE + f"?regions={rk}", "avots": prog_avots})
    # upes, kas kāpj
    try:
        stacijas = [f["properties"] | {"lat": f["geometry"]["coordinates"][1], "lon": f["geometry"]["coordinates"][0]}
                    for f in _kesots("udens", 900, lambda: udens_limenis.stacijas(timeout=20))]
    except Kluda:
        stacijas = []
    kapj = [x for x in stacijas if (x.get("izmaina_24h_cm") or 0) > ABONET_UDENS_CM]
    for x, ir in zip(kapj, _punkti_regiona(kods, [(x["lat"], x["lon"]) for x in kapj])):
        if ir:
            laiks = datetime.fromisoformat(x["laiks"].replace("Z", "+00:00"))
            rez.append({"id": f"tag:map.repo.lv,2026:udens:{x['stacija']}:{laiks.date().isoformat()}",
                        "virsraksts": f"{x['nosaukums']}: ūdens līmenis 24 h cēlies par {x['izmaina_24h_cm']} cm (tagad {x['limenis_cm']} cm)",
                        "teksts": "Līmenis cm virs posteņa nulles. Bīstamības līmeņi nav atvērtie dati.", "laiks": laiks,
                        "saite": vietne, "avots": ("LVĢMC hidroloģiskie novērojumi", "https://data.gov.lv/dati/lv/dataset/hidrometeorologiskie-noverojumi", "CC0 1.0")})
    # ceļu slēgumi un negadījumi
    tagad = datetime.now(timezone.utc)
    notikumi = [n for t, saraksts in celu_notikumi_visi() if t in ("slegums", "negadijums", "joslas_slegums") for n in (saraksts or [])
                if not (_datex_laiks(n["lidz"]) and _datex_laiks(n["lidz"]) < tagad) and not (_datex_laiks(n["no"]) and _datex_laiks(n["no"]) > tagad)]
    redzeti = set()
    for n, ir in zip(notikumi, _punkti_regiona(kods, [(n["lat"], n["lon"]) for n in notikumi])):
        if ir and n["id"] not in redzeti:
            redzeti.add(n["id"])
            rez.append({"id": f"tag:map.repo.lv,2026:celi:{n['id']}", "virsraksts": n["nosaukums"] + (f" · {n['cels']}" if n.get("cels") else ""),
                        "teksts": n.get("apraksts") or "", "laiks": _datex_laiks(n["no"]) or tagad, "saite": vietne,
                        "avots": ("LVC ceļu notikumi (DATEX II, transportdata.gov.lv)", "https://transportdata.gov.lv/", "CC0 1.0")})
    # zibens pēdējās 30 min
    try:
        z = zibens({})
    except Kluda:
        z = {}
    zibeni = z.get("zibeni") or []
    skaits = sum(_punkti_regiona(kods, [(x["lat"], x["lon"]) for x in zibeni])) if zibeni else 0
    if skaits:
        lidz = datetime.fromisoformat(z["lidz"])
        rez.append({"id": f"tag:map.repo.lv,2026:zibens:{kods or 'latvija'}:{lidz.strftime('%Y%m%d%H')}",
                    "virsraksts": f"Zibens pēdējās 30 min: {skaits} izlādes ({nosaukums})",
                    "teksts": "Negaisa laikā turieties prom no kokiem un ūdens; ja apdraudēta dzīvība, zvaniet 112.", "laiks": lidz,
                    "saite": vietne, "avots": ("Ilmatieteen laitos (FMI) atvērtie dati", "https://en.ilmatieteenlaitos.fi/open-data", "CC BY 4.0")})
    rez.sort(key=lambda e: e["laiks"], reverse=True)
    return rez


def _iso(t):
    return t.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _atom(kods, nosaukums, ieraksti):
    A = "http://www.w3.org/2005/Atom"
    _ET.register_namespace("", A)
    f = _ET.Element(f"{{{A}}}feed", {"{http://www.w3.org/XML/1998/namespace}lang": "lv"})

    def pievienot(vecaks, tags, teksts=None, **atr):
        e = _ET.SubElement(vecaks, f"{{{A}}}{tags}", atr)
        if teksts is not None:
            e.text = teksts
        return e

    pievienot(f, "id", f"tag:map.repo.lv,2026:plusma:{kods or 'latvija'}")
    pievienot(f, "title", f"Krīzes karte: {nosaukums} — brīdinājumi un situācija")
    pievienot(f, "subtitle", "LVĢMC brīdinājumi, rītdienas prognoze, upju līmenis, ceļu slēgumi un zibens no atvērtajiem datiem.")
    pievienot(f, "link", rel="self", href=ABONET_VIETNE + "api/plusma.xml" + (f"?regions={kods}" if kods else ""))
    pievienot(f, "link", rel="alternate", href=ABONET_VIETNE + (f"?regions={kods}" if kods else ""))
    pievienot(f, "updated", _iso(max((e["laiks"] for e in ieraksti), default=datetime.now(timezone.utc))))
    autors = pievienot(f, "author")
    pievienot(autors, "name", "map.repo.lv")
    pievienot(autors, "uri", ABONET_VIETNE)
    pievienot(f, "rights", "Apkopojums CC BY 4.0 (map.repo.lv); dati — katra ieraksta avota licence.")
    for e in ieraksti:
        x = pievienot(f, "entry")
        pievienot(x, "id", e["id"])
        pievienot(x, "title", e["virsraksts"])
        pievienot(x, "updated", _iso(e["laiks"]))
        pievienot(x, "link", rel="alternate", href=e["saite"])
        nos, url, licence = e["avots"]
        laiki = (f"\nSpēkā: {_iso(e['no'])} — {_iso(e['lidz'])}" if e.get("no") and e.get("lidz") else "")
        pievienot(x, "summary", f"{e['teksts']}{laiki}\n\nAvots: {nos} ({url}) · {licence}. Ja apdraudēta dzīvība, zvaniet 112.")
    return '<?xml version="1.0" encoding="utf-8"?>\n' + _ET.tostring(f, encoding="unicode")


def _ics_teksts(t):
    return t.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\r\n", "\\n").replace("\n", "\\n")


def _ics_locit(rinda):
    """RFC 5545: rindas ne garākas par 75 oktetiem; turpinājums sākas ar atstarpi (UTF-8 burtus nepārdala)."""
    b = rinda.encode("utf-8")
    if len(b) <= 75:
        return rinda
    dalas, cur = [], ""
    for ch in rinda:
        if len((cur + ch).encode("utf-8")) > (75 if not dalas else 74):
            dalas.append(cur)
            cur = ""
        cur += ch
    dalas.append(cur)
    return "\r\n ".join(dalas)


def _ics(kods, nosaukums, ieraksti):
    tagad = _iso(datetime.now(timezone.utc)).replace("-", "").replace(":", "")
    ut = lambda t: _iso(t).replace("-", "").replace(":", "")  # noqa: E731
    rindas = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//map.repo.lv//Krizes karte//LV", "CALSCALE:GREGORIAN",
              "METHOD:PUBLISH", f"X-WR-CALNAME:{_ics_teksts('Brīdinājumi: ' + nosaukums)}", "X-PUBLISHED-TTL:PT30M",
              "REFRESH-INTERVAL;VALUE=DURATION:PT30M"]
    for e in ieraksti:
        if not e["id"].startswith("tag:map.repo.lv,2026:bridinajums:") or not e.get("no"):
            continue
        lidz = e.get("lidz") or (e["no"] + timedelta(hours=24))
        nos, url, licence = e["avots"]
        rindas += ["BEGIN:VEVENT", f"UID:{e['id'].rsplit(':', 1)[1]}-{kods or 'latvija'}@map.repo.lv", f"DTSTAMP:{tagad}",
                   f"DTSTART:{ut(e['no'])}", f"DTEND:{ut(lidz)}", f"SUMMARY:{_ics_teksts(e['virsraksts'])}",
                   f"DESCRIPTION:{_ics_teksts(e['teksts'] + chr(10) + chr(10) + f'Avots: {nos} · {licence}. Ja apdraudēta dzīvība, zvaniet 112.')}",
                   f"URL:{e['saite']}", "TRANSP:TRANSPARENT", "END:VEVENT"]
    rindas.append("END:VCALENDAR")
    return "\r\n".join(_ics_locit(r) for r in rindas) + "\r\n"


def plusma(q):
    kods, nosaukums = _abonet_regions(q)
    xml = _kesots(("plusma", kods), 300, lambda: _atom(kods, nosaukums, _abonet_ieraksti(kods, nosaukums)))
    return {"_saturs": xml, "_tips": "application/atom+xml; charset=utf-8"}


def kalendars(q):
    kods, nosaukums = _abonet_regions(q)
    ics = _kesots(("kalendars", kods), 300, lambda: _ics(kods, nosaukums, _abonet_ieraksti(kods, nosaukums)))
    return {"_saturs": ics, "_tips": "text/calendar; charset=utf-8"}


# /api/prognoze?lat=&lon= — nākamās ~24 h tuvākajai LVĢMC prognožu vietai (ikstundas fails, CKAN datastore API;
# tā pati datu kopa kā PROGNOZU_AVOTS, CC0 1.0). Fails sniedz ~25 h uz priekšu; DATUMS — Latvijas vietējais laiks.
CKAN_API = "https://data.gov.lv/dati/api/3/action/"
PROGNOZU_STUNDAS_ID = "4e9b37dc-a486-4af1-8964-b370f659811a"  # "Prognožu dati (ikstundas)"
PROGNOZU_STUNDU_PARAMETRI = {"2": "temp", "6": "brazmas", "7": "nokrisni", "11": "negaiss"}  # °C, m/s, mm/h, %
PROGNOZE_MIN_STUNDAS = 6  # mazāk atlikušu stundu (fails sen nav atjaunots) — prognozi nerāda


def _prognozu_punkti():
    """Vietas ar ikstundas prognozi (~1300 no ~6400 cities.csv): (CITY_ID, nosaukums, lat, lon)."""
    parametri = {"resource_id": PROGNOZU_STUNDAS_ID, "distinct": "true", "fields": "CITY_ID", "limit": 32000,
                 "filters": json.dumps({"PARA_ID": 2})}
    dati = json.loads(_lejupieladet(CKAN_API + "datastore_search?" + urllib.parse.urlencode(parametri), timeout=8))
    ar_stundam = {r["CITY_ID"] for r in dati["result"]["records"]}
    teksts = _lejupieladet(PROGNOZU_VIETAS, timeout=8).decode("utf-8-sig")
    punkti = [(r["CITY_ID"], r["NOSAUKUMS"], float(r["LAT"]), float(r["LON"]))
              for r in csv.DictReader(io.StringIO(teksts)) if r.get("LAT") and r.get("LON") and r["CITY_ID"] in ar_stundam]
    if not punkti:
        raise ValueError("nav vietu ar ikstundas prognozi")
    return punkti


def _prognoze_stundas(vietas_id):
    parametri = {
        "resource_id": PROGNOZU_STUNDAS_ID, "sort": "DATUMS", "limit": 1000, "fields": "PARA_ID,DATUMS,VERTIBA",
        "filters": json.dumps({"CITY_ID": vietas_id, "PARA_ID": [int(p) for p in PROGNOZU_STUNDU_PARAMETRI]}),
    }
    dati = json.loads(_lejupieladet(CKAN_API + "datastore_search?" + urllib.parse.urlencode(parametri), timeout=8))
    if not dati.get("success"):
        raise ValueError("datastore_search neizdevās")
    return [(str(r["PARA_ID"]), str(r["DATUMS"])[:19], r["VERTIBA"]) for r in dati["result"]["records"]]


def _prognoze_izdota():
    dati = json.loads(_lejupieladet(CKAN_API + "resource_show?id=" + PROGNOZU_STUNDAS_ID, timeout=8))
    laiks = (dati.get("result") or {}).get("last_modified")
    return laiks[:19] + "Z" if laiks else None  # CKAN: UTC bez zonas


def _prognozes_riski(tmin, tmax, nokrisni, brazmas, negaiss):
    """Riska vārdi pēc PROGNOZU_SLIEKSNI (diennakts sliekšņi derīgi 24 h logam); pirmais — nozīmīgākais."""
    riski = []
    lim = _limenis("brazmas", brazmas)
    if lim is not None:
        riski.append((lim, "vētra" if lim >= 2 else "stiprs vējš"))
    lim = _limenis("nokrisni", nokrisni)
    if lim is not None:
        veids = "sniegs" if tmax is not None and tmax <= 1 else "lietus"
        riski.append((lim, ("stiprs " if lim >= 1 else "") + veids))
    if negaiss is not None and negaiss >= 50:
        riski.append((1 if negaiss >= 80 else 0, "pērkona negaiss"))
    lim = _limenis("sals", tmin)
    if lim is not None:
        riski.append((lim, "salna" if tmin > -5 else "sals"))
    lim = _limenis("karstums", tmax)
    if lim is not None:
        riski.append((lim, "karstums"))
    riski.sort(key=lambda r: -r[0])  # stabila kārtošana: vienādā līmenī vējš → nokrišņi → negaiss → sals → karstums
    return [{"vards": v, "limenis": lim} for lim, v in riski]


def prognoze(q):
    lat, lon = _vieta(q)
    punkti = _kesots("prognozu_punkti", 6 * 3600, _prognozu_punkti)
    kx = math.cos(math.radians(lat))
    vid, nosaukums, plat, plon = min(punkti, key=lambda p: (p[2] - lat) ** 2 + ((p[3] - lon) * kx) ** 2)
    rindas = _kesots(("prognoze", vid), 1800, lambda: _prognoze_stundas(vid))
    try:
        izdota = _kesots("prognoze_izdota", 1800, _prognoze_izdota)
    except Kluda:
        izdota = None
    no = _riga_tagad().strftime("%Y-%m-%dT%H:00:00")
    stundas = {}  # DATUMS → lauks → vērtība
    for para, datums, vertiba in rindas:
        if datums >= no and vertiba not in (None, ""):
            stundas.setdefault(datums, {})[PROGNOZU_STUNDU_PARAMETRI[para]] = float(vertiba)
    laiki = sorted(stundas)[:24]
    vieta = {"id": vid, "nosaukums": nosaukums, "attalums_m": _attalums_m(lat, lon, plat, plon)}
    if len(laiki) < PROGNOZE_MIN_STUNDAS:
        return {"prognoze": None, "vieta": vieta, "izdota": izdota, "avots": PROGNOZU_AVOTS}

    def vertibas(lauks):
        return [stundas[t][lauks] for t in laiki if lauks in stundas[t]]
    temp, brazmas, nokrisni, negaiss = vertibas("temp"), vertibas("brazmas"), vertibas("nokrisni"), vertibas("negaiss")
    p = {
        "no": laiki[0], "lidz": laiki[-1], "stundas": len(laiki),
        "tmin": min(temp, default=None), "tmax": max(temp, default=None),
        "nokrisni_mm": round(sum(nokrisni), 1) if nokrisni else None,
        "brazmas_max": max(brazmas, default=None), "negaiss_max": max(negaiss, default=None),
    }
    p["riski"] = _prognozes_riski(p["tmin"], p["tmax"], p["nokrisni_mm"], p["brazmas_max"], p["negaiss_max"])
    return {"prognoze": p, "vieta": vieta, "izdota": izdota, "avots": PROGNOZU_AVOTS}


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
    (re.compile(r"^/api/noverojumi/?$"), noverojumi, 300),
    (re.compile(r"^/api/veseliba/?$"), veseliba, 0),
    (re.compile(r"^/api/celi/?$"), celi, 120),
    (re.compile(r"^/api/satiksme/?$"), satiksme, 60),
    (re.compile(r"^/api/statuss/?$"), statuss, 60),
    (re.compile(r"^/api/meklejumi/top/?$"), meklejumi_top, 60),
    (re.compile(r"^/api/zinojumi/?$"), zinojumi, 15),
    (re.compile(r"^/api/plusma\.xml$"), plusma, 300),
    (re.compile(r"^/api/kalendars\.ics$"), kalendars, 300),
    (re.compile(r"^/api/prognoze/?$"), prognoze, 600),
]
POST_MARSRUTI = [
    (re.compile(r"^/api/meklejumi/?$"), meklejumi_pievienot),
    (re.compile(r"^/api/zinojumi/?$"), zinojumi_pievienot),
    (re.compile(r"^/api/zinojumi/moderacija/?$"), zinojumi_moderacija),
    (re.compile(r"^/api/zinojumi/(\d{1,12})/(apstiprinat|apstridet|slept|radit)/?$"), zinojumi_darbiba),
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
                if isinstance(rez, dict) and "_saturs" in rez:  # Atom / iCalendar
                    return self._teksts(rez["_saturs"], rez["_tips"], kesot)
                if isinstance(rez, dict) and "_statuss" in rez:  # piem., 202 "ielādējas"
                    statuss = rez.pop("_statuss")
                    return self._atbilde(statuss, rez, 0)
                return self._atbilde(200, rez, kesot)
            except Kluda as e:
                return self._atbilde(e.statuss, {"kluda": str(e)}, 0)
            except psycopg.Error as e:
                self.log_error("db: %s", e)
                return self._atbilde(503, {"kluda": "datubāze nav pieejama"}, 0)
            except Exception as e:  # noqa: BLE001 — klientam vienmēr JSON, nevis pārtraukts savienojums
                self.log_error("kļūda %s: %r", url.path, e)
                return self._atbilde(500, {"kluda": "iekšēja kļūda"}, 0)
        self._atbilde(404, {"kluda": "nav šāda galapunkta"}, 0)

    def do_POST(self):
        cels = urlparse(self.path).path
        funkcija, m = next(((f, m) for r, f in POST_MARSRUTI if (m := r.match(cels))), (None, None))
        if funkcija is None:
            return self._atbilde(404, {"kluda": "nav šāda galapunkta"}, 0)
        # Klienta IP (tikai balsu limitam, glabā jaucējvērtību): aiz Caddy — pēdējais X-Forwarded-For (to pieliek Caddy pats)
        ip = self.client_address[0]
        if ip in ("127.0.0.1", "::1") and self.headers.get("X-Forwarded-For"):
            ip = self.headers["X-Forwarded-For"].split(",")[-1].strip() or ip
        _pieprasijums.ip = ip
        try:
            garums = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            garums = -1
        if not 0 <= garums <= 2000:
            return self._atbilde(413, {"kluda": "pārāk garš pieprasījums"}, 0)
        try:
            dati = json.loads(self.rfile.read(garums) or b"{}")
        except (ValueError, UnicodeDecodeError):
            dati = None  # nederīgs JSON: meklejumi to neskaita, zinojumi atbild 400
        try:
            rez = funkcija(dati, *m.groups())
            if isinstance(rez, tuple):  # (statuss, dati) — galapunkts atbild ar saturu (zinojumi)
                return self._atbilde(*rez, 0)
        except Kluda as e:
            return self._atbilde(e.statuss, {"kluda": str(e)}, 0)
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
        if self.command in ("GET", "HEAD"):  # atvērts API: GET no jebkuras vietnes (api.html); POST — tikai mūsu lapai
            self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(b)

    def _teksts(self, saturs, tips, kesot):
        b = saturs.encode()
        self.send_response(200)
        self.send_header("Content-Type", tips)
        self.send_header("Content-Length", str(len(b)))
        self.send_header("Cache-Control", f"public, max-age={kesot}")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(b)

    do_HEAD = do_GET

    def do_OPTIONS(self):
        """CORS preflight tikai GET maršrutiem (POST paliek same-origin)."""
        cels = urlparse(self.path).path
        if any(r.match(cels) for r, *_ in MARSRUTI):
            self.send_response(204)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, HEAD, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.send_header("Access-Control-Max-Age", "86400")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        self.send_response(204 if any(r.match(cels) for r, _ in POST_MARSRUTI) else 404)
        self.send_header("Content-Length", "0")
        self.end_headers()


def main():
    if not DSN:
        sys.exit("Nav MAP_DB_DSN")
    ports = int(sys.argv[1]) if len(sys.argv) > 1 else 8920
    threading.Thread(target=_statuss_cikls, name="statuss", daemon=True).start()
    threading.Thread(target=_zinojumi_shema, name="zinojumi", daemon=True).start()
    threading.Thread(target=_pludi_shema, name="pludi", daemon=True).start()
    Serveris(("127.0.0.1", ports), Apstradatajs).serve_forever()


class Serveris(ThreadingHTTPServer):
    request_queue_size = 128  # noklusēti 5: slodzē savienojumi tiek atteikti (Caddy 502)
    daemon_threads = True


if __name__ == "__main__":
    main()
