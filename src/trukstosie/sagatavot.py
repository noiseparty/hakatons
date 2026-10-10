"""notes/missing_data.md → production/trukstosie.html ("Ko vēl vajadzētu publicēt"), tādā pašā stilā kā info.html.

Tabulas rindas kļūst par kartītēm (telefonā 6 kolonnas nav lasāmas). Palaišana no repozitorija saknes:
    python src/trukstosie/sagatavot.py
"""

import html
import re
from pathlib import Path

SAKNE = Path(__file__).resolve().parents[2]
AVOTS = SAKNE / "notes" / "missing_data.md"
MERKIS = SAKNE / "production" / "trukstosie.html"
# Pitča piezīmes (iekšējas) publiskajā lapā nerāda
IZLAIST_SADALAS = ("Ko sakām pitčā",)
IZLAIST_RINDKOPAS = ("Īsā versija slaidam",)


# ⚠ → ikonu sprainta brīdinājuma zīme (kā visā lapā, #108): emocijzīmes telefonos izskatās dažādi
UZMANIBU = '<svg class="ik" aria-hidden="true" focusable="false"><use href="ikonas/ikonas.svg#uzmanibu"></use></svg>'


# Iekšējie repozitorija ceļi (`notes/…`) publiskajā lapā → dokumenta nosaukums ar saiti uz GitHub, bez ceļa
REPO = "https://github.com/noiseparty/hakatons/blob/main/"
DOKUMENTI = {
    "notes/research/02": ("Latvijas atvērto datu inventārs krīzes kartei", "notes/research/02_latvia_open_data_inventory.md"),
    "notes/research/04": ("LVĢMC un citi oficiālie dati", "notes/research/04_lvgmc_un_oficialie_dati.md"),
    "notes/research/05": ("avotu pārbaude 2026-10-10", "notes/research/05_avoti_parbaude_2026-10-10.md"),
    "notes/demo-scenariji.md": ("demo scenāriju datu pārskats", "notes/demo-scenariji.md"),
    "notes/ca-plani-kvalitate.md": ("CA plānu kvalitātes pārskats", "notes/ca-plani-kvalitate.md"),
}


def dokumenta_saite(cels):
    nos, fails = DOKUMENTI.get(cels, (None, None))
    if not nos:  # nezināms ceļš: rāda tikai faila vārdu bez mapēm un paplašinājuma
        return html.escape(re.sub(r"\.md$", "", cels.rsplit("/", 1)[-1]).replace("_", " ").replace("-", " "))
    return f'<a href="{REPO}{fails}" target="_blank" rel="noopener">{html.escape(nos)}</a>'


def bez_celiem(teksts):
    """`notes/research/02`, `04`, `05` → trīs nosaukumi; `notes/x.md` → nosaukums (pirms html.escape)."""
    def petijumi(m):
        nri = [m.group(1)] + re.findall(r"`(\d\d)`", m.group(2))
        return "\0".join(f"notes/research/{n}" for n in nri)
    teksts = re.sub(r"`notes/research/(\d\d)`((?:, `\d\d`)*)", petijumi, teksts)
    teksts = re.sub(r"`(notes/[\w./-]+?)`", r"\1", teksts)
    return teksts


def iekļauts(teksts):
    """Markdown rindiņa → HTML: **treknraksts**, `kods`, ⚠ → ikona, notes/… ceļi → nosaukumi; viss pārējais aizsargāts."""
    t = html.escape(bez_celiem(teksts), quote=False).replace("⚠️", "⚠").replace("⚠", UZMANIBU)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"`(.+?)`", r"<code>\1</code>", t)
    t = re.sub(r"notes/[\w./-]*\w", lambda m: dokumenta_saite(m.group(0)), t)
    return t.replace("\0", ", ")


def sunas(rinda):
    return [s.strip() for s in rinda.strip().strip("|").split("|")]


def sadalas(md):
    """[(virsraksts, [rindas])] pa "## " sadaļām; ievads — sadaļa ar virsrakstu None."""
    rez, virsraksts, rindas = [], None, []
    for r in md.splitlines():
        if r.startswith("## "):
            rez.append((virsraksts, rindas))
            virsraksts, rindas = r[3:].strip(), []
        elif not r.startswith("# "):
            rindas.append(r)
    rez.append((virsraksts, rindas))
    return rez


def bloks(rindas):
    out, tabula, saraksts = [], [], []

    def beigt_tabulu():
        if not tabula:
            return
        galva, *dati = [sunas(r) for r in tabula if not re.match(r"^\|\s*-", r)]
        for d in dati:
            nr, nosaukums, *parejie = d
            lauki = "".join(f"<dt>{iekļauts(g)}</dt><dd>{iekļauts(v)}</dd>" for g, v in zip(galva[2:], parejie))
            out.append(f'<article class="dati"><h3><span class="nr">{iekļauts(nr)}</span> {iekļauts(nosaukums)}</h3><dl>{lauki}</dl></article>')
        tabula.clear()

    def beigt_sarakstu():
        if saraksts:
            tags = "ol" if saraksts[0][0] else "ul"
            out.append(f"<{tags}>" + "".join(f"<li>{iekļauts(t)}</li>" for _, t in saraksts) + f"</{tags}>")
            saraksts.clear()

    for r in rindas:
        if r.startswith("|"):
            beigt_sarakstu()
            tabula.append(r)
            continue
        beigt_tabulu()
        if m := re.match(r"^(\d+)\.\s+(.*)", r):
            saraksts.append((True, m.group(2)))
        elif r.startswith("- "):
            saraksts.append((False, r[2:]))
        else:
            beigt_sarakstu()
            if r.strip() and not r.startswith(IZLAIST_RINDKOPAS):
                out.append(f"<p>{iekļauts(r)}</p>")
    beigt_tabulu()
    beigt_sarakstu()
    return "\n".join(out)


def main():
    dalas = sadalas(AVOTS.read_text(encoding="utf-8"))
    ievads = bloks(dalas[0][1])
    saturs = "\n".join(
        f'<section class="bloks" aria-labelledby="d{n}"><h2 id="d{n}">{iekļauts(v)}</h2>\n{bloks(r)}</section>'
        for n, (v, r) in enumerate(dalas[1:], 1) if not re.sub(r"^\d+\.\s*", "", v).startswith(IZLAIST_SADALAS)
    )
    MERKIS.write_text(f"""<!DOCTYPE html>
<html lang="lv">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="format-detection" content="telephone=no">
<title>Ko vēl vajadzētu publicēt · Krīzes karte</title>
<meta name="description" content="30 datu kopas, kas krīzē iedzīvotājam vajadzīgas, bet ko valsts un pašvaldības vēl nepublicē vai publicē bez atvērtas licences.">
<link rel="stylesheet" href="statuss.css">
<link rel="stylesheet" href="info.css">
<link rel="canonical" href="https://map.repo.lv/trukstosie.html">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Krīzes karte">
<meta property="og:title" content="Ko vēl vajadzētu publicēt — Krīzes karte">
<meta property="og:description" content="Viena meklēšana — viens lēmums: patvertne, plūdu zona, evakuācija, brīdinājumi. 32 atvērto datu avoti.">
<meta property="og:url" content="https://map.repo.lv/trukstosie.html">
<meta property="og:image" content="https://map.repo.lv/og.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="Krīzes karte: meklēšanas rezultāts „plūdi Ogre” ar plūdu zonu, drošajām vietām un maršrutu">
<meta property="og:locale" content="lv_LV">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="Ko vēl vajadzētu publicēt — Krīzes karte">
<meta name="twitter:description" content="Viena meklēšana — viens lēmums: patvertne, plūdu zona, evakuācija, brīdinājumi. 32 atvērto datu avoti.">
<meta name="twitter:image" content="https://map.repo.lv/og.png">
<meta name="theme-color" content="#0077c8">
<link rel="icon" href="ikonas/ikona.svg" type="image/svg+xml">
<link rel="icon" href="ikonas/ikona-32.png" type="image/png" sizes="32x32">
<link rel="apple-touch-icon" href="ikonas/ikona-180.png" sizes="180x180">
</head>
<body>
<!-- Ģenerēts no notes/missing_data.md ar src/trukstosie/sagatavot.py; nelabot ar roku. -->
<header class="augsa">
  <div class="augsa-iekss">
    <h1>Krīzes karte <span>· Ko vēl vajadzētu publicēt</span></h1>
    <a class="atpakal" href="./">← Uz karti</a>
  </div>
</header>
<main class="saturs info trukstosie">
{ievads}
{saturs}
  <p class="piezime drukai">map.repo.lv/trukstosie.html · avots: „Trūkstošie dati” repozitorijā github.com/noiseparty/hakatons</p>
</main>
<script src="kajene.js"></script>
</body>
</html>
""", encoding="utf-8", newline="\n")
    print(MERKIS, MERKIS.stat().st_size, "B")


if __name__ == "__main__":
    main()
