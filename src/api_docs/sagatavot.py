"""Atvērtā API dokumentācija: production/api.html un production/openapi.json no SPEC (zemāk) + dzīviem piemēriem.

Katram GET galapunktam vienreiz pieprasa piemēru no https://map.repo.lv (≈ 25 pieprasījumi, kešotie dati), saīsina
atbildi un ieliek lapā. Pārbauda, vai SPEC apraksta visus maršrutus no karte_api.py (MARSRUTI) — jaunu galapunktu bez
apraksta skripts neļauj.

  uv run --no-project --python 3.12 src/api_docs/sagatavot.py [--bez-piemeriem]
"""

import argparse
import html
import json
import pathlib
import re
import sys
import urllib.parse
import urllib.request

SAKNE = pathlib.Path(__file__).resolve().parents[2]
API_FAILS = SAKNE / "src" / "karte" / "api" / "karte_api.py"
BAZE = "https://map.repo.lv"

CC0 = ("CC0 1.0", "https://creativecommons.org/publicdomain/zero/1.0/")
CCBY = ("CC BY 4.0", "https://creativecommons.org/licenses/by/4.0/")
ODBL = ("ODbL 1.0", "https://opendatacommons.org/licenses/odbl/1-0/")
MUSU = ("map.repo.lv (atvasināti dati)", "https://github.com/noiseparty/hakatons", *CCBY)
LVGMC = "Latvijas Vides, ģeoloģijas un meteoroloģijas centrs"

LAT = ("lat", "number", "platums (WGS-84), Latvijā 55–59", "56.8166")
LON = ("lon", "number", "garums (WGS-84), Latvijā 20–29", "24.6046")

# ceļš, virsraksts, apraksts, parametri [(vārds, tips, apraksts, piemērs, obligāts)], piemēra vaicājums,
# avoti [(nosaukums, saite, licence, licences saite)], piezīme
SPEC = [
    ("/api/kategorijas", "Kartes slāņi", "Visi slāņi ar objektu skaitu, krāsu, grupu un avotu kodiem.", [], "",
     [MUSU], "Avotu licences: /api/avoti."),
    ("/api/avoti", "Datu avoti", "Katrs avots: izdevējs, licence, datu kopas saite, ieguve, kā lietots kartē, objektu skaits un ielādes laiks.",
     [], "", [MUSU], "Avots bez atvērtas licences: atverts = false (112.lv patvertnes)."),
    ("/api/regioni", "Pašvaldības un pilsētas", "Novadi, valstspilsētas un pilsētas ar kodu (VZD adrešu reģistrs) un bbox, bez ģeometrijas.",
     [], "", [("VZD Valsts adrešu reģistra atvērtie dati", "https://data.gov.lv/dati/lv/dataset/varis-atvertie-dati", *CCBY)], None),
    ("/api/regioni/{kods}", "Reģiona robeža", "Viena reģiona robeža kā GeoJSON Feature (vienkāršota ~50 m).",
     [("kods", "string", "reģiona kods no /api/regioni (ceļā)", "100016688", True)], "/api/regioni/100016688",
     [("VZD Valsts adrešu reģistra atvērtie dati", "https://data.gov.lv/dati/lv/dataset/varis-atvertie-dati", *CCBY)], None),
    ("/api/objekti", "Punkti kartē", "Kartes objekti (GeoJSON FeatureCollection). Ar lat/lon — sakārtoti pēc attāluma, ar attalums_m.",
     [("kategorijas", "string", "slāņu kodi ar komatu (no /api/kategorijas)", "patvertne,evakuacijas_punkts", False),
      ("regions", "string", "tikai šajā reģionā (kods)", "", False), (*LAT, False), (*LON, False),
      ("bbox", "string", "kartes skats minLon,minLat,maxLon,maxLat: tikai punkti taisnstūrī, īsās īpašības (ko rāda "
       "punkta logs), ≤ 5000; ja vairāk — izlase pa slāņiem un \"apgriezts\": true", "24.55,56.80,24.66,56.84", False),
      ("limit", "integer", "cik punktu (1–20000, ar bbox ≤ 5000; noklusēti 5000)", "3", False)],
     "?kategorijas=evakuacijas_punkts&lat=56.8166&lon=24.6046&limit=2",
     [("Katram punktam savs avots (properties.avots)", "/api/avoti", "skat. /api/avoti", None)],
     "Licence katram punktam pēc avota: CC0 (IeM IC, ZVA, LVĢMC), CC BY 4.0 (VZD), ODbL (OSM), oficiāli dokumenti "
     "(CA plāni); 112.lv patvertnēm licence nav norādīta."),
    ("/api/adreses", "Adrešu meklēšana", "VZD adreses ar koordinātām; bez garumzīmēm, pēc vārdu daļām; mājas numurs augstāk.",
     [("q", "string", "adrese vai tās daļa (vismaz viens vārds ar 3+ burtiem)", "brivibas 15 ogre", True),
      ("limit", "integer", "1–20, noklusēti 8", "2", False)], "?q=brivibas%2015%20ogre&limit=2",
     [("VZD Valsts adrešu reģistra atvērtie dati", "https://data.gov.lv/dati/lv/dataset/varis-atvertie-dati", *CCBY)], None),
    ("/api/adreses/tuvaka", "Tuvākā adrese", "Tuvākā VZD adrese punktam (≤ 300 m), citādi {}.", [(*LAT, True), (*LON, True)],
     "?lat=56.8166&lon=24.6046",
     [("VZD Valsts adrešu reģistra atvērtie dati", "https://data.gov.lv/dati/lv/dataset/varis-atvertie-dati", *CCBY)], None),
    ("/api/pasvaldiba", "Pašvaldība punktā", "Pašvaldība (novads vai valstspilsēta): CA plāna saite, tīmekļvietne, VPVKAC kontakts.",
     [(*LAT, True), (*LON, True)], "?lat=56.8166&lon=24.6046",
     [("Pašvaldību CA plāni (oficiāli dokumenti)", "https://github.com/lata-org/ai-open-data-2026-hakatons/tree/main/ca-plani-hakatons",
       "Oficiāls dokuments", "https://likumi.lv/ta/id/5138-autortiesibu-likums"),
      ("VPVKAC paplašinātā tīkla kontaktpunkti (2022)", "https://data.gov.lv/dati/lv/dataset/vpvkac-kontakti", *CC0), MUSU],
     "VPVKAC dati ir no 2022. gada; valstspilsētām tādu nav."),
    ("/api/bridinajumi", "LVĢMC brīdinājumi", "Spēkā esošie hidrometeoroloģiskie brīdinājumi; ar lat/lon — attiecas: vai punkts ir brīdinājuma poligonā.",
     [(*LAT, False), (*LON, False)], "?lat=56.8166&lon=24.6046",
     [("LVĢMC hidrometeoroloģiskie brīdinājumi", "https://data.gov.lv/dati/lv/dataset/hidrometeorologiskie-bridinajumi", *CC0)],
     "Laiki — Latvijas vietējie."),
    ("/api/pludi", "Plūdu riska zona punktā", "Vai punkts ir applūstošā teritorijā (pavasara pali, ledus sastrēgumi, jūras vējuzplūdi; 10 %, 1 %, 0,5 % varbūtība gadā).",
     [(*LAT, True), (*LON, True)], "?lat=56.81096&lon=24.61059",
     [("LVĢMC 3. cikla plūdu riska kartes (WMS, ĢeoLatvija.lv)", "https://data.gov.lv/dati/lv/dataset/3-cikla-latvijas-pldu-postjumu-vietu-un-pldu-riska-kartes1", *CC0)],
     "Avots atbild 1–30 s: ja ne 25 s laikā — HTTP 202 {ielade: true}, mēģiniet pēc 10 s. Kešs pēc punkta (~100 m) 24 h."),
    ("/api/udens", "Ūdens līmenis upēs", "Tuvākās LVĢMC hidroloģiskās stacijas: līmenis (cm virs posteņa nulles), izmaiņa 24 h, prognoze 7 dienām.",
     [(*LAT, True), (*LON, True), ("limit", "integer", "1–10, noklusēti 3", "1", False)], "?lat=56.8166&lon=24.6046&limit=2",
     [("LVĢMC hidroloģiskie novērojumi", "https://data.gov.lv/dati/lv/dataset/hidrometeorologiskie-noverojumi", *CC0),
      ("LVĢMC hidroloģiskās prognozes", "https://data.gov.lv/dati/lv/dataset/hidrologiskas-prognozes", *CC0)],
     "Bīstamības līmeņi nav atvērtie dati, tāpēc to nav. Prognoze ir ~35 no 74 stacijām."),
    ("/api/prognozes", "Laika prognoze pa novadiem", "LVĢMC prognozes apdzīvotām vietām, apkopotas pa novadiem 3 dienām, + ziņas un brīdinājumu poligoni.",
     [], "", [("LVĢMC meteoroloģiskās prognozes apdzīvotām vietām", "https://data.gov.lv/dati/lv/dataset/meteorologiskas-prognozes-apdzivotam-vietam-jaunaka-datu-kopa", *CC0)],
     "Sliekšņi ziņām ir tuvināti LVĢMC kritērijiem, tie nav oficiāli brīdinājumi."),
    ("/api/prognozes/robezas", "Novadu robežas prognozei", "Vienkāršotas novadu un valstspilsētu robežas (GeoJSON) kartes iekrāsošanai.", [], "",
     [("VZD Valsts adrešu reģistra atvērtie dati", "https://data.gov.lv/dati/lv/dataset/varis-atvertie-dati", *CCBY)], None),
    ("/api/zibens", "Zibens", "Zibens izlādes pēdējās 30 min Latvijas apgabalā + LVĢMC 24 h zibens režģis.", [], "",
     [("Ilmatieteen laitos (FMI) atvērtie dati", "https://en.ilmatieteenlaitos.fi/open-data", *CCBY),
      ("LVĢMC telpiskie novērojumi (zibens režģis)", "https://data.gov.lv/dati/lv/dataset/telpiskie-hidrometeorologiskie-noverojumi", *CC0)], None),
    ("/api/augsne", "Nokrišņi un augsnes mitrums", "Nokrišņi pēdējās 26 dienās un nākamajās 3, augsnes mitrums 3–9 cm (modeļa dati, nav brīdinājums).",
     [(*LAT, True), (*LON, True)], "?lat=56.8166&lon=24.6046", [("Open-Meteo", "https://open-meteo.com/", *CCBY)], None),
    ("/api/marsruts", "Maršruts", "Kājām vai ar auto, var apiet slēgtas zonas (izvairities).",
     [("no", "string", "sākums lat,lon", "56.8166,24.6046", True), ("uz", "string", "galamērķis lat,lon", "56.8139,24.6093", True),
      ("veids", "string", "kajam (noklusēti) vai auto", "kajam", False),
      ("izvairities", "string", "zonas: c:lat,lon,r_m vai poligons lat,lon;lat,lon;… atdalītas ar |", "", False)],
     "?no=56.8166,24.6046&uz=56.8139,24.6093&veids=kajam",
     [("FOSSGIS OSRM (routing.openstreetmap.de), OpenStreetMap dati", "https://routing.openstreetmap.de/about.html", *ODBL)],
     "Līdz 60 km. Lūdzu, nelietojiet masveidā — FOSSGIS serveris ir bezmaksas."),
    ("/api/noverojumi", "Laikapstākļi tagad", "LVĢMC meteostaciju jaunākās brāzmas, vējš, temperatūra, nokrišņi; ar lat/lon — tuvākās.",
     [(*LAT, False), (*LON, False), ("limit", "integer", "1–100", "2", False)], "?lat=56.8166&lon=24.6046&limit=2",
     [("LVĢMC meteoroloģiskie operatīvie dati", "https://data.gov.lv/dati/lv/dataset/hidrometeorologiskie-noverojumi", *CC0)], None),
    ("/api/celi", "Ceļu slēgumi un negadījumi", "Spēkā esošie un plānotie notikumi uz valsts autoceļiem: negadījumi, remontdarbi, slidens ceļš.",
     [("bbox", "string", "minLon,minLat,maxLon,maxLat", "", False), (*LAT, False), (*LON, False),
      ("r", "number", "rādiuss metros (100–100000) ap lat/lon", "5000", False)], "?lat=56.8166&lon=24.6046&r=20000",
     [("LVC DATEX II caur Nacionālo piekļuves punktu", "https://transportdata.gov.lv/", *CC0)], None),
    ("/api/satiksme", "Satiksme zonās", "Satiksmes līmenis pa pašvaldībām no uzskaites iekārtām (minūšu ātrums), slidenā ceļa vietas, robežu gaidīšana.",
     [], "", [("LVC satiksmes intensitāte un ātrums, slidens ceļš (NAP)", "https://transportdata.gov.lv/", *CC0), MUSU],
     "Brīvas plūsmas ātrums ir novērtējums; zonu apkopojums — atvasināti dati (CC BY 4.0)."),
    ("/api/statuss", "Sistēmas statuss", "Vietnes, API un katra datu avota stāvoklis, 24 h pa 15 min, pieejamība 7 dienās.", [], "", [MUSU], None),
    ("/api/meklejumi/top", "Biežāk meklētais", "Biežāk meklētie atpazītie vaicājumi pēdējās 14 dienās (bez lietotāju datiem).",
     [("n", "integer", "1–10, noklusēti 3", "5", False)], "?n=5", [MUSU], None),
    ("/api/zinojumi", "Iedzīvotāju ziņojumi", "Apstiprinātie iedzīvotāju ziņojumi (nav oficiāla informācija) pēdējās dienās.",
     [("dienas", "integer", "1–7", "7", False), ("bbox", "string", "minLon,minLat,maxLon,maxLat", "", False)], "",
     [("Iedzīvotāju ziņojumi (map.repo.lv)", "https://map.repo.lv/", *CCBY)], "Ja apdraudēta dzīvība, zvaniet 112."),
    ("/api/plusma.xml", "Abonēt: Atom/RSS plūsma", "Pašvaldības (vai visas Latvijas) situācija kā Atom 1.0 plūsma jebkurai RSS "
     "lietotnei: LVĢMC brīdinājumi, rītdienas prognoze (brāzmas ≥ 15 m/s vai nokrišņi ≥ 15 mm), upes, kas 24 h kāpušas > 10 cm, "
     "LVC slēgumi un negadījumi, zibens pēdējās 30 min. Katrā ierakstā avots un licence; ieraksta <id> ir stabils.",
     [("regions", "string", "pašvaldības VZD kods (no /api/regioni) vai ATVK; bez tā — visa Latvija", "100016688", False)],
     "?regions=100016688",
     [("LVĢMC brīdinājumi, prognozes, hidroloģiskie novērojumi", "https://data.gov.lv/dati/lv/organization/lvgmc", "CC0 1.0", "https://creativecommons.org/publicdomain/zero/1.0/"),
      ("LVC ceļu notikumi (NAP)", "https://transportdata.gov.lv/", "CC0 1.0", "https://creativecommons.org/publicdomain/zero/1.0/"),
      ("FMI zibens", "https://en.ilmatieteenlaitos.fi/open-data", *CCBY), MUSU],
     "application/atom+xml; apkopojums CC BY 4.0, ierakstu dati — avota licence."),
    ("/api/kalendars.ics", "Abonēt: kalendārs", "LVĢMC brīdinājumi pašvaldībai kā iCalendar notikumi (sākums–beigas) — "
     "pievienojiet kā abonētu kalendāru (Google, Apple, Outlook).",
     [("regions", "string", "pašvaldības VZD kods vai ATVK; bez tā — visa Latvija", "100016688", False)], "?regions=100016688",
     [("LVĢMC hidrometeoroloģiskie brīdinājumi", "https://data.gov.lv/dati/lv/dataset/hidrometeorologiskie-bridinajumi", "CC0 1.0", "https://creativecommons.org/publicdomain/zero/1.0/")],
     "text/calendar; laiki UTC; UID stabils (brīdinājuma id + reģions)."),
    ("/api/veseliba", "Veselības pārbaude", "Vai API un datubāze atbild; ar statistika=1 — keša un datubāzes skaitītāji (skat. zemāk).",
     [("statistika", "integer", "1 — pievienot skaitītājus", "1", False)], "?statistika=1", [MUSU], None),
]

POST = [
    ("/api/meklejumi", "biežāk meklētā skaitītājs (tikai atpazīti vaicājumi, bez lietotāju datiem)"),
    ("/api/zinojumi", "jauns iedzīvotāja ziņojums (moderēts)"),
    ("/api/zinojumi/moderacija, /api/zinojumi/{id}/{darbība}", "moderēšana (ar atslēgu)"),
]


def marsruti():
    """karte_api.py GET maršruti → {ceļš (ar {..} parametriem): kešs sekundēs}."""
    teksts = API_FAILS.read_text(encoding="utf-8")
    bloks = teksts[teksts.index("MARSRUTI = ["):teksts.index("POST_MARSRUTI")]
    rez = {}
    for raksts, kesot in re.findall(r're\.compile\(r"\^([^"]+)\$"\), \w+, (\d+)\)', bloks):
        cels = raksts.replace("/?", "").replace("([^/]+)", "{kods}").replace("\\.", ".")
        rez[cels] = int(kesot)
    return rez


def saisinat(v, dzilums=0):
    """Piemēra atbilde lapai: saraksti līdz 2 elementiem (+ cik vēl), skaitļu saraksti līdz 4, teksti līdz 140 zīmēm."""
    if isinstance(v, list):
        if v and all(isinstance(x, (int, float)) for x in v):
            return v[:4] + ([f"… (+{len(v) - 4})"] if len(v) > 4 else [])
        if dzilums > 5:
            return [f"… ({len(v)})"]
        return [saisinat(x, dzilums + 1) for x in v[:2]] + ([f"… (+{len(v) - 2})"] if len(v) > 2 else [])
    if isinstance(v, dict):
        if dzilums > 6:
            return {"…": f"{len(v)} lauki"}
        if len(v) > 15:  # vārdnīca pēc kodiem (piem., novadi): pirmie 3 + cik vēl
            pirmie = dict(list(v.items())[:3])
            return {**{k: saisinat(x, dzilums + 1) for k, x in pirmie.items()}, "…": f"+{len(v) - 3} lauki"}
        return {k: saisinat(x, dzilums + 1) for k, x in v.items()}
    if isinstance(v, str) and len(v) > 140:
        return v[:140] + "…"
    return v


PARAUGI = SAKNE / "src" / "api_docs" / "paraugi"


def paraugs(cels):
    """Saglabāts paraugs (izdomāti dati) galapunktam, kas vēl nav dzīvajā vietnē."""
    f = PARAUGI / (cels.rsplit("/", 1)[-1] + ".txt")
    return f.read_text(encoding="utf-8") if f.exists() else None


def piemers(cels, vaicajums):
    url = BAZE + (vaicajums if vaicajums.startswith("/api/") else cels + vaicajums)
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "map.repo.lv api_docs"}), timeout=40) as r:
            saturs = r.read()
            if "json" not in (r.headers.get("Content-Type") or ""):  # Atom, iCalendar: pirmās rindas
                return url, r.status, "\n".join(saturs.decode("utf-8", "replace").splitlines()[:28]) + "\n…"
            return url, r.status, saisinat(json.loads(saturs))
    except urllib.error.HTTPError as e:
        if e.code == 404 and paraugs(cels):
            return url, "paraugs (izdomāti dati; dzīvajā vietnē vēl nav)", paraugs(cels)
        try:
            return url, e.code, saisinat(json.loads(e.read()))
        except ValueError:
            return url, e.code, None
    except Exception as e:  # noqa: BLE001
        return url, None, {"kluda": str(e)}


def lic(avots):
    nos, url, licence, lurl = avots
    n = f'<a href="{html.escape(url)}">{html.escape(nos)}</a>' if url and url.startswith(("http", "/")) else html.escape(nos)
    l = f'<a href="{html.escape(lurl)}">{html.escape(licence)}</a>' if lurl else html.escape(licence)
    return f"{n} · {l}"


def kesas_teksts(s):
    if s == 0:
        return "nekešo"
    return f"{s} s" if s < 120 else f"{s // 60} min" if s < 7200 else f"{s // 3600} h"


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--bez-piemeriem", action="store_true")
    args = a.parse_args()

    kesas = marsruti()
    aprakstiti = {s[0] for s in SPEC}
    trukst = sorted(set(kesas) - aprakstiti)
    lieki = sorted(aprakstiti - set(kesas))
    if trukst or lieki:
        sys.exit(f"SPEC neatbilst karte_api.py MARSRUTI: trūkst {trukst}, lieki {lieki}")

    kartites, openapi_celi = [], {}
    for cels, virsraksts, apraksts, param, vaicajums, avoti, piezime in SPEC:
        url, statuss, atbilde = (None, None, None) if args.bez_piemeriem else piemers(cels, vaicajums)
        print(f"{cels}: {statuss}", file=sys.stderr)
        pid = re.sub(r"[^a-z0-9]+", "-", cels.lower()).strip("-")
        rindas = "".join(
            f"<tr><td><code>{html.escape(p[0])}</code>{'' if not (len(p) > 4 and p[4]) else ' <small>obligāts</small>'}</td>"
            f"<td>{html.escape(p[1])}</td><td>{html.escape(p[2])}</td></tr>" for p in param)
        piem_url = url or (BAZE + (vaicajums if vaicajums.startswith("/api/") else cels + vaicajums))
        kartites.append(f"""
<section class="galapunkts" id="{pid}">
  <h2><span class="metode">GET</span> <code>{html.escape(cels)}</code> — {html.escape(virsraksts)}</h2>
  <p>{html.escape(apraksts)}</p>
  {f'<table><thead><tr><th>Parametrs</th><th>Tips</th><th>Nozīme</th></tr></thead><tbody>{rindas}</tbody></table>' if param else ''}
  <p class="meta"><b>Avots un licence:</b> {' ; '.join(lic(x) for x in avoti)}<br>
     <b>Kešs:</b> {kesas_teksts(kesas[cels])} (Cache-Control) {f'<br><b>Piezīme:</b> {html.escape(piezime)}' if piezime else ''}</p>
  <p class="piemers"><b>Piemērs:</b> <a href="{html.escape(piem_url)}"><code>{html.escape(piem_url.replace(BAZE, ''))}</code></a>
    {f'<span class="statuss">{"HTTP " if isinstance(statuss, int) else ""}{html.escape(str(statuss))}</span>' if statuss else ''}</p>
  {f'<details><summary>Atbildes piemērs (saīsināts)</summary><pre>{html.escape(atbilde if isinstance(atbilde, str) else json.dumps(atbilde, ensure_ascii=False, indent=1))}</pre></details>' if atbilde is not None else ''}
</section>""")
        oparam = []
        for p in param:
            vards, tips, nozime, piem = p[:4]
            obligats = len(p) > 4 and p[4]
            oparam.append({"name": vards, "in": "path" if "{" + vards + "}" in cels else "query", "required": bool(obligats) or "{" + vards + "}" in cels,
                           "description": nozime, "schema": {"type": tips}, **({"example": piem} if piem else {})})
        openapi_celi[cels] = {"get": {
            "summary": virsraksts, "description": apraksts + (f"\n\n{piezime}" if piezime else ""), "parameters": oparam,
            "x-avoti": [{"nosaukums": x[0], "url": x[1], "licence": x[2]} for x in avoti], "x-kesa-sekundes": kesas[cels],
            "responses": {"200": ({"description": "Atom 1.0", "content": {"application/atom+xml": {}}} if cels.endswith(".xml") else
                                  {"description": "iCalendar", "content": {"text/calendar": {}}} if cels.endswith(".ics") else
                                  {"description": "JSON", "content": {"application/json": (
                                      {"example": atbilde} if atbilde is not None and statuss == 200 else {})}}),
                **({"202": {"description": "Avots vēl rēķina: {ielade: true}, mēģiniet pēc 10 s"}} if cels == "/api/pludi" else {}),
                "400": {"description": "Nederīgs parametrs: {kluda}"}, "503": {"description": "Avots vai datubāze nav pieejama: {kluda}"}}}}

    openapi = {
        "openapi": "3.1.0",
        "info": {"title": "map.repo.lv krīzes kartes API", "version": "2026-10-10",
                 "description": "Atvērts API: tuvākās drošās vietas, brīdinājumi, plūdu risks, ūdens līmenis, ceļi un satiksme no "
                                "Latvijas atvērtajiem datiem. Katram galapunktam avots un licence laukā x-avoti. Mūsu atvasinātie "
                                "dati — CC BY 4.0; caurlaistie dati — avota licence. Dokumentācija: https://map.repo.lv/api.html",
                 "license": {"name": "CC BY 4.0 (atvasinātie dati); avotu licences — x-avoti", "url": CCBY[1]},
                 "contact": {"url": "https://github.com/noiseparty/hakatons"}},
        "servers": [{"url": BAZE}],
        "paths": openapi_celi,
    }
    (SAKNE / "production" / "openapi.json").write_text(json.dumps(openapi, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")

    saturs = "".join(kartites)
    raditajs = "".join(f'<li><a href="#{re.sub(r"[^a-z0-9]+", "-", s[0].lower()).strip("-")}"><code>{html.escape(s[0])}</code></a> — {html.escape(s[1])}</li>' for s in SPEC)
    post = "".join(f"<li><code>POST {html.escape(c)}</code> — {html.escape(t)}</li>" for c, t in POST)
    lapa = (SAKNE / "src" / "api_docs" / "sablons.html").read_text(encoding="utf-8")
    lapa = lapa.replace("{{RADITAJS}}", raditajs).replace("{{GALAPUNKTI}}", saturs).replace("{{POST}}", post) \
        .replace("{{SKAITS}}", str(len(SPEC)))
    (SAKNE / "production" / "api.html").write_text(lapa, encoding="utf-8", newline="\n")
    print(f"production/api.html, production/openapi.json: {len(SPEC)} galapunkti", file=sys.stderr)


if __name__ == "__main__":
    main()
