// "Mana adrese krīzē": 4 soļi — vieta → kas notiek → Jūsu situācija → kopsavilkums ar rezultātu (no atvērtajiem datiem).
// Hash maršruti #/1…#/4, #/karte = karte (app.js). Neatkarīgs no app.js: strādā arī, ja karte (Leaflet) neielādējas;
// karti lieto caur window.PlusmasKarte, ja tā ir. Brīdinājumu josla (LVĢMC) visas lietotnes augšā — arī šeit.
const Plusma = (() => {
  const API = '/api';
  const KRATUVE = 'mana-adrese-krize';      // localStorage: pēdējā kopsavilkuma karte (strādā arī bez interneta)
  const VIETAS = [                           // kopsavilkuma vietas: kategorija → ko darīt, ja tukša
    { kods: 'evakuacijas_punkts', nos: 'Pulcēšanās vieta evakuācijai', ikona: '🚩', aizstat: 'patvertne' },
    { kods: 'izmitinasana', nos: 'Izmitināšanas vieta', ikona: '🏠', aizstat: 'patvertne' },
    { kods: 'patvertne', nos: 'Tuvākā patvertne', ikona: '🛡️' },
    { kods: 'neatliekama_24h', nos: 'Slimnīca ar 24/7 neatliekamo palīdzību', ikona: '🏥' },
    { kods: 'aptieka', nos: 'Aptieka', ikona: '💊' },
  ];
  const AVOTI_TEKSTS = {
    vzd: ['Valsts adrešu reģistrs (VZD)', 'https://data.gov.lv/dati/lv/dataset/varis-atvertie-dati', 'CC BY 4.0'],
    brid: ['LVĢMC hidrometeoroloģiskie brīdinājumi', 'https://data.gov.lv/dati/lv/dataset/hidrometeorologiskie-bridinajumi', 'CC0'],
    pludi: ['LVĢMC plūdu riska kartes 2026–2031', 'https://data.gov.lv/dati/lv/dataset/3-cikla-latvijas-pldu-postjumu-vietu-un-pldu-riska-kartes1', 'CC0'],
    udens: ['LVĢMC hidroloģiskie novērojumi', 'https://data.gov.lv/dati/lv/dataset/hidrometeorologiskie-noverojumi', 'CC0'],
  };
  const LIMENIS_KRASA = { 1: 'dzeltens', 2: 'oranzs', 3: 'sarkans' };
  const LIMENIS_NOS = { 1: 'Dzeltenais', 2: 'Oranžais', 3: 'Sarkanais' };

  const $ = id => document.getElementById(id);
  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const km = m => m == null ? '' : m < 1000 ? m + ' m' : (m / 1000).toFixed(m < 10000 ? 1 : 0).replace('.', ',') + ' km';
  const kajam = m => m == null ? '' : `~${Math.max(1, Math.round(m * 1.3 / 80))} min kājām`;  // 1,3 — ceļš nav taisna līnija
  const isaAdrese = a => a.split(', ').slice(0, 2).join(', ');
  const laiks = iso => new Date(iso).toLocaleString('lv-LV', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' });

  async function iegut(cels, signal) {
    const r = await fetch(API + cels, { signal });
    if (!r.ok) throw Object.assign(new Error('HTTP ' + r.status), { statuss: r.status });
    return r.json();
  }

  const st = { vieta: null, situacija: null, scenarijs: null, teksts: '', apstakli: new Set() };
  let konf = null, noteikumi = null, klasifikators = null, regioni = [], avoti = {};
  let gatavs = null;           // Promise: konfigurācija ielādēta
  let rezultats = null;        // pēdējais kopsavilkums (kartei)

  // ---------- Ielāde ----------
  function ieladet() {
    const json = u => fetch(u).then(r => { if (!r.ok) throw new Error(r.status); return r.json(); });
    gatavs = Promise.all([
      json('plusma.json'),
      json('scenariji.json').catch(() => null),
      iegut('/regioni').catch(() => []),
      iegut('/avoti').catch(() => []),
    ]).then(([k, n, r, a]) => {
      konf = k; noteikumi = n; regioni = r;
      avoti = Object.fromEntries(a.map(x => [x.kods, x]));
      if (n && typeof Klasifikators !== 'undefined') klasifikators = Klasifikators.izveidot(n, r);
    });
    return gatavs;
  }

  // ---------- 112: dzīvības draudi jebkurā teksta laukā ----------
  function parbauditDraudus(teksts) {
    const draudi = !!(klasifikators && teksts && klasifikators.klasificet(teksts).dzivibas_draudi);
    $('zvanit-josla').hidden = !draudi;
    return draudi;
  }

  // ---------- Brīdinājumu josla (LVĢMC) ----------
  let bridPieprasijums = null;
  async function bridinajumi(vieta) {
    const josla = $('bridinajums');
    if (bridPieprasijums) bridPieprasijums.abort();
    bridPieprasijums = new AbortController();
    const q = vieta ? '?' + new URLSearchParams({ lat: vieta.lat.toFixed(5), lon: vieta.lon.toFixed(5) }) : '';
    try {
      const d = await iegut('/bridinajumi' + q, bridPieprasijums.signal);
      const visi = d.bridinajumi;
      const sheit = vieta ? visi.filter(b => b.attiecas) : visi;
      st.bridinajumi = { sheit, citur: visi.length - sheit.length, vieta: !!vieta };
      const max = Math.max(0, ...sheit.map(b => b.limenis));
      josla.className = 'bridinajums ' + (max ? LIMENIS_KRASA[max] : 'zals');
      if (!sheit.length) {
        josla.innerHTML = `<span>✓ ${vieta ? 'Jūsu vietā' : 'Šobrīd'} LVĢMC brīdinājumu nav` +
          (vieta && st.bridinajumi.citur ? ` <small>(citur Latvijā: ${st.bridinajumi.citur})</small>` : '') + '</span>';
      } else {
        josla.innerHTML = `<details><summary>⚠ ${sheit.map(b => `${LIMENIS_NOS[b.limenis] || esc(b.krasa)} brīdinājums: ${esc(b.paradiba.toLowerCase())}` +
          (b.regioni && !vieta ? ` (${esc(b.regioni)})` : '') + (b.lidz ? `, līdz ${laiks(b.lidz)}` : '')).join(' · ')}</summary>` +
          sheit.map(b => `<p>${esc(b.teksts)}</p><p class="riski">${esc(b.riski).replace(/\n/g, '<br>')}</p>`).join('') +
          `<p class="avots-rinda">Avots: ${avotaSaite('brid')}</p></details>`;
      }
      josla.hidden = false;
    } catch (e) {
      if (e.name === 'AbortError') return;
      st.bridinajumi = null;
      josla.hidden = true;  // galapunkts vēl nav pieejams — joslu nerādām
    }
    if (location.hash === '#/4' && rezultats) atjaunotBridRindu();
  }

  const avotaSaite = k => { const [n, u, l] = AVOTI_TEKSTS[k]; return `<a href="${u}" target="_blank" rel="noopener">${esc(n)}</a> · ${l}`; };
  function objektaAvots(kods) {
    const a = avoti[kods];
    if (!a) return '';
    const n = a.datu_kopa_url ? `<a href="${esc(a.datu_kopa_url)}" target="_blank" rel="noopener">${esc(a.nosaukums)}</a>` : esc(a.nosaukums);
    return `${n} (${esc(a.izdevejs)}) · ${esc(a.licence)}`;
  }

  // ---------- Maršrutēšana ----------
  function solis() {
    const m = location.hash.match(/^#\/(\d|karte)$/);
    return m ? m[1] : '1';
  }

  function radit() {
    const s = solis();
    document.body.classList.toggle('rezims-karte', s === 'karte');
    document.body.classList.toggle('rezims-plusma', s !== 'karte');
    $('rezims-poga').textContent = s === 'karte' ? '← Mana adrese krīzē' : '🗺 Karte';
    window.PlusmasKarte?.paradita();  // kartes izmērs mainās līdz ar režīmu
    if (s === 'karte') return;
    // soli pēc kārtas: bez vietas nevar būt 2.–4. solis, bez situācijas — 3.–4.
    let n = +s;
    if (n > 1 && !st.vieta) n = 1;
    if (n > 2 && !st.situacija) n = 2;
    if (String(n) !== s) { location.replace('#/' + n); return; }
    $('solis-nr').textContent = `Solis ${n} no 4`;
    document.querySelectorAll('.soli li').forEach((li, i) => {
      li.className = i + 1 < n ? 'izdarits' : i + 1 === n ? 'tagad' : '';
      if (i + 1 === n) li.setAttribute('aria-current', 'step'); else li.removeAttribute('aria-current');
    });
    [null, solis1, solis2, solis3, solis4][n]();
    $('plusma').scrollTop = 0;
    window.scrollTo(0, 0);
    const h = $('solis').querySelector('h2');
    if (h && document.activeElement !== document.body) h.focus({ preventScroll: true });
  }

  const uz = n => { location.hash = '#/' + n; };
  const navigacija = (atpakal, uzPriekšu = '') =>
    `<div class="navigacija">${atpakal ? `<button type="button" class="otra" data-uz="${atpakal}">← Atpakaļ</button>` : '<span></span>'}${uzPriekšu}</div>`;

  // ---------- 1. Kur Jūs atrodaties? ----------
  function solis1() {
    const saglabats = saglabataKarte();
    $('solis').innerHTML = `
      <h2 tabindex="-1">Kur Jūs atrodaties?</h2>
      <p class="ievads">Pēc vietas atradīsim tuvākās drošās vietas, brīdinājumus un plūdu risku. Neko nesūtām un nesaglabājam serverī.</p>
      ${st.vieta ? `<p class="izveleta">✔ <b>${esc(st.vieta.nosaukums)}</b></p>` : ''}
      <button type="button" class="galvena liela" id="gps">📍 Izmantot manu atrašanās vietu</button>
      <p id="gps-zina" class="piezime" role="status"></p>
      <p class="vai"><span>vai</span></p>
      <label class="lauks" for="adrese">Adrese</label>
      <div class="meklesana">
        <input id="adrese" type="search" autocomplete="off" enterkeyhint="search" maxlength="120"
               placeholder="Piem.: Brīvības iela 15, Ogre" aria-describedby="adrese-zina"
               role="combobox" aria-expanded="false" aria-controls="adreses-saraksts" aria-autocomplete="list">
        <ul id="adreses-saraksts" role="listbox" hidden></ul>
      </div>
      <p id="adrese-zina" class="piezime">Sāciet rakstīt adresi: ielu, mājas numuru un pilsētu.</p>
      <details id="regions-izvele">
        <summary>Nezināt adresi? Izvēlieties pilsētu vai novadu</summary>
        <select id="regions-sel" aria-label="Pilsēta vai novads"><option value="">Izvēlieties…</option></select>
      </details>
      ${saglabats ? `<button type="button" class="otra" id="saglabata">📄 Jūsu saglabātā karte (${esc(laiks(saglabats.laiks))})</button>` : ''}
      ${navigacija(null, `<button type="button" class="galvena" id="turpinat1">Turpināt →</button>`)}`;

    $('gps').addEventListener('click', noteiktVietu);
    $('turpinat1').addEventListener('click', () => {
      if (st.vieta) return uz(2);
      $('adrese-zina').innerHTML = '<span class="kluda">Norādiet adresi, izvēlieties pilsētu vai izmantojiet atrašanās vietu.</span>';
      $('adrese').focus();
    });
    $('saglabata')?.addEventListener('click', () => radtSaglabato());
    adresuMeklesana();
    const sel = $('regions-sel');
    const grupas = [['valstspilseta', 'Valstspilsētas'], ['pilseta', 'Pilsētas'], ['novads', 'Novadi']];
    for (const [tips, nos] of grupas) {
      const og = document.createElement('optgroup');
      og.label = nos;
      for (const r of regioni.filter(r => r.tips === tips).sort((a, b) => a.nosaukums.localeCompare(b.nosaukums, 'lv'))) {
        og.append(new Option(r.nosaukums, r.kods));
      }
      if (og.children.length) sel.append(og);
    }
    if (!regioni.length) $('regions-izvele').hidden = true;
    sel.addEventListener('change', () => {
      const r = regioni.find(r => r.kods === sel.value);
      if (r) izveletiesVietu(regionaVieta(r));
    });
  }

  const regionaVieta = r => ({
    lat: (r.bbox[1] + r.bbox[3]) / 2, lon: (r.bbox[0] + r.bbox[2]) / 2,
    nosaukums: `${r.nosaukums} (${r.tips === 'novads' ? 'novada' : 'pilsētas'} vidus, aptuveni)`, avots: 'regions',
  });

  function noteiktVietu() {
    const zina = $('gps-zina');
    const uzAdresi = teksts => { zina.innerHTML = `<span class="kluda">${teksts}</span>`; $('adrese').focus(); };
    if (!('geolocation' in navigator)) return uzAdresi('Šī pārlūkprogramma nevar noteikt atrašanās vietu. Ierakstiet adresi zemāk.');
    $('gps').disabled = true;
    zina.textContent = 'Nosaka atrašanās vietu…';
    navigator.geolocation.getCurrentPosition(poz => {
      $('gps').disabled = false;
      const { latitude: lat, longitude: lon, accuracy } = poz.coords;
      if (lat < 55.6 || lat > 58.1 || lon < 20.9 || lon > 28.3) {
        return uzAdresi('Jūs atrodaties ārpus Latvijas. Ierakstiet adresi Latvijā zemāk.');
      }
      izveletiesVietu({ lat, lon, nosaukums: `Jūsu atrašanās vieta (±${Math.round(accuracy)} m)`, avots: 'gps' });
    }, kluda => {
      $('gps').disabled = false;
      uzAdresi(kluda.code === kluda.PERMISSION_DENIED
        ? 'Atrašanās vieta nav atļauta. Ierakstiet adresi zemāk (vai atļaujiet to pārlūka iestatījumos).'
        : 'Neizdevās noteikt atrašanās vietu. Ierakstiet adresi zemāk.');
    }, { enableHighAccuracy: true, timeout: 15000, maximumAge: 60000 });
  }

  function adresuMeklesana() {
    const ievade = $('adrese'), ul = $('adreses-saraksts'), zina = $('adrese-zina');
    let taimeris = null, pieprasijums = null, atrastas = [];
    const aizvert = () => { ul.hidden = true; ievade.setAttribute('aria-expanded', 'false'); };
    const izveleties = a => { aizvert(); ievade.value = isaAdrese(a.adrese); izveletiesVietu({ lat: a.lat, lon: a.lon, nosaukums: isaAdrese(a.adrese), pilna: a.adrese, avots: 'vzd' }); };
    // Ja adrešu meklēšana nav pieejama vai neko neatrod — vietvārds tekstā ("Ogre") → pilsētas vidus
    const pecVietvarda = () => klasifikators?.klasificet(ievade.value).vieta;

    ievade.addEventListener('focus', () => { if (matchMedia('(max-width: 800px)').matches) setTimeout(() => ievade.scrollIntoView({ block: 'start', behavior: 'smooth' }), 300); });
    ievade.addEventListener('input', () => {
      clearTimeout(taimeris);
      if (pieprasijums) pieprasijums.abort();
      parbauditDraudus(ievade.value);
      const q = ievade.value.trim();
      if (q.replace(/\s/g, '').length < 3) { aizvert(); return; }
      taimeris = setTimeout(async () => {
        pieprasijums = new AbortController();
        try {
          atrastas = await iegut('/adreses?' + new URLSearchParams({ q, limit: 6 }), pieprasijums.signal);
          ul.innerHTML = atrastas.map((a, i) => `<li role="option" tabindex="-1" data-i="${i}"><b>${esc(isaAdrese(a.adrese))}</b><small>${esc(a.adrese.split(', ').slice(2).join(', '))}</small></li>`).join('');
          const r = pecVietvarda();
          if (!atrastas.length) ul.innerHTML = `<li class="piezime">Adrese nav atrasta.${r ? '' : ' Pārbaudiet rakstību vai izvēlieties pilsētu zemāk.'}</li>`;
          if (r) ul.insertAdjacentHTML('beforeend', `<li role="option" tabindex="-1" data-regions="${esc(r.kods)}"><b>${esc(r.nosaukums)}</b><small>visa ${r.tips === 'novads' ? 'novada' : 'pilsētas'} vidus</small></li>`);
          ul.hidden = false;
          ievade.setAttribute('aria-expanded', 'true');
          zina.textContent = 'Adreses no Valsts adrešu reģistra (VZD).';
        } catch (e) {
          if (e.name === 'AbortError') return;
          // /api/adreses vēl nav (404) vai serveris nepieejams — nekad neapstājamies: pilsēta vai atrašanās vieta
          const r = pecVietvarda();
          ul.innerHTML = r ? `<li role="option" tabindex="-1" data-regions="${esc(r.kods)}"><b>${esc(r.nosaukums)}</b><small>pilsētas vai novada vidus</small></li>` : '';
          ul.hidden = !r;
          zina.innerHTML = '<span class="kluda">Adrešu meklēšana pašlaik nav pieejama.</span> Ierakstiet pilsētu vai izvēlieties to zemāk, vai izmantojiet atrašanās vietu.';
          $('regions-izvele').open = true;
        }
      }, 250);
    });
    ul.addEventListener('click', e => {
      const li = e.target.closest('li[role=option]');
      if (!li) return;
      if (li.dataset.regions) { aizvert(); izveletiesVietu(regionaVieta(regioni.find(r => r.kods === li.dataset.regions))); }
      else izveleties(atrastas[+li.dataset.i]);
    });
    ul.addEventListener('keydown', e => {
      const li = e.target.closest('li');
      if (e.key === 'Enter' && li) li.click();
      if (e.key === 'ArrowDown') li?.nextElementSibling?.focus();
      if (e.key === 'ArrowUp') (li?.previousElementSibling || ievade).focus();
      if (e.key === 'Escape') { aizvert(); ievade.focus(); }
    });
    ievade.addEventListener('keydown', e => {
      if (e.key === 'ArrowDown') { ul.querySelector('li[role=option]')?.focus(); e.preventDefault(); }
      if (e.key === 'Escape') aizvert();
      if (e.key === 'Enter') { e.preventDefault(); ul.querySelector('li[role=option]')?.click(); }
    });
  }

  function izveletiesVietu(v) {
    st.vieta = v;
    rezultats = null;
    window.PlusmasKarte?.vieta(v);
    bridinajumi(v);
    uz(2);
  }

  // ---------- 2. Kas notiek? ----------
  function solis2() {
    const pogas = [...konf.situacijas, konf.cits].map(s => `
      <button type="button" class="situacija${st.situacija?.kods === s.kods ? ' izveleta-poga' : ''}" data-s="${s.kods}">
        <span class="ikona" aria-hidden="true">${s.ikona}</span><b>${esc(s.nosaukums)}</b><small>${esc(s.apraksts)}</small></button>`).join('');
    $('solis').innerHTML = `
      <h2 tabindex="-1">Kas notiek?</h2>
      <p class="ievads">Vieta: <b>${esc(st.vieta.nosaukums)}</b> <button type="button" class="saite" data-uz="1">Mainīt</button></p>
      <div class="situacijas">${pogas}</div>
      <div id="cits" ${st.situacija?.kods === 'cits' ? '' : 'hidden'}>
        <label class="lauks" for="cits-teksts">Aprakstiet, kas notiek</label>
        <textarea id="cits-teksts" rows="3" maxlength="300" placeholder="Piem.: nav elektrības jau divas dienas">${esc(st.teksts)}</textarea>
        <div id="sapratu" aria-live="polite"></div>
      </div>
      ${navigacija(1, `<button type="button" class="galvena" id="turpinat2" ${st.situacija?.kods === 'cits' ? '' : 'hidden'}>Turpināt →</button>`)}`;

    $('solis').querySelectorAll('[data-s]').forEach(b => b.addEventListener('click', () => {
      if (b.dataset.s === 'cits') {
        st.situacija = konf.cits;
        $('cits').hidden = false;
        $('turpinat2').hidden = false;
        $('solis').querySelectorAll('[data-s]').forEach(x => x.classList.toggle('izveleta-poga', x === b));
        $('cits-teksts').focus();
        return;
      }
      st.situacija = konf.situacijas.find(s => s.kods === b.dataset.s);
      st.scenarijs = noteikumi?.scenariji.find(s => s.kods === st.situacija.scenarijs) || null;
      st.teksts = '';
      uz(3);
    }));
    const teksts = $('cits-teksts');
    teksts.addEventListener('input', () => { st.teksts = teksts.value; saprast(); });
    $('turpinat2').addEventListener('click', () => {
      if (!st.teksts.trim()) {
        $('sapratu').innerHTML = '<p class="kluda">Aprakstiet situāciju dažos vārdos vai izvēlieties kādu no pogām augstāk.</p>';
        teksts.focus();
        return;
      }
      uz(3);
    });
    $('sapratu').addEventListener('click', e => {
      const kods = e.target.closest('[data-scen]')?.dataset.scen;
      if (kods) { st.scenarijs = noteikumi.scenariji.find(s => s.kods === kods); saprast(kods); }
      const r = e.target.closest('[data-vieta]')?.dataset.vieta;
      if (r) { st.vieta = regionaVieta(regioni.find(x => x.kods === r)); window.PlusmasKarte?.vieta(st.vieta); bridinajumi(st.vieta); solis2(); saprast(); }
    });
    if (st.situacija?.kods === 'cits') saprast(st.scenarijs?.kods);
  }

  // "Cits": brīvs teksts → scenārijs (klasifikators.js, bez AI, pārlūkā) + 112 + vietvārds
  function saprast(izvelets) {
    const kaste = $('sapratu');
    const teksts = st.teksts.trim();
    parbauditDraudus(teksts);
    if (!teksts || !klasifikators) { kaste.innerHTML = ''; if (!izvelets) st.scenarijs = null; return; }
    const rez = klasifikators.klasificet(teksts);
    const scen = rez.scenariji;
    if (!izvelets) st.scenarijs = scen[0] || null;
    let h = '';
    if (st.scenarijs) {
      h += `<p class="sapratu">Sapratām: <b>${esc(st.scenarijs.nosaukums)}</b></p>`;
      const citi = scen.filter(s => s !== st.scenarijs);
      if (citi.length) h += '<p class="piezime">Vai domājāt:</p><div class="atras-pogas">' +
        citi.map(s => `<button type="button" data-scen="${esc(s.kods)}">${esc(s.nosaukums)}</button>`).join('') + '</div>';
    } else {
      h += '<p class="piezime">Nesapratām precīzi. Varat turpināt: parādīsim vispārīgu padomu un tuvākās drošās vietas.</p>';
    }
    if (rez.vieta && !st.vieta.nosaukums.startsWith(rez.vieta.nosaukums)) {
      h += `<p class="piezime">Tekstā minēta vieta: <b>${esc(rez.vieta.nosaukums)}</b>.
        <button type="button" class="saite" data-vieta="${esc(rez.vieta.kods)}">Rādīt rezultātu ${esc(rez.vieta.nosaukums)}</button></p>`;
    }
    kaste.innerHTML = h;
  }

  // ---------- 3. Jūsu situācija ----------
  function solis3() {
    $('solis').innerHTML = `
      <h2 tabindex="-1">Jūsu situācija</h2>
      <p class="ievads">Tikai tas, ko reģistri par Jums nezina. Nav obligāti: atzīmējiet, kas attiecas, vai izlaidiet.</p>
      <fieldset class="apstakli"><legend class="sr">Kas attiecas uz Jums?</legend>
        ${konf.apstakli.map(a => `<label class="apstaklis"><input type="checkbox" value="${a.kods}" ${st.apstakli.has(a.kods) ? 'checked' : ''}>
          <span class="ikona" aria-hidden="true">${a.ikona}</span><span>${esc(a.nosaukums)}</span></label>`).join('')}
      </fieldset>
      <p class="piezime">Atbildes paliek tikai Jūsu tālrunī.</p>
      ${navigacija(2, `<span class="pogas-labi"><button type="button" class="otra" id="izlaist">Izlaist</button><button type="button" class="galvena" id="turpinat3">Rādīt rezultātu →</button></span>`)}`;
    $('solis').querySelectorAll('.apstakli input').forEach(i => i.addEventListener('change', () => {
      if (i.checked) st.apstakli.add(i.value); else st.apstakli.delete(i.value);
    }));
    $('turpinat3').addEventListener('click', () => uz(4));
    $('izlaist').addEventListener('click', () => { st.apstakli.clear(); uz(4); });
  }

  // ---------- 4. Kopsavilkums ----------
  let rezPieprasijums = null;
  function solis4() {
    const sit = st.situacija;
    const scen = st.scenarijs;
    const draudi = parbauditDraudus(st.teksts);
    const zvanit112 = `<a class="zvanit112" href="tel:112">📞 Zvanīt 112</a><p class="piezime">Ja apdraudēta dzīvība vai veselība, zvaniet tūlīt. Dispečers palīdzēs.</p>`;
    const apst = konf.apstakli.filter(a => st.apstakli.has(a.kods));
    $('solis').innerHTML = `
      <div id="kopsavilkums">
      <h2 tabindex="-1">Kopsavilkums</h2>
      <dl class="noradijat">
        <div><dt>Vieta</dt><dd>${esc(st.vieta.nosaukums)} <button type="button" class="saite" data-uz="1">Labot</button></dd></div>
        <div><dt>Situācija</dt><dd>${esc(sit.kods === 'cits' ? (scen?.nosaukums || 'Cits') + (st.teksts ? ` („${st.teksts.trim()}”)` : '') : sit.nosaukums)} <button type="button" class="saite" data-uz="2">Labot</button></dd></div>
        <div><dt>Apstākļi</dt><dd>${apst.length ? apst.map(a => esc(a.nosaukums)).join('; ') : 'nav norādīti'} <button type="button" class="saite" data-uz="3">Labot</button></dd></div>
      </dl>
      ${draudi ? zvanit112 : ''}
      <div id="lemums" class="lemums oranzs" aria-live="polite"><b>Pārbauda Jūsu adresi…</b></div>
      ${!draudi && scen?.zvanit112 ? zvanit112 : ''}
      <h3>Jūsu vietā</h3>
      <ul class="fakti">
        <li id="r-brid"><span class="ikona">⚠️</span><div><b>Brīdinājumi</b><span>Pārbauda…</span></div></li>
        <li id="r-pludi"><span class="ikona">🌊</span><div><b>Plūdu riska zona</b><span>Pārbauda… (var aizņemt līdz 15 s)</span></div></li>
        <li id="r-udens"><span class="ikona">📏</span><div><b>Tuvākā upe vai ezers</b><span>Pārbauda…</span></div></li>
      </ul>
      <h3>Tuvākās vietas</h3>
      <ul class="vietas">${VIETAS.map(v => `<li id="r-${v.kods}"><span class="ikona">${v.ikona}</span><div><b>${esc(v.nos)}</b><span>Meklē…</span></div></li>`).join('')}</ul>
      <h3>Ko darīt</h3>
      <ul class="padomi">${padomi().map(p => `<li>${esc(p)}</li>`).join('')}</ul>
      <h3>Kas notiks tālāk</h3>
      <ol class="talak" id="talak"></ol>
      <p class="piezime prototips">Prototips: dati no atvērtajiem avotiem var būt nepilnīgi vai novecojuši. Oficiālie rīkojumi: LR1, LTV1, <a href="https://www.112.lv" target="_blank" rel="noopener">112.lv</a>. Sagatavots ${esc(laiks(new Date()))}.</p>
      </div>
      <div class="darbibas">
        <button type="button" class="galvena" id="drukat">🖨 Saglabāt / drukāt karti</button>
        ${window.PlusmasKarte ? '<button type="button" class="otra" id="skatit-karte">🗺 Skatīt kartē</button>' : ''}
        <button type="button" class="otra" id="no-jauna">↺ Sākt no jauna</button>
        <a class="atsauksme" href="https://github.com/noiseparty/hakatons/issues/new?title=${encodeURIComponent('Atsauksme: Mana adrese krīzē')}" target="_blank" rel="noopener">Atsauksme par šo rīku</a>
      </div>
      ${navigacija(3).replace('class="navigacija"', 'class="navigacija beigas"')}`;
    $('drukat').addEventListener('click', () => { saglabat(); window.print(); });
    $('skatit-karte')?.addEventListener('click', () => { window.PlusmasKarte?.radit(rezultats); uz('karte'); });
    $('no-jauna').addEventListener('click', () => {
      Object.assign(st, { vieta: null, situacija: null, scenarijs: null, teksts: '' });
      st.apstakli.clear();
      rezultats = null;
      $('zvanit-josla').hidden = true;
      bridinajumi(null);
      uz(1);
    });
    aprekinat();
  }

  function padomi() {
    const sit = st.situacija;
    const p = sit.padomi ? [...sit.padomi] : st.scenarijs?.padoms ? [st.scenarijs.padoms] :
      ['Ja kāds ir apdraudēts, zvaniet 112. Sekojiet LR1, LTV1 un 112.lv. Ziniet, kur ir tuvākā patvertne un slimnīca.'];
    for (const a of konf.apstakli) if (st.apstakli.has(a.kods)) p.push(a.padoms);
    return p;
  }

  // Visi avoti paralēli; katra rinda aizpildās, tiklīdz ir dati. Tukša kategorija → aizstājēja (nekad tukša rinda).
  async function aprekinat() {
    if (rezPieprasijums) rezPieprasijums.abort();
    rezPieprasijums = new AbortController();
    const signal = rezPieprasijums.signal;
    const { lat, lon } = st.vieta;
    const ll = { lat: lat.toFixed(5), lon: lon.toFixed(5) };
    rezultats = { vieta: st.vieta, vietas: {}, pludi: null, situacija: st.situacija.kods };
    // Specializētās slimnīcas (dzemdību nams, psihiatrija; ipasibas.specializeta) — tikai, ja tuvumā nav vispārējas
    const tuvakais = kat => iegut('/objekti?' + new URLSearchParams({ kategorijas: kat, ...ll, limit: 5 }), signal)
      .then(g => g.features.find(f => !f.properties.ipasibas?.specializeta) || g.features[0] || null);

    const vietas = VIETAS.map(async v => {
      let f = null, aizstats = false;
      try { f = await tuvakais(v.kods); } catch (e) { if (e.name === 'AbortError') throw e; }
      if (!f && v.aizstat) { aizstats = true; f = await tuvakais(v.aizstat).catch(() => null); }
      rezultats.vietas[v.kods] = f && { f, aizstats };
      vietasRinda(v, f, aizstats);
      return f;
    });
    // plūdu zonu rāda vienmēr (adreses fakts); lēmumu tā nosaka tikai plūdu situācijā
    const pludi = iegut('/pludi?' + new URLSearchParams(ll), signal).then(d => (rezultats.pludi = d))
      .catch(e => { if (e.name !== 'AbortError') rezultats.pludi = { kluda: true }; });
    pludi.then(() => { if (!signal.aborted) pluduRinda(); });
    iegut('/udens?' + new URLSearchParams({ ...ll, limit: 1 }), signal).then(d => udensRinda(d.stacijas[0]))
      .catch(e => { if (e.name !== 'AbortError') udensRinda(null); });
    atjaunotBridRindu();

    await Promise.allSettled([...vietas, pludi]);
    if (signal.aborted) return;
    lemums();
    talak();
    window.PlusmasKarte?.radit(rezultats, true);
    saglabat();
  }

  function rinda(id, saturs) { const li = $(id); if (li) li.querySelector('div').innerHTML = saturs; }

  function atjaunotBridRindu() {
    const b = st.bridinajumi;
    if (!$('r-brid')) return;
    if (b === undefined) return;  // vēl ielādē; bridinajumi() izsauks vēlreiz
    if (!b) return rinda('r-brid', `<b>Brīdinājumi</b><span>Pašlaik nav pieejami. Skatiet <a href="https://bridinajumi.meteo.lv" target="_blank" rel="noopener">bridinajumi.meteo.lv</a>.</span>`);
    rinda('r-brid', `<b>Brīdinājumi</b><span>${b.sheit.length
      ? b.sheit.map(x => `<span class="zime ${LIMENIS_KRASA[x.limenis]}">${LIMENIS_NOS[x.limenis] || esc(x.krasa)}</span> ${esc(x.paradiba)}${x.lidz ? `, līdz ${laiks(x.lidz)}` : ''}`).join('<br>')
      : 'Jūsu vietā spēkā esošu brīdinājumu nav.'}</span><small class="avots-rinda">${avotaSaite('brid')}</small>`);
  }

  function pluduRinda() {
    const p = rezultats.pludi;
    let t;
    if (!p || p.kluda) t = 'Neizdevās pārbaudīt (karšu serviss neatbild). Plūdu zonas var apskatīt kartē.';
    else if (p.zona) t = `<strong class="jā">Jā</strong>: ${p.veidi.map(v => `${esc(v.veids)} (${String(v.varbutiba_proc).replace('.', ',')} % varbūtība gadā)`).join(', ')}`;
    else if (p.nepilnigi) t = 'Pēc pieejamajām kartēm nē, bet daļa karšu neatbildēja.';
    else t = '<strong class="nē">Nē</strong>: adrese nav applūstošā teritorijā (10 %, 1 % un 0,5 % varbūtības kartes).';
    rinda('r-pludi', `<b>Plūdu riska zona</b><span>${t}</span><small class="avots-rinda">${avotaSaite('pludi')}</small>`);
  }

  function udensRinda(s) {
    if (!s) return rinda('r-udens', '<b>Tuvākā upe vai ezers</b><span>Ūdens līmeņa datus neizdevās ielādēt.</span>');
    const izm = s.izmaina_24h_cm;
    const tendence = izm == null ? '' : izm > 0 ? `, 24 h: ↑ +${izm} cm` : izm < 0 ? `, 24 h: ↓ −${Math.abs(izm)} cm` : ', 24 h: → nemainās';
    rinda('r-udens', `<b>Tuvākā upe vai ezers</b><span>Stacija ${esc(s.nosaukums)} (${km(s.attalums_m)}): ${s.limenis_cm} cm${tendence}` +
      `${s.vecs ? ' — <em>dati novecojuši</em>' : ''}<br><small>Mērīts ${esc(laiks(s.laiks))}. Bīstamības līmeņi nav atvērtie dati, tāpēc tos nerādām.</small></span>` +
      `<small class="avots-rinda">${avotaSaite('udens')}</small>`);
  }

  function marsruts(lat, lon) {
    const [x, y] = [(+lat).toFixed(6), (+lon).toFixed(6)];
    return `<span class="marsruts"><a href="https://www.google.com/maps/dir/?api=1&destination=${x}%2C${y}" target="_blank" rel="noopener">Google Maps</a>` +
      `<a href="https://www.waze.com/ul?ll=${x}%2C${y}&navigate=yes" target="_blank" rel="noopener">Waze</a></span>`;
  }

  function vietasRinda(v, f, aizstats) {
    if (!f) return rinda('r-' + v.kods, `<b>${esc(v.nos)}</b><span>Datos nav atrasta. Jautājiet pašvaldībai vai zvaniet 112.</span>`);
    const p = f.properties, i = p.ipasibas || {};
    const [lon, lat] = f.geometry.coordinates;
    if (aizstats) {  // kategorija vēl tukša: īsi norādām tuvāko patvertni (pilnā rinda ir zemāk)
      return rinda('r-' + v.kods, `<b>${esc(v.nos)}</b><span class="aizstats">Šai vietai vēl nav mūsu datos (pašvaldības CA plāns).
        Izmantojiet tuvāko patvertni: <b>${esc(p.nosaukums || p.adrese)}</b>, ${km(p.attalums_m)}</span>${marsruts(lat, lon)}`);
    }
    const ietilpiba = i.vietas ?? i.ietilpiba;  // CA plānu punkti (src/karte/dati/ca_plani): vietas, gultas, plans_url, lpp
    const nos = p.nosaukums || p.adrese || v.nos;
    rinda('r-' + v.kods, `<b>${esc(v.nos)}</b>` +
      `<span class="vietas-nos">${esc(nos)}</span>` +
      (p.adrese && p.adrese !== nos ? `<small>${esc(p.adrese)}</small>` : '') +
      (ietilpiba ? `<small>Ietilpība: ${esc(ietilpiba)} cilvēki${i.gultas ? `, ${esc(i.gultas)} gultas` : ''}</small>` : '') +
      (i.piezime ? `<small>${esc(i.piezime)}</small>` : '') +
      (/^https?:\/\//.test(i.plans_url || '') ? `<small><a href="${esc(i.plans_url)}" target="_blank" rel="noopener">Atvērt CA plānu${i.lpp ? ` (lpp. ${esc(i.lpp)})` : ''}</a></small>` : '') +
      `<span class="attalums">${km(p.attalums_m)} · ${kajam(p.attalums_m)}</span>${marsruts(lat, lon)}` +
      `<small class="avots-rinda">${objektaAvots(p.avots)}</small>`);
  }

  // Lēmums: konkrēts rezultāts, nevis "paldies". Plūdiem — pēc plūdu zonas adresē.
  function lemums() {
    const sit = st.situacija, scen = st.scenarijs, p = rezultats.pludi;
    let l;
    if (sit.pludu_parbaude) l = !p || p.kluda || (!p.zona && p.nepilnigi) ? sit.lemums_nezinams : p.zona ? sit.lemums_zona : sit.lemums_nav_zona;
    else if (sit.lemums) l = sit.lemums;
    else if (scen) l = { limenis: scen.zvanit112 ? 'sarkans' : 'dzeltens', virsraksts: scen.nosaukums, teksts: scen.padoms };
    else l = { limenis: 'dzeltens', virsraksts: 'Rīkojieties piesardzīgi', teksts: 'Ja kāds ir apdraudēts, zvaniet 112. Zemāk ir tuvākās drošās vietas un ko darīt.' };
    let teksts = l.teksts;
    if (st.apstakli.has('kustibas') && ['evakuacija', 'pludi'].includes(sit.kods)) teksts += ' Jums ir kustību ierobežojumi: zvaniet 112 un lūdziet palīdzību evakuācijā.';
    const g = galvenaVieta();
    $('lemums').className = 'lemums ' + l.limenis;
    $('lemums').innerHTML = `<b>${esc(l.virsraksts)}</b><p>${esc(teksts)}</p>` +
      (g ? `<p class="galvena-vieta">${esc(g.nos)}: <b>${esc(g.f.properties.nosaukums || g.f.properties.adrese)}</b>, ${km(g.f.properties.attalums_m)}</p>` : '');
  }

  function galvenaVieta() {
    const kods = st.situacija.galvena_vieta || (st.scenarijs?.kategorijas || []).find(k => rezultats.vietas[k]) || 'patvertne';
    const r = rezultats.vietas[kods] || rezultats.vietas.patvertne;
    if (!r) return null;
    const v = VIETAS.find(v => v.kods === kods) || VIETAS[2];
    return { f: r.f, nos: r.aizstats ? 'Tuvākā patvertne' : v.nos };
  }

  function talak() {
    const g = galvenaVieta();
    const soli = [];
    if (g) {
      const [lon, lat] = g.f.geometry.coordinates;
      const kur = `<b>${esc(g.f.properties.nosaukums || g.f.properties.adrese)}</b> (${km(g.f.properties.attalums_m)}, ${kajam(g.f.properties.attalums_m)}). ${marsruts(lat, lon)}`;
      const evakuacija = ['evakuacijas_punkts', 'izmitinasana'].includes(st.situacija.galvena_vieta);
      soli.push(st.situacija.kods === 'evakuacija' ? `Dodieties uz: ${kur}` : evakuacija ? `Ja jāpamet mājas, dodieties uz: ${kur}` : `${esc(g.nos)}: ${kur}`);
    }
    if (st.apstakli.has('bez_auto') || st.apstakli.has('kustibas')) soli.push('Ja nevarat nokļūt paši, zvaniet 112 vai savai pašvaldībai: palīdzēs ar evakuāciju.');
    soli.push('Par evakuāciju un izmaiņām paziņos LR1, LTV1 un <a href="https://www.112.lv" target="_blank" rel="noopener">112.lv</a>. Brīdinājumi: augšējā joslā šeit.');
    soli.push('Šī karte ir saglabāta Jūsu tālrunī: atverot map.repo.lv, to varēs redzēt arī bez interneta. Pārbaudiet to vēlreiz pēc dažām stundām.');
    soli.push('Ja kāds ir apdraudēts, zvaniet <a href="tel:112">112</a>.');
    $('talak').innerHTML = soli.map(s => `<li>${s}</li>`).join('');
  }

  // ---------- Saglabāšana (localStorage) un drukāšana ----------
  function saglabat() {
    try { localStorage.setItem(KRATUVE, JSON.stringify({ laiks: new Date().toISOString(), html: $('kopsavilkums').innerHTML })); } catch { /* privātais režīms */ }
  }
  function saglabataKarte() {
    try { return JSON.parse(localStorage.getItem(KRATUVE)); } catch { return null; }
  }
  function radtSaglabato() {
    const s = saglabataKarte();
    if (!s) return;
    $('solis').innerHTML = `<div id="kopsavilkums" class="saglabata">${s.html}</div>
      <p class="piezime">Saglabāts ${esc(laiks(s.laiks))}. Dati var būt novecojuši: lai atjaunotu, sāciet no jauna.</p>
      <div class="darbibas"><button type="button" class="galvena" id="drukat">🖨 Drukāt</button>
      <button type="button" class="otra" data-uz="1">↺ Sākt no jauna</button></div>`;
    $('solis').querySelectorAll('#kopsavilkums .saite').forEach(b => b.remove());
    $('drukat').addEventListener('click', () => window.print());
  }

  // ---------- Sākums ----------
  function sakt() {
    if (!window.PlusmasKarte) $('rezims-poga').hidden = true;  // Leaflet neielādējās: bez kartes režīma
    $('rezims-poga').addEventListener('click', () => uz(solis() === 'karte' ? (rezultats ? 4 : st.vieta ? 2 : 1) : 'karte'));
    document.addEventListener('click', e => {
      const b = e.target.closest('[data-uz]');
      if (b && $('plusma').contains(b)) uz(b.dataset.uz);
    });
    window.addEventListener('hashchange', radit);
    // krīzes meklēšanas saite (?q=…) un vecās saites atver karti
    if (new URLSearchParams(location.search).has('q') && !location.hash) location.replace('#/karte');
    bridinajumi(null);
    ieladet().then(radit).catch(() => {
      $('solis').innerHTML = `<h2>Neizdevās ielādēt</h2><p class="kluda">Pārbaudiet interneta savienojumu un pārlādējiet lapu.</p>
        <a class="zvanit112" href="tel:112">📞 Ārkārtas situācijā zvaniet 112</a>`;
      const s = saglabataKarte();
      if (s) $('solis').insertAdjacentHTML('beforeend', `<h3>Jūsu saglabātā karte</h3><div id="kopsavilkums" class="saglabata">${s.html}</div>`);
    });
  }

  return { sakt, st };
})();

Plusma.sakt();

// Bezsaistei: lapas faili kešā (service worker), lai saglabātā karte atveras arī bez interneta.
if ('serviceWorker' in navigator && (location.protocol === 'https:' || location.hostname === 'localhost')) {
  navigator.serviceWorker.register('sw.js').catch(() => {});
}
