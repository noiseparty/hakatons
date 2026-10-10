// Sākumlapa: dzīvie skaitļi (/api/kategorijas), plūsmu stāvoklis (/api/veseliba), avoti (/api/avoti + tiešsaistes avoti).
(() => {
  // Vecās saites (/?q=…, /#…, ?lat=…) ved uz karti, kas tagad ir /map.
  if (location.search || location.hash) { location.replace('/map' + location.search + location.hash); return; }
  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const $ = id => document.getElementById(id);
  const json = u => fetch(u).then(r => { if (!r.ok) throw new Error(u + ' ' + r.status); return r.json(); });
  const nf = n => Number(n).toLocaleString('lv-LV');
  const saite = (u, t) => /^https?:\/\//.test(u || '') ? `<a href="${esc(u)}" target="_blank" rel="noopener">${esc(t)}</a>` : esc(t);
  const kluda = (id, t) => { $(id).innerHTML = `<p class="apak">${t} Mēģiniet vēlreiz vēlāk.</p>`; };

  const GRUPAS = { patvertnes: 'Patvertnes un drošās vietas', veseliba: 'Veselība', infrastruktura: 'Infrastruktūra', vide: 'Ūdens un vide', transports: 'Transports' };

  async function skaiti() {
    try {
      const k = await json('/api/kategorijas');
      let html = '', kops = 0;
      const grupas = [];
      for (const c of k) { let x = grupas.find(y => y.g === c.grupa); if (!x) grupas.push(x = { g: c.grupa, k: [] }); x.k.push(c); }
      const saite_karte = ids => '/map?slanis=' + ids.map(encodeURIComponent).join(',');
      for (const x of grupas) {
        const nos = GRUPAS[x.g] || x.g;
        html += `<h3 class="grupa"><a href="${esc(saite_karte(x.k.map(c => c.kods)))}" aria-label="Atvērt kartē grupu: ${esc(nos)}">${esc(nos)} <i aria-hidden="true">›</i></a></h3>`;
        for (const c of x.k) {
          kops += c.skaits || 0;
          html += `<a class="skaitlis" href="${esc(saite_karte([c.kods]))}" style="--krasa:${/^#[0-9a-f]{3,8}$/i.test(c.krasa) ? c.krasa : '#0077c8'}"><b>${nf(c.skaits)}</b><span>${esc(c.nosaukums)}</span><i class="bulta" aria-hidden="true">›</i></a>`;
        }
      }
      $('kartes').innerHTML = html; $('kartes').removeAttribute('aria-busy');
      $('kops').textContent = `${nf(kops)} objekti ${k.length} kategorijās`;
      const ca = k.filter(c => c.kods === 'evakuacijas_punkts' || c.kods === 'izmitinasana').reduce((s, c) => s + c.skaits, 0);
      $('ca-vietas').textContent = nf(ca);
    } catch (e) { kluda('kartes', 'Skaitļus neizdevās ielādēt.'); $('kops').textContent = 'nav pieejami'; $('ca-vietas').textContent = '1300+'; }
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
      $('statusi').removeAttribute('aria-busy'); $('statusi').innerHTML = PLUSMAS.map(([nos, kodi, ipasa]) => {
        const kn = kodi.filter(k => k in a);
        const slikti = kn.filter(k => a[k] === 'traucejumi' || a[k] === 'nedarbojas');
        const ok = kn.length > 0 && slikti.length === 0;
        let piez = ok ? `${kn.filter(k => a[k] === 'darbojas').length} no ${kn.length} avotiem darbojas` :
          kn.length ? `Traucējumi: ${slikti.length} no ${kn.length} avotiem` : 'Nav informācijas';
        if (ipasa === 'bridinajumi' && v.bridinajumi?.rezerves_aktivs) piez += '. LVĢMC datne nav pieejama, brīdinājumi nāk no Meteoalarm rezerves avota';
        return `<div class="statuss"><span class="zime ${ok ? 'ok' : 'deg'}">${ok ? 'Darbojas' : 'Traucēts'}</span><div><b>${esc(nos)}</b><small>${esc(piez)}</small></div></div>`;
      }).join('');
      if (v.bridinajumi?.lvgmc_atbildeja) $('statuss-apak').textContent = 'Pārbaude no /api/veseliba; LVĢMC pēdējā atbilde ' +
        new Date(v.bridinajumi.lvgmc_atbildeja).toLocaleString('lv-LV', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' }) + '.';
    } catch (e) { kluda('statusi', 'Statusu neizdevās ielādēt.'); }
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

  const dat = iso => iso ? new Date(iso).toLocaleDateString('lv-LV') : '';
  async function avoti() {
    let db = [];
    try { db = await json('/api/avoti'); } catch (e) { $('avoti-apak').textContent = 'Avotu saraksts no datubāzes īslaicīgi nav pieejams; zemāk tiešsaistes avoti.'; }
    const isti = db.filter(a => !/^sim-/.test(a.kods)), sim = db.filter(a => /^sim-/.test(a.kods));
    const visi = [...isti, ...TIESI.filter(t => !isti.some(a => a.nosaukums === t.nosaukums))];
    const atverti = visi.filter(a => a.atverts).length;
    $('avoti-apak').textContent = `${atverti} atvērto datu avoti ar licenci` + (visi.length > atverti ? `, ${visi.length - atverti} bez skaidri norādītas atvērtas licences` : '') +
      (sim.length ? `; ${sim.length} simulēti prototipa dati nav iekļauti.` : '.');
    $('avoti').removeAttribute('aria-busy');
    $('avoti').innerHTML = visi.map(a => {
      const sk = a.skaits ? `<span class="zime skaits">${nf(a.skaits)} objekti</span>` : '';
      const lic = a.atverts ? `<span class="zime ok">${saite(a.licences_url, a.licence)}</span>` : `<span class="zime deg">&#9888; ${esc(a.licence || 'Licence nav norādīta')}</span>`;
      const kad = a.atjaunots ? dat(a.atjaunots) : a.ieladets ? dat(a.ieladets) + ' (ielāde)' : a.biezums || 'nav norādīts';
      return `<li class="${a.atverts ? '' : 'bez'}"><b>${saite(a.datu_kopa_url, a.nosaukums)}</b>
      <small>Izdevējs: ${esc(a.izdevejs)}</small>
      <span class="zimes">${lic}${sk}</span>
      ${a.lietojums ? `<small>Kartē: ${esc(a.lietojums)}</small>` : ''}
      <small>Atjaunots: ${esc(kad)}</small>
      ${a.piezime ? `<details><summary>Piezīme par avotu</summary><small>${esc(a.piezime)}</small></details>` : ''}</li>`;
    }).join('');
  }

  const forma = $('meklet');
  if (forma) forma.addEventListener('submit', e => {
    e.preventDefault();
    const q = $('vaicajums').value.trim();
    if (!q) { $('vaicajums').focus(); return; }
    location.href = '/map?q=' + encodeURIComponent(q);
  });

  skaiti(); statuss(); avoti();
})();
