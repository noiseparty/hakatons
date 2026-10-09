// Ceļu slēgumi un negadījumi (LVC DATEX II caur NAP transportdata.gov.lv, CC0; /api/celi, kešs 5 min):
// slānis kartē (ieslēdz panelī "Slāņi") un rinda "Ceļu satiksme" meklēšanas rezultātā (meklesana.js).
// Lieto app.js globālos (karte, iegut, esc, attalums).
const Celi = (() => {
  const TIPI = {
    slegums: { ikona: '⛔', krasa: '#b91c1c' },
    negadijums: { ikona: '💥', krasa: '#c2410c' },
    joslas_slegums: { ikona: '⚠️', krasa: '#d97706' },
    remonts: { ikona: '🚧', krasa: '#a16207' },
    slidens: { ikona: '❄️', krasa: '#0369a1' },
  };
  const AVOTS = 'Avots: <a href="https://transportdata.gov.lv/card/75611a36-e66b-40cf-af2c-69db48c278cf" target="_blank" rel="noopener">' +
    'VSIA „Latvijas Valsts ceļi”, transportdata.gov.lv</a> · CC0';
  const slanis = L.layerGroup();
  const ieslegt = document.getElementById('celu-slanis');
  const piezime = document.getElementById('celu-piezime');
  let taimeris = null;

  const laiks = iso => iso ? new Date(iso).toLocaleString('lv-LV', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' }) : '';
  function speka(n) {
    if (!n.aktivs) return `Sāksies ${laiks(n.no)}` + (n.lidz ? `, līdz ${laiks(n.lidz)}` : '');
    return n.lidz ? `Spēkā līdz ${laiks(n.lidz)}` : 'Spēkā, beigu laiks nav zināms';
  }
  function popups(n) {
    return `<div class="popup"><b>${TIPI[n.tips].ikona} ${esc(n.nosaukums)}${n.cels ? ' · ' + esc(n.cels) : ''}</b>` +
      (n.apraksts ? `<p>${esc(n.apraksts)}</p>` : '') +
      `<small>${esc(speka(n))}${n.no && n.aktivs ? ` (no ${esc(laiks(n.no))})` : ''}</small>` +
      `<small class="popup-avots">${AVOTS}</small></div>`;
  }

  async function ieladet() {
    let d;
    try { d = await iegut('/celi'); } catch { d = null; }
    if (!ieslegt.checked) return;
    slanis.clearLayers();
    if (!d) { piezime.textContent = 'Ceļu datus neizdevās ielādēt. Mēģiniet vēlreiz pēc brīža.'; return; }
    if (!d.konfigurets) { piezime.textContent = 'Ceļu dati pašlaik nav pieejami (avots vēl nav pieslēgts).'; return; }
    for (const n of d.notikumi) {
      const t = TIPI[n.tips];
      if (n.linija) L.polyline(n.linija, { color: t.krasa, weight: 5, opacity: n.aktivs ? .85 : .45, dashArray: n.aktivs ? null : '6 6' })
        .bindPopup(() => popups(n)).addTo(slanis);
      L.marker([n.lat, n.lon], { icon: L.divIcon({ className: 'celu-ikona', html: `<span style="border-color:${t.krasa}">${t.ikona}</span>`, iconSize: [28, 28] }),
        title: n.nosaukums, keyboard: true, opacity: n.aktivs ? 1 : .6 }).bindPopup(() => popups(n)).addTo(slanis);
    }
    const aktivi = d.notikumi.filter(n => n.aktivs).length;
    piezime.textContent = (d.notikumi.length ? `Šobrīd ${aktivi} spēkā, ${d.notikumi.length - aktivi} plānoti.` : 'Šobrīd nav ceļu slēgumu vai negadījumu.') +
      (d.nepieejami?.length ? ' Daļa datu pašlaik nav pieejama.' : '');
  }

  function radit(jaa) {
    ieslegt.checked = jaa;
    clearInterval(taimeris);
    if (jaa) { slanis.addTo(karte); piezime.textContent = 'Ielādē…'; ieladet(); taimeris = setInterval(ieladet, 5 * 60000); }
    else { slanis.remove(); piezime.textContent = ''; }
  }
  ieslegt.addEventListener('change', e => radit(e.target.checked));

  // Meklēšanas rezultātam: tuvākais spēkā esošais slēgums / negadījums / slidens ceļš ~5 km rādiusā (viena rinda) vai ''.
  async function rinda(ll, signal) {
    const d = await iegut('/celi?' + new URLSearchParams({ ...ll, r: 5000 }), signal);
    const tuvi = (d.notikumi || []).filter(n => n.aktivs && n.tips !== 'remonts');
    if (!tuvi.length) return '';
    const n = tuvi[0];
    return `<p class="celi-rinda">${TIPI[n.tips].ikona} <b>Ceļu satiksme:</b> ${esc(n.nosaukums)}${n.cels ? ' ' + esc(n.cels) : ''}` +
      ` (${attalums(n.attalums_m)})${n.apraksts ? ': ' + esc(n.apraksts) : ''}` +
      (tuvi.length > 1 ? ` <span class="piezime">Tuvumā vēl ${tuvi.length - 1}.</span>` : '') +
      ` <small class="avots-rinda">${AVOTS}</small></p>`;
  }

  return { radit, rinda };
})();
