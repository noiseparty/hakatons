// Kopīgs palīgs punkta logam (app.js) un meklēšanas rezultātam (meklesana.js):
//  • simulētiem prototipa datiem (avots "sim-…") — zīme "SIMULĒTI DATI — prototips";
//  • objektiem ar statusa pazīmēm (ipasibas.statuss: siltums, uzlāde, ūdens, wifi, ģenerators) — svaiguma noteikums:
//    ja statusa laiks (ipasibas.last_updated) nav zināms vai vecāks par 6 h, katra pazīme ir "nav zināms" un
//    rakstām "statuss nav apstiprināts". Apstiprinātu, svaigu statusu rāda tā, kā tas ir.
const ObjektaStatuss = (() => {
  const SVAIGS_H = 6;
  const PAZIMES = { siltums: 'siltums', uzlade: 'telefona uzlāde', udens: 'dzeramais ūdens', wifi: 'wifi', generators: 'ģenerators' };
  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

  const simulets = p => /^sim-/.test(p?.avots || '');

  // Vai laiks (ISO) nav vecāks par h stundām; nezināms laiks nav svaigs
  function svaigs(laiks, h = SVAIGS_H) {
    const t = laiks ? Date.parse(laiks) : NaN;
    return Number.isFinite(t) && Date.now() - t <= h * 3600 * 1000 && t <= Date.now() + 5 * 60 * 1000;
  }

  function zime(p) {
    return simulets(p) ? '<span class="sim-zime" title="Izdomāti dati prototipam: adrese, nosaukums un darba laiks nav reāli">SIMULĒTI DATI — prototips</span><br>' : '';
  }

  // isi: meklēšanas rezultātā viena rinda; logā — pazīmju saraksts
  function statuss(p, isi = false) {
    const i = p?.ipasibas || {};
    if (!i.statuss || typeof i.statuss !== 'object') return '';
    const ir = svaigs(i.last_updated);
    const vertibas = Object.entries(PAZIMES).map(([k, nos]) => [nos, ir ? (i.statuss[k] ?? 'nav zināms') : 'nav zināms']);
    if (isi) {
      return `<small class="obj-statuss">${ir ? 'Statuss: ' + vertibas.map(([n, v]) => `${n} — ${esc(v)}`).join(', ')
        : '<b>Statuss nav apstiprināts</b>: nav zināms, vai šeit ir siltums, uzlāde, ūdens un wifi. Pirms došanās pārliecinieties pašvaldībā.'}</small>`;
    }
    return `<span class="obj-statuss">${ir ? `Statuss (atjaunots ${esc(new Date(i.last_updated).toLocaleString('lv-LV'))}):`
      : '<b>Statuss nav apstiprināts</b> (nav ziņu pēdējās ' + SVAIGS_H + ' h):'}<ul>` +
      vertibas.map(([n, v]) => `<li>${n}: ${esc(v)}</li>`).join('') + '</ul></span>';
  }

  // Ūdens / uzlādes punktu "veids" logā (citiem slāņiem veids jau ir nosaukumā vai nav vajadzīgs)
  const raditVeidu = p => simulets(p) || p?.kategorija === 'noturibas_punkts';

  return { simulets, svaigs, zime, statuss, raditVeidu, SVAIGS_H };
})();
