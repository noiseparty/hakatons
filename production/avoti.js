// Datu avoti (/api/avoti → tabula avoti, src/karte/db/shema.sql): nolaižamā sadaļa "Datu avoti" panelī zem slāņiem
// un avota rinda katra punkta logā. Avots bez atvērtas licences tiek brīdināts. Kartes stūrī — tikai OSM fona kartes atsauce.
// Avoti, kurus API ņem tieši no izdevēja (bez rindas tabulā avoti), ir sarakstā TIESSAISTE; ja datubāzē ir rinda ar to pašu
// kodu, rāda datubāzes rindu. "ja": rāda tikai tad, ja attiecīgā funkcija lapā ir (elementa id).
const Avoti = (() => {
  const CC0 = ['CC0 1.0', 'https://creativecommons.org/publicdomain/zero/1.0/'];
  const CCBY = ['CC BY 4.0', 'https://creativecommons.org/licenses/by/4.0/'];
  const LVGMC = 'Latvijas Vides, ģeoloģijas un meteoroloģijas centrs';
  const TIESSAISTE = [
    ['lvgmc-bridinajumi', 'Hidrometeoroloģiskie brīdinājumi', LVGMC, CC0, 'https://data.gov.lv/dati/lv/dataset/hidrometeorologiskie-bridinajumi',
      'Brīdinājumu josla lapas augšā; vai brīdinājums attiecas uz izvēlēto vietu', 'tiešsaistē, kešs 10 min', 76, { svaigums: 'bridinajumi' }],
    ['lvgmc-pludi', '3. cikla plūdu postījumu vietu un plūdu riska kartes (2026–2031)', LVGMC + ' / ĢeoLatvija.lv', CC0,
      'https://data.gov.lv/dati/lv/dataset/3-cikla-latvijas-pldu-postjumu-vietu-un-pldu-riska-kartes1',
      'Plūdu riska zonu slānis; vai adrese ir applūstošā teritorijā', 'kartes 2026–2031 ciklam; pārbaude tiešsaistē', 77],
    ['lvc-nap', 'Ceļu slēgumi, negadījumi, remontdarbi un slidens ceļš (DATEX II)', 'VSIA „Latvijas Valsts ceļi” / transportdata.gov.lv', CC0,
      'https://transportdata.gov.lv/card/75611a36-e66b-40cf-af2c-69db48c278cf',
      'Slānis „Ceļu slēgumi un negadījumi”; rinda „Ceļu satiksme” meklēšanas rezultātā', 'tiešsaistē, kešs 5 min', 78, { ja: 'celu-slanis' }],
    ['lvgmc-prognozes', 'Meteoroloģiskās prognozes apdzīvotām vietām', LVGMC, CC0,
      'https://data.gov.lv/dati/lv/dataset/meteorologiskas-prognozes-apdzivotam-vietam-jaunaka-datu-kopa',
      '„Prognoze / ziņas”: laikapstākļi pa novadiem 3 dienām', 'vairākas reizes dienā, kešs 5 min', 79, { svaigums: 'prognozes' }],
    ['fmi-zibens', 'Zibens izlādes (pēdējās 30 min)', 'Ilmatieteen laitos (Somijas Meteoroloģijas institūts)', CCBY,
      'https://en.ilmatieteenlaitos.fi/open-data', 'Zibens slānis', 'tiešsaistē, ik minūti', 81, { ja: 'zibens-slanis' }],
    ['lvgmc-meteo', 'Hidrometeoroloģiskie novērojumi (meteoroloģiskie operatīvie dati)', LVGMC, CC0,
      'https://data.gov.lv/dati/lv/dataset/hidrometeorologiskie-noverojumi',
      'Slānis „Laikapstākļi tagad”; vējš tagad meklēšanā; ziņa un riska karte prognožu lentē', 'katru stundu, kešs 10 min', 80,
      { ja: 'noverojumi-slanis' }],
    ['lvgmc-zibens', 'Telpiskie hidrometeoroloģiskie novērojumi (zibens režģis, 24 h)', LVGMC, CC0,
      'https://data.gov.lv/dati/lv/dataset/telpiskie-hidrometeorologiskie-noverojumi', 'Zibens slānis (pelēkie apļi)',
      'katru stundu, kavējas ~2–3 h', 82, { ja: 'zibens-slanis' }],
    ['open-meteo', 'Nokrišņi un augsnes mitrums', 'Open-Meteo', CCBY, 'https://open-meteo.com/',
      'Meklēšanas rezultātā (plūdi, lietusgāzes, vētra): nokrišņi pēdējās 26 dienās un augsnes mitrums', 'tiešsaistē', 83, { ja: 'zibens-slanis' }],
    ['osm-noturiba', 'OpenStreetMap: bibliotēkas, kultūras nami, pašvaldību ēkas, skolas', 'OpenStreetMap līdzstrādnieki',
      ['ODbL 1.0', 'https://opendatacommons.org/licenses/odbl/1-0/'], 'https://www.openstreetmap.org/copyright',
      'Noturības punktu kandidāti (statuss nav apstiprināts)', 'pēc ielādes', 71],
    ['sim-udens', 'Simulēti prototipa dati (komanda): dzeramā ūdens punkti', 'Hakatona komanda', ['Simulēti dati, CC0 1.0', CC0[1]],
      'https://github.com/noiseparty/hakatons/tree/main/atseviski_dati', 'SIMULĒTI: dzeramā ūdens punkti (prototips, nav reāli)', 'statiski', 95],
    ['sim-energija', 'Simulēti prototipa dati (komanda): ierīču uzlādes punkti', 'Hakatona komanda', ['Simulēti dati, CC0 1.0', CC0[1]],
      'https://github.com/noiseparty/hakatons/tree/main/atseviski_dati', 'SIMULĒTI: ierīču uzlādes punkti (prototips, nav reāli)', 'statiski', 96],
    ['opentopomap', 'OpenTopoMap reljefa karte', 'OpenTopoMap (dati: OpenStreetMap līdzstrādnieki, SRTM)',
      ['CC BY-SA 3.0', 'https://creativecommons.org/licenses/by-sa/3.0/'], 'https://opentopomap.org/about', 'Fona karte „Reljefs”', 'tiešsaistē', 91],
  ].map(([kods, nosaukums, izdevejs, [licence, licences_url], datu_kopa_url, lietojums, biezums, kartiba, x = {}]) =>
    ({ kods, nosaukums, izdevejs, licence, licences_url, datu_kopa_url, lietojums, biezums, kartiba, atverts: true, ...x }));
  // Datubāzes avotiem: cik bieži atjauno (pārējiem rāda ielādes datumu)
  const BIEZUMS = { 'lvgmc-hidro': 'katru stundu', 'osm-karte': 'tiešsaistē', 'lvc-nap': 'tiešsaistē, kešs 5 min' };

  let pecKoda = {};
  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const saite = (url, teksts) => /^https?:\/\//.test(url || '')
    ? `<a href="${esc(url)}" target="_blank" rel="noopener">${esc(teksts)}</a>` : esc(teksts);
  const datums = iso => iso ? new Date(iso).toLocaleDateString('lv-LV') : '';
  // avoti.atjaunots (pēdējā veiksmīgā ielāde, ielade.py): "10.10. 04:31"
  const ielLaiks = iso => new Date(iso).toLocaleString('lv-LV', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' });
  const bridinajums = '⚠ Atvērta licence nav norādīta';

  const avotuVards = n => `${n} atvērto datu ${n % 10 === 1 && n % 100 !== 11 ? 'avots' : 'avoti'}`;

  function zimet(saraksts) {
    const ul = document.getElementById('avoti-saraksts');
    if (!ul) return;
    // Simulētie prototipa dati (avots "sim-…", komandas izdomāti) nav atvērto datu avoti: tos skaita atsevišķi un rāda
    // saraksta beigās ar zīmi "SIMULĒTI" (tie paši skaitļi slaidos un trukstosie.html).
    const simulets = a => /^sim-/.test(a.kods);
    const sim = saraksts.filter(simulets), isti = saraksts.filter(a => !simulets(a));
    const atverti = isti.filter(a => a.atverts).length, citi = isti.length - atverti;
    const sk = document.getElementById('avoti-skaits');
    if (sk) sk.textContent = atverti + (citi ? ' · ⚠' : '');
    let kops = document.getElementById('avoti-kopsavilkums');
    if (!kops) {
      kops = document.createElement('p');
      kops.id = 'avoti-kopsavilkums';
      ul.before(kops);
    }
    kops.innerHTML = `<b>${avotuVards(atverti)}</b>` +
      (sim.length ? ` · ${sim.length} simulēti prototipa dati` : '') +
      (citi ? ` · ${citi} bez atvērtas licences ⚠` : '');
    ul.innerHTML = [...isti, ...sim].map((a, i, visi) => `
      ${simulets(a) && !simulets(visi[i - 1] || { kods: '' }) ? '<li class="avoti-grupa">Simulēti prototipa dati (nav atvērtie dati; kartē zīme „SIMULĒTI DATI — prototips”)</li>' : ''}
      <li class="avots${a.atverts ? '' : ' bez-licences'}${simulets(a) ? ' simulets' : ''}" id="avots-${esc(a.kods)}">
        ${simulets(a) ? '<span class="sim-zime">SIMULĒTI</span>' : ''}
        <b>${saite(a.datu_kopa_url, a.nosaukums)}</b>
        <small>${esc(a.izdevejs)}</small>
        <span class="licence">${a.atverts ? '' : bridinajums + ' · '}${saite(a.licences_url, a.licence)}</span>
        <small>Kartē: ${esc(a.lietojums)}${a.skaits ? ` · ${daudzskaitlis(a.skaits, 'objekts', 'objekti')}${a.atjaunots ? '' : `, ielādēts ${datums(a.ieladets)}`}` : ''}</small>
        ${a.atjaunots ? `<small class="atjaunots">Atjaunots ${ielLaiks(a.atjaunots)}</small>` : ''}
        ${a.biezums || BIEZUMS[a.kods] ? `<small>Atjaunošana: ${esc(a.biezums || BIEZUMS[a.kods])}${a.svaigums ? `<span data-svaigums="${esc(a.svaigums)}"></span>` : ''}</small>` : ''}
        ${a.piezime ? `<small class="avota-piezime">${esc(a.piezime)}</small>` : ''}
        ${a.lejupielade && a.lejupielade !== a.datu_kopa_url ? `<small class="ieguve">Ieguve: ${/^https?:/.test(a.lejupielade) ? saite(a.lejupielade, a.lejupielade) : esc(a.lejupielade)}</small>` : ''}
      </li>`).join('');
  }

  async function ieladet() {
    const r = await fetch('/api/avoti');
    if (!r.ok) throw new Error(r.status);
    const noDb = await r.json();
    const kodi = new Set(noDb.map(a => a.kods));
    const saraksts = [...noDb, ...TIESSAISTE.filter(a => !kodi.has(a.kods) && (!a.ja || document.getElementById(a.ja)))]
      .map(a => ({ ...TIESSAISTE.find(t => t.kods === a.kods), ...a }))  // DB rindai paliek biežums un svaigums
      .sort((a, b) => (a.kartiba ?? 100) - (b.kartiba ?? 100));
    pecKoda = Object.fromEntries(saraksts.map(a => [a.kods, a]));
    zimet(saraksts);
    return noDb;
  }

  // Svaigums tiešsaistes avotiem: tikai tad, kad sadaļu atver (neliels pieprasījums, API to kešo)
  const laiks = d => d.toLocaleString('lv-LV', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' });
  const SVAIGUMS = {
    bridinajumi: () => fetch('/api/bridinajumi').then(r => r.json()).then(d => d.laiks_lv && `pārbaudīts ${laiks(new Date(d.laiks_lv))}`),
    prognozes: () => fetch('/api/prognozes').then(r => r.json()).then(d => d.prognoze_mainita && `prognoze izdota ${laiks(new Date(d.prognoze_mainita))}`),
  };
  document.getElementById('avoti')?.addEventListener('toggle', e => {
    if (!e.target.open) return;
    for (const s of e.target.querySelectorAll('[data-svaigums]')) {
      SVAIGUMS[s.dataset.svaigums]?.().then(t => { if (t) s.textContent = ' · ' + t; }).catch(() => {});
    }
  });

  // Rinda punkta logā: "Avots: <datu kopa> (izdevējs) · licence".
  function rinda(kods) {
    const a = pecKoda[kods];
    if (!a) return '';
    return `<small class="popup-avots">Avots: ${saite(a.datu_kopa_url, a.nosaukums)} (${esc(a.izdevejs)}) · ` +
      `${saite(a.licences_url, a.licence)}${a.atverts ? '' : `<br><span class="bez-licences">${bridinajums}</span>`}</small>`;
  }

  const atverts = kods => pecKoda[kods]?.atverts !== false;

  return { ieladet, rinda, atverts };
})();
