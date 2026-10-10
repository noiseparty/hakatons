# Uzbūvē production/ikonas/ikonas.svg: Meteocons "flat" (MIT) laikapstākļiem + Lucide (ISC) pārējam. Lietošana: python src/ikonas/spraits.py production/ikonas/ikonas.svg
import re, sys, urllib.request, pathlib

IZEJA = pathlib.Path(sys.argv[1])
METEO = 'https://cdn.jsdelivr.net/npm/@meteocons/svg-static@3.0.0-next.10/flat/{}.svg'
LUCIDE = 'https://cdn.jsdelivr.net/npm/lucide-static@1.54.0/icons/{}.svg'

METEOCONS = {  # sprite id: meteocons nosaukums
    'brid': 'weather-alert', 'brid-dzeltens': 'code-yellow', 'brid-oranzs': 'code-orange', 'brid-sarkans': 'code-red',
    'vejs': 'wind', 'lietus': 'rain', 'zibens': 'lightning-bolt', 'negaiss': 'thunderstorms', 'sniegs': 'snowflake',
    'pludi': 'water-tide-high', 'prognoze': 'partly-cloudy-day', 'viesulis': 'tornado', 'uguns': 'fire-alert',
    'limenis': 'raindrop-measure', 'temp': 'thermometer', 'nakts': 'clear-night', 'diena': 'clear-day', 'migla': 'fog', 'dumi': 'smoke',
}
LUCIDE_IK = {
    'slimnica': 'hospital', 'maja': 'house', 'patvertne': 'shield', 'karogs': 'flag', 'vieta': 'map-pin',
    'vugd': 'fire-extinguisher', 'zales': 'pill', 'degviela': 'fuel', 'kontakts': 'plug', 'drukat': 'printer',
    'mikrofons': 'mic', 'marsruts': 'navigation', 'remonts': 'construction', 'auto': 'car', 'avarija': 'siren',
    'cisterna': 'cylinder', 'rupnica': 'factory', 'eka': 'building', 'taimeris': 'timer', 'zinot': 'megaphone',
    'zinas': 'newspaper', 'pleksteris': 'bandage', 'nauda': 'banknote', 'dokuments': 'file-text', 'bez-sakariem': 'phone-off',
    'policija': 'shield-user', 'telefons': 'smartphone', 'atkartot': 'repeat', 'autobuss': 'bus', 'logs': 'app-window',
    'ekrans': 'monitor', 'karte': 'map', 'pulkstenis': 'clock', 'slegts': 'ban', 'lejupielade': 'download',
    'atrast': 'locate', 'atpakal-solis': 'skip-back', 'pauze': 'pause', 'uz-prieksu': 'skip-forward', 'atskanot': 'play',
    'apturet': 'square', 'koks': 'tree-deciduous', 'drons': 'plane', 'info': 'info', 'uzmanibu': 'triangle-alert',
    'lase': 'droplet', 'dalities': 'share-2', 'izvelne': 'menu', 'saraksts': 'list', 'aizvert': 'x',
}


def lejup(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'map.repo.lv ikonas'}), timeout=30) as r:
        return r.read().decode('utf-8')


def iekshiene(svg):
    vb = re.search(r'viewBox="([^"]+)"', svg).group(1)
    sakums = re.search(r'<svg[^>]*>', svg).end()
    return vb, svg[sakums:svg.rindex('</svg>')].strip()


simboli = []
for sid, nos in METEOCONS.items():
    vb, saturs = iekshiene(lejup(METEO.format(nos)))
    ids = set(re.findall(r'id="([^"]+)"', saturs))
    for i in sorted(ids, key=len, reverse=True):  # id unikāli visā spraitā
        saturs = re.sub(r'(id="|url\(#|href="#)' + re.escape(i) + r'(["\)])', r'\g<1>' + sid + '-' + i + r'\2', saturs)
    simboli.append(f'<symbol id="{sid}" viewBox="{vb}"><!-- meteocons {nos} -->{saturs}</symbol>')
for sid, nos in LUCIDE_IK.items():
    sid = sid.replace('ī', 'i')
    vb, saturs = iekshiene(lejup(LUCIDE.format(nos)))
    simboli.append(f'<symbol id="{sid}" viewBox="{vb}" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
                   f'stroke-linejoin="round"><!-- lucide {nos} -->{saturs}</symbol>')

IZEJA.parent.mkdir(parents=True, exist_ok=True)
IZEJA.write_text('<svg xmlns="http://www.w3.org/2000/svg">\n<!-- Ikonas: Meteocons (Bas Milius, MIT, laikapstākļi) un Lucide (ISC, pārējās).'
                 ' Licences: ikonas/LICENSES.md. Ģenerē: python src/ikonas/spraits.py production/ikonas/ikonas.svg -->\n' + '\n'.join(simboli) + '\n</svg>\n',
                 encoding='utf-8')
print(IZEJA, len(simboli), IZEJA.stat().st_size // 1024, 'KB')
