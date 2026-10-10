// Kopīgā kājene visām publiskajām lapām (index, info, statuss, trukstosie): "Par datiem · Statuss · Svarīgi · #"
// un licences rinda. Kartes lapā tā ir paneļa apakšā; saites ./#datu-avoti un ./#kas-jauns atver "Datu avoti" sadaļu
// un "Kas jauns" logu (izmainas.js). Slaidos (slaidi.html) tā pati rinda ir pēdējā slaidā.
(() => {
  const kartesLapa = !!document.getElementById('panelis');
  const uz = kartesLapa ? '' : 'map';  // kartes lapā tikai #…, lai neiet caur sākumlapu (/ → /map pāradresācija)
  const k = document.createElement('footer');
  k.className = 'kajene';
  k.innerHTML = `
    <nav aria-label="Lapas saites" data-t-aria="Lapas saites">
      <a href="${uz}#datu-avoti" data-t="Par datiem">Par datiem</a> · <a href="statuss.html" data-t="Statuss">Statuss</a> · <a href="info.html" data-t="Svarīgi">Svarīgi</a> ·
      <a href="${uz}#kas-jauns" title="Kas jauns (izmaiņu žurnāls)" aria-label="Kas jauns" data-t-title="Kas jauns (izmaiņu žurnāls)" data-t-aria="Kas jauns">#</a>
    </nav>
    <p><span data-t="Dati: katram avotam sava licence, norādīta pie avota (CC0, CC BY 4.0, ODbL vai oficiāls dokuments);">Dati: katram avotam sava licence, norādīta pie avota (CC0, CC BY 4.0, ODbL vai oficiāls dokuments);</span>
      <svg class="ik" aria-hidden="true" focusable="false"><use href="ikonas/ikonas.svg#uzmanibu"></use></svg> <span data-t="patvertņu sarakstam licence nav norādīta.">patvertņu sarakstam licence nav norādīta.</span> <span data-t="Iedzīvotāju ziņojumi — CC BY 4.0.">Iedzīvotāju ziņojumi — CC BY 4.0.</span> map.repo.lv · <span data-t="AI atvērto datu hakatons 2026.">AI atvērto datu hakatons 2026.</span></p>`;
  const stils = document.createElement('style');
  stils.textContent = `
    .kajene .ik { width: 1em; height: 1em; vertical-align: -.15em; }
    .kajene { font-size: 12.5px; line-height: 1.45; color: #5c6670; text-align: center; padding: 14px 12px 18px; }
    .kajene nav { margin-bottom: 4px; font-size: 14px; }
    .kajene a { color: #005a99; }
    .kajene nav a { display: inline-block; padding: 12px 8px; margin: -6px 0; }  /* pieskāriena mērķis ≥ 44 px, arī "#" */
    .kajene p { margin: 0 auto; max-width: 60ch; }
    #panelis .kajene { padding: 10px 4px 4px; text-align: left; }
    @media print { .kajene nav { display: none; } }`;
  document.head.appendChild(stils);
  (kartesLapa ? document.getElementById('panelis') : document.body).appendChild(k);

  if (!kartesLapa) return;
  // Saites no citām lapām: ./#datu-avoti, ./#kas-jauns
  function hash() {
    if (location.hash === '#datu-avoti' || location.hash === '#avoti') {
      const p = document.getElementById('panelis-poga');
      const lapa = typeof Apaksa !== 'undefined' && Apaksa.aktiva();
      // telefonā / planšetē panelis ir apakšējās lapas cilnē "Kartes slāņi" (sheet.js): cilne + lapa "Pilns", tad ritina
      if (lapa) { if (typeof Lapa !== 'undefined' && Lapa) Lapa.cilne('slani'); Apaksa.atvert('pilna'); }
      else if (document.body.classList.contains('panelis-slegts') && p) p.click();
      // darbvirsmā Slāņu vadības atvilktne (darbvirsma.js) ir aizvērta un "Datu avoti" tajā neredzami: atver to
      const at = document.getElementById('dv-atvilktne');
      if (!lapa && at && at.hidden) document.querySelector('[data-dv="slani"]')?.click();
      const d = document.getElementById('avoti');
      if (d) {
        d.open = true;
        setTimeout(() => {
          d.scrollIntoView({ block: 'start' });
          const s = document.getElementById('apaksa-saturs');
          if (lapa && s && s.contains(d)) s.scrollTop -= 52;  // zem pielipušās ciļņu rindas
        }, lapa ? 420 : 250);
        // darbvirsmā atvilktne un avotu saraksts ielādējas/animējas vēlāk: ritina vēlreiz, kad izkārtojums nostabilizējies
        if (!lapa) setTimeout(() => d.scrollIntoView({ block: 'start' }), 1200);
      }
    } else if (location.hash === '#kas-jauns') {
      document.getElementById('izmainas-poga')?.click();
    }
    // hash notīra, lai atkārtots klikšķis uz tās pašas saites atkal strādātu (replaceState hashchange nesauc)
    if (location.hash === '#datu-avoti' || location.hash === '#kas-jauns') history.replaceState(null, '', location.pathname + location.search);
  }
  // Telefonā #izmainas-poga ir paslēpta: pēc loga aizvēršanas fokuss atgriežas pie "#" saites, kas to atvēra
  let atvereja = null;
  document.addEventListener('click', e => { const a = e.target.closest && e.target.closest('a[href$="#kas-jauns"]'); if (a) atvereja = a; }, true);
  const logs = document.getElementById('izmainas');
  if (logs) logs.addEventListener('close', () => {
    const p = document.getElementById('izmainas-poga');
    if (atvereja && atvereja.isConnected && !(p && p.offsetParent)) atvereja.focus();
    atvereja = null;
  });
  window.addEventListener('hashchange', hash);
  // tā pati saite vēlreiz (hash nemainās, hashchange nenotiek)
  document.addEventListener('click', e => { if (e.target.closest('.kajene a[href$="#datu-avoti"]')) setTimeout(hash, 0); });
  window.addEventListener('load', () => setTimeout(hash, 300));
})();
