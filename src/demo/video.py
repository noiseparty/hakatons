"""Rezerves demo video (Playwright recordVideo, 390×844) + ekrānuzņēmumi slaidiem — pitch ceļš ~60 s (notes/pitch.md §5).

Video un PNG saglabā ārpus repo (pēc noklusējuma ../demo-video/).

    uv run --no-project --with playwright src/demo/video.py [--url https://map.repo.lv] [--izvade C:/Users/.../demo-video]
"""
import argparse
import pathlib
import shutil
import sys

from playwright.sync_api import sync_playwright

SAKNE = pathlib.Path(__file__).resolve().parents[2]
IZMERS = {"width": 390, "height": 844}


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--url", default="https://map.repo.lv/")
    a.add_argument("--izvade", default=str(SAKNE.parent / "demo-video"))
    args = a.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    izvade = pathlib.Path(args.izvade)
    izvade.mkdir(parents=True, exist_ok=True)
    bazes = args.url.rstrip("/") + "/"
    atteli = []

    with sync_playwright() as p:
        b = p.chromium.launch()
        ctx = b.new_context(viewport=IZMERS, device_scale_factor=3, is_mobile=True, has_touch=True, locale="lv-LV",
                            geolocation={"latitude": 56.8162, "longitude": 24.6140}, permissions=["geolocation"],
                            record_video_dir=str(izvade / "tmp"), record_video_size=IZMERS)
        lapa = ctx.new_page()

        def foto(nos):
            cels = izvade / f"{len(atteli) + 1:02d}-{nos}.png"
            lapa.screenshot(path=str(cels))
            atteli.append(cels)

        def rakstit(teksts):
            lapa.click("#jautajums")
            lapa.fill("#jautajums", "")
            lapa.type("#jautajums", teksts, delay=70)
            lapa.wait_for_timeout(400)
            lapa.press("#jautajums", "Enter")
            lapa.wait_for_function("(() => { const r = document.getElementById('rezultati');"
                                   " return r && !r.hidden && !/Meklē tuvākās|Meklē adresi|Ielādē/.test(r.textContent.slice(0, 300)); })()", timeout=45000)

        # 1. Sākums: meklēšana ir priekšpusē
        lapa.goto(bazes, wait_until="load")
        lapa.wait_for_timeout(2500)
        foto("sakums")

        # 2. Viens vaicājums → viena kartīte (plūdi pie adreses Ogrē)
        rakstit("plūdi Mednieku iela 9 Ogre")
        lapa.wait_for_timeout(3000)
        foto("pludi-karte")
        lapa.wait_for_timeout(5000)  # plūdu zona (WMS) var atbildēt lēnāk
        for sel, nos in [("#rez-pludi-bloks", "pludi-lemums"), (".rez-saraksts.drosas", "pludi-drosas-vietas"), (".talak, #rezultati .padoms", "pludi-padoms-talak")]:
            if lapa.evaluate(f"!!document.querySelector('{sel}')"):
                lapa.evaluate(f"document.querySelector('{sel}').scrollIntoView({{behavior: 'smooth', block: 'start'}})")
                lapa.wait_for_timeout(2200)
                foto(nos)

        # 3. Dzīvības draudi: sarkana rinda "zvaniet 112", bez pogām
        lapa.evaluate("scrollTo(0, 0)")
        rakstit("cilvēks nav pie samaņas")
        lapa.wait_for_timeout(2500)
        foto("112-rinda")

        # 4. Demo panelis: 2026. gada augusta vētra un Ogres augstienes (SIMULĀCIJA)
        for kods, nos in [("vetra-2026", "demo-vetra-2026"), ("pludi-ogre", "demo-pludi-ogre")]:
            lapa.goto(bazes + "?demo=" + kods, wait_until="load")
            lapa.wait_for_function("!!document.querySelector('.demo-kartite') && !document.querySelector('#demo-saturs').textContent.includes('Ielādē tuvākās')", timeout=45000)
            lapa.wait_for_timeout(2500)
            foto(nos)
            lapa.click(".demo-aizvert")
            lapa.wait_for_timeout(1800)
            foto(nos + "-karte")
            lapa.click("#demo-cilne")
            lapa.wait_for_timeout(1200)

        # 5. Avotu statuss: katram avotam redzams, vai tas darbojas
        lapa.goto(bazes + "statuss.html", wait_until="load")
        lapa.wait_for_timeout(3000)
        foto("statuss")

        video = lapa.video.path()
        ctx.close()
        b.close()
    galamerkis = izvade / "map-repo-lv-demo-390x844.webm"
    shutil.move(video, galamerkis)
    shutil.rmtree(izvade / "tmp", ignore_errors=True)
    print(galamerkis)
    for c in atteli:
        print(c)


if __name__ == "__main__":
    main()
