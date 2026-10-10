"""Pašvaldību uzziņa rezultāta kartītei → src/karte/dati/pasvaldibas.json (atslēga: VZD adrešu reģistra kods = regioni.kods).

Avoti:
  ai-open-data-2026-hakatons/ca-plani-hakatons/pasvaldibas.csv + darba_saraksts.json — nosaukums, tīmekļvietne, CA plāna
    publikācijas lapa (organizatoru komplekts);
  markdown/<slug>/*.md priekšvārds avota_url — CA plāna dokuments (lielākais fails mapē, ne lēmumi);
  Uzņēmumu reģistrs, "Publisko personu un iestāžu saraksts" (data.gov.lv public-persons-institutions, CC0, atjauno katru
    dienu) — pašvaldības oficiālais e-pasts, tālrunis, adrese, tīmekļvietne (visas 42 pašvaldības, arī valstspilsētas);
  VPVKAC kontakti (data.gov.lv vpvkac-kontakti, CC0, jaunākā versija 2023-11, CSV) — klientu apkalpošanas centra adrese,
    tālrunis; katrai pašvaldībai viens centrs (pilsētas centrs, ja ir). Valstspilsētām un Ventspils novadam centru
    sarakstā nav; kartīte tos rāda tikai kā papildu rindu, galvenie kontakti ir UR (42/42). Skat. notes/pasvaldibu-kontakti.md.
Palaišana (lokāli): uv run --no-project src/karte/db/pasvaldibas.py
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
          "5ae1dc82-fd3b-4ea6-b868-34b7e36603c0/download/vpvkac-kontakti_2023_aktual_081123.csv")
UA = {"User-Agent": "map.repo.lv (AI Open Data 2026 hakatons)"}
UR = ("https://data.gov.lv/dati/dataset/2e4926ea-8648-44e6-9227-3cb20604ec31/resource/"
      "190ba502-08d1-4c4c-b1b9-b58299bf9a9f/download/ppi_public_persons_institutions.csv")


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
    """VPVKAC kontakti 2023-11 (CSV): ieraksta rinda (Nr., nosaukums, adrese), tālāk darba laika rindas ar tālruni/e-pastu."""
    with urllib.request.urlopen(urllib.request.Request(VPVKAC, headers=UA), timeout=180) as r:
        teksts = r.read().decode("utf-8-sig")
    tirs = lambda t: " ".join((t or "").split())  # noqa: E731
    centri, tagad = [], None
    for rinda in csv.reader(io.StringIO(teksts, newline=""), delimiter=";"):
        rinda = rinda + [""] * (12 - len(rinda))
        if rinda[0].strip().isdigit() and rinda[4].strip():  # nr, ..., jaunais nosaukums, pilnais, īsais, adrese
            tagad = {"punkts": re.sub(r"\s*VPVKAC.*$", "", tirs(rinda[6])), "nosaukums": tirs(rinda[4]),
                     "adrese": tirs(rinda[7]), "talrunis": None, "epasts": None}
            centri.append(tagad)
        elif tagad:
            if not tagad["talrunis"] and re.fullmatch(r"[\d ,;+]{6,}", rinda[10].strip()):
                tagad["talrunis"] = tirs(rinda[10])
            if not tagad["epasts"] and "@" in rinda[11]:
                tagad["epasts"] = tirs(rinda[11]).lower()
    return centri


def ur_kontakti():
    """{"Ogres novada pašvaldība": {...}} — reģistrētās pašvaldības no UR publisko personu saraksta (CC0)."""
    with urllib.request.urlopen(urllib.request.Request(UR, headers=UA), timeout=120) as r:
        teksts = r.read().decode("utf-8-sig")
    rez = {}
    for x in csv.DictReader(io.StringIO(teksts), delimiter=";"):
        if x.get("authorityType") == "DERIVED_PUBLIC_PERSON_PARISH" and x.get("Status") == "REGISTERED" \
                and x.get("name", "").endswith(" pašvaldība"):
            lapa = (x.get("website") or "").strip()
            if lapa and not lapa.startswith("http"):
                lapa = "https://" + lapa
            rez[x["name"].strip()] = {"epasts": (x.get("email") or "").strip().lower() or None,
                                      "talrunis": (x.get("phone") or "").strip() or None,
                                      "adrese": " ".join((x.get("address") or "").split()) or None,
                                      "majas_lapa": lapa or None}
    return rez


def ur_nosaukums(pasvaldiba, tips):
    return gen(pasvaldiba) + (" valstspilsētas pašvaldība" if tips == "valstspilsēta" else " pašvaldība")


def main():
    slugi = {d["pasvaldiba"]: d for d in json.loads((KIT / "darba_saraksts.json").read_text(encoding="utf-8"))}
    centri = vpvkac_centri()
    ur = ur_kontakti()
    rez = {}
    for r in csv.DictReader((KIT / "pasvaldibas.csv").open(encoding="utf-8")):
        d = slugi.get(r["pasvaldiba"], {})
        g = gen(r["pasvaldiba"])
        savi = [c for c in centri if g.lower() in c["nosaukums"].lower()]
        # tikai pašvaldības centra pilsētas centrs ("Ogres novads" → punkts "Ogres"); cita pilsēta kartītē maldinātu
        centrs = next((c for c in savi if c["punkts"] == gen(r["pasvaldiba"].removesuffix(" novads"))
                       and "pilsētas" in c["nosaukums"].lower()), None)
        rez[r["adresu_registra_kods"]] = {
            "nosaukums": r["pasvaldiba"], "tips": r["tips"], "atvk": r["atvk_kods"],
            "majas_lapa": r["parbaudita_url"] or r["majas_lapa"],
            "ca_plans_url": plana_url(d["slug"]) if d.get("slug") else None,
            "ca_lapa": d.get("vugd_norade") or None,
            "vpvkac": centrs, "vpvkac_skaits": len(savi),
            "kontakti": ur.get(ur_nosaukums(r["pasvaldiba"], r["tips"])),
        }
    DATI.mkdir(parents=True, exist_ok=True)
    (DATI / "pasvaldibas.json").write_text(json.dumps(rez, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"pasvaldibas.json: {len(rez)} pašvaldības, ar CA plānu {sum(1 for v in rez.values() if v['ca_plans_url'])}, "
          f"ar VPVKAC {sum(1 for v in rez.values() if v['vpvkac'])}, ar UR kontaktiem {sum(1 for v in rez.values() if v['kontakti'])}")


if __name__ == "__main__":
    main()
