// Izmaiņu žurnāls "Kas jauns": poga # galvenes kreisajā malā atver logu ar izmaiņām pa datumiem (izmainas.json).
// <dialog>: Escape aizver pats; klikšķis ārpus loga satura arī aizver.
(() => {
  const poga = document.getElementById('izmainas-poga');
  if (!poga) return;
  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const t = (k, m) => typeof Valoda !== 'undefined' ? Valoda.t(k, m) : k;
  const LOKALE = { lv: 'lv-LV', ru: 'ru-RU', en: 'en-GB' };
  const datums = d => new Date(d + 'T12:00').toLocaleDateString(LOKALE[typeof Valoda !== 'undefined' ? Valoda.aktiva() : 'lv'] || 'lv-LV', { day: 'numeric', month: 'long', year: 'numeric' });
  document.body.insertAdjacentHTML('beforeend', `
    <dialog id="izmainas" class="izmainas" aria-labelledby="izmainas-virsraksts">
      <div class="izmainas-galva"><h2 id="izmainas-virsraksts">${esc(t('Kas jauns'))}</h2>
        <button type="button" class="izmainas-aizvert" aria-label="${esc(t('Aizvērt izmaiņu žurnālu'))}"><svg class="ik" aria-hidden="true" focusable="false"><use href="ikonas/ikonas.svg#aizvert"></use></svg></button></div>
      <div class="izmainas-saturs"><p class="piezime">${esc(t('Ielādē…'))}</p></div>
    </dialog>`);
  const logs = document.getElementById('izmainas');
  const saturs = logs.querySelector('.izmainas-saturs');
  let ieladets = false;
  let dati = null;  // izmainas.json (pārzīmēšanai pēc valodas maiņas)

  function zimet() {
    if (!dati) return;
    const pecDienas = Map.groupBy ? Map.groupBy(dati, i => i.datums)
      : dati.reduce((m, i) => m.set(i.datums, [...(m.get(i.datums) || []), i]), new Map());
    saturs.innerHTML = [...pecDienas].map(([d, saraksts]) => `<h3>${esc(datums(d))}</h3><ul>` + saraksts.map(i =>
      `<li>${esc(i.teksts)}${i.saite ? ` <a href="${esc(i.saite)}"${/^https?:/.test(i.saite) ? ' target="_blank" rel="noopener"' : ''}>${/^https?:/.test(i.saite) ? esc(t('vairāk')) : esc(t('atvērt'))}</a>` : ''}</li>`).join('') + '</ul>').join('');
  }

  async function ieladet() {
    try {
      const { izmainas } = await (await fetch('izmainas.json')).json();
      dati = izmainas;
      zimet();
      ieladets = true;
    } catch {
      saturs.innerHTML = `<p class="piezime kluda">${esc(t('Izmaiņu sarakstu neizdevās ielādēt.'))}</p>`;
    }
  }

  // Valodas maiņa: virsraksts, aizvēršanas poga un saraksts (ja jau ielādēts) tiek pārzīmēti
  document.addEventListener('valoda-maina', () => {
    logs.querySelector('#izmainas-virsraksts').textContent = t('Kas jauns');
    logs.querySelector('.izmainas-aizvert').setAttribute('aria-label', t('Aizvērt izmaiņu žurnālu'));
    if (ieladets) zimet();
  });

  poga.addEventListener('click', () => {
    if (!ieladets) ieladet();
    logs.showModal();
    poga.setAttribute('aria-expanded', 'true');
  });
  logs.querySelector('.izmainas-aizvert').addEventListener('click', () => logs.close());
  logs.addEventListener('click', e => { if (e.target === logs) logs.close(); });  // klikšķis uz fona (ārpus satura)
  logs.addEventListener('close', () => { poga.setAttribute('aria-expanded', 'false'); poga.focus(); });
})();
