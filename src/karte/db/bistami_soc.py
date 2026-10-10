"""Divi atvērto datu slāņi (data.gov.lv, CC0) → momentuzņēmumi src/karte/dati/*.geojson.

  bistami  Bīstami objekti, kategorija bistams_objekts, divi avoti:
             eva-seveso   VVD/EVA objekti, kuriem jāizstrādā rūpniecisko avāriju novēršanas programma (RANP) vai drošības
                          pārskats (DP): Seveso III uzņēmumi. XLSX, bez koordinātām → adreses ģeokodētas ar VZD adrešu
                          reģistru (aw_eka.csv, CC BY 4.0). → bistami_seveso.geojson
             lvgmc-eprtr  LVĢMC ES Rūpniecisko vietu reģistrs (E-PRTR / IED), INSPIRE GML ar koordinātām (EPSG:4258).
                          Tikai ražotnes (ProductionFacility) ar statusu functional; kontaktpersonu dati netiek glabāti.
                          → bistami_eprtr.geojson
  soc      Sociālo pakalpojumu sniedzēju reģistrs (Labklājības ministrija), JSON bez koordinātām, bet ar VZD adreses
           kodu (FaktiskaAdrese.VZDKods) → koordinātas no aw_eka.csv pēc koda. Tikai statuss "Sniedz" un tikai
           juridiskas personas/iestādes (privātuzņēmēji un individuālie komersanti izlaisti); tālruņi, e-pasti un vadītāju
           vārdi netiek glabāti — tikai iestādes nosaukums, pakalpojums, veids, plānotais klientu skaits, klientu grupas,
           adrese, tīmekļvietne. → soc_pakalpojumi.geojson

Ģeokodēšana: aw_eka.csv (VZD, ~140 MB) tiek lejupielādēts kešā (--kese, noklusēti MAP_CACHE vai ./kese) un lasīts vienu
reizi; koordinātas ir WGS-84 (DD_N, DD_E), tikai spēkā esošas adreses (STATUSS=EKS). VPS šī skripta NEVAJAG — ielādei
pietiek ar repozitorijā iekļautajiem GeoJSON (ielade.py). Skriptu palaiž lokāli, kad jāatjauno momentuzņēmumi:

  uv run --no-project --python 3.12 --with openpyxl src/karte/db/bistami_soc.py bistami soc
  uv run --no-project --python 3.12 --with openpyxl src/karte/db/bistami_soc.py bistami --kese C:/temp/kese

Seveso adreses bez ēkas koordinātām (piem. "Torņi", Saldus pagasts) neatrodas reģistrā → RUCINI saraksts zemāk ar
koordinātām no tā paša uzņēmuma E-PRTR ieraksta vai ĢeoLatvija kartes; katrai norādīts pamatojums.
"""

import csv
import json
import os
import pathlib
import re
import sys
import unicodedata
import zlib
import urllib.request
import xml.etree.ElementTree as ET

DATI = pathlib.Path(__file__).resolve().parents[1] / "dati"
AW_EKA = ("https://data.gov.lv/dati/dataset/6b06a7e8-dedf-4705-a47b-2a7c51177473/resource/"
          "a510737a-18ce-400f-ad4b-04fce5228272/download/aw_eka.csv")
AW_DZIV = ("https://data.gov.lv/dati/dataset/6b06a7e8-dedf-4705-a47b-2a7c51177473/resource/"
           "b83be373-f444-4f50-9b98-28741845325e/download/aw_dziv.csv")
SEVESO_URL = ("https://data.gov.lv/dati/dataset/2e78264e-985c-429e-93cb-97c96b12360f/resource/"
              "c2af85ab-039b-4d10-81b3-4bc76e1704f1/download/eva_objekti-kuriem-jizstrd-rpniecisko-avriju-novranas-"
              "programma-vai-drobas-prskats_2025.1.pusg..xlsx")
EPRTR_URL = ("https://data.gov.lv/dati/lv/dataset/134b0537-9f54-4930-907a-79f0510b4993/resource/"
             "d7e28033-2768-4edb-8e88-79e0a79cc84b/download/3_eu_registry_latvia_2025.gml")
SOC_URL = ("https://data.gov.lv/dati/lv/dataset/64882fbe-7ce3-4c93-bda6-de9bf57fb03c/resource/"
           "e230ab23-8d75-4982-8c8a-77d3f009818b/download/pakalpojumusniedzejudati_20261010.json")
# (CKAN dataset: socialo-pakalpojumu-sniedzeju-registra-dati; faila nosaukumā datums — jaunāko skat. datu kopas lapā)

# Seveso uzņēmumi, kuru adresi automātiski atrast nevar (nav ielas ar numuru vai tāda nr. VZD nav): uzņēmuma nosaukums →
# (VZD adreses kods, pamatojums). Koordinātas tāpat nāk no aw_eka.csv pēc koda; pārbaudiet ar kartes slāni.
RUCINI = {
    "baltic agro, sia": ("104387438", "adrese avotā 'Stropi 16A un 16B' → Stropi 16A (Naujenes pag.)"),
    "conexus baltic grid, as": ("105589484", "Inčukalna pazemes gāzes krātuve → VZD ēka 'Inčukalna gāzes krātuve', Krimuldas pag."),
    "pirmas, sia": ("106353470", "Olaines naftas bāze (Jelgavas šosejas 16. km) → VZD ēka 'Naftas bāze', Olaines pag. (aptuveni)"),
    "riga fertilizer terminal, sia": ("101920257", "Kundziņsalas 8. līnija 5 nav VZD → tuvākā reģistrētā adrese 8. līnija 10 (aptuveni, ~60 m)"),
    "saldus naftas bāze, as": ("106073245", "'Torņi', Saldus pag. → VZD adrese 'Torņi', Saldus pag."),
}

NS = {"gml": "http://www.opengis.net/gml/3.2", "EUReg": "http://dd.eionet.europa.eu/schemaset/euregistryonindustrialsites",
      "base": "http://inspire.ec.europa.eu/schemas/base/3.3", "act": "http://inspire.ec.europa.eu/schemas/act-core/4.0",
      "pf": "http://inspire.ec.europa.eu/schemas/pf/4.0",
      "xlink": "http://www.w3.org/1999/xlink"}
XLINK = "{http://www.w3.org/1999/xlink}href"

# Biežākie darbības kodi (IED I pielikums: kods ar punktu; E-PRTR I pielikums: kods ar iekavām bez punkta)
DARBIBAS = {
    "1.1": "Kurināmā sadedzināšana (≥ 50 MW)", "1(c)": "Siltumelektrostacijas un citas sadedzināšanas iekārtas",
    "1(b)": "Naftas un gāzes pārstrāde", "2.3(a)": "Melno metālu karstā velmēšana", "2.3(c)": "Melno metālu kalšana",
    "2(c)(i)": "Melno metālu apstrāde", "2(c)(iii)": "Melno metālu cinkošana", "2(e)(ii)": "Krāsainie metāli",
    "2.5(b)": "Krāsaino metālu kausēšana", "2.6": "Metālu virsmu apstrāde",
    "3.1(a)": "Cementa vai kaļķa ražošana", "3(c)(i)": "Cements un kaļķis", "3(e)": "Stikla ražošana",
    "3(g)": "Keramikas ražošana", "3.3": "Stikla ražošana", "3.5": "Keramikas ražošana",
    "4(a)(x)": "Ķīmiskā rūpniecība", "4(e)": "Ķīmiskā rūpniecība (neorganiskās vielas)", "4.5": "Farmaceitisko vielu ražošana",
    "5(a)": "Bīstamo atkritumu apsaimniekošana", "5.1": "Bīstamo atkritumu apsaimniekošana", "5.1(b)": "Bīstamo atkritumu apsaimniekošana",
    "5(c)": "Nebīstamo atkritumu apsaimniekošana", "5.3(a)": "Nebīstamo atkritumu apsaimniekošana",
    "5(d)": "Atkritumu poligons", "5.4": "Atkritumu poligons", "5.5": "Bīstamo atkritumu pagaidu glabāšana",
    "5(e)": "Dzīvnieku atliekas", "5(f)": "Pilsētas notekūdeņu attīrīšana",
    "6(b)": "Papīra un kartona ražošana", "6.1(b)": "Papīra un kartona ražošana", "6.4(c)": "Augu izcelsmes izejvielu pārstrāde",
    "6.6(a)": "Intensīva putnu audzēšana", "6.6(b)": "Intensīva cūku audzēšana", "6.7": "Organisko vielu virsmu apstrāde",
    "7(a)(i)": "Intensīva putnu audzēšana", "7(a)(ii)": "Intensīva cūku audzēšana", "7(a)(iii)": "Intensīva sivēnmāšu audzēšana",
    "8(c)": "Pārtikas ražošana (piens, augu izejvielas)", "9(c)": "Tekstilmateriālu apstrāde",
}


def norm(teksts):
    t = unicodedata.normalize("NFKD", teksts or "").encode("ascii", "ignore").decode().lower().replace("\xa0", " ")
    return re.sub(r"[^a-z0-9 ]", "", t).strip()


def lejupielade(url, cels):
    if cels.exists() and cels.stat().st_size > 0:
        return cels
    cels.parent.mkdir(parents=True, exist_ok=True)
    print("lejupielādē", url, file=sys.stderr)
    req = urllib.request.Request(url, headers={"User-Agent": "map.repo.lv (hakatons)"})
    with urllib.request.urlopen(req, timeout=300) as r, open(cels, "wb") as f:
        while chunk := r.read(1 << 20):
            f.write(chunk)
    return cels


def rakstit(fails, features):
    features.sort(key=lambda f: f["properties"]["id"])
    fails.write_text(json.dumps({"type": "FeatureCollection", "features": features}, ensure_ascii=False,
                                separators=(",", ":")), encoding="utf-8")


def feature(koord, ipasibas):
    return {"type": "Feature", "geometry": {"type": "Point", "coordinates": [round(koord[1], 6), round(koord[0], 6)]},
            "properties": ipasibas}


def ieksa_latvija(lat, lon):
    return 55.5 < lat < 58.2 and 20.5 < lon < 28.4


def vzd_csv(kese, vards, url):
    cels = lejupielade(url, kese / vards)
    with open(cels, encoding="utf-8-sig", newline="") as f:
        yield from csv.DictReader(f)


def vzd_rindas(kese):
    """aw_eka.csv spēkā esošās ēku adreses: (kods, std, lat, lon)."""
    for r in vzd_csv(kese, "aw_eka.csv", AW_EKA):
        if r["STATUSS"] == "EKS" and r["DD_N"] and r["DD_E"]:
            yield r["KODS"], r["STD"], float(r["DD_N"]), float(r["DD_E"])


def vzd_koordinatas(kese, kodi):
    """VZD adreses kods → (lat, lon, std). Telpu grupas (dzīvokļa) kodam ņem ēkas (VKUR_CD) koordinātas no aw_eka.csv;
    dzīvokļu adreses (aw_dziv.csv) pašas koordinātu nesatur. Statusu nefiltrē: LM norādītā adrese ir pietiekams pamats."""
    kodi = set(kodi)
    vecaki = {}
    for r in vzd_csv(kese, "aw_dziv.csv", AW_DZIV):
        if r["KODS"] in kodi:
            vecaki[r["KODS"]] = r["VKUR_CD"]
    vajag = kodi | set(vecaki.values())
    eka = {}
    for r in vzd_csv(kese, "aw_eka.csv", AW_EKA):
        if r["KODS"] in vajag and r["DD_N"] and r["DD_E"]:
            eka[r["KODS"]] = (float(r["DD_N"]), float(r["DD_E"]), r["STD"])
    return {k: eka[v] for k in kodi if (v := k if k in eka else vecaki.get(k)) in eka}


# ---------- Seveso ----------

def atslega(teksts):
    """Ielas un numura salīdzināšanas atslēga: bez garumzīmēm, atstarpēm un pieturzīmēm."""
    return norm(teksts).replace(" ", "")


def seveso_adrese(vieta):
    """'naftas terminālis,\nEzera iela 22, Rīga' → ('ezeraiela22', {'riga', ...}, 'Ezera iela 22'): ielas un numura daļa +
    pārējās daļas (pilsēta, pagasts, novads). Vairāki numuri ('Tvaika iela 7a un 9') → pirmais. None, ja nav ielas ar numuru."""
    vieta = vieta.replace("\xa0", " ").replace("“", "").replace("”", "")
    daļas = [d.strip(" ,;") for d in re.split(r"[\n,]", vieta) if d.strip(" ,;")]
    for i, d in enumerate(daļas):
        d = re.split(r"\s+un\s+", d)[0]
        if re.search(r"(iela|ielas|šoseja|šosejas|dambis|prospekts|bulvāris|līnija|ceļš|laukums|ostmala|krastmala)", d, re.I) \
                and re.search(r"\d\s*[a-zA-Z]?$", d):
            return atslega(d), {atslega(x) for j, x in enumerate(daļas) if j != i}, d
    return None



def seveso(kese):
    import openpyxl

    xlsx = lejupielade(SEVESO_URL, kese / "seveso.xlsx")
    wb = openpyxl.load_workbook(xlsx, data_only=True)
    rindas = [r for r in wb.worksheets[0].iter_rows(min_row=2, values_only=True) if r and r[0]]
    vaicajumi = {}
    for r in rindas:
        a = seveso_adrese(str(r[2]))
        if a:
            vaicajumi.setdefault(a[0], [])
    rucini_ar = {norm(k): v for k, v in RUCINI.items()}
    rucini = {kods: None for kods, _ in RUCINI.values()}
    for kods, std, lat, lon in vzd_rindas(kese):
        if kods in rucini:
            rucini[kods] = (lat, lon, std)
        daļas = std.split(",")
        k = atslega(daļas[0])
        if k in vaicajumi:
            vaicajumi[k].append((lat, lon, kods, std, {atslega(x) for x in daļas[1:]}))
    features, neatrasti = [], []
    for r in rindas:
        nos = " ".join(str(r[0]).split()).strip().rstrip(",")
        nos = nos.replace(",+A15", "")  # avota drukas kļūda ("Vitol Terminal Latvia,+A15 SIA")
        vieta = " ".join(str(r[2]).replace(" ", " ").split())
        a = seveso_adrese(str(r[2]))
        g = next((c for c in vaicajumi.get(a[0], []) if a[1] & c[4]), None) if a else None
        if g:
            lat, lon, kods, std, _ = g
            metode, adr = "VZD adrešu reģistrs", std
        elif norm(nos) in rucini_ar and rucini[rucini_ar[norm(nos)][0]]:
            kods, pamats = rucini_ar[norm(nos)]
            lat, lon, std = rucini[kods]
            metode, adr = f"VZD adrešu reģistrs, pēc kodes: {pamats}", vieta
        else:
            neatrasti.append((nos, vieta))
            continue
        tips = str(r[4]).strip()
        features.append(feature((lat, lon), {
            "kategorija": "bistams_objekts",
            "id": f"seveso-{re.sub(r'[^0-9]', '', str(r[1]))}-{zlib.crc32(vieta.encode()):08x}",  # reģ. nr + vietas jaucējkods: stabils
            "nosaukums": nos,
            "adrese": adr,
            "veids": "Seveso III: augstākā līmeņa uzņēmums (drošības pārskats)" if tips == "DP"
            else "Seveso III: zemākā līmeņa uzņēmums (avāriju novēršanas programma)",
            "seveso_limenis": "augstākais" if tips == "DP" else "zemākais",
            "objekta_vieta_avota": vieta,
            "bistamas_vielas": " ".join(str(r[3] or "").split()),
            "reg_nr": str(r[1]),
            "vzd_kods": kods,
            "geokodesana": metode,
        }))
    rakstit(DATI / "bistami_seveso.geojson", features)
    print(f"bistami_seveso.geojson: {len(features)} no {len(rindas)}; neatrasti: {neatrasti}")
    return not neatrasti


# ---------- E-PRTR ----------

def teksts(el, ceļš):
    x = el.find(ceļš, NS)
    return " ".join((x.text or "").split()) if x is not None and x.text else ""


def eprtr(kese):
    gml = lejupielade(EPRTR_URL, kese / "eprtr.gml")
    saknes = ET.parse(gml).getroot()
    features = []
    for fm in saknes.findall("gml:featureMember", NS):
        f = fm.find("EUReg:ProductionFacility", NS)
        if f is None:
            continue
        statuss = f.find("pf:status/pf:StatusType/pf:statusType", NS)
        stat = (statuss.get(XLINK) if statuss is not None else "").rsplit("/", 1)[-1]
        if stat != "functional":
            continue
        pos = f.find("act:geometry/gml:Point/gml:pos", NS)
        if pos is None or not pos.text:
            continue
        lat, lon = (float(x) for x in pos.text.split())  # EPSG:4258: platums, garums
        if not ieksa_latvija(lat, lon):
            continue
        lokalais = teksts(f, "act:inspireId/base:Identifier/base:localId")
        a = f.find("EUReg:address/EUReg:AddressDetails", NS)
        iela = " ".join(x for x in (teksts(a, "EUReg:streetName"), "" if teksts(a, "EUReg:buildingNumber") in ("", "0")
                                    else teksts(a, "EUReg:buildingNumber")) if x) if a is not None else ""
        adrese = ", ".join(x for x in (iela, teksts(a, "EUReg:city") if a is not None else "") if x)
        darb = f.find("EUReg:EPRTRAnnexIActivity/EUReg:EPRTRAnnexIActivityType/EUReg:mainActivity", NS)
        kods = darb.get(XLINK).rsplit("/", 1)[-1] if darb is not None and darb.get(XLINK) else ""
        mate = teksts(f, "EUReg:parentCompany/EUReg:ParentCompanyDetails/EUReg:parentCompanyName")
        url = teksts(f, "EUReg:parentCompany/EUReg:ParentCompanyDetails/EUReg:parentCompanyURL")
        ip = {"kategorija": "bistams_objekts", "id": lokalais.removesuffix(".Facility"),
              "nosaukums": teksts(f, "EUReg:facilityName/EUReg:FeatureName/EUReg:nameOfFeature"),
              "adrese": adrese, "veids": "Rūpnieciskā ražotne (E-PRTR / IED)"}
        if kods:
            ip["darbibas_kods"] = kods
            ip["darbiba"] = DARBIBAS.get(kods) or ("IED I pielikuma darbība " if "." in kods else "E-PRTR I pielikuma darbība ") + kods
        if mate:
            ip["uznemums"] = mate
        if url.startswith("http"):
            ip["majaslapa"] = url
        features.append(feature((lat, lon), ip))
    rakstit(DATI / "bistami_eprtr.geojson", features)
    print(f"bistami_eprtr.geojson: {len(features)}")
    return True


# ---------- Sociālo pakalpojumu sniedzēji ----------

IZSLEGT_STATUSI = {"privātuzņēmējs", "individuālais komersants", "fiziska persona", "zemnieku saimniecība"}


def soc(kese):
    dati = json.loads(lejupielade(SOC_URL, kese / "soc.json").read_text(encoding="utf-8"))["data"]
    aktivie = [x for x in dati if x.get("Statuss") == "Sniedz"
               and (x.get("JuridiskaisStatuss") or "").strip().lower() not in IZSLEGT_STATUSI]
    vajag = {x["FaktiskaAdrese"]["VZDKods"] for x in aktivie if (x.get("FaktiskaAdrese") or {}).get("VZDKods")}
    koord = vzd_koordinatas(kese, vajag)
    features, neatrasti = [], []
    for x in aktivie:
        fa = x.get("FaktiskaAdrese") or {}
        g = koord.get(fa.get("VZDKods"))
        if not g:
            neatrasti.append((x["PakalpojumaSniedzejaNosaukums"], fa.get("Adrese")))
            continue
        nr = x["PakalpojumaSniedzejaRegistracijasNumurs"]
        ip = {"kategorija": "soc_pakalpojumi", "id": str(nr),
              "nosaukums": " ".join(x["PakalpojumaSniedzejaNosaukums"].split()),
              "adrese": fa.get("Adrese") or g[2],
              "pakalpojums": (x.get("SniedzamaPakalpojumaNosaukums") or "").strip(),
              "pakalpojuma_forma": x.get("PakalpojumaSniegsanasForma"),
              "izmitinasana": "izmitināšana" if "ar izmit" in (x.get("PakalpojumaSniegsanasForma") or "") else None,
              "planotais_klientu_skaits": x.get("PlanotaisKlientuSkaits"),
              "klienti": (x.get("KlientiPecVecumaUnDzimuma") or "").strip(" ."),
              "klientu_grupas": [k["KlientuGrupasNosaukums"] for k in x.get("KlientuGrupas") or []],
              "juridiskais_statuss": (x.get("JuridiskaisStatuss") or "").strip(),
              "vzd_kods": fa["VZDKods"]}
        # tikai iestādes tīmekļvietne (nevis tālrunis, e-pasts vai vadītāja vārds)
        lapa = next((m.get("MajasLapa", "").strip() for m in (x.get("KontaktInformacija") or {}).get("MajasLapas") or []
                     if m.get("MajasLapa")), "")
        if lapa:
            ip["majaslapa"] = lapa if lapa.startswith("http") else "https://" + lapa
        ip ={k: v for k, v in ip.items() if v not in (None, "", [])}
        features.append(feature((g[0], g[1]), ip))
    rakstit(DATI / "soc_pakalpojumi.geojson", features)
    print(f"soc_pakalpojumi.geojson: {len(features)} no {len(aktivie)} aktīvajiem ({len(dati)} reģistrā); neatrasti: {neatrasti}")
    return not neatrasti


def main():
    arg = sys.argv[1:]
    kese = pathlib.Path(os.environ.get("MAP_CACHE") or "kese")
    if "--kese" in arg:
        i = arg.index("--kese")
        kese = pathlib.Path(arg[i + 1])
        del arg[i:i + 2]
    darbi = {"bistami": (seveso, eprtr), "soc": (soc,)}
    if not arg or any(a not in darbi for a in arg):
        sys.exit(f"lietošana: bistami_soc.py [--kese MAPE] {' '.join(darbi)}")
    ok = True
    for a in arg:
        for f in darbi[a]:
            ok = f(kese) and ok
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
