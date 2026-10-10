// Zibens slānis (/api/zibens): izlādes pēdējās 30 min no FMI (Ilmatieteen laitos, CC BY 4.0) — jo svaigāka, jo
// spilgtāka; un LVĢMC 24 h zibens režģis (CC0, 5×5 km, kavējas ~2–3 h) — pelēki apļi. Kad slānis ieslēgts,
// atjauno ik minūti; tukša karte nozīmē atbildi "zibens nav reģistrēts". Izmanto `karte` un `el` no app.js.
const Zibens = (() => {
  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const pulkstenis = iso => new Date(iso).toLocaleTimeString('lv-LV', { hour: '2-digit', minute: '2-digit' });
  const avots = a => `<a href="${esc(a.url)}" target="_blank" rel="noopener">${esc(a.nosaukums)}</a> · ${esc(a.licence)}`;
  const slanis = L.layerGroup();
  const teksts = el('zibens-teksts');
  let taimeris = null;

  function zimet(d) {
    slanis.clearLayers();
    for (const s of d.rezgis_24h?.sunas || []) {
      L.circleMarker([s.lat, s.lon], { radius: Math.min(4 + Math.sqrt(s.skaits) * 2, 16), color: '#57534e', weight: 1, fillColor: '#a8a29e', fillOpacity: 0.35 })
        .bindPopup(`<div class="popup"><b>${Valoda.t('Zibens 5×5 km šūnā: {n}', { n: s.skaits })}</b>${Valoda.t('pēdējās 24 h, pēdējais {t}', { t: esc(s.pedejais?.slice(11, 16)) })}` +
          `<small class="popup-avots">${Valoda.t('Kavējas ~2–3 h.')} ${avots(d.rezgis_avots)}</small></div>`).addTo(slanis);
    }
    const tagad = Date.now();
    for (const z of d.zibeni || []) {
      const min = (tagad - new Date(z.laiks)) / 60000;
      const krasa = min <= 10 ? '#dc2626' : min <= 20 ? '#f97316' : '#facc15';
      L.circleMarker([z.lat, z.lon], { radius: 6, color: '#1c1917', weight: 1, fillColor: krasa, fillOpacity: Math.max(0.35, 1 - min / 40) })
        .bindPopup(`<div class="popup"><b>${Ik('zibens')} ${Valoda.t('Zibens {t}', { t: pulkstenis(z.laiks) })}</b>${Valoda.t('pirms {n} min', { n: Math.max(0, Math.round(min)) })}` +
          `${z.strava != null ? Valoda.t(', strāva {v} kA', { v: Math.round(z.strava) }) : ''}<small class="popup-avots">${Valoda.t('Zibens')}: ${avots(d.avots)}</small></div>`)
        .addTo(slanis);
    }
    const n = d.skaits, min = d.minutes || 30;
    teksts.innerHTML = (n == null ? Valoda.t('Pēdējo {m} min dati nav pieejami.', { m: min })
      : n === 0 ? Valoda.t('Pēdējās {m} min zibens nav reģistrēts.', { m: min })
      : Valoda.t(n % 10 === 1 && n % 100 !== 11 ? 'Pēdējās {m} min: {n} zibens izlāde, pēdējā {t}.' : 'Pēdējās {m} min: {n} zibens izlādes, pēdējā {t}.', { m: min, n, t: pulkstenis(d.zibeni[n - 1].laiks) })) +
      `<br><small>${Valoda.t('Zibens')}: ${avots(d.avots)}${d.rezgis_24h?.sunas.length ? Valoda.t('; pelēki apļi — 24 h, {a} (kavējas ~2–3 h)', { a: avots(d.rezgis_avots) }) : ''}.</small>`;
    teksts.hidden = false;
  }

  async function ieladet() {
    try {
      const r = await fetch('/api/zibens');
      if (!r.ok) throw new Error(r.status);
      zimet(await r.json());
    } catch (e) {
      teksts.textContent = Valoda.t('Zibens datus neizdevās ielādēt. Mēģiniet vēlreiz pēc brīža.');
      teksts.hidden = false;
    }
  }

  function radit(ieslegt) {
    el('zibens-slanis').checked = ieslegt;
    clearInterval(taimeris);
    if (ieslegt) {
      slanis.addTo(karte);
      ieladet();
      taimeris = setInterval(ieladet, 60 * 1000);
    } else {
      slanis.remove();
      teksts.hidden = true;
    }
  }

  el('zibens-slanis').addEventListener('change', e => radit(e.target.checked));
  return { radit };
})();
