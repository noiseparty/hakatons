"""Rezultātu kartīšu audits "bez strupceļiem" (vērtēšanas kritērijs 4): katrs scenārijs × 4 vietas telefonā.

    uv run --no-project --python 3.12 --with playwright src/testi/kartites.py [--url https://map.repo.lv] [--csv kludas.csv]

Bez --url pasniedz šī repo production/ lokāli un /api/* pārsūta uz https://map.repo.lv (tā pārbauda nesapludinātas
izmaiņas). Tikai lasa: POST /api/meklejumi netiek sūtīts. Pirmo reizi: `uv run --no-project --with playwright
playwright install chromium`.

Katram scenārijam (production/scenariji.json) vaicājums = pirmais atslēgvārds + vieta (Rīgā, Ogrē, Rēzeknē, Alūksnes
novadā — novada centrs ir lauki), 375×740. Kartītei jāatbilst:
  scenārijs   — parādīts tieši šis scenārijs (citādi pirmais atslēgvārds neved uz savu scenāriju);
  lēmums      — lēmuma rinda (112 teksts vai LVĢMC brīdinājums šai vietai) ir kartītes sākumā;
  vietas      — vismaz viena vietas rinda vai skaidrs teksts, ka tuvākā nav zināma;
  padoms, tālāk — padoms un "Kas notiks tālāk";
  teksts      — nav "undefined", "null", "NaN", "[object"; nav tukšu virsrakstu;
  slāņi       — katrs scenārija slānis ir /api/kategorijas (citādi tukša sadaļa nedrīkst parādīties);
  JS          — nav JS kļūdu;
  ātrums      — kartīte gatava < 4 s (API iesildīts ar pirmo vaicājumu katrā vietā).
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
import socketserver
import sys
import threading
import time
import urllib.request

SAKNE = pathlib.Path(__file__).resolve().parents[2]
LIVE = "https://map.repo.lv"
VIETAS = [("Rīga", "Rīgā"), ("Ogre", "Ogrē"), ("Rēzekne", "Rēzeknē"), ("Alūksnes novads (lauki)", "Alūksnes novadā")]
GATAVS_S = 4.0

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Kartītes stāvoklis pēc meklēšanas (izpilda lapā)
PARBAUDE_JS = r"""() => {
  const k = document.getElementById('rezultati');
  if (!k || k.hidden) return null;
  const vietas = k.querySelector('#rez-vietas');
  const lemums = k.querySelector('#rez-lemums');
  const gaida = (vietas && /Meklē tuvākās vietas/.test(vietas.textContent)) || (lemums && !lemums.textContent.trim())
    || /Meklē adresi/.test(k.textContent);
  const pirmais = [...k.children].find(e => e.textContent.trim() || e.id === 'rez-lemums');
  const virsraksti = [...k.querySelectorAll('h2, h3')].filter(h => !h.textContent.trim()
    || !h.nextElementSibling || !h.nextElementSibling.textContent.trim()).map(h => h.outerHTML.slice(0, 80));
  return {
    gaida, teksts: k.innerText,
    sapratu: k.querySelector('.sapratu b')?.textContent || '',
    pirmais: pirmais ? (pirmais.id || pirmais.className || pirmais.tagName) : '',
    lemums: !!k.querySelector('#rez-lemums .lemums'),
    draudi112: !!k.querySelector('.draudi, .zvanit-teksts'),
    vietuRindas: k.querySelectorAll('#rez-vietas li:not(.tuksa)').length,
    padoms: (k.querySelector('.padoms')?.textContent || '').trim().length,
    talak: /Kas notiks tālāk/.test(k.querySelector('.talak h3')?.textContent || ''),
    virsraksti,
  };
}"""
NAV_ZINAMA = ("nav zināma", "nav atrasta", "vēl nav", "nav pieejam", "neizdevās ielādēt")
SLIKTI = ("undefined", "null", "NaN", "[object")


def lokals_serveris():
    class Klusais(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass
    apstr = functools.partial(Klusais, directory=str(SAKNE / "production"))
    srv = socketserver.ThreadingTCPServer(("127.0.0.1", 0), apstr)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{srv.server_address[1]}"


async def punkts(parluks, bazes_url, proxy, nos, pec, scenariji, kategorijas, kludas, stats, args_ekrani=None):
    # service worker bloķēts: tas apietu /api pārsūtīšanu un kešotu vecās versijas
    ctx = await parluks.new_context(viewport={"width": 375, "height": 740}, is_mobile=True, has_touch=True, locale="lv-LV",
                                    service_workers="block")

    async def api(route):
        if route.request.method == "POST":  # /api/meklejumi skaitīšana — nesūtām
            return await route.fulfill(status=204, body="")
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
    await ctx.route(f"{bazes_url}/api/**", api)
    lapa = await ctx.new_page()
    js_kludas = []
    lapa.on("pageerror", lambda e: js_kludas.append(str(e)[:160]))
    await lapa.goto(bazes_url + "/", wait_until="networkidle", timeout=60000)

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
        await lapa.wait_for_timeout(300)  # vēlās rindas (ceļi, satiksme) — lai teksta pārbaude redz arī tās
        return (await lapa.evaluate(PARBAUDE_JS)) or m, gatavs

    await meklet(f"patvertne {pec}")  # iesilda API kešus šai vietai
    for s in scenariji:
        js_kludas.clear()
        q = f"{s['atslegvardi'][0].rstrip('$')} {pec}"
        m, gatavs = await meklet(q)
        problemas = []
        if not m:
            problemas.append(("kartīte", "rezultāts neparādījās"))
        else:
            if m["sapratu"] != s["nosaukums"]:
                problemas.append(("scenārijs", f"parādīts '{m['sapratu']}'"))
            if not (m["lemums"] or m["draudi112"]) or m["pirmais"] not in ("rez-lemums", "draudi", "zvanit-teksts"):
                problemas.append(("lēmums", f"pirmais elements: {m['pirmais']}, LVĢMC rinda: {m['lemums']}"))
            if not m["vietuRindas"] and not any(t in m["teksts"] for t in NAV_ZINAMA):
                problemas.append(("vietas", "nav ne vietas, ne teksta, ka tuvākā nav zināma"))
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
        ctx = await parluks.new_context(viewport={"width": 375, "height": 740}, is_mobile=True, has_touch=True, locale="lv-LV",
                                        service_workers="block", permissions=[] if liegta else None)

        async def api(route, _req=None, bojats=bojats):
            if route.request.method == "POST":
                return await route.fulfill(status=204, body="")
            if bojats and bojats in route.request.url:
                return await route.fulfill(status=503, body="")
            if not proxy:
                return await route.continue_()
            try:
                await route.fulfill(response=await route.fetch(url=LIVE + route.request.url[len(bazes_url):], timeout=60000))
            except Exception:  # noqa: BLE001
                try:
                    await route.abort()
                except Exception:  # noqa: BLE001
                    pass
        await ctx.route(f"{bazes_url}/api/**", api)
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
    noteikumi = json.loads((SAKNE / "production" / "scenariji.json").read_text(encoding="utf-8"))
    scenariji = noteikumi["scenariji"][: args.limits] if args.limits else noteikumi["scenariji"]
    with urllib.request.urlopen(LIVE + "/api/kategorijas" if not args.url else args.url + "/api/kategorijas", timeout=30) as r:
        kategorijas = {k["kods"] for k in json.load(r)}
    srv = None
    if args.url:
        bazes_url, proxy = args.url.rstrip("/"), False
    else:
        srv, bazes_url = lokals_serveris()
        proxy = True
    kludas, stats = [], {n: 0 for n, _ in VIETAS}
    t0 = time.monotonic()
    async with async_playwright() as p:
        parluks = await p.chromium.launch()
        await robezgadijumi(parluks, bazes_url, proxy, kludas)
        await asyncio.gather(*(punkts(parluks, bazes_url, proxy, n, pec, scenariji, kategorijas, kludas, stats, args.ekrani) for n, pec in VIETAS))
        await parluks.close()
    if srv:
        srv.shutdown()
    kartites = sum(stats.values())
    rg = [k for k in kludas if k["punkts"] == "robežgadījums"]
    print(f"robežgadījumi: 5, ar kļūdām {len({k['scenārijs'] for k in rg})}")
    kludas_k = [k for k in kludas if k["punkts"] != "robežgadījums"]
    ar_kludu = len({(k["punkts"], k["scenārijs"]) for k in kludas_k})
    print(f"{kartites} kartītes ({len(scenariji)} scenāriji × {len(VIETAS)} vietas, {time.monotonic() - t0:.0f} s): "
          f"{kartites - ar_kludu} bez kļūdām, {ar_kludu} ar kļūdām")
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
    a.add_argument("--url", help="pārbaudīt šo vietni (piem. https://map.repo.lv), nevis lokālo production/")
    a.add_argument("--csv", default="kartites_kludas.csv")
    a.add_argument("--ekrani", help="mape: pirmās kļūdainās kartītes ekrānuzņēmums katrai vietai")
    a.add_argument("--limits", type=int, default=0, help="tikai pirmie N scenāriji (ātrai pārbaudei)")
    sys.exit(asyncio.run(galvena(a.parse_args())))
