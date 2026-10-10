# API slodze žūrijas dienai (2026-10-10)

Mērķis: istaba ar telefoniem + projektors (~20–40 vienlaicīgu lietotāju) nedrīkst nogāzt `map.repo.lv/api`. Rīki:
`src/testi/slodze.py` (pret jebkuru URL, ar `--rps` robežu un `--tikai-kesa`), `src/testi/slodze_lokali.py` (lokāli,
viltota DB un lēni viltoti avoti — slēdzenes un pārslodze bez ārējiem avotiem), `src/testi/api_slodze_testi.py` (16 testi).

## Mērījumi

**Dzīvā vietne, pirms labojumiem** (03:05, 50 klienti, 60 s, ≤ 20/s — veikts pirms lietotāja lūguma naktī dzīvo vietni
nenoslogot; turpmāk pret dzīvo tikai ≤ 5 klienti, ≤ 2/s): 1213 pieprasījumi, kļūdas 8 (0,7 %, Caddy 502), p50 109 ms,
p95 1047 ms, p99 15,4 s. Lēnākie: `pludi` p95 25 s (pirmās pārbaudes punktam, pārējie gaida to pašu slēdzeni),
`zibens`/`prognozes` p95 4–7 s (kad beidzas keša derīgums, visi gaida vienu lejupielādi), pilns slāņu saraksts
`objekti` ~600 ms katru reizi.

**Dzīvā vietne, saudzīgi** (03:25, 5 klienti, 30 s, 2/s, tikai kešotie galapunkti): 65 pieprasījumi, 0 kļūdu,
p50 110 ms, p95 610 ms; lēnākais pilns slāņu saraksts (594 ms) un `adreses/tuvaka` (359 ms).

**Lokāli, viltoti avoti, 50 klienti, 40 s, kešs "novecināts" ik 5 s:**

| | main (pirms) | šis PR |
|---|---:|---:|
| pieprasījumi | 923 | 2331 |
| savienojuma kļūdas (Caddy 502 cēlonis) | 29 | 0 |
| p50 / p95 | 578 / 12 390 ms | 172 / 1078 ms |
| `bridinajumi` p50 (avots atbild 2 s) | 2282 ms | 141 ms |
| `pludi` max (WMS punkts 30 s) | 30,2 s | 25,2 s → 202, nākamais no kešas |
| pilns slāņu saraksts p50 | 593 ms | 188 ms |
| vienlaicīgi DB vaicājumi max | 19 (bez robežas) | 16 (robeža) |
| izsaukumi uz "avotu" (brīdinājumi, ūdens) | 5 / 4 | 4 / 4 (viens uz derīguma beigām) |

## Labojumi (`src/karte/api/karte_api.py`)

1. **Savienojumu rinda**: `ThreadingHTTPServer.request_queue_size` 5 → 128 (`Serveris`), `daemon_threads`. Ar 5
   slodzē savienojumi tika atteikti → Caddy 502.
2. **Keša slēdzene netur lietotājus**: `_kesots` — ja vērtība ir, bet derīgums beidzies, to atdod uzreiz un atjauno
   viens fona pavediens (stale-while-revalidate); gaida tikai tad, ja vērtības vēl nav nemaz. Kļūda fonā — paliek vecā,
   nākamais mēģinājums pēc minūtes (kā līdz šim). Ārējo avotu izsaukumu skaits nemainās.
3. **`/api/pludi` ≤ 25 s**: pēc tam `202 {"ielade": true, "zinojums": "…"}`; pārbaude turpinās fonā un nonāk kešā.
   Kartīte (`meklesana.js`) rāda „Plūdu kartes vēl ielādējas, mēģinām vēlreiz pēc 10 s…” un mēģina vēl līdz 2 reizēm.
4. **Atmiņas kešs** (`_LRU`): `/api/objekti` pēc parametriem 30 s (64 ieraksti — lapas ielādē visi prasa vienu slāņu
   sarakstu); `adreses/tuvaka` un pašvaldības reģions pēc punkta (~10 m) 1 h.
5. **DB**: ≤ 16 vienlaicīgi vaicājumi (`MAP_DB_VIENLAICIGI`), virs tā 10 s gaida, tad 503 (Postgres savienojumi ir
   kopīgi ar citu projektu uz VPS); `objekti` statement_timeout 8 s.
6. **Neparedzēta kļūda** → JSON 500, nevis pārtraukts savienojums; `/api/veseliba?statistika=1` — keša skaitītāji
   (`no_kesas`, `uz_avotu`, `novecojusi`, `gaidija`), DB vaicājumi un pārslodzes, pavedienu skaits.

## Caddy (POST ātruma ierobežojums)

VPS Caddy v2.11.6 bez `rate_limit` moduļa (`caddy list-modules`), tāpēc paliek procesa ierobežojumi: `/api/meklejumi`
≤ 60 ierakstu minūtē visam procesam (izmet klusi), ķermenis ≤ 2 KB. Ja vēlāk vajag per-IP ierobežojumu, Caddy jāpārbūvē ar
`github.com/mholt/caddy-ratelimit` (xcaddy) — ne pirms žūrijas.

## VPS soļi

Nav. API pārstartējas pats pēc sapludināšanas. Pēc tam (rītā) saudzīga pārbaude:
`uv run --no-project --python 3.12 --with httpx src/testi/slodze.py --klienti 5 --ilgums 30 --rps 2 --tikai-kesa --statistika`.
