// Pieejamība ar tastatūru un ekrāna lasītāju (notes/pieejamiba.md). Ielādē uzreiz pēc Leaflet (pirms app.js), lai kartes
// iestatījumi derētu arī pirmajai kartei un punktiem; pārējo dara, kad visi moduļi ielādēti (DOMContentLoaded).
// - Kartes punkti nav atsevišķi Tab mērķi (simtiem punktu): visi ir sarakstā "Saraksts" (saraksts.js) ar "Rādīt kartē".
// - Ja lietotājs prasa mazāk kustības: karte pārbīdās un tuvinās bez animācijas.
// - Izlaišanas saites "Uz meklēšanu" / "Uz karti"; telefonā Tab secība: galvene → meklēšana un rezultāts (apakšējā lapa) → karte.
// - Apakšējā lapa "Pilns" stāvoklī ir dialogs: Tab paliek lapā, Escape to samazina līdz "Puse".
// - Uznirstošais logs, kas atvērts no saraksta: fokuss logā, Escape aizver, fokuss atpakaļ.
(() => {
  if (!window.L) return;
  L.Marker.mergeOptions({ keyboard: false });

  const mazakKustibas = matchMedia('(prefers-reduced-motion: reduce)');
  if (mazakKustibas.matches) {
    L.Map.mergeOptions({ zoomAnimation: false, fadeAnimation: false, markerZoomAnimation: false, inertia: false });
    const P = L.Map.prototype;
    const bez = o => ({ ...(o || {}), animate: false });
    const setView = P.setView, panTo = P.panTo, panBy = P.panBy, fitBounds = P.fitBounds;
    P.setView = function (c, z, o) { return setView.call(this, c, z, bez(o)); };
    P.panTo = function (c, o) { return panTo.call(this, c, bez(o)); };
    P.panBy = function (c, o) { return panBy.call(this, c, bez(o)); };
    P.fitBounds = function (b, o) { return fitBounds.call(this, b, bez(o)); };
    P.flyTo = function (c, z, o) { return this.setView(c, z, o); };
    P.flyToBounds = function (b, o) { return this.fitBounds(b, o); };
  }

  const FOKUSEJAMI = 'a[href], button:not([disabled]), input:not([disabled]):not([type=hidden]), select:not([disabled]), textarea:not([disabled]), summary, [tabindex]:not([tabindex="-1"])';
  const redzams = e => !!(e.offsetWidth || e.offsetHeight || e.getClientRects().length) && getComputedStyle(e).visibility !== 'hidden';

  addEventListener('DOMContentLoaded', () => {
    const $ = id => document.getElementById(id);

    // ---- Izlaišanas saites (redzamas tikai ar tastatūras fokusu) ----
    document.body.insertAdjacentHTML('afterbegin', `<nav class="izlaist" aria-label="Pāriet uz">
      <a href="#jautajums" data-uz="jautajums">Uz meklēšanu</a><a href="#karte" data-uz="karte">Uz karti</a></nav>`);
    document.querySelector('.izlaist').addEventListener('click', e => {
      const a = e.target.closest('[data-uz]');
      if (!a) return;
      e.preventDefault();
      const merkis = $(a.dataset.uz);
      if (a.dataset.uz === 'jautajums' && typeof Apaksa !== 'undefined' && Apaksa.aktiva() && Apaksa.stavoklis() === 'peek') Apaksa.atvert('puse');
      merkis?.focus();
    });

    // ---- Telefons: apakšējā lapa (meklēšana + rezultāts) DOM secībā pirms kartes, lai Tab iet meklēšana → kartīte → karte.
    // Lapa ir position: fixed, tāpēc vizuāli nekas nemainās; datorā tā ir paslēpta.
    const lapa = $('apaksa'), galvene = document.querySelector('main');
    if (lapa && galvene) galvene.before(lapa);

    // ---- Apakšējā lapa "Pilns": dialogs ar fokusa slazdu un Escape ----
    if (lapa) {
      const pilna = () => !lapa.hidden && lapa.dataset.stavoklis === 'pilna';
      const atjaunot = () => {
        if (pilna()) { lapa.setAttribute('role', 'dialog'); lapa.setAttribute('aria-modal', 'true'); }
        else { lapa.setAttribute('role', 'region'); lapa.removeAttribute('aria-modal'); }
      };
      new MutationObserver(atjaunot).observe(lapa, { attributes: true, attributeFilter: ['data-stavoklis', 'hidden'] });
      atjaunot();
      lapa.addEventListener('keydown', e => {
        if (!pilna()) return;
        if (e.key === 'Escape' && !e.defaultPrevented && !e.target.closest('[role="menu"], dialog')) {
          // meklēšanas laukā Escape vispirms aizver ieteikumus (meklesana.js); lapu samazina tikai tad, ja nav ko aizvērt
          if (e.target.matches('input') && document.querySelector('#populari:not([hidden])')) return;
          e.preventDefault();
          Apaksa.atvert('puse');
          $('apaksa-rokturis')?.focus();
        } else if (e.key === 'Tab') {
          const f = [...lapa.querySelectorAll(FOKUSEJAMI)].filter(redzams);
          if (!f.length) return;
          const pirmais = f[0], pedejais = f[f.length - 1];
          if (e.shiftKey && document.activeElement === pirmais) { e.preventDefault(); pedejais.focus(); }
          else if (!e.shiftKey && document.activeElement === pedejais) { e.preventDefault(); pirmais.focus(); }
        }
      });
    }

    // ---- Uznirstošais logs, kas atvērts ar tastatūru (no saraksta, rezultāta kartītes) ----
    if (typeof karte === 'undefined') return;
    let atpakal = null;
    karte.on('popupopen', e => {
      const bija = document.activeElement;
      const aizvert = e.popup.getElement()?.querySelector('.leaflet-popup-close-button');
      if (aizvert) aizvert.setAttribute('aria-label', 'Aizvērt logu');
      if (!bija || bija === document.body || bija.closest('.leaflet-container')) { atpakal = null; return; }
      if (!bija.matches(':focus-visible')) { atpakal = null; return; }
      atpakal = bija;
      const saturs = e.popup.getElement()?.querySelector('.leaflet-popup-content');
      if (saturs) { saturs.tabIndex = -1; saturs.focus({ preventScroll: true }); }
    });
    karte.on('popupclose', e => {
      const logs = e.popup.getElement();
      const iekse = logs && (logs.contains(document.activeElement) || document.activeElement === document.body);
      if (iekse && atpakal?.isConnected && redzams(atpakal)) atpakal.focus({ preventScroll: true });
      atpakal = null;
    });
    document.addEventListener('keydown', e => {
      if (e.key === 'Escape' && e.target.closest?.('.leaflet-popup')) { e.preventDefault(); karte.closePopup(); }
    });
  });
})();
