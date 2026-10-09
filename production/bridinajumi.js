// LVĢMC hidrometeoroloģisko brīdinājumu josla lapas augšā (/api/bridinajumi, data.gov.lv, CC0).
// Bez vietas — visi spēkā esošie; ar vietu (meklēšanas sākumpunkts) — tikai tie, kas attiecas uz to.
// Ja galapunkts nav pieejams, josla vienkārši nav redzama.
const Bridinajumi = (() => {
  const LIMENIS = { 1: ['dzeltens', 'Dzeltenais'], 2: ['oranzs', 'Oranžais'], 3: ['sarkans', 'Sarkanais'] };
  const AVOTS = '<a href="https://data.gov.lv/dati/lv/dataset/hidrometeorologiskie-bridinajumi" target="_blank" rel="noopener">LVĢMC hidrometeoroloģiskie brīdinājumi</a> · CC0';
  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const laiks = iso => new Date(iso).toLocaleString('lv-LV', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' });
  let pieprasijums = null;

  async function atjaunot(vieta, nosaukums) {
    const josla = document.getElementById('bridinajums');
    if (pieprasijums) pieprasijums.abort();
    pieprasijums = new AbortController();
    const q = vieta ? '?' + new URLSearchParams({ lat: (+vieta.lat).toFixed(5), lon: (+vieta.lon).toFixed(5) }) : '';
    try {
      const r = await fetch('/api/bridinajumi' + q, { signal: pieprasijums.signal });
      if (!r.ok) throw new Error(r.status);
      const visi = (await r.json()).bridinajumi;
      const sheit = vieta ? visi.filter(b => b.attiecas) : visi;
      const max = Math.max(0, ...sheit.map(b => b.limenis));
      const kur = vieta ? (nosaukums ? esc(nosaukums) : 'Šajā vietā') : 'Latvijā';
      josla.className = 'bridinajums ' + (max ? LIMENIS[max][0] : 'zals');
      josla.innerHTML = !sheit.length
        ? `<span>✓ ${kur}: LVĢMC brīdinājumu šobrīd nav${vieta && visi.length ? ` <small>(citur Latvijā: ${visi.length})</small>` : ''}</span>`
        : `<details><summary>⚠ ${vieta ? kur + ': ' : ''}${sheit.map(b => `${LIMENIS[b.limenis]?.[1] || esc(b.krasa)} brīdinājums: ` +
            `${esc(b.paradiba.toLowerCase())}${b.regioni && !vieta ? ` (${esc(b.regioni)})` : ''}${b.lidz ? `, līdz ${laiks(b.lidz)}` : ''}`).join(' · ')}</summary>` +
          sheit.map(b => `<p>${esc(b.teksts)}</p><p class="riski">${esc(b.riski).replace(/\n/g, '<br>')}</p>`).join('') +
          `<p class="avots-rinda">Avots: ${AVOTS}</p></details>`;
      josla.hidden = false;
    } catch (e) {
      if (e.name !== 'AbortError') josla.hidden = true;
    }
  }

  atjaunot(null);
  return { atjaunot };
})();
