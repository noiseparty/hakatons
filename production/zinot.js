// "Ziņot par bīstamību": iedzīvotāju ziņojumi (nokritis koks, ceļš, elektrolīnija, applūdums) pēc lacukarte.lv parauga.
// Forma dialoglodziņā: tips → īss teksts → vieta (mana atrašanās vieta vai pieskāriens kartei) → apstiprinājums.
// Slānis "Iedzīvotāju ziņojumi" (izslēgts pēc noklusējuma): pelēki punkti ~1 km precizitātē, pēdējās 7 dienas,
// logā "Apstiprinu" / "Nav taisnība". Balsojumu atceras pārlūks (localStorage), serveris IP neglabā.
// API: GET/POST /api/zinojumi, POST /api/zinojumi/<id>/apstiprinat|apstridet (karte_api.py "Ziņojumi").
const Zinot = (() => {
  const TIPI = [
    ['koks', 'koks', 'Nokritis koks'], ['cels', 'remonts', 'Neizbraucams ceļš'], ['elektriba', 'zibens', 'Bojāta elektrolīnija'],
    ['udens', 'pludi', 'Applūdums'], ['cits', 'uzmanibu', 'Cita bīstamība'],
  ];
  const TIPS = Object.fromEntries(TIPI.map(([k, i, n]) => [k, { ikona: i, nos: n }]));
  const ATRUNA = 'Iedzīvotāju ziņojumi, nav oficiāla informācija, CC BY 4.0.';
  const BALSIS = 'zinot-balsis';
  const slanis = L.layerGroup();
  let dialogs, vieta = null, izvelas = false, ieslegts = false, taimeris = null;

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

  async function ieladet() {
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
      piezime.textContent = !d.pieejams ? 'Ziņojumi šobrīd nav pieejami.'
        : d.zinojumi.length ? `${skaits(d.zinojumi.length)} šajā kartes skatā (pēdējās ${d.dienas} dienas). ${ATRUNA}`
        : `Šajā kartes skatā pēdējās ${d.dienas} dienās ziņojumu nav. ${ATRUNA}`;
    } catch {
      piezime.textContent = 'Ziņojumus neizdevās ielādēt. Mēģiniet vēlreiz pēc brīža.';
    }
  }

  function ieslegt(ir) {
    ieslegts = ir;
    document.getElementById('zinojumu-slanis').checked = ir;
    document.getElementById('zinojumu-piezime').hidden = !ir;
    if (ir) { slanis.addTo(karte); ieladet(); } else { slanis.remove(); }
  }

  async function balsot(poga) {
    const kaste = poga.closest('.zinojums-balsis');
    const id = kaste.dataset.id;
    kaste.querySelectorAll('button').forEach(b => { b.disabled = true; });
    try {
      const r = await fetch(`/api/zinojumi/${encodeURIComponent(id)}/${poga.dataset.balss}`, { method: 'POST' });
      if (!r.ok) throw new Error(r.status);
      const b = balsis(); b[id] = poga.dataset.balss; localStorage.setItem(BALSIS, JSON.stringify(b));
      kaste.innerHTML = '<small>Paldies, Jūsu balsojums ir saskaitīts.</small>';  // slānis atjaunosies pēc nākamās kartes kustības
    } catch {
      kaste.insertAdjacentHTML('beforeend', '<small class="kluda">Neizdevās. Mēģiniet vēlreiz.</small>');
      kaste.querySelectorAll('button').forEach(b => { b.disabled = false; });
    }
  }

  // ---- Forma ----
  function izveidot() {
    dialogs = document.createElement('dialog');
    dialogs.id = 'zinot-dialogs';
    dialogs.className = 'saraksts-dialogs zinot-dialogs';
    dialogs.setAttribute('aria-labelledby', 'zinot-virsraksts');
    document.body.appendChild(dialogs);
    dialogs.addEventListener('click', e => {
      if (e.target === dialogs) dialogs.close();
      const d = e.target.closest('[data-zinot]')?.dataset.zinot;
      if (d === 'aizvert') dialogs.close();
      else if (d === 'mana-vieta') manaVieta();
      else if (d === 'karte') saktIzveli();
      else if (d === 'talak') parskats();
      else if (d === 'labot') forma();
      else if (d === 'sutit') sutit();
    });
    dialogs.addEventListener('input', e => {
      if (e.target.id === 'zinot-apraksts') document.getElementById('zinot-zimes').textContent = `${e.target.value.length} / 200`;
    });
  }

  const galva = virsraksts => `<div class="saraksts-galva"><h2 id="zinot-virsraksts">${virsraksts}</h2>
    <button type="button" class="saraksts-aizvert" data-zinot="aizvert" aria-label="Aizvērt">✕</button></div>`;

  let melnraksts = { tips: '', apraksts: '' };
  function forma(kluda = '') {
    const vietasTeksts = vieta
      ? `Izvēlēta vieta: ${vieta.lat.toFixed(3)}, ${vieta.lon.toFixed(3)}. Glabāsim ~100 m precizitātē, kartē rādīsim ~1 km.`
      : 'Vieta vēl nav izvēlēta.';
    dialogs.innerHTML = galva('Ziņot par bīstamību') + `<form class="zinot-forma" novalidate>
      <fieldset><legend>1. Kas noticis?</legend>
        <div class="zinot-tipi">${TIPI.map(([k, i, n]) => `<label><input type="radio" name="tips" value="${k}"${melnraksts.tips === k ? ' checked' : ''}>
          <span aria-hidden="true">${i}</span> ${n}</label>`).join('')}</div></fieldset>
      <label for="zinot-apraksts" class="zinot-etikete">2. Īsi aprakstiet (nav obligāti)</label>
      <textarea id="zinot-apraksts" maxlength="200" rows="3" placeholder="Piem.: koks pāri ceļam pie tilta, var apbraukt pa kreiso joslu">${esc(melnraksts.apraksts)}</textarea>
      <small id="zinot-zimes" class="piezime">${melnraksts.apraksts.length} / 200</small>
      <p class="zinot-etikete">3. Kur?</p>
      <div class="zinot-vieta"><button type="button" class="otra" data-zinot="mana-vieta">${Ik('vieta')} Izmantot manu atrašanās vietu</button>
        <button type="button" class="otra" data-zinot="karte">${Ik('karte')} Norādīt kartē</button></div>
      <p class="piezime" aria-live="polite">${vietasTeksts}</p>
      ${kluda ? `<p class="kluda" role="alert">${esc(kluda)}</p>` : ''}
      <p class="piezime">Ziņojums būs redzams visiem kā iedzīvotāju ziņojums (CC BY 4.0), nevis oficiāla informācija. Neierakstiet vārdus, tālruņus un citus personas datus. Ja apdraudēta dzīvība, zvaniet 112.</p>
      <button type="button" class="galvena" data-zinot="talak">Tālāk: pārbaudīt</button></form>`;
  }

  function saglabatMelnrakstu() {
    const t = dialogs.querySelector('input[name="tips"]:checked');
    const a = dialogs.querySelector('#zinot-apraksts');
    if (t) melnraksts.tips = t.value;
    if (a) melnraksts.apraksts = a.value.trim().slice(0, 200);
  }

  function manaVieta() {
    saglabatMelnrakstu();
    if (!navigator.geolocation) return forma('Šis pārlūks nevar noteikt atrašanās vietu. Norādiet vietu kartē.');
    navigator.geolocation.getCurrentPosition(
      p => { vieta = { lat: p.coords.latitude, lon: p.coords.longitude }; forma(); },
      () => forma('Atrašanās vietu neizdevās noteikt. Norādiet vietu kartē.'),
      { enableHighAccuracy: true, timeout: 10000 });
  }

  function saktIzveli() {
    saglabatMelnrakstu();
    dialogs.close();
    izvelas = true;
    const josla = document.getElementById('zinot-josla');
    josla.hidden = false;
    karte.getContainer().classList.add('zinot-izvele');
  }

  function beigtIzveli() {
    izvelas = false;
    document.getElementById('zinot-josla').hidden = true;
    karte.getContainer().classList.remove('zinot-izvele');
  }

  function parskats() {
    saglabatMelnrakstu();
    if (!melnraksts.tips) return forma('Izvēlieties, kas noticis.');
    if (!vieta) return forma('Izvēlieties vietu: Jūsu atrašanās vieta vai pieskāriens kartei.');
    if (/https?:|www\./i.test(melnraksts.apraksts)) return forma('Aprakstā nedrīkst būt saites.');
    const t = TIPS[melnraksts.tips];
    dialogs.innerHTML = galva('Pārbaudiet ziņojumu') + `<div class="zinot-forma">
      <dl class="zinot-kopsavilkums"><dt>Kas</dt><dd>${Ik(t.ikona)} ${esc(t.nos)}</dd>
        <dt>Apraksts</dt><dd>${melnraksts.apraksts ? esc(melnraksts.apraksts) : '—'}</dd>
        <dt>Vieta</dt><dd>${vieta.lat.toFixed(3)}, ${vieta.lon.toFixed(3)} (kartē ~1 km)</dd></dl>
      <p class="piezime">Pēc nosūtīšanas ziņojums parādīsies kartē kā pelēks punkts „nav apstiprināts”. Citi to var apstiprināt vai apstrīdēt; pēc 7 dienām tas pazūd.</p>
      <div class="zinot-pogas"><button type="button" class="otra" data-zinot="labot">Labot</button>
        <button type="button" class="galvena" data-zinot="sutit">Nosūtīt</button></div></div>`;
    dialogs.querySelector('[data-zinot="sutit"]').focus();
  }

  async function sutit() {
    const poga = dialogs.querySelector('[data-zinot="sutit"]');
    poga.disabled = true;
    try {
      const r = await fetch('/api/zinojumi', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tips: melnraksts.tips, apraksts: melnraksts.apraksts, lat: vieta.lat, lon: vieta.lon }),
      });
      const d = await r.json().catch(() => ({}));
      if (!r.ok) return forma(d.kluda ? `Neizdevās nosūtīt: ${d.kluda}.` : 'Neizdevās nosūtīt. Mēģiniet vēlreiz pēc brīža.');
      dialogs.innerHTML = galva('Paldies!') + `<div class="zinot-forma">
        <p>Jūsu ziņojums ir kartē (slānis „Iedzīvotāju ziņojumi”). Tas nav paziņojums dienestiem: ja apdraudēta dzīvība vai veselība, zvaniet 112.</p>
        <button type="button" class="galvena" data-zinot="aizvert">Uz karti</button></div>`;
      melnraksts = { tips: '', apraksts: '' };
      const v = vieta; vieta = null;
      ieslegt(true);
      slanis.addLayer(markieris(d));
      karte.setView([v.lat, v.lon], Math.max(karte.getZoom(), 14));
    } catch {
      forma('Neizdevās nosūtīt (nav savienojuma). Mēģiniet vēlreiz.');
    }
  }

  function atvert() {
    if (!dialogs) izveidot();
    beigtIzveli();
    forma();
    dialogs.showModal();
    dialogs.querySelector('.saraksts-aizvert').focus();
  }

  // ---- Savienojumi ----
  document.addEventListener('click', e => {
    if (e.target.closest('[data-darbiba="zinot"]')) atvert();
    const b = e.target.closest('[data-balss]');
    if (b) balsot(b);
    if (e.target.closest('[data-zinot="atcelt-izveli"]')) beigtIzveli();
  });
  document.getElementById('zinojumu-slanis')?.addEventListener('change', e => ieslegt(e.target.checked));
  karte.on('moveend', () => { clearTimeout(taimeris); taimeris = setTimeout(ieladet, 300); });
  karte.on('click', e => {
    if (!izvelas) return;
    vieta = { lat: e.latlng.lat, lon: e.latlng.lng };
    beigtIzveli();
    forma();
    dialogs.showModal();
  });

  return { atvert, ieslegt };
})();
