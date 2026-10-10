"""Service worker atjaunošana (production/atjaunot.js + sw.js): jaunas versijas paziņojums un ?svaigs=1.

Tikai lokāli: skripts uz brīdi maina VERSION diskā esošajā production/sw.js (beigās atjauno), tāpēc serverim jāpasniedz
production/ no diska:

    uv run --no-project --python 3.12 src/demo/lokali.py --port 8893
    uv run --no-project --python 3.12 --with playwright src/testi/sw_atjaunosana.py --url http://localhost:8893

Gaita (375×740, tīrs konteksts, SW atļauts): atver lapu → SW aktīvs, paziņojuma nav → VERSION++ diskā → pārlādē →
"Pieejama jauna versija · Atsvaidzināt" (lapa pati nepārlādējas) → klikšķis → jaunā versija aktīva, vecā shell-* keša nav,
meklējums saglabāts (?q=) → statuss.html rāda versiju → ?svaigs=1 noņem SW un kešus. Bez JS kļūdām, bez tel:.
"""
import argparse
import pathlib
import re
import sys

from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8")
SW = pathlib.Path(__file__).resolve().parents[2] / "production" / "sw.js"
rezultati = []


def ieraksts(nos, ok, sik=""):
    rezultati.append((nos, ok))
    print(f"{'OK  ' if ok else 'KĻŪDA'} {nos}{' — ' + sik if sik else ''}")


def kesi(lapa):
    return lapa.evaluate("caches.keys()")


def versija(lapa):
    return lapa.evaluate("""() => new Promise(ok => {
      const k = navigator.serviceWorker.controller; if (!k) return ok(null);
      const ch = new MessageChannel(); ch.port1.onmessage = e => ok(e.data.versija); k.postMessage('versija', [ch.port2]);
    })""")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://localhost:8893")
    ap.add_argument("--ekr", help="mape ekrānuzņēmumam")
    a = ap.parse_args()
    orig = SW.read_text(encoding="utf-8")
    vecā = re.search(r"const VERSION = '([^']+)'", orig).group(1)
    jaunā = vecā + "-tests"
    kludas = []
    with sync_playwright() as p:
        b = p.chromium.launch()
        ctx = b.new_context(viewport={"width": 375, "height": 740}, is_mobile=True, has_touch=True, service_workers="allow")
        lapa = ctx.new_page()
        lapa.on("pageerror", lambda e: kludas.append(str(e)))
        try:
            lapa.goto(a.url + "/map", wait_until="load")
            lapa.evaluate("navigator.serviceWorker.ready")
            lapa.wait_for_function("!!navigator.serviceWorker.controller", timeout=15000)
            ieraksts("SW aktīvs pirmajā apmeklējumā", versija(lapa) == vecā, versija(lapa))
            lapa.wait_for_timeout(500)
            ieraksts("pirmajā apmeklējumā paziņojuma nav", lapa.locator(".jauna-versija").count() == 0)
            ieraksts("shell kešs", f"shell-{vecā}" in kesi(lapa), str(kesi(lapa)))

            lapa.fill("#jautajums", "plūdi Ogre")
            SW.write_text(orig.replace(f"'{vecā}'", f"'{jaunā}'", 1), encoding="utf-8", newline="\n")
            # lapa neatjaunojas: atgriešanās cilnē / pārlāde pārbauda sw.js; šeit — reg.update() kā visibilitychange
            lapa.evaluate("navigator.serviceWorker.getRegistration().then(r => r.update())")
            lapa.wait_for_selector(".jauna-versija", timeout=20000)
            ieraksts("paziņojums parādās bez pārlādes", True, lapa.locator(".jauna-versija").inner_text().replace("\n", " "))
            ieraksts("lapa nav pārlādēta, ievade saglabāta", lapa.input_value("#jautajums") == "plūdi Ogre")
            poga = lapa.locator(".jauna-versija .jv-atsvaidzinat").bounding_box()
            ieraksts("poga ≥ 44 px", poga["height"] >= 44 and poga["width"] >= 44, f"{poga['width']:.0f}×{poga['height']:.0f}")
            if a.ekr:
                pathlib.Path(a.ekr).mkdir(parents=True, exist_ok=True)
                lapa.screenshot(path=str(pathlib.Path(a.ekr) / "sw-pazinojums.png"))
            with lapa.expect_navigation():
                lapa.click(".jauna-versija .jv-atsvaidzinat")
            lapa.wait_for_function("!!navigator.serviceWorker.controller")
            ieraksts("pēc klikšķa jaunā versija aktīva", versija(lapa) == jaunā, versija(lapa))
            k = kesi(lapa)
            ieraksts("vecais shell kešs izdzēsts", f"shell-{vecā}" not in k and f"shell-{jaunā}" in k, str(k))
            ieraksts("meklējums saglabāts (?q=)", "q=" in lapa.url, lapa.url)
            lapa.wait_for_timeout(500)
            ieraksts("pēc pārlādes paziņojuma nav", lapa.locator(".jauna-versija").count() == 0)

            lapa.goto(a.url + "/statuss.html", wait_until="load")
            lapa.wait_for_selector("#sw-versija:not([hidden])", timeout=10000)
            t = lapa.inner_text("#sw-versija")
            ieraksts("statuss.html rāda SW versiju", jaunā in t, t)

            lapa.evaluate("caches.open('svaigs-marķieris').then(c => c.put('/marķieris', new Response('x')))")
            lapa.goto(a.url + "/map?svaigs=1", wait_until="load")
            lapa.wait_for_url(lambda u: "svaigs" not in u, timeout=15000)
            lapa.wait_for_load_state("load")
            k = kesi(lapa)
            # pēc pārlādes atjaunot.js SW reģistrē no jauna (tīra instalācija) — tāpēc pārbaudām marķiera kešu
            ieraksts("?svaigs=1: URL bez parametra, visi keši izdzēsti", "svaigs-marķieris" not in k, f"keši {k}")
            lapa.wait_for_function("!!navigator.serviceWorker.controller", timeout=15000)
            ieraksts("?svaigs=1: SW no jauna", versija(lapa) == jaunā, versija(lapa))

            # parastā pārlāde pēc deploy: VERSION++ → pārlādē → paziņojums (lapa jau no tīkla, SW pārņem pēc tam)
            trešā = vecā + "-tests2"
            SW.write_text(orig.replace(f"'{vecā}'", f"'{trešā}'", 1), encoding="utf-8", newline="\n")
            lapa.reload(wait_until="load")
            lapa.wait_for_selector(".jauna-versija", timeout=20000)
            ieraksts("pēc pārlādes ar jaunu sw.js paziņojums parādās", versija(lapa) == trešā, versija(lapa))
            ieraksts("nav tel: saišu",lapa.locator("a[href^='tel:']").count() == 0)
        finally:
            SW.write_text(orig, encoding="utf-8", newline="\n")
            b.close()
    ieraksts("nav JS kļūdu", not kludas, "; ".join(kludas[:3]))
    sys.exit(0 if all(ok for _, ok in rezultati) else 1)


if __name__ == "__main__":
    main()
