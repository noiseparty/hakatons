// Maršruts kartē, kas apiet slēgtās zonas (/api/marsruts: FOSSGIS OSRM, OpenStreetMap ODbL). Meklēšanas rezultātā —
// līdz tuvākajai patvertnei / 24/7 slimnīcai; demo — līdz vietai ārpus slēgtās zonas. Ja maršrutētājs neatbild, paliek
// līdzšinējās saites uz kartes lietotnēm (marsrutaSaites app.js). Lieto app.js globālos (karte, iegut).
const Marsruts = (() => {
  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const km = m => m >= 1000 ? (m / 1000).toFixed(1).replace('.', ',') + ' km' : Math.round(m / 10) * 10 + ' m';
  const min = s => s >= 3600 ? `${Math.floor(s / 3600)} h ${Math.round(s % 3600 / 60)} min` : Math.max(1, Math.round(s / 60)) + ' min';

  // Demo zonas → ?izvairities: aplis "c:lat,lon,r", poligons "lat,lon;lat,lon;…"
  function zonuTeksts(zonas) {
    return (zonas || []).map(z => z.tips === 'aplis' ? `c:${z.centrs[0]},${z.centrs[1]},${z.radiuss_m}`
      : Array.isArray(z.punkti) ? z.punkti.map(p => p.join(',')).join(';') : null).filter(Boolean).join('|');
  }

  async function iegutMarsrutu(no, uz, zonas, signal) {
    const q = { no: `${(+no[0]).toFixed(5)},${(+no[1]).toFixed(5)}`, uz: `${(+uz[0]).toFixed(5)},${(+uz[1]).toFixed(5)}` };
    const z = zonuTeksts(zonas);
    if (z) q.izvairities = z;
    return iegut('/marsruts?' + new URLSearchParams(q), signal);
  }

  function teksts(d) {
    if (!d.dross) return `<b class="marsruts-bistams">${Ik('uzmanibu')} ${esc(d.piezime)}</b>`;
    const t = typeof Valoda !== 'undefined' ? Valoda.t : k => k;
    return `<b>${t('Maršruts')} (${km(d.attalums_m)}, ${min(d.ilgums_s)} ${t(d.veids === 'auto' ? 'ar auto' : 'kājām')}` +
      `${d.apiet_zonu ? ', apiet slēgto zonu' : d.no_zonas ? ', ved ārā no slēgtās zonas' : ''})</b> — zilā līnija kartē`;
  }
  const avots = d => `<small class="avots-rinda">Maršruts: <a href="${esc(d.avots.url)}" target="_blank" rel="noopener">OSRM (FOSSGIS)</a>, OpenStreetMap (${esc(d.avots.licence)})</small>`;

  function zimet(d, slanis) {
    const ll = d.koord.map(([a, b]) => [a, b]);
    const grupa = L.layerGroup();
    if (d.dross) {
      L.polyline(ll, { color: '#ffffff', weight: 9, opacity: 0.9, interactive: false }).addTo(grupa);
      L.polyline(ll, { color: '#0059a6', weight: 5, opacity: 0.95 }).bindTooltip(teksts(d).replace(/<[^>]+>/g, ''), { sticky: true }).addTo(grupa);
    } else {
      L.polyline(ll, { color: '#b91c1c', weight: 4, dashArray: '6 8' }).addTo(grupa);
    }
    grupa.addTo(slanis);
    return grupa;
  }

  // li: rezultāta rinda (data-lat/lon); aizstat: taisnā līnija, ko noņem, ja maršruts ir
  async function rindai(li, no, uz, { zonas = [], slanis, aizstat = null, signal } = {}) {
    if (!li) return null;
    const vieta = document.createElement('small');
    vieta.className = 'marsruta-rinda';
    vieta.textContent = 'Meklē maršrutu…';
    const piezime = li.querySelector('.marsruta-piezime');
    if (piezime) piezime.replaceWith(vieta); else li.querySelector('.teksts')?.append(vieta);
    try {
      const d = await iegutMarsrutu(no, uz, zonas, signal);
      if (aizstat && d.dross) slanis.removeLayer(aizstat);
      zimet(d, slanis);
      vieta.innerHTML = teksts(d) + avots(d);
      return d;
    } catch (e) {
      if (e.name === 'AbortError') return null;
      vieta.remove();  // maršrutētājs nav pieejams: paliek saites uz kartes lietotnēm
      if (piezime && aizstat) li.querySelector('.teksts')?.append(piezime);
      return null;
    }
  }

  return { rindai, zonuTeksts };
})();
