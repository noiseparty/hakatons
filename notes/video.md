# Backup demo video (~90 s): storyboard and how to rerun

The backup in case the venue Wi-Fi fails (pitch §5) is a 90-second video of https://map.repo.lv on a phone, with a story and Latvian captions.
Script: `src/demo/video.py`. Output goes outside the repo (`..\demo-video\` next to the main checkout) and is **not committed**.

## Output

| File | What |
|---|---|
| `demo-vertikals.mp4` | 1080 × 1920, H.264, 30 fps. The phone sits in a dark frame and the caption is in the bottom third (white text on a dark translucent bar, 2 lines max). |
| `demo-horizontals.mp4` | 1920 × 1080, H.264, 30 fps. The phone is centred with rounded corners. The left side has map.repo.lv and the list of 7 scenes with the current one marked. The right side has "N / 7" and the scene caption, shown for the whole scene. |
| `captions.srt` | The 7 captions, each shown for 5.5 s from the start of its scene (same timing as the vertical video) |
| `01-sakums.png` … `07-datu-avoti.png` | One still per scene for the slides, 1170 × 2532 (390 × 844 at DPR 3) |
| `_kadri/` | Raw screencast frames and `laika-josla.json`. These let you recompose with `--tikai-salikt` without recording again. |

## Storyboard (scene · what happens · caption)

| # | ~s | What is on screen | Caption |
|---|---|---|---|
| 1 | 8 | The map loads with the sheet collapsed ("Mazs") and pans slowly to Ogre. Then the sheet opens to "Puse" and the search field is tapped. | Krīze. Jūs vēlaties zināt vienu lietu: ko darīt. |
| 2 | 13 | Types "Ogre, plūdi" (75 ms per character) and gets one card. The sheet opens to "Pilns". The card scrolls through: LVĢMC warning → flood-risk zone decision → nearest river gauge with level and 24 h change → forecast. | Viena rinda: „Ogre, plūdi”. Brīdinājums, lēmums, upes līmenis. |
| 3 | 14 | Scrolls to "Evakuācijas pulcēšanās vietas (pašvaldību CA plāni)". The first place's "Avots: Ogres novada CA plāns, lpp. 121" and its route links (Google Maps / Waze / OSM) are highlighted. Then scrolls on to the nearest shelter. | Tuvākā pulcēšanās vieta ar avotu un licenci |
| 4 | 13 | Types "Brīvības iela 12, Ogre, plūdi". The VZD address is found, the map shows the pin and the card shows the flood decision for that address plus the gauge. | Jūsu adrese? Atbilde uzreiz. |
| 5 | 12 | Types "cilvēks nav pie samaņas". A red block "Izklausās, ka apdraudēta dzīvība. Zvaniet 112 tūlīt" appears at the top of the card. There is no tel: button. | Dzīvībai bīstami? 112 vienmēr augšā. |
| 6 | 12 | Opens `?demo=bez-sakariem&regions=100003470` (SIMULĀCIJA, Ogre). Under "Ko darīt" the LR1 line ("Latvijas Radio 1 … 90,7 FM") is highlighted, then the view scrolls to "Kur doties bez telefona" (VUGD depot, police). | Darbojas bez interneta un bez elektrības |
| 7 | 15 + 5 | Opens "Kartes slāņi" → "Saglabāt manu apkārtni bezsaistei" → "Datu avoti" ("29 atvērto datu avoti · 2 simulēti"), then a slow scroll through the sources with their licences. Ends on an end card: map.repo.lv, "Ko Jums vajag? Viena rinda — viens lēmums.", the team / hackathon line. | Atvērtie dati: 20+ avoti, katrs ar licenci |

Pacing:
- Typing runs at 75 ms per character, and there is a 1.5–2 s pause after each result.
- Scrolling uses `page.mouse.wheel` in steps of 7–22 px, so it moves at a readable speed.
- Scenes are joined with a 0.3 s crossfade, and the end card fades in over 0.6 s.
- Waiting is never recorded. Recording is paused during page loads, network idle and the slow flood-zone check (LVĢMC WMS takes up to about 45 s), so the video has no dead time.
- The caption covers the bottom third of the screen. For that reason the important line (decision, 112, radio) is scrolled to the top of the sheet or shown after the caption fades out.

## Rerun

```bash
# from the repo root; records against the live site (one browser, ~2 min), then composes both MP4s (~3 min)
uv run --no-project --with playwright --with pillow --with imageio-ffmpeg src/demo/video.py
# only recompose (layout/caption changes), no load on the site:
uv run --no-project --with playwright --with pillow --with imageio-ffmpeg src/demo/video.py --tikai-salikt
# other options: --url http://localhost:8080/ --izvade C:/path/to/dir
```

- **Recording:** Playwright Chromium with a 390 × 844 viewport, DPR 3, `is_mobile`, `lv-LV`, `Europe/Riga` time zone, and geolocation set to Ogre (56.8162, 24.6140). Frames come from the CDP `Page.startScreencast` at 1170 × 2532 with timestamps and are resampled to a constant 30 fps when composed. An injected style hides the cursor, the tap highlight and scrollbars; the site itself is not changed.
- **Composition:** Pillow draws the frame, captions and end card (Segoe UI, falling back to DejaVu). Raw RGB is piped to ffmpeg with `libx264 -crf 18 -preset slow -pix_fmt yuv420p +faststart`. The script uses the system ffmpeg if it is on PATH, otherwise the one from imageio-ffmpeg.
- **Retakes:** a scene is recorded again (at most 2 retries) when the page throws a JS error (`pageerror`), the result card is empty, or the 112 block is missing. Only the frames of the failed attempt are dropped.
- **Checks at the end:** ffprobe duration and size (warns outside 85–95 s), and the pixel standard deviation of each still (warns below 8, which would mean a blank image).
- The flood-zone line depends on LVĢMC's WMS. When it does not answer, the card says honestly "Neizdevās pārbaudīt. Plūdu zonas redzamas kartē (slānis ieslēgts)", and that is what gets recorded. The script cannot force a yes/no answer.
- Old outputs from the previous script (`01-…11-*.png`, `.webm`) are moved to `vecais/`, not deleted.
- The script deletes `_kadri/` and same-named stills before recording. To keep a previous take, move it by hand first (e.g. `vecais/2026-10-10-0514/`).

## Takes

| When (Riga) | Result |
|---|---|
| 2026-10-10 05:14 | 92.3 s. Kept in `vecais/2026-10-10-0514/` (with its `_kadri/`). |
| 2026-10-10 07:10 | 109.7 s, over the limit. The cards have grown since 05:14: the scroll to the advice in scene 5 alone took ~11 s (scene 5 was 24 s). Kept in `vecais/2026-10-10-0710-110s/`, not for use. |
| **2026-10-10 07:16 (final)** | **88.3 s** both MP4s (vertical 22.4 MB, horizontal 13.4 MB), all 7 scenes ok on the first attempt, no stills blank. Flood row in scenes 2 and 4 shows a real answer: "Nē: nav applūstošā teritorijā", from the cached LVĢMC answer (05:58 / 06:11). Script changes: scene 5 no longer scrolls to the advice (stays on the 112 block), scenes 3 and 7 scroll faster. Scene lengths: 7.7, 13.6, 11.6, 13.7, 10.1, 11.8, 14.6 s + 5 s end card. |

Deck screenshots (`src/demo/ekrani.py`) retaken at 07:16–07:18: 01, 02, 03, 06, 07, 08 updated. 04 and 05 (address) showed "Pārbauda…" in the flood row three times running, so the old files were kept.
