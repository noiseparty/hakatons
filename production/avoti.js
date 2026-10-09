// Datu avoti (/api/avoti → tabula avoti, src/karte/db/shema.sql): nolaižamā sadaļa "Datu avoti" panelī zem slāņiem
// un avota rinda katra punkta logā. Avots bez atvērtas licences tiek brīdināts. Kartes stūrī — tikai OSM fona kartes atsauce.
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
    const sk = document.getElementById('avoti-skaits');
    if (sk) sk.textContent = saraksts.length + (saraksts.some(a => !a.atverts) ? ' · ⚠' : '');
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

  const atverts = kods => pecKoda[kods]?.atverts !== false;

  return { ieladet, rinda, atverts };
})();
