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

  // Tukšais stāvoklis (kamēr nav rezultāta): 3 piemēri virs tēmu pogām (meklesana.js pirmaisSkats; stils.css paslēpj)
  saturs.insertAdjacentHTML('afterbegin', `${krizesMeklesana.pirmaisSkats('Uzrakstiet, kas notiek un kur. Piemēri:')}
    <div class="lapa-temas" role="group" aria-label="Biežākās tēmas">${TEMAS.map(([t, q]) =>
      `<button type="button" data-tema="${esc(q)}" aria-pressed="false"><span>${esc(t)}</span></button>`).join('')}</div>
    <div class="lapa-cilnes" role="tablist" aria-label="Lapas saturs">${CILNES.map(([k, t, p], i) =>
      `<button type="button" role="tab" id="cilne-${k}" aria-controls="lapa-${k}" aria-selected="${!i}" tabindex="${i ? -1 : 0}">${esc(t)}${p ? `<small>${esc(p)}</small>` : ''}</button>`).join('')}</div>
    <p class="lapa-kopsavilkums" id="lapa-kopsavilkums" aria-live="polite" aria-busy="true"><span class="skelets">LVĢMC brīdinājumi: ielādē…</span></p>
    <div id="lapa-rezultats" class="lapa-cilne" role="tabpanel" aria-labelledby="cilne-rezultats">
      <p class="lapa-tukss">Rezultātā: lēmums Jūsu vietai, tuvākās drošās vietas un ko darīt.</p>
    </div>
    <div id="lapa-slani" class="lapa-cilne" role="tabpanel" aria-labelledby="cilne-slani" hidden></div>
    <div id="lapa-situacija" class="lapa-cilne" role="tabpanel" aria-labelledby="cilne-situacija" hidden>
      <div class="lapa-prognoze"></div>
      <h3>Upju līmeņi kartes centra tuvumā</h3><ul class="lapa-saraksts" id="lapa-upes">${SKELETS}</ul>
      <h3>Ceļi (LVC)</h3><ul class="lapa-saraksts" id="lapa-celi">${SKELETS}</ul>
    </div>`);

  // ---- Elementu pārcelšana telefons ↔ dators ----
  // LVĢMC un demo josla telefonā — kartes augšmalā virs kartes (pārklāj, nevis bīda karti uz leju)
  el('kartes-laukums').insertAdjacentHTML('afterbegin', '<div class="kartes-joslas" id="kartes-joslas"></div>');
  const PARCELT = [
    [el('bridinajums'), el('kartes-joslas')],
    [el('demo-josla'), el('kartes-joslas')],
    [el('meklet-forma'), el('apaksa-meklet')],
    [el('panelis'), el('lapa-slani')],
    [el('statuss'), el('lapa-slani'), 'prepend'],
    [el('prognozes'), lapa.querySelector('.lapa-prognoze')],
  ].filter(([e]) => e).map(([e, kur, k]) => ({ e, kur, k, majas: e.parentElement, pec: e.nextSibling }));
  function novietot() {
    // atpakaļ — apgrieztā secībā, lai "pec" (nākamais kaimiņš, piem. demo josla aiz LVĢMC joslas) jau ir savā vietā
    for (const p of telefons.matches ? PARCELT : [...PARCELT].reverse()) {
      if (telefons.matches) {
        if (p.e.parentElement !== p.kur) p.k === 'prepend' ? p.kur.prepend(p.e) : p.kur.append(p.e);
      } else if (p.e.parentElement !== p.majas) p.majas.insertBefore(p.e, p.pec?.parentElement === p.majas ? p.pec : null);
    }
    if (typeof Apaksa !== 'undefined') Apaksa.novietot();  // rezultāts → cilne "Rezultāts" (vai atpakaļ sānu panelī)
    karte.invalidateSize();
    // Telefonā karte stiepjas arī zem lapas: robežas uz dienvidiem plašākas, lai Latviju var novietot virs lapas
    // (ar app.js robežām Leaflet karti centrē uz robežu vidu, un Latvija paliek zem lapas)
    karte.setMaxBounds(telefons.matches ? latvija.pad(0.3).extend([50.5, 24.5]) : latvija.pad(0.3));
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
  // Redzamās kartes daļas (virs lapas) centrs Latvijas robežās: telefonā karte stiepjas zem lapas, un /api/udens
  // ārpus Latvijas atbild 400
  function redzamaisCentrs() {
    const k = karte.getSize(), h = telefons.matches ? Math.max(40, k.y - Apaksa.augstums()) : k.y;
    const c = karte.containerPointToLatLng([k.x / 2, h / 2]);
    return L.latLng(Math.min(Math.max(c.lat, latvija.getSouth()), latvija.getNorth()), Math.min(Math.max(c.lng, latvija.getWest()), latvija.getEast()));
  }
  async function situacija() {
    const c = redzamaisCentrs();
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

  // Uznirstošie logi telefonā: automātiskā pārbīde lieto tās pašas atstarpes kā fitBounds (Apaksa.atstarpes(): augšā
  // joslas + "Karte | Reljefs", labajā pusē kartes pogu kolonna, apakšā lapa), un logs nekad nav augstāks par karti starp
  // tām (--popup-augstums, saturs ritinās). Ja logs neietilpst virs lapas, lapa uz laiku saplok līdz "Mazs" un pēc loga
  // aizvēršanas atgriežas. Demo cilne, kamēr logs atvērts, paslēpta (stils.css body.popups-atverts).
  const SMAILE = 24, POPUP_MIN = 160;
  let ieprieksStavoklis = null, atvertais = null;
  const popupVieta = (a = Apaksa.atstarpes()) => karte.getSize().y - a.paddingTopLeft[1] - 8 - a.paddingBottomRight[1] - SMAILE;
  function popupAtstarpes() {
    const o = L.Popup.prototype.options;
    if (!telefons.matches) {
      delete o.autoPanPaddingTopLeft; delete o.autoPanPaddingBottomRight; o.maxWidth = 300;
      karte.getContainer().style.removeProperty('--popup-augstums');
      return;
    }
    const a = Apaksa.atstarpes();
    const labi = a.paddingBottomRight[0];
    // platums: saturs + 50 px (malas, vieta ✕) starp kreiso malu (10 px) un kartes pogām labajā pusē
    o.maxWidth = Math.min(300, innerWidth - 10 - labi - 50);
    o.autoPanPaddingTopLeft = L.point(10, a.paddingTopLeft[1] + 8);  // + ēna zem "Karte | Reljefs"
    o.autoPanPaddingBottomRight = L.point(labi, a.paddingBottomRight[1]);
    karte.getContainer().style.setProperty('--popup-augstums', Math.max(POPUP_MIN, popupVieta(a)) + 'px');
  }
  // Pirms Leaflet pirmās pārbīdes (tā notiek pirms 'popupopen'): izlemj par lapas augstumu un atstarpēm
  const leafletPan = L.Popup.prototype._adjustPan;
  L.Popup.prototype._adjustPan = function () {
    if (telefons.matches && Apaksa.aktiva() && !this._lapaSagatavota) {
      this._lapaSagatavota = true;
      const w = this.getElement()?.querySelector('.leaflet-popup-content-wrapper');
      const c = w?.querySelector('.leaflet-popup-content');
      const st = Apaksa.stavoklis();
      if (c && st !== 'peek' && w.offsetHeight - c.clientHeight + c.scrollHeight > popupVieta()) {
        ieprieksStavoklis ??= st;
        Apaksa.atvert('peek');
      }
      popupAtstarpes();
    }
    return leafletPan.apply(this, arguments);
  };
  lapa.addEventListener('apaksa:stavoklis', popupAtstarpes);
  karte.on('popupopen', e => { atvertais = e.popup; document.body.classList.add('popups-atverts'); });
  karte.on('popupclose', e => {
    e.popup._lapaSagatavota = false;
    setTimeout(() => {  // cits logs var atvērties tajā pašā brīdī (autoClose) — tad lapu neatjauno
      if (atvertais !== e.popup) return;
      atvertais = null;
      document.body.classList.remove('popups-atverts');
      if (ieprieksStavoklis && Apaksa.stavoklis() === 'peek') Apaksa.atvert(ieprieksStavoklis);
      ieprieksStavoklis = null;
    }, 0);
  });
  // Logā atver/aizver "Vairāk" (objekta-statuss.js): logs kļūst augstāks — pārbīda vēlreiz, saturu nepārzīmējot
  document.addEventListener('toggle', e => {
    if (atvertais && e.target.closest?.('.leaflet-popup') && typeof atvertais._adjustPan === 'function') atvertais._adjustPan();
  }, true);

  telefons.addEventListener('change', () => { novietot(); popupAtstarpes(); });
  addEventListener('resize', popupAtstarpes);
  novietot();
  popupAtstarpes();
  // Sākuma skats telefonā: visa Latvija redzamajā kartes daļā virs lapas (citādi tās centrs paliek zem lapas un augšā
  // redzama Igaunija). Tikai ja karti vēl neviens nav pārvietojis (?q=, ?demo= un reģions skatu maina vēlāk).
  if (telefons.matches && karte.getCenter().distanceTo(latvija.getCenter()) < 20000) karte.fitBounds(latvija, Apaksa.atstarpes());
  kopsavilkums();
  setInterval(kopsavilkums, 10 * 60 * 1000);

  return { cilne, novietot };
})();
