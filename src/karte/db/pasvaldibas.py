"""Pašvaldību uzziņa rezultāta kartītei → src/karte/dati/pasvaldibas.json (atslēga: VZD adrešu reģistra kods = regioni.kods).

Avoti:
  ai-open-data-2026-hakatons/ca-plani-hakatons/pasvaldibas.csv + darba_saraksts.json — nosaukums, tīmekļvietne, CA plāna
    publikācijas lapa (organizatoru komplekts);
  markdown/<slug>/*.md priekšvārds avota_url — CA plāna dokuments (lielākais fails mapē, ne lēmumi);
  VPVKAC paplašinātā tīkla kontaktpunkti (data.gov.lv vpvkac-kontakti, CC0, 2022. gada augusts) — klientu apkalpošanas
    centra tālrunis un e-pasts; katrai pašvaldībai viens centrs (pilsētas centrs, ja ir).
Palaišana (lokāli; vajag openpyxl): uv run --no-project --with openpyxl src/karte/db/pasvaldibas.py
"""

import csv
import io
import json
import pathlib
import re
import urllib.request

SAKNE = pathlib.Path(__file__).resolve().parents[3]
KIT = SAKNE / "ai-open-data-2026-hakatons" / "ca-plani-hakatons"
DATI = SAKNE / "src" / "karte" / "dati"
VPVKAC = ("https://data.gov.lv/dati/dataset/efe66739-3a88-47bf-b63c-cd01493ab475/resource/"
          "4b72d47d-bd80-47cb-8309-ca5f2e761339/download/vpvkac_kontakti_2022_08.xlsx")
UA = {"User-Agent": "map.repo.lv (AI Open Data 2026 hakatons)"}


def gen(nosaukums):
    """Ģenitīvs: "Ogres novads" → "Ogres novada", "Rīga" → "Rīgas", "Daugavpils" → "Daugavpils"."""
    if nosaukums.endswith(" novads"):
        return nosaukums[:-1] + "a"
    return nosaukums + "s" if nosaukums[-1] in "ae" else nosaukums


def plana_url(slug):
    mape = KIT / "markdown" / slug
    faili = sorted((f for f in mape.glob("*.md") if f.name != "STRUKTURA.md"), key=lambda f: f.stat().st_size, reverse=True)
    for f in faili:
        m = re.search(r"^avota_url:\s*(\S+)", f.read_text(encoding="utf-8")[:3000], re.M)
        if m:
            return m.group(1)
    return None


def vpvkac_centri():
    import openpyxl
    with urllib.request.urlopen(urllib.request.Request(VPVKAC, headers=UA), timeout=120) as r:
        wb = openpyxl.load_workbook(io.BytesIO(r.read()), read_only=True)
    centri = []
    for rinda in wb.worksheets[0].iter_rows(values_only=True):
        c = [str(x).strip() for x in rinda if x is not None and str(x).strip()]
        if len(c) >= 5 and c[0].isdigit():  # nr, punkts, pilnais nosaukums, adrese, "Darba laiks:", tālrunis, e-pasts
            talr = next((x for x in c[4:] if re.fullmatch(r"[\d ,;]+", x)), None)
            epasts = next((x for x in c[4:] if "@" in x), None)
            tirs = lambda t: " ".join(t.split())  # noqa: E731
            centri.append({"punkts": tirs(c[1]), "nosaukums": tirs(c[2]), "adrese": tirs(c[3]), "talrunis": talr, "epasts": epasts})
    return centri


def main():
    slugi = {d["pasvaldiba"]: d for d in json.loads((KIT / "darba_saraksts.json").read_text(encoding="utf-8"))}
    centri = vpvkac_centri()
    rez = {}
    for r in csv.DictReader((KIT / "pasvaldibas.csv").open(encoding="utf-8")):
        d = slugi.get(r["pasvaldiba"], {})
        g = gen(r["pasvaldiba"])
        savi = [c for c in centri if g.lower() in c["nosaukums"].lower()]
        # pašvaldības centra pilsēta ("Ogres novads" → punkts "Ogre"), citādi jebkura pilsēta, citādi pirmais
        centrs = next((c for c in savi if gen(c["punkts"]) == r["pasvaldiba"].removesuffix(" novads")), None) or \
            next((c for c in savi if "pilsētas" in c["nosaukums"].lower()), savi[0] if savi else None)
        rez[r["adresu_registra_kods"]] = {
            "nosaukums": r["pasvaldiba"], "tips": r["tips"], "atvk": r["atvk_kods"],
            "majas_lapa": r["parbaudita_url"] or r["majas_lapa"],
            "ca_plans_url": plana_url(d["slug"]) if d.get("slug") else None,
            "ca_lapa": d.get("vugd_norade") or None,
            "vpvkac": centrs, "vpvkac_skaits": len(savi),
        }
    DATI.mkdir(parents=True, exist_ok=True)
    (DATI / "pasvaldibas.json").write_text(json.dumps(rez, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"pasvaldibas.json: {len(rez)} pašvaldības, ar CA plānu {sum(1 for v in rez.values() if v['ca_plans_url'])}, "
          f"ar VPVKAC {sum(1 for v in rez.values() if v['vpvkac'])}")


if __name__ == "__main__":
    main()
