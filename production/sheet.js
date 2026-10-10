// Telefonā (≤ 800 px) apakšējās lapas saturs pēc lietotāja maketa (notes/ui-mockup.md "Mobile"):
// meklēšana → tēmu pogas → cilnes → kopsavilkums "2 oranži · 5 dzelteni · Atjaunots …"; cilnes:
// Rezultāts (Lēmums) · Kartes slāņi · Situācija tagad (LVĢMC).
// Telefonā meklēšanas forma, slāņu panelis (#panelis) un prognožu lente (#prognozes) tiek pārcelti lapā; datorā — atpakaļ
// savās vietās (nekas nemainās). Lieto apaksa.js (Apaksa), app.js globālos (karte, el, esc, iegut, attalums) un Prognozes.
const Lapa = (() => {
  const telefons = matchMedia('(max-width: 800px)');
  const lapa = el('apaksa');
  if (!lapa) return null;
  const saturs = el('apaksa-saturs');
  const TEMAS = [['Plūdi', 'plūdi'], ['Nav elektrības', 'nav elektrības'], ['Evakuācija', 'evakuācija'], ['Patvertne', 'patvertne'],
    ['Ārsts', 'ārsts'], ['Ceļi', 'ceļš slēgts'], ['Vētra', 'vētra'], ['Dzeramais ūdens', 'nav ūdens']];
  const CILNES = [['rezultats', 'Rezultāts', 'Lēmums'], ['slani', 'Kartes slāņi', ''], ['situacija', 'Situācija tagad', 'LVĢMC']];

  // Ielādes vietturis (pelēkas joslas, nevis "Ielādē…"): saraksta augstums nelec, kad dati atnāk
  const SKELETS = '<li class="skelets-rinda" aria-hidden="true"><span></span><span></span></li>'.repeat(3);

  saturs.insertAdjacentHTML('afterbegin', `
    <div class="lapa-temas" role="group" aria-label="Biežākās tēmas">${TEMAS.map(([t, q]) =>
      `<button type="button" data-tema="${esc(q)}" aria-pressed="false"><span>${esc(t)}</span></button>`).join('')}</div>
    <div class="lapa-cilnes" role="tablist" aria-label="Lapas saturs">${CILNES.map(([k, t, p], i) =>
      `<button type="button" role="tab" id="cilne-${k}" aria-controls="lapa-${k}" aria-selected="${!i}" tabindex="${i ? -1 : 0}">${esc(t)}${p ? `<small>${esc(p)}</small>` : ''}</button>`).join('')}</div>
    <p class="lapa-kopsavilkums" id="lapa-kopsavilkums" aria-live="polite" aria-busy="true"><span class="skelets">LVĢMC brīdinājumi: ielādē…</span></p>
    <div id="lapa-rezultats" class="lapa-cilne" role="tabpanel" aria-labelledby="cilne-rezultats">
      <p class="lapa-tukss">Uzrakstiet, kas notiek, vai izvēlieties tēmu augstāk. Rezultātā: lēmums Jūsu vietai, tuvākās drošās vietas un ko darīt.</p>
    </div>
    <div id="lapa-slani" class="lapa-cilne" role="tabpanel" aria-labelledby="cilne-slani" hidden></div>
    <div id="lapa-situacija" class="lapa-cilne" role="tabpanel" aria-labelledby="cilne-situacija" hidden>
      <div class="lapa-prognoze"></div>
      <h3>Upju līmeņi kartes centra tuvumā</h3><ul class="lapa-saraksts" id="lapa-upes">${SKELETS}</ul>
      <h3>Ceļi (LVC)</h3><ul class="lapa-saraksts" id="lapa-celi">${SKELETS}</ul>
    </div>`);

  // ---- Elementu pārcelšana telefons ↔ dators ----
  const PARCELT = [
    [el('meklet-forma'), el('apaksa-meklet')],
    [el('panelis'), el('lapa-slani')],
    [el('statuss'), el('lapa-slani'), 'prepend'],
    [el('prognozes'), lapa.querySelector('.lapa-prognoze')],
  ].filter(([e]) => e).map(([e, kur, k]) => ({ e, kur, k, majas: e.parentElement, pec: e.nextSibling }));
  function novietot() {
    for (const p of PARCELT) {
      if (telefons.matches) {
        if (p.e.parentElement !== p.kur) p.k === 'prepend' ? p.kur.prepend(p.e) : p.kur.append(p.e);
      } else if (p.e.parentElement !== p.majas) p.majas.insertBefore(p.e, p.pec?.parentElement === p.majas ? p.pec : null);
    }
    if (typeof Apaksa !== 'undefined') Apaksa.novietot();  // rezultāts → cilne "Rezultāts" (vai atpakaļ sānu panelī)
    karte.invalidateSize();
  }

  // ---- Cilnes ----
  const cilnes = [...lapa.querySelectorAll('[role="tab"]')];
  function cilne(k, fokuss = false) {
    for (const c of cilnes) {
      const ir = c.id === 'cilne-' + k;
      c.setAttribute('aria-selected', ir);
      c.tabIndex = ir ? 0 : -1;
      el(c.getAttribute('aria-controls')).hidden = !ir;
      if (ir && fokuss) c.focus();
    }
    if (k === 'situacija') situacija();
  }
  lapa.querySelector('.lapa-cilnes').addEventListener('click', e => { const c = e.target.closest('[role="tab"]'); if (c) cilne(c.id.slice(6)); });
  lapa.querySelector('.lapa-cilnes').addEventListener('keydown', e => {
    const i = cilnes.indexOf(document.activeElement);
    if (i < 0 || !['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(e.key)) return;
    e.preventDefault();
    const j = e.key === 'Home' ? 0 : e.key === 'End' ? cilnes.length - 1 : (i + (e.key === 'ArrowRight' ? 1 : -1) + cilnes.length) % cilnes.length;
    cilne(cilnes[j].id.slice(6), true);
  });
  lapa.addEventListener('apaksa:rezultats', () => cilne('rezultats'));

  // ---- Tēmas: viena poga = viena meklēšana ----
  lapa.querySelector('.lapa-temas').addEventListener('click', e => {
    const q = e.target.closest('[data-tema]')?.dataset.tema;
    if (!q) return;
    atzimetTemu(q);
    el('jautajums').value = q;
    el('meklet-forma').requestSubmit();
  });

  // Aktīvā tēma: tā, ar ko sākas pašreizējais vaicājums (arī ja ierakstīts ar roku)
  function atzimetTemu(q = el('jautajums').value) {
    const v = q.trim().toLowerCase();
    for (const b of lapa.querySelectorAll('[data-tema]')) b.setAttribute('aria-pressed', !!v && v.startsWith(b.dataset.tema));
  }
  el('meklet-forma').addEventListener('submit', () => atzimetTemu());

  // Gaidīšanas teksti rezultātā ("Meklē adresi…", "Pārbauda…") → pelēka josla (skelets), kamēr atbilde nav atnākusi
  const kaste = el('rezultati');
  new MutationObserver(() => {
    for (const e of kaste.querySelectorAll('p.piezime, #rezultati .fakti li > div > span')) {
      e.classList.toggle('skelets', /^(Meklē|Pārbauda|Ielādē)[^.]*…/.test(e.textContent.trim()));
    }
  }).observe(kaste, { childList: true, subtree: true, characterData: true });

  // ---- Kopsavilkums: LVĢMC brīdinājumu skaits pēc līmeņa + atjaunošanas laiks ----
  const LIM = { 3: ['sarkans', 'sarkani'], 2: ['oranžs', 'oranži'], 1: ['dzeltens', 'dzelteni'] };
  // Brīdinājumi — /api/bridinajumi; ja to nav, prognozes (/api/prognozes) šodienas augstākais risks. Laiks — jaunākais no abiem.
  const RISKS = { 1: 'paaugstināts', 2: 'augsts', 3: 'ļoti augsts' };
  async function kopsavilkums() {
    const p = el('lapa-kopsavilkums');
    const [b, pr] = await Promise.allSettled([iegut('/bridinajumi'), iegut('/prognozes')]);
    if (b.status !== 'fulfilled') {
      p.textContent = 'LVĢMC brīdinājumus neizdevās ielādēt.';
      p.removeAttribute('aria-busy');
      return;
    }
    const sk = {};
    for (const x of b.value.bridinajumi) sk[x.limenis] = (sk[x.limenis] || 0) + 1;
    const limeni = [3, 2, 1].filter(l => sk[l]);
    const dalas = limeni.map(l => `${sk[l]} ${LIM[l][sk[l] === 1 ? 0 : 1]}`);
    const riski = pr.status === 'fulfilled' ? (pr.value.zinas || []).filter(z => z.veids === 'riski' && z.diena === 'Šodien') : [];
    const risks = Math.max(0, ...riski.map(z => z.limenis || 0));
    const laiki = [b.value.laiks_lv, pr.value?.laiks_lv].filter(Boolean).map(t => new Date(t)).filter(t => !isNaN(t));
    const laiks = laiki.length ? new Date(Math.max(...laiki)) : null;
    const sodien = laiks && laiks.toDateString() === new Date().toDateString();
    const kad = laiks ? `Atjaunots ${sodien ? 'šodien' : laiks.toLocaleDateString('lv-LV', { day: '2-digit', month: '2-digit' })} ` +
      laiks.toLocaleTimeString('lv-LV', { hour: '2-digit', minute: '2-digit' }) : '';
    const kreisi = limeni.length
      ? limeni.map(l => `<span class="kops-lim" data-limenis="${l}">${sk[l]} ${LIM[l][sk[l] === 1 ? 0 : 1]}</span>`).join('')
      : `<span class="kops-lim" data-limenis="0">Brīdinājumu nav</span>` + (risks ? `<span class="kops-lim" data-limenis="${risks}">Šodien ${RISKS[risks]} risks</span>` : '');
    p.innerHTML = `<span class="kops-kreisi" title="LVĢMC hidrometeoroloģiskie brīdinājumi">${kreisi}</span>${kad ? `<span class="kops-laiks">${esc(kad)}</span>` : ''}`;
    p.setAttribute('aria-label', 'LVĢMC: ' + (dalas.length ? dalas.join(', ') + ' brīdinājumi' : 'brīdinājumu nav') + (kad ? '. ' + kad : ''));
    p.removeAttribute('aria-busy');
    p.dataset.limenis = Math.max(0, ...limeni);
    lapa.dataset.kopsavilkums = dalas.length ? `Latvijā: ${dalas.join(', ')} brīdinājumi` : 'Latvijā LVĢMC brīdinājumu nav';
    if (typeof Apaksa !== 'undefined') Apaksa.atjaunotSpriedumu();
  }

  // ---- Situācija tagad: prognožu lente (pārcelta), upju līmeņi un ceļu notikumi ap kartes centru ----
  const komats = x => String(x).replace('.', ',');
  async function situacija() {
    const c = karte.getCenter();
    const ll = { lat: c.lat.toFixed(4), lon: c.lng.toFixed(4) };
    const upes = el('lapa-upes'), celi = el('lapa-celi');
    iegut('/udens?' + new URLSearchParams({ ...ll, limit: 5 })).then(d => {
      upes.innerHTML = d.stacijas.map(s => {
        const izm = s.izmaina_24h_cm;
        const tend = izm == null ? '' : izm > 0 ? `↑ +${izm} cm` : izm < 0 ? `↓ −${Math.abs(izm)} cm` : '→ 0 cm';
        return `<li tabindex="0" data-lat="${s.lat}" data-lon="${s.lon}"><b>${esc(s.nosaukums)}</b><span>${s.limenis_cm} cm${s.limenis_m != null ? ` (${komats(s.limenis_m)} m)` : ''}` +
          ` · 24 h: ${tend || '—'}${s.vecs ? ' · dati novecojuši' : ''}</span><small>${attalums(s.attalums_m)} no kartes centra</small></li>`;
      }).join('') + '<li class="avots-rinda">LVĢMC hidroloģiskie novērojumi · CC0</li>';
    }).catch(() => { upes.innerHTML = '<li class="piezime">Upju līmeņus neizdevās ielādēt.</li>'; });
    iegut('/celi').then(d => {
      const n = (d.notikumi || []).map(x => ({ ...x, m: L.latLng(x.lat, x.lon).distanceTo(c) })).sort((a, b) => a.m - b.m);
      const veidi = {};
      for (const x of n) veidi[x.nosaukums] = (veidi[x.nosaukums] || 0) + 1;
      celi.innerHTML = `<li class="lapa-celi-kopa">Latvijā tagad: ${Object.entries(veidi).map(([k, v]) => `${esc(k)} ${v}`).join(' · ') || 'notikumu nav'}</li>` +
        n.slice(0, 5).map(x => `<li tabindex="0" data-lat="${x.lat}" data-lon="${x.lon}"><b>${esc(x.nosaukums)}</b>` +
          `<span>${esc((x.apraksts || '').slice(0, 120))}</span><small>${attalums(Math.round(x.m))} no kartes centra</small></li>`).join('') +
        '<li class="avots-rinda">VSIA „Latvijas Valsts ceļi”, DATEX II (transportdata.gov.lv) · CC0</li>';
    }).catch(() => { celi.innerHTML = '<li class="piezime">Ceļu datus neizdevās ielādēt.</li>'; });
  }
  // Pieskaroties upei vai ceļa notikumam: karte uz turieni, lapa uz "Mazs", lai redzams
  lapa.querySelector('#lapa-situacija').addEventListener('click', e => {
    const li = e.target.closest('li[data-lat]');
    if (!li || e.target.closest('a')) return;
    karte.setView([+li.dataset.lat, +li.dataset.lon], 13);
    Apaksa.atvert('peek');
  });
  lapa.querySelector('#lapa-situacija').addEventListener('keydown', e => { if (e.key === 'Enter' && e.target.matches('li[data-lat]')) e.target.click(); });

  // ---- Kartes poga "Slāņi" (labajā pusē zem + − ◎) → lapa ar cilni "Kartes slāņi" ----
  el('slani-poga')?.addEventListener('click', () => { cilne('slani'); Apaksa.atvert('puse'); });

  telefons.addEventListener('change', novietot);
  novietot();
  kopsavilkums();
  setInterval(kopsavilkums, 10 * 60 * 1000);

  return { cilne };
})();
