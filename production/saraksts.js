// "Saraksts": kartes skatā ieslēgto slāņu objekti (app.js `skataObjekti`) kā teksta saraksts dialoglodziņā — karte bez redzes,
// ar tastatūru vai mazā ekrānā. Atver poga slāņu panelī un rezultāta kartītē (data-darbiba="saraksts").
// Katram objektam: nosaukums, slānis, attālums, adrese, avots un licence, maršruta saites, "Rādīt kartē".
const Saraksts = (() => {
  const SOLIS = 100;  // cik rādīt uzreiz; pārējie ar pogu "Rādīt vēl"
  let dialogs, ul, kopsavilkums, velPoga, saraksts = [], paradits = 0;

  function izveidot() {
    dialogs = document.createElement('dialog');
    dialogs.id = 'saraksts-dialogs';
    dialogs.className = 'saraksts-dialogs';
    dialogs.setAttribute('aria-labelledby', 'saraksts-virsraksts');
    dialogs.innerHTML = `
      <div class="saraksts-galva">
        <h2 id="saraksts-virsraksts">Saraksts</h2>
        <button type="button" class="saraksts-aizvert" aria-label="Aizvērt sarakstu">✕</button>
      </div>
      <p id="saraksts-kopsavilkums" class="piezime" aria-live="polite"></p>
      <ul class="saraksts-ul"></ul>
      <button type="button" class="otra saraksts-vel" hidden></button>`;
    document.body.appendChild(dialogs);
    ul = dialogs.querySelector('.saraksts-ul');
    kopsavilkums = dialogs.querySelector('#saraksts-kopsavilkums');
    velPoga = dialogs.querySelector('.saraksts-vel');
    dialogs.querySelector('.saraksts-aizvert').addEventListener('click', () => dialogs.close());
    velPoga.addEventListener('click', () => paradit(SOLIS));
    dialogs.addEventListener('click', e => {
      const poga = e.target.closest('[data-objekts]');
      if (poga) {
        const f = saraksts[+poga.dataset.objekts];
        dialogs.close();
        if (f && f._slanis) atvertObjektu(f);
      } else if (e.target === dialogs) dialogs.close();  // klikšķis ārpus satura
    });
  }

  function vienums(f, i) {
    const p = f.properties;
    const [lon, lat] = f.geometry.coordinates;
    const k = kategorijas[p.kategorija] || {};
    const nos = nosaukums(p) || k.nosaukums || 'Objekts';
    const att = p.attalums_m != null ? ` · ${attalums(p.attalums_m)} ${stavoklis.vieta?.adrese ? 'no adreses' : 'no Jums'}` : '';
    return `<li>
      <h3>${esc(nos)}</h3>
      <p class="saraksts-meta">${esc(k.nosaukums || '')}${att}</p>
      ${p.adrese ? `<p>${esc(p.adrese)}</p>` : ''}
      ${marsrutaSaites(lat, lon, stavoklis.vieta)}
      ${Avoti.rinda(p.avots)}
      <button type="button" class="otra saraksts-karte" data-objekts="${i}">Rādīt kartē<span class="vizuali-slepts">: ${esc(nos)}</span></button>
    </li>`;
  }

  function paradit(cik) {
    const lidz = Math.min(saraksts.length, paradits + cik);
    ul.insertAdjacentHTML('beforeend', saraksts.slice(paradits, lidz).map((f, j) => vienums(f, paradits + j)).join(''));
    paradits = lidz;
    const atlikums = saraksts.length - paradits;
    velPoga.hidden = atlikums <= 0;
    velPoga.textContent = `Rādīt vēl ${Math.min(SOLIS, atlikums)} (kopā ${saraksts.length})`;
  }

  function atvert() {
    if (!dialogs) izveidot();
    saraksts = skataObjekti();  // app.js: ielādētie punkti, kas ir kartes skatā
    paradits = 0;
    ul.innerHTML = '';
    const slani = [...stavoklis.kategorijas].map(k => kategorijas[k]?.nosaukums).filter(Boolean);
    if (!saraksts.length) {
      kopsavilkums.textContent = slani.length
        ? 'Ieslēgtajos slāņos kartes skatā objektu nav. Attāliniet vai pārvietojiet karti.'
        : 'Nav ieslēgts neviens slānis. Ieslēdziet slāni panelī „Slāņi” vai meklējiet augšā.';
    } else {
      const kartiba = stavoklis.vieta ? 'sakārtoti pēc attāluma (taisnā līnijā)' : 'sakārtoti pēc nosaukuma';
      const izlase = ieladets?.apgriezts ? ' (izlase: pietuviniet karti, lai redzētu visus)' : '';
      kopsavilkums.textContent = `${saraksts.length} objekti kartes skatā${izlase}, ${kartiba}. Slāņi: ${slani.join(', ')}.`;
      paradit(SOLIS);
    }
    dialogs.showModal();
    dialogs.querySelector('.saraksts-aizvert').focus();
  }

  document.addEventListener('click', e => {
    if (e.target.closest('[data-darbiba="saraksts"]')) atvert();
  });

  return { atvert };
})();
