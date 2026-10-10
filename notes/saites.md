# Saišu pārbaude: trukstosie.html, info.html, slaidi.html

Pārbaudīts 2026-10-10 05:55 (+03:00): 22 unikālas saites, no tām 18 ārējas (HEAD, 5 s, GET atkārtojums pie 403/405/501, ne vairāk par 5 pārsūtījumiem). Četras map.repo.lv saites netika pārbaudītas pret dzīvo vietni (slodzes ierobežojums); tās norāda uz production/ failiem, kas ir repozitorijā.

Rezultāts: mirušu saišu nav (0 no 18), neskaidras 2, pārvietota 1.

| Saite | Rezultāts | Ieteikums |
|---|---|---|
| https://www.latvija.gov.lv/ (info.html) | neskaidra: servera SSL sertifikāta ķēde mūsu pārbaudē neapstiprinās; ar `curl -k` 302 (vietne strādā) | atstāt; pārbaudīt telefonā, vai brīdinājuma nav |
| https://github.com/noiseparty/hakatons/blob/main/notes/research/05_avoti_parbaude_2026-10-10.md (trukstosie.html) | neskaidra: 429 (GitHub ierobežo biežumu); fails repozitorijā ir | atstāt |
| https://vugd.gov.lv/lv/media/1351/download (info.html) | pārvietota uz https://www.vugd.gov.lv/lv/media/1351/download (200) | nomainīt uz `www.` adresi, kad info.html tiks labots nākamreiz (labojums nav kritisks, pārsūtījums strādā) |
| https://www.112.lv/ | 200, pārsūta uz https://www.112.lv/lv | atstāt |

Pārējās 14 ārējās saites (data.gov.lv 2, GitHub 4, latvijasradio.lsm.lv, lvportals.lv 2, esakari.lv, lsm.lv 3, vugd.gov.lv/lv/patvertnes) atbild 200.
