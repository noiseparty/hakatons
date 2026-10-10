"""Latvijas Radio 1 FM raidītāju karte → statisks SVG lapā production/info.html (starp <!-- radio-karte:sākums/beigas -->)
un production/lr1.json (rezultāta kartītei: tuvākais raidītājs). Ievade: src/info/lr1_frekvences.json (frekvences no
latvijasradio.lsm.lv, raidītāju vietas ar avotu) un src/info/latvija_robeza.json (VZD robežas, vienkāršotas).

Etiķetes nepārklājas, jo katrai vietai JSON ir nobīde "etikete": [dx, dy] (SVG vienībās); ja nobīde ir liela, zīmē
vadlīniju. Melnbalts, drukājams. Palaišana no repozitorija saknes:
    python src/info/radio_karte.py
"""
import html
import json
import math
import pathlib
import re

SAKNE = pathlib.Path(__file__).resolve().parents[2]
FREKV = SAKNE / "src" / "info" / "lr1_frekvences.json"
ROBEZA = SAKNE / "src" / "info" / "latvija_robeza.json"
INFO = SAKNE / "production" / "info.html"
LR1_JSON = SAKNE / "production" / "lr1.json"

PLATUMS = 840
MALA = 14
LON0, LON1, LAT0, LAT1 = 20.90, 28.30, 55.62, 58.12
KX = math.cos(math.radians(57.0))
K = (PLATUMS - 2 * MALA) / ((LON1 - LON0) * KX)
AUGSTUMS = round((LAT1 - LAT0) * K + 2 * MALA)


def xy(lon, lat):
    return round(MALA + (lon - LON0) * KX * K, 1), round(MALA + (LAT1 - lat) * K, 1)


def cels(geom):
    """GeoJSON (Multi)Polygon → SVG path d."""
    poly = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    d = []
    for p in poly:
        for gredzens in p:
            pts = [xy(lon, lat) for lon, lat in gredzens]
            d.append("M" + " L".join(f"{x},{y}" for x, y in pts) + "Z")
    return " ".join(d)


def frekv_teksts(v):
    return " · ".join(f.replace(".", ",") for f in v)


def svg(dati, robeza):
    v = []
    v.append(f'<svg class="radio-karte" viewBox="0 0 {PLATUMS} {AUGSTUMS}" role="img" aria-labelledby="radio-karte-nos radio-karte-apr" xmlns="http://www.w3.org/2000/svg">')
    v.append('<title id="radio-karte-nos">Latvijas Radio 1 FM raidītāji kartē</title>')
    apr = "; ".join(f"{s['vieta']} {frekv_teksts(s['lr1'])} MHz" for s in dati["raiditaji"])
    v.append(f'<desc id="radio-karte-apr">{html.escape(apr)}</desc>')
    v.append('<g class="rk-pasv" fill="none" stroke="#b9c0c8" stroke-width="0.8">')
    for g in robeza["pasvaldibas"]:
        v.append(f'<path d="{cels(g)}"/>')
    v.append('</g>')
    v.append(f'<path class="rk-robeza" d="{cels(robeza["latvija"])}" fill="none" stroke="#1f2933" stroke-width="2.2" stroke-linejoin="round"/>')
    for s in dati["raiditaji"]:
        x, y = xy(s["lon"], s["lat"])
        dx, dy = s.get("etikete", [10, -8])
        lx, ly = x + dx, y + dy
        anchor = "end" if dx < 0 else "start"
        if math.hypot(dx, dy) > 22:
            v.append(f'<line x1="{x}" y1="{y}" x2="{lx - (4 if dx < 0 else -4) if abs(dx) > 6 else lx}" y2="{ly - 7}" stroke="#1f2933" stroke-width="1"/>')
        v.append(f'<circle cx="{x}" cy="{y}" r="6" fill="#1f2933" stroke="#fff" stroke-width="2"/>')
        v.append(f'<text x="{lx}" y="{ly}" text-anchor="{anchor}" class="rk-et">'
                 f'<tspan class="rk-v">{html.escape(s["vieta"])}</tspan> <tspan class="rk-f">{frekv_teksts(s["lr1"])}</tspan></text>')
    v.append('</svg>')
    return "\n".join(v)


def main():
    dati = json.loads(FREKV.read_text(encoding="utf-8"))
    robeza = json.loads(ROBEZA.read_text(encoding="utf-8"))
    bloks = (
        "<!-- radio-karte:sākums (ģenerēts ar src/info/radio_karte.py; nelabot ar roku) -->\n"
        '<figure class="radio-karte-fig">\n' + svg(dati, robeza) + "\n"
        f'<figcaption>LR1 frekvences (MHz) pie raidītājiem. Vietas aptuvenas; uztveršana atkarīga no reljefa un uztvērēja. '
        f'Avots: <a href="{html.escape(dati["avots_url"])}" target="_blank" rel="noopener">Latvijas Radio, „Frekvences”</a> '
        f'({html.escape(dati["nolasits"])}); robežas: VZD adrešu reģistrs (CC BY 4.0).</figcaption>\n'
        "</figure>\n<!-- radio-karte:beigas -->"
    )
    t = INFO.read_text(encoding="utf-8")
    if "<!-- radio-karte:sākums" in t:
        t = re.sub(r"<!-- radio-karte:sākums.*?<!-- radio-karte:beigas -->", lambda _m: bloks, t, flags=re.S)
    else:
        enkurs = '<p class="avots">Avots: <a href="https://latvijasradio.lsm.lv/lv/par-mums/frekvences/"'
        i = t.index(enkurs)
        t = t[:i] + bloks + "\n    " + t[i:]
    INFO.write_text(t, encoding="utf-8", newline="\n")
    LR1_JSON.write_text(json.dumps({
        "avots": dati["avots_url"], "nolasits": dati["nolasits"],
        "raiditaji": [{k: s[k] for k in ("vieta", "lr1", "lat", "lon")} for s in dati["raiditaji"]],
    }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"info.html: {len(dati['raiditaji'])} raidītāji; lr1.json")


if __name__ == "__main__":
    main()
