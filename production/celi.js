// Ceļu slēgumi un negadījumi (LVC DATEX II caur NAP transportdata.gov.lv, CC0; /api/celi, kešs 5 min):
// slānis kartē (ieslēdz panelī "Slāņi") un rinda "Ceļu satiksme" meklēšanas rezultātā (meklesana.js).
// Lieto app.js globālos (karte, iegut, esc, attalums).
const Celi = (() => {
  const TIPI = {
    slegums: { ikona: 'slegts', krasa: '#b91c1c' },
    negadijums: { ikona: 'avarija', krasa: '#c2410c' },
    joslas_slegums: { ikona: 'uzmanibu', krasa: '#d97706' },
    remonts: { ikona: 'remonts', krasa: '#a16207' },
    slidens: { ikona: 'sniegs', krasa: '#0369a1' },
  };
  const AVOTS = () => Valoda.t('Avots') + ': <a href="https://transportdata.gov.lv/card/75611a36-e66b-40cf-af2c-69db48c278cf" target="_blank" rel="noopener">' +
    'VSIA „Latvijas Valsts ceļi”, transportdata.gov.lv</a> · CC0';
  const slanis = L.layerGroup();
  const ieslegt = document.getElementById('celu-slanis');
  const piezime = document.getElementById('celu-piezime');
  let taimeris = null;

  const laiks = iso => iso ? Valoda.fmtDatums(iso, true) : '';  // DD/MM/YYYY HH:MM visās valodās
  function speka(n) {
    if (!n.aktivs) return Valoda.t('Sāksies {t}', { t: laiks(n.no) }) + (n.lidz ? Valoda.t(', līdz {t}', { t: laiks(n.lidz) }) : '');
    return n.lidz ? Valoda.t('Spēkā līdz {t}', { t: laiks(n.lidz) }) : Valoda.t('Spēkā, beigu laiks nav zināms');
  }
  function popups(n) {
    return `<div class="popup"><b>${Ik(TIPI[n.tips].ikona)} ${esc(n.nosaukums)}${n.cels ? ' · ' + esc(n.cels) : ''}</b>` +
      (n.apraksts ? `<p>${esc(n.apraksts)}</p>` : '') +
      `<small>${esc(speka(n))}${n.no && n.aktivs ? ` (${Valoda.t('no {t}', { t: esc(laiks(n.no)) })})` : ''}</small>` +
      `<small class="popup-avots">${AVOTS()}</small></div>`;
  }

  async function ieladet() {
    let d;
    try { d = await iegut('/celi'); } catch { d = null; }
    if (!ieslegt.checked) return;
    slanis.clearLayers();
    if (!d) { piezime.textContent = Valoda.t('Ceļu datus neizdevās ielādēt. Mēģiniet vēlreiz pēc brīža.'); return; }
    if (!d.konfigurets) { piezime.textContent = Valoda.t('Ceļu dati pašlaik nav pieejami (avots vēl nav pieslēgts).'); return; }
    for (const n of d.notikumi) {
      const t = TIPI[n.tips];
      if (n.linija) L.polyline(n.linija, { color: t.krasa, weight: 5, opacity: n.aktivs ? .85 : .45, dashArray: n.aktivs ? null : '6 6' })
        .bindPopup(() => popups(n)).addTo(slanis);
      L.marker([n.lat, n.lon], { icon: L.divIcon({ className: 'celu-ikona', html: `<span style="background:${t.krasa}">${Ik(t.ikona)}</span>`, iconSize: [44, 44], iconAnchor: [22, 22] }),
        title: n.nosaukums, keyboard: true, opacity: n.aktivs ? 1 : .6 }).bindPopup(() => popups(n)).addTo(slanis);
    }
    const aktivi = d.notikumi.filter(n => n.aktivs).length;
    piezime.textContent = (d.notikumi.length ? Valoda.t('Šobrīd {a} spēkā, {p} plānoti.', { a: aktivi, p: d.notikumi.length - aktivi }) : Valoda.t('Šobrīd nav ceļu slēgumu vai negadījumu.')) +
      (d.nepieejami?.length ? ' ' + Valoda.t('Daļa datu pašlaik nav pieejama.') : '');
  }

  function radit(jaa) {
    ieslegt.checked = jaa;
    clearInterval(taimeris);
    if (jaa) { slanis.addTo(karte); piezime.textContent = Valoda.t('Ielādē…'); ieladet(); taimeris = setInterval(ieladet, 5 * 60000); }
    else { slanis.remove(); piezime.textContent = ''; }
  }
  ieslegt.addEventListener('change', e => radit(e.target.checked));

  // Meklēšanas rezultātam: tuvākais spēkā esošais slēgums / negadījums / slidens ceļš ~5 km rādiusā (viena rinda) vai ''.
  async function rinda(ll, signal) {
    const d = await iegut('/celi?' + new URLSearchParams({ ...ll, r: 5000 }), signal);
    const tuvi = (d.notikumi || []).filter(n => n.aktivs && n.tips !== 'remonts');
    if (!tuvi.length) return '';
    const n = tuvi[0];
    return `<p class="celi-rinda">${Ik(TIPI[n.tips].ikona)} <b>${Valoda.t('Ceļu satiksme')}:</b> ${esc(n.nosaukums)}${n.cels ? ' ' + esc(n.cels) : ''}` +
      ` (${attalums(n.attalums_m)})${n.apraksts ? ': ' + esc(n.apraksts) : ''}` +
      (tuvi.length > 1 ? ` <span class="piezime">${Valoda.t('Tuvumā vēl {n}.', { n: tuvi.length - 1 })}</span>` : '') +
      ` <small class="avots-rinda">${AVOTS()}</small></p>`;
  }

  return { radit, rinda, TIPI, popups };  // TIPI un popups lieto arī demo.js (vētras atkārtojums ar īstiem LVC notikumiem)
})();
