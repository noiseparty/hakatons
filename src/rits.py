"""Viena komanda no rīta: pārbauda repo un dzīvo vietni pa soļiem, beigās kopsavilkuma tabula. Tikai lasa (nekā nemaina).

    uv run --no-project --python 3.12 src/rits.py [--soli 1,2] [--url https://map.repo.lv] [--video]

Soļi (pēc noklusējuma 1-4, 6, 7; 5 tikai ar --video vai --soli 5):
  1 git fetch + vai lokālais checkout sakrīt ar origin/main
  2 API: veseliba, bridinajumi, pludi (Ogre), udens, prognozes, celi, viena pludu flīze (viens pieprasījums katram)
  3 src/testi/parbaude.py (dzīvā pārbaude, viens pārlūks)
  4 src/demo/ekrani.py (slaidu ekrānuzņēmumi; izlaiž, ja 2. solis neparāda īstu plūdu atbildi)
  5 src/demo/video.py (rezerves video, ~2 min)
  6 klasifikatora testi
  7 izdrukā VPS soļus, ko var palaist tikai lietotājs (neko nepalaiž)
Python 3.12 stdlib + subprocess; apakšprogrammas tiek palaistas pa vienai (nav paralēlas slodzes).
"""
import argparse
import json
import os
import pathlib
import re
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request

SAKNE = pathlib.Path(__file__).resolve().parents[1]
OGRE = (56.8166, 24.6072)
FLIZE = "/api/pludi/flize/pali/13/4655/2517.png"
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if os.name == "nt":
    os.system("")
ZALS, DZELT, SARK, PELEKS, BEIGAS = "\033[32m", "\033[33m", "\033[31m", "\033[90m", "\033[0m"
KOMANDAS = {"install", "systemctl", "psql", "bash", "python3", "journalctl", "caddy", "cp", "ssh", "curl", "sudo", "uv"}
KRASA = {"OK": ZALS, "BRIDIN": DZELT, "KLUDA": SARK, "IZLAISTS": PELEKS}
REZ = []  # (nr, nosaukums, rezultats, sekundes, ko darit)
STATUSS = {}  # starp soļiem: STATUSS["pludi"] = True, ja plūdu atbilde ir īsta


def galvene(nr, nosaukums, budzets):
    print(f"\n{'=' * 78}\n[{nr}/7] {nosaukums}   (budžets ~{budzets} s)\n{'=' * 78}", flush=True)


def beigt(nr, nosaukums, rezultats, t0, ko="", piezime=""):
    s = time.time() - t0
    print(f"{KRASA[rezultats]}-> {rezultats}{BEIGAS} {piezime}  ({s:.0f} s)", flush=True)
    REZ.append((nr, nosaukums, rezultats, s, ko if rezultats in ("BRIDIN", "KLUDA") else ""))


def palaist(cmd, budzets):
    """Palaiž apakšprogrammu ar UTF-8 vidi, izvada tās izvadi uzreiz. Atgriež exit kodu vai None, ja pārsniegts laiks."""
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
    print(PELEKS + "$ " + " ".join(cmd) + BEIGAS, flush=True)
    try:
        p = subprocess.Popen(cmd, cwd=SAKNE, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    except FileNotFoundError as e:
        print("nav atrasts:", e)
        return -1

    def lasit():
        for rinda in p.stdout:
            print(rinda.decode("utf-8", "replace").rstrip(), flush=True)
    th = threading.Thread(target=lasit, daemon=True)
    th.start()
    try:
        p.wait(timeout=budzets)
    except subprocess.TimeoutExpired:
        p.kill()
        th.join(2)
        print(f"{SARK}pārsniegts laika budžets ({budzets} s), pārtraukts{BEIGAS}")
        return None
    th.join(5)
    return p.returncode


def uv(*argumenti):
    return ["uv", "run", "--no-project", "--python", "3.12", *argumenti]


def git(*a):
    r = subprocess.run(["git", *a], cwd=SAKNE, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.returncode, (r.stdout + r.stderr).strip()


def solis1(a):
    t0 = time.time()
    galvene(1, "git fetch + sakrīt ar origin/main", 30)
    k, o = git("fetch", "origin")
    if k:
        return beigt(1, "git", "KLUDA", t0, "Nav tīkla vai git? Palaidiet `git fetch origin` pats.", o[:120])
    zars = git("rev-parse", "--abbrev-ref", "HEAD")[1]
    head = git("rev-parse", "HEAD")[1]
    orig = git("rev-parse", "origin/main")[1]
    nemainits = git("status", "--porcelain", "--untracked-files=no")[1]
    print(f"zars: {zars}   HEAD {head[:9]}   origin/main {orig[:9]}   nesaglabātas izmaiņas: {'jā' if nemainits else 'nē'}")
    if head == orig:
        return beigt(1, "git", "OK", t0, piezime=f"{zars} = origin/main" + (" (bet ir nesaglabātas izmaiņas)" if nemainits else ""))
    _, rl = git("rev-list", "--left-right", "--count", "origin/main...HEAD")
    atpakal, uz_priekshu = (rl.split() + ["?", "?"])[:2]
    ko = (f"Esat zarā '{zars}'. Lai redzētu to pašu, ko vietne: `git checkout main && git pull`."
          if zars != "main" else "`git pull` (vai easy/update).")
    beigt(1, "git", "BRIDIN", t0, ko, f"zars '{zars}': aiz origin/main {atpakal}, priekšā {uz_priekshu}")


def get(url, timeout):
    """(statuss, galvenes, ķermenis, sekundes); savienojuma kļūdai statuss = 0 un ķermenis = teksts."""
    t = time.time()
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "rits.py"}), timeout=timeout) as r:
            return r.status, r.headers, r.read(), time.time() - t
    except urllib.error.HTTPError as e:
        return e.code, e.headers, e.read(), time.time() - t
    except Exception as e:  # noqa: BLE001
        return 0, {}, str(e).encode(), time.time() - t


def solis2(a):
    t0 = time.time()
    galvene(2, "API galapunkti (viens pieprasījums katram)", 300)
    b = a.url.rstrip("/")
    lat, lon = OGRE

    def veseliba(d):
        return ("OK" if d.get("ok") else "KLUDA"), f"ok={d.get('ok')}"

    def bridinajumi(d):
        x = d.get("bridinajumi", [])
        return "OK", f"{len(x)} spēkā" + (" · rezerves avots: " + str(d["rezerve"]) if d.get("rezerve") else "") \
            + (" · nepilnīgi" if d.get("nepilnigi") else "")

    def pludi(d):
        zona = "JĀ" if d.get("zona") else "nē"
        if d.get("nepilnigi"):
            return "BRIDIN", f"zona: {zona} · NEPILNĪGI (LVĢMC WMS daļēji neatbildēja)"
        return "OK", f"zona: {zona} · avots {d.get('avots')}"

    def udens(d):
        s = (d.get("stacijas") or [None])[0]
        if not s:
            return "BRIDIN", "nav staciju"
        return ("BRIDIN" if s.get("vecs") else "OK"), f"{s['nosaukums']}: {s['limenis_cm']} cm" + (" · dati novecojuši" if s.get("vecs") else "")

    def prognozes(d):
        ok = bool(d.get("dienas"))
        return ("OK" if ok else "BRIDIN"), f"{len(d.get('zinas', []))} ziņas, dienas: {len(d.get('dienas') or [])}" + \
            ("" if ok else " · prognozes dati nav ielādēti (tikai brīdinājumi)")

    def celi(d):
        if not d.get("konfigurets"):
            return "BRIDIN", "nav konfigurēts (NAP atslēgas)"
        nep = d.get("nepieejami") or []
        return ("BRIDIN" if nep else "OK"), f"{len(d.get('notikumi', []))} notikumi" + (f" · nepieejami: {', '.join(nep)}" if nep else "")

    plan = [("veseliba", "/api/veseliba", 15, veseliba), ("bridinajumi", "/api/bridinajumi", 30, bridinajumi),
            ("pludi (Ogre)", f"/api/pludi?lat={lat}&lon={lon}", 75, pludi),
            ("udens (Ogre)", f"/api/udens?lat={lat}&lon={lon}&limit=1", 30, udens),
            ("prognozes", "/api/prognozes", 90, prognozes), ("celi", "/api/celi", 30, celi)]
    sliktakais = "OK"

    def nosleg(res):
        nonlocal sliktakais
        if res == "KLUDA" or (res == "BRIDIN" and sliktakais == "OK"):
            sliktakais = res

    for nos, cels, tmo, fn in plan:
        st, _, saturs, s = get(b + cels, tmo)
        if st != 200:
            res = "BRIDIN" if nos.startswith("pludi") and st in (0, 502, 503, 504) else "KLUDA"
            txt = f"HTTP {st or 'nav savienojuma'}" + (f" {saturs[:100].decode('utf-8', 'replace')}" if st == 0 else "")
            if res == "BRIDIN":
                txt += " (LVĢMC plūdu serviss lēns/nepieejams)"
        else:
            try:
                res, txt = fn(json.loads(saturs))
            except Exception as e:  # noqa: BLE001
                res, txt = "KLUDA", f"nederīgs JSON: {e}"
        if nos.startswith("pludi"):
            STATUSS["pludi"] = (res == "OK")
        print(f"  {KRASA[res]}{res:7}{BEIGAS} {nos:14} {s:5.1f} s  {txt}", flush=True)
        nosleg(res)
    st, h, saturs, s = get(b + FLIZE, 40)
    if st == 200 and saturs[:4] == b"\x89PNG":
        res, txt = "OK", f"PNG {len(saturs)} B, X-Flize={h.get('X-Flize')}"
    elif st in (0, 502, 503, 504):
        res, txt = "BRIDIN", f"HTTP {st or 'nav savienojuma'} (flīze nav pieejama; zonas zīmējas bez tās)"
    else:
        res, txt = "KLUDA", f"HTTP {st}"
    print(f"  {KRASA[res]}{res:7}{BEIGAS} {'pludi/flize':14} {s:5.1f} s  {txt}", flush=True)
    nosleg(res)
    beigt(2, "API galapunkti", sliktakais, t0,
          "Skatiet statuss.html. Plūdu BRIDIN = LVĢMC lēns: mēģiniet vēlāk un iesildiet (notes/ritdiena.md). KLUDA = API/VPS (journalctl -u hakatons-map-api).")


def solis3(a):
    t0 = time.time()
    galvene(3, "Dzīvā pārbaude src/testi/parbaude.py", 600)
    k = palaist(uv("--with", "playwright", "--with", "httpx", "src/testi/parbaude.py", "--url", a.url), 600)
    beigt(3, "parbaude.py", "OK" if k == 0 else "KLUDA", t0,
          "Sarkanās rindas augstāk labojiet vai nododiet orķestratoram. Pirmā reize: `uv run --no-project --with playwright playwright install chromium`.",
          f"exit {k}")


def solis4(a):
    t0 = time.time()
    galvene(4, "Slaidu ekrānuzņēmumi src/demo/ekrani.py", 400)
    if not STATUSS.get("pludi"):
        print("Izlaists: 2. solis (vai tā plūdu rinda) nav apstiprinājis īstu plūdu atbildi, kadrā būtu ielādes josla.")
        return beigt(4, "ekrani.py", "IZLAISTS", t0, piezime="plūdu atbilde nav apstiprināta")
    k = palaist(uv("--with", "playwright", "--with", "pillow", "src/demo/ekrani.py", "--url", a.url), 400)
    beigt(4, "ekrani.py", "OK" if k == 0 else "KLUDA", t0,
          "Skatiet ⚠ tabulu augstāk; production/slaidi/*.webp mainās, tos jāiekļauj PR (sw.js versija).", f"exit {k}")


def solis5(a):
    t0 = time.time()
    galvene(5, "Rezerves demo video src/demo/video.py", 300)
    if 5 not in a.soli_set:
        print("Izlaists: pievienojiet --video (vai --soli 5), ~2 min.")
        return beigt(5, "video.py", "IZLAISTS", t0)
    k = palaist(uv("--with", "playwright", "--with", "pillow", "--with", "imageio-ffmpeg", "src/demo/video.py", "--url", a.url + "/"), 300)
    beigt(5, "video.py", "OK" if k == 0 else "KLUDA", t0, "Skatiet notes/video.md; izvade ir mapē ../demo-video.", f"exit {k}")


def solis6(a):
    t0 = time.time()
    galvene(6, "Klasifikatora testi", 120)
    k = palaist(uv("--with", "quickjs", "src/meklesana/testi.py"), 120)
    beigt(6, "klasifikatora testi", "OK" if k == 0 else "KLUDA", t0, "Skatiet, kurš scenārijs nesakrīt (izvade augstāk).", f"exit {k}")


def vps_punkti():
    """Lasa TODO.md neatzīmētās rindas ar 'VPS' un notes/stavoklis.md VPS bloku. Atgriež [(teksts, [komandas])]."""
    punkti, redzeti = [], set()
    todo = SAKNE / "TODO.md"
    if todo.exists():
        for r in todo.read_text(encoding="utf-8").splitlines():
            m = re.match(r"- \[ \] (.*)", r)
            if not m or not re.match(r"VPS\b", m.group(1)):
                continue
            t = re.sub(r"\s+— added .*$", "", m.group(1))
            if t in redzeti:
                continue
            redzeti.add(t)
            punkti.append((t, re.findall(r"`([^`]+)`", t)))
    st = SAKNE / "notes" / "stavoklis.md"
    if st.exists():
        m = re.search(r"^#+ VPS step[^\n]*\n(.*?)(?=^#+ |\Z)", st.read_text(encoding="utf-8"), re.M | re.S)
        if m:
            bloki = re.findall(r"```(?:bash|sh)?\n(.*?)```", m.group(1), re.S)
            if bloki:
                punkti.append(("notes/stavoklis.md (var būt jau izpildīts, pārbaudiet TODO.md Done): " +m.group(0).splitlines()[0].lstrip("# "), [b.strip() for b in bloki]))
    return punkti


def solis7(a):
    t0 = time.time()
    galvene(7, "VPS soļi, ko var palaist tikai lietotājs (tikai izdruka, nekas netiek palaists)", 10)
    p = vps_punkti()
    if not p:
        print("Neatzīmētu VPS punktu TODO.md nav.")
    print("Pieslēgšanās: ssh root@161.97.105.130\n"
          "Pēc tam:      cd /srv/hakatons && set -a && . /etc/hakatons/map.env && set +a\n")
    for i, (txt, kom) in enumerate(p, 1):
        print(f"{DZELT}{i}. {txt}{BEIGAS}")
        rindas = []
        for c in kom:
            if "\n" in c or c.split(" ", 1)[0] in KOMANDAS:
                rindas.extend(c.splitlines())
        if rindas:
            print("   --- kopējiet ---\n" + "\n".join("   " + ln for ln in rindas) + "\n   ---")
        print()
    print(PELEKS + "PR aprakstu sadaļas 'VPS steps' šeit netiek lasītas: `gh pr list --state merged --limit 20 --json number,body`." + BEIGAS)
    beigt(7, "VPS saraksts", "OK", t0, piezime=f"{len(p)} punkti")


def main():
    ap = argparse.ArgumentParser(description="Rīta pārbaude vienā komandā")
    ap.add_argument("--soli", default="", help="komats: 1,2,... (noklusējums 1-4, 6, 7)")
    ap.add_argument("--url", default="https://map.repo.lv")
    ap.add_argument("--video", action="store_true", help="pievieno 5. soli (rezerves video, ~2 min)")
    a = ap.parse_args()
    a.url = a.url.rstrip("/")
    a.soli_set = {int(x) for x in a.soli.split(",") if x.strip()} if a.soli else {1, 2, 3, 4, 6, 7} | ({5} if a.video else set())
    print(f"rits.py · {time.strftime('%Y-%m-%d %H:%M:%S')} · {a.url} · soļi {sorted(a.soli_set)}")
    t00 = time.time()
    fns = {1: solis1, 2: solis2, 3: solis3, 4: solis4, 5: solis5, 6: solis6, 7: solis7}
    for nr in sorted(a.soli_set & set(fns)):
        try:
            fns[nr](a)
        except KeyboardInterrupt:
            print("pārtraukts")
            break
        except Exception as e:  # noqa: BLE001
            REZ.append((nr, f"solis {nr}", "KLUDA", 0, f"Skripta kļūda: {e!r}"))
            print(f"{SARK}kļūda: {e!r}{BEIGAS}")
    print(f"\n{'=' * 78}\nKOPSAVILKUMS ({time.time() - t00:.0f} s)\n{'=' * 78}")
    print(f"{'#':2} {'Solis':22} {'Rezultāts':9} {'sek':>5}  Ko darīt, ja nav zaļš")
    for nr, nos, res, s, ko in REZ:
        print(f"{nr:<2} {nos:22} {KRASA[res]}{res:9}{BEIGAS} {s:5.0f}  {ko}")
    sys.exit(1 if any(r[2] == "KLUDA" for r in REZ) else 0)


if __name__ == "__main__":
    main()
