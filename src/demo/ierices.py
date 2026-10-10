"""Ierīču matrica: pitch demo ceļš uz vairākiem telefoniem/planšetes (Playwright ierīču profili), atrašanās vieta atļauta un liegta.

Pārbauda: JS kļūdas, neizdevušies pieprasījumi, horizontāla ritināšana, pogas/saites < 44 px, teksts < 12 px, 112 rinda,
SIMULĀCIJA zīmes, "Beigt demo". Ekrānuzņēmumi un ziņojums (JSON) — izvades mapē (ārpus repo).

    uv run --no-project --with playwright src/demo/ierices.py [--url https://map.repo.lv] [--izvade C:/.../telefonu-tests]
    --lokali: production/ no šī repo + /api uz map.repo.lv (labojumu pārbaudei pirms PR)
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
IERICES = ["iPhone SE", "iPhone 14", "Pixel 7", "Galaxy S9+", "iPad Mini"]
OGRE = {"latitude": 56.8162, "longitude": 24.6140}
VAICAJUMI = ["plūdi Ogre", "nav elektrības Rīgā", "cilvēks nav pie samaņas"]
DEMO = ["vejs", "vetra", "drons", "nakts", "pludi-ogre", "vetra-2026", "bez-sakariem"]

# Lapā: mazi pieskāriena mērķi, mazs teksts, pārplūde. Iekļautas saites tekstā (p, small, li teksts) WCAG 2.5.8 izņēmums.
PARBAUDE = """() => {
  const redzams = e => { const r = e.getBoundingClientRect(); const s = getComputedStyle(e);
    return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none' && r.bottom > 0 && r.top < innerHeight; };
  const nos = e => (e.id ? '#' + e.id : e.tagName.toLowerCase() + (e.className && typeof e.className === 'string' ? '.' + e.className.trim().split(/\\s+/).join('.') : ''))
    + ' "' + (e.getAttribute('aria-label') || e.textContent || e.value || '').trim().slice(0, 30) + '"';
  const mazi = [];
  for (const e of document.querySelectorAll('button, a[href], input:not([type=hidden]), select, summary, [role=button], [role=option]')) {
    if (!redzams(e) || e.closest('.leaflet-control-attribution')) continue;
    if (e.matches('a') && e.closest('p, small, .popup-avots, .avots-rinda, li > span.teksts > small')) continue;
    const r = e.getBoundingClientRect();
    if (r.width < 44 || r.height < 44) mazi.push(`${nos(e)} ${Math.round(r.width)}×${Math.round(r.height)}`);
  }
  const mazsTeksts = new Set();
  const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  while (w.nextNode()) {
    const t = w.currentNode; const e = t.parentElement;
    if (!t.textContent.trim() || !e || !redzams(e) || e.closest('.leaflet-control-attribution, .leaflet-control-scale')) continue;
    const px = parseFloat(getComputedStyle(e).fontSize);
    if (px < 12) mazsTeksts.add(`${nos(e)} ${px}px`);
  }
  const plati = [...document.querySelectorAll('body *')].filter(e => redzams(e) && e.getBoundingClientRect().right > innerWidth + 1
    && !e.closest('.leaflet-pane, .leaflet-control-container') && getComputedStyle(e).position !== 'fixed').slice(0, 5).map(nos);
  return { parplude: document.documentElement.scrollWidth > innerWidth + 1, plati, mazi: [...new Set(mazi)], mazsTeksts: [...mazsTeksts].slice(0, 15),
    tel: document.querySelectorAll('a[href^="tel:"]').length };
}"""


def serveris():
    class Klusais(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass
    s = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Klusais, directory=str(SAKNE / "production")))
    threading.Thread(target=s.serve_forever, daemon=True).start()
    return s


def api(route):
    u = urllib.parse.urlsplit(route.request.url)
    try:
        with urllib.request.urlopen(urllib.request.Request("https://map.repo.lv" + u.path + ("?" + u.query if u.query else ""),
                                                           headers={"User-Agent": "ierices"}), timeout=40) as r:
            route.fulfill(status=r.status, body=r.read(), headers={"content-type": r.headers.get("content-type", "application/json")})
    except urllib.error.HTTPError as e:
        route.fulfill(status=e.code, body=e.read())


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--url", default="https://map.repo.lv/")
    a.add_argument("--izvade", default=str(SAKNE.parent / "telefonu-tests"))
    a.add_argument("--ierices", default=",".join(IERICES))
    a.add_argument("--lokali", action="store_true")
    a.add_argument("--atrasanas", default="atlauta,liegta")
    args = a.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    izvade = pathlib.Path(args.izvade)
    izvade.mkdir(parents=True, exist_ok=True)
    s = serveris() if args.lokali else None
    bazes = f"http://127.0.0.1:{s.server_port}/" if s else args.url.rstrip("/") + "/"
    zinojums = []
    with sync_playwright() as p:
        for ierice in args.ierices.split(","):
            profils = p.devices[ierice]
            parluks = getattr(p, profils.get("default_browser_type", "chromium")).launch()
            for atr in args.atrasanas.split(","):
                ctx = parluks.new_context(**profils, geolocation=OGRE if atr == "atlauta" else None,
                                          permissions=["geolocation"] if atr == "atlauta" else [])
                lapa = ctx.new_page()
                if s:
                    lapa.route("**/api/**", api)
                kludas = []
                lapa.on("pageerror", lambda e: kludas.append("JS: " + str(e)))
                lapa.on("console", lambda m: m.type == "error" and not m.text.startswith("Failed to load resource") and kludas.append("console: " + m.text[:200]))
                lapa.on("response", lambda r: r.status >= 400 and "geo-dpps.viss.gov.lv" not in r.url and kludas.append(f"{r.status} {r.url[:140]}"))
                tag = f"{ierice.replace(' ', '_')}-{atr}"
                ieraksti = []

                def solis(nos, darbiba):
                    try:
                        darbiba()
                        lapa.wait_for_timeout(600)
                        r = lapa.evaluate(PARBAUDE)
                    except Exception as e:  # noqa: BLE001 — strupceļš vai taimauts ir rezultāts, ne avārija
                        r = {"kluda": str(e).splitlines()[0][:200]}
                    r["solis"] = nos
                    ieraksti.append(r)
                    lapa.screenshot(path=str(izvade / f"{tag}-{len(ieraksti):02d}-{nos}.png"))

                def sakums():
                    lapa.goto(bazes, wait_until="load", timeout=60000)
                    lapa.wait_for_timeout(1500)

                def meklet(q):
                    def f():
                        lapa.fill("#jautajums", q)
                        lapa.press("#jautajums", "Enter")
                        lapa.wait_for_function("(() => { const r = document.getElementById('rezultati');"
                                               " return r && !r.hidden && !/Meklē tuvākās|Meklē adresi|Ielādē/.test(r.textContent.slice(0, 400)); })()", timeout=45000)
                        lapa.wait_for_timeout(2500)
                    return f

                def demo(k):
                    def f():
                        lapa.goto(bazes + "?demo=" + k, wait_until="load", timeout=60000)
                        lapa.wait_for_function("!document.querySelector('#demo-saturs')?.textContent.includes('Ielādē tuvākās')"
                                               " && !!document.querySelector('.demo-kartite')", timeout=45000)
                        lapa.wait_for_timeout(1500)
                    return f

                def beigt():
                    lapa.click(".demo-beigt")
                    lapa.wait_for_timeout(800)
                    assert not lapa.evaluate("document.body.classList.contains('demo-aktivs')"), "demo palika aktīvs"

                def prognoze():
                    lapa.goto(bazes, wait_until="load", timeout=60000)
                    lapa.wait_for_timeout(1500)
                    if not lapa.is_visible("#prog-panelis"):
                        lapa.click(".prog-poga", timeout=8000)

                def avoti():
                    if lapa.is_visible("#prog-panelis") and lapa.is_visible(".prog-aizvert"):
                        lapa.click(".prog-aizvert")
                    if not lapa.is_visible("#avoti"):
                        lapa.click("#panelis-poga")
                    lapa.click("#avoti > summary")
                    lapa.wait_for_timeout(500)
                    lapa.locator("#avoti").scroll_into_view_if_needed()

                solis("sakums", sakums)
                for q in VAICAJUMI:
                    solis("q-" + q.split()[0] + "-" + q.split()[-1], meklet(q))
                    if q.startswith("cilvēks"):
                        ieraksti[-1]["112"] = lapa.evaluate("!!document.querySelector('#rezultati .draudi')")
                # Apakšējā lapa (#60, tikai ≤ 800 px): stāvokļi peek/puse/pilna, galvenā darbība, demo panelis un lapa nav atvērti abi
                if lapa.viewport_size["width"] <= 800:
                    solis("lapa-pludi", meklet("plūdi Ogre"))
                    lapas = {"sakums": lapa.evaluate("(() => { const a = document.getElementById('apaksa'); return a && !a.hidden ? a.dataset.stavoklis : 'nav'; })()")}
                    for i in range(3):
                        solis(f"lapa-rokturis-{i + 1}", lambda: lapa.click("#apaksa-rokturis"))
                        lapas[f"pec_{i + 1}"] = lapa.evaluate("document.getElementById('apaksa').dataset.stavoklis")
                    lapas["darbiba"] = lapa.evaluate("""(() => { const d = document.querySelector('.apaksa-darbiba');
                      if (!d || d.hidden) return 'nav'; const r = d.getBoundingClientRect();
                      return `${Math.round(r.width)}×${Math.round(r.height)} ${r.bottom <= innerHeight ? 'redzama' : 'ārpus ekrāna'}: ${d.textContent.trim().slice(0, 40)}`; })()""")
                    solis("lapa-un-demo", lambda: lapa.click("#demo-cilne"))
                    lapas["abas_atvertas"] = lapa.evaluate("""document.body.classList.contains('demo-atverts')
                      && document.getElementById('apaksa').dataset.stavoklis !== 'peek'""")
                    lapa.click(".demo-aizvert")
                    ieraksti[-1]["apaksa"] = lapas
                for k in DEMO:
                    solis("demo-" + k, demo(k))
                    ieraksti[-1]["zimes"] = lapa.evaluate("document.querySelectorAll('.demo-zime').length")
                solis("beigt-demo", beigt)
                solis("prognoze", prognoze)
                solis("datu-avoti", avoti)
                solis("statuss", lambda: (lapa.goto(bazes + "statuss.html", wait_until="load", timeout=60000), lapa.wait_for_timeout(2500)))
                zinojums.append({"ierice": ierice, "atrasanas": atr, "kludas": kludas, "soli": ieraksti})
                n_mazi = sum(len(r.get("mazi", [])) for r in ieraksti)
                print(f"{tag}: kļūdas {len(kludas)}, pārplūde {[r['solis'] for r in ieraksti if r.get('parplude')]}, "
                      f"strupceļi {[r['solis'] + ': ' + r['kluda'] for r in ieraksti if 'kluda' in r]}, mazi mērķi {n_mazi}")
                ctx.close()
            parluks.close()
    (izvade / f"zinojums-{args.ierices.replace(' ', '_').replace(',', '+')}.json").write_text(json.dumps(zinojums, ensure_ascii=False, indent=1), encoding="utf-8")
    if s:
        s.shutdown()


if __name__ == "__main__":
    main()
