"""Pārbauda krīzes meklēšanas klasifikatoru (production/klasifikators.js + scenariji.json) ar testi.json.

Palaišana (no repo saknes; Node nav vajadzīgs, JS izpilda QuickJS):
  uv run --no-project --python 3.12 --with quickjs src/meklesana/testi.py
Vietvārdu testiem reģionus ņem no https://map.repo.lv/api/regioni (bez interneta tos izlaiž).
"""

import json
import pathlib
import re
import sys
import urllib.request
import zlib

import quickjs

SAKNE = pathlib.Path(__file__).resolve().parents[2]


def regioni():
    try:
        with urllib.request.urlopen("https://map.repo.lv/api/regioni", timeout=10) as r:
            return json.load(r)
    except Exception as e:  # noqa: BLE001 - bez reģioniem vienkārši izlaižam vietu pārbaudes
        print(f"reģioni nav pieejami ({e}), vietas nepārbaudu", file=sys.stderr)
        return None


def main():
    js = quickjs.Context()
    js.eval("var module = undefined;")
    js.eval((SAKNE / "production" / "klasifikators.js").read_text(encoding="utf-8") + "\nglobalThis.Klasifikators = Klasifikators;")
    noteikumi = (SAKNE / "production" / "scenariji.json").read_text(encoding="utf-8")
    reg = regioni()
    js.eval(f"globalThis.k = Klasifikators.izveidot({noteikumi}, {json.dumps(reg or [], ensure_ascii=False)});")
    klasificet = js.eval("(q => JSON.stringify(k.klasificet(q), (key, v) => key === 'raksti' || key === 'atslegvardi' ? undefined : v))")

    testi = json.loads((pathlib.Path(__file__).parent / "testi.json").read_text(encoding="utf-8"))
    kludas = 0
    for t in testi:
        rez = json.loads(klasificet(t["q"]))
        kodi = [s["kods"] for s in rez["scenariji"]]
        problemas = []
        if (kodi[0] if kodi else None) != t["scenarijs"]:
            problemas.append(f"scenārijs {kodi or None}, gaidīju {t['scenarijs']}")
        if "zvanit112" in t and rez["zvanit112"] != t["zvanit112"]:
            problemas.append(f"zvanit112 {rez['zvanit112']}")
        vieta = (rez["vieta"] or {}).get("nosaukums")
        if reg is not None and vieta != t.get("vieta"):
            problemas.append(f"vieta {vieta}, gaidīju {t.get('vieta')}")
        kludas += bool(problemas)
        zime = "KĻŪDA" if problemas else "ok   "
        papildus = f" +{kodi[1:]}" if len(kodi) > 1 else ""
        print(f"{zime} {t['q']!r} → {kodi[0] if kodi else '-'}{papildus}"
              f"{' 112' if rez['zvanit112'] else ''}{' @' + vieta if vieta else ''}"
              f"{'  ← ' + '; '.join(problemas) if problemas else ''}")
    print(f"\n{len(testi) - kludas}/{len(testi)} pareizi")

    # Katra notes/SCENARIJI.md scenārija nosaukumam jāatrod savs scenārijs (pirmais vai starp "Vai domāji…?").
    # 72 un 73 apzināti netiek atpazīti: tie vērtētu cilvēkus pēc izcelsmes/izskata, nevis rīcības.
    md = (SAKNE / "notes" / "SCENARIJI.md").read_text(encoding="utf-8")
    nosaukumi = re.findall(r"^\| (\d+) \| ([^|]+?) \|", md, re.M)
    nr_saraksts = js.eval("(q => JSON.stringify(k.klasificet(q).scenariji.map(s => s.nr || null)))")
    bez = [(nr, n) for nr, n in nosaukumi if int(nr) not in (72, 73) and int(nr) not in json.loads(nr_saraksts(n))]
    for nr, n in bez:
        print(f"KĻŪDA SCENARIJI.md #{nr} {n!r} neatrod savu scenāriju")
    print(f"{len(nosaukumi) - len(bez)}/{len(nosaukumi)} scenāriju nosaukumi atrod sevi")
    zems = vaicajumu_parbaude(klasificet, "-v" in sys.argv)
    laiks = js.eval("(q => { const s = Date.now(); k.klasificet(q); return Date.now() - s; })")
    zems_k = kludaino_parbaude(klasificet, laiks, reg is not None, "-v" in sys.argv)
    sys.exit(1 if kludas or bez or zems or zems_k else 0)


MERKIS = 0.90  # top-1 precizitāte uz vaicajumi.json, zem kuras tests krīt


def vaicajumu_parbaude(klasificet, viss=False):
    """Reālistisks vaicājumu kopums (vaicajumi.json; kā veidots — notes/klasifikators.md).

    Pareizs = pirmais scenārijs ir starp "pienemami". Divdomīgajiem skaita, vai "Vai domājāt" rāda vēl kādu pieņemamo,
    skaidrajiem — cik bieži "Vai domājāt" parādās lieki. Rāda precizitāti pa tipiem un 20 sliktākos scenārijus.
    Ar -v izdrukā arī visus kļūdainos vaicājumus.
    """
    cels = pathlib.Path(__file__).parent / "vaicajumi.json"
    if not cels.exists():
        return False
    vaicajumi = json.loads(cels.read_text(encoding="utf-8"))
    pa_tipiem, gaidits, prognozets, pareizi_pec = {}, {}, {}, {}
    divd_ar_citiem = divd = lieki = skaidri = 0
    kludainie = []
    for v in vaicajumi:
        kodi = [s["kods"] for s in json.loads(klasificet(v["q"]))["scenariji"]]
        pirmais = kodi[0] if kodi else None
        labs = pirmais in v["pienemami"]
        t = pa_tipiem.setdefault(v["tips"], [0, 0])
        t[0] += labs
        t[1] += 1
        gaidits[v["scenarijs"]] = gaidits.get(v["scenarijs"], 0) + 1
        pareizi_pec[v["scenarijs"]] = pareizi_pec.get(v["scenarijs"], 0) + labs
        if pirmais:
            prognozets.setdefault(pirmais, [0, 0])
            prognozets[pirmais][0] += labs
            prognozets[pirmais][1] += 1
        if v["tips"] == "divdomigs":
            divd += 1
            divd_ar_citiem += len(set(kodi) & set(v["pienemami"])) >= 2  # vismaz divi pieņemamie redzami
        else:
            skaidri += 1
            lieki += len(kodi) >= 2
        if not labs:
            kludainie.append((v, kodi))

    kopa = sum(t[0] for t in pa_tipiem.values())
    print(f"\nvaicajumi.json: {kopa}/{len(vaicajumi)} pareizi pirmajā vietā ({kopa / len(vaicajumi):.1%}, mērķis ≥ {MERKIS:.0%})")
    # Labojot atslēgvārdus, skatieties tikai "dev" kļūdas; "paturētie" (30 % pēc crc32) rāda, vai labojums vispārinās
    paturets = [v for v in vaicajumi if zlib.crc32(v["q"].encode()) % 10 >= 7]
    lab_pat = sum(1 for v in paturets if v["q"] not in {k[0]["q"] for k in kludainie})
    print(f"  paturētie (nelabotie) {lab_pat}/{len(paturets)} = {lab_pat / len(paturets):.1%}")
    for tips, (lab, n) in sorted(pa_tipiem.items()):
        print(f"  {tips:10} {lab:3}/{n:3}  {lab / n:.0%}")
    print(f"  'Vai domājāt' divdomīgajiem: {divd_ar_citiem}/{divd}; lieki skaidrajiem: {lieki}/{skaidri}")

    # Sliktākie: zemākā F1 (atrasts no sagaidāmajiem × precizitāte, kad izvēlēts) pa scenārijiem
    def f1(kods):
        parkl = pareizi_pec.get(kods, 0) / gaidits[kods]
        lab, n = prognozets.get(kods, (0, 0))
        prec = lab / n if n else parkl  # nekad nav izvēlēts pats (pareizi caur citu pieņemamo) — skaitām pēc pārklājuma
        return (0.0 if not parkl + prec else 2 * parkl * prec / (parkl + prec)), prec, n
    print("  20 sliktākie scenāriji (F1 · atrasti no sagaidāmajiem · precizitāte, kad izvēlēts):")
    for kods in sorted(gaidits, key=lambda k: f1(k)[0])[:20]:
        f, prec, n = f1(kods)
        print(f"    {kods:26} F1 {f:.2f}  {pareizi_pec.get(kods, 0)}/{gaidits[kods]}  prec {prec:.2f} (izvēlēts {n}×)")
    if viss:
        print("  Kļūdainie (tikai dev; paturētos neskatieties, lai skaitlis paliek godīgs):")
        for v, kodi in kludainie:
            if zlib.crc32(v["q"].encode()) % 10 >= 7:
                continue
            print(f"    {v['q']!r} → {kodi or '-'}  gaidīju {v['pienemami']}")
    return kopa / len(vaicajumi) < MERKIS


MERKIS_KLUDAINI = 0.90  # top-1 precizitāte uz vaicajumi_kludaini.json, zem kuras tests krīt (2026-10-10: 93,5 %)
LAIKA_ROBEZA_MS = 5  # klasificet() QuickJS, pirmais (nekešotais) izsaukums: mediānai un p95 jābūt zem šī


def kludaino_parbaude(klasificet, laiks, ar_vietam, viss=False):
    """Pavirši rakstīti vaicājumi (vaicajumi_kludaini.json, ģenerē kludaini.py): precizitāte pa kļūdu veidiem un laiks.

    Pareizs = pirmais scenārijs ir starp "pienemami" un, ja ir "vieta" un reģioni pieejami, atrasta tā vieta.
    Laiku mēra JS iekšienē (Date.now, ms) pirmajam izsaukumam, pirms vārdu labojumi ir kešoti.
    """
    cels = pathlib.Path(__file__).parent / "vaicajumi_kludaini.json"
    if not cels.exists():
        return False
    vaicajumi = json.loads(cels.read_text(encoding="utf-8"))
    pa_veidiem, kludainie, laiki = {}, [], []
    for v in vaicajumi:
        laiki.append(laiks(v["q"]))
        rez = json.loads(klasificet(v["q"]))
        kodi = [s["kods"] for s in rez["scenariji"]]
        vieta = (rez["vieta"] or {}).get("nosaukums")
        labs = (kodi[0] if kodi else None) in v["pienemami"] and (not ar_vietam or "vieta" not in v or vieta == v["vieta"])
        t = pa_veidiem.setdefault(v["veids"], [0, 0])
        t[0] += labs
        t[1] += 1
        if not labs:
            kludainie.append((v, kodi, vieta))
    kopa = sum(t[0] for t in pa_veidiem.values())
    laiki.sort()
    print(f"\nvaicajumi_kludaini.json: {kopa}/{len(vaicajumi)} pareizi ({kopa / len(vaicajumi):.1%}, mērķis ≥ {MERKIS_KLUDAINI:.0%})"
          f"; laiks QuickJS mediāna {laiki[len(laiki) // 2]} ms, p95 {laiki[int(len(laiki) * .95)]} ms, max {laiki[-1]} ms"
          f" (robeža {LAIKA_ROBEZA_MS} ms)")
    for veids, (lab, n) in sorted(pa_veidiem.items()):
        print(f"  {veids:18} {lab:3}/{n:3}  {lab / n:.0%}")
    if viss:
        for v, kodi, vieta in kludainie:
            print(f"    {v['q']!r} → {kodi or '-'}{' @' + vieta if vieta else ''}  gaidīju {v['pienemami']} {v.get('vieta', '')}")
    return kopa / len(vaicajumi) < MERKIS_KLUDAINI or laiki[int(len(laiki) * .95)] >= LAIKA_ROBEZA_MS


if __name__ == "__main__":
    main()
