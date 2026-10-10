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


def iekļauts(teksts):
    """Markdown rindiņa → HTML: **treknraksts**, `kods`; viss pārējais aizsargāts."""
    t = html.escape(teksts, quote=False)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    return re.sub(r"`(.+?)`", r"<code>\1</code>", t)


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
<meta name="description" content="25 datu kopas, kas krīzē iedzīvotājam vajadzīgas, bet ko valsts un pašvaldības vēl nepublicē vai publicē bez atvērtas licences.">
<link rel="stylesheet" href="statuss.css">
<link rel="stylesheet" href="info.css">
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
  <p class="piezime drukai">map.repo.lv/trukstosie.html · avots: notes/missing_data.md repozitorijā github.com/noiseparty/hakatons</p>
</main>
</body>
</html>
""", encoding="utf-8", newline="\n")
    print(MERKIS, MERKIS.stat().st_size, "B")


if __name__ == "__main__":
    main()
