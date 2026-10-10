// Kopīgā kājene visām publiskajām lapām (index, info, statuss, trukstosie): "Par datiem · Statuss · Svarīgi · #"
// un licences rinda. Kartes lapā tā ir paneļa apakšā; saites ./#datu-avoti un ./#kas-jauns atver "Datu avoti" sadaļu
// un "Kas jauns" logu (izmainas.js). Slaidos (slaidi.html) tā pati rinda ir pēdējā slaidā.
(() => {
  const kartesLapa = !!document.getElementById('panelis');
  const k = document.createElement('footer');
  k.className = 'kajene';
  k.innerHTML = `
    <nav aria-label="Lapas saites">
      <a href="./#datu-avoti">Par datiem</a> · <a href="statuss.html">Statuss</a> · <a href="info.html">Svarīgi</a> ·
      <a href="./#kas-jauns" title="Kas jauns (izmaiņu žurnāls)" aria-label="Kas jauns">#</a>
    </nav>
    <p>Dati: katram avotam sava licence, norādīta pie avota (CC0, CC BY 4.0, ODbL vai oficiāls dokuments);
      ⚠ patvertņu sarakstam licence nav norādīta. Iedzīvotāju ziņojumi — CC BY 4.0. map.repo.lv · AI atvērto datu hakatons 2026.</p>`;
  const stils = document.createElement('style');
  stils.textContent = `
    .kajene { font-size: 12.5px; line-height: 1.45; color: #5c6670; text-align: center; padding: 14px 12px 18px; }
    .kajene nav { margin-bottom: 4px; font-size: 14px; }
    .kajene a { color: #005a99; }
    .kajene p { margin: 0 auto; max-width: 60ch; }
    #panelis .kajene { padding: 10px 4px 4px; text-align: left; }
    @media print { .kajene nav { display: none; } }`;
  document.head.appendChild(stils);
  (kartesLapa ? document.getElementById('panelis') : document.body).appendChild(k);

  if (!kartesLapa) return;
  // Saites no citām lapām: ./#datu-avoti, ./#kas-jauns
  function hash() {
    if (location.hash === '#datu-avoti') {
      const p = document.getElementById('panelis-poga');
      if (document.body.classList.contains('panelis-slegts') && p) p.click();
      const d = document.getElementById('avoti');
      if (d) { d.open = true; setTimeout(() => d.scrollIntoView({ block: 'start' }), 250); }
    } else if (location.hash === '#kas-jauns') {
      document.getElementById('izmainas-poga')?.click();
    }
  }
  window.addEventListener('hashchange', hash);
  window.addEventListener('load', () => setTimeout(hash, 300));
})();
