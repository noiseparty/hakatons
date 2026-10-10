// Slānis "Laikapstākļi tagad" (/api/noverojumi): LVĢMC meteoroloģisko staciju jaunākie mērījumi (data.gov.lv, CC0).
// Stacijas krāsa pēc brāzmām: < 10 m/s pelēka, 10–15 dzeltena, 15–20 oranža, ≥ 20 sarkana; vecāks par 3 h — pelēks
// "novecojis". Ieslēdzot atjauno ik 10 min. Izmanto app.js globālos (karte, el).
const Noverojumi = (() => {
  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const sk = x => x == null ? '–' : String(Math.abs(x) >= 10 ? Math.round(x) : x.toFixed(1)).replace('.', ',');
  const VIRZIENI = ['Z', 'ZA', 'A', 'DA', 'D', 'DR', 'R', 'ZR'];
  const virziens = g => g == null ? '' : Valoda.t(VIRZIENI[Math.round(g / 45) % 8]);
  const laiks = iso => new Date(iso).toLocaleString('lv-LV', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' });
  const krasa = s => s.vecs || s.brazmas == null ? '#a8a29e' : s.brazmas >= 20 ? '#dc2626' : s.brazmas >= 15 ? '#f97316' : s.brazmas >= 10 ? '#facc15' : '#d6d3d1';
  const slanis = L.layerGroup();
  const teksts = el('noverojumi-teksts');
  let taimeris = null;

  function popups(s, avots) {
    return `<div class="popup"><b>${esc(s.nosaukums)}</b><small>${Valoda.t('LVĢMC meteoroloģiskā stacija')}</small><br>` +
      (s.vecs ? `<small class="kluda">${Valoda.t('Mērījums novecojis (vecāks par 3 h)')}</small><br>` : '') +
      (s.brazmas != null ? `${Valoda.t('Brāzmas')}: <b>${sk(s.brazmas)} m/s</b><br>` : '') +
      (s.vejs != null ? `${Valoda.t('Vējš')}: ${sk(s.vejs)} m/s ${virziens(s.virziens)}<br>` : '') +
      (s.temp != null ? `${Valoda.t('Temperatūra')}: ${sk(s.temp)} °C<br>` : '') +
      (s.nokrisni_1h != null ? `${Valoda.t('Nokrišņi stundā')}: ${sk(s.nokrisni_1h)} mm<br>` : '') +
      `<small>${Valoda.t('Mērīts')} ${esc(laiks(s.laiks))}</small>` +
      `<small class="popup-avots">${Valoda.t('Avots')}: <a href="${esc(avots.url)}" target="_blank" rel="noopener">LVĢMC</a>, ${esc(avots.licence)}</small></div>`;
  }

  function zimet(d) {
    slanis.clearLayers();
    for (const s of d.stacijas) {
      // marķierī viena zīme aiz komata (14,8 ir dzeltens, 15,2 — oranžs); stacijas bez vēja mērījuma — mazs punkts
      const vertiba = s.brazmas != null ? s.brazmas.toFixed(1).replace('.', ',') : '';
      const izm = s.brazmas != null ? 36 : 14;
      L.marker([s.lat, s.lon], {
        icon: L.divIcon({ className: 'noverojums-ikona', iconSize: [izm, izm], iconAnchor: [izm / 2, izm / 2],
          html: `<span style="background:${krasa(s)}" class="${s.vecs ? 'vecs' : ''}">${vertiba}</span>` }),
        title: s.brazmas != null ? Valoda.t('{s}: brāzmas {v} m/s', { s: s.nosaukums, v: vertiba }) : Valoda.t('{s}: nokrišņu stacija', { s: s.nosaukums }),
      }).bindPopup(popups(s, d.avots)).addTo(slanis);
    }
    const m = d.maks_brazmas;
    teksts.innerHTML = (m ? Valoda.t('Stiprākās brāzmas: {v} m/s ({n}, {t}).', { v: sk(m.brazmas), n: esc(m.nosaukums), t: esc(laiks(m.laiks)) }) : Valoda.t('Svaigu mērījumu nav.')) +
      `<br><small>${Valoda.t('Skaitlis — brāzmas m/s.')} ${Valoda.t('Avots')}: <a href="${esc(d.avots.url)}" target="_blank" rel="noopener">LVĢMC novērojumi</a>, ${esc(d.avots.licence)}.</small>`;
    teksts.hidden = false;
  }

  async function ieladet() {
    try {
      const r = await fetch('/api/noverojumi');
      if (!r.ok) throw new Error(r.status);
      zimet(await r.json());
    } catch {
      teksts.textContent = Valoda.t('Novērojumus neizdevās ielādēt. Mēģiniet vēlreiz pēc brīža.');
      teksts.hidden = false;
    }
  }

  function radit(ieslegt) {
    el('noverojumi-slanis').checked = ieslegt;
    clearInterval(taimeris);
    if (ieslegt) { slanis.addTo(karte); ieladet(); taimeris = setInterval(ieladet, 10 * 60 * 1000); }
    else { slanis.remove(); teksts.hidden = true; }
  }

  el('noverojumi-slanis').addEventListener('change', e => radit(e.target.checked));
  return { radit, virziens, sk, laiks };
})();
