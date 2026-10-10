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
    return vairak('obj-statuss', ir ? `Statuss (atjaunots ${esc(new Date(i.last_updated).toLocaleString('lv-LV'))})`
      : `<b>Statuss nav apstiprināts</b> (nav ziņu pēdējās ${SVAIGS_H} h)`,
      ir ? vertibas.map(([n, v]) => `${n} — ${esc(v)}`).join(', ') : 'siltums, uzlāde, ūdens, wifi, ģenerators — nav zināms',
      vertibas.map(([n, v]) => `<li>${n}: ${esc(v)}</li>`));
  }

  // Logā: virsraksts + viena īsa rinda; pilnais pazīmju saraksts zem "Vairāk" (telefonā garš saraksts aizņēma visu logu)
  function vairak(klase, virsraksts, isaRinda, rindas) {
    return `<span class="${klase}">${virsraksts}: ${isaRinda}.` +
      `<details class="statuss-vairak"><summary>Vairāk</summary><ul>${rindas.join('')}</ul></details></span>`;
  }

  // Viens kopīgs statusa bloks patvertnēm, evakuācijas un izmitināšanas vietām un noturības punktiem — visur vienāds.
  // Pazīmes (siltums, uzlāde, ūdens, wifi, ģenerators) ir "nav zināms", ja nav svaigu (≤ 6 h) ziņu; patvertnēm,
  // evakuācijas un izmitināšanas vietām vēl ietilpība, pieejamība ratiņkrēslam un dzīvnieki — "nav norādīts", ja datos nav.
  // Citiem slāņiem — iepriekšējais statuss() (piem., simulētie ūdens/uzlādes punkti).
  const BLOKA_KATEGORIJAS = new Set(['patvertne', 'evakuacijas_punkts', 'izmitinasana', 'noturibas_punkts']);
  const AR_VIETU_ZINAM = new Set(['patvertne', 'evakuacijas_punkts', 'izmitinasana']);
  const jaNe = v => v === true || /^(ir|jā|ja|yes|limited|daļēji)$/i.test(String(v ?? '')) ? 'ir'
    : v === false || /^(nav|nē|ne|no)$/i.test(String(v ?? '')) ? 'nav' : (v == null || v === '' ? null : String(v));

  function vietasZinas(i) {
    const n = +(i.ietilpiba ?? i.vietas);
    const ratini = jaNe(i.ratinkresls ?? i.wheelchair);
    const dzivnieki = jaNe(i.dzivnieki ?? i.majdzivnieki);
    return [
      ['ietilpība', Number.isFinite(n) && n > 0 ? `${n} vietas` : null],
      ['pieejamība ratiņkrēslam', ratini],
      ['dzīvnieki', dzivnieki],
    ];
  }

  function statusaBloks(p, isi = false) {
    if (!BLOKA_KATEGORIJAS.has(p?.kategorija)) return statuss(p, isi);
    const i = p.ipasibas || {};
    const ir = svaigs(i.last_updated) && i.statuss && typeof i.statuss === 'object';
    const pazimes = Object.entries(PAZIMES).map(([k, nos]) => [nos, ir ? (i.statuss[k] ?? 'nav zināms') : 'nav zināms']);
    const vietas = AR_VIETU_ZINAM.has(p.kategorija) ? vietasZinas(i) : [];
    const virsraksts = ir ? `Statuss (atjaunots ${esc(new Date(i.last_updated).toLocaleString('lv-LV'))})`
      : `<b>Statuss nav apstiprināts</b> (nav ziņu pēdējās ${SVAIGS_H} h)`;
    const dalas = [ir ? pazimes.map(([n, v]) => `${n} — ${esc(v)}`).join(', ') : 'siltums, uzlāde, ūdens, wifi, ģenerators — nav zināms'];
    const zinamas = vietas.filter(([, v]) => v), nezinamas = vietas.filter(([, v]) => !v);
    if (zinamas.length) dalas.push(zinamas.map(([n, v]) => n === 'ietilpība' ? esc(v) : `${n} — ${esc(v)}`).join(', '));
    if (isi) {
      if (nezinamas.length) dalas.push(nezinamas.map(([n]) => n).join(', ') + ' — nav norādīts');
      return `<small class="obj-statuss statusa-bloks">${virsraksts}: ${dalas.join('; ')}.</small>`;
    }
    // Logā īsā rinda bez "nav norādīts" daļas (tā ir sarakstā zem "Vairāk")
    return vairak('obj-statuss statusa-bloks', virsraksts, dalas.join('; '),
      [...pazimes.map(([n, v]) => `<li>${n}: ${esc(v)}</li>`), ...vietas.map(([n, v]) => `<li>${n}: ${v ? esc(v) : 'nav norādīts'}</li>`)]);
  }

  // Ūdens / uzlādes punktu "veids" logā (citiem slāņiem veids jau ir nosaukumā vai nav vajadzīgs)
  const raditVeidu = p => simulets(p) || p?.kategorija === 'noturibas_punkts';

  return { simulets, svaigs, zime, statuss, statusaBloks, raditVeidu, SVAIGS_H };
})();
