"""Pašvaldību CA plānu pulcēšanās un izmitināšanas vietas → kartes slāņi ar atsauci uz plāna lappusi.

Ievade: src/karte/dati/ca_plani/<slug>.json — no plāna Markdown izvilktie ieraksti (AI + regex, skat.
notes/ca-plani-kvalitate.md). Katram ierakstam ir `citats`: burtiska rinda no plāna faila. Šis skripts:
  1. pārbauda, ka citāts tiešām ir failā (citādi ieraksts tiek izmests: neko neizdomājam),
     un no tuvākā iepriekšējā `<!-- lpp. N -->` marķiera nosaka lappusi;
  2. plāna koordinātas (WGS-84, LKS-92 vai DMS) pārbauda pret pašvaldības robežu (map.repo.lv/api/regioni);
  3. adreses ģeokodē ar VZD adrešu reģistru (kadastrs.db, v_adrese — avoti/kadastrs/atjaunot.py);
  4. apvieno dublikātus pašvaldības ietvaros (tā pati adrese vai < 30 m);
  5. raksta src/karte/dati/ca_pulcesanas_vietas.geojson, ca_izmitinasana.geojson un notes/ca-plani-kvalitate.md.

Palaišana (lokāli, tad PR):
  uv run --no-project --with shapely --with pyproj src/karte/db/ca_plani.py
"""

import argparse
import csv
import json
import math
import re
import sqlite3
import sys
import unicodedata
import urllib.request
from collections import defaultdict
from pathlib import Path

from pyproj import Transformer
from shapely.geometry import Point, shape
from shapely.ops import transform as shp_transform

SAKNE = Path(__file__).resolve().parents[3]
KIT = SAKNE / "ai-open-data-2026-hakatons" / "ca-plani-hakatons"
IZVILKUMS = SAKNE / "src" / "karte" / "dati" / "ca_plani"
API = "https://map.repo.lv/api/regioni/"
ROBEZAS_TOLERANCE_M = 300   # robežas ir vienkāršotas (~50 m); punkts pie pašas robežas nav kļūda
TALU_NO_ADRESES_M = 1000    # plāna koordinātas tālāk par šo no plāna adreses → karodziņš
DUBLIKATS_M = 30
# Aizstāti plāni, kas vēl ir mapē: to ieraksti dublē aktuālo plānu (lappuse jāņem no aktuālā)
AIZSTATI = {"baldonessadarbibasteritorijasplans.md"}  # Baldones 2021. g. plāns → Ķekavas novada plāns

UZ_LKS = Transformer.from_crs(4326, 3059, always_xy=True).transform
NO_LKS = Transformer.from_crs(3059, 4326, always_xy=True).transform

GENITIVS = {"Rīga": "Rīgas", "Daugavpils": "Daugavpils", "Jelgava": "Jelgavas", "Jūrmala": "Jūrmalas",
            "Liepāja": "Liepājas", "Rēzekne": "Rēzeknes", "Ventspils": "Ventspils"}


def norm(t):
    t = unicodedata.normalize("NFKD", t or "").encode("ascii", "ignore").decode().lower()
    t = re.sub(r"\bpagasts\b|\bpag\.?", "pag", t)
    t = re.sub(r"\bnovads\b|\bnov\.?", "nov", t)
    t = re.sub(r"\biela\b|\biela\.", "iela", t)
    return re.sub(r"[^a-z0-9]", "", t)


DATIVS = [(r"ielai\b", "iela"), (r"gatvei\b", "gatve"), (r"prospektam\b", "prospekts"), (r"bulvārim\b", "bulvāris"),
          (r"laukumam\b", "laukums"), (r"šosejai\b", "šoseja"), (r"\bielā\b", "iela"), (r"\bprosp\.\s*", "prospekts ")]
PRETI = re.compile(r"^.*?\bpret[īi]\s*", re.I)


def tirit(adrese):
    """Plāna adreses pieraksts → VZD stilam tuvāks: "Rīgas iela5. Vecumnieki" → "Rīgas iela 5, Vecumnieki";
    "Pretī Albatrosu ielai 19" → "Albatrosu iela 19" (otrs elements: vai adrese ir aptuvena)."""
    adrese = re.sub(r"[\"„“”«»'’]", "", adrese or "")
    adrese = re.sub(r"\bLV[- ]?\d{4}\b", "", adrese)
    aptuvena = False
    if PRETI.search(adrese.split(",")[0]):
        adrese, aptuvena = PRETI.sub("", adrese, count=1), True
    adrese = re.sub(r"(?<=[a-zāčēģīķļņšūž])(?=\d)", " ", adrese)          # iela5 → iela 5
    for no, uz in DATIVS:
        adrese = re.sub(no, uz, adrese)
    adrese = re.sub(r"(?<=[a-zāčēģīķļņšūž\d])(?=(iela|gatve|prospekts)\b)", " ", adrese)
    adrese = re.sub(r"\.\s+(?=[A-ZĀČĒĢĪĶĻŅŠŪŽ])", ", ", adrese)           # "2. Bauska" → "2, Bauska"
    return adrese, aptuvena


def komponentes(adrese):
    return [k for k in (norm(x) for x in re.split(r"[,;]", adrese or "")) if k]


# Iela + numurs komponentes sākumā, aiz kā vēl teksts ("dubultuprospekts105pieviesnicasliesma").
# Mājas burts ir neviennozīmīgs ("38aolaine" = "38a" + "olaine", "105pie…" = "105" + "pie…"), tāpēc mēģina abus.
IELA_NR = [re.compile(r"^(.*?(iela|gatve|prospekts|bulvaris|laukums|soseja|cels|aleja|krastmala|dambis|linija)\d+"
                      + burts + r"(k\d+)?)(.*)$") for burts in (r"[a-z]?", "")]


def vieta_sakrit(a, std_komp):
    """2 = plāna vietas daļa (pilsēta/ciems/pagasts) burtiski sakrīt ar kādu VZD adreses daļu, 1 = sakrīt
    locījumā ("Alojas pilsēta" ~ "Aloja", "Meņģelē" ~ "Meņģele"), 0 = nesakrīt. Pilsēta ≠ pagasts ("Balvi" ≠ "Balvu pag.")."""
    a = re.sub(r"(pilseta|ciems|ciemats)$", "", a)
    if a in std_komp:
        return 2
    for b in std_komp:
        if a.endswith("pag") != b.endswith("pag"):
            if len(b) >= 5 and not b.endswith("pag") and b in a:  # "sauleskalnsberzaunespag" ⊃ "sauleskalns"
                return 1
            continue
        isais, garais = sorted((a, b), key=len)
        if len(isais) >= 4 and garais.startswith(isais[:-1]) and len(garais) - len(isais) <= 2:
            return 1
    return 0


# ---------- pašvaldības un robežas ----------

def pasvaldibas():
    kodi = {}
    with open(KIT / "pasvaldibas.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            kodi[r["pasvaldiba"]] = r["adresu_registra_kods"]
    saraksts = json.loads((KIT / "darba_saraksts.json").read_text(encoding="utf-8"))
    rez = {}
    for p in saraksts:
        if p["pasvaldiba"] in kodi:
            rez[p["slug"]] = {"nosaukums": p["pasvaldiba"], "kods": kodi[p["pasvaldiba"]],
                              "kopigs": [s for s in (p.get("iespejams_kopigs_ar") or "").split(",") if s.strip()]}
    # kopīgie plāni darbojas abos virzienos
    for slug, p in rez.items():
        for cits in p["kopigs"]:
            if cits in rez and slug not in rez[cits]["kopigs"]:
                rez[cits]["kopigs"].append(slug)
    return rez


def robeza(kods, kese):
    fails = kese / f"{kods}.json"
    if not fails.exists():
        with urllib.request.urlopen(API + kods, timeout=60) as r:
            fails.write_bytes(r.read())
    gj = json.loads(fails.read_text(encoding="utf-8"))
    return shp_transform(UZ_LKS, shape(gj["geometry"]))


def genitivs(nosaukums):
    if nosaukums.endswith(" novads"):
        return nosaukums[:-1] + "a"
    return GENITIVS.get(nosaukums, nosaukums)


# ---------- plāna faili ----------

class Plans:
    def __init__(self, slug):
        self.dir = KIT / "markdown" / slug
        self.kese = {}

    def fails(self, nosaukums):
        if nosaukums not in self.kese:
            teksts = (self.dir / nosaukums).read_text(encoding="utf-8")
            fm = {}
            m = re.match(r"---\n(.*?)\n---\n", teksts, re.S)
            if m:
                for rinda in m.group(1).splitlines():
                    if ":" in rinda and not rinda.startswith(" "):
                        k, v = rinda.split(":", 1)
                        fm[k.strip()] = v.strip()
            lpp = [(m.start(), int(m.group(1))) for m in re.finditer(r"<!-- lpp\. (\d+) -->", teksts)]
            self.kese[nosaukums] = (teksts, fm, lpp)
        return self.kese[nosaukums]

    def atrast(self, nosaukums, citats):
        """(lpp, avota_url) vai None, ja citāta failā nav."""
        if not citats or not (self.dir / nosaukums).exists():
            return None
        teksts, fm, lpp = self.fails(nosaukums)
        poz = teksts.find(citats)
        if poz < 0:
            sakums = " ".join(citats.split())
            plakans = " ".join(teksts.split())
            if sakums not in plakans:
                return None
            # aptuvena pozīcija pēc pirmajiem 20 burtiem
            poz = teksts.find(citats.strip()[:20])
        lappuse = None
        for p, n in lpp:
            if p <= poz:
                lappuse = n
            else:
                break
        return lappuse, fm.get("avota_url")


# ---------- VZD adrešu reģistrs ----------

class Adreses:
    def __init__(self, db):
        self.pec_pirmas = defaultdict(list)
        con = sqlite3.connect(db)
        for kods, std, lat, lon in con.execute("select kods, adrese, lat, lon from v_adrese where lat is not null"):
            komp = komponentes(std)
            if komp:
                self.pec_pirmas[komp[0]].append((kods, std, lat, lon, set(komp[1:])))

    def meklet(self, adrese, robezas):
        """(kods, std, lat, lon, karodziņš|None) vai (None, iemesls).
        Atslēga: pirmā adreses daļa (iela + nr vai mājas nosaukums), citādi pirmā daļa ar ielu un numuru.
        Ja plānā ir vieta (pilsēta/ciems/pagasts), vismaz vienai jāsakrīt ar VZD adresi."""
        teksts, aptuvena = tirit(adrese)
        komp = komponentes(teksts)
        if not komp:
            return None, "address_missing"
        meginajumi = [(komp[0], komp[1:])]
        m = re.fullmatch(r"([a-z]+?)(\d+[a-z]?(k\d+)?)", komp[0])
        if m and not re.search(r"(iela|gatve|prospekts|bulvaris|laukums|soseja|cels|aleja|dambis|linija)$", m.group(1)):
            meginajumi.append((f"{m.group(1)}iela{m.group(2)}", komp[1:]))  # "Raiņa 15" → "Raiņa iela 15"
        for i, k in enumerate(komp):
            for rx in IELA_NR:
                m = rx.match(k)
                if m and (i > 0 or m.group(4)) and len(m.group(4)) != 1:  # "2a" nav "2" + "a"
                    meginajumi.append((m.group(1), ([m.group(4)] if m.group(4) else []) + komp[:i] + komp[i + 1:]))
        for atslega, citas in meginajumi:
            vietas = [c for c in citas if not c.endswith("nov") and not re.fullmatch(r"\d+", c)]
            atrasti, labakais = [], 1
            for kods, std, lat, lon, std_komp in self.pec_pirmas.get(atslega, ()):
                rez = sum(vieta_sakrit(v, std_komp) for v in vietas) if vietas else 1
                if rez < labakais:
                    continue
                p = Point(UZ_LKS(lon, lat))
                if any(r.distance(p) <= ROBEZAS_TOLERANCE_M for r in robezas):
                    if rez > labakais:
                        atrasti, labakais = [], rez
                    atrasti.append((kods, std, lat, lon))
            if not atrasti:
                continue
            p0 = UZ_LKS(atrasti[0][3], atrasti[0][2])
            if max(math.dist(p0, UZ_LKS(l[3], l[2])) for l in atrasti) > 300:
                return None, "address_ambiguous"
            kods, std, lat, lon = atrasti[0]
            return (kods, std, lat, lon, "address_approximate" if aptuvena else None), None
        return None, "address_not_found"


# ---------- koordinātas ----------

def dms(teksts):
    vals = re.findall(r"(\d+)[°º]\s*(\d+)['′’]\s*([\d.,]+)?", teksts or "")
    if len(vals) < 2:
        return None
    d = [int(a) + int(b) / 60 + float((c or "0").replace(",", ".")) / 3600 for a, b, c in vals[:2]]
    lat, lon = (d[0], d[1]) if d[0] > d[1] else (d[1], d[0])
    return lat, lon


def plana_koord(r):
    """(lat, lon) WGS-84 kā plānā ierakstīts, vai None."""
    sist = r.get("koord_sistema")
    if sist == "dms":
        return dms(r.get("koord_teksts"))
    lat, lon = r.get("lat"), r.get("lon")
    if lat is None or lon is None:
        return None
    lat, lon = float(lat), float(lon)
    if sist == "lks92" or (lat > 1000 and lon > 1000):
        x, y = (lon, lat) if lon > lat else (lat, lon)  # LKS-92: x (austrumi) 300000–770000, y 160000–450000
        lon, lat = NO_LKS(x, y)
    return lat, lon


# ---------- galvenais ----------

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--kadastrs", default=str(KIT / "avoti" / "kadastrs" / "dati" / "kadastrs.db"))
    ap.add_argument("--robezas", default=str(Path.home() / ".cache" / "hakatons-regioni"),
                    help="kešs map.repo.lv/api/regioni/<kods> failiem")
    args = ap.parse_args()
    kese = Path(args.robezas)
    kese.mkdir(parents=True, exist_ok=True)

    pasv = pasvaldibas()
    print("Ielādēju VZD adreses…", file=sys.stderr)
    adreses = Adreses(args.kadastrs)

    slani = {"evakuacijas_punkti": [], "izmitinasana": []}
    parskats = []
    ar_ierakstiem = set()
    for fails in IZVILKUMS.glob("*.json"):
        izv = json.loads(fails.read_text(encoding="utf-8"))
        if izv.get("evakuacijas_punkti") or izv.get("izmitinasana"):
            ar_ierakstiem.add(izv["slug"])
    for fails in sorted(IZVILKUMS.glob("*.json")):
        izv = json.loads(fails.read_text(encoding="utf-8"))
        slug = izv["slug"]
        p = pasv[slug]
        partneri = [s for s in p["kopigs"] if s in pasv]
        robezas = [robeza(p["kods"], kese)] + [robeza(pasv[s]["kods"], kese) for s in partneri]
        plans = Plans(slug)
        stat = {"slug": slug, "pasvaldiba": p["nosaukums"], "statuss": izv["statuss"], "piezime": izv.get("piezime"),
                "atsauces": izv.get("atsauces", []), "kludas": [], "neatrasti": [], "izmesti": []}
        for slanis, ieraksti in slani.items():
            s = stat[slanis] = {"atrasti": 0, "ar_koord": 0, "geokodeti": 0, "kartē": 0, "vietas": 0, "dublikati": 0}
            punkti = []
            for r in izv.get(slanis, []):
                if r.get("fails") in AIZSTATI:
                    continue
                s["atrasti"] += 1
                vieta = plans.atrast(r.get("fails", ""), r.get("citats", ""))
                if not vieta:
                    stat["izmesti"].append(f"{r.get('nosaukums')} — citāts nav atrasts failā {r.get('fails')}")
                    continue
                lpp, url = vieta
                karodzini = []
                kludu_sk = len(stat["kludas"])
                koord, metode = None, None
                pk = plana_koord(r)
                if pk:
                    s["ar_koord"] += 1
                pg = None
                if r.get("adrese"):
                    g, iemesls = adreses.meklet(r["adrese"], robezas)
                    if g:
                        pg = g
                        if g[4]:
                            karodzini.append(g[4])
                    elif not pk:
                        karodzini.append(iemesls)
                if pk:
                    lat, lon = pk
                    pt = Point(UZ_LKS(lon, lat))
                    att = min(rb.distance(pt) for rb in robezas)
                    if att <= ROBEZAS_TOLERANCE_M:
                        koord, metode = (lat, lon), "plan_coords"
                    else:
                        apm = Point(UZ_LKS(lat, lon))
                        if min(rb.distance(apm) for rb in robezas) <= ROBEZAS_TOLERANCE_M:
                            karodzini.append("plan_coords_swapped")
                            koord, metode = (lon, lat), "plan_coords_swapped"
                        else:
                            karodzini.append("plan_coordinate_error")
                            stat["kludas"].append({"nosaukums": r.get("nosaukums"), "nr": r.get("nr"), "lpp": lpp,
                                                   "fails": r.get("fails"), "citats": r.get("citats"),
                                                   "koord_teksts": r.get("koord_teksts"),
                                                   "attalums_km": round(att / 1000, 1) if math.isfinite(att) else None,
                                                   "aizstats_ar_adresi": bool(pg)})
                    if koord and pg:
                        d = math.dist(UZ_LKS(koord[1], koord[0]), UZ_LKS(pg[3], pg[2]))
                        if d > TALU_NO_ADRESES_M:
                            karodzini.append("plan_coords_far_from_address")
                            stat["kludas"].append({"nosaukums": r.get("nosaukums"), "nr": r.get("nr"), "lpp": lpp,
                                                   "fails": r.get("fails"), "citats": r.get("citats"),
                                                   "koord_teksts": r.get("koord_teksts"),
                                                   "attalums_km": round(d / 1000, 1), "tips": "far_from_address",
                                                   "adrese_vzd": pg[1]})
                            koord = None  # adrešu reģistrs ir autoritatīvs adresei; plāna koordinātas paliek īpašībās
                if not koord and pg:
                    koord, metode = (pg[2], pg[3]), "varis_address"
                    s["geokodeti"] += 1
                for k in stat["kludas"][kludu_sk:]:
                    k["rezultats"] = metode or "not_on_map"
                    k["adrese_vzd"] = k.get("adrese_vzd") or (pg[1] if pg else None)
                    k["parbaudes_piezime"] = r.get("parbaudes_piezime")  # cilvēka pārbaude pret oriģinālo PDF
                    k["slanis"] = slanis
                if not koord:
                    stat["neatrasti"].append(f"{r.get('nosaukums')}, {r.get('adrese') or '(bez adreses)'} (lpp. {lpp}): "
                                             + ", ".join(karodzini or ["no_location"]))
                    continue
                # kopīgais plāns (piem. Daugavpils + Augšdaugavas novads): partnera teritorijas punktus
                # ieskaita partnera izvilkumā, ja tāds ir — citādi tie būtu kartē divreiz
                xy = Point(UZ_LKS(koord[1], koord[0]))
                if robezas[0].distance(xy) > ROBEZAS_TOLERANCE_M:
                    cits = next((ps for ps, rb in zip(partneri, robezas[1:])
                                 if ps in ar_ierakstiem and rb.distance(xy) <= ROBEZAS_TOLERANCE_M), None)
                    if cits:
                        s["atrasti"] -= 1
                        s["ar_koord"] -= bool(pk)
                        s["geokodeti"] -= metode == "varis_address"
                        stat["kludas"] = stat["kludas"][:kludu_sk]
                        continue
                props = {
                    "kategorija": "evakuacijas_punkts" if slanis == "evakuacijas_punkti" else "izmitinasana",
                    "nosaukums": r.get("nosaukums"),
                    "adrese": r.get("adrese"),
                    "pasvaldiba": p["nosaukums"],
                    "pasvaldiba_slug": slug,
                    "nr_plana": r.get("nr"),
                    "avots_teksts": f"Avots: {genitivs(p['nosaukums'])} CA plāns, lpp. {lpp}" if lpp else
                                    f"Avots: {genitivs(p['nosaukums'])} CA plāns",
                    "plans_url": url,
                    "plans_fails": r.get("fails"),
                    "lpp": lpp,
                    "citats": r.get("citats"),
                    "izdevejs": f"{p['nosaukums']} (pašvaldība)",
                    "geokodesana": metode,
                    "adrese_vzd": pg[1] if pg else None,
                    "vzd_kods": pg[0] if pg else None,
                    "plana_lat": pk[0] if pk else None,
                    "plana_lon": pk[1] if pk else None,
                    "koord_teksts": r.get("koord_teksts"),
                    "karodzini": karodzini,
                }
                if slanis == "izmitinasana" or r.get("vietas"):
                    props.update(vietas=r.get("vietas"), gultas=r.get("gultas"), edinasana=r.get("edinasana"))
                if r.get("piezime"):
                    props["izvilkuma_piezime"] = r["piezime"]
                # komentars: production/app.js to rāda punkta logā (saite: plans_url)
                kom = [props["avots_teksts"]]
                if props.get("vietas"):
                    kom.append(f"{props['vietas']} vietas")
                if "plan_coordinate_error" in karodzini or "plan_coords_far_from_address" in karodzini:
                    kom.append("plāna koordinātas kļūdainas, vieta noteikta pēc adreses (VZD)")
                elif metode == "varis_address":
                    kom.append("vieta noteikta pēc adreses (VZD)")
                props["komentars"] = " · ".join(kom)
                punkti.append((props, koord))

            # dublikāti: tā pati adrese vai < 30 m
            palikusie = []
            for props, koord in punkti:
                xy = UZ_LKS(koord[1], koord[0])
                dub = None
                for q, qk, qxy in palikusie:
                    if (props["adrese"] and q["adrese"] and norm(props["adrese"]) == norm(q["adrese"])) \
                            or math.dist(xy, qxy) < DUBLIKATS_M:
                        dub = q
                        break
                if dub:
                    dub.setdefault("dublikati", []).append(f"{props['nosaukums']} (nr. {props['nr_plana']}, lpp. {props['lpp']})")
                    s["dublikati"] += 1
                    continue
                palikusie.append((props, koord, xy))
            for i, (props, koord, _) in enumerate(palikusie):
                props["id"] = f"{slug}-{'evak' if slanis == 'evakuacijas_punkti' else 'izm'}-{i + 1}"
                s["kartē"] += 1
                s["vietas"] += int(props.get("vietas") or 0)
                ieraksti.append({"type": "Feature", "properties": props,
                                 "geometry": {"type": "Point", "coordinates": [round(koord[1], 6), round(koord[0], 6)]}})
        parskats.append(stat)

    dati = SAKNE / "src" / "karte" / "dati"
    for slanis, fname, nos in (("evakuacijas_punkti", "ca_pulcesanas_vietas.geojson", "Pulcēšanās (evakuācijas) vietas"),
                               ("izmitinasana", "ca_izmitinasana.geojson", "Pagaidu izmitināšanas vietas")):
        gj = {"type": "FeatureCollection", "nosaukums": nos,
              "avots": "Pašvaldību civilās aizsardzības plāni (ai-open-data-2026-hakatons/ca-plani-hakatons/markdown); "
                       "izvilkts ar src/karte/db/ca_plani.py", "features": slani[slanis]}
        (dati / fname).write_text(json.dumps(gj, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
        print(f"{fname}: {len(slani[slanis])} punkti", file=sys.stderr)
    (dati / "ca_plani_parskats.json").write_text(json.dumps(parskats, ensure_ascii=False, indent=1) + "\n",
                                                 encoding="utf-8", newline="\n")
    (SAKNE / "notes" / "ca-plani-kvalitate.md").write_text(parskats_md(parskats), encoding="utf-8", newline="\n")


REZULTATS = {"varis_address": "placed by VZD address", "plan_coords_swapped": "placed with lat/lon swapped",
             "not_on_map": "**not on map**", "plan_coords": "kept plan coordinates"}


def parskats_md(parskats):
    sum_ = lambda sl, k: sum(s[sl][k] for s in parskats)
    ar_sarakstu = [s for s in parskats if s["evakuacijas_punkti"]["atrasti"] or s["izmitinasana"]["atrasti"]]
    nav = [s for s in parskats if s not in ar_sarakstu]
    kludas = [dict(k, pasvaldiba=s["pasvaldiba"]) for s in parskats for k in s["kludas"]]
    arpus = [k for k in kludas if k.get("tips") != "far_from_address"]
    r = ["# CA plans → map: what the municipal civil protection plans publish", "",
         "_Generated by `src/karte/db/ca_plani.py` — do not edit by hand; re-run the script._", "",
         "## Totals", "",
         "| | Assembly points (`evakuacijas_punkts`) | Temporary accommodation (`izmitinasana`) |",
         "|---|---:|---:|"]
    for nos, k in (("Rows extracted from plans", "atrasti"), ("…with coordinates in the plan", "ar_koord"),
                   ("…placed by VZD address register", "geokodeti"), ("Merged duplicates", "dublikati"),
                   ("**On the map**", "kartē"), ("Places (capacity) on the map", "vietas")):
        r.append(f"| {nos} | {sum_('evakuacijas_punkti', k)} | {sum_('izmitinasana', k)} |")
    r += ["",
          f"- Plan folders scanned: **{len(parskats)}** (42 municipalities; Ventspils county shares Ventspils' folder).",
          f"- Municipalities with at least one list published in the plan: **{len(ar_sarakstu)}**; "
          f"without: **{len(nav)}** (see below).",
          f"- Coordinate errors found in official plans: **{len(arpus)}** points outside their municipality, "
          f"**{len(kludas) - len(arpus)}** more than {TALU_NO_ADRESES_M / 1000:g} km from the plan's own address.",
          "",
          "## Method", "",
          "1. AI agents read every plan (Markdown conversion with `<!-- lpp. N -->` page markers) and extracted each "
          "assembly point / accommodation site into `src/karte/dati/ca_plani/<slug>.json` with a verbatim quote "
          "(`citats`) of the source line. Nothing is inferred: if a plan points to an annex that is not published, "
          "the municipality is recorded as \"not published\" with the quote.",
          "2. `ca_plani.py` checks every quote against the plan text (a record whose quote is not in the file is dropped), "
          "and derives the page from the nearest preceding page marker → popup \"Avots: <municipality> CA plāns, lpp. N\".",
          f"3. Plan coordinates (WGS-84, LKS-92 or DMS) are checked against the municipality boundary "
          f"(VZD, map.repo.lv/api/regioni, {ROBEZAS_TOLERANCE_M} m tolerance) and against the plan's own address "
          "geocoded in the VZD address register (CC BY 4.0).",
          "4. Address-only rows are geocoded with the VZD address register; street + number or house name must match "
          "and, if the plan names a town/village/parish, it must match too. Ambiguous or unmatched addresses are left off "
          "the map (listed below), never guessed.",
          f"5. Duplicates within a municipality (same address or < {DUBLIKATS_M} m) are merged; the merged rows are kept "
          "in the `dublikati` property.", "",
          "## Coordinate errors in official plans", "",
          "| Municipality | Place (plan row) | Page | Plan value | Problem | On the map |", "|---|---|---:|---|---|---|"]
    for k in sorted(kludas, key=lambda k: (k["pasvaldiba"], k.get("tips") == "far_from_address", k["lpp"] or 0)):
        if k.get("tips") == "far_from_address":
            problema = f"{k['attalums_km']} km from its own address ({k['adrese_vzd']})"
        elif k["attalums_km"] is None:
            problema = "not a valid coordinate"
        else:
            problema = f"outside the municipality ({k['attalums_km']} km away)"
        if k.get("parbaudes_piezime"):
            problema += f"; {k['parbaudes_piezime']}"
        if k.get("rezultats") == "varis_address" and k.get("tips") != "far_from_address":
            problema += f" — VZD: {k['adrese_vzd']}"
        vert = (k.get("koord_teksts") or "").replace("|", " / ").replace("<br>", " ")
        r.append(f"| {k['pasvaldiba']} | {k['nosaukums']} (nr. {k.get('nr') or '–'}) | {k['lpp'] or '–'} | `{vert}` | "
                 f"{problema} | {REZULTATS.get(k.get('rezultats'), k.get('rezultats'))} |")
    r += ["", "## Per municipality", "",
          "| Municipality | Status | Assembly: found → map | Accommodation: found → map | Plan coords | VZD geocoded | Coord. errors | Places |",
          "|---|---|---:|---:|---:|---:|---:|---:|"]
    for s in sorted(parskats, key=lambda s: s["pasvaldiba"]):
        e, i = s["evakuacijas_punkti"], s["izmitinasana"]
        r.append(f"| {s['pasvaldiba']} | {s['statuss']} | {e['atrasti']} → {e['kartē']} | {i['atrasti']} → {i['kartē']} | "
                 f"{e['ar_koord'] + i['ar_koord']} | {e['geokodeti'] + i['geokodeti']} | {len(s['kludas'])} | {i['vietas'] or ''} |")
    r += ["", "Status: `publicets` both lists published; `dalejs` only one list or partial; `nav_publicets` lists not in the "
          "published plan; `kopigs_plans` covered by another municipality's plan.", "",
          "## Lists not published", ""]
    for s in sorted(nav + [s for s in ar_sarakstu if s["statuss"] == "dalejs"], key=lambda s: s["pasvaldiba"]):
        r.append(f"- **{s['pasvaldiba']}** (`{s['statuss']}`): {s.get('piezime') or ''}")
        for a in s.get("atsauces", [])[:2]:
            r.append(f"  - {a['fails']}: „{a['citats'].strip()[:200]}”")
    r += ["", "## Rows not placed on the map", ""]
    for s in sorted(parskats, key=lambda s: s["pasvaldiba"]):
        if s["neatrasti"] or s["izmesti"]:
            r.append(f"- **{s['pasvaldiba']}**")
            r += [f"  - {n}" for n in s["neatrasti"]]
            r += [f"  - dropped: {n}" for n in s["izmesti"]]
    return "\n".join(r) + "\n"


if __name__ == "__main__":
    main()
