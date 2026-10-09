// "Prognoze / ziņas": LVĢMC prognozes apdzīvotām vietām + spēkā esošie brīdinājumi kā ziņu lente (/api/prognozes).
// Novadi kartē iekrāsoti pēc izvēlētās dienas prognozes (mūsu sliekšņi, NAV oficiāls brīdinājums); brīdinājumu
// poligoni — raustīta līnija. Pieskaroties ziņai, karte pietuvina skartos novadus. Izmanto `karte` no app.js.
const Prognozes = (() => {
  const KRASAS = { 0: '#bae6fd', 1: '#facc15', 2: '#f97316', 3: '#dc2626' };
  const LIMENI = { 0: 'ievērībai', 1: 'dzeltenais līmenis', 2: 'oranžais līmenis', 3: 'sarkanais līmenis' };
  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const sk = x => x == null ? '–' : String(Math.abs(x) >= 10 || x === Math.round(x) ? Math.round(x) : x.toFixed(1)).replace('.', ',');
  const kaste = document.getElementById('prognozes');
  let dati = null, diena = null, robezas = null, aktivie = [];
  const novaduSlanis = L.geoJSON(null, { style: stils, onEachFeature: (f, l) => l.on('click', e => popups(f, e.latlng)) });
  const bridSlanis = L.layerGroup();

  function limenis(r) {
    if (!r || !dati) return null;
    const s = dati.sliekshni;
    const pec = (veids, v, maz) => s[veids].reduce((rez, [robeza, lim]) => (maz ? v <= robeza : v >= robeza) ? lim : rez, null);
    const l = [pec('brazmas', r.brazmas), pec('nokrisni', r.nokrisni), pec('karstums', r.tmax), pec('sals', r.tmin, true)]
      .filter(x => x != null);
    return l.length ? Math.max(...l) : null;
  }

  function stils(f) {
    const lim = limenis(dati?.regioni[f.id]?.dienas[diena]);
    const izcelts = aktivie.includes(f.id);
    return {
      color: izcelts ? '#0f172a' : '#64748b', weight: izcelts ? 2.5 : 0.6, opacity: 0.8,
      fillColor: lim == null ? '#ffffff' : KRASAS[lim], fillOpacity: lim == null ? 0 : lim === 0 ? 0.25 : 0.4,
    };
  }

  function avots(a) {
    return `<small class="avots-rinda">Avots: <a href="${esc(a.url)}" target="_blank" rel="noopener">${esc(a.nosaukums)}</a> · ${esc(a.licence)}</small>`;
  }

  function popups(f, ll) {
    const r = dati?.regioni[f.id];
    const d = r?.dienas[diena];
    if (!d) return;
    const dn = dati.dienas.find(x => x.datums === diena)?.nosaukums || diena;
    const lim = limenis(d);
    L.popup().setLatLng(ll).setContent(`<div class="popup"><b>${esc(r.nosaukums)}</b>${esc(dn)}: ${esc(d.laiks || '')}<br>` +
      `${sk(d.tmin)}…${sk(d.tmax)} °C · brāzmas līdz ${sk(d.brazmas)} m/s${d.brazmas_vieta ? ` (${esc(d.brazmas_vieta)})` : ''}<br>` +
      `nokrišņi līdz ${sk(d.nokrisni)} mm${d.nokrisni_vieta ? ` (${esc(d.nokrisni_vieta)})` : ''}` +
      `${lim != null ? `<br><small>Pēc mūsu sliekšņiem: ${LIMENI[lim]}</small>` : ''}` +
      `<span class="popup-avots">${avots({ url: 'https://data.gov.lv/dati/lv/dataset/meteorologiskas-prognozes-apdzivotam-vietam-jaunaka-datu-kopa', nosaukums: `LVĢMC prognoze, ${d.vietas} apdzīvotas vietas`, licence: 'CC0 1.0' })}</span></div>`)
      .openOn(karte);
  }

  function zinasHtml() {
    const z = dati.zinas.filter(z => z.veids === 'bridinajums' || z.datums === diena);
    if (!z.length) return '<p class="piezime">Šai dienai ziņu nav.</p>';
    return '<ul class="prog-saraksts">' + z.map(z => `<li class="prog-zina lim-${z.limenis}" data-i="${dati.zinas.indexOf(z)}"` +
      `${z.bbox ? ' tabindex="0"' : ''}>` +
      `<span class="prog-veids">${z.veids === 'bridinajums' ? '⚠ LVĢMC brīdinājums' : z.veids === 'kopsavilkums' ? 'Prognoze' : 'Prognoze · ' + LIMENI[z.limenis]}</span>` +
      `<b>${esc(z.virsraksts)}</b><span class="prog-teksts">${esc(z.teksts)}</span>${avots(z.avots)}</li>`).join('') + '</ul>';
  }

  function zimet() {
    const bridinajumi = dati.zinas.filter(z => z.veids === 'bridinajums').length;
    const svarigas = dati.zinas.filter(z => z.limenis >= 1 && (z.veids === 'bridinajums' || z.datums === dati.dienas[0]?.datums || z.datums === dati.dienas[1]?.datums)).length;
    kaste.querySelector('.prog-poga-teksts').textContent = `Prognoze${svarigas ? ' · ' + svarigas : ''}`;
    kaste.querySelector('.prog-poga').classList.toggle('ir-bridinajumi', bridinajumi > 0);
    kaste.querySelector('.prog-dienas').innerHTML = dati.dienas.map(d =>
      `<button type="button" data-diena="${d.datums}" aria-pressed="${d.datums === diena}" class="${d.datums === diena ? 'aktiva' : ''}">${esc(d.nosaukums)}</button>`).join('');
    kaste.querySelector('.prog-saturs').innerHTML = zinasHtml() +
      `<p class="piezime">Krāsas kartē: dienas lielākās brāzmas, nokrišņi un temperatūra novadā pēc LVĢMC prognozes 6 427 vietām; ` +
      `sliekšņi ir mūsu (dzeltens ≈ brāzmas no 20 m/s vai nokrišņi no 15 mm), tas <b>nav oficiāls brīdinājums</b>. ` +
      `Raustīta līnija: spēkā esoša LVĢMC brīdinājuma teritorija.` +
      `${dati.prognoze_mainita ? ` Prognoze atjaunota ${esc(new Date(dati.prognoze_mainita).toLocaleString('lv-LV', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' }))}.` : ''}</p>`;
    novaduSlanis.setStyle(stils);
  }

  function zimetBridinajumus() {
    bridSlanis.clearLayers();
    for (const p of dati.bridinajumu_poligoni) {
      L.polygon(p.poligons, { color: KRASAS[p.limenis] === KRASAS[1] ? '#a16207' : KRASAS[p.limenis], weight: 2.5, dashArray: '6 5', fill: false, interactive: false })
        .addTo(bridSlanis);
    }
  }

  function radit(z) {
    aktivie = z.regioni || [];
    novaduSlanis.setStyle(stils);
    if (!z.bbox) return;
    const [x1, y1, x2, y2] = z.bbox;
    const lapa = kaste.querySelector('.prog-panelis');
    const telefons = matchMedia('(max-width: 800px)').matches;
    karte.fitBounds([[y1, x1], [y2, x2]], {
      paddingTopLeft: [telefons ? 10 : lapa.offsetWidth + 20, 10],
      paddingBottomRight: [50, telefons ? lapa.offsetHeight + 10 : 10], maxZoom: 10,
    });
  }

  async function ieladet() {
    try {
      const [p, r] = await Promise.all([
        fetch('/api/prognozes').then(r => r.ok ? r.json() : Promise.reject(r.status)),
        robezas || fetch('/api/prognozes/robezas').then(r => r.ok ? r.json() : null).catch(() => null),
      ]);
      dati = p;
      if (r && !robezas) { robezas = r; novaduSlanis.addData(r); }
      if (!diena || !dati.dienas.some(d => d.datums === diena)) diena = dati.dienas[1]?.datums || dati.dienas[0]?.datums;
      zimetBridinajumus();
      zimet();
      kaste.hidden = false;
    } catch (e) {
      if (!dati) kaste.hidden = true;  // nav datu — poga nav redzama, karte strādā kā līdz šim
    }
  }

  function atvert(atvert) {
    kaste.classList.toggle('atverts', atvert);
    kaste.querySelector('.prog-poga').setAttribute('aria-expanded', atvert);
    kaste.querySelector('.prog-panelis').hidden = !atvert;
    if (atvert) { novaduSlanis.addTo(karte); bridSlanis.addTo(karte); }
    else { novaduSlanis.remove(); bridSlanis.remove(); aktivie = []; }
  }

  kaste.querySelector('.prog-poga').addEventListener('click', () => atvert(!kaste.classList.contains('atverts')));
  kaste.querySelector('.prog-aizvert').addEventListener('click', () => atvert(false));
  kaste.querySelector('.prog-dienas').addEventListener('click', e => {
    const b = e.target.closest('[data-diena]');
    if (!b) return;
    diena = b.dataset.diena;
    aktivie = [];
    zimet();
  });
  const izveleties = e => {
    if (e.target.closest('a')) return;
    const li = e.target.closest('.prog-zina[tabindex]');
    if (!li) return;
    kaste.querySelectorAll('.prog-zina.izvelets').forEach(x => x.classList.remove('izvelets'));
    li.classList.add('izvelets');
    radit(dati.zinas[+li.dataset.i]);
  };
  kaste.querySelector('.prog-saturs').addEventListener('click', izveleties);
  kaste.querySelector('.prog-saturs').addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); izveleties(e); } });

  kaste.addEventListener('keydown', e => {
    if (e.key === 'Escape' && kaste.classList.contains('atverts')) { atvert(false); kaste.querySelector('.prog-poga').focus(); }
  });

  // Meklējot rezultāts ir galvenais: lente aizveras, lai neaizsedz karti
  document.getElementById('meklet-forma')?.addEventListener('submit', () => atvert(false));

  ieladet().then(() => { if (dati && !matchMedia('(max-width: 800px)').matches) atvert(true); });
  setInterval(ieladet, 15 * 60 * 1000);
  return { atvert, ieladet };
})();
