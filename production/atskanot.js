// Atskaņošana prezentācijai: demo scenāriji pēc kārtas (pa 20 s), katram arī tipiskais meklēšanas vaicājums, lai
// redzama rezultāta kartīte ar lēmumu. Poga "Atskaņot" demo paneļa galvā vai saite ?demo=atskanot[&saraksts=a,b,c&ilgums=20].
// Noklusēti — visi demo/scenariji.json scenāriji paneļa secībā (Demo.kartiba: reālie notikumi pēc veida, tad simulācijas).
// Vadība galvenes rindā (n/19, iepriekšējais, pauze, nākamais, "Beigt demo"): tā neaizsedz karti, uznirstošos logus un
// apakšējās lapas lēmuma rindu; demo panelis atskaņošanas laikā aizvērts, telefonā lapa vismaz "Puse".
// Taustiņi (datorā): atstarpe — pauze, → nākamais, ← iepriekšējais, Escape — beigt.
// Lieto demo.js (Demo.sakt, Demo.beigt, Demo.atvert, Demo.kartiba), apaksa.js (Apaksa) un meklesana.js (krizesMeklesana.meklet).
// Vaicājums: scenārija lauks `vaicajums` (demo/scenariji.json), ja ir, citādi VAICAJUMI.
const Atskanot = (() => {
  if (typeof Demo === 'undefined') return null;
  const VAICAJUMI = {
    'vetra-2026': 'vētra Bauskā', 'pludi-ogre': 'plūdi Ogrē', drons: 'drons Rēzeknē', 'bez-sakariem': 'nav elektrības Rīgā',
    vetra: 'vētra Rīgā', vejs: 'stiprs vējš Liepājā', nakts: 'sagriezta roka Saulkrastos',
  };
  const q = new URLSearchParams(location.search);
  const saraksts = (q.get('saraksts') || '').split(',').map(s => s.trim()).filter(Boolean);
  const SARAKSTS = saraksts.length ? saraksts : null;  // null — visi paneļa secībā
  const ILGUMS = Math.min(120, Math.max(5, +q.get('ilgums') || 20)) * 1000;
  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

  let dati = null, solis = -1, sakums = 0, atlikums = ILGUMS, pauze = false, taimeris = null, aktivs = false, paaudze = 0;
  let sakumaPludi = false;  // plūdu slānis pirms atskaņošanas: katrs solis sākas no tā (citādi plūdu meklējums to atstāj ieslēgtu)
  let sakumaSlani = null;   // slāņi pirms atskaņošanas: Demo.beigt() atjauno tikai pēdējā soļa sākumu (ar iepriekšējā soļa slāņiem)
  const pludiKa = ieslegti => { if (typeof radtPludus === 'function' && el('pludu-slanis') && el('pludu-slanis').checked !== ieslegti) radtPludus(ieslegti); };

  // Josla galvenes rindā (pārklāj galvenes saturu, karte paliek brīva): solis, nosaukums, atpakaļskaitīšana, pogas, progress
  document.querySelector('header').insertAdjacentHTML('beforeend', `
    <div id="atskanot-josla" class="atskanot-josla" role="region" aria-label="Demo atskaņošana" hidden>
      <span class="demo-zime">SIMULĀCIJA</span>
      <span class="atskanot-solis"></span>
      <div class="atskanot-teksts"><b class="atskanot-nos"></b><span class="atskanot-laiks" aria-live="off"></span></div>
      <div class="atskanot-pogas">
        <button type="button" data-a="ieprieks" aria-label="Iepriekšējais scenārijs" title="Iepriekšējais (←)">${Ik('atpakal-solis')}</button>
        <button type="button" data-a="pauze" aria-label="Pauze" title="Pauze (atstarpe)">${Ik('pauze')}</button>
        <button type="button" data-a="nakamais" aria-label="Nākamais scenārijs" title="Nākamais (→)">${Ik('uz-prieksu')}</button>
        <button type="button" data-a="beigt" aria-label="Beigt demo" title="Beigt demo (Escape)">${Ik('apturet')}<span>Beigt demo</span></button>
      </div>
      <div class="atskanot-progress" aria-hidden="true"><span></span></div>
    </div>`);
  const josla = el('atskanot-josla');
  const progress = josla.querySelector('.atskanot-progress span');

  // Poga demo paneļa galvā (demo.js to nepārzīmē)
  document.querySelector('#demo-panelis .demo-galva')?.insertAdjacentHTML('afterend',
    '<div class="atskanot-rinda"><button type="button" class="atskanot-sakt">' + Ik('atskanot') + ' Atskaņot ' + (SARAKSTS ? 'izvēlētos' : 'visus') +
    ' pēc kārtas</button><small>pa ' + ILGUMS / 1000 + ' s katru; datorā atstarpe — pauze, ← → — iepriekšējais / nākamais</small></div>');
  document.querySelector('#demo-panelis .atskanot-sakt')?.addEventListener('click', () => sakt());

  async function ieladet() {
    if (!SARAKSTS) return Demo.kartiba();  // tā pati secība kā demo panelī
    if (!dati) {
      try { dati = await (await fetch('demo/scenariji.json')).json(); } catch { dati = { scenariji: [] }; }
    }
    return dati.scenariji.filter(s => SARAKSTS.includes(s.kods)).sort((a, b) => SARAKSTS.indexOf(a.kods) - SARAKSTS.indexOf(b.kods));
  }
  // Telefonā apakšējā lapa ar meklēšanas kartīti vismaz "Puse" (lēmuma rinda redzama); demo panelis aizvērts
  const lapaRedzama = () => {
    Demo.atvert(false);
    if (typeof Apaksa !== 'undefined' && Apaksa.aktiva() && Apaksa.stavoklis() === 'peek') Apaksa.atvert('puse');
  };

  let soli = [];
  async function sakt() {
    soli = await ieladet();
    if (!soli.length) return;
    if (!aktivs) {
      if (document.body.classList.contains('demo-aktivs')) Demo.beigt();  // sākts no atvērta scenārija
      sakumaPludi = !!el('pludu-slanis')?.checked;
      sakumaSlani = typeof stavoklis !== 'undefined' ? new Set(stavoklis.kategorijas) : null;
    }
    aktivs = true;
    josla.hidden = false;
    document.body.classList.add('atskano');
    lapaRedzama();
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
    if (document.body.classList.contains('demo-aktivs')) Demo.beigt();  // iepriekšējais scenārijs: slāņi kā pirms tā
    pludiKa(sakumaPludi);
    const vaicajums = sc.vaicajums || VAICAJUMI[sc.kods];
    // Katra kartīte stāv uz savas vietas: iepriekšējā soļa adrese/reģions prom, kartes centrs = scenārija `vieta`
    // (vaicājumi bez vietvārda, piem. "nestrādā e-pakalpojumi", citādi atkārtotu iepriekšējo vietu)
    if (typeof atmestAdresi === 'function') atmestAdresi();
    if (typeof stavoklis !== 'undefined' && stavoklis.regions && typeof radtRegionu === 'function') radtRegionu('');
    if (sc.vieta && typeof karte !== 'undefined') karte.setView([sc.vieta.lat, sc.vieta.lon], 11, { animate: false });
    if (vaicajums && typeof krizesMeklesana !== 'undefined') {
      el('jautajums').value = vaicajums;
      // lēns API nedrīkst aizturēt soli: gaidām līdz 6 s, kartīte ielādējas tālāk pati
      try { await Promise.race([krizesMeklesana.meklet(vaicajums), new Promise(r => setTimeout(r, 6000))]); } catch { /* kartīte nav obligāta */ }
    }
    if (mana !== paaudze || !aktivs) return;
    lapaRedzama();  // pirms Demo.sakt: skats pielāgojas lapas augstumam (Apaksa.atstarpes)
    await Demo.sakt(sc.kods, null, { panelis: false });
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
    josla.querySelector('.atskanot-nos').innerHTML = `${Ikonas.no(sc.ikona)} ${esc(sc.nosaukums)}`;
    josla.querySelector('.atskanot-laiks').textContent = Math.ceil(atlikums / 1000) + ' s';
    progress.style.width = '0%';
    const p = josla.querySelector('[data-a="pauze"]');
    p.innerHTML = Ik(pauze ? 'atskanot' : 'pauze');
    p.setAttribute('aria-label', pauze ? 'Turpināt' : 'Pauze');
  }

  function parslegtPauzi() {
    if (!aktivs) return;
    if (!pauze) atlikums -= performance.now() - sakums;  // atceras atlikušo laiku
    else sakums = performance.now();
    pauze = !pauze;
    josla.classList.toggle('pauze', pauze);
    const p = josla.querySelector('[data-a="pauze"]');
    p.innerHTML = Ik(pauze ? 'atskanot' : 'pauze');
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
    // Simulētais vaicājums, kartīte un scenāriju slāņi prom (meklesana.js "Notīrīt": viss uz sākumu), slāņi — kā pirms atskaņošanas
    el('notirit-meklesanu')?.click();
    if (sakumaSlani && typeof stavoklis !== 'undefined') {
      stavoklis.kategorijas = new Set(sakumaSlani);
      document.querySelectorAll('#kategorijas input').forEach(i => { i.checked = stavoklis.kategorijas.has(i.value); });
      if (typeof atjaunot === 'function') atjaunot();
    }
    sakumaSlani = null;
    pludiKa(sakumaPludi);
    el('jautajums')?.blur();  // "Notīrīt" fokusē lauku — pēc pogas "Beigt demo" tastatūrai nav jāatveras
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
