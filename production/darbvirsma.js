// Datora izkārtojums (> 800 px) pēc lietotāja maketa (notes/mockup/desktop.html, notes/ui-mockup.md "Desktop"):
// galvene (zīme, "Meklēšana & Lēmums" / "Slāņu vadība", "Par datiem & AI"), 112 josla ar datu svaigumu,
// brīdinājumu josla ar "Aizvērt"; trīs kolonnas — kreisajā meklēšana, čipi, kopējā situācija un rezultāta kartīte,
// vidū karte ar leģendu, labajā "Situācija tagad (Latvija)". Abas malas var sakļaut, lai karte būtu pa visu platumu.
// Telefona izkārtojumu (≤ 800 px) šis fails neaiztiek: esošos elementus pārvieto tikai platā ekrānā un atliek
// atpakaļ, kad ekrāns kļūst šaurs (stils: darbvirsma.css). Lieto app.js globālos (karte, kategorijas, stavoklis…).
const Darbvirsma = (() => {
  const plats = matchMedia('(min-width: 801px)');
  const $ = id => document.getElementById(id);
  const laiks = iso => iso ? Valoda.fmtDatums(iso, true) : '';  // DD/MM/YYYY HH:MM visās valodās
  const stunda = d => d.toLocaleTimeString('lv-LV', { hour: '2-digit', minute: '2-digit' });
  const LIMENI = { 1: ['dzeltens', 'Dzeltens'], 2: ['oranzs', 'Oranžs'], 3: ['sarkans', 'Sarkans'] };
  const PILLS = { 3: ['{n} sarkans brīdinājums', '{n} sarkani brīdinājumi'], 2: ['{n} oranžs brīdinājums', '{n} oranži brīdinājumi'], 1: ['{n} dzeltens brīdinājums', '{n} dzelteni brīdinājumi'] };
  const ATSLEGA = 'darbvirsma';  // { situacija: true|false, kreisa: true|false } pārlūkā
  const IKONAS = {
    vairogs: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2 4 5v6c0 5 3.4 9.4 8 11 4.6-1.6 8-6 8-11V5l-8-3Z" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/><path d="M12 8v6M9 11h6" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>',
    meklet: '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="6.5" fill="none" stroke="currentColor" stroke-width="2"/><path d="m16 16 4.5 4.5" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>',
    slani: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m12 3 9 5-9 5-9-5 9-5Z" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/><path d="m3 13 9 5 9-5" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/></svg>',
    vieta: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M21 3 3 10.5l7.5 2.5L13 21l8-18Z" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/></svg>',
    info: '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" stroke-width="2"/><path d="M12 8v5M12 16h.01" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>',
    panelis: '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3.5" y="4.5" width="17" height="15" rx="2" fill="none" stroke="currentColor" stroke-width="2"/><path d="M14.5 4.5v15" stroke="currentColor" stroke-width="2"/></svg>',
    zinot: '<svg viewBox="0 0 24 24" aria-hidden="true" class="dv-zinot-ikona"><path d="M4 10v4h3l6 4V6L7 10H4Z" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/><path d="M17 9a4 4 0 0 1 0 6M19.5 6.5a7.5 7.5 0 0 1 0 11" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>',
    pilns: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 9V4h5M20 9V4h-5M4 15v5h5M20 15v5h-5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
  };
  const AVOTI = {
    bridinajumi: '<a href="https://data.gov.lv/dati/lv/dataset/hidrometeorologiskie-bridinajumi" target="_blank" rel="noopener">LVĢMC</a>',
    udens: '<a href="https://data.gov.lv/dati/lv/dataset/hidrometeorologiskie-noverojumi" target="_blank" rel="noopener">LVĢMC</a>',
    celi: '<a href="https://transportdata.gov.lv" target="_blank" rel="noopener">LVC DATEX II</a>',
  };
  const stavs = (() => { try { return JSON.parse(localStorage.getItem(ATSLEGA)) || {}; } catch { return {}; } })();
  const saglabat = () => { try { localStorage.setItem(ATSLEGA, JSON.stringify(stavs)); } catch { /* privātais režīms */ } };
  const elements = (tag, klase, html = '', atr = {}) => {
    const e = document.createElement(tag);
    if (klase) e.className = klase;
    e.innerHTML = html;
    for (const [k, v] of Object.entries(atr)) e.setAttribute(k, v);
    return e;
  };
  const skelets = n => Array.from({ length: n }, () => '<li class="dv-skelets" aria-hidden="true"><span></span><span></span></li>').join('');

  // ---- Jaunie elementi (izveido vienreiz) ----
  const galva = document.querySelector('header');
  const zime = elements('span', 'dv-zime-logo', IKONAS.vairogs);
  const apaksvirsraksts = elements('span', 'dv-apaksvirsraksts', '<span data-t="Latvija · map.repo.lv">Latvija · map.repo.lv</span>');
  const nav = elements('nav', 'dv-nav', `<button type="button" data-dv="meklesana" aria-pressed="true">${IKONAS.meklet}<span data-t="Meklēšana &amp; Lēmums">Meklēšana &amp; Lēmums</span></button>` +
    `<button type="button" class="slani-akcents" data-dv="slani" aria-pressed="false" aria-expanded="false" aria-controls="dv-atvilktne">${IKONAS.slani}<span data-t="Slāņu vadība">Slāņu vadība</span><span class="slani-skaits" hidden></span></button>`, { 'aria-label': 'Skats', 'data-t-aria': 'Skats' });
  const centrs = elements('div', 'dv-centrs');
  centrs.append(nav);
  const parPoga = elements('button', 'dv-par-poga', '<span data-t="Par datiem &amp; AI">Par datiem &amp; AI</span>', { type: 'button', 'aria-haspopup': 'dialog' });

  const josla112 = elements('div', 'dv-112', `<p class="dv-112-teksts">${IKONAS.info}<span data-t="Ja apdraudēta dzīvība vai veselība, zvaniet 112.">Ja apdraudēta dzīvība vai veselība, zvaniet 112.</span></p>` +
    `<p class="dv-svaigums" role="status"><span class="dv-punkts"></span><span class="dv-svaigums-teksts">${Valoda.t('Ielādē datus…')}</span></p>`,
    { role: 'region', 'aria-label': 'Ārkārtas palīdzība' });

  const ievads = elements('section', 'dv-ievads', '<h2 data-t="Noskaidrojiet situāciju savā adresē">Noskaidrojiet situāciju savā adresē</h2><div class="dv-forma-vieta"></div>' +
    `<button type="button" class="dv-atrast">${IKONAS.vieta}<span data-t="Izmantot manu atrašanās vietu">Izmantot manu atrašanās vietu</span></button>` +
    '<div class="dv-aktivie" role="group" aria-label="Ieslēgtie slāņi" data-t-aria="Ieslēgtie slāņi"></div>');
  // Pirmais skats (meklesana.js): ko rakstīt + 3 piemēri; CSS to paslēpj pēc pirmās meklēšanas (body.ir-meklets)
  const pirmais = elements('div', 'dv-pirmais', krizesMeklesana.pirmaisSkats());
  const valsts = elements('div', 'dv-valsts', '<span class="dv-valsts-nos" data-t="Kopējā situācija valstī:">Kopējā situācija valstī:</span>' +
    '<span class="dv-valsts-pills" aria-live="polite"><span class="dv-pill dv-pill-skelets" aria-hidden="true"></span></span>');

  const atvilktne = elements('div', 'dv-atvilktne', '<div class="dv-atv-galva"><h2 data-t="Slāņu vadība">Slāņu vadība</h2>' +
    '<button type="button" class="dv-aizvert" aria-label="Aizvērt slāņu vadību" data-t-aria="Aizvērt slāņu vadību">✕</button></div><div class="dv-atv-saturs"></div>',
    { id: 'dv-atvilktne', role: 'region', 'aria-label': 'Slāņu vadība', 'data-t-aria': 'Slāņu vadība' });
  atvilktne.hidden = true;

  const bloks = (id, virsraksts, labaPuse, avots) => `<section class="dv-bloks" id="${id}" aria-labelledby="${id}-v"><h3 id="${id}-v"><span data-t="${virsraksts}">${virsraksts}</span>` +
    `<span class="dv-avots">${labaPuse}</span></h3><ul>${skelets(2)}</ul><small class="dv-bloka-avots"><span data-t="Avots:">Avots:</span> ${avots} · CC0</small></section>`;
  const situacija = elements('aside', 'dv-situacija', '<div class="dv-sit-galva"><h2><span class="dv-punkts"></span><span data-t="Situācija tagad (Latvija)">Situācija tagad (Latvija)</span></h2>' +
    '<button type="button" class="dv-aizvert" aria-label="Aizvērt situācijas paneli" data-t-aria="Aizvērt situācijas paneli">✕</button></div>' +
    bloks('dv-bridinajumi', 'Hidrometeo brīdinājumi', 'LVĢMC', AVOTI.bridinajumi) +
    bloks('dv-udens', 'Upju ūdens līmenis (pieaugums)', '', AVOTI.udens) +
    bloks('dv-celi', 'Satiksmes ierobežojumi', 'LVC DATEX II', AVOTI.celi), { id: 'dv-situacija', 'aria-label': 'Situācija tagad (Latvija)', 'data-t-aria': 'Situācija tagad (Latvija)' });

  const aktivie = ievads.querySelector('.dv-aktivie');
  const legenda = elements('details', 'dv-legenda', '<summary><span data-t="Kartes leģenda &amp; simboli">Kartes leģenda &amp; simboli</span><button type="button" class="notirit-visus dv-leg-notirit" data-visi="1" data-t="Notīrīt visus" hidden>Notīrīt visus</button></summary><ul></ul>');
  legenda.open = true;
  const situacijasPoga = elements('button', 'dv-rikis-poga', IKONAS.panelis,
    { type: 'button', title: 'Situācija tagad', 'aria-label': 'Situācija tagad (labais panelis)', 'data-t-title': 'Situācija tagad', 'data-t-aria': 'Situācija tagad (labais panelis)', 'aria-controls': 'dv-situacija', 'aria-pressed': 'true' });
  const pilnaPoga = elements('button', 'dv-rikis-poga', IKONAS.pilns,
    { type: 'button', title: 'Karte pa visu platumu', 'aria-label': 'Karte pa visu platumu', 'data-t-title': 'Karte pa visu platumu', 'data-t-aria': 'Karte pa visu platumu', 'aria-pressed': 'false' });
  const brAizvert = elements('button', 'dv-br-aizvert', '<span data-t="Aizvērt">Aizvērt</span>', { type: 'button', 'aria-label': 'Aizvērt brīdinājumu joslu', 'data-t-aria': 'Aizvērt brīdinājumu joslu' });

  const dialogs = elements('dialog', 'dv-dialogs', `<h2 id="dv-par-v" data-t="Par datiem &amp; AI">Par datiem &amp; AI</h2>
    <p><b data-t="Dati.">Dati.</b> <span data-t="Kartē ir tikai atvērtie dati ar licenci: LVĢMC brīdinājumi, plūdu kartes un upju līmeņi, VZD adreses, IeM IC, ZVA, VM, LVC satiksme un ceļi, OpenStreetMap, pašvaldību civilās aizsardzības plāni. Katrā punktā un kartītes rindā ir avots un licence.">Kartē ir tikai atvērtie dati ar licenci: LVĢMC brīdinājumi, plūdu kartes un upju līmeņi, VZD adreses, IeM IC, ZVA, VM, LVC satiksme un ceļi, OpenStreetMap, pašvaldību civilās aizsardzības plāni. Katrā punktā un kartītes rindā ir avots un licence.</span></p>
    <p><b data-t="AI.">AI.</b> <span data-t="Lietotnē AI nedarbojas, un Jūsu teksts netiek sūtīts uz AI. AI izmantojām iepriekš, bezsaistē: no 42 pašvaldību CA plāniem izvilkām evakuācijas un izmitināšanas vietas ar lappušu atsaucēm (un atradām 41 koordinātu kļūdu oficiālajos plānos), kā arī sagatavojām meklēšanas atslēgvārdus un pārbaudes vaicājumus.">Lietotnē AI nedarbojas, un Jūsu teksts netiek sūtīts uz AI. AI izmantojām iepriekš, bezsaistē: no 42 pašvaldību CA plāniem izvilkām evakuācijas un izmitināšanas vietas ar lappušu atsaucēm (un atradām 41 koordinātu kļūdu oficiālajos plānos), kā arī sagatavojām meklēšanas atslēgvārdus un pārbaudes vaicājumus.</span></p>
    <p class="dv-dialogs-pogas"><button type="button" class="dv-sek-poga" data-dv-par="avoti" data-t="Datu avoti un licences">Datu avoti un licences</button>
      <a class="dv-sek-poga" href="statuss.html" data-t="Vai avoti darbojas?">Vai avoti darbojas?</a>
      <a class="dv-sek-poga" href="trukstosie.html" data-t="Ko vēl vajadzētu publicēt">Ko vēl vajadzētu publicēt</a></p>
    <form method="dialog"><button type="submit" class="dv-galv-poga" data-t="Aizvērt">Aizvērt</button></form>`, { 'aria-labelledby': 'dv-par-v' });
  document.body.append(dialogs);

  // ---- Pārvietošana: plats ekrāns ↔ telefons ----
  const forma = $('meklet-forma');  // galvenē visos režīmos (nav jāpārvieto)
  const soli = document.querySelector('.soli');
  const situacijaPoga = $('situacija-poga');
  const izmainas = $('izmainas-poga');
  const panelis = $('panelis');
  const kartesLaukums = $('kartes-laukums');
  const rikis = kartesLaukums.querySelector('.kartes-rikis');
  const h1 = galva.querySelector('h1');
  let sekcijas = [];
  let ieslegts = false;
  let zinotPoga = null, zinotVieta = null;

  function ieslegt() {
    if (ieslegts) return;
    ieslegts = true;
    document.body.classList.add('dv');
    document.body.classList.remove('panelis-slegts');  // kā datora ielādē (telefonā app.js to pieliek)
    const kreisi = galva.querySelector('.galva-kreisi'), labi = galva.querySelector('.galva-labi');
    kreisi.prepend(zime);
    if (izmainas) kreisi.prepend(izmainas);  // izmaiņu žurnāls [#] pirms zīmes, kā telefonā
    h1.append(apaksvirsraksts);
    galva.insertBefore(centrs, labi);
    zinotPoga = $('zinot-poga');  // "Ziņot par bīstamību" (zinot.js) — galvenē blakus "Slāņu vadība"
    if (zinotPoga) { zinotVieta = [zinotPoga.parentNode, zinotPoga.nextSibling]; centrs.append(zinotPoga); zinotPoga.classList.add('dv-zinot'); zinotPoga.insertAdjacentHTML('afterbegin', IKONAS.zinot); }
    labi.prepend(parPoga);
    galva.after(josla112);
    if (soli) ievads.querySelector('.dv-forma-vieta').append(soli);  // meklēšanas lauks ir galvenē; soļi zem ievada
    ievads.append(valsts, pirmais);
    panelis.prepend(ievads);
    sekcijas = [...panelis.children].filter(e => e.tagName === 'SECTION' && e.id !== 'meklesana' && e !== ievads);
    atvilktne.querySelector('.dv-atv-saturs').append(...sekcijas);
    kartesLaukums.append(atvilktne, legenda);
    rikis?.append(situacijasPoga, pilnaPoga);
    panelis.parentNode.append(situacija);
    raditSituaciju(stavs.situacija ?? false);  // pēc noklusējuma aizvērts; atver poga galvenē
    raditKreiso(stavs.kreisa ?? true);
    brJosla();
    atjaunotLegendu();
    aizvertPrognozi();
    Valoda.lietot();  // jaunie elementi (data-t) → aktīvā valoda
    setTimeout(() => karte.invalidateSize(), 0);
  }

  // prognozes.js datorā pats atver prognožu lenti un tā aizsedz pusi kartes; datorā to aizstāj labā kolonna,
  // tāpēc sākumā lenti aizveram (vienreiz; poga "Prognoze" paliek un atver to kā līdz šim)
  let prognozeAizverta = false;
  function aizvertPrognozi() {
    if (prognozeAizverta) return;
    const p = $('prognozes');
    if (!p) return;
    const aizvert = () => { if (p.classList.contains('atverts')) p.querySelector('.prog-aizvert')?.click(); };
    const n = new MutationObserver(() => { if (p.classList.contains('atverts')) { aizvert(); n.disconnect(); prognozeAizverta = true; } });
    n.observe(p, { attributes: true, attributeFilter: ['class'] });
    aizvert();
    setTimeout(() => { n.disconnect(); prognozeAizverta = true; }, 15000);
  }

  function izslegt() {
    if (!ieslegts) return;
    ieslegts = false;
    document.body.classList.remove('dv', 'dv-kreisa-slegta', 'dv-situacija-slegta');
    raditAtvilktni(false);
    if (soli) $('rezultati').before(soli);
    if (zinotPoga && zinotVieta) { zinotVieta[0].insertBefore(zinotPoga, zinotVieta[1]); zinotPoga.classList.remove('dv-zinot'); zinotPoga.querySelector('.dv-zinot-ikona')?.remove(); }
    if (izmainas) galva.querySelector('.galva-kreisi').prepend(izmainas);
    for (const e of [zime, apaksvirsraksts, centrs, parPoga, josla112, valsts, pirmais, ievads, atvilktne, legenda, situacijasPoga, pilnaPoga, situacija, brAizvert]) e.remove();
    panelis.append(...sekcijas);
    const br = $('bridinajums');
    if (br?.dataset.dvAizverts) { delete br.dataset.dvAizverts; br.hidden = false; }
    // Kā telefona ielādē (app.js): filtru panelis aizvērts — citādi apaksa.js katrā body klases maiņā saplok lapu
    document.body.classList.add('panelis-slegts');
    $('panelis-poga')?.setAttribute('aria-expanded', 'false');
    // sheet.js uz to pašu platuma maiņu reaģēja pirms mums (meklēšanu pārcēla lapā) — mēs to atlikām galvenē; vēlreiz
    if (typeof Lapa !== 'undefined' && Lapa) Lapa.novietot();
    setTimeout(() => karte.invalidateSize(), 0);
  }

  function raditAtvilktni(rad) {
    atvilktne.hidden = !rad;
    const [m, s] = nav.querySelectorAll('button');
    s.setAttribute('aria-expanded', rad);
    s.setAttribute('aria-pressed', rad);
    m.setAttribute('aria-pressed', !rad);
    if (rad) atvilktne.querySelector('.dv-aizvert').focus();
  }

  function raditSituaciju(rad, lietotajs = false) {
    situacija.hidden = !rad;
    document.body.classList.toggle('dv-situacija-slegta', !rad);
    situacijasPoga.setAttribute('aria-pressed', rad);
    if (situacijaPoga && ieslegts) { situacijaPoga.setAttribute('aria-pressed', rad); situacijaPoga.setAttribute('aria-expanded', rad); }
    if (lietotajs) { stavs.situacija = rad; saglabat(); }
    if (rad) ieladetSituaciju();
    atjaunotPilnu();
    setTimeout(() => karte.invalidateSize(), 0);
  }

  function raditKreiso(rad, lietotajs = false) {
    document.body.classList.toggle('dv-kreisa-slegta', !rad);
    if (lietotajs) { stavs.kreisa = rad; saglabat(); }
    atjaunotPilnu();
    setTimeout(() => karte.invalidateSize(), 0);
  }

  const atjaunotPilnu = () => pilnaPoga.setAttribute('aria-pressed', document.body.classList.contains('dv-kreisa-slegta') && situacija.hidden);

  nav.addEventListener('click', e => {
    const b = e.target.closest('[data-dv]');
    if (!b) return;
    if (b.dataset.dv === 'slani') return raditAtvilktni(atvilktne.hidden);
    raditAtvilktni(false);
    raditKreiso(true, true);
    panelis.scrollTop = 0;
    $('jautajums').focus();
  });
  atvilktne.querySelector('.dv-aizvert').addEventListener('click', () => { raditAtvilktni(false); nav.querySelector('[data-dv="slani"]').focus(); });
  situacija.querySelector('.dv-aizvert').addEventListener('click', () => { raditSituaciju(false, true); situacijasPoga.focus(); });
  situacijasPoga.addEventListener('click', () => raditSituaciju(situacija.hidden, true));
  situacijaPoga?.addEventListener('click', () => { if (ieslegts) raditSituaciju(situacija.hidden, true); });
  pilnaPoga.addEventListener('click', () => {
    const pilns = pilnaPoga.getAttribute('aria-pressed') === 'true';
    raditKreiso(pilns, true);
    raditSituaciju(pilns, true);
  });
  parPoga.addEventListener('click', () => dialogs.showModal());
  dialogs.addEventListener('click', e => {
    if (e.target === dialogs) return dialogs.close();  // klikšķis ārpus loga
    if (e.target.closest('[data-dv-par="avoti"]')) {
      dialogs.close();
      raditAtvilktni(true);
      const avoti = $('avoti');
      if (avoti) { avoti.open = true; avoti.scrollIntoView({ block: 'start' }); }
    }
  });
  ievads.querySelector('.dv-atrast').addEventListener('click', () => $('atrast')?.click());
  document.addEventListener('keydown', e => { if (e.key === 'Escape' && ieslegts && !atvilktne.hidden) raditAtvilktni(false); });

  // ---- Brīdinājumu josla (bridinajumi.js): "Aizvērt" līdz brīdim, kad teksts mainās ----
  // joslas teksts bez "Aizvērt" pogas (valodas neatkarīgi: poga tiek tulkota, tāpēc teksts netiek meklēts pēc vārda)
  const brTeksts = br => { const k = br.cloneNode(true); k.querySelector('.dv-br-aizvert')?.remove(); return k.textContent.trim(); };
  function brPoga() {  // poga tiek izveidota/pievienota pēc valodas pielietošanas, tāpēc tulko arī šeit un uz valodas maiņu
    brAizvert.querySelector('span').textContent = Valoda.t('Aizvērt');
    brAizvert.setAttribute('aria-label', Valoda.t('Aizvērt brīdinājumu joslu'));
  }
  function brJosla() {
    const br = $('bridinajums');
    if (!br || !ieslegts) return;
    brPoga();
    const teksts = brTeksts(br);
    if (br.dataset.dvAizverts && br.dataset.dvAizverts !== teksts) delete br.dataset.dvAizverts;
    if (br.dataset.dvAizverts) br.hidden = true;
    if (!br.contains(brAizvert) && br.firstElementChild) br.append(brAizvert);
  }
  brAizvert.addEventListener('click', () => {
    const br = $('bridinajums');
    br.dataset.dvAizverts = brTeksts(br);
    br.hidden = true;
    setTimeout(() => karte.invalidateSize(), 0);
  });
  if ($('bridinajums')) new MutationObserver(() => brJosla()).observe($('bridinajums'), { childList: true });
  document.addEventListener('valoda-maina', () => { if (ieslegts) brPoga(); });

  // ---- Leģenda: ieslēgtie slāņi ar to krāsām (no /api/kategorijas, app.js) ----
  function atjaunotLegendu() {
    const ul = legenda.querySelector('ul');
    const kodi = [...(stavoklis.kategorijas || [])].filter(k => kategorijas[k]);
    const parklajumi = [...document.querySelectorAll('.parklajums input:checked')].map(i => i.closest('label'))
      .map(l => [l.querySelector('.punkts')?.style.background || l.querySelector('svg.forma g')?.getAttribute('fill') || '#999', l.textContent.trim(), l.querySelector('input').id,
        l.querySelector('svg')?.outerHTML || '']);  // pārklājumam: tā pati forma slāņa krāsā / ikona (ikonas.js), nevis pelēks punkts
    const T = k => typeof Valoda !== 'undefined' ? Valoda.t(k) : k;
    // sānjoslas čipi: ieslēgtie slāņi ar × un "Notīrīt visus" (klikšķi: app.js, tas pats apstrādātājs kas leģendai)
    const cx = (atr, t, ik) => `<span class="dv-aktivs">${ik}<span class="dv-leg-nos">${esc(t)}</span><button type="button" class="dv-akt-x" ${atr} aria-label="${esc(Valoda.t('Noņemt slāni'))}: ${esc(t)}">×</button></span>`;
    aktivie.innerHTML = (kodi.length || parklajumi.length)
      ? kodi.map(k => cx(`data-kods="${esc(k)}"`, Valoda.t(kategorijas[k].nosaukums), Ikonas.formaHTML(k))).join('') +
        parklajumi.map(([k, t, id, sv]) => cx(`data-id="${esc(id)}"`, t, sv || `<span class="punkts" style="background:${esc(k)}"></span>`)).join('') +
        `<button type="button" class="dv-akt-visi" data-visi="1">${esc(Valoda.t('Notīrīt visus'))}</button>`
      : `<span class="dv-akt-tukss">${esc(Valoda.t('Nav ieslēgtu slāņu'))}</span>`;
    const x = (atr, t) => `<button type="button" class="dv-leg-x" ${atr} aria-label="${esc(T('Noņemt slāni'))}: ${esc(t)}">×</button>`;
    if (!kodi.length && !parklajumi.length) {
      legenda.querySelector('.dv-leg-notirit').hidden = true;
      ul.innerHTML = `<li class="dv-leg-tukss">${Valoda.t('Neviens slānis nav ieslēgts. Atveriet „Slāņu vadība”.')}</li>`;
      return;
    }
    const pecGrupas = {};
    for (const k of kodi) (pecGrupas[kategorijas[k].grupa] ||= []).push(k);
    // tā pati marķiera forma kā kartē (ikonas.js), nevis tikai krāsa
    ul.innerHTML = Object.entries(pecGrupas).map(([g, kk]) => `<li class="dv-leg-grupa">${esc(Valoda.t(GRUPAS[g] || g))}</li>` +
      kk.map(k => `<li>${Ikonas.formaHTML(k)}<span class="dv-leg-nos">${esc(Valoda.t(kategorijas[k].nosaukums))}</span>${x(`data-kods="${esc(k)}"`, kategorijas[k].nosaukums)}</li>`).join('')).join('') +
      (parklajumi.length ? `<li class="dv-leg-grupa">${Valoda.t('Pārklājumi')}</li>` + parklajumi.map(([k, t, id, sv]) => `<li>${sv || `<span class="punkts" style="background:${esc(k)}"></span>`}<span class="dv-leg-nos">${esc(t)}</span>${x(`data-id="${esc(id)}"`, t)}</li>`).join('') : '');
    legenda.querySelector('.dv-leg-notirit').hidden = false;
  }
  legenda.querySelector('summary').addEventListener('click', e => { if (e.target.closest('.dv-leg-notirit')) e.preventDefault(); });  // nesakļauj leģendu; notīra app.js
  document.addEventListener('click', e => { if (ieslegts && e.target.closest('[data-visi]')) setTimeout(atjaunotLegendu, 300); });  // "Notīrīt visus" (app.js) change nesūta
  document.addEventListener('change', e => { if (ieslegts && e.target.matches('input[type="checkbox"]')) setTimeout(atjaunotLegendu, 0); });
  let legendasTaimeris = null;  // slāņus maina arī meklēšana (meklesana.js) — leģendu atjauno pēc kartes izmaiņām
  karte.on('layeradd layerremove', () => { if (!ieslegts) return; clearTimeout(legendasTaimeris); legendasTaimeris = setTimeout(atjaunotLegendu, 200); });

  // ---- Dati: kopējā situācija valstī + labā kolonna ----
  let ieladets = 0, bridinajumi = [], izcelums = null;
  const lidz = iso => iso ? Valoda.t('līdz {x}', { x: laiks(iso) }) : '';
  const isi = t => { t = String(t || '').replace(/\s+/g, ' ').trim(); return t.length > 80 ? t.slice(0, 78).replace(/\s\S*$/, '') + '…' : t; };
  const iegutJson = c => fetch(c).then(r => r.ok ? r.json() : Promise.reject(r.status));

  let svaigumsOk = false;  // pēdējais svaiguma stāvoklis (valodas maiņai)
  function svaigums(ok) {
    svaigumsOk = ok;
    const t = josla112.querySelector('.dv-svaigums-teksts'), p = josla112.querySelector('.dv-punkts');
    const tiessaiste = ok && navigator.onLine;
    p.classList.toggle('novecojis', !tiessaiste);
    t.textContent = tiessaiste ? Valoda.t('Tiešsaistes dati · atjaunots šodien {x}', { x: stunda(new Date()) }) : Valoda.t('Bezsaistē vai dati nav pieejami · rāda saglabātos');
  }

  function izcelt(slanis) {
    if (izcelums) izcelums.remove();
    izcelums = slanis.addTo(karte);
    setTimeout(() => { if (izcelums === slanis) { slanis.remove(); izcelums = null; } }, 8000);
  }

  let notiek = Promise.resolve();  // pēdējā ielāde: simulētā stāvokļa maiņa gaida to, lai novecojusi atbilde nepārraksta jauno
  async function ieladetSituaciju(spiest = false) {
    if (!spiest && Date.now() - ieladets < 5 * 60000) return;
    ieladets = Date.now();
    notiek = Promise.allSettled([ieladetBridinajumus(), ieladetUdeni(), ieladetCelus()]);
    const rezultati = await notiek;
    svaigums(rezultati.some(r => r.status === 'fulfilled'));
  }

  async function ieladetBridinajumus() {
    const ul = situacija.querySelector('#dv-bridinajumi ul');
    try {
      bridinajumi = ((await iegutJson('/api/bridinajumi?poligoni=1')).bridinajumi || []).slice().sort((x, y) => y.limenis - x.limenis);
    } catch (e) {
      valsts.querySelector('.dv-valsts-pills').innerHTML = '<span class="dv-pill">' + Valoda.t('neizdevās ielādēt') + '</span>';
      ul.innerHTML = '<li class="dv-tukss">' + Valoda.t('Neizdevās ielādēt. Skatiet meteo.lv.') + '</li>';
      throw e;
    }
    const skaits = l => bridinajumi.filter(x => x.limenis === l).length;
    const pills = [[3, 'sarkan'], [2, 'oranž'], [1, 'dzelten']].filter(([l]) => skaits(l))
      .map(([l]) => `<span class="dv-pill ${LIMENI[l][0]}">${Valoda.t(PILLS[l][skaits(l) === 1 ? 0 : 1], { n: skaits(l) })}</span>`);
    valsts.querySelector('.dv-valsts-pills').innerHTML = pills.length ? pills.join('') : '<span class="dv-pill zals">' + Valoda.t('brīdinājumu nav') + '</span>';
    ul.innerHTML = bridinajumi.length ? bridinajumi.map((x, i) =>
      `<li class="dv-karte-rinda ${LIMENI[x.limenis]?.[0] || ''}" tabindex="0" data-bridinajums="${i}">` +
      `<span class="dv-rinda-teksts"><b>${esc(x.paradiba)}</b><small>${esc(x.regioni)} · ${esc(lidz(x.lidz))}</small></span>` +
      `<span class="dv-limenis">${esc(Valoda.t(LIMENI[x.limenis]?.[1] || x.krasa))}</span></li>`).join('')
      : '<li class="dv-tukss">' + Valoda.t('Spēkā esošu brīdinājumu nav.') + '</li>';
  }

  async function ieladetUdeni() {
    const ul = situacija.querySelector('#dv-udens ul');
    let st;
    try {
      st = ((await iegutJson('/api/objekti?kategorijas=udens_limenis&limit=500')).features || [])
        .map(f => ({ ...f.properties.ipasibas, nosaukums: f.properties.nosaukums, lon: f.geometry.coordinates[0], lat: f.geometry.coordinates[1] }))
        .filter(s => s.limenis_cm != null);
    } catch (e) {
      ul.innerHTML = '<li class="dv-tukss">' + Valoda.t('Neizdevās ielādēt.') + '</li>';
      throw e;
    }
    situacija.querySelector('#dv-udens .dv-avots').textContent = Valoda.t('{n} stacijas', { n: st.length });
    const augosas = st.filter(s => s.izmaina_24h_cm > 0).sort((a, b) => b.izmaina_24h_cm - a.izmaina_24h_cm).slice(0, 3);
    const prognozes = await Promise.all(augosas.map(s => iegutJson(`/api/udens?lat=${s.lat}&lon=${s.lon}&limit=1`)
      .then(u => u.stacijas?.[0]?.stacija === s.stacija ? u.stacijas[0].prognoze : null).catch(() => null)));
    ul.innerHTML = augosas.length ? augosas.map((s, i) =>
      `<li class="dv-karte-rinda" tabindex="0" data-lat="${s.lat}" data-lon="${s.lon}">` +
      `<span class="dv-rinda-teksts"><b>${esc(s.nosaukums)}</b><small>${s.limenis_cm} cm · ${laiks(s.laiks)} ` +
      `<span class="dv-pieaug">▲ +${s.izmaina_24h_cm} cm</span></small></span>${sikgrafiks(s, prognozes[i])}</li>`).join('')
      : '<li class="dv-tukss">' + Valoda.t('Pēdējās 24 h neviena stacija nerāda pieaugumu.') + '</li>';
  }

  async function ieladetCelus() {
    const ul = situacija.querySelector('#dv-celi ul');
    let n;
    try {
      n = ((await iegutJson('/api/celi')).notikumi || []).filter(x => x.aktivs !== false)
        .sort((a, b) => String(b.no || '').localeCompare(String(a.no || ''))).slice(0, 3);
    } catch (e) {
      ul.innerHTML = '<li class="dv-tukss">' + Valoda.t('Neizdevās ielādēt.') + '</li>';
      throw e;
    }
    ul.innerHTML = n.length ? n.map(x => {
      const slegts = /slēgt/i.test(x.apraksts || '');
      return `<li class="dv-karte-rinda" tabindex="0" data-lat="${x.lat}" data-lon="${x.lon}" data-linija="${esc(JSON.stringify(x.linija || []))}">` +
        `<span class="dv-rinda-teksts"><b>${x.cels ? `<span class="dv-cels">${esc(x.cels)}</span>` : ''}${esc(x.nosaukums)}</b>` +
        `<small class="${slegts ? 'dv-slegts' : ''}">${esc(isi(x.apraksts))}</small><small>${esc(lidz(x.lidz))}</small></span></li>`;
    }).join('') : '<li class="dv-tukss">' + Valoda.t('Spēkā esošu ierobežojumu nav.') + '</li>';
  }

  // 3 punkti: līmenis pirms 24 h, tagad, 7 dienu prognozes mediāna (raustīta), ja ir
  function sikgrafiks(s, prog) {
    const v = [s.limenis_cm - s.izmaina_24h_cm, s.limenis_cm, ...(prog?.mediana_cm != null ? [prog.mediana_cm] : [])];
    const min = Math.min(...v), max = Math.max(...v), h = 24, w = 56;
    const y = x => max === min ? h / 2 : h - 4 - (x - min) / (max - min) * (h - 8);
    const x = i => 4 + i * (w - 8) / 2;
    const nak = v.length > 2 ? `<path d="M${x(1)},${y(v[1])} L${x(2)},${y(v[2])}" stroke-dasharray="3 2"/>` : '';
    return `<svg class="dv-sikgrafiks" viewBox="0 0 ${w} ${h}" width="${w}" height="${h}" role="img" ` +
      `aria-label="${Valoda.t('Pirms 24 h {a} cm, tagad {b} cm', { a: v[0], b: v[1] })}${v.length > 2 ? ', ' + Valoda.t('prognoze pēc 7 dienām {c} cm', { c: v[2] }) : ''}">` +
      `<path d="M${x(0)},${y(v[0])} L${x(1)},${y(v[1])}"/>${nak}<circle cx="${x(1)}" cy="${y(v[1])}" r="2.4"/></svg>`;
  }

  situacija.addEventListener('click', e => {
    const li = e.target.closest('li[tabindex]');
    if (!li || e.target.closest('a')) return;
    raditAtvilktni(false);
    karte.closePopup();  // atvērts punkta logs citādi paliek piesiets punktam ārpus jaunā skata, kartes malā zem rīkiem
    if (li.dataset.bridinajums != null) {
      const p = (bridinajumi[+li.dataset.bridinajums]?.poligoni || []).filter(x => x.length > 2);
      if (!p.length) return karte.fitBounds(latvija);
      const sl = L.featureGroup(p.map(x => L.polygon(x, { color: '#D66D25', weight: 2, fill: false, dashArray: '6 4', interactive: false })));
      izcelt(sl);
      return karte.fitBounds(sl.getBounds(), { padding: [20, 20] });
    }
    const linija = JSON.parse(li.dataset.linija || '[]');
    if (linija.length > 1) {
      const sl = L.polyline(linija, { color: '#BA2525', weight: 6, opacity: .8, interactive: false });
      izcelt(sl);
      return karte.fitBounds(sl.getBounds(), { padding: [40, 40], maxZoom: 14 });
    }
    izcelt(L.circleMarker([+li.dataset.lat, +li.dataset.lon], { radius: 14, color: '#1E66D5', weight: 3, fill: false, interactive: false }));
    karte.flyTo([+li.dataset.lat, +li.dataset.lon], 12);
  });
  situacija.addEventListener('keydown', e => {
    if ((e.key === 'Enter' || e.key === ' ') && e.target.matches('li[tabindex]')) { e.preventDefault(); e.target.click(); }
  });
  document.addEventListener('sim-maina', () => { if (ieslegts) notiek.then(() => ieladetSituaciju(true)); });  // demo.js: simulētais stāvoklis
  addEventListener('online', () => ieslegts && ieladetSituaciju(true));
  addEventListener('offline', () => ieslegts && svaigums(false));

  const sakt = () => { if (plats.matches) { ieslegt(); ieladetSituaciju(); } };
  plats.addEventListener('change', () => { if (plats.matches) sakt(); else izslegt(); });
  sakt();
  setInterval(() => { if (ieslegts) ieladetSituaciju(true); }, 10 * 60000);

  // valodas maiņa: rāmis (data-t), leģenda, situācijas saraksti un svaiguma teksts jaunajā valodā
  document.addEventListener('valoda-maina', () => {
    if (!ieslegts) return;
    Valoda.lietot();
    atjaunotLegendu();
    svaigums(svaigumsOk);
    ieladetSituaciju(true);
  });

  return { ieslegt, izslegt, raditAtvilktni };
})();
