// Ikonas un marķieru formas visai lapai.
//  • Ik('vejs') → <svg><use href="ikonas/ikonas.svg#vejs"></svg> (Meteocons MIT laikapstākļiem, Lucide ISC pārējam;
//    licences: ikonas/LICENSES.md). Emocijzīmes UI nelieto: tās telefonos izskatās dažādi un ekrāna lasītāji tās nolasa.
//  • Formas pa slāņu grupām, lai slāņus var atšķirt arī bez krāsas: medicīna — krusts, infrastruktūra — trijstūris,
//    ūdens — lāse, transports — kvadrāts, patvertnes un dienesti — aplis. Ikonas.markeris(): 26 px forma 44 × 44 px
//    apaļā pieskāriena laukumā; pārklājoties atveras tuvākais punkts (app.js atvertTuvako).
const Ikonas = (() => {
  const SPRAITS = 'ikonas/ikonas.svg';
  const ik = (nos, klase = '') => nos ? `<svg class="ik${klase ? ' ' + klase : ''}" aria-hidden="true" focusable="false"><use href="${SPRAITS}#${nos}"></use></svg>` : '';

  const GRUPAS = {
    krusts: ['slimnica', 'neatliekama_24h', 'aptieka', 'veterinars', 'soc_pakalpojumi'],
    trijsturis: ['degviela', 'bankomats', 'uzlades_stacija', 'noturibas_punkts', 'udens_nemsana', 'wifi_punkts', 'bistams_objekts'],
    lase: ['udens_limenis', 'udens_punkts'],
    kvadrats: ['pietura', 'ev_uzlade', 'celi', 'robezas'],
    aplis: ['patvertne', 'evakuacijas_punkts', 'izmitinasana', 'policija', 'ugunsdzeseji'],
  };
  const PEC_KATEGORIJAS = Object.fromEntries(Object.entries(GRUPAS).flatMap(([f, k]) => k.map(x => [x, f])));
  const forma = kategorija => PEC_KATEGORIJAS[kategorija] || 'aplis';
  // viewBox 0 0 24 24; lāse — Lucide "droplet" (ISC), vietturis līdz lietotāja SVG kopai
  // kontūras krāsa: stils.css tokeni --gim-drosas / --gim-veseliba / --gim-infra / --gim-udens / --gim-transports
  const GRUPAS_TOKENS = { aplis: 'drosas', krusts: 'veseliba', trijsturis: 'infra', lase: 'udens', kvadrats: 'transports' };
  const CELI = {
    aplis: '<circle cx="12" cy="12" r="9.5"/>',
    krusts: '<path d="M8.6 2.5h6.8v6.1h6.1v6.8h-6.1v6.1H8.6v-6.1H2.5V8.6h6.1z"/>',
    trijsturis: '<path d="M12 2.2 22.6 20.8H1.4z"/>',
    lase: '<path d="M12 22.3a7.6 7.6 0 0 0 7.6-7.6c0-2.2-1.1-4.2-3.3-6-2.2-1.7-3.8-4.3-4.3-7-.5 2.7-2.1 5.3-4.3 7-2.2 1.8-3.3 3.8-3.3 6a7.6 7.6 0 0 0 7.6 7.6z"/>',
    kvadrats: '<rect x="3" y="3" width="18" height="18" rx="2.5"/>',
  };
  // Forma kā SVG (leģendai, sarakstam, marķierim); tumša kontūra + balta apmale — redzama uz abām pamatkartēm
  function formaSvg(kategorija, krasa, izmers = 16, klase = '') {
    const f = typeof kategorija === 'string' && CELI[kategorija] ? kategorija : forma(kategorija);
    return `<svg class="forma forma-${f}${klase ? ' ' + klase : ''}" viewBox="0 0 24 24" width="${izmers}" height="${izmers}" aria-hidden="true" focusable="false">` +
      `<g fill="${krasa || '#57534e'}" style="stroke:var(--gim-${GRUPAS_TOKENS[f]}, #1c1917)" stroke-width="1.8" stroke-linejoin="round">${CELI[f]}</g></svg>`;
  }
  function markeris(kategorija, krasa_ = krasa(kategorija), izmers = 26) {
    return L.divIcon({ className: 'forma-markeris', iconSize: [44, 44], iconAnchor: [22, 22], popupAnchor: [0, -12],
      html: formaSvg(kategorija, krasa_, izmers) });
  }

  // Ikona no datos esoša nosaukuma (piem., demo scenāriju "ikona": "drons"); nezināmu neizvada
  const no = v => /^[a-z0-9-]+$/.test(String(v ?? '')) ? ik(v) : '';

  // Forma slāņa krāsā (kategorijas no app.js) — tā pati slāņu sarakstā, leģendā, sarakstā, rezultātā un kartē
  const krasa = kategorija => (typeof kategorijas !== 'undefined' && kategorijas[kategorija]?.krasa) || '#57534e';
  const formaHTML = (kategorija, izmers = 16) => formaSvg(kategorija, krasa(kategorija), izmers, 'forma-rinda');

  // Statiskās HTML vietas: <span class="forma-vieta" data-forma="lase" data-krasa="#…"> vai data-ikona="zibens">
  function aizpilditVietas(sakne = document) {
    for (const v of sakne.querySelectorAll('.forma-vieta:empty')) {
      v.outerHTML = v.dataset.ikona ? ik(v.dataset.ikona, 'ik-rinda') : formaSvg(v.dataset.forma, v.dataset.krasa, 16, 'forma-rinda');
    }
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', () => aizpilditVietas());
  else aizpilditVietas();

  return { ik, no, forma, formaSvg, formaHTML, markeris, GRUPAS, aizpilditVietas };
})();
const Ik = Ikonas.ik;
