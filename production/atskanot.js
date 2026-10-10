// Atskaņošana prezentācijai: demo scenāriji pēc kārtas (pa 20 s), katram arī tipiskais meklēšanas vaicājums, lai
// redzama rezultāta kartīte. Poga "▶ Atskaņot" demo paneļa galvā vai saite ?demo=atskanot[&saraksts=a,b,c&ilgums=20].
// Taustiņi (datorā): atstarpe — pauze, → nākamais, ← iepriekšējais, Escape — beigt. Beigās "Beigt demo".
// Lieto demo.js publiskās funkcijas (Demo.sakt, Demo.beigt, Demo.atvert) un meklesana.js (krizesMeklesana.meklet);
// demo.js netiek mainīts. Vaicājums: scenārija lauks `vaicajums` (demo/scenariji.json), ja ir, citādi VAICAJUMI.
const Atskanot = (() => {
  if (typeof Demo === 'undefined') return null;
  const NOKLUSETAIS = ['vetra-2026', 'pludi-ogre', 'drons', 'bez-sakariem'];
  const VAICAJUMI = {
    'vetra-2026': 'vētra Bauskā', 'pludi-ogre': 'plūdi Ogrē', drons: 'drons Rēzeknē', 'bez-sakariem': 'nav elektrības Rīgā',
    vetra: 'vētra Rīgā', vejs: 'stiprs vējš Liepājā', nakts: 'sagriezta roka Saulkrastos',
  };
  const q = new URLSearchParams(location.search);
  const saraksts = (q.get('saraksts') || '').split(',').map(s => s.trim()).filter(Boolean);
  const SARAKSTS = saraksts.length ? saraksts : NOKLUSETAIS;
  const ILGUMS = Math.min(120, Math.max(5, +q.get('ilgums') || 20)) * 1000;
  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

  let dati = null, solis = -1, sakums = 0, atlikums = ILGUMS, pauze = false, taimeris = null, aktivs = false, paaudze = 0;

  // Josla kartes augšā: nosaukums, solis, atpakaļskaitīšana, progress, pogas
  el('kartes-laukums').insertAdjacentHTML('beforeend', `
    <div id="atskanot-josla" class="atskanot-josla" role="region" aria-label="Demo atskaņošana" hidden>
      <div class="atskanot-teksts"><span class="atskanot-solis"></span> <b class="atskanot-nos"></b>
        <span class="atskanot-laiks" aria-live="off"></span></div>
      <div class="atskanot-progress" aria-hidden="true"><span></span></div>
      <div class="atskanot-pogas">
        <button type="button" data-a="ieprieks" aria-label="Iepriekšējais scenārijs">⏮</button>
        <button type="button" data-a="pauze" aria-label="Pauze">⏸</button>
        <button type="button" data-a="nakamais" aria-label="Nākamais scenārijs">⏭</button>
        <button type="button" data-a="beigt" aria-label="Beigt atskaņošanu">■ Beigt</button>
      </div>
    </div>`);
  const josla = el('atskanot-josla');
  const progress = josla.querySelector('.atskanot-progress span');

  // Poga demo paneļa galvā (demo.js to nepārzīmē)
  document.querySelector('#demo-panelis .demo-galva')?.insertAdjacentHTML('afterend',
    '<div class="atskanot-rinda"><button type="button" class="atskanot-sakt">▶ Atskaņot visus pēc kārtas</button>' +
    '<small>pa ' + ILGUMS / 1000 + ' s; datorā atstarpe — pauze, ← → — iepriekšējais / nākamais</small></div>');
  document.querySelector('#demo-panelis .atskanot-sakt')?.addEventListener('click', () => sakt());

  async function ieladet() {
    if (!dati) {
      try { dati = await (await fetch('demo/scenariji.json')).json(); } catch { dati = { scenariji: [] }; }
    }
    return dati.scenariji.filter(s => SARAKSTS.includes(s.kods)).sort((a, b) => SARAKSTS.indexOf(a.kods) - SARAKSTS.indexOf(b.kods));
  }

  let soli = [];
  async function sakt() {
    soli = await ieladet();
    if (!soli.length) return;
    aktivs = true;
    josla.hidden = false;
    document.body.classList.add('atskano');
    iet(0);
  }

  async function iet(i) {
    if (!aktivs) return;
    if (i >= soli.length) return beigt();
    solis = Math.max(0, i);
    const sc = soli[solis], mana = ++paaudze;
    atlikums = ILGUMS;
    sakums = performance.now();
    zimet();
    // vispirms meklēšana (rezultāta kartīte), tad scenārijs — lai kartes skats paliek scenārija
    const vaicajums = sc.vaicajums || VAICAJUMI[sc.kods];
    if (vaicajums && typeof krizesMeklesana !== 'undefined') {
      el('jautajums').value = vaicajums;
      // lēns API nedrīkst aizturēt soli: gaidām līdz 6 s, kartīte ielādējas tālāk pati
      try { await Promise.race([krizesMeklesana.meklet(vaicajums), new Promise(r => setTimeout(r, 6000))]); } catch { /* kartīte nav obligāta */ }
    }
    if (mana !== paaudze || !aktivs) return;
    await Demo.sakt(sc.kods);
    if (mana !== paaudze || !aktivs) return;
    sakums = performance.now();  // laiks skaitās no brīža, kad scenārijs ir redzams
    clearInterval(taimeris);
    taimeris = setInterval(tiks, 250);
  }

  function tiks() {
    if (pauze || !aktivs) return;
    const pagajis = performance.now() - sakums;
    const palika = Math.max(0, atlikums - pagajis);
    progress.style.width = (100 * (1 - palika / ILGUMS)).toFixed(1) + '%';
    josla.querySelector('.atskanot-laiks').textContent = Math.ceil(palika / 1000) + ' s';
    if (palika <= 0) { clearInterval(taimeris); iet(solis + 1); }
  }

  function zimet() {
    const sc = soli[solis];
    josla.querySelector('.atskanot-solis').textContent = `${solis + 1}/${soli.length}`;
    josla.querySelector('.atskanot-nos').textContent = `${sc.ikona || ''} ${sc.nosaukums}`;
    josla.querySelector('.atskanot-laiks').textContent = Math.ceil(atlikums / 1000) + ' s';
    progress.style.width = '0%';
    const p = josla.querySelector('[data-a="pauze"]');
    p.textContent = pauze ? '▶' : '⏸';
    p.setAttribute('aria-label', pauze ? 'Turpināt' : 'Pauze');
  }

  function parslegtPauzi() {
    if (!aktivs) return;
    if (!pauze) atlikums -= performance.now() - sakums;  // atceras atlikušo laiku
    else sakums = performance.now();
    pauze = !pauze;
    josla.classList.toggle('pauze', pauze);
    const p = josla.querySelector('[data-a="pauze"]');
    p.textContent = pauze ? '▶' : '⏸';
    p.setAttribute('aria-label', pauze ? 'Turpināt' : 'Pauze');
  }

  function beigt() {
    aktivs = false;
    paaudze++;
    pauze = false;
    clearInterval(taimeris);
    josla.hidden = true;
    josla.classList.remove('pauze');
    document.body.classList.remove('atskano');
    Demo.beigt();
  }

  josla.addEventListener('click', e => {
    const a = e.target.closest('[data-a]')?.dataset.a;
    if (a === 'ieprieks') { pauze = false; iet(solis - 1); }
    if (a === 'nakamais') { pauze = false; iet(solis + 1); }
    if (a === 'pauze') parslegtPauzi();
    if (a === 'beigt') beigt();
  });
  document.addEventListener('keydown', e => {
    if (!aktivs || e.altKey || e.ctrlKey || e.metaKey) return;
    if (e.target.closest?.('input, textarea, select, [contenteditable]')) return;  // rakstot meklētājā — nē
    if (e.key === ' ') { e.preventDefault(); parslegtPauzi(); }
    else if (e.key === 'ArrowRight') { e.preventDefault(); pauze = false; iet(solis + 1); }
    else if (e.key === 'ArrowLeft') { e.preventDefault(); pauze = false; iet(solis - 1); }
    else if (e.key === 'Escape') beigt();
  });

  // ?demo=atskanot: sāk, kad kartes slāņi un reģioni ir ielādēti (kā demo.js ?demo=<kods>)
  if (q.get('demo') === 'atskanot') {
    const t0 = Date.now();
    (function gaidit() {
      const gatavs = typeof kategorijas !== 'undefined' && Object.keys(kategorijas).length && Object.keys(regioni).length;
      if (gatavs || Date.now() - t0 > 10000) sakt(); else setTimeout(gaidit, 200);
    })();
  }

  return { sakt, beigt, iet: i => iet(i), get solis() { return solis; }, get aktivs() { return aktivs; } };
})();
