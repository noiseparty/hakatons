// Balss ievade meklētājā: poga "Runāt" (SpeechRecognition / webkitSpeechRecognition), valoda lv-LV; ilgi turot vai
// ar labo klikšķi — izvēlne krievu / angļu valodai (atceras pārlūkā). Rezultāts nonāk laukā, un meklēšana sākas.
// Poga paslēpta, ja pārlūks to neprot vai servera Permissions-Policy aizliedz mikrofonu.
// Privātums: runu atpazīst pārlūka pakalpojums (Chrome — Google, Safari — Apple); audio tiek nosūtīts tam.
const Runa = (() => {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  const politika = document.permissionsPolicy || document.featurePolicy;
  const atlauts = !politika?.allowsFeature || politika.allowsFeature('microphone');
  const poga = document.getElementById('runat');
  const izvelne = document.getElementById('runa-valodas');
  if (!SR || !atlauts || !poga) return { pieejama: false };

  const VALODAS = { 'lv-LV': 'Latviski', 'ru-RU': 'По-русски', 'en-US': 'English' };
  let valoda = localStorage.getItem('runa-valoda') || 'lv-LV';
  if (!VALODAS[valoda]) valoda = 'lv-LV';
  let atpazinejs = null, ilgiTur = null, izvelneAtverta = false;
  const lauks = document.getElementById('jautajums');
  const vietturis = lauks.placeholder;

  function zinot(teksts) {
    const s = document.getElementById('statuss');
    if (s) s.textContent = teksts;
  }

  function beigt() {
    poga.classList.remove('klausas');
    poga.setAttribute('aria-pressed', 'false');
    lauks.placeholder = vietturis;
    atpazinejs = null;
  }

  function sakt() {
    if (atpazinejs) { atpazinejs.stop(); return; }
    atpazinejs = new SR();
    atpazinejs.lang = valoda;
    atpazinejs.interimResults = true;
    atpazinejs.maxAlternatives = 1;
    atpazinejs.onresult = e => {
      const teksts = [...e.results].map(r => r[0].transcript).join(' ').trim();
      lauks.value = teksts;
      if (e.results[e.results.length - 1].isFinal && teksts) {
        atpazinejs.stop();
        document.getElementById('meklet-forma').requestSubmit();
      }
    };
    atpazinejs.onerror = e => {
      zinot(e.error === 'not-allowed' || e.error === 'service-not-allowed'
        ? 'Mikrofons nav atļauts. Ierakstiet tekstu meklētājā.'
        : e.error === 'no-speech' ? 'Nedzirdējām runu. Mēģiniet vēlreiz vai ierakstiet tekstu.'
        : 'Runas atpazīšana pašlaik nav pieejama. Ierakstiet tekstu meklētājā.');
    };
    atpazinejs.onend = beigt;
    try {
      atpazinejs.start();
      poga.classList.add('klausas');
      poga.setAttribute('aria-pressed', 'true');
      lauks.value = '';
      lauks.placeholder = 'Klausos… (' + VALODAS[valoda] + ')';
    } catch {
      beigt();
    }
  }

  function raditIzvelni(atvert) {
    izvelneAtverta = atvert;
    izvelne.hidden = !atvert;
    poga.setAttribute('aria-expanded', atvert);
    if (atvert) {
      izvelne.innerHTML = Object.entries(VALODAS).map(([k, v]) =>
        `<button type="button" role="menuitemradio" aria-checked="${k === valoda}" data-valoda="${k}">${v}</button>`).join('') +
        '<p>Runu atpazīst pārlūka pakalpojums (piem., Google); ieraksts tiek nosūtīts tam.</p>';
      izvelne.querySelector('[aria-checked="true"]')?.focus();
    }
  }

  // Pieskāriens — klausīties; ilgi turot (0,5 s) vai labā poga — valodas izvēlne
  poga.addEventListener('pointerdown', () => { ilgiTur = setTimeout(() => { ilgiTur = 'izvelne'; raditIzvelni(true); }, 500); });
  poga.addEventListener('pointerup', () => { if (ilgiTur !== 'izvelne') clearTimeout(ilgiTur); });
  poga.addEventListener('pointerleave', () => { if (ilgiTur !== 'izvelne') clearTimeout(ilgiTur); });
  poga.addEventListener('contextmenu', e => { e.preventDefault(); clearTimeout(ilgiTur); ilgiTur = 'izvelne'; raditIzvelni(true); });
  poga.addEventListener('click', () => {
    if (ilgiTur === 'izvelne') { ilgiTur = null; return; }
    if (izvelneAtverta) raditIzvelni(false);
    sakt();
  });
  poga.addEventListener('keydown', e => { if (e.key === 'ArrowDown') { e.preventDefault(); raditIzvelni(true); } });
  izvelne.addEventListener('click', e => {
    const b = e.target.closest('[data-valoda]');
    if (!b) return;
    valoda = b.dataset.valoda;
    localStorage.setItem('runa-valoda', valoda);
    raditIzvelni(false);
    poga.title = 'Runāt (' + VALODAS[valoda] + '; ilgi turiet, lai mainītu valodu)';
    sakt();
  });
  izvelne.addEventListener('keydown', e => { if (e.key === 'Escape') { raditIzvelni(false); poga.focus(); } });
  document.addEventListener('pointerdown', e => { if (izvelneAtverta && !izvelne.contains(e.target) && e.target !== poga) raditIzvelni(false); });

  poga.title = 'Runāt (' + VALODAS[valoda] + '; ilgi turiet, lai mainītu valodu)';
  poga.hidden = false;
  document.getElementById('meklet-forma').classList.add('ar-runu');
  return { pieejama: true, sakt };
})();
