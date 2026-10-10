"""Lejupielādē valsts atvērtos datus (data.gov.lv, CC0) un saglabā vienotā CSV formā src/karte/dati/.

Katrs fails: id, nosaukums, adrese, x, y (+ papildu lauki). Koordinātu sistēma norādīta SRID kolonnā
ielade_visu.sh (VP un VUGD: LKS-92 TM, EPSG:3059; pārējie WGS-84).
Licences un saites: tabula avoti (shema.sql). Palaišana (lokāli vai VPS, tikai standarta bibliotēka):
  python src/karte/db/valsts_dati.py
"""

import csv
import io
import os
import pathlib
import urllib.request

# HAKATONS_DATI: cita mape (VPS ikdienas atjaunošana raksta /var/lib/hakatons/dati, nevis git kopijā)
DATI = pathlib.Path(os.environ.get("HAKATONS_DATI") or pathlib.Path(__file__).resolve().parents[1] / "dati")
UA = {"User-Agent": "map.repo.lv (AI Open Data 2026 hakatons)"}


def lejupieladet(url, kodejums="utf-8-sig"):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r:
        return r.read().decode(kodejums).lstrip("﻿")  # ZVA failam ir divi BOM


def saglabat(vards, lauki, rindas):
    cels = DATI / vards
    with open(cels, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=lauki, lineterminator="\n")
        w.writeheader()
        w.writerows(rindas)
    print(f"{cels.name}: {len(rindas)}")


def labot_kodejumu(s):
    """VP failā daļa nosaukumu ir cp1257 baiti, nolasīti kā latin-1 ("pârvalde" → "pārvalde").
    Latviešu burti nav latin-1 diapazonā 0xC0–0xFF, tāpēc tos droši pārkodējam atpakaļ."""
    return "".join(bytes([ord(c)]).decode("cp1257") if 0xC0 <= ord(c) <= 0xFF else c for c in s)


def skaitlis(s):
    return (s or "").replace(",", ".").strip()


def arstniecibas_iestades():
    url = ("https://data.gov.lv/dati/dataset/05068340-d155-49cc-9a37-ab7d63ccd769/resource/"
           "5ea6e4aa-ee21-462a-8590-283483d2b0a4/download/medicinasiestades.csv")
    rindas = [
        {"id": r["ID"], "nosaukums": r["Nosaukums"], "adrese": r["Adrese"], "tips": r["IestadesTips"],
         "x": skaitlis(r["long"]), "y": skaitlis(r["lat"])}
        for r in csv.DictReader(io.StringIO(lejupieladet(url)))
        if r["IestadesTips"] != "Ģimenes ārstu prakse" and r["lat"]
    ]
    saglabat("iemic_arstniecibas_iestades.csv", ["id", "nosaukums", "adrese", "tips", "x", "y"], rindas)


def aptiekas():
    rindas = [
        {"id": r["object_id"], "nosaukums": r["object_name"], "adrese": r["object_addr_nice"],
         "tips": r["object_type_txt"], "telefons": r["object_phone"], "licence": r["lic_code"],
         "x": skaitlis(r["object_coord_x"]), "y": skaitlis(r["object_coord_y"])}
        for r in csv.DictReader(io.StringIO(lejupieladet("https://dati.zva.gov.lv/fdu-registrs/export/fdu_register.csv")))
        # 4 = licence spēkā (3 = apturēta); bez koordinātām nevar parādīt kartē
        if r["object_type_txt"].startswith("Vispārēja tipa aptieka") and r["lic_status"] == "4" and r["object_coord_x"]
    ]
    saglabat("zva_aptiekas.csv", ["id", "nosaukums", "adrese", "tips", "telefons", "licence", "x", "y"], rindas)


def vp_iecirkni():
    url = ("https://data.gov.lv/dati/dataset/f37fb118-4dfe-4011-9816-ebe964ebc203/resource/"
           "80cc2dd9-f424-4c5c-9bbc-a01c02bfcb28/download/vp_iecirknu_adreses.csv")
    rindas = [{"id": r["id"], "nosaukums": labot_kodejumu(r["iecirknis"]), "adrese": r["adrese"], "x": r["x"], "y": r["y"]}
              for r in csv.DictReader(io.StringIO(lejupieladet(url))) if r["x"]]
    saglabat("iemic_vp_iecirkni.csv", ["id", "nosaukums", "adrese", "x", "y"], rindas)


def pasvaldibu_policija():
    url = ("https://data.gov.lv/dati/dataset/af093e35-5962-41d8-9f3f-f59312c5616f/resource/"
           "1a11bf3a-b79d-4999-bb8d-67065b55bb3a/download/pp.csv")
    rindas = []
    for i, r in enumerate(csv.DictReader(io.StringIO(lejupieladet(url, "cp1257")), delimiter=";")):
        if not r["lat"]:
            continue
        adrese = ", ".join(x for x in (" ".join(x for x in (r["IELA"], r["MAJA"]) if x), r["APDZ_VIETA"]) if x)
        rindas.append({"id": f"{i}-{r['NOSAUKUMS']}-{r['APDZ_VIETA']}", "nosaukums": r["NOSAUKUMS"], "adrese": adrese,
                       "x": skaitlis(r["lon"]), "y": skaitlis(r["lat"])})
    saglabat("iemic_pasvaldibu_policija.csv", ["id", "nosaukums", "adrese", "x", "y"], rindas)


def vugd_depo():
    url = ("https://data.gov.lv/dati/dataset/2466e938-6eba-4016-8ff8-f7e3f2736249/resource/"
           "a91ff743-e064-41d4-b449-b29d713fc6fb/download/vugd_depo_adreses.csv")
    rindas = [{"id": r["id"], "nosaukums": r["nosaukums"], "adrese": r["adrese"], "telefons": r["telefons"],
               "epasts": r["epasts"], "parvalde": r["regiona_piederiba"], "x": r["x"], "y": r["y"]}
              for r in csv.DictReader(io.StringIO(lejupieladet(url))) if r["x"]]
    saglabat("iemic_vugd_depo.csv", ["id", "nosaukums", "adrese", "telefons", "epasts", "parvalde", "x", "y"], rindas)


def udens_nemsanas_vietas():
    """VKCP IĢIS "Atklātās ūdens ņemšanas vietas" (CC0). Failā ir arī ~15 000 hidrantu (UH, EX, R, M, T, …):
    kartē liekam tikai atklātās ūdens ņemšanas vietas (apzīmējums "Ut;<tilpums> (U<nr>)"). LKS-92 TM (EPSG:3059)."""
    url = ("https://data.gov.lv/dati/dataset/d43c5e7f-7c11-4b0e-8222-51261c23d752/resource/"
           "b3705fbe-3b29-47a3-a8c7-cdb3269d26cc/download/atklatas_udens_nemsanas_vietas_un_hidranti.csv")
    rindas = []
    for r in csv.DictReader(io.StringIO(lejupieladet(url))):
        if not r["name"].startswith("Ut;") or not r["x"]:
            continue
        tilpums, _, nr = r["name"][3:].partition(" (")
        rindas.append({"id": r["id"], "nosaukums": "Ūdens ņemšanas vieta ugunsdzēsībai" + (f" {nr.rstrip(')')}" if nr else ""),
                       "apzimejums": r["name"], "tilpums": tilpums.strip(), "x": r["x"], "y": r["y"]})
    saglabat("vkcp_udens_nemsanas_vietas.csv", ["id", "nosaukums", "apzimejums", "tilpums", "x", "y"], rindas)


if __name__ == "__main__":
    DATI.mkdir(parents=True, exist_ok=True)
    for f in (arstniecibas_iestades, aptiekas, vp_iecirkni, pasvaldibu_policija, vugd_depo, udens_nemsanas_vietas):
        f()
