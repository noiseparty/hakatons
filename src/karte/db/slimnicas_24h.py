"""37 slimnīcas ar 24/7 neatliekamo palīdzību → src/karte/dati/slimnicas_24h.geojson.

Avots: VM 04.03.2026. rīkojums Nr. 01-01.1/26, Valsts katastrofu medicīnas plāna 12. pielikums
(ai-open-data-2026-hakatons/atseviski_dati/*.pdf). Adreses pārbaudītas pret VZD reģistru, OSM un iestāžu datiem.
Palaišana (VPS): python3 src/karte/db/slimnicas_24h.py /var/lib/hakatons-map/aw_eka.csv > src/karte/dati/slimnicas_24h.geojson
(aw_eka.csv: VZD adrešu reģistrs, data.gov.lv kopa varis-atvertie-dati)
"""
import csv, json, sys

REG = ["Rīgas"] * 6 + ["Kurzemes"] * 3 + ["Latgales"] * 6 + ["Vidzemes"] * 6 + ["Zemgales"] * 5 + ["Specializētās"] * 11
H = [
 (1, 'Valsts SIA "Bērnu klīniskā universitātes slimnīca"', "Vienības gatve 45, Rīga"),
 (2, 'Valsts SIA "Paula Stradiņa Klīniskā universitātes slimnīca"', "Pilsoņu iela 13 k-15, Rīga"),
 (3, 'SIA "Rīgas Austrumu klīniskā universitātes slimnīca"', "Hipokrāta iela 2, Rīga"),
 (4, 'SIA "Jūrmalas slimnīca"', "Vienības prospekts 19/21, Jūrmala"),
 (5, 'SIA "Ogres rajona slimnīca"', "Slimnīcas iela 2, Ogre"),
 (6, 'SIA "Tukuma slimnīca"', "Raudas iela 8, Tukums"),
 (7, 'SIA "Liepājas reģionālā slimnīca"', "Slimnīcas iela 25, Liepāja"),
 (8, 'SIA "Ziemeļkurzemes reģionālā slimnīca"', "Inženieru iela 60, Ventspils"),
 (9, 'SIA "Kuldīgas slimnīca"', "Aizputes iela 22, Kuldīga"),
 (10, 'SIA "Daugavpils reģionālā slimnīca"', "Vasarnīcu iela 20, Daugavpils"),
 (11, 'SIA "Rēzeknes slimnīca"', "18. novembra iela 41, Rēzekne"),
 (12, 'SIA "Preiļu slimnīca"', "Raiņa bulvāris 13, Preiļi"),
 (13, 'SIA "Krāslavas slimnīca"', "Rīgas iela 159, Krāslava"),
 (14, 'SIA "Līvānu slimnīca"', "Zaļā iela 44, Līvāni"),
 (15, 'SIA "Ludzas medicīnas centrs"', "Raiņa iela 43, Ludza"),
 (16, 'SIA "Vidzemes slimnīca"', "Jumaras iela 195, Valmiera"),
 (17, 'Madonas novada pašvaldības SIA "Madonas slimnīca"', "Rūpniecības iela 38, Madona"),
 (18, 'SIA "Balvu un Gulbenes slimnīcu apvienība"', "Vidzemes iela 2, Balvi"),
 (19, 'SIA "Cēsu klīnika"', "Slimnīcas iela 9, Cēsis"),
 (20, 'SIA "Alūksnes slimnīca"', "Pils iela 1, Alūksne"),
 (21, 'SIA "Limbažu slimnīca"', "Klostera iela 3, Limbaži"),
 (22, 'SIA "Jelgavas pilsētas slimnīca"', "Brīvības bulvāris 6, Jelgava"),
 (23, 'SIA "Jēkabpils reģionālā slimnīca"', "Andreja Pormaļa iela 125, Jēkabpils"),
 (24, 'SIA "Dobeles un apkārtnes slimnīca"', "Ādama iela 2, Dobele"),
 (25, 'SIA "Aizkraukles klīnika"', "Bērzu iela 5, Aizkraukle"),
 (26, 'SIA "Bauskas slimnīca"', "Dārza iela 7 k-1, Bauska"),
 (27, 'Valsts SIA "Traumatoloģijas un ortopēdijas slimnīca"', "Duntes iela 22, Rīga"),
 (28, 'Rīgas pašvaldības SIA "Rīgas 2. slimnīca"', "Ģimnastikas iela 1, Rīga"),
 (29, 'Valsts SIA "Nacionālais rehabilitācijas centrs "Vaivari""', "Asaru prospekts 61, Jūrmala"),
 (30, 'Rīgas pašvaldības SIA "Rīgas Dzemdību nams"', "Miera iela 45, Rīga"),
 (31, 'Valsts SIA "Nacionālais psihiskās veselības centrs"', "Tvaika iela 2, Rīga"),
 (32, 'Valsts SIA "Strenču psihoneiroloģiskā slimnīca"', "Valkas iela 11, Strenči"),
 (33, 'Valsts SIA "Slimnīca "Ģintermuiža""', "Filozofu iela 69, Jelgava"),
 (34, 'Valsts SIA "Daugavpils psihoneiroloģiskā slimnīca"', "Lielā Dārza iela 60/62, Daugavpils"),
 (35, 'SIA "Siguldas slimnīca"', "Lakstīgalas iela 13, Sigulda"),
 (36, 'VSIA "Piejūras slimnīca"', "Jūrmalas iela 2, Liepāja"),
 (37, 'VSIA "Bērnu psihoneiroloģiskā slimnīca "Ainaži""', "Valdemāra iela 46, Ainaži"),
]
# Lielajos kompleksos — neatliekamās palīdzības uzņemšanas ieeja no OSM (precīzāk par adreses punktu)
OSM_IEEJA = {
    2: (56.93138, 24.06594, "OSM node/9625153862 (PSKUS Neatliekamās medicīnas centrs)"),
    3: (56.96626, 24.24486, "OSM node/2530780593 (Neatliekamās medicīnas un pacientu uzņemšanas klīnika)"),
}
pref = {a.lower() + ",": nr for nr, _, a in H}
hits = {}
with open(sys.argv[1], encoding="utf-8-sig", newline="") as f:
    for r in csv.DictReader(f):
        if r["STATUSS"] == "EKS" and r["DD_N"]:
            low = r["STD"].lower()
            for p, nr in pref.items():
                if low.startswith(p) and nr not in hits:
                    hits[nr] = (r["STD"], float(r["DD_N"]), float(r["DD_E"]), r["KODS"])
feats, missing = [], []
for i, (nr, nos, adr) in enumerate(H):
    if nr not in hits:
        missing.append((nr, adr)); continue
    std, lat, lon, kods = hits[nr]
    avots = f"VZD adrešu reģistrs, adreses kods {kods}"
    if nr in OSM_IEEJA:
        lat, lon, avots = OSM_IEEJA[nr]
    feats.append({"type": "Feature", "geometry": {"type": "Point", "coordinates": [round(lon, 6), round(lat, 6)]},
                  "properties": {"nr": nr, "nosaukums": nos, "adrese": std, "regions": REG[i],
                                 "specializeta": REG[i] == "Specializētās",
                                 "piezime": "Neatliekamā palīdzība atbilstoši specializācijai" if REG[i] == "Specializētās" else "Neatliekamā medicīniskā palīdzība 24/7",
                                 "koord_avots": avots}})
if missing:
    sys.exit(f"Nav atrastas VZD: {missing}")
json.dump({"type": "FeatureCollection",
           "avots": "Veselības ministrijas 04.03.2026. rīkojums Nr. 01-01.1/26, Valsts katastrofu medicīnas plāna 12. pielikums",
           "features": feats}, sys.stdout, ensure_ascii=False, indent=1)
