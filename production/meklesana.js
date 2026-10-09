// "Ko tev vajag?": krīzes meklēšana. Teksts → scenārijs (klasifikators.js + scenariji.json, bez AI, pārlūkā)
// → tuvākās vietas katrā scenārija kategorijā caur /api/objekti. Lieto app.js globālos (karte, stavoklis, iegut…).
const krizesMeklesana = (() => {
  const UZ_KATEGORIJU = 3;
  let klasifikators = null;
  let pedejais = null;          // { teksts, scenarijs } — atkārto, kad mainās atrašanās vieta vai reģions
  let pieprasijums = null;
  const rezultatuSlanis = L.layerGroup().addTo(karte);
  const kaste = el('rezultati');

  async function sakt(regioniSaraksts) {
    try {
      const noteikumi = await (await fetch('scenariji.json')).json();
      klasifikators = Klasifikators.izveidot(noteikumi, regioniSaraksts);
    } catch {
      el('jautajums').disabled = true;
      el('jautajums').placeholder = 'Meklēšana nav pieejama';
      return;
    }
    const q = new URLSearchParams(location.search).get('q');
    if (q) { el('jautajums').value = q; meklet(q); }
  }

  el('meklet-forma').addEventListener('submit', e => {
    e.preventDefault();
    const teksts = el('jautajums').value.trim();
    if (teksts) meklet(teksts); else notirit();
  });
  kaste.addEventListener('click', e => {
    const darbiba = e.target.closest('[data-darbiba]')?.dataset.darbiba;
    if (darbiba === 'notirit') notirit();
    if (darbiba === 'atrast') atrastMani();
    const cits = klasifikators?.scenariji.find(s => s.kods === e.target.closest('[data-cits]')?.dataset.cits);
    if (cits && pedejais) meklet(pedejais.teksts, cits);
    const li = e.target.closest('li[data-lat]');
    if (li && !e.target.closest('a')) {
      const ll = { lat: +li.dataset.lat, lng: +li.dataset.lon };
      karte.setView(ll, Math.max(karte.getZoom(), 16));
      L.popup().setLatLng(ll).setContent(popupSaturs(JSON.parse(li.dataset.p), ll)).openOn(karte);
    }
  });

  function notirit() {
    pedejais = null;
    if (pieprasijums) pieprasijums.abort();
    rezultatuSlanis.clearLayers();
    kaste.hidden = true;
    kaste.innerHTML = '';
    el('jautajums').value = '';
  }

  function atkartot() {
    if (pedejais) meklet(pedejais.teksts, pedejais.scenarijs);
  }

  // Kur meklēt: vietvārds vaicājumā (reģionu meklet() jau izvēlējās) → mana atrašanās vieta → izvēlētais reģions.
  // Reģionam ņem bbox centru.
  function izcelsme(vieta) {
    if (vieta) return { ...centrs(vieta), apraksts: `no centra (${vieta.nosaukums})`, regions: true };
    if (stavoklis.vieta) return { ...stavoklis.vieta, apraksts: stavoklis.vieta.adrese ? `no adreses ${isaAdrese(stavoklis.vieta.adrese)}` : 'no tevis' };
    const r = regioni[stavoklis.regions];
    if (r) return { ...centrs(r), apraksts: `no centra (${r.nosaukums})`, regions: true };
    return null;
  }
  const centrs = r => ({ lat: (r.bbox[1] + r.bbox[3]) / 2, lon: (r.bbox[0] + r.bbox[2]) / 2 });

  // scenarijs: izvēlēts ar pogu (ātrā poga vai "Vai domāji…?") — tad tekstu izmanto tikai vietai un 112.
  async function meklet(teksts, scenarijs = null) {
    if (!klasifikators) return;
    pedejais = { teksts, scenarijs };
    const rez = klasifikators.klasificet(teksts);
    if (scenarijs) {
      rez.scenariji = [scenarijs];
      rez.zvanit112 = rez.dzivibas_draudi || !!scenarijs.zvanit112;
    }
    kaste.hidden = false;
    rezultatuSlanis.clearLayers();

    // Vietvārds vaicājumā ("lācis Ogrē", "Rēzekne") — karti pārvietojam uz to vienmēr, arī ja scenārijs
    // nav atpazīts vai tam nav slāņu kartē (tad zemāk iznākam agrāk un izcelsme() netiek izsaukta).
    const jaunsRegions = rez.vieta && stavoklis.regions !== rez.vieta.kods;
    if (rez.vieta) radtRegionu(rez.vieta.kods);

    if (!rez.scenariji.length) {
      if (jaunsRegions) atjaunot();
      kaste.innerHTML = zvanit(rez) + (rez.vieta ? `<p class="sapratu">Vieta: <b>${esc(rez.vieta.nosaukums)}</b></p>` : '') +
        `<p class="piezime">Nesapratu, ko tev vajag. Izvēlies kādu no pogām augstāk
        vai uzraksti citiem vārdiem, piem., „patvertne”, „ārsts”, „aptieka”.</p>` + (rez.zvanit112 ? '' : zvanit({ zvanit112: true }, true)) + notiritPoga();
      return;
    }

    // Galvenais scenārijs nosaka padomu un slāņus; pārējos piedāvājam kā "Vai domāji…?"
    const [galvenais, ...citi] = rez.scenariji;
    const galva = zvanit(rez) +
      `<p class="sapratu">${galvenais.nr ? 'Situācija' : 'Meklēju'}: <b>${esc(galvenais.nosaukums)}</b>${rez.vieta ? ' · ' + esc(rez.vieta.nosaukums) : ''}</p>` +
      (galvenais.padoms ? `<p class="padoms">${esc(galvenais.padoms)}</p>` : '');
    const vaiDomaji = citi.length ? `<p class="piezime">Vai domāji:</p><div class="atras-pogas">` +
      citi.map(s => `<button type="button" data-cits="${esc(s.kods)}">${esc(s.nosaukums)}</button>`).join('') + '</div>' : '';

    // Slāņi, kuru vēl nav kartē (piem., noturības punkti), tiek izlaisti; ja nepaliek neviens — tikai padoms.
    const kodi = galvenais.kategorijas.filter(k => kategorijas[k]?.skaits);
    if (!kodi.length) {
      if (jaunsRegions) atjaunot();
      kaste.innerHTML = galva + vaiDomaji + notiritPoga();
      return;
    }

    stavoklis.kategorijas = new Set(kodi);
    document.querySelectorAll('#kategorijas input').forEach(i => { i.checked = stavoklis.kategorijas.has(i.value); });
    const no = izcelsme(rez.vieta);
    atjaunot();

    if (!no) {
      kaste.innerHTML = galva + `<p class="piezime">Lai atrastu tuvākās vietas, nosaki savu atrašanās vietu
        vai pievieno pilsētu, piem., „${esc(teksts)} Ogrē”.</p>
        <button type="button" class="galvena" data-darbiba="atrast">📍 Noteikt manu atrašanās vietu</button>` + vaiDomaji + notiritPoga();
      return;
    }

    kaste.innerHTML = galva + '<p class="piezime">Meklē tuvākās vietas…</p>';
    if (pieprasijums) pieprasijums.abort();
    pieprasijums = new AbortController();
    try {
      const grupas = await Promise.all(kodi.map(k => iegut('/objekti?' + new URLSearchParams(
        { kategorijas: k, lat: no.lat.toFixed(5), lon: no.lon.toFixed(5), limit: UZ_KATEGORIJU * 2 }), pieprasijums.signal)));
      grupas.forEach(g => { g.features = izveleties(g.features); });
      kaste.innerHTML = galva + kodi.map((k, i) => grupa(k, grupas[i].features, no)).join('') +
        '<p class="piezime">Attālums taisnā līnijā ' + esc(no.apraksts) + '.</p>' + vaiDomaji + notiritPoga();
      zimetKarte(grupas.map(g => g.features), no, rez.vieta);
    } catch (e) {
      if (e.name !== 'AbortError') kaste.innerHTML = galva + '<p class="piezime kluda">Vietas neizdevās ielādēt. Mēģini vēlreiz pēc brīža.</p>';
    }
  }

  // Specializētās slimnīcas (dzemdību nams, psihiatrija; ipasibas.specializeta) pēc vispārējām, citādi pēc attāluma.
  const izveleties = features => features
    .map((f, i) => ({ f, i, spec: f.properties.ipasibas?.specializeta ? 1 : 0 }))
    .sort((a, b) => a.spec - b.spec || a.i - b.i).slice(0, UZ_KATEGORIJU).map(x => x.f);

  function zvanit(rez, mazs = false) {
    if (!rez.zvanit112) return '';
    return mazs
      ? '<p class="piezime">Ja apdraudēta dzīvība, zvani <a href="tel:112">112</a>.</p>'
      : `<a class="zvanit112" href="tel:112">📞 Zvanīt 112</a>` +
        `<p class="piezime">${rez.dzivibas_draudi ? 'Izklausās, ka apdraudēta dzīvība. Zvani tūlīt, dispečers palīdzēs.' : 'Ārkārtas situācijā zvani 112.'}</p>`;
  }

  const notiritPoga = () => '<button type="button" class="otra" data-darbiba="notirit">✕ Notīrīt meklēšanu</button>';

  function grupa(kods, features, no) {
    const k = kategorijas[kods];
    if (!features.length) return '';
    const vienumi = features.map(f => {
      // attālums no reģiona centra nav "no tevis", tāpēc uznirstošajā logā to nerādām
      const p = no.regions ? { ...f.properties, attalums_m: null } : f.properties;
      const [lon, lat] = f.geometry.coordinates;
      return `<li tabindex="0" data-lat="${lat}" data-lon="${lon}" data-p="${esc(JSON.stringify(p))}">
        <span class="teksts"><b>${esc(nosaukums(p) || k.nosaukums)}</b><small>${esc(p.adrese || '')}</small>${marsrutaSaites(lat, lon, no.regions ? null : no)}</span>
        <span class="attalums">${attalums(f.properties.attalums_m)}</span></li>`;
    }).join('');
    return `<h3><span class="punkts" style="background:${esc(k.krasa)}"></span>${esc(k.nosaukums)}</h3><ol class="rez-saraksts">${vienumi}</ol>`;
  }

  // Karti pietuvina sākumpunktam (un vaicājuma vietai) + tuvākajai vietai katrā kategorijā; tālākās (piem., 24/7
  // slimnīca citā novadā) tikai uzzīmē, citādi pilsēta paliek mazā stūrītī.
  function zimetKarte(grupas, no, vieta) {
    const punkti = [[no.lat, no.lon]];
    if (vieta) punkti.push([vieta.bbox[1], vieta.bbox[0]], [vieta.bbox[3], vieta.bbox[2]]);
    for (const g of grupas) if (g[0]) punkti.push([...g[0].geometry.coordinates].reverse());
    for (const f of grupas.flat()) {
      const [lon, lat] = f.geometry.coordinates;
      const k = kategorijas[f.properties.kategorija] || {};
      L.circleMarker([lat, lon], { radius: 10, color: '#1c1917', weight: 2.5, fillColor: k.krasa || '#57534e', fillOpacity: 1 })
        .bindPopup(() => popupSaturs(no.regions ? { ...f.properties, attalums_m: null } : f.properties, { lat, lng: lon }))
        .addTo(rezultatuSlanis);
    }
    if (no.regions) L.circleMarker([no.lat, no.lon], { radius: 5, color: '#1c1917', weight: 2, fillOpacity: 0 })
      .bindTooltip('Attālumi no šejienes').addTo(rezultatuSlanis);
    karte.fitBounds(L.latLngBounds(punkti), { padding: [40, 40], maxZoom: 15 });
  }

  // Enter rezultātu sarakstā = klikšķis
  kaste.addEventListener('keydown', e => { if (e.key === 'Enter' && e.target.matches('li[data-lat]')) e.target.click(); });

  return { sakt, atkartot, meklet };
})();
