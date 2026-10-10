// "Ziņot par bīstamību" (poga #zinot-poga galvenē, saite rezultāta kartītē; Zinot.atvert() citiem moduļiem): iedzīvotāju ziņojumi (nokritis koks, ceļš, elektrolīnija, applūdums) pēc lacukarte.lv parauga.
// Plūsma 5 soļos nemodālā panelī (telefonā apakšā, datorā kreisajā malā; karte paliek redzama un pieskarama):
// 1 kas (aizpildīts no meklētā scenārija) → 2 kur (meklētā adrese vai atrašanās vieta; tuvākā VZD adrese un pašvaldība
// no API; maina ar pieskārienu kartei) → 3 viena neobligāta teksta rinda → 4 kopsavilkums ar "Labot" un datu izmantošanu →
// 5 nosūtīšana un rezultāts (Nr., kas notiks tālāk, saite dalīšanai, "Ziņot vēl"). Līdz 5. solim nekas netiek sūtīts.
// Esc un pārlūka "Atpakaļ" — solis atpakaļ.
// Slānis "Iedzīvotāju ziņojumi" (izslēgts pēc noklusējuma): pelēki punkti ~1 km precizitātē, pēdējās 7 dienas,
// logā "Apstiprinu" / "Nav taisnība". Balsojumu atceras pārlūks (localStorage), serveris IP neglabā.
// API: GET/POST /api/zinojumi, POST /api/zinojumi/<id>/apstiprinat|apstridet (karte_api.py "Ziņojumi").
const Zinot = (() => {
  const TIPI = [
    ['koks', 'koks', 'Nokritis koks'], ['cels', 'remonts', 'Neizbraucams ceļš'], ['elektriba', 'zibens', 'Bojāta elektrolīnija'],
    ['udens', 'pludi', 'Applūdums'], ['cits', 'uzmanibu', 'Cita bīstamība'],
  ];
  const TIPS = Object.fromEntries(TIPI.map(([k, i, n]) => [k, { ikona: i, nos: n }]));
  const LICENCE = 'CC BY 4.0';  // = karte_api.py ZINOJUMI_LICENCE
  const ATRUNA = `Iedzīvotāju ziņojumi, nav oficiāla informācija, ${LICENCE}.`;
  // Meklētais scenārijs (scenariji.json) → ziņojuma tips; pārējiem tipu neaizpilda
  const NO_SCENARIJA = {
    koks_pari_celam: 'koks', vads_pari_celam: 'elektriba', nav_elektribas: 'elektriba', pludi: 'udens', udens_celas: 'udens',
    bloketa_soseja: 'cels', ledus_celi: 'cels',
  };
  const SOLI = ['Kas noticis?', 'Kur?', 'Sīkāk (nav obligāti)', 'Pārbaudiet un nosūtiet', 'Ziņojums nosūtīts'];
  const BALSIS = 'zinot-balsis';
  const slanis = L.layerGroup();
  let ieslegts = false, taimeris = null;

  const skaits = n => `${n} ${n % 10 === 1 && n % 100 !== 11 ? 'ziņojums' : 'ziņojumi'}`;
  const balsis = () => { try { return JSON.parse(localStorage.getItem(BALSIS) || '{}'); } catch { return {}; } };
  const pirms = iso => {
    const min = Math.max(0, Math.round((Date.now() - new Date(iso)) / 60000));
    return min < 60 ? `pirms ${min} min` : min < 2880 ? `pirms ${Math.round(min / 60)} h` : `pirms ${Math.round(min / 1440)} d.`;
  };

  // ---- Slānis ----
  function popups(z) {
    const t = TIPS[z.tips] || TIPS.cits;
    const nobalsots = balsis()[z.id];
    const apst = z.apstiprina ? `Apstiprinājuši: ${z.apstiprina}` : 'Nav apstiprināts';
    return `<div class="popup zinojums-popup"><b>${Ik(t.ikona)} ${esc(t.nos)}</b>
      ${z.apraksts ? `<p>${esc(z.apraksts)}</p>` : ''}
      <small>${pirms(z.laiks)} · ${apst}${z.apstrid ? ` · apstrīdējuši: ${z.apstrid}` : ''}</small>
      <small>Vieta rādīta ~1 km precizitātē.</small>
      <div class="zinojums-balsis" data-id="${z.id}">
        ${nobalsots ? '<small>Paldies, Jūsu balsojums ir saskaitīts.</small>'
          : `<button type="button" class="otra" data-balss="apstiprinat">✓ Apstiprinu</button>
             <button type="button" class="otra" data-balss="apstridet">✕ Nav taisnība</button>`}
      </div>
      <small class="popup-avots">${ATRUNA}</small></div>`;
  }

  function markieris(z) {
    return L.circleMarker([z.lat, z.lon], {
      zinojums: z.id, radius: 8, color: '#fff', weight: 2, fillColor: z.apstiprina ? '#57534e' : '#a8a29e', fillOpacity: .95, dashArray: z.apstiprina ? null : '3 2',
    }).bindPopup(() => popups(z)).bindTooltip(`${(TIPS[z.tips] || TIPS.cits).nos} (nav apstiprināts)`, { direction: 'top' });
  }

  async function ieladet(atvertId = null) {
    if (!ieslegts) return;
    if (slanis.getLayers().some(l => l.isPopupOpen())) return;  // logs atvērts (arī tā automātiskā pārbīde): neaizvērt
    const b = karte.getBounds();
    const bbox = [b.getWest(), b.getSouth(), b.getEast(), b.getNorth()].map(v => v.toFixed(3)).join(',');
    const piezime = document.getElementById('zinojumu-piezime');
    try {
      const r = await fetch('/api/zinojumi?bbox=' + bbox);
      if (!r.ok) throw new Error(r.status);
      const d = await r.json();
      slanis.clearLayers();
      d.zinojumi.forEach(z => slanis.addLayer(markieris(z)));
      if (atvertId) slanis.getLayers().find(l => String(l.options.zinojums) === String(atvertId))?.openPopup();
      piezime.textContent = !d.pieejams ? 'Ziņojumi šobrīd nav pieejami.'
        : d.zinojumi.length ? `${skaits(d.zinojumi.length)} šajā kartes skatā (pēdējās ${d.dienas} dienas). ${ATRUNA}`
        : `Šajā kartes skatā pēdējās ${d.dienas} dienās ziņojumu nav. ${ATRUNA}`;
    } catch {
      piezime.textContent = 'Ziņojumus neizdevās ielādēt. Mēģiniet vēlreiz pēc brīža.';
    }
  }

  function ieslegt(ir, atvertId = null) {
    ieslegts = ir;
    document.getElementById('zinojumu-slanis').checked = ir;
    document.getElementById('zinojumu-piezime').hidden = !ir;
    if (ir) { slanis.addTo(karte); ieladet(atvertId); } else { slanis.remove(); }
  }

  async function balsot(poga) {
    const kaste = poga.closest('.zinojums-balsis');
    const id = kaste.dataset.id;
    kaste.querySelectorAll('button').forEach(b => { b.disabled = true; });
    try {
      const r = await fetch(`/api/zinojumi/${encodeURIComponent(id)}/${poga.dataset.balss}`, { method: 'POST' });
      if (r.status === 429) {  // servera stundas limits (ziņojumam vai tīklam): pogas paliek atslēgtas
        const d = await r.json().catch(() => ({}));
        const t = d.kluda || 'pārāk daudz balsojumu, mēģiniet vēlāk';
        kaste.insertAdjacentHTML('beforeend', `<small class="kluda">${esc(t.charAt(0).toUpperCase() + t.slice(1))}.</small>`);
        return;
      }
      if (!r.ok) throw new Error(r.status);
      const b = balsis(); b[id] = poga.dataset.balss; localStorage.setItem(BALSIS, JSON.stringify(b));
      kaste.innerHTML = '<small>Paldies, Jūsu balsojums ir saskaitīts.</small>';  // slānis atjaunosies pēc nākamās kartes kustības
    } catch {
      kaste.insertAdjacentHTML('beforeend', '<small class="kluda">Neizdevās. Mēģiniet vēlreiz.</small>');
      kaste.querySelectorAll('button').forEach(b => { b.disabled = false; });
    }
  }

  // ---- Plūsma ----
  let panelis, saturs, solis = 1, labo = false, sutits = null, vesture = false, vietasPieprasijums = null, apaksaBija = null;
  let dati = { tips: '', apraksts: '', vieta: null };
  let noMeklejuma = '';  // scenārija nosaukums, ja tips aizpildīts no meklējuma
  const vietasZime = L.circleMarker([0, 0], { radius: 10, color: '#fff', weight: 3, fillColor: '#d52b1e', fillOpacity: 1, interactive: false });
  const telefons = matchMedia('(max-width: 800px)');
  const AVOTU_TEKSTI = { adrese: 'meklētā adrese (VZD adrešu reģistrs)', gps: 'Jūsu atrašanās vieta', karte: 'pieskāriens kartei', saite: 'saitē norādītā vieta' };

  function izveidot() {
    panelis = document.createElement('section');
    panelis.id = 'zinot-panelis';
    panelis.className = 'zinot-panelis';
    panelis.setAttribute('role', 'dialog');
    panelis.setAttribute('aria-modal', 'false');
    panelis.setAttribute('aria-labelledby', 'zinot-virsraksts');
    panelis.hidden = true;
    panelis.innerHTML = `<div class="zinot-galva"><div><p class="zinot-solis" id="zinot-solis"></p><h2 id="zinot-virsraksts" tabindex="-1"></h2></div>
      <button type="button" class="zinot-aizvert" data-zinot="aizvert" aria-label="Aizvērt">${Ik('aizvert')}</button></div>
      <div class="zinot-saturs" aria-live="polite"></div><div class="zinot-kaja"></div>`;
    document.body.appendChild(panelis);
    saturs = panelis.querySelector('.zinot-saturs');
    panelis.addEventListener('click', e => {
      const b = e.target.closest('[data-zinot]');
      if (!b) return;
      const d = b.dataset.zinot;
      if (d === 'aizvert') aizvert();
      else if (d === 'atpakal') atpakal();
      else if (d === 'talak') talak();
      else if (d === 'tips') { dati.tips = b.dataset.tips; noMeklejuma = ''; talak(); }
      else if (d === 'mana-vieta') manaVieta();
      else if (d === 'labot') { labo = true; uzSoli(+b.dataset.solis); }
      else if (d === 'sutit') sutit();
      else if (d === 'dalities') dalities();
      else if (d === 'vel') { dati = { tips: '', apraksts: '', vieta: dati.vieta }; sutits = null; noMeklejuma = ''; uzSoli(1); }
    });
    panelis.addEventListener('keydown', e => {
      if (e.key === 'Enter' && e.target.id === 'zinot-apraksts') { e.preventDefault(); talak(); }
    });
    panelis.addEventListener('input', e => {
      if (e.target.id !== 'zinot-apraksts') return;
      dati.apraksts = e.target.value;
      panelis.querySelector('#zinot-zimes').textContent = `${e.target.value.length} / 200`;
    });
    // Telefona tastatūra: panelis paliek virs tās un ekrānā (visualViewport; stils.css --zinot-kb, --zinot-vh)
    const vv = window.visualViewport;
    if (vv) {
      const pielagot = () => {
        panelis.style.setProperty('--zinot-kb', Math.max(0, Math.round(innerHeight - vv.height - vv.offsetTop)) + 'px');
        panelis.style.setProperty('--zinot-vh', Math.round(vv.height) + 'px');
      };
      vv.addEventListener('resize', pielagot);
      vv.addEventListener('scroll', pielagot);
      pielagot();
    }
    panelis.addEventListener('focusin', e => {
      if (e.target.matches('input')) setTimeout(() => e.target.scrollIntoView({ block: 'nearest' }), 300);
    });
  }

  const atverts = () => !!panelis && !panelis.hidden;

  // Datorā — kreisajā malā zem galvenes (sānu paneļa vietā); telefonā — apakšā (stils.css)
  function novietot() {
    const galvene = document.querySelector('header');
    panelis.style.top = !telefons.matches && galvene ? Math.round(galvene.getBoundingClientRect().bottom) + 'px' : '';
  }

  function uzSoli(n) {
    solis = n;
    zimet();
    if (n === 2 && dati.vieta) radtVietu(false);
    panelis.querySelector('#zinot-virsraksts').focus({ preventScroll: true });
  }

  const pogaAtpakal = '<button type="button" class="otra" data-zinot="atpakal">Atpakaļ</button>';
  const pogaTalak = (t = 'Tālāk') => `<button type="button" class="galvena" data-zinot="talak">${labo ? 'Uz kopsavilkumu' : t}</button>`;

  function vietasHtml(v) {
    if (!v) return '<p class="zinot-vieta-teksts">Vieta vēl nav norādīta.</p>';
    const nos = v.adrese ? (v.avots === 'adrese' ? '' : '~') + esc(v.adrese) : v.ielade ? 'Nosaka adresi…' : `${v.lat.toFixed(3)}, ${v.lon.toFixed(3)}`;
    const avoti = [AVOTU_TEKSTI[v.avots] || 'karte'];
    if (v.adrese && v.avots !== 'adrese') avoti.push('tuvākā adrese — VZD adrešu reģistrs');
    if (v.pasvaldiba) avoti.push('pašvaldība — VZD adrešu reģistra robežas');
    return `<p class="zinot-vieta-teksts"><b>${nos}</b>${v.pasvaldiba ? `<br>${esc(v.pasvaldiba)}` : ''}<br><small>Avots: ${avoti.join('; ')}</small></p>`;
  }

  function zimet(kluda = '') {
    panelis.querySelector('#zinot-solis').textContent = `${solis}/5`;
    panelis.querySelector('#zinot-virsraksts').textContent = SOLI[solis - 1];
    panelis.dataset.solis = solis;
    const kaja = panelis.querySelector('.zinot-kaja');
    const k = kluda ? `<p class="kluda" role="alert">${esc(kluda)}</p>` : '';
    if (solis === 1) {
      saturs.innerHTML = (noMeklejuma && dati.tips ? `<p class="piezime">Atzīmēts pēc Jūsu meklējuma „${esc(noMeklejuma)}”. Ja vajag, izvēlieties citu.</p>` : '') +
        `<div class="zinot-tipi" role="group" aria-label="Bīstamības veids">${TIPI.map(([kods, ik, nos]) =>
          `<button type="button" data-zinot="tips" data-tips="${kods}" aria-pressed="${dati.tips === kods}">${Ik(ik)}<span>${esc(nos)}</span></button>`).join('')}</div>` + k +
        '<p class="zvanit-teksts">Ja apdraudēta dzīvība vai veselība, zvaniet 112.</p>';
      kaja.innerHTML = dati.tips ? pogaTalak() : '';
    } else if (solis === 2) {
      saturs.innerHTML = vietasHtml(dati.vieta) +
        `<p class="piezime">${dati.vieta ? 'Lai mainītu vietu, pieskarieties kartei.' : 'Pieskarieties kartei vietā, kur ir bīstamība, vai izmantojiet savu atrašanās vietu.'}</p>` +
        `<button type="button" class="otra" data-zinot="mana-vieta">${Ik('vieta')}<span> ${dati.vieta?.avots === 'gps' ? 'Atjaunot manu atrašanās vietu' : 'Izmantot manu atrašanās vietu'}</span></button>` + k;
      kaja.innerHTML = pogaAtpakal + (dati.vieta ? pogaTalak() : '');
    } else if (solis === 3) {
      saturs.innerHTML = `<label for="zinot-apraksts" class="zinot-etikete">Īsi aprakstiet, kas redzams</label>
        <input id="zinot-apraksts" type="text" maxlength="200" autocomplete="off" enterkeyhint="next" value="${esc(dati.apraksts)}"
          placeholder="Piem.: koks pāri ceļam pie tilta">
        <small id="zinot-zimes" class="piezime">${dati.apraksts.length} / 200</small>
        <p class="piezime">Neierakstiet vārdus, tālruņus un citus personas datus. Saites netiek pieņemtas.</p>` + k;
      kaja.innerHTML = pogaAtpakal + pogaTalak('Tālāk: pārbaudīt');
    } else if (solis === 4) {
      const t = TIPS[dati.tips];
      const labot = (n, ko) => `<button type="button" class="zinot-labot" data-zinot="labot" data-solis="${n}" aria-label="Labot: ${ko}">Labot</button>`;
      saturs.innerHTML = `<dl class="zinot-kopsavilkums">
          <div><dt>Kas</dt><dd>${Ik(t.ikona)} ${esc(t.nos)}</dd>${labot(1, 'kas')}</div>
          <div><dt>Kur</dt><dd>${vietasHtml(dati.vieta)}</dd>${labot(2, 'kur')}</div>
          <div><dt>Apraksts</dt><dd>${dati.apraksts ? esc(dati.apraksts) : '<span class="piezime">nav</span>'}</dd>${labot(3, 'apraksts')}</div>
        </dl>
        <div class="zinot-datu-piezime"><b>Kā izmantosim šos datus</b><ul>
          <li>Ziņojums būs publisks kartē (slānis „Iedzīvotāju ziņojumi”) 7 dienas kā iedzīvotāju ziņojums, nevis oficiāla informācija.</li>
          <li>Vietu glabājam ~100 m precizitātē, kartē rādām noapaļotu līdz ~1 km.</li>
          <li>Jūsu IP adresi un citus personas datus neglabājam.</li>
          <li>Licence: ${LICENCE}, ziņojumu drīkst izmantot citi.</li></ul></div>` + k;
      kaja.innerHTML = pogaAtpakal + '<button type="button" class="galvena" data-zinot="sutit">Nosūtīt</button>';
    } else if (!sutits) {
      saturs.innerHTML = '<p>Sūta…</p>';
      kaja.innerHTML = '';
    } else {
      const v = dati.vieta;
      saturs.innerHTML = `<p class="zinot-rezultats">${Ik('karogs')} Ziņojums Nr. <b>${esc(sutits.id)}</b> ir kartē.</p>
        <p><b>${esc(TIPS[sutits.tips]?.nos || '')}</b> · ${v?.adrese ? esc(v.adrese) : `${(+sutits.lat).toFixed(2)}, ${(+sutits.lon).toFixed(2)}`}</p>
        <p class="zinot-etikete">Kas notiks tālāk</p><ul class="zinot-talak">
          <li>Redzams kartē tūlīt (slānis „Iedzīvotāju ziņojumi”, ~1 km precizitātē) 7 dienas.</li>
          <li>Citi iedzīvotāji to var apstiprināt vai apstrīdēt; apstrīdētu ziņojumu karte paslēpj.</li>
          <li>Pašvaldība un VUGD to automātiski neredz.</li></ul>
        <p class="zvanit-teksts">Ja apdraudēta dzīvība vai veselība, zvaniet 112.</p>
        <p class="piezime zinot-dalities-zina" role="status" hidden></p>`;
      kaja.innerHTML = `<button type="button" class="otra" data-zinot="dalities">${Ik('dalities')} Dalīties</button>
        <button type="button" class="otra" data-zinot="vel">Ziņot vēl</button>
        <button type="button" class="galvena" data-zinot="aizvert">Uz karti</button>`;
    }
  }

  function talak() {
    if (solis === 1 && !dati.tips) return zimet('Izvēlieties, kas noticis.');
    if (solis === 2 && !dati.vieta) return zimet('Norādiet vietu: pieskarieties kartei vai izmantojiet savu atrašanās vietu.');
    if (solis === 3) {
      dati.apraksts = dati.apraksts.replace(/\s+/g, ' ').trim().slice(0, 200);
      if (/https?:|www\./i.test(dati.apraksts)) return zimet('Aprakstā nedrīkst būt saites.');
    }
    if (labo) { labo = false; return uzSoli(4); }
    uzSoli(Math.min(solis + 1, 4));
  }

  function atpakal() {
    if (solis === 1 || solis === 5) return aizvert();
    if (labo) { labo = false; return uzSoli(4); }
    uzSoli(solis - 1);
  }

  // ---- Vieta: tuvākā VZD adrese un pašvaldība (tikai GET; nekas netiek saglabāts) ----
  function iestatitVietu(lat, lon, avots, adrese = '') {
    if (vietasPieprasijums) vietasPieprasijums.abort();
    const ctrl = vietasPieprasijums = new AbortController();
    const v = dati.vieta = { lat, lon, avots, adrese, pasvaldiba: '', ielade: !adrese };
    const ll = new URLSearchParams({ lat: lat.toFixed(5), lon: lon.toFixed(5) });
    const parzimet = () => { if (dati.vieta === v && atverts() && (solis === 2 || solis === 4)) zimet(); };
    if (!adrese) {
      iegut('/adreses/tuvaka?' + ll, ctrl.signal).then(a => { if (a.adrese) v.adrese = isaAdrese(a.adrese); })
        .catch(() => {}).finally(() => { v.ielade = false; parzimet(); });
    }
    iegut('/pasvaldiba?' + ll, ctrl.signal).then(p => { v.pasvaldiba = p.nosaukums || ''; parzimet(); }).catch(() => {});
  }

  function radtVietu(centrot = true) {
    const v = dati.vieta;
    if (!v) { vietasZime.remove(); return; }
    vietasZime.setLatLng([v.lat, v.lon]).addTo(karte);
    if (!centrot) return;
    karte.setView([v.lat, v.lon], Math.max(karte.getZoom(), 15), { animate: false });
    // panelis sedz daļu kartes — vietu rāda redzamajā daļā (telefonā virs paneļa, datorā pa labi no tā)
    if (telefons.matches) karte.panBy([0, Math.round(panelis.offsetHeight / 2)], { animate: false });
    else karte.panBy([-Math.round(panelis.offsetWidth / 2), 0], { animate: false });
  }

  function manaVieta() {
    if (!navigator.geolocation) return zimet('Šis pārlūks nevar noteikt atrašanās vietu. Pieskarieties kartei.');
    const poga = panelis.querySelector('[data-zinot="mana-vieta"]');
    if (poga) { poga.disabled = true; poga.lastChild.textContent = ' Nosaka atrašanās vietu…'; }
    navigator.geolocation.getCurrentPosition(p => {
      const { latitude: lat, longitude: lon } = p.coords;
      if (!(lat > 55 && lat < 59 && lon > 20 && lon < 29)) return zimet('Jūsu atrašanās vieta nav Latvijā. Pieskarieties kartei.');
      iestatitVietu(lat, lon, 'gps');
      zimet();
      radtVietu();
    }, () => zimet('Atrašanās vietu neizdevās noteikt. Pieskarieties kartei.'), { enableHighAccuracy: true, timeout: 10000, maximumAge: 60000 });
  }

  // Sākuma dati no tā, ko lapa jau zina: meklētais scenārijs un adrese vai atrašanās vieta (neprasām vēlreiz)
  function aizpildit() {
    const k = typeof krizesMeklesana !== 'undefined' && krizesMeklesana.konteksts?.();
    dati = { tips: NO_SCENARIJA[k?.kods] || '', apraksts: '', vieta: null };
    noMeklejuma = dati.tips ? k.nosaukums : '';
    const no = k?.vieta && !k.vieta.regions ? k.vieta : stavoklis.vieta;
    if (!no) return;
    const adrese = k?.adrese && no === k.vieta ? k.adrese : no.adrese;
    iestatitVietu(+no.lat, +no.lon, adrese ? 'adrese' : no.noSaites ? 'saite' : 'gps', adrese ? isaAdrese(adrese) : '');
  }

  async function sutit() {
    if (!dati.tips || !dati.vieta) return uzSoli(dati.tips ? 2 : 1);
    sutits = null;
    uzSoli(5);
    const v = dati.vieta;
    try {
      const r = await fetch('/api/zinojumi', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tips: dati.tips, apraksts: dati.apraksts, lat: v.lat, lon: v.lon }),
      });
      const d = await r.json().catch(() => ({}));
      if (!r.ok || d.id == null) {
        solis = 4;
        return zimet(d.kluda ? `Neizdevās nosūtīt: ${d.kluda}.` : 'Neizdevās nosūtīt. Mēģiniet vēlreiz pēc brīža.');
      }
      sutits = d;
      zimet();
      vietasZime.remove();
      ieslegt(true);
      slanis.addLayer(markieris(d));
    } catch {
      solis = 4;
      zimet('Neizdevās nosūtīt (nav savienojuma). Mēģiniet vēlreiz.');
    }
  }

  const saite = z => `${location.origin}${location.pathname}?${new URLSearchParams({ zinojums: z.id, lat: (+z.lat).toFixed(2), lon: (+z.lon).toFixed(2) })}`;

  async function dalities() {
    const url = saite(sutits), nos = `Iedzīvotāja ziņojums: ${TIPS[sutits.tips]?.nos || 'bīstamība'}`;
    const zina = t => { const z = panelis.querySelector('.zinot-dalities-zina'); if (z) { z.textContent = t; z.hidden = false; } };
    if (navigator.share) {
      try { await navigator.share({ title: nos, text: nos, url }); return; } catch (e) { if (e.name === 'AbortError') return; }
    }
    try { await navigator.clipboard.writeText(url); zina('Saite nokopēta: ' + url); } catch { zina('Saite: ' + url); }
  }

  function atvert() {
    if (!panelis) izveidot();
    if (!atverts()) {
      aizpildit();
      sutits = null; labo = false;
      panelis.hidden = false;
      document.body.classList.add('zinot-atverts');
      // telefonā rezultātu lapu (apaksa.js) saplok, lai virs paneļa redzama karte, kurai var pieskarties
      apaksaBija = typeof Apaksa !== 'undefined' && Apaksa.aktiva() ? Apaksa.stavoklis() : null;
      if (apaksaBija && apaksaBija !== 'peek') Apaksa.atvert('peek');
      history.pushState({ zinot: true }, '');
      vesture = true;
    }
    novietot();
    uzSoli(1);
    if (dati.vieta) radtVietu();
  }

  function aizvert() {
    if (!atverts()) return;
    panelis.hidden = true;
    document.body.classList.remove('zinot-atverts');
    vietasZime.remove();
    if (vietasPieprasijums) vietasPieprasijums.abort();
    if (apaksaBija && apaksaBija !== 'peek' && Apaksa.aktiva()) Apaksa.atvert(apaksaBija);
    apaksaBija = null;
    if (sutits) karte.setView([+sutits.lat, +sutits.lon], Math.max(karte.getZoom(), 14));
    if (vesture) { vesture = false; history.back(); }
    document.getElementById('zinot-poga')?.focus({ preventScroll: true });
  }

  // ---- Savienojumi ----
  document.addEventListener('click', e => {
    if (e.target.closest('[data-darbiba="zinot"]')) atvert();
    const b = e.target.closest('[data-balss]');
    if (b) balsot(b);
  });
  document.addEventListener('keydown', e => {
    if (e.key !== 'Escape' || !atverts() || document.querySelector('dialog[open]')) return;
    e.preventDefault();
    atpakal();
  });
  // Pārlūka / telefona "Atpakaļ": solis atpakaļ (vēstures ierakstu ieliek atverot un atjauno pēc katra soļa)
  addEventListener('popstate', () => {
    if (!atverts() || !vesture) return;
    vesture = false;
    if (solis > 1 && solis < 5) { atpakal(); history.pushState({ zinot: true }, ''); vesture = true; } else aizvert();
  });
  addEventListener('resize', () => { if (atverts()) novietot(); });
  document.getElementById('zinojumu-slanis')?.addEventListener('change', e => ieslegt(e.target.checked));
  karte.on('moveend', () => { clearTimeout(taimeris); taimeris = setTimeout(ieladet, 300); });
  karte.on('click', e => {
    if (!atverts() || solis !== 2) return;
    iestatitVietu(e.latlng.lat, e.latlng.lng, 'karte');
    zimet();
    radtVietu(false);
    setTimeout(() => karte.closePopup(), 50);  // citu slāņu logi (objekti, zonas) šajā solī netraucē
  });

  // Dalītā saite ?zinojums=<id>&lat=&lon= → ieslēdz slāni un atver šo ziņojumu
  const saitesQ = new URLSearchParams(location.search);
  const sLat = +saitesQ.get('lat'), sLon = +saitesQ.get('lon');
  if (saitesQ.has('zinojums') && sLat > 55 && sLat < 59 && sLon > 20 && sLon < 29) {
    setTimeout(() => { karte.setView([sLat, sLon], 14, { animate: false }); ieslegt(true, saitesQ.get('zinojums')); }, 800);
  }

  return { atvert, ieslegt };
})();
