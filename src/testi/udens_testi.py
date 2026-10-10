"""Upju līmeņa sliekšņu (udens_slieksni.json) un riska kartes upju / ledus iemeslu testi (bez datubāzes un ārējiem avotiem).

  uv run --no-project --python 3.12 --with "psycopg[binary]" src/testi/udens_testi.py
"""

import os
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "karte", "api"))
os.environ.setdefault("MAP_DB_DSN", "postgresql://viltots/x")
import karte_api as k  # noqa: E402
import udens_limenis as u  # noqa: E402

kludas = 0


def parbaude(nos, nosacijums):
    global kludas
    print(("OK   " if nosacijums else "KĻŪDA ") + nos)
    kludas += not nosacijums


# ---- sliekšņu fails ----
s = u.slieksni()
parbaude("Ogre, Pļaviņas, Liepājas ezers failā", {"HD073401", "HD073904", "HD073991"} <= set(s))
ogre = s["HD073401"]
parbaude("Ogre kritiskais 22,15 m (CA plāns)", ogre["kritiskais_m"] == 22.15 and "29" in ogre["avots"]["lpp"])
parbaude("Ogre slieksnis pieņemts 0,5 m zem kritiskā", ogre["slieksnis_pienemts"] and ogre["slieksnis_m"] == 21.65)
parbaude("Pļaviņas: oficiāls slieksnis", not s["HD073904"]["slieksnis_pienemts"] and s["HD073904"]["slieksnis_m"] == 73.04)
for sid, x in s.items():
    parbaude(f"{sid}: slieksnis < kritiskais, avots ar URL", x["slieksnis_m"] < x["kritiskais_m"] and x["avots"]["url"].startswith("https://"))

# ---- statuss ----
parbaude("statuss normāls", u.statuss(21.40, ogre) == "normāls")
parbaude("statuss paaugstināts (= slieksnis)", u.statuss(21.65, ogre) == "paaugstināts")
parbaude("statuss kritisks (= kritiskais)", u.statuss(22.15, ogre) == "kritisks")
parbaude("statuss bez līmeņa / sliekšņa → None", u.statuss(None, ogre) is None and u.statuss(21.0, None) is None)

# ---- ar_slieksni (/api/udens lauki) ----
a = u.ar_slieksni({"stacija": "HD073401", "nosaukums": "Ogre", "limenis_m": 21.40})
parbaude("ar_slieksni: Ogre 0,75 m zem kritiskā", a["statuss"] == "normāls" and a["lidz_kritiskajam_m"] == 0.75
         and a["kritiskais"] == 22.15 and a["vieta"] == "Ogre pie Ogres")
b = u.ar_slieksni({"stacija": "HD073062", "nosaukums": "Sigulda", "limenis_m": 12.0})
parbaude("ar_slieksni: stacija bez sliekšņa → null", b == {"slieksnis": None, "kritiskais": None, "statuss": None})
c = u.ar_slieksni({"stacija": "HD073401", "limenis_m": None})
parbaude("ar_slieksni: bez limenis_m → statuss None", c["statuss"] is None and c["lidz_kritiskajam_m"] is None)

# ---- bojāts fails: paliek pēdējie labie dati ----
vecais = u.SLIEKSNI_FAILS
u.SLIEKSNI_FAILS = os.path.join(os.path.dirname(vecais), "nav_tada_faila.json")
parbaude("trūkstošs fails → iepriekšējie dati", "HD073401" in u.slieksni())
u.SLIEKSNI_FAILS = vecais


# ---- ledus brīdinājumā ----
parbaude("ledus iešana → jā", k._min_ledu({"paradiba": "Plūdi", "teksts": "Gaidāma ledus iešana Ogrē", "riski": ""}))
parbaude("vižņi → jā", k._min_ledu({"paradiba": "Plūdi", "teksts": "Vižņu sastrēgumi Daugavā", "riski": None}))
parbaude("vējš → nē", not k._min_ledu({"paradiba": "Vējš", "teksts": "Brāzmas līdz 25 m/s", "riski": "koki"}))
parbaude("'apledojums' nav 'ledus' vārds", not k._min_ledu({"paradiba": "Apledojums", "teksts": "", "riski": ""}))


# ---- upju iemesli riska kartei ----
def stacija(sid, lim_m, vecums_h=1, lat=56.81, lon=24.64):
    laiks = (datetime.now(timezone.utc) - timedelta(hours=vecums_h)).isoformat().replace("+00:00", "Z")
    return {"geometry": {"coordinates": [lon, lat]},
            "properties": {"stacija": sid, "nosaukums": "X", "limenis_m": lim_m, "laiks": laiks}}


atslegas = [("sodien", "2026-10-10"), ("rit", "2026-10-11")]
atrast = lambda lat, lon: "ogre-kods"  # noqa: E731
iem = k._upju_iemesli([stacija("HD073401", 21.90)], {}, atrast, atslegas)
parbaude("paaugstināts → +1 šodien un rīt (bez prognozes)", [(x[1], x[2]) for x in iem] == [("sodien", 1), ("rit", 1)])
parbaude("teksts: 'Upes līmenis paaugstināts: Ogre pie Ogres 21,90 m'",
         iem and iem[0][3].startswith("Upes līmenis paaugstināts: Ogre pie Ogres 21,90 m"))
parbaude("avots: LVĢMC + CA plāns ar lpp.", iem and "Ogres novada" in iem[0][4]["nosaukums"] and "lpp." in iem[0][4]["nosaukums"])
iem = k._upju_iemesli([stacija("HD073401", 22.40)], {"HD073401": {"2026-10-11": (0, 0, 21.0, 0, 0)}}, atrast, atslegas)
parbaude("kritisks šodien +2, rīt pēc prognozes normāls → nav", [(x[1], x[2]) for x in iem] == [("sodien", 2)])
iem = k._upju_iemesli([stacija("HD073401", 21.0)], {"HD073401": {"2026-10-11": (0, 0, 22.3, 0, 0)}}, atrast, atslegas)
parbaude("rīt pēc prognozes kritisks → +2 rīt", [(x[1], x[2]) for x in iem] == [("rit", 2)] and "pēc prognozes" in iem[0][3])
parbaude("normāls → nav", k._upju_iemesli([stacija("HD073401", 20.6)], {}, atrast, atslegas) == [])
parbaude("vecs mērījums → nav", k._upju_iemesli([stacija("HD073401", 23.0, vecums_h=10)], {}, atrast, atslegas) == [])
parbaude("stacija bez sliekšņa → nav", k._upju_iemesli([stacija("HD073062", 99.0)], {}, atrast, atslegas) == [])
parbaude("ārpus reģiona → nav", k._upju_iemesli([stacija("HD073401", 23.0)], {}, lambda *_: None, atslegas) == [])
iem = k._upju_iemesli([stacija("HD073991", 0.86, lat=56.48, lon=21.03)], {}, atrast, atslegas[:1])
parbaude("Liepājas ezers: 'Ezera līmenis paaugstināts'", iem and iem[0][3].startswith("Ezera līmenis paaugstināts"))


# ---- _riski: upes +2 un ledus +1 nāk klāt pēc prognozes (max), ne vairāk par 3 ----
def kesot(atslega, vertiba):
    with k._kesas_slots:
        k._kesa[atslega] = (1e12, vertiba)  # "svaigs" līdz tālai nākotnei


tagad = datetime(2026, 10, 10, 9, 0)
kesot("bridinajumi", [{"id": "b1", "krasa": "Dzeltens", "limenis": 1, "paradiba": "Plūdi", "teksts": "Gaidāma ledus iešana",
                       "riski": "", "no": None, "lidz": None, "poligoni": [[(56.7, 24.5), (56.9, 24.5), (56.9, 24.8), (56.7, 24.8)]]}])
kesot("udens", [stacija("HD073401", 22.50)])
kesot("hidro_prognoze", {})
kesot("zibens_fmi", {"zibeni": []})
k._noverojumi_svaigi = lambda: []
vietas = {"1": ("Ogre", 56.81, 24.60, "ogre-kods")}
kesot(("bridinajuma_novadi", "b1", len(vietas)), ([], ["ogre-kods"]))
dati = {"kopsavilkums": {"2026-10-10": {"ogre-kods": {"brazmas": 21, "brazmas_vieta": "Ogre", "nokrisni": 0}}}}
r = k._riski(dati, {"ogre-kods": {}}, vietas, tagad, ["2026-10-10", "2026-10-11"])["ogre-kods"]
teksti = [i["teksts"] for i in r["iemesli"] if i["diena"] == "sodien"]
parbaude("_riski: brāzmas 2 + ledus 1 + upe 2 → 3 (griesti)", r["sodien"] == 3)
parbaude("_riski: iemeslos ledus un upe", any(t.startswith("ledus") for t in teksti) and any(t.startswith("Upes līmenis kritisks") for t in teksti))
parbaude("_riski: upe ar limenis 2 (popup rāda +2)", any(i["limenis"] == 2 and i["klat"] for i in r["iemesli"] if i["teksts"].startswith("Upes")))
parbaude("_riski: rīt brīdinājums 1 + ledus 1 + upe 2 → 3", r["rit"] == 3)

print("\nKļūdas:", kludas)
sys.exit(1 if kludas else 0)
