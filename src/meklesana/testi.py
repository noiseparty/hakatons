"""Pārbauda krīzes meklēšanas klasifikatoru (production/klasifikators.js + scenariji.json) ar testi.json.

Palaišana (no repo saknes; Node nav vajadzīgs, JS izpilda QuickJS):
  uv run --no-project --with quickjs src/meklesana/testi.py
Vietvārdu testiem reģionus ņem no https://map.repo.lv/api/regioni (bez interneta tos izlaiž).
"""

import json
import pathlib
import sys
import urllib.request

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
    sys.exit(1 if kludas else 0)


if __name__ == "__main__":
    main()
