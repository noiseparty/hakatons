// Sistēmu statuss (/api/statuss): kartes un tās datu avotu pārbaužu rezultāti, 96 intervāli pa 15 min (24 h).
// Testam: statuss.html?dati=/<ceļš> pārraksta datu adresi (tikai šī paša servera ceļš).
(() => {
  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const saite = (url, teksts) => /^https?:\/\//.test(url || '')
    ? `<a href="${esc(url)}" target="_blank" rel="noopener">${esc(teksts)}</a>` : esc(teksts);
  const tests = new URLSearchParams(location.search).get('dati') || '';
  const adrese = /^\/(?!\/)/.test(tests) ? tests : '/api/statuss';
  const PERIODS = 60000;

  const VARDI = { darbojas: 'Darbojas', traucejumi: 'Traucējumi', nedarbojas: 'Nedarbojas', nav_datu: 'Nav datu' };
  const IKONAS = { darbojas: '✓', traucejumi: '!', nedarbojas: '✕', nav_datu: '–' };

  const el = id => document.getElementById(id);
  const stunda = iso => iso ? new Date(iso).toLocaleTimeString('lv-LV', { hour: '2-digit', minute: '2-digit' }) : '';
  const dec = (x, d) => x.toLocaleString('lv-LV', { minimumFractionDigits: d, maximumFractionDigits: d });
  const proc = x => x == null ? '—' : dec(x, 1) + ' %';

  function joslasTeksts(j, min) {
    const sak = new Date(j.sakums);
    const beigas = new Date(sak.getTime() + min * 60000);
    return `${stunda(j.sakums)}–${stunda(beigas.toISOString())} · ${VARDI[j.stavoklis] || 'Nav datu'}`;
  }

  function komponents(k, min) {
    const st = VARDI[k.stavoklis] ? k.stavoklis : 'nav_datu';
    const joslas = k.joslas || [];
    const ok = joslas.filter(j => j.stavoklis === 'darbojas').length;
    const av = k.avots;
    const avotaRinda = av ? `<p class="avots">Avots: ${saite(av.url, av.nosaukums)}${av.licence ? ` · ${saite(av.licences_url, av.licence)}` : ''}</p>` : '';
    const laiks = k.parbaudits
      ? `<p class="laiks">Pārbaudīts ${stunda(k.parbaudits)}${k.ilgums_ms != null ? ` (${dec(k.ilgums_ms / 1000, 1)} s)` : ''}</p>` : '';
    const segm = joslas.map((j, i) =>
      `<i class="${esc(j.stavoklis || 'nav')}" data-i="${i}" title="${esc(joslasTeksts(j, min))}"></i>`).join('');
    return `<article class="komp" data-kods="${esc(k.kods)}">
      <div class="komp-augsa">
        <div><h2>${esc(k.nosaukums)}</h2>${k.apraksts ? `<p class="apraksts">${esc(k.apraksts)}</p>` : ''}</div>
        <span class="pill ${st}"><span aria-hidden="true">${IKONAS[st]}</span> ${VARDI[st]}</span>
      </div>
      ${k.zinojums ? `<p class="zinojums">${esc(k.zinojums)}</p>` : ''}
      ${avotaRinda}${k.rezerves ? `<p class="avots">Rezerves avots: ${saite(k.rezerves.url, 'Meteoalarm')} (EUMETNET) — brīdinājumu joslā tagad rāda LVĢMC brīdinājumus caur Meteoalarm</p>` : ''}${laiks}
      <div class="josla" role="img" aria-label="Pēdējās 24 stundas: ${ok} no ${joslas.length} intervāliem darbojās">${segm}</div>
      <div class="josla-uzraksti"><span>pirms 24 h</span><b>7 dienās: ${proc(k.pieejamiba_7d)}</b><span>tagad</span></div>
      <p class="detala" aria-live="polite"></p>
    </article>`;
  }

  function baneris(komp) {
    const b = el('baneris');
    const nos = st => komp.filter(k => k.stavoklis === st).map(k => k.nosaukums).join(', ');
    let kl = 'ok', t = 'Visas sistēmas darbojas';
    if (komp.some(k => k.stavoklis === 'nedarbojas')) { kl = 'kluda'; t = 'Nedarbojas: ' + nos('nedarbojas'); }
    else if (komp.some(k => k.stavoklis === 'traucejumi')) { kl = 'dalejs'; t = 'Daļējie traucējumi: ' + nos('traucejumi'); }
    else if (!komp.length || komp.every(k => k.stavoklis === 'nav_datu' || !VARDI[k.stavoklis])) { kl = 'nav'; t = 'Nav datu'; }
    b.className = 'baneris ' + kl;
    b.textContent = t;
  }

  function zimet(d) {
    const komp = d.komponenti || [];
    const min = d.intervals_min || 15;
    baneris(komp);
    const p = el('pedeja');
    const pedeja = komp.map(k => k.parbaudits).filter(Boolean).sort().pop() || d.laiks;
    p.hidden = false;
    p.innerHTML = `${pedeja ? `Pēdējā pārbaude: ${stunda(pedeja)}` : ''}<small>Pārbaudes ik ${min} minūtes; lapa atjaunojas ik minūti.</small>`;
    el('komponenti').innerHTML = komp.map(k => komponents(k, min)).join('');
    el('komponenti')._dati = Object.fromEntries(komp.map(k => [k.kods, k]));
    el('komponenti')._min = min;
  }

  function kluda() {
    const b = el('baneris');
    b.className = 'baneris kluda';
    b.textContent = 'Statusa API nav pieejams — karte, iespējams, darbojas daļēji.';
    const p = el('pedeja');
    p.hidden = false;
    p.innerHTML = '<small>Mēģināsim vēlreiz pēc minūtes.</small>';
  }

  async function ieladet() {
    try {
      const r = await fetch(adrese, { cache: 'no-store' });
      if (!r.ok) throw new Error(r.status);
      zimet(await r.json());
    } catch (e) {
      // veco datu vietā neko nerādām: kļūda ir svarīgāka par novecojušu statusu
      el('komponenti').innerHTML = '';
      kluda();
    }
  }

  // Pieskāriens joslas intervālam parāda tā aprakstu zem joslas (uz skārienekrāna nav hover).
  el('komponenti').addEventListener('click', e => {
    const s = e.target.closest('.josla i');
    if (!s) return;
    const art = s.closest('.komp');
    const k = el('komponenti')._dati?.[art.dataset.kods];
    if (!k) return;
    art.querySelectorAll('.izv').forEach(x => x.classList.remove('izv'));
    s.classList.add('izv');
    art.querySelector('.detala').textContent = joslasTeksts(k.joslas[+s.dataset.i], el('komponenti')._min);
  });

  ieladet();
  setInterval(() => { if (!document.hidden) ieladet(); }, PERIODS);
  document.addEventListener('visibilitychange', () => { if (!document.hidden) ieladet(); });
})();
