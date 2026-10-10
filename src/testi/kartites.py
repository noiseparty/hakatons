"""Rezultātu kartīšu audits "bez strupceļiem" (vērtēšanas kritērijs 4): katrs scenārijs × varianti telefonā (375×740).

    # bez slodzes map.repo.lv: /api no ierakstītām fiksturām (src/testi/fiksturas_ierakstit.py, src/demo/lokali.py)
    uv run --no-project --python 3.12 src/demo/lokali.py --port 8763 --fiksturas src/testi/fiksturas
    uv run --no-project --python 3.12 --with playwright src/testi/kartites.py --url http://127.0.0.1:8763 [--csv kludas.csv]

Bez --url pasniedz šī repo production/ lokāli un /api/* pārsūta uz https://map.repo.lv (simtiem pieprasījumu — tikai, ja
tiešām vajag dzīvos datus). Tikai lasa: POST /api/meklejumi netiek sūtīts; ārējie pieprasījumi (fona kartes flīzes u.c.)
testā tiek atcelti. Pirmo reizi: `uv run --no-project --with playwright playwright install chromium`.

Varianti (--varianti, noklusēti visi trīs; --vietas pieliek vecos 4 vietvārdu punktus "… Rīgā/Ogrē/Rēzeknē/Alūksnes novadā"):
  ar vietu   — atrašanās vieta atļauta (Ogres centrs), vaicājums = pirmais atslēgvārds;
  bez vietas — atrašanās vieta nav zināma, tas pats vaicājums: jābūt pogai "Noteikt manu atrašanās vietu";
  RU         — kā "ar vietu", bet kartītes valoda krievu (localStorage valoda=ru, LV/RU/EN slēdzis).
Kartītei jāatbilst:
  scenārijs   — parādīts tieši šis scenārijs (citādi pirmais atslēgvārds neved uz savu scenāriju);
  lēmums      — ar vietu: lēmuma rinda (112 teksts vai LVĢMC brīdinājums šai vietai) kartītes sākumā;
                bez vietas: 112 teksts vai lūgums noteikt vietu (poga) — bez vietas lēmumu pieņemt nevar;
  darbība     — vismaz viens nākamais solis: maršruta saite, vietas rinda, 112 teksts vai atrašanās vietas poga;
  vietas      — vismaz viena vietas rinda vai skaidrs teksts, ka tuvākā nav zināma (tikai ar vietu);
  avots       — katrai vietas rindai ir avota rinda (datu kopa, izdevējs, licence vai CA plāns ar lappusi);
  padoms, tālāk — padoms un "Kas notiks tālāk";
  teksts      — nav "undefined", "null", "NaN", "[object"; nav tukšu virsrakstu;
  saites      — katra saite kartītē un vietas logā: iekšēja (production/ fails, #id tajā, /api/ galapunkts karte_api.py)
                vai http(s); nekādu tel:, mailto:, javascript:;
  ekrāns      — kartīte un pirmās vietas logs kartē (pēc pieskāriena rindai) ir ekrāna platumā, lapa neritinās uz sāniem;
  slāņi       — katrs scenārija slānis ir /api/kategorijas (citādi tukša sadaļa nedrīkst parādīties);
  JS          — nav JS kļūdu;
  ātrums      — kartīte gatava < 4 s.
Robežgadījumi: nesaprasts vaicājums, vaicājums bez vietas, atrašanās vieta liegta, /api/objekti vai /api/bridinajumi
nedarbojas — katrā jābūt skaidram tekstam (ko darīt tālāk), nevis tukšai vietai.
Kļūdas → CSV (punkts, scenārijs, vaicājums, pārbaude, detaļas); exit 1, ja ir kļūdas.
"""
import argparse
import asyncio
import csv
import functools
import http.server
import json
import pathlib
import re
import socketserver
import sys
import threading
import time
import urllib.parse
import urllib.request

SAKNE = pathlib.Path(__file__).resolve().parents[2]
PROD = SAKNE / "production"
LIVE = "https://map.repo.lv"
OGRE = {"latitude": 56.8162, "longitude": 24.614}
VARIANTI = {
    "ar vietu": {"geo": OGRE, "valoda": None, "pec": ""},
    "bez vietas": {"geo": None, "valoda": None, "pec": ""},
    "RU": {"geo": OGRE, "valoda": "ru", "pec": ""},
}
VIETAS = {"Rīga": "Rīgā", "Ogre": "Ogrē", "Rēzekne": "Rēzeknē", "Alūksnes novads (lauki)": "Alūksnes novadā"}
GATAVS_S = 4.0

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Kartītes stāvoklis pēc meklēšanas (izpilda lapā)
PARBAUDE_JS = r"""() => {
  const k = document.getElementById('rezultati');
  if (!k || k.hidden) return null;
  const t = s => typeof Valoda !== 'undefined' ? Valoda.t(s) : s;
  const vietas = k.querySelector('#rez-vietas');
  const lemums = k.querySelector('#rez-lemums');
  const gaida = (vietas && vietas.textContent.includes(t('Meklē tuvākās vietas…'))) || (lemums && !lemums.textContent.trim())
    || k.textContent.includes(t('Meklē adresi…'));
  const pirmais = [...k.children].find(e => e.textContent.trim() || e.id === 'rez-lemums');
  const virsraksti = [...k.querySelectorAll('h2, h3')].filter(h => !h.textContent.trim()
    || !h.nextElementSibling || !h.nextElementSibling.textContent.trim()).map(h => h.outerHTML.slice(0, 80));
  const rindas = [...k.querySelectorAll('#rez-vietas li[data-lat]')];
  const bezAvota = rindas.filter(li => !li.querySelector('.popup-avots, .ca-avots, .avots-rinda'))
    .map(li => (li.querySelector('b')?.textContent || '?') + ' [' + (JSON.parse(li.dataset.p || '{}').avots || '') + ']');
  const r = k.getBoundingClientRect();
  return {
    gaida, teksts: k.innerText,
    sapratu: k.querySelector('.sapratu b')?.textContent || '',
    pirmais: pirmais ? (pirmais.id || pirmais.className || pirmais.tagName) : '',
    lemums: !!k.querySelector('#rez-lemums .lemums'),
    draudi112: !!k.querySelector('.draudi, .zvanit-teksts'),
    atrastPoga: !!k.querySelector('[data-darbiba="atrast"]'),
    vietuRindas: k.querySelectorAll('#rez-vietas li:not(.tuksa)').length,
    tuksasRindas: k.querySelectorAll('#rez-vietas li.tuksa').length,
    marsrutuSaites: k.querySelectorAll('.marsruts a').length,
    bezAvota,
    padoms: (k.querySelector('.padoms')?.textContent || '').trim().length,
    talak: !!(k.querySelector('.talak h3')?.textContent || '').trim(),
    virsraksti,
    saites: [...k.querySelectorAll('a')].map(a => a.getAttribute('href')),
    platums: { kreisa: Math.round(r.left), laba: Math.round(r.right), ekrans: innerWidth,
               lapa: document.documentElement.scrollWidth,
               plati: [...k.querySelectorAll('*')].filter(e => { const b = e.getBoundingClientRect();
                 return b.width && (b.right > innerWidth + 1 || b.left < -1); }).slice(0, 3)
                 .map(e => e.tagName + '.' + e.className + ' ' + (e.textContent || '').trim().slice(0, 40)) },
  };
}"""
LOGS_JS = r"""() => {
  const p = document.querySelector('.leaflet-popup');
  if (!p) return null;
  const r = p.getBoundingClientRect();
  return { kreisa: Math.round(r.left), laba: Math.round(r.right), augsa: Math.round(r.top), apaksa: Math.round(r.bottom),
           ekrans: innerWidth, augstums: innerHeight, saites: [...p.querySelectorAll('a')].map(a => a.getAttribute('href')),
           teksts: p.innerText };
}"""
NAV_ZINAMA = ("nav zināma", "nav atrasta", "vēl nav", "nav pieejam", "neizdevās ielādēt")
SLIKTI = ("undefined", "null", "NaN", "[object")


def api_marsruti():
    """/api/ ceļu regulārās izteiksmes no karte_api.py (MARSRUTI + flīzes) — iekšējo saišu pārbaudei bez tīkla."""
    t = (SAKNE / "src" / "karte" / "api" / "karte_api.py").read_text(encoding="utf-8")
    return [re.compile(m) for m in re.findall(r're\.compile\(r"(\^/api/[^"]+)"\)', t)]


API_CELI = api_marsruti()
_id_kesa = {}


def saites_kluda(href, bazes_url):
    """None, ja saite der; citādi īss iemesls."""
    if not href or href.startswith("#"):
        return None if href and len(href) > 1 else "tukša saite"
    u = urllib.parse.urlsplit(urllib.parse.urljoin(bazes_url + "/", href))
    if u.scheme not in ("http", "https"):
        return f"nav http(s): {href[:60]}"
    if f"{u.scheme}://{u.netloc}" != bazes_url:
        return None  # ārēja https saite
    cels = urllib.parse.unquote(u.path)
    if cels.startswith("/api/"):
        return None if any(r.match(cels) for r in API_CELI) else f"nav API galapunkta: {cels}"
    fails = PROD / (cels.lstrip("/") or "index.html")
    if fails.is_dir():
        fails = fails / "index.html"
    if not fails.is_file():
        return f"nav faila: {cels}"
    if u.fragment:
        if fails not in _id_kesa:
            _id_kesa[fails] = set(re.findall(r'\bid="([^"]+)"', fails.read_text(encoding="utf-8", errors="ignore")))
        if u.fragment not in _id_kesa[fails]:
            return f"nav #{u.fragment} failā {cels}"
    return None


def lokals_serveris():
    class Klusais(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass
    apstr = functools.partial(Klusais, directory=str(PROD))
    class Serveris(socketserver.ThreadingTCPServer):
        request_queue_size = 128  # noklusētās 5: vairākas cilnes vienlaikus nomet skriptus (ERR_NO_BUFFER_SPACE)
    srv = Serveris(("127.0.0.1", 0), apstr)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{srv.server_address[1]}"


async def konteksts(parluks, bazes_url, proxy, geo=None, valoda=None, liegta=False, bojats=None):
    kw = {"viewport": {"width": 375, "height": 740}, "is_mobile": True, "has_touch": True, "locale": "lv-LV",
          # service worker bloķēts: tas apietu /api pārsūtīšanu un kešotu vecās versijas
          "service_workers": "block"}
    if geo:
        kw.update(permissions=["geolocation"], geolocation=geo)
    elif liegta:
        kw.update(permissions=[])
    ctx = await parluks.new_context(**kw)
    if valoda:
        await ctx.add_init_script(f"try {{ localStorage.setItem('valoda', '{valoda}'); }} catch {{}}")


    async def api(route):
        if route.request.method == "POST":  # /api/meklejumi skaitīšana — nesūtām
            return await route.fulfill(status=204, body="")
        if bojats and bojats in route.request.url:
            return await route.fulfill(status=503, body="")
        if not proxy:
            return await route.continue_()
        try:
            r = await route.fetch(url=LIVE + route.request.url[len(bazes_url):], timeout=60000)
            await route.fulfill(response=r)
        except Exception:  # noqa: BLE001
            try:
                await route.abort()
            except Exception:  # noqa: BLE001
                pass
    # ārējie pieprasījumi (fona kartes flīzes u.c.) — nesūtām: tests nedrīkst slogot citus. Tikai tos (regex), jo
    # visu pieprasījumu pārtveršana Windows Chromium dažkārt nomet lokālos skriptus (net::ERR_NO_BUFFER_SPACE).
    await ctx.route(re.compile(r"^https?://(?!" + re.escape(urllib.parse.urlsplit(bazes_url).netloc) + r"/)"),
                    lambda route: route.abort())
    await ctx.route(f"{bazes_url}/api/**", api)
    return ctx


async def punkts(parluks, bazes_url, proxy, nos, var, scenariji, kategorijas, kludas, stats, args_ekrani=None):
    ctx = await konteksts(parluks, bazes_url, proxy, geo=var["geo"], valoda=var["valoda"])
    lapa = await ctx.new_page()
    js_kludas = []
    lapa.on("pageerror", lambda e: js_kludas.append(str(e)[:160]))
    await lapa.goto(bazes_url + "/", wait_until="networkidle", timeout=60000)
    await lapa.wait_for_function("!document.getElementById('jautajums').disabled && typeof Klasifikators !== 'undefined'", timeout=30000)
    if var["geo"]:
        await lapa.wait_for_function("typeof stavoklis !== 'undefined' && !!stavoklis.vieta", timeout=15000)
    bez_vietas = not var["geo"] and not var["pec"]

    async def meklet(q):
        await lapa.fill("#jautajums", q)
        await lapa.press("#jautajums", "Enter")
        t0 = time.monotonic()
        m, gatavs = None, None
        while time.monotonic() - t0 < 15:
            await lapa.wait_for_timeout(150)
            m = await lapa.evaluate(PARBAUDE_JS)
            if m and not m["gaida"] and m["talak"]:
                gatavs = time.monotonic() - t0
                break
        await lapa.wait_for_timeout(300)  # vēlās rindas (ceļi, satiksme, maršruts) — lai pārbaudes redz arī tās
        return (await lapa.evaluate(PARBAUDE_JS)) or m, gatavs

    await meklet(f"patvertne {var['pec']}".strip())  # iesilda API kešus šai vietai
    for s in scenariji:
        js_kludas.clear()
        q = f"{s['atslegvardi'][0].rstrip('$')} {var['pec']}".strip()
        m, gatavs = await meklet(q)
        problemas = []
        if not m:
            problemas.append(("kartīte", "rezultāts neparādījās"))
        else:
            if m["sapratu"] != s["nosaukums"]:
                problemas.append(("scenārijs", f"parādīts '{m['sapratu']}'"))
            if bez_vietas:
                if not (m["draudi112"] or m["atrastPoga"]):
                    problemas.append(("lēmums", "bez vietas: nav ne 112 teksta, ne pogas noteikt vietu"))
            elif not (m["lemums"] or m["draudi112"]) or m["pirmais"] not in ("rez-lemums", "draudi", "zvanit-teksts"):
                problemas.append(("lēmums", f"pirmais elements: {m['pirmais']}, LVĢMC rinda: {m['lemums']}"))
            if not (m["marsrutuSaites"] or m["vietuRindas"] or m["draudi112"] or m["atrastPoga"]):
                problemas.append(("darbība", "nav ne maršruta, ne vietas, ne 112, ne vietas pogas"))
            if not bez_vietas and not m["vietuRindas"] and not m["tuksasRindas"] and not any(t in m["teksts"] for t in NAV_ZINAMA):
                problemas.append(("vietas", "nav ne vietas, ne teksta, ka tuvākā nav zināma"))
            if m["bezAvota"]:
                problemas.append(("avots", f"{len(m['bezAvota'])} vietām nav avota rindas: {m['bezAvota'][:3]}"))
            if not m["padoms"]:
                problemas.append(("padoms", "nav padoma"))
            if not m["talak"]:
                problemas.append(("tālāk", "nav 'Kas notiks tālāk'"))
            slikti = [t for t in SLIKTI if t in m["teksts"]]
            if slikti:
                i = m["teksts"].find(slikti[0])
                problemas.append(("teksts", f"{slikti}: …{m['teksts'][max(0, i - 40):i + 30]!r}…"))
            if m["virsraksti"]:
                problemas.append(("virsraksts", f"tukšs virsraksts vai sadaļa: {m['virsraksti'][:2]}"))
            sl = sorted({k for h in m["saites"] if (k := saites_kluda(h, bazes_url))})
            if sl:
                problemas.append(("saites", "; ".join(sl[:3])))
            p = m["platums"]
            if p["kreisa"] < 0 or p["laba"] > p["ekrans"] or p["lapa"] > p["ekrans"] or p["plati"]:
                problemas.append(("ekrāns", f"kartīte {p['kreisa']}–{p['laba']} px, lapa {p['lapa']} px, plati: {p['plati']}"))
            # Pirmās vietas logs kartē (pieskāriens rindai): ekrāna platumā, saites derīgas
            rinda = await lapa.query_selector("#rez-vietas li[data-lat]")
            if rinda:
                await lapa.evaluate("document.querySelector('.leaflet-popup-close-button')?.click()")
                await rinda.evaluate("li => li.querySelector('.teksts b, .teksts').click()")
                await lapa.wait_for_timeout(900)  # karte pārvietojas pie vietas (setView + logs autoPan)
                logs = await lapa.evaluate(LOGS_JS)
                if not logs:
                    problemas.append(("logs", "pieskāriens vietas rindai neatvēra logu kartē"))
                else:
                    if logs["kreisa"] < 0 or logs["laba"] > logs["ekrans"]:
                        problemas.append(("ekrāns", f"vietas logs {logs['kreisa']}–{logs['laba']} px (ekrāns {logs['ekrans']})"))
                    sl = sorted({k for h in logs["saites"] if (k := saites_kluda(h, bazes_url))})
                    if sl:
                        problemas.append(("saites", "logā: " + "; ".join(sl[:3])))
                    slikti = [t for t in SLIKTI if t in logs["teksts"]]
                    if slikti:
                        problemas.append(("teksts", f"logā {slikti}: {logs['teksts'][:80]!r}"))
                await lapa.evaluate("document.querySelector('.leaflet-popup-close-button')?.click()")
        trukst = [k for k in s.get("kategorijas", []) if k not in kategorijas]
        if trukst:
            problemas.append(("slāņi", f"nav /api/kategorijas: {trukst}"))
        if js_kludas:
            problemas.append(("JS", "; ".join(js_kludas[:2])))
        if gatavs is None or gatavs > GATAVS_S:
            problemas.append(("ātrums", f"gatava pēc {gatavs:.1f} s" if gatavs else "nav gatava 15 s laikā"))
        stats[nos] += 1
        if problemas and args_ekrani and not any(k["punkts"] == nos for k in kludas):
            await lapa.screenshot(path=str(pathlib.Path(args_ekrani) / f"{nos.split()[0]}_{s['kods']}.png"), full_page=True)
        for p, d in problemas:
            kludas.append({"punkts": nos, "scenārijs": s["kods"], "vaicājums": q, "pārbaude": p, "detaļas": d})
    await ctx.close()


async def robezgadijumi(parluks, bazes_url, proxy, kludas):
    """Strupceļi ārpus parastā ceļa: nesaprasts vaicājums, bez vietas, atrašanās vieta liegta, API kļūdas."""
    gadijumi = [
        # (nosaukums, vaicājums, bojāts API ceļš vai None, ģeolokācija liegta, pēc tam klikšķis, gaidāmie teksti (jebkurš))
        ("nesaprasts vaicājums", "qwzx plnk", None, False, None, ["Nesapratām", "zvaniet 112"]),
        ("bez vietas", "plūdi", None, False, None, ["Noteikt manu atrašanās vietu", "Kas notiks tālāk"]),
        ("vieta liegta", "plūdi", None, True, '[data-darbiba="atrast"]', ["atrašanās viet", "pilsēt"]),
        ("/api/objekti nedarbojas", "patvertne Ogrē", "/api/objekti", False, None, ["neizdevās ielādēt", "nav zināma"]),
        ("/api/bridinajumi nedarbojas", "plūdi Ogrē", "/api/bridinajumi", False, None, ["LVĢMC brīdinājum"]),
    ]
    for nos, q, bojats, liegta, klikskis, gaidits in gadijumi:
        ctx = await konteksts(parluks, bazes_url, proxy, liegta=liegta, bojats=bojats)
        lapa = await ctx.new_page()
        js_kludas = []
        lapa.on("pageerror", lambda e: js_kludas.append(str(e)[:160]))
        await lapa.goto(bazes_url + "/", wait_until="load", timeout=60000)  # ar bojātu API lapa atkārto pieprasījumus
        await lapa.wait_for_function("!document.getElementById('jautajums').disabled && typeof Klasifikators !== 'undefined'", timeout=30000)
        await lapa.wait_for_timeout(2500)
        await lapa.fill("#jautajums", q)
        await lapa.press("#jautajums", "Enter")
        await lapa.wait_for_timeout(5000)
        if klikskis:
            await lapa.click(klikskis)
            await lapa.wait_for_timeout(2500)
        teksts = await lapa.evaluate("document.getElementById('rezultati')?.innerText || ''")
        teksts += " | " + await lapa.evaluate("document.getElementById('vieta-teksts')?.innerText || ''")
        if not any(g.lower() in teksts.lower() for g in gaidits):
            kludas.append({"punkts": "robežgadījums", "scenārijs": nos, "vaicājums": q, "pārbaude": "strupceļš",
                           "detaļas": f"nav neviena no {gaidits}; kartītē: {teksts[:160]!r}"})
        if any(t in teksts for t in SLIKTI):
            kludas.append({"punkts": "robežgadījums", "scenārijs": nos, "vaicājums": q, "pārbaude": "teksts", "detaļas": teksts[:160]})
        if js_kludas:
            kludas.append({"punkts": "robežgadījums", "scenārijs": nos, "vaicājums": q, "pārbaude": "JS", "detaļas": "; ".join(js_kludas[:2])})
        await ctx.close()


async def galvena(args):
    from playwright.async_api import async_playwright
    noteikumi = json.loads((PROD / "scenariji.json").read_text(encoding="utf-8"))
    scenariji = noteikumi["scenariji"][: args.limits] if args.limits else noteikumi["scenariji"]
    if args.scenariji:
        scenariji = [s for s in scenariji if s["kods"] in args.scenariji.split(",")]
    with urllib.request.urlopen(LIVE + "/api/kategorijas" if not args.url else args.url + "/api/kategorijas", timeout=30) as r:
        kategorijas = {k["kods"] for k in json.load(r)}
    srv = None
    if args.url:
        bazes_url, proxy = args.url.rstrip("/"), False
    else:
        srv, bazes_url = lokals_serveris()
        proxy = True
    punkti = {n: VARIANTI[n] for n in args.varianti.split(",") if n}
    if args.vietas:
        punkti |= {n: {"geo": None, "valoda": None, "pec": pec} for n, pec in VIETAS.items()}
    kludas, stats = [], {n: 0 for n in punkti}
    t0 = time.monotonic()
    async with async_playwright() as p:
        parluks = await p.chromium.launch()
        if not args.bez_robezgadijumiem:
            await robezgadijumi(parluks, bazes_url, proxy, kludas)
        await asyncio.gather(*(punkts(parluks, bazes_url, proxy, n, v, scenariji, kategorijas, kludas, stats, args.ekrani)
                               for n, v in punkti.items()))
        await parluks.close()
    if srv:
        srv.shutdown()
    kartites = sum(stats.values())
    rg = [k for k in kludas if k["punkts"] == "robežgadījums"]
    if not args.bez_robezgadijumiem:
        print(f"robežgadījumi: 5, ar kļūdām {len({k['scenārijs'] for k in rg})}")
    kludas_k = [k for k in kludas if k["punkts"] != "robežgadījums"]
    ar_kludu = len({(k["punkts"], k["scenārijs"]) for k in kludas_k})
    print(f"{kartites} kartītes ({len(scenariji)} scenāriji × {len(punkti)} varianti: {', '.join(punkti)}; "
          f"{time.monotonic() - t0:.0f} s): {kartites - ar_kludu} bez kļūdām, {ar_kludu} ar kļūdām")
    for n in punkti:
        print(f"  {n:24} {stats[n] - len({k['scenārijs'] for k in kludas_k if k['punkts'] == n})}/{stats[n]}")
    pa_parbaudem = {}
    for k in kludas:
        pa_parbaudem[k["pārbaude"]] = pa_parbaudem.get(k["pārbaude"], 0) + 1
    for p, n in sorted(pa_parbaudem.items(), key=lambda x: -x[1]):
        piemers = next(k for k in kludas if k["pārbaude"] == p)
        print(f"  {p:11} {n:4}  piem.: {piemers['punkts']} · {piemers['scenārijs']} · {piemers['detaļas'][:110]}")
    if args.csv:
        with open(args.csv, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["punkts", "scenārijs", "vaicājums", "pārbaude", "detaļas"])
            w.writeheader()
            w.writerows(sorted(kludas, key=lambda k: (k["pārbaude"], k["scenārijs"], k["punkts"])))
        print(f"kļūdas: {args.csv}")
    return 1 if kludas else 0


if __name__ == "__main__":
    a = argparse.ArgumentParser()
    a.add_argument("--url", help="pārbaudīt šo vietni (piem. http://127.0.0.1:8763 ar lokali.py --fiksturas), nevis "
                                 "lokālo production/ ar /api no map.repo.lv")
    a.add_argument("--csv", default="kartites_kludas.csv")
    a.add_argument("--ekrani", help="mape: pirmās kļūdainās kartītes ekrānuzņēmums katram variantam")
    a.add_argument("--limits", type=int, default=0, help="tikai pirmie N scenāriji (ātrai pārbaudei)")
    a.add_argument("--scenariji", help="tikai šie scenāriju kodi (ar komatu)")
    a.add_argument("--varianti", default=",".join(VARIANTI), help=f"ar komatu no: {', '.join(VARIANTI)}")
    a.add_argument("--vietas", action="store_true", help="pievienot 4 vietvārdu punktus (… Rīgā/Ogrē/Rēzeknē/Alūksnes novadā)")
    a.add_argument("--bez-robezgadijumiem", action="store_true")
    sys.exit(asyncio.run(galvena(a.parse_args())))
