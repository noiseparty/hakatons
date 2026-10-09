// Datu avoti (/api/avoti → tabula avoti, src/karte/db/shema.sql): sadaļa "Datu avoti" panelī,
// avota rinda katra punkta logā un kartes atsauce. Avots bez atvērtas licences tiek brīdināts.
const Avoti = (() => {
  let pecKoda = {};
  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const saite = (url, teksts) => /^https?:\/\//.test(url || '')
    ? `<a href="${esc(url)}" target="_blank" rel="noopener">${esc(teksts)}</a>` : esc(teksts);
  const datums = iso => iso ? new Date(iso).toLocaleDateString('lv-LV') : '';
  const bridinajums = '⚠ Atvērta licence nav norādīta';

  function zimet(saraksts) {
    const ul = document.getElementById('avoti-saraksts');
    if (!ul) return;
    ul.innerHTML = saraksts.map(a => `
      <li class="avots${a.atverts ? '' : ' bez-licences'}" id="avots-${esc(a.kods)}">
        <b>${saite(a.datu_kopa_url, a.nosaukums)}</b>
        <small>${esc(a.izdevejs)}</small>
        <span class="licence">${a.atverts ? '' : bridinajums + ' · '}${saite(a.licences_url, a.licence)}</span>
        <small>Kartē: ${esc(a.lietojums)}${a.skaits ? ` · ${a.skaits} objekti, ielādēts ${datums(a.ieladets)}` : ''}</small>
        ${a.piezime ? `<small class="avota-piezime">${esc(a.piezime)}</small>` : ''}
        ${a.lejupielade && a.lejupielade !== a.datu_kopa_url ? `<small class="ieguve">Ieguve: ${/^https?:/.test(a.lejupielade) ? saite(a.lejupielade, a.lejupielade) : esc(a.lejupielade)}</small>` : ''}
      </li>`).join('');
  }

  async function ieladet() {
    const r = await fetch('/api/avoti');
    if (!r.ok) throw new Error(r.status);
    const saraksts = await r.json();
    pecKoda = Object.fromEntries(saraksts.map(a => [a.kods, a]));
    zimet(saraksts);
    return saraksts;
  }

  // Rinda punkta logā: "Avots: <datu kopa> (izdevējs) · licence".
  function rinda(kods) {
    const a = pecKoda[kods];
    if (!a) return '';
    return `<small class="popup-avots">Avots: ${saite(a.datu_kopa_url, a.nosaukums)} (${esc(a.izdevejs)}) · ` +
      `${saite(a.licences_url, a.licence)}${a.atverts ? '' : `<br><span class="bez-licences">${bridinajums}</span>`}</small>`;
  }

  // Īsā atsauce kartes stūrī: izdevēji ar licencēm + saite uz pilno sarakstu.
  function atsauce() {
    const dati = Object.values(pecKoda).filter(a => a.skaits || a.kods === 'vzd-varis');
    return '<a href="#avoti">Dati</a>: ' + dati.map(a => `${esc(a.izdevejs)} (${esc(a.atverts ? a.licence.split(' (')[0] : 'licence nav norādīta')})`).join(', ');
  }

  const atverts = kods => pecKoda[kods]?.atverts !== false;

  return { ieladet, rinda, atsauce, atverts };
})();
