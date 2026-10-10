// Izmaiņu žurnāls "Kas jauns": poga # galvenes kreisajā malā atver logu ar izmaiņām pa datumiem (izmainas.json).
// <dialog>: Escape aizver pats; klikšķis ārpus loga satura arī aizver.
(() => {
  const poga = document.getElementById('izmainas-poga');
  if (!poga) return;
  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const datums = d => new Date(d + 'T12:00').toLocaleDateString('lv-LV', { day: 'numeric', month: 'long', year: 'numeric' });
  document.body.insertAdjacentHTML('beforeend', `
    <dialog id="izmainas" class="izmainas" aria-labelledby="izmainas-virsraksts">
      <div class="izmainas-galva"><h2 id="izmainas-virsraksts">Kas jauns</h2>
        <button type="button" class="izmainas-aizvert" aria-label="Aizvērt izmaiņu žurnālu">✕</button></div>
      <div class="izmainas-saturs"><p class="piezime">Ielādē…</p></div>
    </dialog>`);
  const logs = document.getElementById('izmainas');
  const saturs = logs.querySelector('.izmainas-saturs');
  let ieladets = false;

  async function ieladet() {
    try {
      const { izmainas } = await (await fetch('izmainas.json')).json();
      const pecDienas = Map.groupBy ? Map.groupBy(izmainas, i => i.datums)
        : izmainas.reduce((m, i) => m.set(i.datums, [...(m.get(i.datums) || []), i]), new Map());
      saturs.innerHTML = [...pecDienas].map(([d, saraksts]) => `<h3>${esc(datums(d))}</h3><ul>` + saraksts.map(i =>
        `<li>${esc(i.teksts)}${i.saite ? ` <a href="${esc(i.saite)}"${/^https?:/.test(i.saite) ? ' target="_blank" rel="noopener"' : ''}>${/^https?:/.test(i.saite) ? 'vairāk' : 'atvērt'}</a>` : ''}</li>`).join('') + '</ul>').join('');
      ieladets = true;
    } catch {
      saturs.innerHTML = '<p class="piezime kluda">Izmaiņu sarakstu neizdevās ielādēt.</p>';
    }
  }

  poga.addEventListener('click', () => {
    if (!ieladets) ieladet();
    logs.showModal();
    poga.setAttribute('aria-expanded', 'true');
  });
  logs.querySelector('.izmainas-aizvert').addEventListener('click', () => logs.close());
  logs.addEventListener('click', e => { if (e.target === logs) logs.close(); });  // klikšķis uz fona (ārpus satura)
  logs.addEventListener('close', () => { poga.setAttribute('aria-expanded', 'false'); poga.focus(); });
})();
