"""Ģenerē vaicajumi_kludaini.json: "pavirši telefonā rakstīti" vaicājumi no vaicajumi.json sagaidāmajiem pāriem.

Palaišana (no repo saknes): python src/meklesana/kludaini.py
Kļūdas ir mehāniskas un ar fiksētu sēklu, lai kopa nemainās un netiek pielāgota klasifikatoram:
bez garumzīmēm, dubults vai iztrūkstošs burts, samainīti blakus burti, krievu valoda latīņu burtiem (vairākas
translitā shēmas), angļu vaicājums + latviska vieta, lielie burti un pieturzīmes, vieta pielipusi vārdam.
"""

import json
import pathlib
import random
import re
import unicodedata

MAPE = pathlib.Path(__file__).parent
SEKLA = 2026

# Vietas, ko pievienot (forma vaicājumā → nosaukums tabulā regioni)
VIETAS = [("Ogrē", "Ogre"), ("Rēzeknē", "Rēzekne"), ("Jelgavā", "Jelgava"), ("Cēsīs", "Cēsis"), ("Liepājā", "Liepāja"),
          ("Daugavpilī", "Daugavpils"), ("Rīgā", "Rīga"), ("Valmierā", "Valmiera"), ("Tukumā", "Tukums"), ("Talsos", "Talsi")]

# Divas izplatītas translitā shēmas: "pase" (zh, kh, ts, shch, ya) un "sarunu" (zh, h, c, sch, ja); burtam izvēlas nejauši
TRANSLITS = {
    "а": ["a"], "б": ["b"], "в": ["v"], "г": ["g"], "д": ["d"], "е": ["e"], "ё": ["e", "yo"], "ж": ["zh"], "з": ["z"],
    "и": ["i"], "й": ["y", "i", "j"], "к": ["k"], "л": ["l"], "м": ["m"], "н": ["n"], "о": ["o"], "п": ["p"], "р": ["r"],
    "с": ["s"], "т": ["t"], "у": ["u"], "ф": ["f"], "х": ["kh", "h"], "ц": ["ts", "c"], "ч": ["ch"], "ш": ["sh"],
    "щ": ["shch", "sch"], "ъ": [""], "ы": ["y", "i"], "ь": ["", "'"], "э": ["e"], "ю": ["yu", "ju"], "я": ["ya", "ja"],
}


def bez_garumzimem(s):
    return unicodedata.normalize("NFC", "".join(c for c in unicodedata.normalize("NFD", s) if not unicodedata.combining(c)))


def translits(s, rnd):
    return "".join(rnd.choice(TRANSLITS[c.lower()]) if c.lower() in TRANSLITS else c for c in s)


def garakais_vards(q, rnd, min_garums):
    vardi = [(m.start(), m.group()) for m in re.finditer(r"[^\W\d_]+", q) if len(m.group()) >= min_garums]
    return rnd.choice(vardi) if vardi else None


def kluda(q, veids, rnd):
    """Viena drukas kļūda nejaušā vārdā (≥ 5 burti), ne pirmajā burtā."""
    v = garakais_vards(q, rnd, 5)
    if not v:
        return None
    sak, vards = v
    i = rnd.randrange(1, len(vards) - 1)
    if veids == "dubults":
        jauns = vards[:i] + vards[i] + vards[i:]
    elif veids == "iztrukst":
        jauns = vards[:i] + vards[i + 1:]
    else:  # samainits
        jauns = vards[:i] + vards[i + 1] + vards[i] + vards[i + 2:]
    if jauns == vards:
        return None
    return q[:sak] + jauns + q[sak + len(vards):]


def main():
    rnd = random.Random(SEKLA)
    visi = json.loads((MAPE / "vaicajumi.json").read_text(encoding="utf-8"))
    lv = [v for v in visi if v["tips"] in ("lv", "kluda", "divdomigs") and not re.search("[а-яё]", v["q"], re.I)]
    ar_garumz = [v for v in lv if bez_garumzimem(v["q"]) != v["q"]]
    kir = [v for v in visi if re.search("[а-яё]", v["q"], re.I)]
    en = [v for v in visi if v["tips"] == "ru_en" and not re.search("[а-яё]", v["q"], re.I)]
    bez_vietas = [v for v in lv if v["tips"] != "vieta"]

    def ieraksts(v, q, veids, vieta=None):
        r = {"q": q, "scenarijs": v["scenarijs"], "pienemami": v["pienemami"], "veids": veids, "no": v["q"]}
        if vieta:
            r["vieta"] = vieta
        return r

    kopa = []
    for v in rnd.sample(ar_garumz, 30):
        kopa.append(ieraksts(v, bez_garumzimem(v["q"]).lower(), "bez_garumzimem"))
    for veids in ("dubults", "iztrukst", "samainits"):
        n = 0
        for v in rnd.sample(lv + en, len(lv + en)):
            q = kluda(v["q"], veids, rnd)
            if not q:
                continue
            if rnd.random() < 0.6:  # telefonā bieži arī bez garumzīmēm
                q = bez_garumzimem(q)
            kopa.append(ieraksts(v, q, veids))
            n += 1
            if n == 30:
                break
    for v in rnd.sample(kir, 30):
        kopa.append(ieraksts(v, translits(v["q"], rnd), "ru_translits"))
    for v in rnd.sample(en, 15):
        forma, nos = rnd.choice(VIETAS)
        q = v["q"] + " " + (bez_garumzimem(forma) if rnd.random() < 0.5 else forma)
        kopa.append(ieraksts(v, q, "en_lv", nos))
    for v in rnd.sample(lv + en, 15):
        q = rnd.choice([str.upper, str.capitalize, str.lower])(v["q"]) + rnd.choice(["!!!", "??", "...", "!", " ?", ".."])
        kopa.append(ieraksts(v, q, "reģistrs_pieturz"))
    for v in rnd.sample(bez_vietas, 20):
        forma, nos = rnd.choice(VIETAS)
        q, forma = bez_garumzimem(v["q"]).lower(), bez_garumzimem(forma).lower()
        q = q + forma if rnd.random() < 0.6 else forma + q  # "nav elektribasrezekne" / "ogrepludi"
        kopa.append(ieraksts(v, q, "pielipusi_vieta", nos))

    redzets, unikali = set(), []
    for r in kopa:
        if r["q"] not in redzets:
            redzets.add(r["q"])
            unikali.append(r)
    teksts = "[\n" + ",\n".join(json.dumps(r, ensure_ascii=False) for r in unikali) + "\n]\n"
    (MAPE / "vaicajumi_kludaini.json").write_text(teksts, encoding="utf-8", newline="\n")
    print(f"{len(unikali)} vaicājumi → vaicajumi_kludaini.json")


if __name__ == "__main__":
    main()
