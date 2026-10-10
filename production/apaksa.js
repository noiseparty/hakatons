// Telefonā (≤ 800 px) meklēšanas rezultāts ir apakšējā lapā virs kartes, nevis zem tās: karte paliek redzama.
// Trīs stāvokļi: "peek" (rokturis + spriedums), "puse" (~50 %), "pilna" (ritināma); rokturi var vilkt vai pieskarties.
// Pirmā rinda vienmēr ir spriedums: 112 / plūdu zona jā-nē / LVĢMC brīdinājums. Galvenā darbība — maršruts uz tuvāko.
// Kad atveras demo panelis (demo.js), prognožu lente (prognozes.js) vai filtri, lapa saplok līdz rokturim — un otrādi.
// Datorā nekas nemainās: #rezultati paliek sānu panelī. Lieto app.js globālos (karte, el).
const Apaksa = (() => {
  const telefons = matchMedia('(max-width: 800px)');
  const STAVOKLI = ['peek', 'puse', 'pilna'];
  const kaste = el('rezultati');
  const majas = kaste.parentElement;  // #meklesana sānu panelī
  document.body.insertAdjacentHTML('beforeend', `
    <section id="apaksa" class="apaksa" role="region" aria-label="Meklēšanas rezultāts" data-stavoklis="puse" hidden>
      <button id="apaksa-rokturis" class="apaksa-rokturis" type="button" aria-expanded="true" aria-controls="apaksa-saturs">
        <span class="apaksa-svitra" aria-hidden="true"></span>
        <span class="apaksa-spriedums"></span>
        <span class="apaksa-norade" aria-hidden="true"></span>
      </button>
      <a class="apaksa-darbiba" target="_blank" rel="noopener" hidden></a>
      <div id="apaksa-saturs" class="apaksa-saturs"></div>
    </section>`);
  const lapa = el('apaksa'), rokturis = el('apaksa-rokturis'), saturs = el('apaksa-saturs');
  const spriedums = lapa.querySelector('.apaksa-spriedums'), darbiba = lapa.querySelector('.apaksa-darbiba');
  let stavoklis = 'puse';

  const aktiva = () => telefons.matches;
  const redzama = () => aktiva() && !lapa.hidden;

  // Lapas augstums pēc stāvokļa (nevis CSS pārejas vidū); jāsakrīt ar stils.css .apaksa[data-stavoklis]
  const DALA = { peek: 0.2, puse: 0.5, pilna: 0.92 };
  function augstums() {
    return redzama() ? Math.round(innerHeight * DALA[stavoklis]) : 0;
  }

  function iestatit(jauns) {
    stavoklis = jauns;
    lapa.dataset.stavoklis = jauns;
    lapa.style.height = '';
    rokturis.setAttribute('aria-expanded', jauns !== 'peek');
    rokturis.setAttribute('aria-label', (jauns === 'peek' ? 'Atvērt' : jauns === 'puse' ? 'Atvērt visu' : 'Sakļaut') + ' rezultātu: ' + spriedums.textContent);
    lapa.querySelector('.apaksa-norade').textContent = jauns === 'pilna' ? '▾' : '▴';
    if (jauns !== 'peek') {
      if (document.body.classList.contains('demo-atverts') && typeof Demo !== 'undefined') Demo.atvert(false);
      if (el('prognozes')?.classList.contains('atverts') && typeof Prognozes !== 'undefined') Prognozes.atvert(false);
    }
    setTimeout(atjaunotAugstumu, 260);  // pēc CSS pārejas
  }

  // Kartes apakšējās vadīklas (atsauces, mērogs, pamatkarte) paceļ līdz "peek" augstumam, ne augstāk: pie atvērtas
  // lapas tās citādi uzkāptu virsū demo cilnei un kartes rīkiem
  function atjaunotAugstumu() {
    document.documentElement.style.setProperty('--apaksa-h', Math.min(augstums(), Math.round(innerHeight * DALA.peek)) + 'px');
  }

  // Spriedums: 112 → plūdu zona jā/nē → LVĢMC brīdinājums šai vietai → ko sapratām
  function atjaunotSpriedumu() {
    const teksts = s => (s?.textContent || '').replace(/\s+/g, ' ').trim();
    const draudi = kaste.querySelector('.draudi');
    const pludi = kaste.querySelector('#rez-pludi div > span');
    const josla = el('bridinajums');
    let t = '', klase = '', ikona = '';
    if (draudi) { t = teksts(draudi); klase = 'sarkans'; }
    else if (pludi && !/Pārbauda/.test(pludi.textContent)) {
      t = 'Plūdu riska zona: ' + teksts(pludi); ikona = 'pludi';
      klase = pludi.querySelector('.jā') ? 'oranzs' : '';
    } else if (josla && !josla.hidden && !josla.classList.contains('zals')) {
      t = teksts(josla.querySelector('summary') || josla); klase = 'dzeltens';
    } else t = teksts(kaste.querySelector('.zvanit-teksts')) || teksts(kaste.querySelector('.sapratu')) || 'Meklēšanas rezultāts';
    spriedums.innerHTML = (ikona ? Ik(ikona) + ' ' : '') + esc(t);
    lapa.dataset.spriedums = klase;
    // Galvenā darbība: maršruts uz pirmo (tuvāko) vietu kartītē
    const saite = kaste.querySelector('li[data-lat] .marsruts a');
    const vieta = saite?.closest('li[data-lat]')?.querySelector('b');
    darbiba.hidden = !saite;
    if (saite) {
      darbiba.href = saite.href;
      darbiba.innerHTML = Ik('marsruts') + ' Maršruts: ' + esc(teksts(vieta));
      darbiba.setAttribute('aria-label', 'Maršruts uz tuvāko vietu: ' + teksts(vieta));
    }
  }

  function novietot() {
    if (aktiva()) {
      if (kaste.parentElement !== saturs) saturs.append(kaste);
      document.body.classList.add('apaksa-aktiva');
      lapa.hidden = kaste.hidden;
    } else {
      if (kaste.parentElement !== majas) majas.append(kaste);
      document.body.classList.remove('apaksa-aktiva');
      lapa.hidden = true;
    }
    karte.invalidateSize();
    atjaunotAugstumu();
  }

  // Rezultāts parādās / pazūd / mainās (meklesana.js) → lapa seko
  new MutationObserver(() => {
    const bija = lapa.hidden;
    if (aktiva()) lapa.hidden = kaste.hidden;
    if (bija && !lapa.hidden) iestatit('puse');
    atjaunotSpriedumu();
    atjaunotAugstumu();
  }).observe(kaste, { attributes: true, attributeFilter: ['hidden'], childList: true, subtree: true, characterData: true });
  new MutationObserver(atjaunotSpriedumu).observe(el('bridinajums'), { attributes: true, childList: true, subtree: true });

  // Demo panelis, prognožu lente vai filtru panelis atveras → lapa saplok līdz rokturim
  const saplakt = () => { if (redzama() && stavoklis !== 'peek') iestatit('peek'); };
  new MutationObserver(() => {
    const b = document.body.classList;
    if (b.contains('demo-atverts') || !b.contains('panelis-slegts')) saplakt();
  }).observe(document.body, { attributes: true, attributeFilter: ['class'] });
  const prognozes = el('prognozes');
  if (prognozes) new MutationObserver(() => { if (prognozes.classList.contains('atverts')) saplakt(); })
    .observe(prognozes, { attributes: true, attributeFilter: ['class'] });

  // Rokturis: pieskāriens pārslēdz peek → puse → pilna → peek; vilkšana — uz tuvāko stāvokli
  let vilkt = null;
  rokturis.addEventListener('pointerdown', e => {
    vilkt = { y: e.clientY, h: lapa.getBoundingClientRect().height, kustejas: false };
    rokturis.setPointerCapture(e.pointerId);
  });
  rokturis.addEventListener('pointermove', e => {
    if (!vilkt) return;
    const dy = e.clientY - vilkt.y;
    if (Math.abs(dy) > 6) vilkt.kustejas = true;
    if (vilkt.kustejas) {
      lapa.classList.add('velk');
      lapa.style.height = Math.max(64, Math.min(innerHeight * 0.92, vilkt.h - dy)) + 'px';
    }
  });
  const beigtVilkt = e => {
    if (!vilkt) return;
    const v = vilkt;
    vilkt = null;
    lapa.classList.remove('velk');
    if (!v.kustejas) return;
    e.preventDefault();
    const h = lapa.getBoundingClientRect().height / innerHeight;
    iestatit(h < 0.35 ? 'peek' : h < 0.71 ? 'puse' : 'pilna');
    rokturis.dataset.vilkts = '1';  // nākamais "click" pēc vilkšanas nav pieskāriens
  };
  rokturis.addEventListener('pointerup', beigtVilkt);
  rokturis.addEventListener('pointercancel', beigtVilkt);
  rokturis.addEventListener('click', () => {
    if (rokturis.dataset.vilkts) { delete rokturis.dataset.vilkts; return; }
    iestatit(STAVOKLI[(STAVOKLI.indexOf(stavoklis) + 1) % STAVOKLI.length]);
  });

  // Velkot karti, lapa saplok, lai karte ir redzama
  karte.on('dragstart', () => { if (redzama() && stavoklis === 'pilna') iestatit('puse'); });

  telefons.addEventListener('change', novietot);
  addEventListener('resize', atjaunotAugstumu);
  novietot();

  return {
    aktiva,
    augstums,
    atvert(st = 'puse') {
      if (!aktiva()) return;
      karte.invalidateSize();  // kartes izmērs varēja mainīties (filtru panelis, 100dvh); citādi fitBounds rēķina pēc veca augstuma
      lapa.hidden = kaste.hidden; iestatit(st); atjaunotSpriedumu();
    },
  };
})();
