// "Saraksts": kartes skatā ieslēgto slāņu objekti (app.js `skataObjekti` — /api/objekti?bbox= ielādētie, kas ir skatā)
// kā teksta saraksts — karte bez redzes, ar tastatūru vai mazā ekrānā. Atver poga slāņu panelī un rezultāta kartītē
// (data-darbiba="saraksts"). Telefonā saraksts ir apakšējā lapā (apaksa.js) stāvoklī "Pilns" un ritinās tās iekšpusē;
// datorā — kreisajā kolonnā (#panelis). Rinda = poga: forma un krāsa kā kartē (ikonas.js), nosaukums, slānis, attālums
// (no Jums / adreses / kartes centra), statusa zīme (objekta-statuss.js), avots un licence; patvertnēm vēl ietilpība,
// ratiņkrēsls un dzīvnieki, ja dati tos satur. Pieskaroties: karte uz vietu un tās logs. Esc aizver.
// Kārtošana (attālums / nosaukums), slāņu čipi un teksta filtrs; "Lejupielādēt CSV" (UTF-8 ar BOM, ar avotu un licenci)
// un drukas skats. Lieto app.js globālos (karte, kategorijas, stavoklis, ieladets, gaida, esc, attalums, nosaukums…).
const Saraksts = (() => {
  const SOLIS = 100;  // cik rindu zīmēt uzreiz; pārējās ar pogu "Rādīt vēl"
  const telefons = matchMedia('(max-width: 800px)');
  // Slāņi ar statusa bloku (objekta-statuss.js statusaBloks) un ar vietu ziņām (ietilpība, ratiņkrēsls, dzīvnieki)
  const AR_STATUSU = new Set(['patvertne', 'evakuacijas_punkts', 'izmitinasana', 'noturibas_punkts']);
  const AR_VIETAM = new Set(['patvertne', 'evakuacijas_punkts', 'izmitinasana']);
  const vienk = s => String(s ?? '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
  // Saraksta rāmis LV / RU / EN (valoda.js); dati (nosaukumi, adreses, slāņi, avoti) netiek tulkoti
  const t = (k, m) => typeof Valoda !== 'undefined' ? Valoda.t(k, m) : (m ? Object.entries(m).reduce((s, [a, b]) => s.split('{' + a + '}').join(b), k) : k);
  const isaisSlanis = kods => (kategorijas[kods]?.nosaukums || kods || '').replace(/\s*\([^)]*\)\s*$/, '');

  let sakne, ul, skaitaRinda, atskaitesRinda, velPoga, filtrs, kartot, cipi, atjaunotPoga, atvere = null;
  let visi = [], redzami = [], paradits = 0, atverts = false, piesprausts = false, aktivais = null, ritums = 0, taimeris = null;
  const izveletie = new Set();  // čipos izvēlētie slāņi; tukšs = visi

  function izveidot() {
    sakne = document.createElement('section');
    sakne.id = 'saraksts';
    sakne.className = 'saraksts';
    sakne.hidden = true;
    sakne.setAttribute('aria-labelledby', 'saraksts-virsraksts');
    sakne.innerHTML = `
      <div class="saraksts-galva">
        <div class="saraksts-galva-rinda">
          <h2 id="saraksts-virsraksts" tabindex="-1">${Ik('saraksts')} <span data-t="Vietas kartes skatā"></span></h2>
          <button type="button" class="saraksts-aizvert" aria-label="Aizvērt sarakstu">${Ik('aizvert')}</button>
        </div>
        <p class="saraksts-skaits" role="status" aria-live="polite"></p>
        <div class="saraksts-riki">
          <input type="search" class="saraksts-filtrs" data-t-placeholder="Meklēt sarakstā" autocomplete="off">
          <select class="saraksts-kartot">
            <option value="att" data-t="Tuvākās"></option><option value="nos" data-t="Pēc nosaukuma"></option>
          </select>
        </div>
        <div class="saraksts-cipi" role="group"></div>
      </div>
      <p class="saraksts-atskaite piezime"></p>
      <button type="button" class="otra saraksts-atjaunot" data-t="Karte pārvietota — atjaunot sarakstu" hidden></button>
      <ul class="saraksts-ul"></ul>
      <button type="button" class="otra saraksts-vel" hidden></button>
      <div class="saraksts-darbibas">
        <button type="button" class="otra" data-saraksts="csv">${Ik('lejupielade')} <span data-t="Lejupielādēt CSV"></span></button>
        <button type="button" class="otra" data-saraksts="drukat" data-t="Drukāt sarakstu"></button>
      </div>`;
    ul = sakne.querySelector('.saraksts-ul');
    skaitaRinda = sakne.querySelector('.saraksts-skaits');
    atskaitesRinda = sakne.querySelector('.saraksts-atskaite');
    velPoga = sakne.querySelector('.saraksts-vel');
    filtrs = sakne.querySelector('.saraksts-filtrs');
    kartot = sakne.querySelector('.saraksts-kartot');
    cipi = sakne.querySelector('.saraksts-cipi');
    atjaunotPoga = sakne.querySelector('.saraksts-atjaunot');

    sakne.querySelector('.saraksts-aizvert').addEventListener('click', () => aizvert());
    velPoga.addEventListener('click', () => paradit(SOLIS));
    atjaunotPoga.addEventListener('click', () => { piesprausts = false; parladet(); });
    filtrs.addEventListener('input', () => { clearTimeout(taimeris); taimeris = setTimeout(atlasit, 120); });
    kartot.addEventListener('change', atlasit);
    cipi.addEventListener('click', e => {
      const c = e.target.closest('[data-kat]');
      if (!c) return;
      const k = c.dataset.kat;
      if (izveletie.has(k)) izveletie.delete(k); else izveletie.add(k);
      atlasit();
    });
    ul.addEventListener('click', e => {
      const b = e.target.closest('[data-i]');
      if (b) radit(redzami[+b.dataset.i], b);
    });
    sakne.querySelector('[data-saraksts="csv"]').addEventListener('click', lejupieladet);
    sakne.querySelector('[data-saraksts="drukat"]').addEventListener('click', drukat);
    sakne.addEventListener('keydown', e => {
      if (e.key !== 'Escape') return;
      if (e.target === filtrs && filtrs.value) return;  // pirmais Esc notīra meklēšanas lauku (pārlūks)
      e.preventDefault();
      aizvert();
    });
    tulkot();
    novietot();
  }

  // Rāmja teksti aktīvajā valodā: data-t / data-t-placeholder (tos maina arī valoda.js slēdzis) un aria-label
  function tulkot() {
    sakne.querySelectorAll('[data-t]').forEach(e => { e.textContent = t(e.dataset.t); });
    sakne.querySelectorAll('[data-t-placeholder]').forEach(e => { e.placeholder = t(e.dataset.tPlaceholder); });
    sakne.querySelector('.saraksts-aizvert').setAttribute('aria-label', t('Aizvērt sarakstu'));
    filtrs.setAttribute('aria-label', t('Filtrēt sarakstu pēc nosaukuma vai adreses'));
    kartot.setAttribute('aria-label', t('Kārtošana'));
    cipi.setAttribute('aria-label', t('Rādīt slāņus'));
    sakne.lang = typeof Valoda !== 'undefined' ? Valoda.aktiva() : 'lv';
  }

  // Telefonā — apakšējās lapas saturs (pirms cilnēm), datorā — kreisā kolonna
  function novietot() {
    if (!sakne) return;
    const kur = telefons.matches ? el('apaksa-saturs') : el('panelis');
    if (kur && sakne.parentElement !== kur) kur.prepend(sakne);
  }
  telefons.addEventListener('change', () => {
    novietot();
    if (atverts && telefons.matches && typeof Apaksa !== 'undefined') Apaksa.atvert('pilna');
  });

  // Atskaites punkts attālumam: Jūsu vieta vai izvēlētā adrese; citādi kartes centrs
  function atskaite() {
    const v = stavoklis.vieta;
    if (v) return { ll: L.latLng(v.lat, v.lon), no: t(v.adrese ? 'no adreses' : 'no Jums'),
      apraksts: v.adrese ? t('adreses {adrese}', { adrese: isaAdrese(v.adrese) }) : t('Jūsu atrašanās vietas') };
    return { ll: karte.getCenter(), no: t('no kartes centra'), apraksts: t('kartes centra') };
  }

  // Statusa zīme: tikai slāņiem ar statusa bloku vai objektiem ar statusa datiem. Svaigs (≤ 6 h) un nav "slēgts" → atvērts.
  function statusaZime(p) {
    const i = p.ipasibas || {};
    const irDati = (i.statuss && typeof i.statuss === 'object') || typeof i.statuss === 'string' || i.atverts != null || i.darbojas != null;
    if (!AR_STATUSU.has(p.kategorija) && !irDati) return null;
    const ne = ObjektaStatuss.nepieejams(p);
    if (ne) return { klase: 'slegts', teksts: t(ne) };
    if (irDati && ObjektaStatuss.svaigs(i.last_updated)) return { klase: 'atverts', teksts: t('atvērts') };
    return { klase: 'nezinams', teksts: t('statuss nav zināms') };
  }

  const JA_NE = v => v === true || /^(ir|jā|ja|yes|limited|daļēji)$/i.test(String(v ?? '')) ? 'ir'
    : v === false || /^(nav|nē|ne|no)$/i.test(String(v ?? '')) ? 'nav' : (v == null || v === '' ? null : String(v));
  // Patvertņu un evakuācijas vietu ziņas, ja tās ir datos (112.lv datos parasti tikai ēkas veids un adrese)
  function vietasZinas(p) {
    if (!AR_VIETAM.has(p.kategorija)) return null;
    const i = p.ipasibas || {};
    const n = +(i.ietilpiba ?? i.vietas ?? i.capacity);
    return {
      ietilpiba: Number.isFinite(n) && n > 0 ? n : null,
      ratini: JA_NE(i.ratinkresls ?? i.wheelchair),
      dzivnieki: JA_NE(i.dzivnieki ?? i.majdzivnieki),
      veids: i.veids && i.veids !== p.nosaukums ? i.veids : null,
    };
  }

  // Viena saraksta ieraksts: aprēķina vienreiz (attālums, kārtošanas un filtra teksts)
  function ieraksts(f, no) {
    const p = f.properties;
    const ll = f._slanis.getLatLng();
    const k = kategorijas[p.kategorija] || {};
    const nos = nosaukums(p) || k.nosaukums || 'Objekts';
    return { f, ll, nos, kat: p.kategorija, m: Math.round(no.distanceTo(ll)), kartot: kartosanai(p) || nos,
      meklet: vienk([nos, p.adrese, k.nosaukums, p.ipasibas?.veids].join(' ')), statuss: statusaZime(p), vieta: vietasZinas(p) };
  }

  function avotaZime(kods) {
    const a = Avoti.dati(kods);
    if (!a) return '';
    return `<span class="saraksts-avots">${esc(a.izdevejs || a.nosaukums)} · ${esc(a.licence || t('licence nav norādīta'))}` +
      `${a.atverts === false ? ' ' + Ik('uzmanibu') + `<span class="vizuali-slepts"> (${t('nav atvērtas licences')})</span>` : ''}</span>`;
  }

  function vietasTeksts(v) {
    if (!v) return '';
    const d = [];
    if (v.veids) d.push(esc(v.veids));
    if (v.ietilpiba) d.push(t('{n} vietas', { n: v.ietilpiba }));
    if (v.ratini) d.push(`${t('ratiņkrēslam')}: ${esc(t(v.ratini))}`);
    if (v.dzivnieki) d.push(`${t('dzīvnieki')}: ${esc(t(v.dzivnieki))}`);
    return d.length ? `<span class="saraksts-vieta">${d.join(' · ')}</span>` : '';
  }

  function rinda(r, i, no) {
    const p = r.f.properties;
    const slanis = isaisSlanis(r.kat);
    return `<li><button type="button" class="saraksts-rinda" data-i="${i}"${r === aktivais ? ' aria-current="true"' : ''}>
      <span class="saraksts-forma">${Ikonas.formaHTML(r.kat, 22)}</span>
      <span class="saraksts-teksts">
        <span class="saraksts-nos">${esc(r.nos)}</span>
        <span class="saraksts-meta">${esc(slanis)}${p.adrese ? ' · ' + esc(p.adrese) : ''}</span>
        ${vietasTeksts(r.vieta)}
        <span class="saraksts-zimes">${r.statuss ? `<span class="saraksts-statuss st-${r.statuss.klase}">${esc(r.statuss.teksts)}</span>` : ''}${avotaZime(p.avots)}</span>
      </span>
      <span class="saraksts-att">${attalums(r.m)}<small>${no}</small></span>
    </button></li>`;
  }

  // Ielādētie skata objekti → visi; tad čipi un atlase
  function parladet() {
    if (!sakne) return;
    atjaunotPoga.hidden = true;
    const no = atskaite();
    visi = stavoklis.kategorijas.size ? skataObjekti().map(f => ieraksts(f, no.ll)) : [];
    if (aktivais) aktivais = visi.find(r => r.f === aktivais.f) || null;
    for (const k of [...izveletie]) if (!visi.some(r => r.kat === k)) izveletie.delete(k);
    atlasit();
  }

  function zimetCipus() {
    const skaits = {};
    for (const r of visi) skaits[r.kat] = (skaits[r.kat] || 0) + 1;
    const kodi = Object.keys(skaits).sort((a, b) => (kategorijas[a]?.kartiba ?? 99) - (kategorijas[b]?.kartiba ?? 99));
    cipi.hidden = kodi.length < 2;
    cipi.innerHTML = kodi.map(k => `<button type="button" class="saraksts-cips" data-kat="${esc(k)}" aria-pressed="${izveletie.has(k)}">` +
      `${Ikonas.formaHTML(k, 16)}<span>${esc(isaisSlanis(k))}</span><span class="saraksts-cips-skaits">${skaits[k]}</span></button>`).join('');
  }

  // Filtrs + čipi + kārtošana → redzami; zīmē pirmās SOLIS rindas
  function atlasit() {
    const vardi = vienk(filtrs.value).split(/\s+/).filter(Boolean);
    redzami = visi.filter(r => (!izveletie.size || izveletie.has(r.kat)) && vardi.every(v => r.meklet.includes(v)));
    if (kartot.value === 'nos') redzami.sort((a, b) => a.kartot.localeCompare(b.kartot, 'lv'));
    else redzami.sort((a, b) => a.m - b.m);
    zimetCipus();
    ul.innerHTML = '';
    paradits = 0;
    paradit(SOLIS);
    skaitaTeksts();
  }

  function skaitaTeksts() {
    const no = atskaite();
    atskaitesRinda.textContent = visi.length
      ? t(kartot.value === 'nos' ? 'Sakārtots pēc nosaukuma; attālums no {kur} (taisnā līnijā).' : 'Sakārtots pēc attāluma no {kur} (taisnā līnijā).', { kur: no.apraksts }) : '';
    if (!stavoklis.kategorijas.size) {
      skaitaRinda.textContent = t('Nav ieslēgts neviens slānis. Ieslēdziet slāni (piem., Publiskās patvertnes) vai meklējiet augšā.');
      return;
    }
    if (gaida) { skaitaRinda.textContent = t('Ielādē vietas kartes skatā…'); return; }
    if (!visi.length) { skaitaRinda.textContent = t('Kartes skatā vietu nav. Attāliniet vai pārvietojiet karti.'); return; }
    // latviski ar pareizo skaitli (1 vieta, 2 vietas); RU / EN bez skaitļa formām ("Мест в области карты: N")
    let teksts = t('{vietas} skatā', { n: visi.length, vietas: daudzskaitlis(visi.length, 'vieta', 'vietas') });
    if (redzami.length !== visi.length) teksts += ' · ' + t('filtrā {n}', { n: redzami.length });
    if (ieladets?.apgriezts) teksts += ' · ' + t('rādīti pirmie {n}, pietuviniet karti, lai redzētu visas', { n: karte.getZoom() < SKATA_ZOOM ? VALSTS_LIMITS : SKATA_LIMITS });
    skaitaRinda.textContent = teksts;
  }

  function paradit(cik) {
    const no = atskaite().no;
    const lidz = Math.min(redzami.length, paradits + cik);
    let html = '';
    for (let i = paradits; i < lidz; i++) html += rinda(redzami[i], i, no);
    ul.insertAdjacentHTML('beforeend', html);
    if (!redzami.length && visi.length) ul.innerHTML = `<li class="saraksts-tukss">${t('Filtram neatbilst neviena vieta.')}</li>`;
    paradits = lidz;
    const atlikums = redzami.length - paradits;
    velPoga.hidden = atlikums <= 0;
    velPoga.textContent = t('Rādīt vēl {n} (kopā {kopa})', { n: Math.min(SOLIS, atlikums), kopa: redzami.length });
  }

  // Rinda → karte uz vietu un tās logs. Telefonā lapa saplok līdz "Mazs" un punkts ir redzamajā kartes daļā virs tās.
  // Saraksts paliek "piesprausts": kartes kustība to vairs nepārzīmē, līdz lietotājs pats pavelk karti vai nospiež "atjaunot".
  function radit(r, poga) {
    if (!r) return;
    aktivais = r;
    ul.querySelectorAll('[aria-current]').forEach(b => b.removeAttribute('aria-current'));
    poga?.setAttribute('aria-current', 'true');
    piesprausts = true;
    const z = Math.max(karte.getZoom(), 16);
    if (telefons.matches && typeof Apaksa !== 'undefined' && Apaksa.aktiva()) {
      ritums = el('apaksa-saturs').scrollTop;
      Apaksa.atvert('peek');
      // punkts redzamās daļas lejasdaļā (logs atveras virs tā), nevis karte centrā zem lapas
      const y = karte.getSize().y, merkis = Math.max(y / 2, y - Apaksa.augstums() - 48);
      const centrs = karte.unproject(karte.project(r.ll, z).subtract([0, merkis - y / 2]), z);
      karte.setView(centrs, z, { animate: false });
    } else {
      karte.setView(r.ll, z, { animate: false });
    }
    L.popup().setLatLng(r.ll).setContent(popupSaturs(r.f.properties, r.ll)).openOn(karte);
  }

  // Lapa atkal "Pilns" pēc rindas atvēršanas → atpakaļ tajā pašā saraksta vietā (apaksa.js ritinājumu nonullē)
  el('apaksa')?.addEventListener('apaksa:stavoklis', e => {
    if (atverts && e.detail === 'pilna' && ritums) requestAnimationFrame(() => { el('apaksa-saturs').scrollTop = ritums; });
  });

  // Kartes skats vai slāņi mainījās → saraksts seko (ja nav piesprausts pie atvērtas rindas)
  function skatsMainijas() {
    if (!atverts) return;
    if (piesprausts) { atjaunotPoga.hidden = false; return; }
    parladet();
  }
  document.addEventListener('karte:objekti', skatsMainijas);
  karte.on('moveend', () => { if (atverts && !gaida) { clearTimeout(taimeris); taimeris = setTimeout(skatsMainijas, 150); } });
  karte.on('dragstart', () => { piesprausts = false; });

  function atvert(no) {
    if (!sakne) izveidot();
    atvere = no || document.activeElement;
    novietot();
    atverts = true;
    piesprausts = false;
    aktivais = null;
    ritums = 0;
    sakne.hidden = false;
    tulkot();
    document.body.classList.add('saraksts-atverts');
    if (telefons.matches && typeof Apaksa !== 'undefined') Apaksa.atvert('pilna');
    else {
      document.body.classList.remove('dv-kreisa-slegta');  // kreisā kolonna redzama
      if (typeof Darbvirsma !== 'undefined' && !el('dv-atvilktne')?.hidden) Darbvirsma.raditAtvilktni?.(false);
      setTimeout(() => karte.invalidateSize(), 0);
    }
    parladet();
    sakne.parentElement.scrollTop = 0;
    sakne.querySelector('h2').focus({ preventScroll: true });
  }

  function aizvert() {
    if (!atverts) return;
    atverts = false;
    sakne.hidden = true;
    document.body.classList.remove('saraksts-atverts');
    ul.innerHTML = '';
    visi = redzami = [];
    if (atvere?.isConnected && atvere.offsetParent !== null) atvere.focus();
  }

  // ---- CSV (Excel ar latviešu reģionu: atdalītājs ";", UTF-8 ar BOM) ----
  const sunas = v => {
    let s = String(v ?? '');
    if (/^[=+\-@\t\r]/.test(s)) s = "'" + s;  // formulas neizpilda
    return /[";\n\r]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
  };
  function lejupieladet() {
    const no = atskaite();
    const kolonnas = ['Nosaukums', 'Slānis', 'Adrese', 'Platums', 'Garums', 'Attālums, m', 'Attālums no', 'Statuss',
      'Ēkas veids', 'Ietilpība', 'Ratiņkrēslam', 'Dzīvnieki', 'Avots', 'Izdevējs', 'Licence', 'Licences saite', 'Datu kopa'].map(k => t(k));
    const rindas = redzami.map(r => {
      const p = r.f.properties, a = Avoti.dati(p.avots) || {}, v = r.vieta || {};
      return [r.nos, kategorijas[r.kat]?.nosaukums || r.kat, p.adrese, r.ll.lat.toFixed(6), r.ll.lng.toFixed(6), r.m, no.apraksts,
        r.statuss?.teksts, v.veids, v.ietilpiba, v.ratini, v.dzivnieki, a.nosaukums || p.avots, a.izdevejs, a.licence,
        a.licences_url, a.datu_kopa_url];
    });
    const teksts = [kolonnas, ...rindas].map(r => r.map(sunas).join(';')).join('\r\n');
    const url = URL.createObjectURL(new Blob(['﻿' + teksts + '\r\n'], { type: 'text/csv;charset=utf-8' }));
    const a = document.createElement('a');
    a.href = url;
    a.download = `map-repo-lv-vietas-${new Date().toISOString().slice(0, 10)}.csv`;
    document.body.append(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  // ---- Drukas skats: tabula ar visām atlasītajām vietām (ne tikai pirmajām 100) un avotu sarakstu ----
  function drukat() {
    el('saraksts-druka')?.remove();
    const no = atskaite();
    const avoti = [...new Set(redzami.map(r => r.f.properties.avots))].map(Avoti.dati).filter(Boolean);
    const d = document.createElement('div');
    d.id = 'saraksts-druka';
    d.lang = sakne.lang;
    d.innerHTML = `<h1>${esc(t('Vietas kartes skatā'))} — map.repo.lv</h1>
      <p>${esc(new Date().toLocaleString('lv-LV'))} · ${esc(skaitaRinda.textContent)} · ${esc(t('attālums no {kur} (taisnā līnijā)', { kur: no.apraksts }))}</p>
      <p>${esc(t('Ja apdraudēta dzīvība vai veselība, zvaniet 112.'))}</p>
      <table><thead><tr>${['Nr.', 'Vieta', 'Slānis', 'Adrese', 'Attālums', 'Statuss', 'Avots, licence'].map(k => `<th>${esc(t(k))}</th>`).join('')}</tr></thead><tbody>` +
      redzami.map((r, i) => {
        const p = r.f.properties, a = Avoti.dati(p.avots);
        return `<tr><td>${i + 1}</td><td>${esc(r.nos)}${r.vieta ? '<br>' + vietasTeksts(r.vieta) : ''}</td><td>${esc(isaisSlanis(r.kat))}</td>` +
          `<td>${esc(p.adrese || '')}</td><td>${attalums(r.m)}</td><td>${esc(r.statuss?.teksts || '')}</td>` +
          `<td>${a ? esc(`${a.izdevejs || a.nosaukums} · ${a.licence || t('licence nav norādīta')}`) : ''}</td></tr>`;
      }).join('') + `</tbody></table>
      <h2>${esc(t('Datu avoti'))}</h2><ul>${avoti.map(a => `<li>${esc(a.nosaukums)} (${esc(a.izdevejs)}) · ${esc(a.licence || t('licence nav norādīta'))}` +
        `${a.datu_kopa_url ? ' · ' + esc(a.datu_kopa_url) : ''}</li>`).join('')}</ul>`;
    document.body.append(d);
    document.body.classList.add('druka-saraksts');
    const beigt = () => { document.body.classList.remove('druka-saraksts'); d.remove(); };
    addEventListener('afterprint', beigt, { once: true });
    window.print();
  }

  document.addEventListener('click', e => {
    const b = e.target.closest('[data-darbiba="saraksts"]');
    if (b) atvert(b);
    // valodas slēdzis (valoda.js) → atvērtā saraksta rāmis, rindas un skaits jaunajā valodā
    else if (atverts && e.target.closest('.valoda-sledzis [data-valoda]')) setTimeout(() => { tulkot(); atlasit(); }, 0);
  });

  return { atvert, aizvert, atverts: () => atverts };
})();
