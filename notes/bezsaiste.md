# Bezsaiste (offline PWA): pārbaude 2026-10-10

"Darbojas bez interneta" pārbaudīts pēc nakts ~20 merge. Skripts: `src/testi/bezsaiste.py` (Playwright Chromium,
375×740, service worker atļauts, tīrs konteksts). Gaita: atver lapu → "Ogre, plūdi" → "Datu avoti" →
`navigator.serviceWorker.ready` + kešu saturs → otrs apmeklējums (pārlādē, meklē vēlreiz) → `context.set_offline(True)` →
pārlādē; info.html; statuss.html; `?demo=bez-sakariem`.

```bash
uv run --no-project --python 3.12 src/demo/lokali.py --port 8573        # production/ + /api → map.repo.lv
uv run --no-project --python 3.12 --with playwright src/testi/bezsaiste.py --url http://localhost:8573 --ekr ekr
uv run --no-project --python 3.12 src/testi/sw_faili.py --parbaudit     # exit 1, ja SHELL_FAILI novecojis
uv run --no-project --python 3.12 src/testi/sw_faili.py --rakstit       # pārraksta sarakstu (tad VERSION++)
```

## Rezultāts

| Pārbaude | Pirms (map.repo.lv, `main` 41e6b84, sw `2026-10-10aj`) | Pēc (lokāli, sw `2026-10-10ak`) |
|---|---|---|
| SW instalējas, keši | jā: shell, api-v1, cdn-v1 | jā: + flizes-v1 |
| Shell kešā visi lapu faili | **nē, 51/60**: trūka `zinot.js`, `kajene.js`, `trukstosie.html`, `openapi.json`, `ikona-32/180.png`, Leaflet `images/*.png` | 60/60 (saraksts ģenerēts) |
| Lapa bez tīkla | jā (~4 s); `zinot.js`/`kajene.js` kešā tikai tad, ja lapa jau reiz ielādēta ar SW kontroli (pirmajā apmeklējumā nē) | jā (~4 s), visi skripti |
| Josla "Nav interneta — rādām pēdējos saglabātos datus" | jā | jā + "Šim kartes skatam fona attēli nav saglabāti", ja trūkst flīžu |
| Pēdējā rezultāta kartīte | jā (no localStorage vai API keša) | jā; kartītē rinda "Bez interneta, saglabātie dati: brīdinājumi 04:57 · prognoze 24 h · plūdu zona · upes līmenis · pašvaldība · vietas…" |
| Kartes flīzes | 12/12 (tas pats skats) | 4/10 skatam pēc kartītes atvēršanas; pārējais pelēks, joslā paziņojums |
| info.html (LR1 radio karte) | jā | jā |
| statuss.html | atveras; saka "Statusa API nav pieejams" (sarkans) | tas pats (TODO) |
| `?demo=bez-sakariem` | **daļēji**: simulācija sākās, bet offline.js to pārrakstīja ar saglabāto "Ogre, plūdi" kartīti | demo panelis un scenārijs redzami; josla piedāvā saglabāto kartīti kā pogu |
| Nenotvertas JS kļūdas | nav | nav |
| Manifest | name, short_name, ikonas 192/512 (+svg), theme `#0077c8`, standalone; start_url "/" | start_url un scope "./" |

## Kas mainīts

- `production/sw.js`: SHELL_FAILI no `src/testi/sw_faili.py` (lapas index/info/statuss/api/trukstosie → to
  `src`/`href`, JS/JSON pēdiņās esošie ceļi, CSS `url()`, manifest ikonas; tikai esoši faili; bez og.png, slaidiem,
  moderācijas). API kešs jau saglabāja visus `/api/*` GET (arī `/api/prognoze`, `/api/udens`, `/api/pasvaldiba`,
  `/api/zinojumi`); `noverojumi`, `zinojumi`, `veseliba` tagad skaitās mainīgi dati (bezsaistē ne vecāki par 6 h).
  VERSION `2026-10-10ak`.
- `production/offline.js`: ar `?demo=` (tāpat kā ar `?q=`) saglabātā kartīte neaizstāj simulāciju; josla saka, ja kartes
  fons šim skatam nav saglabāts; kartītes rindā nosaukumi arī `prognoze`, `noverojumi`, `zinojumi`.
- `production/manifest.webmanifest`: `start_url`/`scope` "./".

## Zināmie ierobežojumi

- **Pirmā meklēšana pirmajā apmeklējumā** notiek, pirms SW kontrolē lapu, tāpēc tās API atbildes kešā nenonāk; to sedz
  localStorage kartīte (pēdējās 3). No otrā apmeklējuma viss iet caur kešu.
- Flīzes kešā ir tikai tās, kas skatītas ar SW (vai "Saglabāt manu apkārtni", z12–15). Citā tuvinājumā pelēks fons + josla.
- statuss.html bez tīkla rāda sarkanu "Statusa API nav pieejams" (godīgi, bet varētu teikt "Nav interneta").
- LVĢMC plūdu WMS (geo-dpps.viss.gov.lv) šonakt atbild 504; tās kļūdas ignorētas.
- **Nav pārbaudīts:** īsts telefons (lidmašīnas režīms, "Pievienot sākuma ekrānam" Android Chrome / iOS Safari),
  Firefox/Safari SW uzvedība, ilgāks par 6 h bezsaistes laiks (mainīgie dati tad vairs netiek rādīti).
- Citas sesijas arī maina sw.js: pēc `git merge main` palaidiet `sw_faili.py --rakstit` un nomainiet VERSION.
