// Service worker (sw.js): reģistrācija visām lapām, paziņojums par jaunu versiju un ?svaigs=1.
//  • sw.js install → skipWaiting, activate → izdzēš vecos shell-* kešus un clients.claim; kad jaunā versija pārņem
//    lapu (controllerchange), rādām mazu paziņojumu "Pieejama jauna versija · Atsvaidzināt". Lapu NEKAD nepārlādējam
//    paši (var būt atvērta meklēšana vai ziņojums) — tikai pēc pogas; meklējums saglabājas (?q=).
//  • sw.js atjaunošanu pārbauda bez HTTP keša (updateViaCache: 'none'), ielādējot lapu, atgriežoties cilnē un ik 30 min.
//  • ?svaigs=1 — avārijas slēdzis pirms prezentācijas (notes/ritdiena.md): noņem SW, izdzēš visus kešus, pārlādē bez parametra.
//  • statuss.html: #sw-versija rāda aktīvā SW VERSION.
(() => {
  if (!('serviceWorker' in navigator)) return;
  const drosi = location.protocol === 'https:' || ['localhost', '127.0.0.1'].includes(location.hostname);
  const sw = navigator.serviceWorker;
  const params = new URLSearchParams(location.search);

  if (params.has('svaigs')) {
    (async () => {
      try {
        for (const r of await sw.getRegistrations()) await r.unregister();
        if (window.caches) for (const k of await caches.keys()) await caches.delete(k);
      } catch { /* tik un tā pārlādējam */ }
      params.delete('svaigs');
      location.replace(location.pathname + (params.toString() ? '?' + params : '') + location.hash);
    })();
    return;
  }
  if (!drosi) return;

  let kontrolieris = sw.controller;  // pirmajā apmeklējumā SW pārņem lapu — tas nav "jauna versija"
  window.addEventListener('load', async () => {
    let reg;
    try { reg = await sw.register('sw.js', { updateViaCache: 'none' }); } catch { return; }
    const parbaudit = () => reg.update().catch(() => {});
    document.addEventListener('visibilitychange', () => { if (document.visibilityState === 'visible') parbaudit(); });
    setInterval(parbaudit, 30 * 60e3);
    raditVersiju();
  });

  sw.addEventListener('controllerchange', () => {
    raditVersiju();
    if (kontrolieris) pazinot();
    kontrolieris = sw.controller;
  });

  // Aktīvā SW versija (sw.js atbild uz 'versija' pa MessageChannel)
  async function versija() {
    const k = sw.controller || (await sw.getRegistration())?.active;
    if (!k) return null;
    return new Promise(ok => {
      const ch = new MessageChannel();
      const t = setTimeout(() => ok(null), 2000);
      ch.port1.onmessage = e => { clearTimeout(t); ok(e.data?.versija || null); };
      k.postMessage('versija', [ch.port2]);
    });
  }
  async function raditVersiju() {
    const el = document.getElementById('sw-versija');
    if (!el) return;
    const v = await versija();
    el.textContent = v ? Valoda.t('Bezsaistes kopijas (service worker) versija: {v}.', { v }) : Valoda.t('Bezsaistes kopija (service worker) šajā pārlūkā nav aktīva.');
    el.hidden = false;
  }

  let radits = false;
  function pazinot() {
    if (radits) return;
    radits = true;
    const stils = document.createElement('style');
    stils.textContent = `
.jauna-versija { position: fixed; z-index: 2000; top: calc(8px + env(safe-area-inset-top, 0px)); left: 0; right: 0; margin: 0 auto;
  display: flex; align-items: center; gap: 4px; width: max-content; max-width: calc(100vw - 16px); white-space: nowrap; box-sizing: border-box; padding: 0 0 0 12px;
  background: #1c1917; color: #fff; border-radius: 22px; box-shadow: 0 2px 10px rgba(0,0,0,.3); font: 14px/1.3 system-ui, sans-serif; }
.jauna-versija button { width: auto; flex: none; min-height: 44px; min-width: 44px; border: 0; background: transparent; color: #fff; font: inherit; cursor: pointer;
  display: inline-flex; align-items: center; gap: 6px; padding: 0 12px; border-radius: 22px; }
.jauna-versija .jv-atsvaidzinat { font-weight: 600; text-decoration: underline; }
.jauna-versija button:focus-visible { outline: 2px solid #7cc4ff; outline-offset: -2px; }
.jauna-versija .ik { width: 18px; height: 18px; fill: none; stroke: currentColor; }
@media print { .jauna-versija { display: none; } }`;
    document.head.appendChild(stils);
    const p = document.createElement('div');
    p.className = 'jauna-versija';
    p.setAttribute('role', 'status');
    p.innerHTML = `<span>${Valoda.t('Pieejama jauna versija')}</span>` +
      `<button type="button" class="jv-atsvaidzinat"><svg class="ik" aria-hidden="true" focusable="false"><use href="ikonas/ikonas.svg#atkartot"></use></svg>${Valoda.t('Atsvaidzināt')}</button>` +
      `<button type="button" class="jv-aizvert" aria-label="${Valoda.t('Aizvērt paziņojumu')}"><svg class="ik" aria-hidden="true" focusable="false"><use href="ikonas/ikonas.svg#aizvert"></use></svg></button>`;
    p.querySelector('.jv-aizvert').addEventListener('click', () => p.remove());
    p.querySelector('.jv-atsvaidzinat').addEventListener('click', () => {
      // meklējumu saglabājam: pēc pārlādes ?q= to atver vēlreiz
      const q = (document.getElementById('jautajums')?.value || '').trim();
      const u = new URL(location.href);
      if (q && !u.searchParams.has('demo')) u.searchParams.set('q', q);
      location.replace(u.toString());
    });
    document.body.appendChild(p);
  }
})();
