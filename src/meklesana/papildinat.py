"""Pievieno ģenerētos atslēgvārdus scenariji.json un apvieno ģenerēto vaicājumu kopu vaicajumi.json.

Ģenerēšana notika bezsaistē (Claude apakšaģenti pa 25 scenārijiem, sk. notes/klasifikators.md); šis skripts tikai
filtrē un apvieno. Palaišana no repo saknes:
  python src/meklesana/papildinat.py atslegvardi <dir ar atslegvardi_*.json>
  python src/meklesana/papildinat.py vaicajumi <dir ar vaicajumi_*.json>

Atslēgvārdu filtrs: tas pats normalizējums kā klasifikators.js (mazie burti, bez garumzīmēm); izmet dublikātus,
tos, ko jau sedz esošs prefikss ('patvert' sedz 'patvertn'), īsākus par 4 burtiem (ja nav '$') un vispārīgus vārdus.
scenariji.json ir formatēts ar roku, tāpēc to nepārrakstām: jaunos vārdus pieliekam katra masīva beigās.
"""

import json
import pathlib
import re
import sys
import unicodedata

SAKNE = pathlib.Path(__file__).resolve().parents[2]
SCENARIJI = SAKNE / "production" / "scenariji.json"
VAICAJUMI = pathlib.Path(__file__).parent / "vaicajumi.json"

# vārdi, kas sasaista nesaistītus vaicājumus (sk. scenariji.json _apraksts)
VISPARIGI = {
    "palidz", "help", "cels", "iela", "maja", "majas", "cilvek", "nav", "ir", "loti", "please", "need", "помог",
    "помощ", "нужн", "человек", "дом", "улиц", "дорог", "очень", "есть", "нет", "problem", "проблем",
    "steidz", "срочн", "urgent", "tagad", "сейчас", "now", "what", "kas", "что", "kur", "где", "where",
}


def normalizet(s):
    s = unicodedata.normalize("NFD", s.lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return " ".join(re.sub(r"[^\w]+", " ", s).split())


def masiva_beigas(teksts, sakums):
    """Indekss aizverošajai ']' masīvam, kas sākas ar '[' pozīcijā sakums (ņem vērā virknes)."""
    virkne = False
    i = sakums + 1
    while True:
        c = teksts[i]
        if virkne:
            if c == "\\":
                i += 1
            elif c == '"':
                virkne = False
        elif c == '"':
            virkne = True
        elif c == "]":
            return i
        i += 1


def atslegvardi(dir_):
    dati = json.loads(SCENARIJI.read_text(encoding="utf-8"))
    jauni = {}
    for f in sorted(pathlib.Path(dir_).glob("atslegvardi_*.json")):
        for kods, saraksts in json.loads(f.read_text(encoding="utf-8")).items():
            jauni.setdefault(kods, []).extend(saraksts)
    teksts = SCENARIJI.read_text(encoding="utf-8")
    pievienoti = izmesti = 0
    for s in dati["scenariji"]:
        esosie = [(normalizet(a.rstrip("$")), a.endswith("$")) for a in s["atslegvardi"]]
        klat = []
        for a in jauni.pop(s["kods"], []):
            a = a.strip()
            vesels = a.endswith("$")
            n = normalizet(a.rstrip("$"))
            if (not n or (len(n) < 4 and not vesels) or n in VISPARIGI
                    or any(n == e or (not ev and n.startswith(e)) for e, ev in esosie)):
                izmesti += 1
                continue
            klat.append(a)
            esosie.append((n, vesels))
        if not klat:
            continue
        pievienoti += len(klat)
        rindas, rinda = [], ""
        for a in klat:
            gab = json.dumps(a, ensure_ascii=False)
            if rinda and len(rinda) + len(gab) + 2 > 110:
                rindas.append(rinda)
                rinda = ""
            rinda += (", " if rinda else "") + gab
        rindas.append(rinda)
        sakums = teksts.index("[", teksts.index('"atslegvardi"', teksts.index(f'"kods": "{s["kods"]}"')))
        beigas = masiva_beigas(teksts, sakums)
        pirms = teksts[:beigas].rstrip()
        atstarpe = teksts[len(pirms):beigas]  # "\n      " ja ']' savā rindā, citādi ""
        teksts = pirms + "," + ",".join(f"\n        {r}" for r in rindas) + (atstarpe or "\n      ") + teksts[beigas:]
    if jauni:
        print(f"nezināmi scenāriji: {sorted(jauni)}", file=sys.stderr)
    json.loads(teksts)  # jāpaliek derīgam JSON
    SCENARIJI.write_text(teksts, encoding="utf-8", newline="\n")
    print(f"pievienoti {pievienoti}, izmesti {izmesti} (dublikāti, sedz esošs prefikss, par īsu, vispārīgi)")


def vaicajumi(dir_):
    kodi = {s["kods"] for s in json.loads(SCENARIJI.read_text(encoding="utf-8"))["scenariji"]}
    visi, redzeti, slikti = [], set(), 0
    for f in sorted(pathlib.Path(dir_).glob("vaicajumi_*.json")):
        for v in json.loads(f.read_text(encoding="utf-8")):
            v["pienemami"] = list(dict.fromkeys([v["scenarijs"], *v.get("pienemami", [])]))
            if not set(v["pienemami"]) <= kodi or normalizet(v["q"]) in redzeti:
                slikti += 1
                continue
            redzeti.add(normalizet(v["q"]))
            visi.append({k: v[k] for k in ("q", "scenarijs", "pienemami", "tips", "vieta") if k in v})
    VAICAJUMI.write_text("[\n" + ",\n".join(json.dumps(v, ensure_ascii=False) for v in visi) + "\n]\n",
                         encoding="utf-8", newline="\n")
    print(f"{len(visi)} vaicājumi ({slikti} izmesti: nezināms kods vai dublikāts)")


if __name__ == "__main__":
    {"atslegvardi": atslegvardi, "vaicajumi": vaicajumi}[sys.argv[1]](sys.argv[2])
