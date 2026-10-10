// Rezultātu var nosūtīt un izdrukāt: pēc meklēšanas adreses joslā ?q=<vaicājums>[&lat=&lon=] (bez pārlādes), tāda
// saite atver to pašu rezultātu; kartītes beigās pogas "Dalīties" (Web Share, citādi nokopē saiti) un "Drukāt"
// (drukā tikai kartīti ar QR kodu uz saiti — bezsaistei). QR: vendor/qrcode.js (MIT), bez CDN.
// Atrašanās vieta saitē ir noapaļota līdz ~10 m; to ieliek tikai tad, ja meklēts no Jūsu vietas vai izvēlētas adreses.
const Dalities = (() => {
  const kaste = document.getElementById('rezultati');
  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

  const t = (k, m) => typeof Valoda !== 'undefined' ? Valoda.t(k, m) : k;
  const valoda = () => typeof Valoda !== 'undefined' ? Valoda.aktiva() : 'lv';
  const LOKALE = { lv: 'lv-LV', ru: 'ru-RU', en: 'en-GB' };

  function atjaunotUrl(teksts, vieta) {
    if (document.body.classList.contains('demo-aktivs')) return;  // demo saitēm paliek ?demo=
    const q = new URLSearchParams({ q: teksts });
    if (valoda() !== 'lv') q.set('valoda', valoda());  // RU/EN saite atver kartīti tajā pašā valodā
    if (vieta && !vieta.regions) { q.set('lat', (+vieta.lat).toFixed(4)); q.set('lon', (+vieta.lon).toFixed(4)); }
    history.replaceState(null, '', '?' + q);
  }
  function notiritUrl() {
    if (new URLSearchParams(location.search).has('q')) history.replaceState(null, '', location.pathname);
  }
  // Saitē norādītā vieta (lat, lon) → atskaites punkts, pirms meklēšana sākas
  function vietaNoUrl() {
    const q = new URLSearchParams(location.search);
    const lat = +q.get('lat'), lon = +q.get('lon');
    return q.has('lat') && lat > 55 && lat < 59 && lon > 20 && lon < 29 ? { lat, lon, noSaites: true } : null;
  }

  const pogas = () => `<div class="dalities-pogas">
      <button type="button" class="otra" data-darbiba="dalities"><span aria-hidden="true">↗</span> ${t('Dalīties')}</button>
      <button type="button" class="otra" data-darbiba="drukat">${Ik('drukat')} ${t('Drukāt')}</button>
    </div><p class="dalities-zina piezime" role="status" hidden></p>`;

  function virsraksts() {
    const rinda = e => e ? e.textContent.replace(/\s+/g, ' ').trim() : '';
    // lēmums (plūdu zona / tuvākā vieta, citādi brīdinājums) + ko sapratām: kopīgotajā tekstā uzreiz redzams rezultāts
    const lemums = rinda(kaste.querySelector('#rez-lemuma-rinda')) || rinda(kaste.querySelector('.lemums')), s = rinda(kaste.querySelector('.sapratu'));
    return t('Krīzes karte') + ': ' + ([lemums, s].filter(Boolean).join(' · ') || t('meklēšanas rezultāts'));
  }

  function zinot(teksts) {
    const z = kaste.querySelector('.dalities-zina');
    if (!z) return;
    z.textContent = teksts;
    z.hidden = false;
    clearTimeout(zinot.t);
    zinot.t = setTimeout(() => { z.hidden = true; }, 4000);
  }

  async function dalities() {
    const url = location.href;
    if (navigator.share) {
      try { await navigator.share({ title: virsraksts(), text: virsraksts(), url }); return; } catch (e) { if (e.name === 'AbortError') return; }
    }
    try {
      await navigator.clipboard.writeText(url);
      zinot(t('Saite nokopēta. Ielīmējiet to ziņā vai e-pastā.'));
    } catch {
      zinot(t('Nokopējiet saiti no adreses joslas:') + ' ' + url);
    }
  }

  function qrSvg(teksts) {
    if (typeof qrcode === 'undefined') return '';
    const q = qrcode(0, 'M');
    q.addData(teksts);
    q.make();
    return q.createSvgTag({ cellSize: 3, margin: 2, scalable: true, alt: t('QR kods uz šo rezultātu') });
  }

  // vendor/qrcode.js (12 KB) vajag tikai drukāšanai — ielādē pirmajā reizē
  let qrIelade = null;
  const ieladetQr = () => qrIelade ||= typeof qrcode !== 'undefined' ? Promise.resolve() : new Promise(gatavs => {
    const s = document.createElement('script');
    s.src = 'vendor/qrcode.js';
    s.onload = s.onerror = () => gatavs();
    document.head.append(s);
  });

  let atvertie = [];
  async function drukat() {
    await ieladetQr();
    kaste.querySelector('.druka-galva')?.remove();
    kaste.querySelector('.druka-qr')?.remove();
    const laiks = new Date().toLocaleString(LOKALE[valoda()], { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' });
    kaste.insertAdjacentHTML('afterbegin', `<p class="druka-galva">${t('Krīzes karte')} · map.repo.lv · ${t('izdrukāts')} ${esc(laiks)}</p>`);
    kaste.insertAdjacentHTML('beforeend', `<div class="druka-qr">${qrSvg(location.href)}<div><p>${t('Atjaunināts rezultāts tiešsaistē:')}<br>${esc((() => { try { return decodeURI(location.href); } catch { return location.href; } })())}</p>
      <p>${t('Dati mainās (brīdinājumi, ūdens līmenis). Pirms došanās pārbaudiet tiešsaistē vai klausieties Latvijas Radio 1. Ja apdraudēta dzīvība, zvaniet 112.')}</p></div></div>`);
    // drukā viss atvērts: saplocītie "Vairāk" bloki (details) uz papīra citādi paliek paslēpti
    atvertie = [...kaste.querySelectorAll('details:not([open])')];
    atvertie.forEach(d => { d.open = true; });
    document.body.classList.add('druka-rezultats');
    window.print();
  }
  addEventListener('afterprint', () => {
    document.body.classList.remove('druka-rezultats');
    atvertie.forEach(d => { d.open = false; }); atvertie = [];
  });

  kaste.addEventListener('click', e => {
    const d = e.target.closest('[data-darbiba]')?.dataset.darbiba;
    if (d === 'dalities') dalities();
    if (d === 'drukat') drukat();
  });

  return { atjaunotUrl, notiritUrl, vietaNoUrl, pogas, qrSvg };
})();
