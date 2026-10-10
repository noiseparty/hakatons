"""Pitch slaidu ekrānuzņēmumu atjaunošana (production/slaidi/*.webp, kurus lieto production/slaidi.html).

    uv run --no-project --with playwright --with pillow src/demo/ekrani.py [--url https://map.repo.lv] [--tikai 03,05] [--izvade <mape>]

Telefons 390x844 @2x (780x1688), dators 1280x800 @1. Plūdu zonas rinda tiek gaidīta, līdz tai ir īsta atbilde (nevis
"Pārbauda…"), bet ne ilgāk par 40 s; ja LVĢMC nav atbildējis, kadrs tomēr tiek saglabāts un tabulā parādās brīdinājums.
Vienā palaišanā ~6 lapas ielādes (parasti lietotāja apmeklējums, bez atkārtojumiem). Pēc palaišanas pārbaudiet ✓/⚠ tabulu
un atveriet slaidi.html. Pēc izmaiņu pievienošanas: nākamajā palaišanā failu nosaukumi jāatjauno slaidi.html (FAILI zemāk).
"""
import argparse
import io
import pathlib
import re
import sys

from PIL import Image
from playwright.sync_api import sync_playwright

SAKNE = pathlib.Path(__file__).resolve().parents[2]
TELEFONS = dict(viewport={"width": 390, "height": 844}, device_scale_factor=2, is_mobile=True, has_touch=True)
DATORS = dict(viewport={"width": 1280, "height": 800}, device_scale_factor=1)
MAKS_KB = 300
CSS = "*{cursor:none!important;caret-color:transparent!important}"
IELADE = re.compile(r"Pārbauda|ielādējas|Ielādē|mēģinām vēlreiz", re.I)

# numurs -> (fails, aprakstam)
FAILI = {
    "01": "01-dators-ogre-pludi.webp",
    "02": "02-ogre-pludi.webp",
    "03": "03-ogre-upe.webp",
    "04": "04-adrese-karte.webp",
    "05": "05-adrese-pulcesanas.webp",
    "06": "06-112.webp",
    "07": "07-datu-avoti.webp",
    "08": "08-lr1-radio.webp",
}


def webp(png, maks_kb=MAKS_KB):
    im = Image.open(io.BytesIO(png)).convert("RGB")
    for q in (88, 82, 76, 70, 64, 56, 48):
        b = io.BytesIO()
        im.save(b, "WEBP", quality=q, method=6)
        if len(b.getvalue()) <= maks_kb * 1024:
            return b.getvalue(), q
    return b.getvalue(), q


def jauns(p, **ctx):
    b = p.chromium.launch()
    c = b.new_context(locale="lv-LV", permissions=[], service_workers="block", **ctx)
    c.add_init_script("try{localStorage.clear()}catch(e){}")
    return b, c


def gaidit_pludus(lapa, kuvs=40000):
    """Gaida, līdz plūdu zonas rindai (#rez-pludi) ir īsta atbilde. Atgriež (ok, teksts)."""
    try:
        lapa.wait_for_selector("#rez-pludi span", timeout=kuvs)
        lapa.wait_for_function(
            "re => { const e = document.querySelector('#rez-pludi span'); return e && !new RegExp(re, 'i').test(e.textContent); }",
            arg=IELADE.pattern, timeout=kuvs)
    except Exception:
        pass
    teksts = lapa.evaluate("document.querySelector('#rez-pludi')?.innerText || ''").replace("\n", " ")
    return bool(teksts) and not IELADE.search(teksts), teksts


def gaidit_udeni(lapa, kuvs=15000):
    try:
        lapa.wait_for_function("() => { const e = document.querySelector('#rez-udens span'); return e && !/Ielādē/.test(e.textContent); }", timeout=kuvs)
    except Exception:
        pass


def meklet(lapa, teksts):
    lapa.fill("#jautajums", teksts)
    lapa.press("#jautajums", "Enter")
    lapa.wait_for_selector("#rezultati .draudi, #rezultati #rez-lemums, #rezultati .fakti, #rezultati .rez-saraksts", state="attached", timeout=20000)


def uz_redzamu(lapa, selektors=None, teksts=None):
    """Ritina kartīti tā, lai rinda būtu augšā (ligzdots ritinātājs: scrollIntoView)."""
    return lapa.evaluate(
        """([sel, txt]) => {
            let e = sel ? document.querySelector(sel) : null;
            if (!e && txt) {
                const c = [...document.querySelectorAll('#lapa-rezultats li, #rezultati li, #rezultati h3')].filter(x => x.textContent.toLowerCase().includes(txt.toLowerCase()));
                e = c.sort((a, b) => a.textContent.length - b.textContent.length)[0];
            }
            if (!e) return false;
            e.scrollIntoView({ block: 'start' });
            return true;
        }""", [selektors, teksts])


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--url", default="https://map.repo.lv")
    a.add_argument("--tikai", default="", help="komats numuru saraksts, piem. 03,05")
    a.add_argument("--izvade", default=str(SAKNE / "production" / "slaidi"))
    args = a.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    bāze = args.url.rstrip("/")
    izv = pathlib.Path(args.izvade)
    izv.mkdir(parents=True, exist_ok=True)
    gribam = set(x.strip() for x in args.tikai.split(",") if x.strip()) or set(FAILI)
    tab = []  # (nr, fails, kb, kvalitate, piezime)
    kludas = []

    def saglabat(nr, png, brid=""):
        dati, q = webp(png)
        (izv / FAILI[nr]).write_bytes(dati)
        tab.append((nr, FAILI[nr], len(dati) / 1024, q, brid))

    def grupa(nr_saraksts):
        return any(n in gribam for n in nr_saraksts)

    with sync_playwright() as p:
        def atvert(b_ctx, ceļš, klausit=True):
            b, c = b_ctx
            lapa = c.new_page()
            if klausit:
                lapa.on("pageerror", lambda e: kludas.append(f"{ceļš}: {e}"))
            lapa.goto(bāze + ceļš, wait_until="load")
            lapa.add_style_tag(content=CSS)
            return lapa

        # 01: dators, "Ogre, plūdi"
        if grupa(["01"]):
            b, c = jauns(p, **DATORS)
            lapa = atvert((b, c), "/")
            meklet(lapa, "Ogre, plūdi")
            ok, t = gaidit_pludus(lapa)
            gaidit_udeni(lapa)
            lapa.wait_for_timeout(1500)
            saglabat("01", lapa.screenshot(), "" if ok else f"ielādes stāvoklis: {t[:60]}")
            b.close()

        # 02, 03: telefons, "Ogre, plūdi"
        if grupa(["02", "03"]):
            b, c = jauns(p, **TELEFONS)
            lapa = atvert((b, c), "/")
            meklet(lapa, "Ogre, plūdi")
            ok, t = gaidit_pludus(lapa)
            gaidit_udeni(lapa)
            lapa.wait_for_timeout(1500)
            brid = "" if ok else f"ielādes stāvoklis: {t[:60]}"
            if "02" in gribam:
                saglabat("02", lapa.screenshot(), brid)
            if "03" in gribam:
                if not uz_redzamu(lapa, "#rez-udens"):
                    brid += " (nav upes rindas)"
                lapa.wait_for_timeout(600)
                saglabat("03", lapa.screenshot(), brid)
            b.close()

        # 04, 05: telefons, adrese
        if grupa(["04", "05"]):
            b, c = jauns(p, **TELEFONS)
            lapa = atvert((b, c), "/")
            meklet(lapa, "plūdi Brīvības iela 33 Ogre")
            ok, t = gaidit_pludus(lapa)
            gaidit_udeni(lapa)
            lapa.wait_for_timeout(2000)
            brid = "" if ok else f"ielādes stāvoklis: {t[:60]}"
            if "04" in gribam:
                saglabat("04", lapa.screenshot(), brid)
            if "05" in gribam:
                if not uz_redzamu(lapa, teksts="pulcēšan"):
                    brid += " (nav pulcēšanās rindas)"
                lapa.wait_for_timeout(600)
                saglabat("05", lapa.screenshot(), brid)
            b.close()

        # 06: telefons, 112
        if grupa(["06"]):
            b, c = jauns(p, **TELEFONS)
            lapa = atvert((b, c), "/")
            meklet(lapa, "cilvēks nav pie samaņas")
            lapa.wait_for_timeout(1500)
            brid = "" if "112" in lapa.inner_text("body") else "nav 112 rindas"
            saglabat("06", lapa.screenshot(), brid)
            b.close()

        # 07: dators @2x, panelis "Datu avoti" (390x270 izgriezums)
        if grupa(["07"]):
            b, c = jauns(p, viewport={"width": 1280, "height": 800}, device_scale_factor=2)
            lapa = atvert((b, c), "/")
            lapa.click('[data-dv="slani"]')  # darbvirsma.js: slāņu atvilktne, kurā ir "Datu avoti"
            lapa.evaluate("document.querySelector('#avoti').open = true")
            lapa.wait_for_selector("#avoti-saraksts li", state="attached", timeout=20000)
            kaste = lapa.evaluate("""(() => {
                const li = [...document.querySelectorAll('#avoti-saraksts li')].find(x => /civilās aizsardzības plāni/i.test(x.textContent));
                if (!li) return null;
                li.scrollIntoView({ block: 'start' });
                const r = li.getBoundingClientRect(); return [r.x, r.y, r.width];
            })()""")
            lapa.wait_for_timeout(800)
            brid = "" if kaste else "nav CA plānu avota rindas"
            kaste = kaste or [0, 0]
            png = lapa.screenshot(clip={"x": max(0, kaste[0] - 6), "y": max(0, kaste[1] - 6), "width": min(390, int(kaste[2]) + 12) if len(kaste) > 2 else 390, "height": 270})
            saglabat("07", png, brid)
            b.close()

        # 08: telefons, info.html LR1 radio (390x770 izgriezums)
        if grupa(["08"]):
            b, c = jauns(p, **TELEFONS)
            lapa = atvert((b, c), "/info.html")
            lapa.evaluate("document.querySelector('#b-radio').scrollIntoView({block: 'start'})")
            lapa.wait_for_timeout(800)
            saglabat("08", lapa.screenshot(clip={"x": 0, "y": 0, "width": 390, "height": 770}))
            b.close()

    print(f"\n{'nr':<3} {'fails':<28} {'KB':>6} {'q':>3}  piezīme")
    for nr, f, kb, q, brid in sorted(tab):
        print(f"{nr:<3} {f:<28} {kb:6.1f} {q:3d}  {'⚠ ' + brid if brid else 'ok'}")
    if kludas:
        print("\nJS kļūdas:\n  " + "\n  ".join(kludas))
    sl = [t for t in tab if t[4]]
    if sl:
        print(f"\n⚠ {len(sl)} kadri vēl rāda ielādes stāvokli vai trūkstošu rindu — pirms izmantošanas atkārtojiet vēlāk "
              f"(--tikai {','.join(t[0] for t in sl)}).")
    print(f"Saglabāts: {izv}")


if __name__ == "__main__":
    main()
