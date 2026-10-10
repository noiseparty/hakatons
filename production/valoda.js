// Rezultāta kartītes valoda: LV (noklusētā), RU vai EN. Meklēšana jau saprot krievu un angļu vaicājumus
// (klasifikators.js); te — kartītes "rāmis" (112 rinda, lēmums, sadaļu virsraksti, pogas, "Maršruts", "Avots")
// vaicājuma valodā. Padomi un "Kas notiks tālāk" soļi paliek latviski (oficiālais avots, bez mašīntulkošanas),
// virs tiem rinda "Padomi latviski (oficiālais avots)". Dati (vietu, kategoriju, brīdinājumu nosaukumi) netiek tulkoti.
//
// Valoda = slēdzī izvēlētā (LV/RU/EN, atceras localStorage) vai, ja nav izvēlēta, noteiktā no pēdējā vaicājuma
// (Klasifikators.valoda). Valoda.t('latviskais teksts') → teksts aktīvajā valodā; ja tulkojuma nav — latviskais.
// Statiskie elementi ar data-t="…" (teksts) vai data-t-placeholder="…" mainās līdzi.
const Valoda = (() => {
  const VALODAS = ['lv', 'ru', 'en'];
  const ATSLEGA = 'valoda';

  // Atslēga = latviskais teksts (tad meklesana.js paliek lasāms un bez valoda.js nekas nesalūzt);
  // gariem tekstiem — īsa atslēga ar lauku lv. {x} — vieta mainīgajam (Valoda.t(atslēga, { x })).
  const V = {
    // 112
    'Ja apdraudēta dzīvība vai veselība, zvaniet 112.': {
      ru: 'Если под угрозой жизнь или здоровье, звоните 112.',
      en: 'If life or health is in danger, call 112.' },
    'Izklausās, ka apdraudēta dzīvība. Zvaniet 112 tūlīt: dispečers palīdzēs, ko darīt.': {
      ru: 'Похоже, что под угрозой жизнь. Звоните 112 сейчас: диспетчер подскажет, что делать.',
      en: 'It sounds like a life is in danger. Call 112 now: the dispatcher will tell you what to do.' },
    // Meklēšanas josla un slēdzis
    'Meklēt': { ru: 'Найти', en: 'Search' },
    'Kas Jums vajadzīgs? Piem.: plūdi Ogrē': { ru: 'Что Вам нужно? Например: нет света Резекне', en: 'What do you need? E.g.: flood Ogre' },
    'Rezultāta valoda': { ru: 'Язык результата', en: 'Result language' },
    // Lēmums
    'šai vietai': { ru: 'для этого места', en: 'for this place' },
    'šajā apvidū': { ru: 'в этом районе', en: 'in this area' },
    'LVĢMC brīdinājums {kur}:': { ru: 'Предупреждение LVĢMC {kur}:', en: 'LVĢMC warning {kur}:' },
    'LVĢMC brīdinājumu {kur} nav.': { ru: 'Предупреждений LVĢMC {kur} нет.', en: 'No LVĢMC warnings {kur}.' },
    'LVĢMC brīdinājumus šobrīd neizdevās pārbaudīt.': {
      ru: 'Предупреждения LVĢMC сейчас проверить не удалось.', en: 'LVĢMC warnings could not be checked right now.' },
    'Skatiet meteo.lv vai klausieties LR1.': { ru: 'Смотрите meteo.lv или слушайте LR1.', en: 'See meteo.lv or listen to LR1.' },
    'Plūdu riska zona': { ru: 'Зона риска наводнений', en: 'Flood risk zone' },
    'Pārbauda… (līdz 15 s)': { ru: 'Проверяем… (до 15 с)', en: 'Checking… (up to 15 s)' },
    'Tuvākā upe vai ezers': { ru: 'Ближайшая река или озеро', en: 'Nearest river or lake' },
    'Ielādē…': { ru: 'Загрузка…', en: 'Loading…' },
    'Jā': { ru: 'Да', en: 'Yes' },
    'Nē': { ru: 'Нет', en: 'No' },
    'nav applūstošā teritorijā (10 %, 1 % un 0,5 % kartes).': {
      ru: 'не в зоне затопления (карты 10 %, 1 % и 0,5 %).', en: 'not in a flood-prone area (10 %, 1 % and 0.5 % maps).' },
    'Neizdevās pārbaudīt. Plūdu zonas redzamas kartē (slānis ieslēgts).': {
      ru: 'Проверить не удалось. Зоны наводнений видны на карте (слой включён).',
      en: 'Could not be checked. Flood zones are shown on the map (layer on).' },
    'Rādīt plūdu zonas kartē': { ru: 'Показать зоны наводнений на карте', en: 'Show flood zones on the map' },
    // Kas sapratām
    'Situācija': { ru: 'Ситуация', en: 'Situation' },
    'Meklēju': { ru: 'Ищу', en: 'Looking for' },
    'Adrese': { ru: 'Адрес', en: 'Address' },
    'Vieta': { ru: 'Место', en: 'Place' },
    'Meklē adresi…': { ru: 'Ищем адрес…', en: 'Looking up the address…' },
    'Uzrakstiet arī, kas notiek, piem., „plūdi”, „nav elektrības”, „evakuācija”.': {
      ru: 'Напишите также, что происходит, например: «наводнение», «нет света», «эвакуация».',
      en: 'Also write what is happening, e.g. “flood”, “no power”, “evacuation”.' },
    nesapratam: {
      lv: 'Nesapratām, kas Jums vajadzīgs. Uzrakstiet citiem vārdiem, piem., „patvertne”, „ārsts”, „plūdi Ogrē”, „nav elektrības Brīvības 15 Ogre”.',
      ru: 'Мы не поняли, что Вам нужно. Напишите иначе, например: «убежище», «врач», «наводнение Огре», «нет света Brīvības 15 Ogre».',
      en: 'We did not understand what you need. Try other words, e.g. “shelter”, “doctor”, “flood Ogre”, “no power Brīvības 15 Ogre”.' },
    vieta_zina: {
      ru: 'Чтобы найти ближайшие места, добавьте адрес или город (например, «… Ogre» или «… Brīvības 15 Ogre») или определите своё местоположение.',
      en: 'To find the nearest places, add an address or town (e.g. “… Ogre” or “… Brīvības 15 Ogre”) or use your location.' },
    'Kartes dati pašlaik nav pieejami: tuvākās vietas nevaram parādīt. Padoms un 112 ir spēkā.': {
      ru: 'Данные карты сейчас недоступны: ближайшие места показать не можем. Советы и 112 действуют.',
      en: 'Map data is unavailable right now, so we cannot show the nearest places. The advice and 112 still apply.' },
    // Sadaļu virsraksti
    'Brīdinājumi': { ru: 'Предупреждения', en: 'Warnings' },
    'Lēmums': { ru: 'Решение', en: 'Decision' },
    'Tuvākās vietas': { ru: 'Ближайшие места', en: 'Nearest places' },
    'Ko darīt': { ru: 'Что делать', en: 'What to do' },
    'Drošās vietas tuvumā': { ru: 'Безопасные места поблизости', en: 'Safe places nearby' },
    'Kas notiks tālāk': { ru: 'Что будет дальше', en: 'What happens next' },
    'Padomi latviski (oficiālais avots)': {
      ru: 'Советы на латышском языке (официальный источник)', en: 'Advice in Latvian (official source)' },
    // Drošās vietas
    'Evakuācijas pulcēšanās vieta': { ru: 'Пункт сбора для эвакуации', en: 'Evacuation assembly point' },
    'Izmitināšanas vieta': { ru: 'Место временного размещения', en: 'Temporary accommodation' },
    'Tuvākā patvertne': { ru: 'Ближайшее укрытие', en: 'Nearest shelter' },
    '24/7 neatliekamā palīdzība': { ru: 'Неотложная помощь 24/7', en: '24/7 emergency care' },
    'Tuvākā mūsu datos ir tālu, citā pašvaldībā. Jautājiet savai pašvaldībai vai izmantojiet tuvāko patvertni.': {
      ru: 'Ближайшее в наших данных далеко, в другом самоуправлении. Спросите своё самоуправление или используйте ближайшее укрытие.',
      en: 'The nearest one in our data is far away, in another municipality. Ask your municipality or use the nearest shelter.' },
    'Šai vietai pašvaldības CA plānā mūsu datos vēl nav. Izmantojiet tuvāko patvertni.': {
      ru: 'Для этого места в наших данных из плана гражданской защиты самоуправления пока ничего нет. Используйте ближайшее укрытие.',
      en: 'Our data from the municipal civil protection plan has nothing for this place yet. Use the nearest shelter.' },
    'Datos nav atrasta. Jautājiet pašvaldībai.': { ru: 'В данных не найдено. Спросите самоуправление.', en: 'Not found in the data. Ask the municipality.' },
    'Meklē tuvākās vietas…': { ru: 'Ищем ближайшие места…', en: 'Finding the nearest places…' },
    'Daļu tuvāko vietu neizdevās ielādēt. Mēģiniet vēlreiz pēc brīža; padoms un 112 ir spēkā.': {
      ru: 'Часть ближайших мест загрузить не удалось. Попробуйте ещё раз чуть позже; советы и 112 действуют.',
      en: 'Some nearby places could not be loaded. Try again shortly; the advice and 112 still apply.' },
    'Vietas neizdevās ielādēt. Mēģiniet vēlreiz pēc brīža.': {
      ru: 'Не удалось загрузить места. Попробуйте ещё раз чуть позже.', en: 'Places could not be loaded. Try again shortly.' },
    'Attālums taisnā līnijā': { ru: 'Расстояние по прямой', en: 'Straight-line distance' },
    // Saites, avoti, pogas
    'Maršruts': { ru: 'Маршрут', en: 'Route' },
    'ar auto': { ru: 'на машине', en: 'by car' },
    'kājām': { ru: 'пешком', en: 'on foot' },
    'Avots': { ru: 'Источник', en: 'Source' },
    'Radio krīzē': { ru: 'Радио в кризис', en: 'Radio in a crisis' },
    'visas frekvences': { ru: 'все частоты', en: 'all frequencies' },
    'Izmantot manu atrašanās vietu': { ru: 'Использовать моё местоположение', en: 'Use my location' },
    'Noteikt manu atrašanās vietu': { ru: 'Использовать моё местоположение', en: 'Use my location' },
    'Vai domājāt:': { ru: 'Возможно, Вы имели в виду:', en: 'Did you mean:' },
    'Visi kartes objekti sarakstā': { ru: 'Все объекты карты списком', en: 'All map objects as a list' },
    'Ziņot par bīstamību šeit': { ru: 'Сообщить об опасности здесь', en: 'Report a hazard here' },
    'Notīrīt meklēšanu': { ru: 'Очистить поиск', en: 'Clear search' },
  };

  let izveleta = null;   // slēdzī izvēlētā (localStorage) vai null — tad pēc vaicājuma
  let noteikta = 'lv';   // no pēdējā vaicājuma
  try { const v = localStorage.getItem(ATSLEGA); if (VALODAS.includes(v)) izveleta = v; } catch { /* privātais režīms */ }

  const aktiva = () => izveleta || noteikta;

  function t(atslega, mainigie) {
    const ieraksts = V[atslega];
    let s = ieraksts?.[aktiva()] ?? ieraksts?.lv ?? atslega;
    if (mainigie) for (const [k, v] of Object.entries(mainigie)) s = s.split('{' + k + '}').join(v);
    return s;
  }

  // Rinda virs latviskajiem padomiem (tikai RU/EN): tulkojums un latviskais oriģināls
  const padomiPiezime = () => aktiva() === 'lv' ? ''
    : `<p class="valoda-padomi">${t('Padomi latviski (oficiālais avots)')} · <span lang="lv">Padomi latviski (oficiālais avots)</span></p>`;

  // Statiskie elementi (112 josla, meklēšanas lauks, poga "Izmantot manu atrašanās vietu") un slēdža stāvoklis
  function lietot() {
    const v = aktiva();
    document.querySelectorAll('[data-t]').forEach(e => { e.textContent = t(e.dataset.t); e.lang = v; });
    document.querySelectorAll('[data-t-placeholder]').forEach(e => { e.placeholder = t(e.dataset.tPlaceholder); });
    document.querySelectorAll('.valoda-sledzis button').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.valoda === v)));
  }

  // Meklēšana (meklesana.js) pirms kartītes zīmēšanas: valoda no vaicājuma, ja slēdzī nav izvēlēta
  function noteikt(vaicajums) {
    const v = typeof Klasifikators !== 'undefined' && Klasifikators.valoda ? Klasifikators.valoda(vaicajums) : 'lv';
    if (v !== noteikta) { noteikta = v; if (!izveleta) lietot(); }
    return aktiva();
  }

  function izveleties(v) {
    if (!VALODAS.includes(v)) return;
    izveleta = v;
    try { localStorage.setItem(ATSLEGA, v); } catch { /* privātais režīms */ }
    lietot();
    // atvērto rezultātu pārzīmē jaunajā valodā (tas pats vaicājums un scenārijs)
    if (typeof krizesMeklesana !== 'undefined' && !document.getElementById('rezultati')?.hidden) krizesMeklesana.atkartot();
  }

  // Slēdzis LV / RU / EN zem meklēšanas lauka (formā, lai sheet.js / darbvirsma.js to pārvieto kopā ar lauku)
  const forma = document.getElementById('meklet-forma');
  if (forma) {
    const sledzis = document.createElement('div');
    sledzis.className = 'valoda-sledzis';
    sledzis.setAttribute('role', 'group');
    sledzis.setAttribute('aria-label', 'Valoda / Язык / Language');
    sledzis.innerHTML = [['lv', 'Latviski'], ['ru', 'По-русски'], ['en', 'English']].map(([v, nos]) =>
      `<button type="button" data-valoda="${v}" lang="${v}" aria-label="${nos}" aria-pressed="false">${v.toUpperCase()}</button>`).join('');
    sledzis.addEventListener('click', e => { const b = e.target.closest('button[data-valoda]'); if (b) izveleties(b.dataset.valoda); });
    forma.insertBefore(sledzis, document.getElementById('populari') || null);
  }
  lietot();
  document.addEventListener('DOMContentLoaded', lietot);  // darbvirsma.js elementi rodas pēc šī faila

  return { t, aktiva, noteikt, izveleties, padomiPiezime, lietot };
})();
