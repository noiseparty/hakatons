"""Bezsaistes (PWA) pārbaude ar Playwright: 375×740, service worker atļauts, katru reizi tīrs pārlūka konteksts.

Ar tīklu: atver lapu, meklē "Ogre, plūdi", atver "Datu avoti", gaida sw.js (navigator.serviceWorker.ready) un
pārbauda, kuri production/ faili (src/testi/sw_faili.py saraksts) ir shell kešā. Tad context.set_offline(True) un:
pārlādē lapu (shell, pēdējā kartīte vai "Saglabāts rezultāts", josla #bezsakaru, kartes flīzes), info.html
(LR1 radio karte), statuss.html un ?demo=bez-sakariem. Uzskaita nenotvertās JS kļūdas (pageerror).

    uv run --no-project --python 3.12 --with playwright src/testi/bezsaiste.py --url http://localhost:8491
    (pret map.repo.lv tikai saudzīgi: viena palaišana, ~6 lapas ielādes)
"""
import argparse
import json
import pathlib
import sys
import time

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from sw_faili import shell_faili  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

rezultati = []


def ieraksts(nos, ok, sik=""):
    rezultati.append((nos, ok, sik))
    print(f"{'OK  ' if ok else 'NAV '} {nos}: {sik}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://localhost:8491")
    ap.add_argument("--ekr", help="mape ekrānuzņēmumiem")
    a = ap.parse_args()
    url = a.url.rstrip("/")
    ekr = pathlib.Path(a.ekr) if a.ekr else None
    if ekr:
        ekr.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        b = p.chromium.launch()
        ctx = b.new_context(viewport={"width": 375, "height": 740}, is_mobile=True, has_touch=True,
                            service_workers="allow", locale="lv-LV")
        kludas = []
        lapa = ctx.new_page()
        lapa.on("pageerror", lambda e: kludas.append(f"{lapa.url}: {e}"))

        # 1) ar tīklu
        lapa.goto(url + "/map", wait_until="load")
        lapa.fill("#jautajums", "Ogre, plūdi")
        lapa.press("#jautajums", "Enter")
        try:
            lapa.wait_for_selector("#rezultati .sapratu", timeout=20000)
        except Exception:  # noqa: BLE001
            pass
        lapa.wait_for_timeout(9000)  # vietas, upes, brīdinājumi; offline.js kartīti saglabā pēc 2,5 s klusuma
        lapa.evaluate("() => { const d = document.getElementById('avoti'); if (d) d.open = true; }")
        lapa.wait_for_timeout(1500)
        sw = lapa.evaluate("""async () => {
          if (!('serviceWorker' in navigator)) return { nav: 'serviceWorker nav' };
          const r = await Promise.race([navigator.serviceWorker.ready.then(() => true), new Promise(ok => setTimeout(() => ok(false), 20000))]);
          const keys = await caches.keys();
          const shell = keys.find(k => k.startsWith('shell-'));
          let saturs = [];
          if (shell) saturs = (await (await caches.open(shell)).keys()).map(r => new URL(r.url).pathname);
          const api = keys.includes('api-v1') ? (await (await caches.open('api-v1')).keys()).map(r => new URL(r.url).pathname) : [];
          return { ready: r, keys, shell: saturs, api, kartites: JSON.parse(localStorage.getItem('bezsaiste-kartites') || '[]').map(k => k.vaicajums) };
        }""")
        ieraksts("SW gatavs", bool(sw.get("ready")), ", ".join(sw.get("keys", [])))
        api_pirmaja = sorted({c.split("/")[2] for c in sw.get("api", []) if c.count("/") >= 2})
        ieraksts("API kešā pēc 1. apmeklējuma", True, ", ".join(api_pirmaja) + " (1. meklēšana notiek, pirms SW kontrolē lapu)")
        # atkārtots apmeklējums: SW jau kontrolē lapu, meklēšanas API atbildes nonāk kešā
        lapa.reload(wait_until="load")
        lapa.fill("#jautajums", "Ogre, plūdi")
        lapa.press("#jautajums", "Enter")
        lapa.wait_for_timeout(10000)
        sw.update(lapa.evaluate("""async () => ({ api: (await (await caches.open('api-v1')).keys()).map(r => new URL(r.url).pathname),
          kartites: JSON.parse(localStorage.getItem('bezsaiste-kartites') || '[]').map(k => k.vaicajums) })"""))
        vajag = shell_faili()
        ir = set(sw.get("shell", []))
        trukst = [f for f in vajag if f != "./" and "/" + f not in ir]
        ieraksts("Shell kešā visi lapu faili", not trukst, f"{len(vajag) - len(trukst)}/{len(vajag)}" + (f"; trūkst: {', '.join(trukst)}" if trukst else ""))
        api_celi = sorted({c.split("/")[2] for c in sw.get("api", []) if c.count("/") >= 2})
        ieraksts("API kešā pēc 2. apmeklējuma", bool(api_celi), ", ".join(api_celi))
        ieraksts("Kartīte saglabāta (localStorage)", bool(sw.get("kartites")), ", ".join(sw.get("kartites", [])))
        if ekr:
            lapa.screenshot(path=str(ekr / "1-ar-tiklu.png"))

        # 2) bez tīkla: pārlādē
        ctx.set_offline(True)
        t0 = time.time()
        try:
            lapa.reload(wait_until="load", timeout=30000)
            ieladeta = True
        except Exception as e:  # noqa: BLE001
            ieladeta = False
            ieraksts("Lapa bez tīkla", False, str(e)[:120])
        if ieladeta:
            lapa.wait_for_timeout(4000)
            st = lapa.evaluate("""() => ({
              lauks: !!document.getElementById('jautajums'),
              stils: getComputedStyle(document.body).fontFamily,
              leaflet: typeof L !== 'undefined',
              josla: (() => { const j = document.getElementById('bezsakaru'); return j && !j.hidden ? j.innerText : ''; })(),
              kartite: (() => { const k = document.getElementById('rezultati'); return k && !k.hidden ? k.innerText.slice(0, 160) : ''; })(),
              flizes: document.querySelectorAll('.leaflet-tile-loaded').length,
              flizesVisas: document.querySelectorAll('.leaflet-tile').length,
              kartesKluda: (() => { const j = document.getElementById('kartes-kluda'); return j && !j.hidden ? j.innerText : ''; })(),
            })""")
            ieraksts("Shell bez tīkla", st["lauks"] and st["leaflet"], f"{time.time() - t0:.1f} s, Leaflet {st['leaflet']}")
            ieraksts("Josla #bezsakaru", bool(st["josla"]), st["josla"][:140])
            ieraksts("Pēdējā kartīte", bool(st["kartite"]), st["kartite"].replace("\n", " ")[:140])
            ieraksts("Kartes flīzes no keša", st["flizes"] > 0, f"{st['flizes']}/{st['flizesVisas']} ielādētas" + (f"; paziņojums: {st['kartesKluda']}" if st["kartesKluda"] else ""))
            if ekr:
                lapa.screenshot(path=str(ekr / "2-bez-tikla.png"))

        # 3) info.html un statuss.html bez tīkla
        for cels, sel in (("/info.html", "svg.radio-karte"), ("/statuss.html", "main, body")):
            try:
                lapa.goto(url + cels, wait_until="load", timeout=20000)
                lapa.wait_for_timeout(1500)
                ok = lapa.locator(sel).count() > 0
                ieraksts(f"{cels} bez tīkla", ok, lapa.title())
                if ekr:
                    lapa.screenshot(path=str(ekr / f"3{cels.replace('/', '-').replace('.html', '')}.png"))
            except Exception as e:  # noqa: BLE001
                ieraksts(f"{cels} bez tīkla", False, str(e)[:120])

        # 4) ?demo=bez-sakariem bez tīkla
        try:
            lapa.goto(url + "/map?demo=bez-sakariem", wait_until="load", timeout=30000)
            lapa.wait_for_timeout(6000)
            d = lapa.evaluate("""() => ({
              demo: !!document.querySelector('.demo-josla, #demo-josla, [class*="demo"]:not(link)'),
              teksts: (document.getElementById('rezultati')?.innerText || '').slice(0, 140),
              josla: (() => { const j = document.getElementById('bezsakaru'); return j && !j.hidden ? j.innerText : ''; })(),
            })""")
            ieraksts("?demo=bez-sakariem bez tīkla", d["demo"], (d["teksts"] or d["josla"]).replace("\n", " "))
            if ekr:
                lapa.screenshot(path=str(ekr / "4-demo-bez-sakariem.png"))
        except Exception as e:  # noqa: BLE001
            ieraksts("?demo=bez-sakariem bez tīkla", False, str(e)[:120])

        ieraksts("Nenotvertas JS kļūdas", not kludas, "; ".join(kludas)[:600])
        b.close()

    print(json.dumps([{"parbaude": n, "ok": o, "detalas": s} for n, o, s in rezultati], ensure_ascii=False, indent=1))
    sys.exit(0 if all(o for _, o, _ in rezultati) else 1)


if __name__ == "__main__":
    main()
