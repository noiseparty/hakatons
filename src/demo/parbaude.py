"""Demo paneļa pārbaude ar Playwright: katrs scenārijs 375×740 (telefons) un 1280×800, JS kļūdas, ekrānuzņēmumi.

Lokālā production/ (python http.server) + /api/* pārsūtīts uz https://map.repo.lv (dzīvie dati, tikai lasīšana).

    uv run --no-project --with playwright src/demo/parbaude.py [--izvade ekr] [--scenariji vejs,drons]
"""
import argparse
import functools
import http.server
import json
import pathlib
import sys
import threading
import urllib.parse
import urllib.request

from playwright.sync_api import sync_playwright

SAKNE = pathlib.Path(__file__).resolve().parents[2]
PROD = SAKNE / "production"
LIVE = "https://map.repo.lv"


def serveris():
    class Klusais(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass
    h = functools.partial(Klusais, directory=str(PROD))
    s = http.server.ThreadingHTTPServer(("127.0.0.1", 0), h)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    return s


def api(route):
    u = urllib.parse.urlsplit(route.request.url)
    url = LIVE + u.path + ("?" + u.query if u.query else "")
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "demo-parbaude"}), timeout=40) as r:
            route.fulfill(status=r.status, body=r.read(), headers={"content-type": r.headers.get("content-type", "application/json")})
    except urllib.error.HTTPError as e:
        route.fulfill(status=e.code, body=e.read())


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--izvade", default=str(SAKNE / "ekr-demo"))
    a.add_argument("--scenariji", default="")
    args = a.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    izvade = pathlib.Path(args.izvade)
    izvade.mkdir(exist_ok=True)
    kodi = [s["kods"] for s in json.loads((PROD / "demo" / "scenariji.json").read_text(encoding="utf-8"))["scenariji"]]
    if args.scenariji:
        kodi = [k for k in kodi if k in args.scenariji.split(",")]
    s = serveris()
    bazes = f"http://127.0.0.1:{s.server_port}/"
    kludas_kopa = 0
    with sync_playwright() as p:
        b = p.chromium.launch()
        for nos, izm, mob in [("telefons", (375, 740), True), ("dators", (1280, 800), False)]:
            ctx = b.new_context(viewport={"width": izm[0], "height": izm[1]}, is_mobile=mob, has_touch=mob, device_scale_factor=2 if mob else 1,
                                service_workers="block")  # sw.js (offline.js) citādi apiet /api pārsūtīšanu
            lapa = ctx.new_page()
            kludas = []
            lapa.on("pageerror", lambda e: kludas.append(str(e)))
            lapa.on("console", lambda m: m.type == "error" and not m.text.startswith("Failed to load resource") and kludas.append(m.text))
            # LVĢMC plūdu WMS (app.js) dažām flīzēm atbild 404: zināms, ne demo kļūda
            lapa.on("response", lambda r: r.status >= 400 and "geo-dpps.viss.gov.lv" not in r.url and kludas.append(f"{r.status} {r.url[:150]}"))
            lapa.route("**/api/**", api)
            lapa.goto(bazes, wait_until="networkidle")
            lapa.wait_for_timeout(1500)
            lapa.click("#demo-cilne")
            lapa.wait_for_selector(".demo-saraksts button")
            lapa.screenshot(path=str(izvade / f"{nos}-0-saraksts.png"))
            for i, kods in enumerate(kodi, 1):
                if not lapa.is_visible(f'[data-demo="{kods}"]'):
                    if lapa.is_visible(".demo-atpakal"):
                        lapa.click(".demo-atpakal")
                    else:
                        lapa.click("#demo-cilne")
                lapa.click(f'[data-demo="{kods}"]')
                lapa.wait_for_selector(".demo-kartite")
                lapa.wait_for_function("!document.querySelector('#demo-saturs').textContent.includes('Ielādē tuvākās')", timeout=45000)
                lapa.wait_for_timeout(2500)
                info = lapa.evaluate("""() => ({
                  zimes: document.querySelectorAll('.demo-zime').length,
                  josla: !document.getElementById('demo-josla').hidden,
                  vietas: document.querySelectorAll('#demo-saturs li[data-lat]').length,
                  tel: document.querySelectorAll('a[href^="tel:"]').length,
                  ieksa: document.body.scrollWidth <= innerWidth })""")
                print(nos, kods, info)
                if info["tel"] or not info["ieksa"]:
                    kludas.append(f"{kods}: tel saites vai horizontāla ritināšana {info}")
                lapa.screenshot(path=str(izvade / f"{nos}-{i}-{kods}.png"))
                if mob:  # telefonā aizver paneli, lai redzētu karti
                    lapa.click(".demo-aizvert")
                    lapa.wait_for_timeout(400)
                    lapa.screenshot(path=str(izvade / f"{nos}-{i}-{kods}-karte.png"))
                    lapa.click("#demo-cilne")
            lapa.click(".demo-beigt")
            lapa.wait_for_timeout(1500)
            beigas = lapa.evaluate("""() => ({ aktivs: document.body.classList.contains('demo-aktivs'),
              josla: document.getElementById('demo-josla').hidden, url: location.search })""")
            print(nos, "beigt", beigas)
            if beigas["aktivs"] or not beigas["josla"] or beigas["url"]:
                kludas.append(f"beigt demo neatjaunoja: {beigas}")
            # tieša saite
            lapa.goto(bazes + "?demo=bez-sakariem&regions=100003470", wait_until="networkidle")
            lapa.wait_for_selector(".demo-kartite h2")
            lapa.wait_for_timeout(3000)
            lapa.screenshot(path=str(izvade / f"{nos}-saite-bez-sakariem-ogre.png"))
            print(nos, "JS kļūdas:", kludas or "nav")
            kludas_kopa += len(kludas)
            ctx.close()
        b.close()
    s.shutdown()
    raise SystemExit(1 if kludas_kopa else 0)


if __name__ == "__main__":
    main()
