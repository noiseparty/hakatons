"""Rezerves demo video (~90 s, 7 ainas ar latviešu subtitriem) + 7 kadri slaidiem — storyboard: notes/video.md.

Ieraksta https://map.repo.lv telefona skatā (Playwright Chromium, 390×844, DPR 3, lv-LV, ģeolokācija Ogrē) ar CDP
screencast (kadri 1170×2532 ar laika zīmogiem), tad Pillow + ffmpeg saliek divus MP4 (H.264, 30 fps):
  demo-vertikals.mp4   1080×1920: telefons tumšā rāmī, subtitrs apakšējā trešdaļā
  demo-horizontals.mp4 1920×1080: telefons centrā ar noapaļotiem stūriem, teksts sānos
un captions.srt, 01…07-*.png (viena katrai ainai). Izvade ārpus repo (pēc noklusējuma ../demo-video/).

Gaidīšana (lapas ielāde, plūdu WMS) netiek ierakstīta: ieraksts tiek "pauzēts", un video paliek tikai darbības.
Ja ainā ir JS kļūda vai tukša kartīte, aina tiek ierakstīta no jauna (≤ 2 reizes).

    uv run --no-project --with playwright --with pillow --with imageio-ffmpeg src/demo/video.py
    ... src/demo/video.py --tikai-salikt    # tikai salikt video no jau ierakstītajiem kadriem (bez slodzes vietnei)
"""
import argparse
import base64
import bisect
import json
import pathlib
import shutil
import subprocess
import sys
import time

SAKNE = pathlib.Path(__file__).resolve().parents[2]


def noklusejuma_izvade():
    """../demo-video blakus repo; no git worktree (.claude/worktrees/…) — blakus galvenajam repo."""
    try:
        kop = subprocess.run(["git", "rev-parse", "--path-format=absolute", "--git-common-dir"], cwd=SAKNE,
                             capture_output=True, text=True, check=True).stdout.strip()
        return pathlib.Path(kop).parent.parent / "demo-video"
    except Exception:
        return SAKNE.parent / "demo-video"

SKATS = {"width": 390, "height": 844}
DPR = 3
OGRE = {"latitude": 56.8162, "longitude": 24.6140}
FPS = 30
PARKLAJUMS = 0.3      # s, pāreja starp ainām
BEIGU_KARTE = 5.0     # s
SUBTITRS = (0.25, 5.75)  # subtitra logs no ainas sākuma (s)

AINAS = [
    ("sakums", "Krīze. Jūs vēlaties zināt vienu lietu: ko darīt."),
    ("ogre-pludi", "Viena rinda: „Ogre, plūdi”. Brīdinājums, lēmums, upes līmenis."),
    ("pulcesanas-vieta", "Tuvākā pulcēšanās vieta ar avotu un licenci"),
    ("adrese", "Jūsu adrese? Atbilde uzreiz."),
    ("112", "Dzīvībai bīstami? 112 vienmēr augšā."),
    ("bez-sakariem", "Darbojas bez interneta un bez elektrības"),
    ("datu-avoti", "Atvērtie dati: 20+ avoti, katrs ar licenci"),
]
BEIGAS = ("map.repo.lv", "Ko Jums vajag? Viena rinda — viens lēmums.",
          "VARAM / LATA „AI atvērto datu” hakatons 2026 · krīžu vadības virziens")

# Bez kursora, bez pieskāriena izgaismojuma, bez ritjoslām (video tīrībai; vietnes izskats citādi nemainās)
STILS = """*{cursor:none!important;-webkit-tap-highlight-color:transparent!important}
::-webkit-scrollbar{display:none!important}*{scrollbar-width:none!important}"""


class Kluda(Exception):
    pass


# ---------------------------------------------------------------- ieraksts

class Ieraksts:
    """CDP screencast → JPEG kadri diskā; segmenti = laika logi (sienas pulkstenis), kas paliek video."""

    def __init__(self, lapa, mape):
        self.mape = mape
        self.kadri = []          # (laiks, fails)
        self.segmenti = []       # [aina, t0, t1]
        self.aktivs = None
        self.cdp = lapa.context.new_cdp_session(lapa)
        self.cdp.on("Page.screencastFrame", self._kadrs)
        self.cdp.send("Page.startScreencast", {"format": "jpeg", "quality": 92, "maxWidth": SKATS["width"] * DPR,
                                               "maxHeight": SKATS["height"] * DPR, "everyNthFrame": 1})

    def _kadrs(self, p):
        t = p["metadata"].get("timestamp") or time.time()
        f = self.mape / f"{len(self.kadri):05d}.jpg"
        f.write_bytes(base64.b64decode(p["data"]))
        self.kadri.append((t, f.name))
        try:
            self.cdp.send("Page.screencastFrameAck", {"sessionId": p["sessionId"]})
        except Exception:
            pass

    def turpinat(self, aina):
        if self.aktivs is None:
            self.aktivs = [aina, time.time(), None]

    def pauze(self):
        if self.aktivs is not None:
            self.aktivs[2] = time.time()
            self.segmenti.append(self.aktivs)
            self.aktivs = None

    def atmest(self, aina):
        self.aktivs = None
        self.segmenti = [s for s in self.segmenti if s[0] != aina]

    def apturet(self):
        self.pauze()
        try:
            self.cdp.send("Page.stopScreencast")
        except Exception:
            pass
        (self.mape / "laika-josla.json").write_text(json.dumps({"kadri": self.kadri, "segmenti": self.segmenti}))


def ierakstit(bazes, izvade, kadri_mape):
    from playwright.sync_api import sync_playwright

    kadri_mape.mkdir(parents=True, exist_ok=True)
    stills = {}
    with sync_playwright() as p:
        b = p.chromium.launch()
        ctx = b.new_context(viewport=SKATS, device_scale_factor=DPR, is_mobile=True, has_touch=True, locale="lv-LV",
                            timezone_id="Europe/Riga", geolocation=OGRE, permissions=["geolocation"])
        ctx.add_init_script("addEventListener('DOMContentLoaded',()=>{const s=document.createElement('style');"
                            f"s.textContent={json.dumps(STILS)};document.head.append(s)}})")
        lapa = ctx.new_page()
        kludas = []
        lapa.on("pageerror", lambda e: kludas.append(str(e)))
        rec = Ieraksts(lapa, kadri_mape)

        # ---- palīgi ----
        def gaidit(ms):
            lapa.wait_for_timeout(ms)

        def tikla_miers(ms=10000):
            try:
                lapa.wait_for_load_state("networkidle", timeout=ms)
            except Exception:
                pass

        def atvert(url, aina):
            rec.pauze()
            lapa.goto(url, wait_until="load")
            tikla_miers(15000)
            gaidit(1200)

        def foto(aina, nos):
            rec.pauze()
            cels = izvade / f"{aina + 1:02d}-{nos}.png"
            lapa.screenshot(path=str(cels))
            stills[aina] = cels
            rec.turpinat(aina)

        def lapa_stavoklis(st):
            lapa.evaluate(f"Apaksa.atvert('{st}')")
            gaidit(450)

        def rakstit(teksts, aina):
            lapa.evaluate("document.getElementById('apaksa-saturs').scrollTo({top:0,behavior:'smooth'})")
            gaidit(500)
            lapa.click("#jautajums")
            lapa.fill("#jautajums", "")
            gaidit(250)
            lapa.type("#jautajums", teksts, delay=75)
            gaidit(400)
            lapa.press("#jautajums", "Enter")
            # kartīte gatava: rezultāts ir, nav "Meklē…"; gaidīšana pēc 1,2 s netiek ierakstīta
            gaidit(1200)
            rec.pauze()
            lapa.wait_for_function("(() => { const r = document.getElementById('rezultati');"
                                   " return r && !r.hidden && r.innerText.trim().length > 80 &&"
                                   " !/Meklē tuvākās|Meklē adresi|Ielādē…/.test(r.innerText.slice(0, 400)); })()",
                                   timeout=45000)
            tikla_miers(8000)
            gaidit(600)
            rec.turpinat(aina)

        def gaidit_pludus():
            """Plūdu zona (LVĢMC WMS caur /api/pludi) var atbildēt līdz ~45 s; gaidām ārpus ieraksta."""
            rec.pauze()
            try:
                lapa.wait_for_function("(() => { const r = document.getElementById('rez-pludi');"
                                       " return !r || !/Pārbauda/.test(r.innerText); })()", timeout=60000)
            except Exception:
                pass
            gaidit(500)

        def ritinat(konteiners, merkis_js, nobide=70, solis=38):
            """Gluda ritināšana ar page.mouse.wheel pa soļiem, līdz mērķis ir `nobide` px no konteinera augšas."""
            for _ in range(200):
                d = lapa.evaluate(f"""(() => {{ const k = document.querySelector('{konteiners}'); const m = ({merkis_js});
                    if (!k || !m) return 0;
                    // lapas augšdaļa (meklēšana + cilnes) ir "sticky": nobīdi skaita no tās apakšas
                    const c = k.querySelector('.lapa-cilnes'), aug = k.getBoundingClientRect().top;
                    const d = m.getBoundingClientRect().top - Math.max(aug, c ? c.getBoundingClientRect().bottom : aug) - {nobide};
                    const maks = k.scrollHeight - k.clientHeight - k.scrollTop;
                    return Math.max(-k.scrollTop, Math.min(d, maks)); }})()""")
                if abs(d) < 4:
                    return
                kaste = lapa.evaluate(f"(() => {{ const r = document.querySelector('{konteiners}').getBoundingClientRect();"
                                      " return [r.left + r.width / 2, r.top + Math.min(r.height / 2, 200)]; })()")
                lapa.mouse.move(*kaste)
                pirms = lapa.evaluate(f"document.querySelector('{konteiners}').scrollTop")
                lapa.mouse.wheel(0, max(-solis, min(solis, d)))
                gaidit(16)
                if lapa.evaluate(f"document.querySelector('{konteiners}').scrollTop") == pirms:  # ritenis neritina
                    lapa.evaluate(f"document.querySelector('{konteiners}').scrollBy(0, {max(-solis, min(solis, d))})")
                    gaidit(16)

        def virsraksts(re_):
            return (f"[...document.querySelectorAll('#rezultati h3')].find(h => /{re_}/i.test(h.textContent))")

        def kartite_ok():
            ok = lapa.evaluate("(() => { const r = document.getElementById('rezultati');"
                               " return !!r && !r.hidden && r.innerText.trim().length > 80; })()")
            if not ok:
                raise Kluda("tukša kartīte")

        # ---- ainas ----
        # Subtitrs redzams ainas pirmās ~5,5 s apakšējā trešdaļā: svarīgais (lēmums, 112, radio rinda) tiek parādīts
        # ekrāna augšpusē (lapa "pilna") vai pēc tam, kad subtitrs izzudis.
        def aina1(i):
            atvert(bazes, i)
            lapa_stavoklis("peek")
            # abas kartes vietas ielādē iepriekš, lai pārvietojoties nav pelēku flīžu
            lapa.evaluate("karte.setView([56.8162, 24.614], 13, {animate:false})")
            tikla_miers(6000)
            lapa.evaluate("karte.setView([56.862, 24.585], 13, {animate:false})")
            tikla_miers(6000)
            gaidit(800)
            rec.turpinat(i)
            gaidit(700)
            lapa.evaluate("karte.flyTo([56.8162, 24.614], 13, {duration: 3.6, easeLinearity: 0.15})")
            gaidit(3900)
            foto(i, AINAS[i][0])
            gaidit(600)
            lapa_stavoklis("puse")
            gaidit(700)
            lapa.click("#jautajums")
            gaidit(1300)

        def aina2(i):
            rec.turpinat(i)
            rakstit("Ogre, plūdi", i)
            kartite_ok()
            gaidit(900)
            lapa_stavoklis("pilna")
            gaidit(900)
            gaidit_pludus()
            rec.turpinat(i)
            ritinat("#apaksa-saturs", "document.getElementById('rez-lemums') || document.getElementById('rezultati')", 8, 20)
            gaidit(1800)
            ritinat("#apaksa-saturs", "document.getElementById('rez-pludi-bloks') || document.getElementById('rezultati')", 8, 16)
            foto(i, AINAS[i][0])
            gaidit(1900)
            ritinat("#apaksa-saturs", "document.getElementById('rez-udens') || document.getElementById('rez-pludi-bloks')", 8, 14)
            gaidit(1800)

        def aina3(i):
            rec.turpinat(i)
            ritinat("#apaksa-saturs", virsraksts("pulcēšan"), 10, 22)
            gaidit(1500)
            lapa.evaluate(f"(() => {{ const h = {virsraksts('pulcēšan')}; const s = h && h.nextElementSibling;"
                          " for (const x of s ? s.querySelectorAll('li:first-child .ca-avots, li:first-child .marsruts') : [])"
                          " x.style.transition = 'background .4s', x.style.background = '#fef08a'; })()")
            gaidit(600)
            foto(i, AINAS[i][0])
            gaidit(1500)
            ritinat("#apaksa-saturs", virsraksts("patvert") + f" || {virsraksts('Drošās vietas')}", 10, 16)
            gaidit(1900)

        def aina4(i):
            rec.turpinat(i)
            lapa_stavoklis("puse")
            gaidit(400)
            rakstit("Brīvības iela 12, Ogre, plūdi", i)
            kartite_ok()
            gaidit(1500)
            lapa_stavoklis("pilna")
            gaidit(700)
            gaidit_pludus()
            rec.turpinat(i)
            ritinat("#apaksa-saturs", "document.getElementById('rez-lemums') || document.getElementById('rezultati')", 8, 20)
            gaidit(1500)
            ritinat("#apaksa-saturs", "document.getElementById('rez-pludi-bloks') || document.getElementById('rezultati')", 8, 14)
            foto(i, AINAS[i][0])
            gaidit(1900)

        def aina5(i):
            rec.turpinat(i)
            lapa_stavoklis("puse")
            gaidit(400)
            rakstit("cilvēks nav pie samaņas", i)
            kartite_ok()
            if not lapa.evaluate("!!document.querySelector('#rezultati .draudi')"):
                raise Kluda("nav sarkanās 112 rindas")
            lapa_stavoklis("pilna")
            ritinat("#apaksa-saturs", "document.getElementById('rezultati')", 8, 20)
            gaidit(1600)
            foto(i, AINAS[i][0])
            gaidit(1800)
            ritinat("#apaksa-saturs", "document.querySelector('#rezultati .padoms') || document.getElementById('rezultati')", 60, 12)
            gaidit(1500)

        def aina6(i):
            atvert(bazes + "?demo=bez-sakariem&regions=100003470", i)
            lapa.wait_for_function("!!document.querySelector('.demo-kartite') &&"
                                   " !/Ielādē tuvākās/.test(document.getElementById('demo-saturs').innerText)", timeout=45000)
            tikla_miers(8000)
            gaidit(800)
            rec.turpinat(i)
            gaidit(1900)
            ritinat("#demo-saturs", "document.querySelector('.demo-kartite h3, .demo-kartite h2') || document.querySelector('.demo-kartite')", 6, 8)
            gaidit(1700)
            radio = ("[...document.querySelectorAll('#demo-saturs li')].find(l => /Radio 1/.test(l.textContent))")
            ritinat("#demo-saturs", radio, 30, 12)
            lapa.evaluate(f"(() => {{ const l = {radio}; if (l) l.style.transition='background .5s',"
                          " l.style.background='#fef08a'; })()")
            gaidit(1000)
            foto(i, AINAS[i][0])
            gaidit(1600)
            ritinat("#demo-saturs", "[...document.querySelectorAll('#demo-saturs *')].find(h => h.children.length === 0 &&"
                    " /Kur doties bez telefona/i.test(h.textContent)) || " + radio, 6, 14)
            gaidit(1800)

        def aina7(i):
            atvert(bazes, i)
            lapa.click("#cilne-slani")
            lapa_stavoklis("pilna")
            lapa.evaluate("document.getElementById('avoti').open = true")
            tikla_miers(8000)
            lapa.evaluate("document.getElementById('avoti').open = false")
            gaidit(300)
            rec.turpinat(i)
            gaidit(1200)
            ritinat("#apaksa-saturs", "document.getElementById('avoti')", 200, 18)
            gaidit(900)
            lapa.click("#avoti > summary")
            gaidit(1300)
            ritinat("#apaksa-saturs", "document.getElementById('avoti')", 8, 16)
            gaidit(1200)
            foto(i, AINAS[i][0])
            ritinat("#apaksa-saturs", "document.querySelector('#avoti-saraksts li:nth-child(12)') || "
                    "document.getElementById('avoti')", 8, 7)
            gaidit(900)

        for i, f in enumerate([aina1, aina2, aina3, aina4, aina5, aina6, aina7]):
            for meginajums in range(3):
                kludas.clear()
                try:
                    f(i)
                    rec.pauze()
                    if kludas:
                        raise Kluda("JS kļūda: " + kludas[0][:200])
                    print(f"aina {i + 1}: ok" + (f" (mēģinājums {meginajums + 1})" if meginajums else ""), flush=True)
                    break
                except Exception as e:
                    rec.atmest(i)
                    print(f"aina {i + 1}: {type(e).__name__}: {str(e)[:300]}; atkārto", flush=True)
                    if meginajums == 2:
                        raise
                    # stāvokli atjauno: ainas 2–5 sākas no kartes ar Ogri
                    if i in (1, 2, 3, 4):
                        atvert(bazes, i)
                        if i == 2:  # 3. aina turpina 2. ainas kartīti
                            lapa.click("#jautajums")
                            lapa.fill("#jautajums", "Ogre, plūdi")
                            lapa.press("#jautajums", "Enter")
                            lapa.wait_for_function("document.getElementById('rezultati').innerText.length > 200", timeout=45000)
                            gaidit_pludus()
                            lapa_stavoklis("pilna")
        rec.apturet()
        ctx.close()
        b.close()
    return stills


# ---------------------------------------------------------------- salikšana

def fonts(izmers, trekns=False):
    from PIL import ImageFont
    for f in (["segoeuib.ttf", "C:/Windows/Fonts/segoeuib.ttf", "DejaVuSans-Bold.ttf"] if trekns else
              ["segoeui.ttf", "C:/Windows/Fonts/segoeui.ttf", "DejaVuSans.ttf"]):
        try:
            return ImageFont.truetype(f, izmers)
        except OSError:
            continue
    return ImageFont.load_default(izmers)


def aplauzt(teksts, fonts_, platums):
    rindas, r = [], ""
    for v in teksts.split():
        m = (r + " " + v).strip()
        if fonts_.getlength(m) <= platums or not r:
            r = m
        else:
            rindas.append(r)
            r = v
    return rindas + [r] if r else rindas


class Formats:
    """Izvades formāts: izmērs, telefona ekrāna vieta (centrā horizontāli), fons ar rāmi, noapaļotu stūru maska."""

    def __init__(self, nos, w, h, tel_h, tel_y):
        from PIL import Image, ImageDraw
        self.nos, self.w, self.h = nos, w, h
        self.tel_h = tel_h
        self.tel_w = round(tel_h * SKATS["width"] / SKATS["height"])
        self.tel_xy = tel_xy = ((w - self.tel_w) // 2, tel_y)
        r = round(self.tel_w * 0.075)
        self.maska = Image.new("L", (self.tel_w, self.tel_h), 0)
        ImageDraw.Draw(self.maska).rounded_rectangle([0, 0, self.tel_w - 1, self.tel_h - 1], r, fill=255)
        # fons: tumšs vertikāls gradients + telefona rāmis (bezel) ar ēnu
        self.fons = Image.new("RGB", (w, h))
        d = ImageDraw.Draw(self.fons)
        for y in range(h):
            k = y / h
            d.line([(0, y), (w, y)], fill=(int(11 + 8 * k), int(17 + 6 * k), int(32 + 8 * k)))
        b = max(8, round(self.tel_w * 0.022))
        x, y = tel_xy
        d.rounded_rectangle([x - b - 2, y - b - 2, x + self.tel_w + b + 1, y + self.tel_h + b + 1], r + b + 2, fill=(52, 60, 76))
        d.rounded_rectangle([x - b, y - b, x + self.tel_w + b - 1, y + self.tel_h + b - 1], r + b, fill=(8, 10, 16))


def salikt(izvade, kadri_mape, ffmpeg):
    from PIL import Image, ImageDraw

    dati = json.loads((kadri_mape / "laika-josla.json").read_text())
    kadri = sorted(dati["kadri"])
    laiki = [k[0] for k in kadri]
    seg = [s for s in dati["segmenti"] if s[2] - s[1] > 0.05]
    # video laika josla: segmenti pēc kārtas; ainas sākums = pirmā segmenta sākums
    josla, v = [], 0.0
    for a, t0, t1 in seg:
        josla.append((v, v + t1 - t0, a, t0))
        v += t1 - t0
    ainu_sak = {}
    for v0, v1, a, _ in josla:
        ainu_sak.setdefault(a, v0)
    ainu_beig = {a: max(v1 for v0, v1, b, _ in josla if b == a) for a in ainu_sak}
    ilgums_ainas = v
    kopa = ilgums_ainas + BEIGU_KARTE
    print(f"ainas {ilgums_ainas:.1f} s + beigu kartīte {BEIGU_KARTE} s = {kopa:.1f} s;", "ainu ilgumi:",
          ", ".join(f"{a + 1}: {ainu_beig[a] - ainu_sak[a]:.1f}" for a in sorted(ainu_sak)), flush=True)

    def kadrs_pie(v):
        v = min(max(v, 0), ilgums_ainas - 1e-3)
        for v0, v1, a, t0 in josla:
            if v0 <= v < v1:
                t = t0 + (v - v0)
                break
        j = max(0, bisect.bisect_right(laiki, t) - 1)
        return kadri[j][1]

    kesa = {}

    def ekrans(fails, f):
        k = (fails, f.nos)
        if k not in kesa:
            if len(kesa) > 60:
                kesa.clear()
            im = Image.open(kadri_mape / fails).convert("RGB").resize((f.tel_w, f.tel_h), Image.LANCZOS)
            kesa[k] = im
        return kesa[k]

    # subtitri (SRT): katras ainas sākumā SUBTITRS logā
    srt = []
    for a in sorted(ainu_sak):
        s, e = ainu_sak[a] + SUBTITRS[0], min(ainu_sak[a] + SUBTITRS[1], ainu_beig[a] - 0.1)
        srt.append((s, e, AINAS[a][1], a))

    def ts(x):
        ms = round(x * 1000)
        return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"
    (izvade / "captions.srt").write_text("".join(f"{n}\n{ts(s)} --> {ts(e)}\n{t}\n\n" for n, (s, e, t, _) in enumerate(srt, 1)),
                                         encoding="utf-8")

    vert = Formats("vertikals", 1080, 1920, 1720, 70)
    hor = Formats("horizontals", 1920, 1080, 980, 50)

    F_SUB = fonts(56, True)
    F_LIELS, F_VID, F_MAZS = fonts(54, True), fonts(34), fonts(26)
    F_NR = fonts(30, True)

    def subtitrs_vert(im, teksts, alfa):
        if alfa <= 0:
            return
        rindas = aplauzt(teksts, F_SUB, 900)[:2]
        lh = 72
        h = 48 + lh * len(rindas)
        y0 = 1330
        sl = Image.new("RGBA", im.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(sl)
        d.rounded_rectangle([60, y0, 1020, y0 + h], 30, fill=(8, 12, 22, int(200 * alfa)))
        for n, r in enumerate(rindas):
            d.text((540, y0 + 24 + n * lh + lh / 2), r, font=F_SUB, fill=(255, 255, 255, int(255 * alfa)), anchor="mm")
        im.alpha_composite(sl)

    def sanu_teksts(im, aina, alfa):
        d = ImageDraw.Draw(im)
        # kreisā puse: zīmols + ainu saraksts
        d.text((110, 120), "map.repo.lv", font=F_LIELS, fill=(255, 255, 255, 255))
        d.text((110, 190), "Ko Jums vajag?", font=F_VID, fill=(148, 163, 184, 255))
        for n, (_, t) in enumerate(AINAS):
            y = 300 + n * 84
            akt = n == aina
            d.ellipse([110, y + 6, 134, y + 30], fill=(239, 68, 68, 255) if akt else (51, 65, 85, 255))
            for k, r in enumerate(aplauzt(t, F_MAZS, 470)[:2]):
                d.text((152, y + k * 32), r, font=F_MAZS, fill=(255, 255, 255, 255) if akt else (100, 116, 139, 255))
        if aina is None or alfa <= 0:
            return
        sl = Image.new("RGBA", im.size, (0, 0, 0, 0))
        d2 = ImageDraw.Draw(sl)
        x = hor.tel_xy[0] + hor.tel_w + 90
        d2.text((x, 330), f"{aina + 1} / {len(AINAS)}", font=F_NR, fill=(239, 68, 68, int(255 * alfa)))
        for k, r in enumerate(aplauzt(AINAS[aina][1], F_LIELS, 1920 - x - 90)):
            d2.text((x, 390 + k * 72), r, font=F_LIELS, fill=(255, 255, 255, int(255 * alfa)))
        im.alpha_composite(sl)

    beigu_kesa = {}

    def beigu_karte(f):
        if f.nos in beigu_kesa:
            return beigu_kesa[f.nos]
        im = Image.new("RGBA", (f.w, f.h), (11, 17, 32, 255))
        d = ImageDraw.Draw(im)
        cx, cy = f.w // 2, f.h // 2
        d.text((cx, cy - 120), BEIGAS[0], font=fonts(130 if f.w > f.h else 120, True), fill=(255, 255, 255), anchor="mm")
        d.line([(cx - 120, cy - 30), (cx + 120, cy - 30)], fill=(239, 68, 68), width=6)
        for k, r in enumerate(aplauzt(BEIGAS[1], fonts(48), f.w - 160)):
            d.text((cx, cy + 40 + k * 64), r, font=fonts(48), fill=(226, 232, 240), anchor="mm")
        for k, r in enumerate(aplauzt("Komanda · " + BEIGAS[2], fonts(32), f.w - 200)):
            d.text((cx, cy + 190 + k * 46), r, font=fonts(32), fill=(148, 163, 184), anchor="mm")
        d.text((cx, f.h - 90), "Prototips · atvērtie dati · bez MI izpildes laikā", font=fonts(26), fill=(100, 116, 139), anchor="mm")
        beigu_kesa[f.nos] = im
        return im

    def kadrs(f, v):
        if v >= ilgums_ainas:
            pec = v - ilgums_ainas
            bk = beigu_karte(f)
            if pec < 0.6:  # pāreja no pēdējās ainas
                return Image.blend(kadrs(f, ilgums_ainas - 1e-3).convert("RGBA"), bk, pec / 0.6)
            return bk
        aina = next(a for v0, v1, a, _ in josla if v0 <= v < v1) if v < ilgums_ainas else len(AINAS) - 1
        ekr = ekrans(kadrs_pie(v), f)
        # pāreja starp ainām
        for a in sorted(ainu_sak):
            b = ainu_sak[a]
            if a and abs(v - b) < PARKLAJUMS / 2:
                vec = ekrans(kadrs_pie(b - 1e-3), f)
                jaun = ekrans(kadrs_pie(b + 1e-3), f)
                ekr = Image.blend(vec, jaun, (v - b + PARKLAJUMS / 2) / PARKLAJUMS)
        im = f.fons.copy().convert("RGBA")
        im.paste(ekr, f.tel_xy, f.maska)
        s = ainu_sak[aina]
        rel = v - s
        if f is vert:
            alfa = min(1, max(0, (rel - SUBTITRS[0]) / 0.3), max(0, (SUBTITRS[1] - rel) / 0.3))
            subtitrs_vert(im, AINAS[aina][1], alfa)
            ImageDraw.Draw(im).text((540, 1868), "map.repo.lv", font=F_MAZS, fill=(148, 163, 184), anchor="mm")
        else:
            alfa = min(1, max(0, (rel - 0.1) / 0.4), max(0, (ainu_beig[aina] - v) / 0.3))
            sanu_teksts(im, aina, alfa)
        return im

    procesi = {}
    for f, nos in [(vert, "demo-vertikals.mp4"), (hor, "demo-horizontals.mp4")]:
        procesi[f.nos] = subprocess.Popen(
            [ffmpeg, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{f.w}x{f.h}", "-r", str(FPS),
             "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p",
             "-movflags", "+faststart", str(izvade / nos)], stdin=subprocess.PIPE)
    n = round(kopa * FPS)
    for k in range(n):
        v = k / FPS
        for f in (vert, hor):
            procesi[f.nos].stdin.write(kadrs(f, v).convert("RGB").tobytes())
        if k % (FPS * 10) == 0:
            print(f"  salikts {v:.0f}/{kopa:.0f} s", flush=True)
    for p in procesi.values():
        p.stdin.close()
        if p.wait():
            raise SystemExit("ffmpeg kļūda")
    return kopa, srt


# ---------------------------------------------------------------- pārbaude

def parbaudit(izvade, ffmpeg):
    from PIL import Image, ImageStat
    ffprobe = shutil.which("ffprobe")
    rez = {}
    for nos in ("demo-vertikals.mp4", "demo-horizontals.mp4"):
        cels = izvade / nos
        if ffprobe:
            d = json.loads(subprocess.run([ffprobe, "-v", "error", "-show_entries", "format=duration:stream=width,height,codec_name,r_frame_rate",
                                           "-of", "json", str(cels)], capture_output=True, text=True).stdout)
            rez[nos] = (float(d["format"]["duration"]), d["streams"][0])
        else:  # imageio-ffmpeg: ilgumu nolasa no ffmpeg -i
            o = subprocess.run([ffmpeg, "-i", str(cels)], capture_output=True, text=True).stderr
            h, m, s = o.split("Duration: ")[1].split(",")[0].split(":")
            rez[nos] = (int(h) * 3600 + int(m) * 60 + float(s), None)
        print(f"{nos}: {rez[nos][0]:.2f} s {rez[nos][1] or ''} {cels.stat().st_size / 1e6:.1f} MB")
        if not 85 <= rez[nos][0] <= 95:
            print(f"  BRĪDINĀJUMS: ilgums ārpus 85–95 s")
    for p in sorted(izvade.glob("0[1-7]-*.png")):
        st = ImageStat.Stat(Image.open(p).convert("L"))
        print(f"{p.name}: {Image.open(p).size}, pikseļu std {st.stddev[0]:.1f}" + ("  TUKŠS?" if st.stddev[0] < 8 else ""))
    return rez


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--url", default="https://map.repo.lv/")
    a.add_argument("--izvade", default=None, help="pēc noklusējuma ../demo-video blakus repo")
    a.add_argument("--tikai-salikt", action="store_true", help="neierakstīt no jauna, salikt no izvade/_kadri")
    args = a.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    izvade = pathlib.Path(args.izvade) if args.izvade else noklusejuma_izvade()
    izvade.mkdir(parents=True, exist_ok=True)
    kadri_mape = izvade / "_kadri"
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        import imageio_ffmpeg
        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    if not args.tikai_salikt:
        shutil.rmtree(kadri_mape, ignore_errors=True)
        vecais = izvade / "vecais"  # iepriekšējā ieraksta faili (vecā skripta nosaukumi) — nost no ceļa, nevis dzēst
        for p in [*izvade.glob("[01][0-9]-*.png"), *izvade.glob("*.webm")]:
            if p.name[:2] in {f"{n:02d}" for n in range(1, len(AINAS) + 1)} and any(p.stem[3:] == x for x, _ in AINAS):
                p.unlink()
            else:
                vecais.mkdir(exist_ok=True)
                shutil.move(p, vecais / p.name)
        sak = time.time()
        ierakstit(args.url.rstrip("/") + "/", izvade, kadri_mape)
        print(f"ieraksts: {time.time() - sak:.0f} s", flush=True)
    salikt(izvade, kadri_mape, ffmpeg)
    parbaudit(izvade, ffmpeg)


if __name__ == "__main__":
    main()
