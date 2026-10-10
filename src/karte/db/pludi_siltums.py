"""Plūdu pārbaudes "iesildīšana": demo adresēm un punktiem piepilda /api/pludi kešu (pludi_kesa) no LVĢMC WMS un
salīdzina to ar lokālo kopiju (pludu_zonas), lai pitch laikā atbilde nekad nav "neizdevās", pat ja LVĢMC neatbild.

Punkti: production/demo/scenariji.json (katra scenārija "vieta"), src/testi/parbaude.py (OGRE, JURMALA un
pārbaudes adreses) un auditā lietotās adreses (ADRESES zemāk). Adreses → koordinātas caur /api/adreses (VZD).

Palaišana (VPS, atjaunot_visu.sh pēc plūdu zonu ielādes; vai lokāli pret citu API):
  python3 src/karte/db/pludi_siltums.py [--api http://127.0.0.1:8920/api] [--bez-wms]
Tikai standarta bibliotēka. Pieprasījumi pa vienam (LVĢMC serviss ir lēns; nekādas slodzes).
Iznākuma kods 1, ja kādam punktam atbilde nav zināma vai kopija nesakrīt ar WMS.
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

SAKNE = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
SCENARIJI = os.path.join(SAKNE, "production", "demo", "scenariji.json")
PARBAUDE = os.path.join(SAKNE, "src", "testi", "parbaude.py")
# Adreses no src/testi/parbaude.py (adrešu pārbaude, VAICAJUMI) un 2026-10-10 audita ("Brīvības iela 12, Ogre, plūdi")
ADRESES = ["Brīvības iela 12 Ogre", "Brīvības 15 Ogre", "Mednieku iela 9 Ogre"]
PUNKTI = [("audits: /api/pludi piemērs (Ogre)", 56.816, 24.614)]
MEGINAJUMI = 4      # 202 "ielādējas" → vēlreiz pēc 10 s
TAIMAUTS = 30


def iegut(api, cels, parametri):
    url = f"{api}/{cels}?{urllib.parse.urlencode(parametri)}"
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "pludi_siltums.py"}),
                                timeout=TAIMAUTS) as r:
        return r.status, json.load(r)


def punkti(api):
    rez = list(PUNKTI)
    with open(SCENARIJI, encoding="utf-8") as f:
        for s in json.load(f)["scenariji"]:
            v = s.get("vieta")
            if v and "lat" in v and "lon" in v:
                rez.append((f"demo {s['kods']}: {v.get('nosaukums', '')}", float(v["lat"]), float(v["lon"])))
    teksts = open(PARBAUDE, encoding="utf-8").read()
    for nos in ("OGRE", "JURMALA"):
        m = re.search(rf"^{nos}\s*=\s*\(\s*([\d.]+)\s*,\s*([\d.]+)\s*\)", teksts, re.M)
        if m:
            rez.append((f"parbaude.py {nos}", float(m[1]), float(m[2])))
    for adrese in ADRESES:
        try:
            _, atrastas = iegut(api, "adreses", {"q": adrese, "limit": 1})
        except Exception as e:  # noqa: BLE001
            print(f"  adrese {adrese}: {e}", file=sys.stderr)
            continue
        if atrastas:
            a = atrastas[0]
            rez.append((f"adrese {a['adrese']}", float(a["lat"]), float(a["lon"])))
    redzets, unikali = set(), []
    for nos, lat, lon in rez:
        k = (round(lat, 4), round(lon, 4))
        if k not in redzets:
            redzets.add(k)
            unikali.append((nos, lat, lon))
    return unikali


def pludi(api, lat, lon, wms):
    parametri = {"lat": f"{lat:.6f}", "lon": f"{lon:.6f}", **({"wms": 1} if wms else {})}
    for m in range(MEGINAJUMI):
        try:
            statuss, d = iegut(api, "pludi", parametri)
        except Exception as e:  # noqa: BLE001
            d, statuss = {"zinams": False, "iemesls": str(e)}, 0
        if statuss != 202:
            return d
        if m < MEGINAJUMI - 1:
            time.sleep(10)
    return {"zinams": False, "iemesls": "joprojām ielādējas"}


def apraksts(d):
    if not d.get("zinams", True) or d.get("zona") is None:
        return f"NAV ZINĀMS ({d.get('iemesls', '?')})"
    zona = ", ".join(f"{v['veids']} {v['varbutiba_proc']} %" for v in d.get("veidi", [])) if d.get("zona") else "nē"
    return f"{zona} [{d.get('metode')}{', novecojis' if d.get('novecojis') else ''}]"


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--api", default=os.environ.get("MAP_API", "http://127.0.0.1:8920/api"))
    p.add_argument("--bez-wms", action="store_true", help="nejautāt LVĢMC WMS (tikai parastā /api/pludi atbilde)")
    a = p.parse_args()
    for straume in (sys.stdout, sys.stderr):
        straume.reconfigure(encoding="utf-8", errors="replace")

    api = a.api.rstrip("/")
    saraksts = punkti(api)
    print(f"pludi_siltums: {len(saraksts)} punkti, API {api}")
    problemas = 0
    for nos, lat, lon in saraksts:
        parasta = pludi(api, lat, lon, wms=False)
        rinda = f"  {nos} ({lat:.4f}, {lon:.4f}): {apraksts(parasta)}"
        if not a.bez_wms:
            w = pludi(api, lat, lon, wms=True)
            rinda += f" | WMS/kešs: {apraksts(w)}"
            if (parasta.get("metode") == "PostGIS kopija" and w.get("zinams") and not w.get("nepilnigi")
                    and bool(parasta.get("zona")) != bool(w.get("zona"))):
                rinda += "  ← NESAKRĪT"
                problemas += 1
            time.sleep(1)
        if not parasta.get("zinams", True) or parasta.get("zona") is None:
            problemas += 1
        print(rinda, flush=True)
    print(f"pludi_siltums: {'gatavs' if not problemas else f'{problemas} problēmas'}")
    return 1 if problemas else 0


if __name__ == "__main__":
    sys.exit(main())
