"""Pārbaude pirms prezentācijas: viena komanda, kas izsauc visus API galapunktus (un tā iesilda kešus) un ar Playwright
izstaigā demo ceļu telefonā (390×844) un datorā (1280×800). Beigās zaļa/dzeltena/sarkana tabula; ar sarkanu — exit 1.

    uv run --no-project --python 3.12 --with playwright --with httpx src/testi/parbaude.py [--url https://map.repo.lv]
        [--screenshots DIR] [--bez-parluka] [--tikai-telefons]

Pirmo reizi: `uv run --no-project --with playwright playwright install chromium`.
Sarkans: API kļūda, JS kļūda konsolē, neizdevies pieprasījums, horizontāla ritināšana, "tel:" saite, "tu/tev" tekstā.
Dzeltens: lēna atbilde (> 5 s), API brīdinājums (piem., nepilnīga plūdu pārbaude, statusā ne viss "darbojas"),
pieskaršanās mērķi < 44 px telefonā. Tikai lasa: neko nemaina ne serverī, ne datubāzē (POST /api/meklejumi netiek sūtīts).
"""
import argparse
import os
import pathlib
import re
import sys
import time
from urllib.parse import quote

import httpx

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
if os.name == "nt":
    os.system("")  # ieslēdz ANSI krāsas Windows konsolē

ZALS, DZELT, SARK, PELEKS, BEIGAS = "\033[32m", "\033[33m", "\033[31m", "\033[90m", "\033[0m"
KRASA = {"OK": ZALS, "BRĪDIN.": DZELT, "KĻŪDA": SARK}

# Demo ceļš (notes/pitch.md, notes/ritdiena.md)
VAICAJUMI = ["plūdi Mednieku iela 9 Ogre", "nav elektrības Rīgā", "cilvēks nav pie samaņas"]
DEMO = ["vejs", "vetra", "drons", "nakts", "pludi-ogre", "vetra-2026", "bez-sakariem"]
OGRE = (56.8166, 24.6072)            # rezerve, ja adrešu meklēšana neatbild
JURMALA = (56.964556, 23.735869)     # Melluži, Dubultu prospekts 105 (CA plānā kļūdaini 56.064556)
LENS_S = 5.0
# Zināmi, nekaitīgi pieprasījumi: LVĢMC plūdu WMS flīzes ārpus zonām mēdz atbildēt 404; POST skaitīšana
IGNORET = [re.compile(r"geo-dpps\.viss\.gov\.lv"), re.compile(r"/api/meklejumi$")]
# Emocijzīmes UI vairs nelieto (ikonas/ikonas.svg): katra redzamā teksta emocijzīme ir kļūda
EMOCIJZIMES = re.compile("[🀀-🫿☀-⛿✀-✒✔✖-➿⏩-⏺⬇▶■◎️]")
TU_FORMAS = re.compile(r"(?<![\wĀ-ſ])(tu|tev|tevi|tavs|tava|tavu|tavā|tavi|tavas|tavam|tavai|tavus|tavās|tavos)"
                       r"(?![\wĀ-ſ])", re.IGNORECASE)

rezultati = []  # (daļa, pārbaude, statuss, detaļas)


def pieraksts(dala, nos, statuss, detalas):
    rezultati.append((dala, nos, statuss, detalas))
    print(f"  {KRASA[statuss]}{statuss:8}{BEIGAS} {nos:34} {detalas}")


# ---------- 1. API ----------

def api_parbaude(bazes_url):
    print(f"\n1. API ({bazes_url}/api/*) — arī iesilda kešus\n")
    klients = httpx.Client(base_url=bazes_url, headers={"User-Agent": "map.repo.lv parbaude.py"}, follow_redirects=True)

    def iegut(nos, cels, timeout=30, kluda_kluss=False):
        t0 = time.monotonic()
        try:
            r = klients.get(cels, timeout=timeout)
        except httpx.HTTPError as e:
            if not kluda_kluss:
                pieraksts("API", nos, "KĻŪDA", f"{type(e).__name__}: {e}"[:150])
            return None, None
        ilgums = time.monotonic() - t0
        info = f"{r.status_code} · {ilgums:4.1f} s · {len(r.content) / 1024:6.1f} KB"
        try:
            dati = r.json()
        except ValueError:
            dati = None
        if r.status_code == 202:  # avots vēl rēķina (piem., plūdu WMS lēns) — atbilde būs nākamajā pieprasījumā
            if not kluda_kluss:
                pieraksts("API", nos, "BRĪDIN.", f"{info} · avots vēl pārbauda (202), mēģiniet pēc brīža")
            return None, None
        if r.status_code != 200:
            kluda = dati.get("kluda") if isinstance(dati, dict) else r.text[:80]
            if not kluda_kluss:
                pieraksts("API", nos, "KĻŪDA", f"{info} · {kluda}")
            return None, None
        return dati, (info, ilgums)

    def zinot(nos, cels, fakts, timeout=30, atkartot=False):
        dati, meta = iegut(nos, cels, timeout, kluda_kluss=atkartot)
        if dati is None and atkartot:  # lēns augšupējais avots (plūdu WMS): otrais mēģinājums parasti jau no kešas
            dati, meta = iegut(nos, cels, timeout)
            if dati is not None:
                meta = (meta[0] + " · izdevās tikai 2. mēģinājumā", meta[1] + LENS_S)
        if dati is None:
            return None
        info, ilgums = meta
        try:
            statuss, teksts = fakts(dati)
        except Exception as e:  # noqa: BLE001 — formāts mainījies
            statuss, teksts = "KĻŪDA", f"negaidīts formāts: {type(e).__name__}: {e}"[:120]
        if statuss == "OK" and ilgums > LENS_S:
            statuss, teksts = "BRĪDIN.", teksts + f" (lēni: {ilgums:.1f} s)"
        pieraksts("API", nos, statuss, f"{info} · {teksts}")
        return dati

    zinot("veseliba", "/api/veseliba", lambda d: ("OK" if d.get("ok") else "KĻŪDA", f"ok={d.get('ok')}"))
    zinot("kategorijas", "/api/kategorijas",
          lambda d: ("OK" if d else "KĻŪDA", f"{len(d)} slāņi, {sum(k['skaits'] for k in d)} objekti"))
    zinot("regioni", "/api/regioni", lambda d: ("OK" if len(d) > 100 else "KĻŪDA", f"{len(d)} reģioni"))
    adr = zinot("adreses (Brīvības 15 Ogre)", "/api/adreses?q=" + quote("Brīvības 15 Ogre"),
                lambda d: ("OK" if d else "KĻŪDA", d[0]["adrese"] if d else "nav atrasta"))
    mednieku = zinot("adreses (Mednieku 9 Ogre)", "/api/adreses?q=" + quote("Mednieku iela 9 Ogre"),
                     lambda d: ("OK" if d else "BRĪDIN.", d[0]["adrese"] if d else "nav atrasta"))
    ogre = (mednieku[0]["lat"], mednieku[0]["lon"]) if mednieku else (adr[0]["lat"], adr[0]["lon"]) if adr else OGRE

    def bridinajumi_fakts(d):
        b = d["bridinajumi"]
        return "OK", (f"{len(b)} spēkā, maks. līmenis {max(x['limenis'] for x in b)}: " +
                      "; ".join(f"{x['krasa']} {x['paradiba']}" for x in b[:3]) if b else "spēkā esošu brīdinājumu nav")
    zinot("bridinajumi", "/api/bridinajumi", bridinajumi_fakts)

    def pludi_fakts(d):
        t = ("zona: JĀ (" + ", ".join(f"{v['veids']} {v['varbutiba_proc']} %" for v in d["veidi"]) + ")") if d["zona"] else "zona: nē"
        return ("BRĪDIN." if d.get("nepilnigi") else "OK"), t + (" · nepilnīgi (daļa WMS neatbildēja)" if d.get("nepilnigi") else "")
    zinot("pludi (Mednieku 9 Ogre)", f"/api/pludi?lat={ogre[0]}&lon={ogre[1]}", pludi_fakts, timeout=90, atkartot=True)
    zinot("pludi (Jūrmala, Melluži)", f"/api/pludi?lat={JURMALA[0]}&lon={JURMALA[1]}", pludi_fakts, timeout=90, atkartot=True)

    def udens_fakts(d):
        s = d["stacijas"][0]
        return ("BRĪDIN." if s.get("vecs") else "OK"), f"{s['nosaukums']}: {s['limenis_cm']} cm, 24 h {s.get('izmaina_24h_cm')} cm" + \
            (" · dati novecojuši" if s.get("vecs") else "")
    zinot("udens (Ogre)", f"/api/udens?lat={ogre[0]}&lon={ogre[1]}&limit=1", udens_fakts)

    def prognozes_fakts(d):
        riski = d.get("riski") or {}
        paaugst = sum(1 for r in riski.values() if r.get("sodien", 0) >= 1)
        ok = bool(d.get("dienas"))
        return ("OK" if ok else "BRĪDIN."), (f"{len(d['zinas'])} ziņas, dienas {', '.join(x['nosaukums'] for x in d['dienas'])}, "
                                             f"{len(d['bridinajumu_poligoni'])} brīd. poligoni" +
                                             (f", šodien paaugstināts risks {paaugst} novados" if riski else "") +
                                             ("" if ok else " · prognozes dati nav ielādēti (tikai brīdinājumi)"))
    zinot("prognozes", "/api/prognozes", prognozes_fakts, timeout=120)
    zinot("prognozes/robezas", "/api/prognozes/robezas",
          lambda d: ("OK" if len(d["features"]) >= 40 else "KĻŪDA", f"{len(d['features'])} robežas"))

    def statuss_fakts(d):
        k = d["komponenti"]
        slikti = [f"{x['nosaukums']}: {x['stavoklis']}" for x in k if x["stavoklis"] != "darbojas"]
        return ("BRĪDIN." if slikti else "OK"), f"{len(k) - len(slikti)}/{len(k)} darbojas" + \
            (" · " + "; ".join(slikti)[:200] if slikti else "")
    zinot("statuss", "/api/statuss", statuss_fakts)
    zinot("zibens", "/api/zibens", lambda d: (
        "OK" if d.get("skaits") is not None else "BRĪDIN.",
        f"pēdējās {d['minutes']} min: {d['skaits']} izlādes; LVĢMC 24 h šūnas ar zibeni: "
        f"{len(d['rezgis_24h']['sunas']) if d.get('rezgis_24h') else 'nav datu'}"))
    zinot("augsne (Ogre)", f"/api/augsne?lat={ogre[0]:.2f}&lon={ogre[1]:.2f}", lambda d: (
        "OK", f"{d['nokrisni_pagatne_mm']} mm / {d['dienas_pagatne']} d, augsne {d['augsne']}"))

    def celi_fakts(d):
        if not d.get("konfigurets"):
            return "BRĪDIN.", d.get("piezime", "nav konfigurēts")
        nep = d.get("nepieejami") or []
        return ("BRĪDIN." if nep else "OK"), f"{len(d['notikumi'])} notikumi" + (f" · nepieejami: {', '.join(nep)}" if nep else "")
    zinot("celi", "/api/celi", celi_fakts)

    def satiksme_fakts(d):
        kopas = d.get("kopas") or {}
        labi = [k for k, v in kopas.items() if v.get("pieejams")]
        slikti = [f"{k}: {v.get('kluda') or ('nav konfigurēts' if not v.get('konfigurets') else 'nav pieejams')}"
                  for k, v in kopas.items() if not v.get("pieejams")]
        return ("BRĪDIN." if slikti else "OK"), f"kopas OK: {', '.join(labi) or '—'}" + (f" · nestrādā: {'; '.join(slikti)}"[:220] if slikti else "")
    zinot("satiksme", "/api/satiksme", satiksme_fakts)
    zinot("meklejumi/top", "/api/meklejumi/top?n=3", lambda d: (
        "OK", f"{len(d.get('vaicajumi', []))} populāri vaicājumi"))
    klients.close()


# ---------- 2. Pārlūks ----------

PARBAUDES_JS = r"""() => {
  const redzams = el => { const r = el.getBoundingClientRect(), s = getComputedStyle(el);
    return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none' && r.bottom > 0 && r.top < innerHeight; };
  const mazi = [];
  const sel = 'button, input:not([type=checkbox]):not([type=radio]):not([type=hidden]), select, summary, [role=button], a.galvena, .marsruts a, .apaksa-darbiba, .demo-saraksts button';
  for (const el of document.querySelectorAll(sel)) {
    if (!redzams(el) || el.closest('.leaflet-control-attribution')) continue;
    const r = el.getBoundingClientRect();
    if (r.height < 43.5 || r.width < 43.5) mazi.push(`${el.tagName.toLowerCase()}${el.id ? '#' + el.id : el.className && typeof el.className === 'string' ? '.' + el.className.split(' ')[0] : ''} „${(el.textContent || el.getAttribute('aria-label') || '').trim().slice(0, 20)}” ${Math.round(r.width)}×${Math.round(r.height)}`);
  }
  return {
    parplude: document.documentElement.scrollWidth > innerWidth + 1 ? document.documentElement.scrollWidth - innerWidth : 0,
    tel: [...document.querySelectorAll('a[href^="tel:"]')].map(a => a.getAttribute('href')),
    teksts: document.body.innerText,
    mazi,
  };
}"""


# Telefonā katrs kartes uznirstošais logs (popup) ir pilnībā ekrānā un ✕ ir sasniedzams: pa 3 nejaušiem marķieriem no
# katra slāņa (grupē pēc krāsas) + meklēšanas rezultāta marķieri. Logu atver kartes centrā ar to pašu saturu un autoPan.
POPUP_JS = r"""async () => {
  const grupas = {};
  const visi = [...(typeof objektuSlanis !== 'undefined' ? objektuSlanis.getLayers() : [])];
  karte.eachLayer(l => { if (l.getPopup?.() && !visi.includes(l)) visi.push(l); });
  for (const l of visi) if (l.getPopup?.()) (grupas[l.options.fillColor || l.options.color || 'cits'] ||= []).push(l);
  const sliktie = [];
  let parbauditi = 0;
  for (const [k, ls] of Object.entries(grupas)) {
    for (const l of ls.sort(() => Math.random() - .5).slice(0, 3)) {
      const c = l.getPopup().getContent();
      const saturs = typeof c === 'function' ? c(l) : c;
      const ll = l.getLatLng ? l.getLatLng() : karte.getCenter();
      const p = L.popup(l.getPopup().options).setLatLng(ll).setContent(saturs).openOn(karte);
      await new Promise(r => setTimeout(r, 450));
      const w = p.getElement()?.querySelector('.leaflet-popup-content-wrapper');
      const x = p.getElement()?.querySelector('.leaflet-popup-close-button');
      parbauditi++;
      if (w) {
        const r = w.getBoundingClientRect(), xr = x?.getBoundingClientRect();
        const ara = r.top < -1 || r.left < -1 || r.bottom > innerHeight + 1 || r.right > innerWidth + 1;
        const xAra = xr && (xr.top < 0 || xr.bottom > innerHeight || xr.width < 43.5);
        if (ara || xAra) sliktie.push(`${k}: ${Math.round(r.left)},${Math.round(r.top)} ${Math.round(r.width)}×${Math.round(r.height)}${xAra ? ' (✕ ārpus/mazs)' : ''}`);
      }
      karte.closePopup(p);
    }
  }
  return { parbauditi, sliktie };
}"""


def parluka_parbaude(bazes_url, ekrani, tikai_telefons):
    from playwright.sync_api import sync_playwright
    from playwright.sync_api import TimeoutError as PwTimeout

    print(f"\n2. Demo ceļš pārlūkā ({bazes_url})")
    skati = [("telefons", {"width": 390, "height": 844}, True)] + ([] if tikai_telefons else [("dators", {"width": 1280, "height": 800}, False)])
    with sync_playwright() as p:
        parluks = p.chromium.launch()
        for skats, vp, mob in skati:
            print(f"\n  — {skats} {vp['width']}×{vp['height']}")
            # service_workers="block": citādi lokāli (src/demo/lokali.py) sw.js apiet /api starpniekserveri
            ctx = parluks.new_context(viewport=vp, is_mobile=mob, has_touch=mob, device_scale_factor=2 if mob else 1,
                                      locale="lv-LV", service_workers="block")
            # skaitīšanas POST neiet uz serveri (pārbaude nedrīkst mainīt "Biežāk meklēto")
            ctx.route("**/api/meklejumi", lambda r: r.fulfill(status=204, body="") if r.request.method == "POST" else r.continue_())
            lapa = ctx.new_page()
            lapa.set_default_timeout(30000)
            notikumi = []

            def ignorets(url):
                return any(r.search(url) for r in IGNORET)
            lapa.on("console", lambda m: notikumi.append(("konsole", m.text)) if m.type == "error" and not ignorets(m.location.get("url", "") + m.text) else None)
            lapa.on("pageerror", lambda e: notikumi.append(("JS", str(e))))
            lapa.on("requestfailed", lambda r: notikumi.append(("pieprasījums", f"{r.url[:110]} {r.failure}")) if not ignorets(r.url) and "net::ERR_ABORTED" not in (r.failure or "") else None)
            lapa.on("response", lambda r: notikumi.append(("HTTP", f"{r.status} {r.url[:110]}")) if r.status >= 400 and not ignorets(r.url) else None)
            n = [0]

            def solis(nos, darbiba):
                notikumi.clear()
                t0 = time.monotonic()
                kluda = None
                try:
                    darbiba()
                except PwTimeout as e:
                    kluda = f"taimauts: {str(e).splitlines()[0][:120]}"
                except Exception as e:  # noqa: BLE001
                    kluda = f"{type(e).__name__}: {str(e).splitlines()[0][:120]}"
                lapa.wait_for_timeout(600)
                try:
                    m = lapa.evaluate(PARBAUDES_JS)
                except Exception as e:  # noqa: BLE001 — lapa pārlādējas
                    m = {"parplude": 0, "tel": [], "teksts": "", "mazi": []}
                    notikumi.append(("JS", f"pārbaude neizdevās: {e}"[:120]))
                n[0] += 1
                if ekrani:
                    lapa.screenshot(path=str(pathlib.Path(ekrani) / f"{skats}_{n[0]:02d}_{re.sub(r'[^a-z0-9]+', '-', nos.lower())[:40]}.png"))
                sarkani = ([kluda] if kluda else []) + [f"{t}: {x}"[:160] for t, x in notikumi]
                if m["parplude"]:
                    sarkani.append(f"horizontāla ritināšana: +{m['parplude']} px")
                if m["tel"]:
                    sarkani.append(f"tel: saites: {m['tel'][:3]}")
                tu = sorted({x.group(0) for x in TU_FORMAS.finditer(m["teksts"])})
                if tu:
                    konteksts = [m["teksts"][max(0, x.start() - 25):x.end() + 25].replace("\n", " ") for x in TU_FORMAS.finditer(m["teksts"])][:2]
                    sarkani.append(f"'tu' forma tekstā: {tu} — {konteksts}")
                emo = sorted(set(EMOCIJZIMES.findall(m["teksts"])))
                if emo:
                    sarkani.append(f"emocijzīmes tekstā: {emo[:8]}")
                dzelteni = [f"< 44 px: {len(m['mazi'])} — " + "; ".join(m["mazi"][:4])] if mob and m["mazi"] else []
                ilgums = time.monotonic() - t0
                statuss = "KĻŪDA" if sarkani else "BRĪDIN." if dzelteni else "OK"
                pieraksts(skats, nos, statuss, f"{ilgums:4.1f} s" + (" · " + " | ".join(sarkani + dzelteni) if sarkani or dzelteni else ""))

            def atvert_sakumu():
                lapa.goto(bazes_url + "/", wait_until="networkidle", timeout=60000)
            solis("sākumlapa", atvert_sakumu)

            for v in VAICAJUMI:
                def meklet(v=v):
                    lapa.fill("#jautajums", v)
                    lapa.press("#jautajums", "Enter")
                    lapa.wait_for_selector("#rezultati .talak", timeout=40000)
                    lapa.wait_for_timeout(1500)
                solis(f"meklēt: {v}", meklet)
                if mob:
                    def popupi(v=v):
                        r = lapa.evaluate(POPUP_JS)
                        if r["sliktie"]:
                            raise RuntimeError(f"{len(r['sliktie'])}/{r['parbauditi']} logi neietilpst ekrānā: " + "; ".join(r["sliktie"][:3]))
                    solis(f"popupi ekrānā: {v[:20]}", popupi)

            for kods in DEMO:
                def demo(kods=kods):
                    # ne "networkidle": LVĢMC plūdu WMS flīzes (pludi-ogre) atbild 5–30 s, bet kartīte gatava ~4 s
                    lapa.goto(f"{bazes_url}/?demo={kods}", wait_until="domcontentloaded", timeout=60000)
                    lapa.wait_for_function("document.body.classList.contains('demo-aktivs') && !!document.querySelector('.demo-kartite')"
                                           " && !document.querySelector('#demo-saturs').textContent.includes('Ielādē tuvākās')", timeout=30000)
                    lapa.wait_for_timeout(800)
                solis(f"?demo={kods}", demo)

            def beigt():
                if not lapa.locator('#demo-saturs [data-darbiba="beigt"]').is_visible():
                    lapa.click("#demo-cilne")
                    lapa.wait_for_timeout(400)
                lapa.click('#demo-saturs [data-darbiba="beigt"]')
                lapa.wait_for_function("!document.body.classList.contains('demo-aktivs')", timeout=10000)
            solis("Beigt demo", beigt)

            def prognoze():
                lapa.goto(bazes_url + "/", wait_until="networkidle", timeout=60000)
                lapa.wait_for_selector("#prognozes:not([hidden])", state="attached", timeout=60000)  # telefonā — slēptā cilnē
                if lapa.locator("#cilne-situacija").is_visible():  # telefonā prognoze ir lapas cilnē "Situācija tagad"
                    lapa.click('.apaksa-stavokli [data-st="pilna"]')
                    lapa.click("#cilne-situacija")
                elif not lapa.locator("#prognozes.atverts").count():
                    lapa.click(".prog-poga")
                lapa.wait_for_selector(".prog-zina", timeout=20000)
            solis("Prognoze", prognoze)

            def riski():
                if lapa.locator("#prognozes.atverts .prog-aizvert").is_visible():
                    lapa.click(".prog-aizvert")
                poga = lapa.locator('[data-riski="sodien"]')
                if not poga.count():
                    raise RuntimeError("riska kartes slēdža nav (vai #65 ir sapludināts?)")
                poga.click()
                lapa.wait_for_selector(".riski-legenda:not([hidden])", timeout=10000)
            solis("Riska karte (šodien)", riski)

            def avoti():
                if lapa.locator("#cilne-slani").is_visible():  # telefonā slāņi un avoti ir lapas cilnē "Kartes slāņi"
                    lapa.click('.apaksa-stavokli [data-st="pilna"]')
                    lapa.click("#cilne-slani")
                elif mob and lapa.locator("body.panelis-slegts").count():
                    lapa.click("#panelis-poga")
                if lapa.locator("#dv-atvilktne[hidden]").count():  # datorā (darbvirsma.js) avoti ir "Slāņu vadība" atvilktnē
                    lapa.click('.dv-nav [data-dv="slani"]')
                lapa.click("#avoti > summary")
                lapa.wait_for_selector("#avoti-saraksts li", timeout=15000)
            solis("Datu avoti", avoti)

            def statuss():
                lapa.goto(bazes_url + "/statuss.html", wait_until="networkidle", timeout=60000)
            solis("statuss.html", statuss)

            def info():
                lapa.goto(bazes_url + "/info.html", wait_until="networkidle", timeout=60000)
            solis("info.html", info)
            ctx.close()
        parluks.close()


def main():
    a = argparse.ArgumentParser(description="map.repo.lv pārbaude pirms prezentācijas")
    a.add_argument("--url", default="https://map.repo.lv")
    a.add_argument("--screenshots", metavar="DIR", help="saglabāt ekrānuzņēmumus katram solim")
    a.add_argument("--bez-parluka", action="store_true", help="tikai API")
    a.add_argument("--tikai-telefons", action="store_true", help="pārlūkā tikai 390×844")
    arg = a.parse_args()
    url = arg.url.rstrip("/")
    if arg.screenshots:
        pathlib.Path(arg.screenshots).mkdir(parents=True, exist_ok=True)
    t0 = time.monotonic()
    api_parbaude(url)
    if not arg.bez_parluka:
        parluka_parbaude(url, arg.screenshots, arg.tikai_telefons)

    print(f"\n3. Kopsavilkums ({time.monotonic() - t0:.0f} s)\n")
    for dala in dict.fromkeys(r[0] for r in rezultati):
        rindas = [r for r in rezultati if r[0] == dala]
        sk = {s: sum(1 for r in rindas if r[2] == s) for s in KRASA}
        print(f"  {dala:9} {ZALS}{sk['OK']:3} OK{BEIGAS}  {DZELT}{sk['BRĪDIN.']:3} brīdin.{BEIGAS}  {SARK}{sk['KĻŪDA']:3} kļūdas{BEIGAS}")
        for r in rindas:
            if r[2] == "KĻŪDA":
                print(f"     {SARK}✗ {r[1]}{BEIGAS} {PELEKS}{r[3][:200]}{BEIGAS}")
    sarkans = any(r[2] == "KĻŪDA" for r in rezultati)
    print(f"\n  {SARK + 'SARKANS: ir kļūdas (sk. augstāk)' if sarkans else ZALS + 'ZAĻŠ: viss strādā'}{BEIGAS}\n")
    sys.exit(1 if sarkans else 0)


if __name__ == "__main__":
    main()
