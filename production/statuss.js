// Sistēmu statuss (/api/statuss): kartes un tās datu avotu pārbaužu rezultāti, 96 intervāli pa 15 min (24 h).
// Testam: statuss.html?dati=/<ceļš> pārraksta datu adresi (tikai šī paša servera ceļš).
(() => {
  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const saite = (url, teksts) => /^https?:\/\//.test(url || '')
    ? `<a href="${esc(url)}" target="_blank" rel="noopener">${esc(teksts)}</a>` : esc(teksts);
  const tests = new URLSearchParams(location.search).get('dati') || '';
  const adrese = /^\/(?!\/)/.test(tests) ? tests : '/api/statuss';
  const PERIODS = 60000;

  const VARDI = { darbojas: 'Darbojas', traucejumi: 'Traucējumi', nedarbojas: 'Nedarbojas', nav_datu: 'Nav datu' };
  const IKONAS = { darbojas: '✓', traucejumi: '!', nedarbojas: '✕', nav_datu: '–' };

  const el = id => document.getElementById(id);
  const stunda = iso => iso ? new Date(iso).toLocaleTimeString('lv-LV', { hour: '2-digit', minute: '2-digit' }) : '';
  const dec = (x, d) => x.toLocaleString('lv-LV', { minimumFractionDigits: d, maximumFractionDigits: d });
  const proc = x => x == null ? '—' : dec(x, 1) + ' %';

  function joslasTeksts(j, min) {
    const sak = new Date(j.sakums);
    const beigas = new Date(sak.getTime() + min * 60000);
    return `${stunda(j.sakums)}–${stunda(beigas.toISOString())} · ${VARDI[j.stavoklis] || 'Nav datu'}`;
  }

  function komponents(k, min) {
    const st = VARDI[k.stavoklis] ? k.stavoklis : 'nav_datu';
    const joslas = k.joslas || [];
    const ok = joslas.filter(j => j.stavoklis === 'darbojas').length;
    const av = k.avots;
    const avotaRinda = av ? `<p class="avots">Avots: ${saite(av.url, av.nosaukums)}${av.licence ? ` · ${saite(av.licences_url, av.licence)}` : ''}</p>` : '';
    const laiks = k.parbaudits
      ? `<p class="laiks">Pārbaudīts ${stunda(k.parbaudits)}${k.ilgums_ms != null ? ` (${dec(k.ilgums_ms / 1000, 1)} s)` : ''}</p>` : '';
    const segm = joslas.map((j, i) =>
      `<i class="${esc(j.stavoklis || 'nav')}" data-i="${i}" title="${esc(joslasTeksts(j, min))}"></i>`).join('');
    return `<article class="komp" data-kods="${esc(k.kods)}">
      <div class="komp-augsa">
        <div><h2>${esc(k.nosaukums)}</h2>${k.apraksts ? `<p class="apraksts">${esc(k.apraksts)}</p>` : ''}</div>
        <span class="pill ${st}"><span aria-hidden="true">${IKONAS[st]}</span> ${VARDI[st]}</span>
      </div>
      ${k.zinojums ? `<p class="zinojums">${esc(k.zinojums)}</p>` : ''}
      ${avotaRinda}${k.rezerves ? `<p class="avots">Rezerves avots: ${saite(k.rezerves.url, 'Meteoalarm')} (EUMETNET) — brīdinājumu joslā tagad rāda LVĢMC brīdinājumus caur Meteoalarm</p>` : ''}${laiks}
      <div class="josla" role="img" aria-label="Pēdējās 24 stundas: ${ok} no ${joslas.length} intervāliem darbojās">${segm}</div>
      <div class="josla-uzraksti"><span>pirms 24 h</span><b>7 dienās: ${proc(k.pieejamiba_7d)}</b><span>tagad</span></div>
      <p class="detala" aria-live="polite"></p>
    </article>`;
  }

  function baneris(komp) {
    const b = el('baneris');
    const nos = st => komp.filter(k => k.stavoklis === st).map(k => k.nosaukums).join(', ');
    let kl = 'ok', t = 'Visas sistēmas darbojas';
    if (komp.some(k => k.stavoklis === 'nedarbojas')) { kl = 'kluda'; t = 'Nedarbojas: ' + nos('nedarbojas'); }
    else if (komp.some(k => k.stavoklis === 'traucejumi')) { kl = 'dalejs'; t = 'Daļējie traucējumi: ' + nos('traucejumi'); }
    else if (!komp.length || komp.every(k => k.stavoklis === 'nav_datu' || !VARDI[k.stavoklis])) { kl = 'nav'; t = 'Nav datu'; }
    b.className = 'baneris ' + kl;
    b.textContent = t;
  }

  function zimet(d, noKesas) {
    const komp = d.komponenti || [];
    const min = d.intervals_min || 15;
    baneris(komp);
    const p = el('pedeja');
    const pedeja = komp.map(k => k.parbaudits).filter(Boolean).sort().pop() || d.laiks;
    p.hidden = false;
    if (noKesas) {
      // Bez tīkla service worker (sw.js) atdod pēdējo saglabāto atbildi: rādām to ar laiku un "bezsaistē", nevis kļūdu
      const kad = noKesas.getTime() ? `${stunda(noKesas.toISOString())}${noKesas.toDateString() === new Date().toDateString() ? '' : ' ' + noKesas.toLocaleDateString('lv-LV', { day: 'numeric', month: 'numeric' })}` : '';
      el('baneris').textContent += kad ? ` (saglabāts ${kad})` : ' (saglabāts)';
      p.innerHTML = `<span class="bezsaiste">bezsaistē</span> Rāda pēdējo saglabāto statusu${kad ? `, ${kad}` : ''}.${pedeja ? ` Pēdējā pārbaude: ${stunda(pedeja)}.` : ''}<small>Kad būs internets, lapa atjaunosies pati.</small>`;
    } else {
      p.innerHTML = `${pedeja ? `Pēdējā pārbaude: ${stunda(pedeja)}` : ''}<small>Pārbaudes ik ${min} minūtes; lapa atjaunojas ik minūti.</small>`;
    }
    el('komponenti').innerHTML = komp.map(k => komponents(k, min)).join('');
    el('komponenti')._dati = Object.fromEntries(komp.map(k => [k.kods, k]));
    el('komponenti')._min = min;
    try { el('papildu').innerHTML = papildu(d); } catch (e) { el('papildu').innerHTML = ''; }
  }

  // ---- Papildu sadaļas (/api/statuss: arejie_avoti, flizes, zinojumi, slani); vecs API bez tām — nerāda ----
  const sk = n => n == null ? '—' : Number(n).toLocaleString('lv-LV');
  const ilgums = s => s == null ? '—' : s < 90 ? `${Math.round(s)} s` : s < 5400 ? `${Math.round(s / 60)} min`
    : s < 172800 ? `${dec(s / 3600, s < 36000 ? 1 : 0)} h` : `${Math.round(s / 86400)} d.`;
  const datums = iso => new Date(iso).toLocaleDateString('lv-LV', { day: 'numeric', month: 'numeric' });
  function kad(iso, tagad) {
    if (!iso) return '—';
    const s = (tagad - new Date(iso)) / 1000;
    const diena = new Date(iso).toDateString() === new Date(tagad).toDateString();
    return `pirms ${ilgums(Math.max(s, 0))} <small>(${stunda(iso)}${diena ? '' : ' ' + datums(iso)})</small>`;
  }
  const pill = st => {
    const s = VARDI[st] ? st : 'nav_datu';
    return `<span class="pill ${s}"><span aria-hidden="true">${IKONAS[s]}</span> ${VARDI[s]}</span>`;
  };
  const sadala = (id, virsraksts, apraksts, saturs) => `<section class="sadala" id="${id}" aria-labelledby="${id}-v">
      <h2 id="${id}-v">${virsraksts}</h2>${apraksts ? `<p class="apraksts">${apraksts}</p>` : ''}${saturs}</section>`;
  const nav = d => !d || typeof d !== 'object' || d.kluda;
  const kludaSadala = (id, v) => sadala(id, v, '', '<p class="zinojums">Šie dati pašlaik nav pieejami.</p>');
  const flize = (v, n, sik) => `<div class="flize"><span>${v}</span><b>${n}</b>${sik ? `<small>${sik}</small>` : ''}</div>`;

  const tk = tukss => tukss ? ' class="tukss"' : ''; // šaurā ekrānā tukšas šūnas nerāda
  function arejie(rindas, tagad) {
    const r = rindas.map(a => `<tr>
        <td data-l="Avots"><b>${esc(a.nosaukums)}</b>${a.zinojums ? `<small>${esc(a.zinojums)}</small>` : ''}</td>
        <td data-l="Stāvoklis">${pill(a.stavoklis)}</td>
        <td data-l="Pēdējā veiksmīgā"${tk(!a.pedejais_ok)}>${kad(a.pedejais_ok, tagad)}</td>
        <td data-l="Pēdējā kļūda"${tk(!a.pedeja_kluda)}>${a.pedeja_kluda ? `${kad(a.pedeja_kluda, tagad)}<small>${esc(a.kluda || '')}</small>` : '—'}</td>
        <td data-l="Keša vecums"${tk(a.kesa_vecums_s == null)}>${ilgums(a.kesa_vecums_s)}${a.derigs_s ? `<small>derīgs ${ilgums(a.derigs_s)}</small>` : ''}</td>
        <td data-l="Rezerve"${tk(!a.rezerve && !a.piezime)}>${a.rezerve ? `<span class="birka dzeltena">${esc(a.rezerve)}</span>` : 'nav vajadzīga'}${a.piezime ? `<small>${esc(a.piezime)}</small>` : ''}</td>
      </tr>`).join('');
    return `<table class="tabula"><thead><tr><th>Avots</th><th>Stāvoklis</th><th>Pēdējā veiksmīgā</th><th>Pēdējā kļūda</th>
      <th>Keša vecums</th><th>Rezerve</th></tr></thead><tbody>${r}</tbody></table>`;
  }

  function flizes(f, tagad) {
    const p = f.procesa_skaititaji || {};
    const vardi = { kesa: 'no keša', jauna: 'jaunas', veca: 'vecas no diska', kluda: 'kļūdas', aiznemts: 'aizņemts', tukss: 'ārpus kartes' };
    const sis = Object.keys(vardi).filter(k => p[k]).map(k => `${vardi[k]} ${sk(p[k])}`).join(', ');
    return `<div class="flizes">
        ${flize('Flīzes diskā', f.diska_kess === false ? 'nav diska keša' : sk(f.flizes), f.skenets ? `skaitīts ${kad(f.skenets, tagad)}` : 'vēl nav skaitīts')}
        ${flize('Aizņemts', f.baiti == null ? '—' : `${dec(f.baiti / 1048576, 1)} MB`, f.max_baiti ? `no ${sk(Math.round(f.max_baiti / 1048576))} MB` : '')}
        ${flize('Vecākā flīze', f.vecaka ? datums(f.vecaka) : '—', f.vecaka ? kad(f.vecaka, tagad) : '')}
        ${flize('Trāpījumi kešā', f.trapijumi_proc == null ? '—' : `${dec(f.trapijumi_proc, 1)} %`, f.skaititaji_kops ? `kopš ${datums(f.skaititaji_kops)}` : '')}
      </div>
      <p class="zinojums">Šajā API startā: ${sis || 'flīzes vēl nav prasītas'}${f.procesa_trapijumi_proc != null ? ` (trāpījumi ${dec(f.procesa_trapijumi_proc, 1)} %)` : ''}.</p>`;
  }

  function zinojumi(z, tagad) {
    const l = z.limiti || {}, rob = z.limiti_robezas || {};
    const kopa = Object.values(l).reduce((a, b) => a + (b || 0), 0);
    const vardi = { jauni_minute: 'jauni ziņojumi minūtē', balsis_minute: 'balsis minūtē', zinojums_stunda: 'balsis vienam ziņojumam stundā', ip_stunda: 'balsis no viena tīkla stundā' };
    const sad = Object.keys(vardi).map(k => `${vardi[k]}${rob[k] ? ` (≤ ${rob[k]})` : ''}: ${sk(l[k] || 0)}`).join('; ');
    return `<div class="flizes">
        ${flize('Ziņojumi', z.pieejams === false ? 'nav pieejami' : sk(z.kopa), z.redzami_7d != null ? `${sk(z.redzami_7d)} redzami 7 dienās` : '')}
        ${flize('Balsis pēdējā stundā', sk(z.balsis_1h), z.balsis_avots ? 'no API atmiņas' : '')}
        ${flize('Limits sasniegts', sk(kopa), z.limiti_kops ? `kopš API starta ${kad(z.limiti_kops, tagad)}` : '')}
        ${flize('Pēdējais ziņojums', z.pedejais ? kad(z.pedejais, tagad) : '—', '')}
      </div><p class="zinojums">Limiti: ${esc(sad)}.</p>`;
  }

  function slani(rindas) {
    const r = rindas.map(s => {
      const b = s.ieladejams ? '<span class="birka dzeltena">ielādējams</span>'
        : s.karte === s.repo ? '<span class="birka zala">sakrīt</span>'
        : s.apvienoti_dublikati ? '<span class="birka peleka">dublikāti apvienoti</span>' : '';
      return `<tr><td data-l="Slānis"><b>${esc(s.nosaukums)}</b><small>${esc(s.fails)}</small></td>
        <td data-l="Kartē" class="sk">${sk(s.karte)}</td><td data-l="Repozitorijā" class="sk">${sk(s.repo)}</td><td data-l="">${b}</td></tr>`;
    }).join('');
    return `<table class="tabula slani"><thead><tr><th>Slānis</th><th class="sk">Kartē</th><th class="sk">Repozitorijā</th><th></th></tr></thead>
      <tbody>${r}</tbody></table>`;
  }

  function papildu(d) {
    const tagad = d.laiks ? new Date(d.laiks).getTime() : Date.now();
    let h = '';
    if ('arejie_avoti' in d) h += Array.isArray(d.arejie_avoti)
      ? sadala('arejie', 'Ārējie avoti', `Katrs ārējais datu avots: kad pēdējo reizi izdevās ielāde, pēdējā kļūda, cik veci ir kešotie dati un vai šobrīd darbojas rezerve. Uzskaite kopš API starta${d.api_starts ? ` (${stunda(d.api_starts)}${new Date(d.api_starts).toDateString() === new Date(tagad).toDateString() ? '' : ' ' + datums(d.api_starts)})` : ''}; lapas atvēršana avotus nesauc.`, arejie(d.arejie_avoti, tagad))
      : kludaSadala('arejie', 'Ārējie avoti');
    if ('flizes' in d) h += nav(d.flizes) ? kludaSadala('flizes', 'Plūdu karšu flīžu kešs')
      : sadala('flizes', 'Plūdu karšu flīžu kešs', 'LVĢMC plūdu zonu flīzes glabājas servera diskā 30 dienas; ja LVĢMC neatbild, rāda vecās.', flizes(d.flizes, tagad));
    if ('zinojumi' in d) h += nav(d.zinojumi) ? kludaSadala('zinojumi', 'Iedzīvotāju ziņojumi')
      : sadala('zinojumi', 'Iedzīvotāju ziņojumi', 'Ziņojumu skaits, balsojumi un cik reižu pieprasījumi atteikti limita dēļ (aizsardzība pret ļaunprātīgu lietošanu).', zinojumi(d.zinojumi, tagad));
    if ('slani' in d) h += Array.isArray(d.slani)
      ? sadala('slani', 'Slāņu dati: kartē un repozitorijā', 'Objektu skaits kartes datubāzē pret failu repozitorijā. „Ielādējams” nozīmē, ka repozitorijā ir jaunāki dati un serverī jāpalaiž ielāde.', slani(d.slani))
      : kludaSadala('slani', 'Slāņu dati: kartē un repozitorijā');
    return h;
  }

  function kluda() {
    const b = el('baneris');
    b.className = 'baneris kluda';
    const bezTikla = navigator.onLine === false;
    b.textContent = bezTikla ? 'Nav interneta — nav arī saglabāta statusa.' : 'Statusa API nav pieejams — karte, iespējams, darbojas daļēji.';
    const p = el('pedeja');
    p.hidden = false;
    p.innerHTML = bezTikla ? '<small>Statuss parādīsies, kad būs savienojums.</small>' : '<small>Mēģināsim vēlreiz pēc minūtes.</small>';
  }

  async function ieladet() {
    try {
      const r = await fetch(adrese, { cache: 'no-store' });
      if (!r.ok) throw new Error(r.status);
      // sw.js bez tīkla atbild ar saglabāto kopiju un galvenēm x-sw-no-kesas / x-sw-saglabats
      const noKesas = r.headers.get('x-sw-no-kesas') ? new Date(r.headers.get('x-sw-saglabats') || NaN) : null;
      zimet(await r.json(), noKesas);
    } catch (e) {
      // veco datu vietā neko nerādām: kļūda ir svarīgāka par novecojušu statusu
      el('komponenti').innerHTML = '';
      el('papildu').innerHTML = '';
      kluda();
    }
  }

  // Pieskāriens joslas intervālam parāda tā aprakstu zem joslas (uz skārienekrāna nav hover).
  el('komponenti').addEventListener('click', e => {
    const s = e.target.closest('.josla i');
    if (!s) return;
    const art = s.closest('.komp');
    const k = el('komponenti')._dati?.[art.dataset.kods];
    if (!k) return;
    art.querySelectorAll('.izv').forEach(x => x.classList.remove('izv'));
    s.classList.add('izv');
    art.querySelector('.detala').textContent = joslasTeksts(k.joslas[+s.dataset.i], el('komponenti')._min);
  });

  ieladet();
  setInterval(() => { if (!document.hidden) ieladet(); }, PERIODS);
  document.addEventListener('visibilitychange', () => { if (!document.hidden) ieladet(); });
})();
