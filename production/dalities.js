// Rezultātu var nosūtīt un izdrukāt: pēc meklēšanas adreses joslā ?q=<vaicājums>[&lat=&lon=] (bez pārlādes), tāda
// saite atver to pašu rezultātu; kartītes beigās pogas "Dalīties" (Web Share, citādi nokopē saiti) un "Drukāt"
// (drukā tikai kartīti ar QR kodu uz saiti — bezsaistei). QR: vendor/qrcode.js (MIT), bez CDN.
// Atrašanās vieta saitē ir noapaļota līdz ~10 m; to ieliek tikai tad, ja meklēts no Jūsu vietas vai izvēlētas adreses.
const Dalities = (() => {
  const kaste = document.getElementById('rezultati');
  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

  function atjaunotUrl(teksts, vieta) {
    if (document.body.classList.contains('demo-aktivs')) return;  // demo saitēm paliek ?demo=
    const q = new URLSearchParams({ q: teksts });
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
      <button type="button" class="otra" data-darbiba="dalities"><span aria-hidden="true">↗</span> Dalīties</button>
      <button type="button" class="otra" data-darbiba="drukat"><span aria-hidden="true">🖨</span> Drukāt</button>
    </div><p class="dalities-zina piezime" role="status" hidden></p>`;

  function virsraksts() {
    const s = kaste.querySelector('.sapratu');
    return 'Krīzes karte: ' + (s ? s.textContent.replace(/\s+/g, ' ').trim() : 'meklēšanas rezultāts');
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
      zinot('Saite nokopēta. Ielīmējiet to ziņā vai e-pastā.');
    } catch {
      zinot('Nokopējiet saiti no adreses joslas: ' + url);
    }
  }

  function qrSvg(teksts) {
    if (typeof qrcode === 'undefined') return '';
    const q = qrcode(0, 'M');
    q.addData(teksts);
    q.make();
    return q.createSvgTag({ cellSize: 3, margin: 2, scalable: true, alt: 'QR kods uz šo rezultātu' });
  }

  // vendor/qrcode.js (12 KB) vajag tikai drukāšanai — ielādē pirmajā reizē
  let qrIelade = null;
  const ieladetQr = () => qrIelade ||= typeof qrcode !== 'undefined' ? Promise.resolve() : new Promise(gatavs => {
    const s = document.createElement('script');
    s.src = 'vendor/qrcode.js';
    s.onload = s.onerror = () => gatavs();
    document.head.append(s);
  });

  async function drukat() {
    await ieladetQr();
    kaste.querySelector('.druka-galva')?.remove();
    kaste.querySelector('.druka-qr')?.remove();
    const laiks = new Date().toLocaleString('lv-LV', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' });
    kaste.insertAdjacentHTML('afterbegin', `<p class="druka-galva">Krīzes karte · map.repo.lv · izdrukāts ${esc(laiks)}</p>`);
    kaste.insertAdjacentHTML('beforeend', `<div class="druka-qr">${qrSvg(location.href)}<div><p>Atjaunināts rezultāts tiešsaistē:<br>${esc(location.href)}</p>
      <p>Dati mainās (brīdinājumi, ūdens līmenis). Pirms došanās pārbaudiet tiešsaistē vai klausieties Latvijas Radio 1. Ja apdraudēta dzīvība, zvaniet 112.</p></div></div>`);
    document.body.classList.add('druka-rezultats');
    window.print();
  }
  addEventListener('afterprint', () => document.body.classList.remove('druka-rezultats'));

  kaste.addEventListener('click', e => {
    const d = e.target.closest('[data-darbiba]')?.dataset.darbiba;
    if (d === 'dalities') dalities();
    if (d === 'drukat') drukat();
  });

  return { atjaunotUrl, notiritUrl, vietaNoUrl, pogas, qrSvg };
})();
