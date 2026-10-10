// Telefonā (≤ 800 px) apakšējā lapa virs kartes (notes/ui-mockup.md "Mobile"): augšā rokturis un stāvokļu pogas
// Mazs · Puse · Pilns (140 px · 52 % · 84 %), zem tiem meklēšana; saturu (tēmas, kopsavilkums, cilnes Rezultāts /
// Kartes slāņi / Situācija tagad) veido sheet.js. Lapa redzama vienmēr, arī bez rezultāta; karte paliek redzama virs tās.
// Vilkšana kā lietotnēs: lapa seko pirkstam, pāri robežām "atsperīgi", atlaižot — pēc ātruma uz nākamo stāvokli vai
// uz tuvāko. Saturs ritinās tikai stāvoklī "Pilns"; tajā, ritinot uz leju no pašas augšas, lapa sāk vilkties uz leju.
// Kad atveras demo panelis (demo.js) vai prognožu lente kartē (prognozes.js), lapa saplok līdz "Mazs" — un otrādi.
// Datorā nekas nemainās: #rezultati paliek sānu panelī. Lieto app.js globālos (karte, el).
const Apaksa = (() => {
  const telefons = matchMedia('(max-width: 800px)');
  const STAVOKLI = ['peek', 'puse', 'pilna'];
  const NOS = { peek: 'Mazs', puse: 'Puse', pilna: 'Pilns' };
  const kaste = el('rezultati');
  const majas = kaste.parentElement;  // #meklesana sānu panelī
  document.body.insertAdjacentHTML('beforeend', `
    <section id="apaksa" class="apaksa" role="region" aria-label="Meklēšana un rezultāts" data-stavoklis="puse" hidden>
      <div class="apaksa-augsa">
        <button id="apaksa-rokturis" class="apaksa-rokturis" type="button" aria-expanded="true" aria-controls="apaksa-saturs">
          <span class="apaksa-svitra" aria-hidden="true"></span><span class="apaksa-spriedums"></span>
        </button>
        <div class="apaksa-stavokli" role="group" aria-label="Lapas augstums">${STAVOKLI.map(st =>
          `<button type="button" data-st="${st}" aria-pressed="${st === 'puse'}"><span>${NOS[st]}</span></button>`).join('')}</div>
      </div>
      <div id="apaksa-meklet" class="apaksa-meklet"></div>
      <div id="apaksa-saturs" class="apaksa-saturs"></div>
    </section>`);
  const lapa = el('apaksa'), rokturis = el('apaksa-rokturis'), saturs = el('apaksa-saturs');
  const spriedums = lapa.querySelector('.apaksa-spriedums');
  let stavoklis = 'puse';
  let redzamaisPx = 0;  // pašreizējais redzamais augstums (arī vilkšanas laikā)

  const aktiva = () => telefons.matches;
  const redzama = () => aktiva() && !lapa.hidden;

  // Redzamais augstums pēc stāvokļa. Lapa pati vienmēr ir "Pilns" augstumā (+ REZERVE atsperei uz augšu) un tiek
  // nobīdīta ar transform — tā vilkšana nepārrēķina izkārtojumu katrā kadrā.
  const DALA = { puse: 0.52, pilna: 0.84 }, PEEK_PX = 140, REZERVE = 80;
  const augstumsPx = st => st === 'peek' ? PEEK_PX : Math.round(innerHeight * DALA[st]);
  const augstums = () => redzama() ? augstumsPx(stavoklis) : 0;
  // Rezultāta kartītes vieta: sheet.js cilne "Rezultāts", citādi lapas saturs
  const rezVieta = () => el('lapa-rezultats') || saturs;

  function novietotPx(h) {
    redzamaisPx = h;
    const pilna = augstumsPx('pilna');
    lapa.style.height = (pilna + REZERVE) + 'px';
    lapa.style.transform = `translate3d(0, ${Math.round(pilna - h)}px, 0)`;
  }

  function iestatit(jauns) {
    const bija = stavoklis;
    stavoklis = jauns;
    lapa.dataset.stavoklis = jauns;
    novietotPx(augstumsPx(jauns));
    rokturis.setAttribute('aria-expanded', jauns !== 'peek');
    lapa.querySelectorAll('.apaksa-stavokli button').forEach(b => b.setAttribute('aria-pressed', b.dataset.st === jauns));
    if (jauns !== 'pilna') saturs.scrollTop = 0;
    if (jauns !== 'peek') {
      if (document.body.classList.contains('demo-atverts') && typeof Demo !== 'undefined') Demo.atvert(false);
      // prognožu lente kartē (ne tā, kas pārcelta lapas cilnē "Situācija tagad")
      if (el('prognozes')?.classList.contains('atverts') && !lapa.contains(el('prognozes')) && typeof Prognozes !== 'undefined') Prognozes.atvert(false);
    }
    atjaunotSpriedumu();
    atjaunotAugstumu();
    if (bija !== jauns) lapa.dispatchEvent(new CustomEvent('apaksa:stavoklis', { detail: jauns }));
  }

  // Kartes apakšējās vadīklas (atsauces, mērogs, leģenda) paceļ līdz "Mazs" augstumam, ne augstāk
  function atjaunotAugstumu() {
    document.documentElement.style.setProperty('--apaksa-h', Math.min(augstums(), PEEK_PX) + 'px');
  }

  // Spriedums (ekrāna lasītājam rokturī): 112 → plūdu zona jā/nē → LVĢMC brīdinājums šai vietai → ko sapratām
  function atjaunotSpriedumu() {
    const teksts = s => (s?.textContent || '').replace(/\s+/g, ' ').trim();
    const draudi = kaste.querySelector('.draudi');
    const pludi = kaste.querySelector('#rez-pludi div > span');
    const josla = el('bridinajums');
    let t = '';
    if (draudi) t = teksts(draudi);
    else if (pludi && !/Pārbauda/.test(pludi.textContent)) t = 'Plūdu riska zona: ' + teksts(pludi);
    else if (josla && !josla.hidden && !josla.classList.contains('zals') && !josla.classList.contains('gaida')) t = teksts(josla.querySelector('summary') || josla);
    else if (kaste.hidden) t = lapa.dataset.kopsavilkums || '';
    else t = teksts(kaste.querySelector('.zvanit-teksts')) || teksts(kaste.querySelector('.sapratu'));
    spriedums.textContent = t;
    rokturis.setAttribute('aria-label', (stavoklis === 'pilna' ? 'Sakļaut lapu' : 'Atvērt lapu') + (t ? ': ' + t : ''));
  }

  function novietot() {
    if (aktiva()) {
      if (kaste.parentElement !== rezVieta()) rezVieta().append(kaste);
      document.body.classList.add('apaksa-aktiva');
      lapa.hidden = false;
      novietotPx(augstumsPx(stavoklis));
    } else {
      if (kaste.parentElement !== majas) majas.append(kaste);
      document.body.classList.remove('apaksa-aktiva');
      lapa.hidden = true;
      lapa.style.height = lapa.style.transform = '';
    }
    karte.invalidateSize();
    atjaunotAugstumu();
  }

  // Rezultāts parādās / pazūd / mainās (meklesana.js) → lapa seko
  let bijaRezultats = !kaste.hidden;
  new MutationObserver(() => {
    if (aktiva() && bijaRezultats !== !kaste.hidden) {
      bijaRezultats = !kaste.hidden;
      if (bijaRezultats) { if (stavoklis === 'peek') iestatit('puse'); lapa.dispatchEvent(new CustomEvent('apaksa:rezultats')); }  // sheet.js atver cilni
    }
    atjaunotSpriedumu();
  }).observe(kaste, { attributes: true, attributeFilter: ['hidden'], childList: true, subtree: true, characterData: true });
  new MutationObserver(atjaunotSpriedumu).observe(el('bridinajums'), { attributes: true, childList: true, subtree: true });

  // Demo panelis, prognožu lente kartē vai filtru panelis atveras → lapa saplok līdz "Mazs"
  const saplakt = () => { if (redzama() && stavoklis !== 'peek') iestatit('peek'); };
  new MutationObserver(() => {
    const b = document.body.classList;
    if (b.contains('demo-atverts') || !b.contains('panelis-slegts')) saplakt();
  }).observe(document.body, { attributes: true, attributeFilter: ['class'] });
  const prognozes = el('prognozes');
  if (prognozes) new MutationObserver(() => { if (prognozes.classList.contains('atverts') && !lapa.contains(prognozes)) saplakt(); })
    .observe(prognozes, { attributes: true, attributeFilter: ['class'] });

  // ---- Vilkšana: pirksts (touch*) visā lapā, pele (pointer*) augšējā joslā ----
  const SLIEKSNIS = 6, ATRUMS = 0.3;  // px; px/ms — ātrāk par to atlaižot, lapa aizslīd uz nākamo stāvokli virzienā
  let v = null;
  function sakt(x, y, t, merkis) {
    v = { x0: x, y0: y, h0: redzamaisPx, punkti: [[y, t]], saturs: !!merkis.closest?.('.apaksa-saturs'), rezims: null };
  }
  // Atgriež true, ja kustība ir lapas vilkšana (tad notikumam jāizsauc preventDefault)
  function kustet(x, y, t) {
    if (!v || v.rezims === 'nav') return false;
    const dx = x - v.x0, dy = y - v.y0;
    if (!v.rezims) {
      // līdz lēmumam: "Pilns" satura augšā uz leju neļaujam pārlūkam sākt ritināt (citādi vilkšanu vairs nevar pārņemt)
      if (Math.abs(dx) < SLIEKSNIS && Math.abs(dy) < SLIEKSNIS) return stavoklis === 'pilna' && v.saturs && saturs.scrollTop <= 0 && dy > 0;
      if (Math.abs(dx) > Math.abs(dy)) v.rezims = 'nav';  // horizontāli: tēmu pogu josla ritinās pati
      else if (v.saturs && stavoklis === 'pilna' && (saturs.scrollTop > 0 || dy < 0)) v.rezims = 'nav';  // parasta ritināšana
      else { v.rezims = 'velk'; v.y0 = y; lapa.classList.add('velk'); }
      if (v.rezims === 'nav') return false;
    }
    const zem = augstumsPx('peek'), virs = augstumsPx('pilna');
    let h = v.h0 - (y - v.y0);
    if (h > virs) h = virs + Math.min(REZERVE, (h - virs) * 0.3);  // atspere virs "Pilns"
    else if (h < zem) h = zem - Math.min(60, (zem - h) * 0.3);    // un zem "Mazs"
    novietotPx(h);
    v.punkti.push([y, t]);
    while (v.punkti.length > 2 && t - v.punkti[0][1] > 100) v.punkti.shift();
    return true;
  }
  function beigt(tBeigas) {
    if (!v) return;
    const b = v;
    v = null;
    if (b.rezims !== 'velk') return;
    lapa.classList.remove('velk');
    rokturis.dataset.vilkts = '1';  // "click" uzreiz pēc vilkšanas nav pieskāriens
    setTimeout(() => delete rokturis.dataset.vilkts, 350);
    const [y0, t0] = b.punkti[0], [y1, t1] = b.punkti[b.punkti.length - 1];
    // + uz leju; ja pirksts pirms atlaišanas apstājās (> 90 ms bez kustības), ātrums ir 0 — tad uz tuvāko stāvokli
    const atr = t1 > t0 && !(tBeigas - t1 > 90) ? (y1 - y0) / (t1 - t0) : 0;
    const h = redzamaisPx, augst = STAVOKLI.map(augstumsPx);
    let merkis;
    if (atr > ATRUMS) merkis = [...STAVOKLI].reverse().find(st => augstumsPx(st) < h - 8) || 'peek';
    else if (atr < -ATRUMS) merkis = STAVOKLI.find(st => augstumsPx(st) > h + 8) || 'pilna';
    else merkis = STAVOKLI[augst.reduce((lab, a, i) => Math.abs(a - h) < Math.abs(augst[lab] - h) ? i : lab, 0)];
    iestatit(merkis);
  }
  lapa.addEventListener('touchstart', e => {
    if (e.touches.length === 1) sakt(e.touches[0].clientX, e.touches[0].clientY, e.timeStamp, e.target);
    else v = null;
  }, { passive: true });
  lapa.addEventListener('touchmove', e => {
    if (v && kustet(e.touches[0].clientX, e.touches[0].clientY, e.timeStamp) && e.cancelable) e.preventDefault();
  }, { passive: false });
  lapa.addEventListener('touchend', e => beigt(e.timeStamp));
  lapa.addEventListener('touchcancel', e => beigt(e.timeStamp));
  lapa.querySelector('.apaksa-augsa').addEventListener('pointerdown', e => {
    if (e.pointerType !== 'mouse' || e.button) return;
    sakt(e.clientX, e.clientY, e.timeStamp, e.target);
    const kust = m => kustet(m.clientX, m.clientY, m.timeStamp);
    const gals = u => { removeEventListener('pointermove', kust); removeEventListener('pointerup', gals); beigt(u.timeStamp); };
    addEventListener('pointermove', kust);
    addEventListener('pointerup', gals);
  });

  // Rokturis: pieskāriens pārslēdz Mazs → Puse → Pilns → Mazs; stāvokļu pogas — tieši
  rokturis.addEventListener('click', () => {
    if (rokturis.dataset.vilkts) return;
    iestatit(STAVOKLI[(STAVOKLI.indexOf(stavoklis) + 1) % STAVOKLI.length]);
  });
  lapa.querySelector('.apaksa-stavokli').addEventListener('click', e => {
    const st = e.target.closest('[data-st]')?.dataset.st;
    if (st && !rokturis.dataset.vilkts) iestatit(st);
  });

  // Velkot karti, pilna lapa saplok līdz pusei, lai karte ir redzama
  karte.on('dragstart', () => { if (redzama() && stavoklis === 'pilna') iestatit('puse'); });

  telefons.addEventListener('change', novietot);
  addEventListener('resize', () => { if (redzama() && !v) novietotPx(augstumsPx(stavoklis)); atjaunotAugstumu(); });
  novietot();

  return {
    aktiva,
    augstums,
    atvert(st = 'puse') {
      if (!aktiva()) return;
      karte.invalidateSize();  // kartes izmērs varēja mainīties (100dvh); citādi fitBounds rēķina pēc veca augstuma
      lapa.hidden = false; iestatit(st);
    },
    stavoklis: () => stavoklis,
    // fitBounds atstarpes telefonā: augšā joslas + "Karte | Reljefs", labajā pusē kartes pogas, apakšā lapa
    atstarpes(apaksa = augstums()) {
      return { paddingTopLeft: [24, (el('kartes-joslas')?.offsetHeight || 0) + 58], paddingBottomRight: [60, apaksa + 16] };
    },
    atjaunotSpriedumu,
    novietot,
  };
})();
