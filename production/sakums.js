// Sākumlapa: dzīvie skaitļi (/api/kategorijas), plūsmu stāvoklis (/api/veseliba), avoti (/api/avoti + tiešsaistes avoti).
// Teksti iet caur Valoda.t (LV/RU/EN); pēc slēdža maiņas ('valoda-maina') viss tiek pārzīmēts no jau ielādētajiem datiem.
(() => {
  // Vecās saites (/?q=…, /#…, ?lat=…) ved uz karti, kas tagad ir /map.
  if (location.search || location.hash) { location.replace('/map' + location.search + location.hash); return; }
  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const $ = id => document.getElementById(id);
  const t = (k, m) => typeof Valoda !== 'undefined' ? Valoda.t(k, m) : k;
  const LOKALE = { lv: 'lv-LV', ru: 'ru-RU', en: 'en-GB' };
  const loc = () => LOKALE[typeof Valoda !== 'undefined' ? Valoda.aktiva() : 'lv'] || 'lv-LV';
  // Tīkla atbildes saglabā, lai valodas maiņa nepieprasa tās no jauna
  const atbildes = new Map();
  const json = u => {
    if (!atbildes.has(u)) atbildes.set(u, fetch(u).then(r => { if (!r.ok) throw new Error(u + ' ' + r.status); return r.json(); }));
    return atbildes.get(u);
  };
  const nf = n => Number(n).toLocaleString(loc());
  const saite = (u, tekst) => /^https?:\/\//.test(u || '') ? `<a href="${esc(u)}" target="_blank" rel="noopener">${esc(tekst)}</a>` : esc(tekst);
  const kluda = (id, tekst) => { $(id).innerHTML = `<p class="apak">${esc(tekst)}</p>`; };

  const GRUPAS = { patvertnes: 'Patvertnes un drošās vietas', veseliba: 'Veselība', infrastruktura: 'Infrastruktūra', vide: 'Ūdens un vide', transports: 'Transports' };

  async function skaiti() {
    try {
      const k = await json('/api/kategorijas');
      let html = '', kops = 0;
      const grupas = [];
      for (const c of k) { let x = grupas.find(y => y.g === c.grupa); if (!x) grupas.push(x = { g: c.grupa, k: [] }); x.k.push(c); }
      const saite_karte = ids => '/map?slanis=' + ids.map(encodeURIComponent).join(',');
      for (const x of grupas) {
        const nos = GRUPAS[x.g] ? t(GRUPAS[x.g]) : x.g;
        html += `<h3 class="grupa"><a href="${esc(saite_karte(x.k.map(c => c.kods)))}" aria-label="${esc(t('Atvērt kartē grupu: {x}', { x: nos }))}">${esc(nos)} <i aria-hidden="true">›</i></a></h3>`;
        for (const c of x.k) {
          kops += c.skaits || 0;
          html += `<a class="skaitlis" href="${esc(saite_karte([c.kods]))}" style="--krasa:${/^#[0-9a-f]{3,8}$/i.test(c.krasa) ? c.krasa : '#0077c8'}"><b>${nf(c.skaits)}</b><span>${esc(t(c.nosaukums))}</span><i class="bulta" aria-hidden="true">›</i></a>`;
        }
      }
      $('kartes').innerHTML = html; $('kartes').removeAttribute('aria-busy');
      $('kops').textContent = t('{n} objekti {k} kategorijās', { n: nf(kops), k: k.length });
      const ca = k.filter(c => c.kods === 'evakuacijas_punkts' || c.kods === 'izmitinasana').reduce((s, c) => s + c.skaits, 0);
      $('ca-vietas').textContent = nf(ca);
    } catch (e) { kluda('kartes', t('Skaitļus neizdevās ielādēt. Mēģiniet vēlreiz vēlāk.')); $('kops').textContent = t('nav pieejami'); $('ca-vietas').textContent = '1300+'; }
  }

  // /api/veseliba arejie_avoti vērtības: darbojas | traucejumi | nedarbojas | nav_datu
  const PLUSMAS = [
    ['Brīdinājumi (LVĢMC)', ['lvgmc_bridinajumi', 'meteoalarm'], 'bridinajumi'],
    ['Upju līmeņi un plūdi', ['lvgmc_hidro', 'lvgmc_pludi', 'lvgmc_pludu_flizes'], null],
    ['Ceļi un satiksme (LVC)', ['nap_slegumi', 'nap_negadijumi', 'nap_remonti', 'nap_satiksme_slidens'], null],
    ['Laikapstākļi un zibens', ['lvgmc_prognozes', 'lvgmc_noverojumi', 'lvgmc_zibens', 'fmi_zibens', 'open_meteo'], null],
  ];
  async function statuss() {
    try {
      const v = await json('/api/veseliba');
      const a = v.arejie_avoti || {};
      $('statusi').removeAttribute('aria-busy');
      $('statusi').innerHTML = PLUSMAS.map(([nos, kodi, ipasa]) => {
        const kn = kodi.filter(k => k in a);
        const slikti = kn.filter(k => a[k] === 'traucejumi' || a[k] === 'nedarbojas');
        const ok = kn.length > 0 && slikti.length === 0;
        let piez = ok ? t('{n} no {m} avotiem darbojas', { n: kn.filter(k => a[k] === 'darbojas').length, m: kn.length }) :
          kn.length ? t('Traucējumi: {n} no {m} avotiem', { n: slikti.length, m: kn.length }) : t('Nav informācijas');
        if (ipasa === 'bridinajumi' && v.bridinajumi?.rezerves_aktivs) piez += t('. LVĢMC datne nav pieejama, brīdinājumi nāk no Meteoalarm rezerves avota');
        return `<div class="statuss"><span class="zime ${ok ? 'ok' : 'deg'}">${esc(t(ok ? 'Darbojas' : 'Traucēts'))}</span><div><b>${esc(t(nos))}</b><small>${esc(piez)}</small></div></div>`;
      }).join('');
      if (v.bridinajumi?.lvgmc_atbildeja) $('statuss-apak').textContent = t('Pārbaude no /api/veseliba; LVĢMC pēdējā atbilde {x}.', {
        x: new Date(v.bridinajumi.lvgmc_atbildeja).toLocaleString(loc(), { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' }) });
    } catch (e) { kluda('statusi', t('Statusu neizdevās ielādēt. Mēģiniet vēlreiz vēlāk.')); }
  }

  // Avoti, ko API ņem tieši no izdevēja (tie paši, kas avoti.js sarakstā TIESSAISTE)
  const CC0 = ['CC0 1.0', 'https://creativecommons.org/publicdomain/zero/1.0/'], CCBY = ['CC BY 4.0', 'https://creativecommons.org/licenses/by/4.0/'];
  const LV = 'Latvijas Vides, ģeoloģijas un meteoroloģijas centrs';
  const TIESI = [
    ['Hidrometeoroloģiskie brīdinājumi', LV, CC0, 'https://data.gov.lv/dati/lv/dataset/hidrometeorologiskie-bridinajumi', 'tiešsaistē, kešs 10 min'],
    ['Meteoalarm: brīdinājumu rezerves avots', 'LVĢMC, caur Meteoalarm (EUMETNET)', CCBY, 'https://www.meteoalarm.org', 'tiešsaistē, kavējums līdz 10 min'],
    ['3. cikla plūdu riska kartes (2026–2031)', LV + ' / ĢeoLatvija.lv', CC0, 'https://data.gov.lv/dati/lv/dataset/3-cikla-latvijas-pldu-postjumu-vietu-un-pldu-riska-kartes1', 'kartes 2026–2031 ciklam'],
    ['Ceļu slēgumi, negadījumi, remontdarbi (DATEX II)', 'VSIA „Latvijas Valsts ceļi”', CC0, 'https://transportdata.gov.lv/card/75611a36-e66b-40cf-af2c-69db48c278cf', 'tiešsaistē, kešs 5 min'],
    ['Meteoroloģiskās prognozes apdzīvotām vietām', LV, CC0, 'https://data.gov.lv/dati/lv/dataset/meteorologiskas-prognozes-apdzivotam-vietam-jaunaka-datu-kopa', 'vairākas reizes dienā'],
    ['Hidrometeoroloģiskie novērojumi', LV, CC0, 'https://data.gov.lv/dati/lv/dataset/hidrometeorologiskie-noverojumi', 'katru stundu'],
    ['Telpiskie novērojumi (zibens režģis)', LV, CC0, 'https://data.gov.lv/dati/lv/dataset/telpiskie-hidrometeorologiskie-noverojumi', 'katru stundu'],
    ['Hidroloģiskās prognozes (14 dienas)', LV, CC0, 'https://data.gov.lv/dati/dataset/5d9b0379-c0b8-4ce9-9094-7c30b5502433', 'reizi dienā'],
    ['Zibens izlādes', 'Ilmatieteen laitos (Somijas Meteoroloģijas institūts)', CCBY, 'https://en.ilmatieteenlaitos.fi/open-data', 'tiešsaistē, ik minūti'],
    ['Nokrišņi un augsnes mitrums', 'Open-Meteo', CCBY, 'https://open-meteo.com/', 'tiešsaistē'],
    ['Publisko personu un iestāžu saraksts', 'Uzņēmumu reģistrs', CC0, 'https://data.gov.lv/dati/dataset/public-persons-institutions', 'pēc ielādes'],
    ['VPVKAC kontaktpunkti', 'VPVKAC tīkls (data.gov.lv)', CC0, 'https://data.gov.lv/dati/lv/dataset/vpvkac-kontakti', '2022. gada dati'],
  ].map(([nosaukums, izdevejs, [licence, licences_url], datu_kopa_url, biezums]) => ({ nosaukums, izdevejs, licence, licences_url, datu_kopa_url, biezums, atverts: true }));

  const dat = iso => iso ? new Date(iso).toLocaleDateString(loc()) : '';
  async function avoti() {
    let db = [];
    try { db = await json('/api/avoti'); } catch (e) { $('avoti-apak').textContent = t('Avotu saraksts no datubāzes īslaicīgi nav pieejams; zemāk tiešsaistes avoti.'); }
    const isti = db.filter(a => !/^sim-/.test(a.kods)), sim = db.filter(a => /^sim-/.test(a.kods));
    const visi = [...isti, ...TIESI.filter(x => !isti.some(a => a.nosaukums === x.nosaukums))];
    const atverti = visi.filter(a => a.atverts).length;
    $('avoti-apak').textContent = t('{n} atvērto datu avoti ar licenci', { n: atverti }) +
      (visi.length > atverti ? t(', {m} bez skaidri norādītas atvērtas licences', { m: visi.length - atverti }) : '') +
      (sim.length ? t('; {n} simulēti prototipa dati nav iekļauti.', { n: sim.length }) : '.');
    $('avoti').removeAttribute('aria-busy');
    $('avoti').innerHTML = visi.map(a => {
      const sk = a.skaits ? `<span class="zime skaits">${t('{n} objekti', { n: nf(a.skaits) })}</span>` : '';
      const lic = a.atverts ? `<span class="zime ok">${saite(a.licences_url, a.licence)}</span>` : `<span class="zime deg">&#9888; ${esc(t(a.licence || 'licence nav norādīta'))}</span>`;
      const kad = a.atjaunots ? dat(a.atjaunots) : a.ieladets ? dat(a.ieladets) + t(' (ielāde)') : t(a.biezums || 'nav norādīts');
      return `<li class="${a.atverts ? '' : 'bez'}"><b>${saite(a.datu_kopa_url, a.nosaukums)}</b>
      <small>${esc(t('Izdevējs'))}: ${esc(a.izdevejs)}</small>
      <span class="zimes">${lic}${sk}</span>
      ${a.lietojums ? `<small>${esc(t('Kartē:'))} ${esc(a.lietojums)}</small>` : ''}
      <small>${esc(t('Atjaunots'))}: ${esc(kad)}</small>
      ${a.piezime ? `<details><summary>${esc(t('Piezīme par avotu'))}</summary><small>${esc(a.piezime)}</small></details>` : ''}</li>`;
    }).join('');
  }

  const forma = $('meklet');
  if (forma) forma.addEventListener('submit', e => {
    e.preventDefault();
    const q = $('vaicajums').value.trim();
    if (!q) { $('vaicajums').focus(); return; }
    location.href = '/map?q=' + encodeURIComponent(q);
  });

  // Dzīvie slāņi: katra plūsma ielādējas atsevišķi, kļūda vienā neaptur pārējos.
  // Atslēgas (?slanis=): udens_limenis = kategorijas kods; celu / zibens / zinojumu / bridinajumi = pārklājumu slāņi (app.js ids "<atslēga>-slanis").
  const T = (k, m) => (typeof Valoda !== 'undefined' ? Valoda.t(k, m) : k);
  const SLANI = [
    { nos: 'Aktīvie brīdinājumi', vien: 'LVĢMC / Meteoalarm', saite: '/map?slanis=bridinajumi',
      get: async () => { const d = await json('/api/bridinajumi'); return { n: (d.bridinajumi || []).length, rezerve: !!d.rezerves }; } },
    { nos: 'Ceļu notikumi', vien: 'LVC', saite: '/map?slanis=celu',
      get: async () => { const d = await json('/api/celi'); if (d.konfigurets === false) throw new Error('nekonfigurets'); return { n: (d.notikumi || []).length, daleji: d.nepieejami > 0 }; } },
    { nos: 'Zibens pēdējās 30 min', vien: 'FMI', saite: '/map?slanis=zibens',
      get: async () => { const d = await json('/api/zibens'); return { n: d.skaits ?? (d.zibeni || []).length }; } },
    { nos: 'Upju līmeņa mērītāji', vien: 'LVĢMC', saite: '/map?slanis=udens_limenis',
      get: async () => { const k = await json('/api/kategorijas'); const c = k.find(x => x.kods === 'udens_limenis'); if (!c) throw new Error('nav'); return { n: c.skaits }; } },
  ];
  async function slani() {
    const el = $('slani');
    const kartes = await Promise.all(SLANI.map(async s => {
      let r = null;
      try { r = await s.get(); } catch (e) { /* kritums zemāk */ }
      const ok = !!r, deg = ok && (r.rezerve || r.daleji);
      const zime = !ok ? ['deg', 'nav pieejams'] : deg ? ['deg', r.rezerve ? 'rezerves avots' : 'daļēji pieejams'] : ['ok', 'tiešraide'];
      return `<a class="slanis" href="${esc(s.saite)}"><b>${ok ? nf(r.n) : '–'}</b><span>${esc(T(s.nos))} <small>${esc(s.vien)}</small></span>` +
        `<em class="zime ${zime[0]}">${esc(T(zime[1]))}</em><i class="bulta" aria-hidden="true">›</i></a>`;
    }));
    el.innerHTML = kartes.join(''); el.removeAttribute('aria-busy');
  }

  // Iedzīvotāju ziņojumi: lietotāju radīts saturs, nav oficiāls avots
  async function zinojumuAvots() {
    const ul = $('zinojumu-avots');
    let d = null;
    try { d = await json('/api/zinojumi'); } catch (e) { /* skaits nav obligāts */ }
    const lic = d?.avots?.licence || 'CC BY 4.0', url = d?.avots?.licences_url || 'https://creativecommons.org/licenses/by/4.0/';
    ul.innerHTML = `<li class="bez"><b>${esc(T('Iedzīvotāju ziņojumi'))}</b>
      <small>${esc(T('Izdevējs'))}: ${esc(T('paši iedzīvotāji caur map.repo.lv; netiek pārbaudīti pirms publicēšanas, moderācija pēc fakta'))}</small>
      <span class="zimes"><span class="zime deg">&#9888; ${esc(T('Nav oficiāls avots'))}</span><span class="zime">${saite(url, lic)}</span>${Array.isArray(d?.zinojumi) ? `<span class="zime skaits">${nf(d.zinojumi.length)} ${esc(T('pēdējās 7 dienās'))}</span>` : ''}</span>
      <small>${esc(T('Kartē: pelēki punkti ar ~1 km precizitāti, pēdējās 7 dienas. Tas nav oficiāls brīdinājums; ja apdraudēta dzīvība, zvaniet 112.'))}</small>
      <small><a href="/map?slanis=zinojumu">${esc(T('Atvērt slāni kartē'))}</a></small></li>`;
  }

  // Pārzīmē visu dinamisko tekstu no jau ielādētajām atbildēm (bez jauniem tīkla izsaukumiem)
  function renderAll() { document.title = t('Krīzes karte · Datu pārskats'); slani(); zinojumuAvots(); skaiti(); statuss(); avoti(); }
  document.addEventListener('valoda-maina', renderAll);
  renderAll();
})();
