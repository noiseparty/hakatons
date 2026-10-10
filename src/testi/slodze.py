"""Slodzes tests map.repo.lv API: N vienlaicīgi klienti T sekundes ar reālu pieprasījumu sajaukumu, kopējais ātrums
ierobežots ar --rps (lai netraucētu ārējiem avotiem: plūdu WMS, FMI u.c. jāsasniedz tikai caur mūsu kešu).

  uv run --no-project --python 3.12 --with httpx src/testi/slodze.py --url https://map.repo.lv --klienti 5 --ilgums 30 --rps 2 --tikai-kesa

Pret dzīvo vietni — tikai saudzīgi (≤ 5 klienti, ≤ 2/s, --tikai-kesa); slēdzenes un pārslodzi pārbauda lokāli: slodze_lokali.py.

Rezultāts: katram galapunktam skaits, kļūdas, p50/p95/p99 (ms) un lēnākais; kopsavilkums. Ar --statistika pēc testa
nolasa /api/veseliba?statistika=1 (cik reižu katra keša atslēga tiešām gāja uz ārējo avotu, cik gaidīja slēdzeni).
Rezultātu apraksts: notes/slodze.md.
"""

import argparse
import asyncio
import random
import statistics
import time
from collections import defaultdict

import httpx

PUNKTI = [(56.8166, 24.6046), (56.9677, 23.7704), (56.9496, 24.1052)]  # Ogre, Jūrmala (Melluži), Rīga
SLANI = ("patvertne,evakuacijas_punkts,izmitinasana,neatliekama_24h,slimnica,aptieka,bankomats,policija,"
         "ugunsdzeseji,degviela,udens_limenis")


# Galapunkti, kas (ja nav kešā) iet uz ārējiem avotiem ar stingriem noteikumiem: plūdu WMS, FMI, NAP, Open-Meteo, LVĢMC
AREJIE = {"pludi", "zibens", "celi", "satiksme", "augsne", "noverojumi", "prognozes"}
TIKAI_KESA = False


def pieprasijums():
    """(nosaukums, ceļš) pēc svariem: lapas ielāde (slāņi, brīdinājumi) + meklēšanas kartīte (tuvākās vietas, plūdi…)."""
    lat, lon = random.choice(PUNKTI)
    ll = f"lat={lat}&lon={lon}"
    izvele = [
        (6, "kategorijas", "/api/kategorijas"),
        (4, "regioni", "/api/regioni"),
        (4, "avoti", "/api/avoti"),
        (5, "objekti (visi slāņi)", f"/api/objekti?kategorijas={SLANI}&limit=20000"),
        (14, "objekti (kartīte)", f"/api/objekti?kategorijas={random.choice(['evakuacijas_punkts', 'patvertne', 'neatliekama_24h', 'izmitinasana'])}&{ll}&limit=5"),
        (4, "adreses", "/api/adreses?q=" + random.choice(["brivibas 15 ogre", "mednieku 9 ogre", "kr barona 1 riga"]) + "&limit=5"),
        (8, "bridinajumi", f"/api/bridinajumi?{ll}"),
        (5, "pludi", f"/api/pludi?{ll}"),
        (5, "udens", f"/api/udens?{ll}&limit=3"),
        (4, "prognozes", "/api/prognozes"),
        (2, "statuss", "/api/statuss"),
        (3, "zibens", "/api/zibens"),
        (4, "celi", f"/api/celi?{ll}&r=5000"),
        (4, "satiksme", "/api/satiksme"),
        (4, "meklejumi/top", "/api/meklejumi/top?n=10"),
        (5, "pasvaldiba", f"/api/pasvaldiba?{ll}"),
        (3, "noverojumi", "/api/noverojumi"),
        (3, "augsne", f"/api/augsne?{ll}"),
        (3, "adreses/tuvaka", f"/api/adreses/tuvaka?{ll}"),
    ]
    if TIKAI_KESA:
        izvele = [x for x in izvele if x[1] not in AREJIE]
    svari = [x[0] for x in izvele]
    _, nos, cels = random.choices(izvele, weights=svari)[0]
    return nos, cels


class Atrums:
    """Kopējais pieprasījumu ātruma ierobežotājs (token bucket) visiem klientiem."""
    def __init__(self, rps):
        self.intervals = 1 / rps
        self.nakamais = time.monotonic()
        self.slots = asyncio.Lock()

    async def gaidit(self):
        async with self.slots:
            tagad = time.monotonic()
            if self.nakamais > tagad:
                await asyncio.sleep(self.nakamais - tagad)
            self.nakamais = max(self.nakamais, tagad) + self.intervals


async def klients(c, atrums, beigas, rez, taimauts):
    while time.monotonic() < beigas:
        await atrums.gaidit()
        nos, cels = pieprasijums()
        t = time.monotonic()
        try:
            r = await c.get(cels, timeout=taimauts)
            kods = r.status_code
            await r.aread()
        except httpx.HTTPError as e:
            kods = type(e).__name__
        rez[nos].append(((time.monotonic() - t) * 1000, kods))


def procentile(v, p):
    return v[min(len(v) - 1, int(round(p / 100 * (len(v) - 1))))]


async def main():
    a = argparse.ArgumentParser()
    a.add_argument("--url", default="https://map.repo.lv")
    a.add_argument("--klienti", type=int, default=50)
    a.add_argument("--ilgums", type=int, default=60)
    a.add_argument("--rps", type=float, default=20, help="kopējais pieprasījumu skaits sekundē (augšējā robeža)")
    a.add_argument("--taimauts", type=float, default=30)
    a.add_argument("--statistika", action="store_true", help="pēc testa nolasīt /api/veseliba?statistika=1")
    a.add_argument("--tikai-kesa", action="store_true", help="bez galapunktiem, kas var iet uz ārējiem avotiem (pludi, FMI, NAP…)")
    args = a.parse_args()
    global TIKAI_KESA
    TIKAI_KESA = args.tikai_kesa

    rez = defaultdict(list)
    atrums = Atrums(args.rps)
    limits = httpx.Limits(max_connections=args.klienti, max_keepalive_connections=args.klienti)
    async with httpx.AsyncClient(base_url=args.url, limits=limits, headers={"User-Agent": "map.repo.lv slodzes tests"}) as c:
        sakums = time.monotonic()
        beigas = sakums + args.ilgums
        await asyncio.gather(*(klients(c, atrums, beigas, rez, args.taimauts) for _ in range(args.klienti)))
        ilgums = time.monotonic() - sakums
        stat = None
        if args.statistika:
            try:
                stat = (await c.get("/api/veseliba?statistika=1", timeout=10)).json()
            except Exception as e:  # noqa: BLE001
                stat = {"kluda": str(e)}

    visi = sorted(ms for v in rez.values() for ms, _ in v)
    kludas = sum(1 for v in rez.values() for _, k in v if not (isinstance(k, int) and k < 400))
    print(f"\n{args.url}: {args.klienti} klienti, {ilgums:.0f} s, {len(visi)} pieprasījumi ({len(visi) / ilgums:.1f}/s), "
          f"kļūdas {kludas} ({100 * kludas / max(1, len(visi)):.1f} %)")
    print(f"kopā: p50 {procentile(visi, 50):.0f} ms, p95 {procentile(visi, 95):.0f} ms, p99 {procentile(visi, 99):.0f} ms\n")
    print(f"{'galapunkts':24} {'n':>5} {'kļūd.':>5} {'p50':>7} {'p95':>7} {'p99':>7} {'max':>7}  statusi")
    for nos, v in sorted(rez.items(), key=lambda x: -procentile(sorted(m for m, _ in x[1]), 95)):
        ms = sorted(m for m, _ in v)
        kodi = defaultdict(int)
        for _, k in v:
            kodi[k] += 1
        kl = sum(n for k, n in kodi.items() if not (isinstance(k, int) and k < 400))
        print(f"{nos:24} {len(v):5} {kl:5} {procentile(ms, 50):7.0f} {procentile(ms, 95):7.0f} {procentile(ms, 99):7.0f} "
              f"{ms[-1]:7.0f}  {dict(kodi)}")
    if stat is not None:
        print("\n/api/veseliba?statistika=1:", stat)
    print(f"\nvidējais {statistics.mean(visi):.0f} ms")


if __name__ == "__main__":
    asyncio.run(main())
