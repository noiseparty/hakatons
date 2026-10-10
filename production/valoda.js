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
    // Soļu josla zem meklēšanas lauka
    'Soļi': { ru: 'Шаги', en: 'Steps' },
    'Jautājums': { ru: 'Вопрос', en: 'Question' },
    'Atbilde': { ru: 'Ответ', en: 'Answer' },
    'Rīcība': { ru: 'Действие', en: 'Action' },
    // Lēmuma rinda kartītes augšā
    'Tuvākā vieta': { ru: 'Ближайшее место', en: 'Nearest place' },
    'Tuvākā pulcēšanās vieta': { ru: 'Ближайший пункт сбора', en: 'Nearest assembly point' },
    'Tuvākā izmitināšanas vieta': { ru: 'Ближайшее место размещения', en: 'Nearest temporary accommodation' },
    'Tuvākā 24/7 neatliekamā palīdzība': { ru: 'Ближайшая неотложная помощь 24/7', en: 'Nearest 24/7 emergency care' },
    'Tuvākā ārstniecības iestāde': { ru: 'Ближайшее медицинское учреждение', en: 'Nearest medical institution' },
    'Tuvākā aptieka': { ru: 'Ближайшая аптека', en: 'Nearest pharmacy' },
    'Tuvākais bankomāts': { ru: 'Ближайший банкомат', en: 'Nearest ATM' },
    'Tuvākā policija': { ru: 'Ближайшая полиция', en: 'Nearest police station' },
    'Tuvākais ugunsdzēsēju depo': { ru: 'Ближайшее пожарное депо', en: 'Nearest fire station' },
    'Tuvākā degvielas uzpilde': { ru: 'Ближайшая заправка', en: 'Nearest fuel station' },
    'Tuvākais noturības punkta kandidāts': { ru: 'Ближайший кандидат в пункт устойчивости', en: 'Nearest resilience point candidate' },
    'Tuvākā pietura': { ru: 'Ближайшая остановка', en: 'Nearest stop' },
    'no kartes centra': { ru: 'от центра карты', en: 'from the map centre' },
    'no centra ({x})': { ru: 'от центра ({x})', en: 'from the centre ({x})' },
    '{x}, centrs': { ru: '{x}, центр', en: '{x}, centre' },
    'Adrese „{a}” VZD adrešu reģistrā nav atrasta; rādām atrasto: {x}.': { ru: 'Адрес «{a}» не найден в реестре адресов VZD; показываем найденный: {x}.', en: 'Address "{a}" was not found in the VZD address register; showing the one found: {x}.' },
    'Adrese „{a}” VZD adrešu reģistrā nav atrasta; rādām pēc vietas: {x}.': { ru: 'Адрес «{a}» не найден в реестре адресов VZD; показываем по месту: {x}.', en: 'Address "{a}" was not found in the VZD address register; showing results for: {x}.' },
    'Adrese „{a}” VZD adrešu reģistrā nav atrasta. Pārbaudiet adresi vai izmantojiet savu atrašanās vietu.': { ru: 'Адрес «{a}» не найден в реестре адресов VZD. Проверьте адрес или используйте своё местоположение.', en: 'Address "{a}" was not found in the VZD address register. Check the address or use your location.' },
    'pārbauda…': { ru: 'проверяем…', en: 'checking…' },
    'meklē…': { ru: 'ищем…', en: 'searching…' },
    'upe virs kritiskā līmeņa': { ru: 'река выше критического уровня', en: 'river above the critical level' },
    'kartes vēl ielādējas…': { ru: 'карты ещё загружаются…', en: 'maps are still loading…' },
    'pašlaik nevar pārbaudīt; zonas redzamas kartē': {
      ru: 'сейчас проверить нельзя; зоны видны на карте', en: 'cannot be checked right now; zones are shown on the map' },
    'neizdevās pārbaudīt; zonas redzamas kartē': {
      ru: 'проверить не удалось; зоны видны на карте', en: 'could not be checked; zones are shown on the map' },
    '{x} % varbūtība gadā': { ru: 'вероятность {x} % в год', en: '{x} % chance per year' },
    'pēc pieejamajām kartēm nē (daļa karšu neatbildēja)': {
      ru: 'по доступным картам нет (часть карт не ответила)', en: 'no, according to the available maps (some maps did not respond)' },
    'nav applūstošā teritorijā': { ru: 'не в зоне затопления', en: 'not in a flood-prone area' },
    'Atrašanās vieta nav atļauta.': { ru: 'Доступ к местоположению не разрешён.', en: 'Location access is not allowed.' },
    'Atrašanās vietu neizdevās noteikt.': { ru: 'Местоположение определить не удалось.', en: 'Your location could not be determined.' },
    vieta_nav: {
      lv: 'Pievienojiet vaicājumam adresi vai pilsētu, piem., „{x} Ogrē” vai „… Brīvības 15 Ogre”.',
      ru: 'Добавьте к запросу адрес или город, например, «{x} Ogre» или «… Brīvības 15 Ogre».',
      en: 'Add an address or town to the query, e.g. “{x} Ogre” or “… Brīvības 15 Ogre”.' },
    // MI zīme pie CA plāna vietām; "Kā tas tapa" (Datu avoti)
    'izvilkts ar MI no CA plāna': { ru: 'извлечено ИИ из плана гражданской защиты', en: 'extracted by AI from the civil protection plan' },
    '{x}. lpp.': { ru: 'стр. {x}', en: 'p. {x}' },
    'atvērt plānu': { ru: 'открыть план', en: 'open the plan' },
    'Atvērt CA plānu': { ru: 'Открыть план гражданской защиты', en: 'Open the civil protection plan' },
    'Kā tas tapa': { ru: 'Как это сделано', en: 'How it was made' },
    // Saraksts (saraksts.js): rāmis; vietu, slāņu un avotu nosaukumi paliek kā datos
    'Vietas kartes skatā': { ru: 'Места в области карты', en: 'Places in the map view' },
    'Aizvērt sarakstu': { ru: 'Закрыть список', en: 'Close the list' },
    'Meklēt sarakstā': { ru: 'Искать в списке', en: 'Search the list' },
    'Filtrēt sarakstu pēc nosaukuma vai adreses': { ru: 'Фильтр списка по названию или адресу', en: 'Filter the list by name or address' },
    'Kārtošana': { ru: 'Сортировка', en: 'Sort order' },
    'Tuvākās': { ru: 'Ближайшие', en: 'Nearest' },
    'Pēc nosaukuma': { ru: 'По названию', en: 'By name' },
    'Rādīt slāņus': { ru: 'Показать слои', en: 'Show layers' },
    'Karte pārvietota — atjaunot sarakstu': { ru: 'Карта сдвинута — обновить список', en: 'Map moved — refresh the list' },
    'Lejupielādēt CSV': { ru: 'Скачать CSV', en: 'Download CSV' },
    'Drukāt sarakstu': { ru: 'Распечатать список', en: 'Print the list' },
    'no adreses': { ru: 'от адреса', en: 'from the address' },
    'no Jums': { ru: 'от Вас', en: 'from you' },
    'adreses {adrese}': { ru: 'адреса {adrese}', en: 'the address {adrese}' },
    'Jūsu atrašanās vietas': { ru: 'Вашего местоположения', en: 'your location' },
    'kartes centra': { ru: 'центра карты', en: 'the map centre' },
    'Sakārtots pēc attāluma no {kur} (taisnā līnijā).': {
      ru: 'Сортировка по расстоянию от {kur} (по прямой).', en: 'Sorted by distance from {kur} (straight line).' },
    'Sakārtots pēc nosaukuma; attālums no {kur} (taisnā līnijā).': {
      ru: 'Сортировка по названию; расстояние от {kur} (по прямой).', en: 'Sorted by name; distance from {kur} (straight line).' },
    'attālums no {kur} (taisnā līnijā)': { ru: 'расстояние от {kur} (по прямой)', en: 'distance from {kur} (straight line)' },
    'Nav ieslēgts neviens slānis. Ieslēdziet slāni (piem., Publiskās patvertnes) vai meklējiet augšā.': {
      ru: 'Не включён ни один слой. Включите слой (например, «Publiskās patvertnes») или воспользуйтесь поиском выше.',
      en: 'No layer is switched on. Switch on a layer (e.g. “Publiskās patvertnes”) or search above.' },
    'Ielādē vietas kartes skatā…': { ru: 'Загружаем места в области карты…', en: 'Loading places in the map view…' },
    'Kartes skatā vietu nav. Attāliniet vai pārvietojiet karti.': {
      ru: 'В области карты мест нет. Отдалите или сдвиньте карту.', en: 'No places in the map view. Zoom out or move the map.' },
    '{vietas} skatā': { ru: 'Мест в области карты: {n}', en: 'Places in view: {n}' },
    'filtrā {n}': { ru: 'по фильтру {n}', en: '{n} match the filter' },
    'rādīti pirmie {n}, pietuviniet karti, lai redzētu visas': {
      ru: 'показаны первые {n}, приблизьте карту, чтобы увидеть все', en: 'showing the first {n}, zoom in to see all' },
    'Filtram neatbilst neviena vieta.': { ru: 'Под фильтр не подходит ни одно место.', en: 'No places match the filter.' },
    'Rādīt vēl {n} (kopā {kopa})': { ru: 'Показать ещё {n} (всего {kopa})', en: 'Show {n} more ({kopa} in total)' },
    'atvērts': { ru: 'открыто', en: 'open' },
    'slēgts': { ru: 'закрыто', en: 'closed' },
    'pilns': { ru: 'мест нет', en: 'full' },
    'nedarbojas': { ru: 'не работает', en: 'not working' },
    'statuss nav zināms': { ru: 'статус неизвестен', en: 'status unknown' },
    'licence nav norādīta': { ru: 'лицензия не указана', en: 'licence not stated' },
    'nav atvērtas licences': { ru: 'нет открытой лицензии', en: 'no open licence' },
    '{n} vietas': { ru: 'мест: {n}', en: '{n} places' },
    'ratiņkrēslam': { ru: 'для инвалидной коляски', en: 'wheelchair' },
    'dzīvnieki': { ru: 'животные', en: 'pets' },
    'ir': { ru: 'да', en: 'yes' },
    'nav': { ru: 'нет', en: 'no' },
    'Datu avoti': { ru: 'Источники данных', en: 'Data sources' },
    // Dalīties / Drukāt (dalities.js)
    'Dalīties': { ru: 'Поделиться', en: 'Share' },
    'Drukāt': { ru: 'Печать', en: 'Print' },
    'Krīzes karte': { ru: 'Карта кризиса', en: 'Crisis map' },
    'meklēšanas rezultāts': { ru: 'результат поиска', en: 'search result' },
    'izdrukāts': { ru: 'напечатано', en: 'printed' },
    'Atjaunināts rezultāts tiešsaistē:': { ru: 'Обновлённый результат онлайн:', en: 'Updated result online:' },
    'Dati mainās (brīdinājumi, ūdens līmenis). Pirms došanās pārbaudiet tiešsaistē vai klausieties Latvijas Radio 1. Ja apdraudēta dzīvība, zvaniet 112.': {
      ru: 'Данные меняются (предупреждения, уровень воды). Перед выходом проверьте онлайн или слушайте Latvijas Radio 1. Если под угрозой жизнь, звоните 112.',
      en: 'Data changes (warnings, water level). Before you set out, check online or listen to Latvijas Radio 1. If life is in danger, call 112.' },
    'QR kods uz šo rezultātu': { ru: 'QR-код на этот результат', en: 'QR code for this result' },
    'Saite nokopēta. Ielīmējiet to ziņā vai e-pastā.': { ru: 'Ссылка скопирована. Вставьте её в сообщение или письмо.', en: 'Link copied. Paste it into a message or email.' },
    'Nokopējiet saiti no adreses joslas:': { ru: 'Скопируйте ссылку из адресной строки:', en: 'Copy the link from the address bar:' },
    // CSV kolonnas un drukas tabula
    'Nosaukums': { ru: 'Название', en: 'Name' },
    'Slānis': { ru: 'Слой', en: 'Layer' },
    'Platums': { ru: 'Широта', en: 'Latitude' },
    'Garums': { ru: 'Долгота', en: 'Longitude' },
    'Attālums, m': { ru: 'Расстояние, м', en: 'Distance, m' },
    'Attālums no': { ru: 'Расстояние от', en: 'Distance from' },
    'Statuss': { ru: 'Статус', en: 'Status' },
    'Ēkas veids': { ru: 'Тип здания', en: 'Building type' },
    'Ietilpība': { ru: 'Вместимость', en: 'Capacity' },
    'Ratiņkrēslam': { ru: 'Для инвалидной коляски', en: 'Wheelchair' },
    'Dzīvnieki': { ru: 'Животные', en: 'Pets' },
    'Izdevējs': { ru: 'Издатель', en: 'Publisher' },
    'Licence': { ru: 'Лицензия', en: 'Licence' },
    'Licences saite': { ru: 'Ссылка на лицензию', en: 'Licence link' },
    'Datu kopa': { ru: 'Набор данных', en: 'Dataset' },
    'Nr.': { ru: '№', en: 'No.' },
    'Attālums': { ru: 'Расстояние', en: 'Distance' },
    'Avots, licence': { ru: 'Источник, лицензия', en: 'Source, licence' },
  };

  let izveleta = null;   // slēdzī izvēlētā (localStorage) vai null — tad pēc vaicājuma
  let noteikta = 'lv';   // no pēdējā vaicājuma
  try { const v = localStorage.getItem(ATSLEGA); if (VALODAS.includes(v)) izveleta = v; } catch { /* privātais režīms */ }
  // Saite ?q=…&valoda=ru (dalities.js) atjauno kartītes valodu; neaiztiek localStorage (saites saņēmēja izvēle paliek)
  { const v = new URLSearchParams(location.search).get('valoda'); if (VALODAS.includes(v)) izveleta = v; }

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
