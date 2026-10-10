"""/api/statuss un /api/veseliba jaunās sadaļas: ārējo avotu žurnāls, plūdu flīžu skaitītāji (diskā), ziņojumi, slāņi
pret repozitoriju. Bez datubāzes un bez tīkla (vaicat un avoti aizstāti ar viltotiem).

  uv run --no-project --python 3.12 --with "psycopg[binary]" src/testi/statuss_testi.py
  ... statuss_testi.py --serveris 8931   # pēc testiem atstāj API ar viltotiem datiem (statuss.html pārbaudei)
"""

import json
import os
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
DATI = tempfile.mkdtemp(prefix="statuss-testi-")
os.environ["HAKATONS_DATI"] = DATI
os.environ.setdefault("MAP_DB_DSN", "postgresql://viltots/x")
os.environ["MAP_DB_OWNER_DSN"] = ""
os.environ["METEOALARM_ATOM"] = "http://127.0.0.1:9/meteoalarm"  # /api/veseliba to atjauno fonā: bez tīkla
for m in [k for k in os.environ if k.startswith("NAP_API_KEY_")]:
    del os.environ[m]
os.environ["NAP_API_KEY_SLEGUMI"] = "viltota"
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "karte", "api"))
import karte_api as k  # noqa: E402

kludas = 0


def parbaude(nos, nosacijums, detalas=""):
    global kludas
    print(("ok    " if nosacijums else "KĻŪDA ") + nos + (f"  ({detalas})" if detalas and not nosacijums else ""))
    kludas += 0 if nosacijums else 1


# ---------- Viltota datubāze ----------
DB_IESLEGTA = [True]


def vaicat(sql, params=(), timeout="10s"):
    if not DB_IESLEGTA[0]:
        raise k.psycopg.OperationalError("nav datubāzes")
    if sql.strip() == "select true":
        return True
    if "from objekti where avots = any" in sql:
        return {"ca-plani/evakuacijas_punkts": 730, "ca-plani/izmitinasana": 579, "vugd-112/patvertne": 770,
                "vm-24h/neatliekama_24h": 37}
    if "from zinojumi" in sql:
        return {"kopa": 12, "redzami_7d": 9, "pedejais": "2026-10-10T19:00:00+00:00"}
    if "from zinojumu_balsis" in sql:
        raise k.psycopg.errors.UndefinedTable("nav tabulas")  # → balsis no atmiņas
    if "statuss_parbaudes" in sql:
        return []
    raise AssertionError("neparedzēts SQL: " + sql[:80])


k.vaicat = vaicat

# ---------- 1. Ārējo avotu žurnāls caur _kesots ----------
k._kesots("bridinajumi", 600, lambda: [])
parbaude("veiksme pierakstīta (bridinajumi)", "ok" in k._avotu_zurnals.get("bridinajumi", {}))
parbaude("derīguma laiks pierakstīts", k._avotu_zurnals["bridinajumi"].get("derigs_s") == 600)


def kluda_http():
    raise urllib.error.HTTPError("https://x", 503, "Service Unavailable", {}, None)


try:
    k._kesots("zibens_fmi", 60, kluda_http)
except k.Kluda:
    pass
z = k._avotu_zurnals.get("zibens_fmi", {})
parbaude("kļūda bez kešas: pierakstīta, Kluda 503 kā līdz šim", z.get("kluda_teksts") == "HTTP 503" and "ok" not in z, z)

# novecojis kešs: vērtība ir, atjaunošana neizdodas → "traucejumi" + rezerve "novecojis kešs"
k._kesots("udens", 900, lambda: [1])
with k._kesas_slots:
    k._kesa["udens"] = (time.time() - 2000, [1])


def kluda_taimauts():
    raise TimeoutError("lēni")


parbaude("novecojis kešs: atdod veco vērtību", k._kesots("udens", 900, kluda_taimauts) == [1])
for _ in range(50):  # fona pavediens
    if "kluda" in k._avotu_zurnals.get("udens", {}):
        break
    time.sleep(0.05)
k._kesots(("nap", "NAP_API_KEY_SLEGUMI"), 300, lambda: {"ieraksti": []})
k._kesots(("augsne", 56.8, 24.6), 3600, lambda: {"augsne": "mitra"})

rindas = {r["kods"]: r for r in k._arejie_avoti()}
parbaude("katram AREJIE_AVOTI ir rinda", all(a[0] in rindas for a in k.AREJIE_AVOTI))
parbaude("LVĢMC brīdinājumi: darbojas", rindas["lvgmc_bridinajumi"]["stavoklis"] == "darbojas", rindas["lvgmc_bridinajumi"])
parbaude("FMI: nedarbojas, kļūda HTTP 503", rindas["fmi_zibens"]["stavoklis"] == "nedarbojas"
         and rindas["fmi_zibens"]["kluda"] == "HTTP 503", rindas["fmi_zibens"])
u = rindas["lvgmc_hidro"]
parbaude("ūdens: traucējumi, rezerve novecojis kešs, taimauts", u["stavoklis"] == "traucejumi"
         and u["rezerve"] == "novecojis kešs" and u["kluda"] == "neatbildēja laikā", u)
parbaude("Open-Meteo (atslēga ar koordinātām) → open_meteo darbojas", rindas["open_meteo"]["stavoklis"] == "darbojas")
parbaude("NAP slēgumi: konfigurēts, darbojas", rindas["nap_slegumi"]["stavoklis"] == "darbojas", rindas.get("nap_slegumi"))
parbaude("NAP bez atslēgas: nav_datu, nav konfigurēts", rindas["nap_robezas_laiks"]["stavoklis"] == "nav_datu"
         and "konfigurēts" in rindas["nap_robezas_laiks"]["zinojums"])
parbaude("NAP: katrs vides mainīgais vienreiz", len([r for r in rindas if r.startswith("nap_")])
         == len({m for m, *_ in k.NAP_KOPAS} | {m for _k, m, *_ in k.SATIKSME_KOPAS}))
parbaude("nepieprasīts avots: nav_datu", rindas["lvgmc_zibens"]["stavoklis"] == "nav_datu")
parbaude("OSM: rinda ir (vēl nav pārbaudīts)", rindas["osm"]["stavoklis"] == "nav_datu")
k._lvgmc_stavoklis["rezerves"] = time.time()
r = {r["kods"]: r for r in k._arejie_avoti()}["lvgmc_bridinajumi"]
parbaude("Meteoalarm rezerve aktīva → traucējumi, rezerve Meteoalarm", r["stavoklis"] == "traucejumi" and r["rezerve"] == "Meteoalarm", r)
k._lvgmc_stavoklis["rezerves"] = 0
parbaude("žurnāla kļūda nesabojā _kesots", k._kesots("x", 60, lambda: 5) == 5)
k._avota_kods, vecais = (lambda a: 1 / 0), k._avota_kods
parbaude("_avots_atzimet nekad neizmet kļūdu", k._kesots("y", 60, lambda: 6) == 6)
k._avota_kods = vecais

# ---------- 2. Plūdu flīžu skaitītāji ----------
mape = k._flizu_mape()
fails = os.path.join(mape, k.FLIZU_SKAITITAJI)
with open(fails, "w", encoding="utf-8") as f:
    f.write("{bojāts")
k._flizu_skaitit("kesa")
parbaude("bojāts skaitītāju fails → no nulles, bez kļūdas", k._flizu_kopa["skaits"] == {"kesa": 1}, k._flizu_kopa)
parbaude("pirmā skaitīšana ieraksta failu (atomiski, derīgs JSON)",
         json.load(open(fails, encoding="utf-8"))["skaits"] == {"kesa": 1})
for v in ["kesa"] * 7 + ["jauna", "jauna", "tukss"]:
    k._flizu_skaitit(v)
parbaude("fails netiek rakstīts biežāk par 1× minūtē", json.load(open(fails, encoding="utf-8"))["skaits"] == {"kesa": 1})
s = k._flizu_kopsavilkums()
parbaude("trāpījumi: 8 / (8 + 2) = 80 %, tukss neskaitās", s["trapijumi_proc"] == 80.0, s)
# restarts: ielādē no faila un turpina
with open(fails, "w", encoding="utf-8") as f:
    json.dump({"skaits": {"kesa": 100, "jauna": 25, "x": -3}, "kops": "2026-10-01T00:00:00+00:00"}, f)
k._flizu_kopa.update(skaits={}, kops=None, ieladets=False, saglabats=0.0)
k._flizu_skaitit("kesa")
parbaude("pēc restarta: skaitītāji no faila + jaunie, negatīvie izmesti",
         k._flizu_kopa["skaits"] == {"kesa": 101, "jauna": 25} and k._flizu_kopa["kops"].startswith("2026-10-01"), k._flizu_kopa)
os.remove(fails)
k._flizu_kopa.update(skaits={}, kops=None, ieladets=False, saglabats=0.0)
k._flizu_skaitit("veca")
parbaude("trūkstošs fails → no nulles", k._flizu_kopa["skaits"] == {"veca": 1})
# diska skenēšana: 3 flīzes, vecākā zināma; skaitītāju fails neskaitās
for i, vec in enumerate((10, 3600, 86400)):
    c = os.path.join(mape, "pali", "12", "1", f"{i}.png")
    os.makedirs(os.path.dirname(c), exist_ok=True)
    with open(c, "wb") as f:
        f.write(b"x" * 100)
    os.utime(c, (time.time() - vec, time.time() - vec))
k._flizu_tirit(mape)
s = k._flizu_kopsavilkums()
parbaude("disks: 3 flīzes, 300 B, vecākā pirms ~1 dienas", s["flizes"] == 3 and s["baiti"] == 300
         and abs(time.time() - k._flizu_disks["vecaka"] - 86400) < 5, s)

# ---------- 3. Ziņojumi ----------
k._zinojumi_logi["jauni"][:] = [time.time(), k.ZINOJUMI_MINUTE]
try:
    k.zinojumi_pievienot({"tips": "koks", "apraksts": "", "lat": 56.8, "lon": 24.6})
except k.Kluda as e:
    parbaude("429 jauniem ziņojumiem", e.statuss == 429)
k._balsis_atmina[("z", 5)] = [time.time() - 10, time.time() - 7200]
z = k._zinojumu_kopsavilkums()
parbaude("ziņojumi: kopā 12, balsis stundā 1 (no atmiņas), limits 1", z["kopa"] == 12 and z["balsis_1h"] == 1
         and z["balsis_avots"] == "atmiņa" and z["limiti"]["jauni_minute"] == 1, z)

# ---------- 4. Slāņi pret repozitoriju ----------
sl = {r["kategorija"]: r for r in k._slanu_salidzinajums()}
e = sl["evakuacijas_punkts"]
parbaude("pulcēšanās vietas: 730 kartē pret repozitorija skaitu, ielādējams", e["karte"] == 730 and e["repo"] and e["repo"] > 730
         and e["ieladejams"], e)
parbaude("izmitināšana sakrīt → nav ielādējams", sl["izmitinasana"]["karte"] == sl["izmitinasana"]["repo"]
         and not sl["izmitinasana"]["ieladejams"], sl["izmitinasana"])
parbaude("patvertnes: mazāk (dublikāti apvienoti) → nav ielādējams", not sl["patvertne"]["ieladejams"], sl["patvertne"])
parbaude("bankomāti: kartē 0 → ielādējams", sl["bankomats"]["karte"] == 0 and sl["bankomats"]["ieladejams"])
t0 = time.perf_counter()
k._slanu_salidzinajums()
parbaude("repozitorija skaiti kešoti (otrreiz < 50 ms)", time.perf_counter() - t0 < 0.05)

# ---------- 5. HTTP: /api/statuss un /api/veseliba ----------
k._statuss_atmina.append(("osm", k.datetime.now(k.timezone.utc), "darbojas", None, 120))
for i in range(96):
    k._statuss_atmina.append(("api", k.datetime.now(k.timezone.utc) - k.timedelta(minutes=15 * i), "darbojas", "ok", 50))
serveris = k.Serveris(("127.0.0.1", 0), k.Apstradatajs)
ports = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[1] == "--serveris" else None
threading.Thread(target=serveris.serve_forever, daemon=True).start()
adrese = f"http://127.0.0.1:{serveris.server_address[1]}"


def iegut(cels):
    with urllib.request.urlopen(adrese + cels, timeout=10) as r:
        return r.status, json.loads(r.read())


st, d = iegut("/api/statuss")
parbaude("/api/statuss 200 ar vecajiem laukiem", st == 200 and {"laiks", "intervals_min", "komponenti"} <= set(d))
parbaude("/api/statuss jaunās sadaļas", {"arejie_avoti", "flizes", "zinojumi", "slani", "api_starts"} <= set(d), list(d))
parbaude("/api/statuss sadaļās nav kļūdu", all(not (isinstance(d[x], dict) and "kluda" in d[x])
                                              for x in ("arejie_avoti", "flizes", "zinojumi", "slani")))
st, v = iegut("/api/veseliba")
parbaude("/api/veseliba: ok + bridinajumi (kā līdz šim) + arejie_avoti + flizes",
         st == 200 and v["ok"] is True and "bridinajumi" in v and v["arejie_avoti"]["osm"] == "darbojas" and "trapijumi_proc" in v["flizes"], v)
# DB nav: statuss joprojām 200, slāņi → kluda, pārējās sadaļas strādā
DB_IESLEGTA[0] = False
k._kesa.pop("statuss", None)
st, d = iegut("/api/statuss")
parbaude("bez DB: /api/statuss 200, slāņi {kluda}, ziņojumi pieejams=false, avoti strādā",
         st == 200 and "kluda" in d["slani"] and d["zinojumi"]["pieejams"] is False and isinstance(d["arejie_avoti"], list), d.get("slani"))
DB_IESLEGTA[0] = True
# sadaļas funkcija izmet kļūdu → tikai tā sadaļa ir {kluda}
k._kesa.pop("statuss", None)
vecais, k._flizu_kopsavilkums = k._flizu_kopsavilkums, (lambda: 1 / 0)
st, d = iegut("/api/statuss")
st2, v = iegut("/api/veseliba")
parbaude("salūzusi sadaļa: statuss un veselība 200, tikai flizes = {kluda}",
         st == 200 and d["flizes"] == {"kluda": "ZeroDivisionError"} and isinstance(d["arejie_avoti"], list)
         and st2 == 200 and v["flizes"] == {"kluda": "ZeroDivisionError"} and v["ok"] is True)
k._flizu_kopsavilkums = vecais
k._kesa.pop("statuss", None)

print("\nVisi testi izdevās." if not kludas else f"\n{kludas} KĻŪDAS")
if ports:
    serveris.shutdown()
    lokali = k.Serveris(("127.0.0.1", ports), k.Apstradatajs)
    print(f"API ar viltotiem datiem: http://127.0.0.1:{ports}/api/statuss (Ctrl+C — beigt)", flush=True)
    lokali.serve_forever()
sys.exit(1 if kludas else 0)
