"""map.repo.lv API: lasa datubāzi `map` un atgriež JSON / GeoJSON. Caddy to pieslēdz zem /api/.

Galapunkti:
  GET /api/kategorijas                 slāņi ar objektu skaitu
  GET /api/regioni                     pašvaldības un pilsētas (bez ģeometrijas, ar bbox)
  GET /api/regioni/<kods>              reģiona robeža (GeoJSON Feature, vienkāršota)
  GET /api/objekti?kategorijas=a,b&regions=<kods>&lat=..&lon=..&limit=..
                                       punkti (GeoJSON); ar lat/lon sakārtoti pēc attāluma
  GET /api/veseliba                    pārbaude

Palaišana: MAP_DB_DSN=postgresql://map_api:...@127.0.0.1/map python3 karte_api.py [ports]
Tikai standarta bibliotēka + psycopg 3 (Ubuntu: python3-psycopg).
"""

import json
import os
import re
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

import psycopg

DSN = os.environ.get("MAP_DB_DSN", "")
MAX_LIMIT = 20000
KODS = re.compile(r"^[A-Za-z0-9_-]{1,40}$")


class Kluda(Exception):
    def __init__(self, statuss, teksts):
        super().__init__(teksts)
        self.statuss = statuss


def vaicat(sql, params=()):
    with psycopg.connect(DSN, connect_timeout=5) as conn, conn.cursor() as cur:
        cur.execute("set statement_timeout = '10s'")
        cur.execute(sql, params)
        rinda = cur.fetchone()
        return rinda[0] if rinda else None


def kategorijas(_q):
    return vaicat(
        """select coalesce(json_agg(k order by kartiba, nosaukums), '[]') from (
             select k.kods, k.nosaukums, k.grupa, k.krasa, k.kartiba, count(o.id)::int as skaits
             from kategorijas k left join objekti o on o.kategorija = k.kods
               and (o.derigs_lidz is null or o.derigs_lidz > now())
             group by k.kods) k"""
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


def veseliba(_q):
    return {"ok": vaicat("select true")}


MARSRUTI = [
    (re.compile(r"^/api/kategorijas/?$"), kategorijas, 300),
    (re.compile(r"^/api/regioni/?$"), regioni, 3600),
    (re.compile(r"^/api/regioni/([^/]+)$"), regions, 3600),
    (re.compile(r"^/api/objekti/?$"), objekti, 60),
    (re.compile(r"^/api/veseliba/?$"), veseliba, 0),
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
