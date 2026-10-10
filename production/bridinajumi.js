// LVĢMC hidrometeoroloģisko brīdinājumu josla lapas augšā (/api/bridinajumi, data.gov.lv, CC0).
// Bez vietas — visi spēkā esošie; ar vietu (meklēšanas sākumpunkts) — tikai tie, kas attiecas uz to.
// Ja LVĢMC datne nav pieejama, API atbild no rezerves avota Meteoalarm (rezerves: true): tad josla nosauc LVĢMC kā
// izdevēju, rāda izdošanas laiku, saiti uz meteoalarm.org un Meteoalarm atrunu (to noteikumi, notes/research/04).
// Ja galapunkts nav pieejams, josla vienkārši nav redzama.
const Bridinajumi = (() => {
  const LIMENIS = { 1: ['dzeltens', 'Dzeltenais'], 2: ['oranzs', 'Oranžais'], 3: ['sarkans', 'Sarkanais'] };
  const AVOTS = '<a href="https://data.gov.lv/dati/lv/dataset/hidrometeorologiskie-bridinajumi" target="_blank" rel="noopener">LVĢMC hidrometeoroloģiskie brīdinājumi</a> · CC0';
  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const laiks = iso => new Date(iso).toLocaleString('lv-LV', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' });
  // Meteoalarm (rezerves avots): izdevējs, saite un atruna, kā prasa Meteoalarm noteikumi
  const MA = '<a href="https://www.meteoalarm.org" target="_blank" rel="noopener">www.meteoalarm.org</a>';
  const rezervesAvots = d => `Avots: LVĢMC, caur Meteoalarm (EUMETNET), ${MA} · CC BY 4.0. Rezerves avots: LVĢMC datne šobrīd ` +
    `nav pieejama. Iespējama kavēšanās; jaunākā informācija — ${MA}.` + (d.atruna ? ` <span lang="en">${esc(d.atruna)}</span>` : '');
  // Meteoalarm apgabalu var būt daudz (pa novadam): joslā pirmie 3
  const apgabali = b => {
    const a = b.apgabali || [];
    return a.length > 3 ? `${a.slice(0, 3).join(', ')} u. c. (${a.length})` : b.regioni;
  };
  let pieprasijums = null, pedeja = [null, null];
  // Aizvērtie brīdinājumi (id|līmenis) — tikai atmiņā, līdz lapas pārlādei; jauns vai augstāka līmeņa brīdinājums rādās.
  const aizvertie = new Set();
  const atslega = b => b.id + '|' + b.limenis;
  // Poga "Situācija" galvenē: skaits ar aktīvajiem brīdinājumiem Latvijā (krāsa pēc augstākā līmeņa); 0 — nozīme paslēpta
  function nozime(n, max) {
    const e = document.getElementById('situacija-nozime'), poga = document.getElementById('situacija-poga');
    if (!e || !poga) return;
    e.hidden = !n;
    e.textContent = n || '';
    e.dataset.limenis = max || 0;
    poga.setAttribute('aria-label', 'Situācija tagad — Latvija' + (n ? `: ${n} brīdinājum${n === 1 ? 's' : 'i'}` : ''));
  }
  // LVĢMC teksta sākumā mēdz būt kampaņas sauklis "ESI INFORMĒTS par …!" (uzruna "tu"): UI to nerāda, paliek pats brīdinājums
  const bezSlogana = s => String(s).replace(/^\s*ESI INFORMĒTS[^!\n]*!\s*/i, '');

  async function atjaunot(vieta, nosaukums) {
    const josla = document.getElementById('bridinajums');
    pedeja = [vieta, nosaukums];
    if (pieprasijums) pieprasijums.abort();
    pieprasijums = new AbortController();
    const q = vieta ? '?' + new URLSearchParams({ lat: (+vieta.lat).toFixed(5), lon: (+vieta.lon).toFixed(5) }) : '';
    try {
      const r = await fetch('/api/bridinajumi' + q, { signal: pieprasijums.signal });
      if (!r.ok) throw new Error(r.status);
      const d = await r.json(), visi = d.bridinajumi, rez = !!d.rezerves;
      // rezerves avotam attiecas var būt null (vietu neizdevās pārbaudīt): tad brīdinājumu rāda, nevis slēpj
      const attiecas = vieta ? visi.filter(b => rez ? b.attiecas !== false : b.attiecas) : visi;
      const sheit = attiecas.filter(b => !aizvertie.has(atslega(b)));
      const max = Math.max(0, ...sheit.map(b => b.limenis));
      if (!vieta) nozime(visi.length, Math.max(0, ...visi.map(b => b.limenis)));  // skaitlis uz pogas "Situācija" galvenē
      const kur = vieta ? (nosaukums ? esc(nosaukums) : 'Šajā vietā') : 'Latvijā';
      const piezime = rez ? ' <small class="rezerves">(rezerves avots: Meteoalarm)</small>' : '';
      if (aizvertie.size && !sheit.length) { josla.hidden = true; josla.innerHTML = ''; return; }  // lietotājs aizvēra joslu: arī „brīdinājumu nav” (zaļā) josla vairs neatgriežas, kamēr nav jauna/augstāka līmeņa brīdinājuma
      josla.dataset.atslegas = JSON.stringify(sheit.map(atslega));
      josla.className = 'bridinajums ' + (max ? LIMENIS[max][0] : 'zals');
      josla.innerHTML = !sheit.length
        ? `<span>${Ik('ok')} ${kur}: LVĢMC brīdinājumu šobrīd nav${vieta && visi.length ? ` <small>(citur Latvijā: ${visi.length})</small>` : ''}${piezime}</span>`
        : `<details><summary>${Ik('brid')} ${vieta ? kur + ': ' : ''}${sheit.map(b => `${LIMENIS[b.limenis]?.[1] || esc(b.krasa)} brīdinājums: ` +
            `${esc(b.paradiba.toLowerCase())}${b.regioni && !vieta ? ` (${esc(apgabali(b))})` : ''}${b.lidz ? `, līdz ${laiks(b.lidz)}` : ''}`).join(' · ')}${piezime}</summary>` +
          sheit.map(b => (rez && b.notikums ? `<p><b>${esc(b.notikums)}</b>${b.regioni ? ` — ${esc(b.regioni)}` : ''}</p>` : '') +
            (b.teksts ? `<p>${esc(bezSlogana(b.teksts))}</p>` : '') +
            (b.riski ? `<p class="riski">${esc(bezSlogana(b.riski)).replace(/\n/g, '<br>')}</p>` : '') +
            (rez && b.izdots ? `<p class="riski">Izdots ${laiks(b.izdots)}</p>` : '')).join('') +
          `<p class="avots-rinda">${rez ? rezervesAvots(d) : 'Avots: ' + AVOTS}</p>` +
          `<button type="button" class="otra brid-aizvert">${Ik('aizvert')} ${Valoda.t('Aizvērt')}</button></details>` +
          `<button type="button" class="brid-x" aria-label="${Valoda.t('Aizvērt brīdinājumu joslu')}">${Ik('aizvert')}</button>`;  // telefonā: atvērtā josla sedz karti
      josla.hidden = false;
    } catch (e) {
      if (e.name !== 'AbortError') josla.hidden = true;
    }
  }

  document.getElementById('bridinajums')?.addEventListener('click', e => {
    if (!e.target.closest('.brid-aizvert, .brid-x')) return;
    const d = e.currentTarget.querySelector('details');
    if (d) d.open = false;
    try { JSON.parse(e.currentTarget.dataset.atslegas || '[]').forEach(k => aizvertie.add(k)); } catch {}
    atjaunot(...pedeja);
  });
  setInterval(() => atjaunot(...pedeja), 5 * 60e3);
  atjaunot(null);
  return { atjaunot, aizvertie };
})();
