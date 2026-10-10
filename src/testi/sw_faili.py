"""production/sw.js SHELL_FAILI saraksts no lapām, nevis ar roku.

Sāk no publiskajām lapām (LAPAS), ņem to <script src>/<link href>/<a href> uz mūsu failiem, tad no katra atrastā
JS/CSS/JSON faila — pēdiņās esošus ceļus un CSS url(), kas ir esoši production/ faili, un manifest ikonas.
Nesaglabā /api/*, ārējās saites, og.png, slaidus un moderāciju (tie bezsaistē nav vajadzīgi).

    uv run --no-project --python 3.12 src/testi/sw_faili.py            # parāda sarakstu un atšķirību no sw.js
    uv run --no-project --python 3.12 src/testi/sw_faili.py --rakstit  # pārraksta SHELL_FAILI sw.js (VERSION mainiet paši)
    uv run --no-project --python 3.12 src/testi/sw_faili.py --parbaudit  # exit 1, ja sw.js sarakstā kaut kā trūkst

Pēc `git merge main`, ja kāds pievienojis jaunu JS/CSS, palaidiet ar --rakstit un nomainiet VERSION.
"""
import json
import pathlib
import re
import sys

PROD = pathlib.Path(__file__).resolve().parents[2] / "production"
LAPAS = ["index.html", "info.html", "statuss.html", "api.html", "trukstosie.html"]
NEVAJAG = {"og.png", "slaidi.html", "moderacija.html", "sw.js"}
HTML_ATS = re.compile(r'''(?:src|href)\s*=\s*["']([^"'#?]+)''')
CITAT = re.compile(r'''["'`]([A-Za-z0-9_./-]+\.(?:js|css|json|geojson|svg|png|html|webmanifest))["'`]''')
CSS_URL = re.compile(r'''url\(\s*["']?([^"')#?]+)''')
BLOKS = re.compile(r"(const SHELL_FAILI = \[\n)(.*?)(\n\];)", re.S)


def _faila_cels(bazes_mape: pathlib.Path, ats: str):
    if re.match(r"^[a-z]+:|^//|^/api/|^data:", ats):
        return None
    p = (PROD / ats.lstrip("/")) if ats.startswith("/") else (bazes_mape / ats)
    try:
        p = p.resolve()
        rel = p.relative_to(PROD.resolve()).as_posix()
    except ValueError:
        return None
    if not p.is_file() or rel in NEVAJAG or rel.startswith("slaidi/"):
        return None
    return rel


def shell_faili():
    atrasti, rinda = [], list(LAPAS)
    while rinda:
        rel = rinda.pop(0)
        if rel in atrasti:
            continue
        atrasti.append(rel)
        p = PROD / rel
        teksts = p.read_text(encoding="utf-8", errors="replace") if p.suffix not in (".png",) else ""
        atsauces = []
        if p.suffix == ".html":
            atsauces = HTML_ATS.findall(teksts)
            atsauces += [m for m in CITAT.findall(teksts)]  # iekļautie <script> bloki
        elif p.suffix in (".js", ".json", ".geojson"):
            atsauces = CITAT.findall(teksts)
        elif p.suffix == ".css":
            atsauces = CSS_URL.findall(teksts)
        elif p.suffix == ".webmanifest":
            atsauces = [i["src"] for i in json.loads(teksts).get("icons", [])]
        # JS fetch() ceļi ir relatīvi pret lapu (production/), CSS url() — pret CSS failu
        baze = p.parent if p.suffix == ".css" else PROD
        for a in atsauces:
            f = _faila_cels(baze, a)
            if f and f not in atrasti and f not in rinda:
                rinda.append(f)
    return ["./"] + atrasti


def _formatet(faili):
    rindas, rinda = [], "  "
    for f in faili:
        gab = f"'{f}', "
        if len(rinda) + len(gab) > 118:
            rindas.append(rinda.rstrip())
            rinda = "  "
        rinda += gab
    rindas.append(rinda.rstrip())
    return "\n".join(rindas)


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sw = PROD / "sw.js"
    teksts = sw.read_text(encoding="utf-8")
    m = BLOKS.search(teksts)
    esosie = re.findall(r"'([^']+)'", m.group(2)) if m else []
    faili = shell_faili()
    trukst = [f for f in faili if f not in esosie]
    lieki = [f for f in esosie if f not in faili]
    print(f"{len(faili)} faili; sw.js sarakstā trūkst: {trukst or '-'}; lieki: {lieki or '-'}")
    if "--rakstit" in sys.argv:
        sw.write_text(teksts[:m.start(2)] + _formatet(faili) + teksts[m.end(2):], encoding="utf-8", newline="\n")
        print("sw.js SHELL_FAILI pārrakstīts; nomainiet VERSION.")
    elif "--parbaudit" in sys.argv and trukst:
        sys.exit(1)
    elif "--parbaudit" not in sys.argv:
        print("\n".join(faili))


if __name__ == "__main__":
    main()
