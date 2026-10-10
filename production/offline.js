// Bezsaistes režīms (sw.js): josla "Nav interneta — rādām pēdējos saglabātos datus", rezultāta kartītē
// rinda par saglabātajiem datiem, pēdējās 3 kartītes (localStorage) un "Saglabāt manu apkārtni" (flīzes z12–15).
// Lieto app.js globālos (karte, el, stavoklis, pamatkartes) — tikai tad, kad tie ir.
const Bezsaiste = (() => {
  const KARTITES = 'bezsaiste-kartites';
  const josla = document.getElementById('bezsakaru');
  const saglabati = {};  // /api/<galapunkts> → saglabāšanas laiks (no sw.js galvenes), šīs meklēšanas laikā
  const NOSAUKUMI = { bridinajumi: 'brīdinājumi', objekti: 'vietas', udens: 'upes līmenis', pludi: 'plūdu zona', celi: 'ceļi',
    satiksme: 'satiksme', pasvaldiba: 'pašvaldība', adreses: 'adrese', kategorijas: 'slāņi', regioni: 'reģioni', avoti: 'avoti',
    augsne: 'nokrišņi', prognozes: 'prognoze', prognoze: 'prognoze 24 h', zibens: 'zibens', noverojumi: 'laikapstākļi',
    zinojumi: 'iedzīvotāju ziņojumi' };
  const laiks = iso => new Date(iso).toLocaleString('lv-LV', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' });
  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

  // Service worker reģistrē atjaunot.js (visām lapām; paziņojums par jaunu versiju, ?svaigs=1)

  // Atbildes no sw.js keša: atzīmējam galapunktu un laiku
  const fetchOrig = window.fetch.bind(window);
  window.fetch = async (...args) => {
    const r = await fetchOrig(...args);
    try {
      if (r.headers.get('x-sw-no-kesas')) {
        const cels = new URL(r.url).pathname.split('/')[2] || '';
        const t = r.headers.get('x-sw-saglabats');
        if (t && (!saglabati[cels] || t < saglabati[cels])) saglabati[cels] = t;
        atjaunotJoslu();
        atjaunotKartitesRindu();
      }
    } catch { /* nekas */ }
    return r;
  };

  function vecakais() {
    const t = Object.values(saglabati).sort()[0];
    return t ? laiks(t) : null;
  }

  function atjaunotJoslu() {
    if (!josla) return;
    const bez = !navigator.onLine || Object.keys(saglabati).length;
    if (!bez) { josla.hidden = true; return; }
    const kartites = lasitKartites();
    const t = vecakais();
    josla.innerHTML = `<b>${navigator.onLine ? Valoda.t('Serveris neatbild') : Valoda.t('Nav interneta')}</b> — ${Valoda.t('rādām pēdējos saglabātos datus')}${t ? ` (${Valoda.t('saglabāti {t}', { t: esc(t) })})` : ''}.` +
      (flizuTrukst ? ' ' + Valoda.t('Šim kartes skatam fona attēli nav saglabāti.') : '') +
      (kartites.length ? ' ' + Valoda.t('Pēdējie rezultāti') + ': ' + kartites.map((k, i) =>
        `<button type="button" data-kartite="${i}">${esc(k.vaicajums)}</button>`).join(' ') : '');
    josla.hidden = false;
  }
  josla?.addEventListener('click', e => {
    const i = e.target.closest('[data-kartite]')?.dataset.kartite;
    if (i != null) atvertKartiti(lasitKartites()[+i]);
  });
  window.addEventListener('online', () => { for (const k in saglabati) delete saglabati[k]; flizuTrukst = false; atjaunotJoslu(); });
  // Kartes fons bez interneta: flīzes, kuru nav sw.js kešā, paliek pelēkas — joslā pasakām, kāpēc
  let flizuTrukst = false;
  function flizuKluda() {
    if (navigator.onLine || flizuTrukst) return;
    flizuTrukst = true;
    atjaunotJoslu();
  }
  document.addEventListener('DOMContentLoaded', () => {
    if (typeof pamatkartes !== 'undefined') for (const s of Object.values(pamatkartes)) s.on('tileerror', flizuKluda);
  });
  window.addEventListener('offline', atjaunotJoslu);

  // Rezultāta kartītē: kuri dati ir no saglabātā (un kad)
  function atjaunotKartitesRindu() {
    const kaste = document.getElementById('rezultati');
    if (!kaste || kaste.hidden || kaste.querySelector('.saglabata-kartite')) return;
    const dalas = Object.entries(saglabati).filter(([c]) => NOSAUKUMI[c] && !['kategorijas', 'regioni', 'avoti', 'prognozes', 'zibens'].includes(c))
      .map(([c, t]) => `${Valoda.t(NOSAUKUMI[c])} ${laiks(t)}`);
    if (!dalas.length) return;
    let p = kaste.querySelector('#rez-kesa');
    if (!p) {
      p = document.createElement('p');
      p.id = 'rez-kesa';
      p.className = 'kesa-rinda';
      kaste.prepend(p);
    }
    p.textContent = (navigator.onLine ? Valoda.t('Serveris neatbild') : Valoda.t('Bez interneta')) + Valoda.t(', saglabātie dati: ') + dalas.join(' · ') + '.';
  }
  document.getElementById('meklet-forma')?.addEventListener('submit', () => {
    if (navigator.onLine) for (const k in saglabati) delete saglabati[k];
  });

  // Pēdējās 3 kartītes: saglabājam, kad kartīte ir pilna (vietas ielādētas), atveram bez interneta
  function lasitKartites() {
    try { return JSON.parse(localStorage.getItem(KARTITES)) || []; } catch { return []; }
  }
  let taimeris = null;
  const kaste = document.getElementById('rezultati');
  if (kaste) new MutationObserver(() => {
    clearTimeout(taimeris);
    taimeris = setTimeout(saglabatKartiti, 2500);
  }).observe(kaste, { childList: true, subtree: true, characterData: true });

  function saglabatKartiti() {
    if (!kaste || kaste.hidden || kaste.querySelector('.saglabata-kartite')) return;
    const vaicajums = (document.getElementById('jautajums')?.value || '').trim();
    if (!vaicajums || !kaste.querySelector('.sapratu') || /Meklē tuvākās vietas…|Meklē adresi…/.test(kaste.textContent)) return;
    const kopija = kaste.cloneNode(true);
    kopija.querySelector('#rez-kesa')?.remove();
    const ieraksts = { vaicajums, html: kopija.innerHTML, laiks: new Date().toISOString() };
    const saraksts = [ieraksts, ...lasitKartites().filter(k => k.vaicajums.toLowerCase() !== vaicajums.toLowerCase())].slice(0, 3);
    try { localStorage.setItem(KARTITES, JSON.stringify(saraksts)); } catch { /* pilns — nesaglabājam */ }
  }

  function atvertKartiti(k) {
    if (!k || !kaste) return;
    kaste.innerHTML = `<p class="kesa-rinda saglabata-kartite">${Valoda.t('Saglabāts rezultāts ({t}), rādīts bez interneta.', { t: esc(laiks(k.laiks)) })} ` +
      Valoda.t('Dati var būt novecojuši; ja apdraudēta dzīvība vai veselība, zvaniet 112.') + '</p>' + k.html;
    kaste.hidden = false;
    const lauks = document.getElementById('jautajums');
    if (lauks) lauks.value = k.vaicajums;
    // telefonā kartīte ir apakšējā lapā (apaksa.js); filtru paneli neatveram — tas lapu saplacina
    if (typeof Apaksa !== 'undefined' && Apaksa.aktiva()) Apaksa.atvert('puse');
  }

  // Ielādējot bez interneta: josla un pēdējā kartīte (ja meklēšana pati neko nerāda)
  window.addEventListener('load', () => setTimeout(() => {
    if (navigator.onLine) return;
    if (document.querySelector('#karte .leaflet-tile:not(.leaflet-tile-loaded)')) flizuTrukst = true;
    atjaunotJoslu();
    if (kaste && (kaste.hidden || !kaste.textContent.trim())
        && !['q', 'demo'].some(k => new URLSearchParams(location.search).get(k))) {  // ?q= meklē pats; ?demo= rāda simulāciju
      atvertKartiti(lasitKartites()[0]);
    }
  }, 800));

  // "Saglabāt manu apkārtni": fona flīzes z12–15 ap redzamo laukumu (≤ 400; OSM noteikumi: bez masveida
  // lejupielādes, z ≤ 15, tikai pēc lietotāja pieprasījuma) + pamatdati no API (sw.js tos saglabā)
  const poga = document.getElementById('saglabat-apkartni');
  const teksts = document.getElementById('apkartne-teksts');
  const flize = (lat, lon, z) => {
    const n = 2 ** z, x = Math.floor((lon + 180) / 360 * n);
    const r = lat * Math.PI / 180, y = Math.floor((1 - Math.log(Math.tan(r) + 1 / Math.cos(r)) / Math.PI) / 2 * n);
    return [x, y];
  };
  function flizuSaraksts(b, max = 400) {
    for (let pus = 1; pus > 0.02; pus /= 1.5) {  // ja par daudz, laukumu ap centru samazina
      const c = b.getCenter();
      const dlat = (b.getNorth() - b.getSouth()) / 2 * pus, dlon = (b.getEast() - b.getWest()) / 2 * pus;
      const saraksts = [];
      for (let z = 12; z <= 15; z++) {
        const [x1, y1] = flize(c.lat + dlat, c.lng - dlon, z), [x2, y2] = flize(c.lat - dlat, c.lng + dlon, z);
        for (let x = x1; x <= x2; x++) for (let y = y1; y <= y2; y++) saraksts.push([z, x, y]);
      }
      if (saraksts.length <= max) return saraksts;
    }
    return [];
  }
  poga?.addEventListener('click', async () => {
    if (typeof karte === 'undefined') return;
    if (!navigator.onLine) { teksts.textContent = Valoda.t('Nav interneta: apkārtni var saglabāt tikai ar savienojumu.'); teksts.hidden = false; return; }
    // bez aktīva service worker lejupielādētie attēli bezsaistē neatvērsies — to nesolām
    if (!navigator.serviceWorker?.controller) {
      teksts.textContent = Valoda.t('Bezsaistes kopija šajā pārlūkā vēl nav aktīva (service worker). Atveriet lapu vēlreiz un mēģiniet atkal; privātajā režīmā bezsaistes kopija nav pieejama.');
      teksts.hidden = false;
      return;
    }
    let b = karte.getBounds();
    // tālu attālināta karte → ~10 km ap centru; mazs laukums (telefonā, atvērts panelis) → vismaz ~5 km
    if (karte.getZoom() < 12) b = karte.getCenter().toBounds(10000);
    else if (b.getNorth() - b.getSouth() < 0.045) b = karte.getCenter().toBounds(5000);
    const flizes = flizuSaraksts(b);
    const slanis = Object.values(pamatkartes).find(s => karte.hasLayer(s)) || pamatkartes.karte;
    poga.disabled = true;
    teksts.hidden = false;
    let gatavs = 0, kludas = 0;
    const rinda = [...flizes];
    const darbs = async () => {
      while (rinda.length) {
        const [z, x, y] = rinda.shift();
        const url = slanis.getTileUrl({ x, y, z });
        try { const r = await fetch(url, { mode: 'cors' }); if (!r.ok) kludas++; } catch { kludas++; }
        gatavs++;
        if (gatavs % 10 === 0 || !rinda.length) teksts.textContent = Valoda.t('Saglabā kartes attēlus: {g} / {n}…', { g: gatavs, n: flizes.length });
      }
    };
    await Promise.all([darbs(), darbs()]);  // 2 vienlaicīgi — saudzīgi pret OSM serveriem
    const c = karte.getCenter(), ll = { lat: c.lat.toFixed(5), lon: c.lng.toFixed(5) };
    await Promise.all(['/api/kategorijas', '/api/regioni', '/api/avoti', '/api/bridinajumi?' + new URLSearchParams(ll),
      '/api/udens?' + new URLSearchParams({ ...ll, limit: 3 }), '/api/pasvaldiba?' + new URLSearchParams(ll)]
      .map(u => fetch(u).catch(() => {})));
    teksts.textContent = Valoda.t('Saglabāti {n} kartes attēli (tuvinājums 12–15) un pamatdati. Bez interneta šī apkārtne un pēdējie meklēšanas rezultāti atvērsies no saglabātā.', { n: gatavs - kludas });
    poga.disabled = false;
  });

  return { lasitKartites, atvertKartiti };
})();
