// Tikai tastatūra (notes/pieejamiba.md): Tab secība, izlaišanas saites, meklēšana → Saraksts → "Rādīt kartē" → logs → Escape,
// lapa "Pilns" kā dialogs, nav tel:, nav JS kļūdu. Palaišana kā axe.mjs: node tastatura.mjs 8761
import { chromium } from 'playwright';
import fs from 'node:fs';
import crypto from 'node:crypto';

const PORT = process.argv[2] || '8761';
const KESA = process.env.KESA || 'kesa';  // /api atbildes: pirmajā reizē no map.repo.lv (caur lokali.py), pēc tam no diska
fs.mkdirSync(KESA, { recursive: true });
const browser = await chromium.launch();
let kluda = 0;
const parbaude = (ok, t) => { console.log((ok ? 'OK   ' : 'KĻŪDA ') + t); if (!ok) kluda++; };

for (const [w, h] of [[375, 740], [1280, 800]]) {
  console.log(`\n=== ${w}x${h} ===`);
  const ctx = await browser.newContext({ viewport: { width: w, height: h }, isMobile: w < 800, hasTouch: w < 800, reducedMotion: 'reduce' });
  await ctx.route(u => !u.href.startsWith('http://127.0.0.1'), r => r.abort());
  await ctx.route(u => u.href.startsWith('http://127.0.0.1') && u.pathname.startsWith('/api/'), async r => {
    const req = r.request();
    if (req.method() !== 'GET') return r.fulfill({ status: 204, body: '' });
    const f = `${KESA}/${crypto.createHash('sha1').update(req.url().replace(/^https?:\/\/[^/]+/, '')).digest('hex')}.json`;
    if (fs.existsSync(f)) { const c = JSON.parse(fs.readFileSync(f, 'utf8')); return r.fulfill({ status: c.status, contentType: c.tips, body: Buffer.from(c.body, 'base64') }); }
    let resp; try { resp = await r.fetch({ timeout: 60000 }); } catch { return r.fulfill({ status: 502, body: '{}' }); }
    const body = await resp.body();
    fs.writeFileSync(f, JSON.stringify({ status: resp.status(), tips: resp.headers()['content-type'] || 'application/json', body: body.toString('base64') }));
    return r.fulfill({ status: resp.status(), contentType: resp.headers()['content-type'], body });
  });
  const p = await ctx.newPage();
  const jsKludas = [];
  p.on('pageerror', e => jsKludas.push(String(e)));
  await p.goto(`http://127.0.0.1:${PORT}/map`, { waitUntil: 'load' });
  await p.waitForTimeout(2500);
  const fokuss = () => p.evaluate(() => {
    const a = document.activeElement;
    if (!a || a === document.body) return 'body';
    const t = (a.getAttribute('aria-label') || a.textContent || a.value || '').replace(/\s+/g, ' ').trim().slice(0, 40);
    const kur = a.closest('#apaksa') ? 'lapa' : a.closest('header') ? 'galvene' : a.closest('#kartes-laukums') ? 'karte' : a.closest('#panelis') ? 'panelis' : a.closest('.dv-kreisa, .dv-kolonna, aside') ? 'kolonna' : '?';
    return `${kur}:${a.tagName.toLowerCase()}${a.id ? '#' + a.id : ''} "${t}"`;
  });
  const seciba = [];
  for (let i = 0; i < 14; i++) { await p.keyboard.press('Tab'); seciba.push(await fokuss()); }
  console.log('Tab secība:\n  ' + seciba.join('\n  '));
  const iMekl = seciba.findIndex(s => s.includes('#jautajums')), iKarte = seciba.findIndex(s => s.startsWith('karte:'));
  parbaude(seciba[0].includes('Uz meklēšanu'), 'pirmā Tab: izlaišanas saite "Uz meklēšanu"');
  parbaude(iMekl >= 0 && (iKarte < 0 || iMekl < iKarte), `meklēšana (${iMekl}) pirms kartes (${iKarte})`);
  const marķieri = await p.evaluate(() => document.querySelectorAll('.leaflet-marker-icon[tabindex="0"]').length);
  parbaude(marķieri === 0, `kartes punkti nav Tab mērķi (${marķieri})`);

  // Izlaišanas saite → meklēšana → Enter
  await p.focus('.izlaist a[data-uz="karte"]');
  await p.keyboard.press('Enter');
  parbaude(await p.evaluate(() => document.activeElement.id === 'karte'), '"Uz karti" → fokuss kartē');
  await p.focus('.izlaist a[data-uz="jautajums"]');
  await p.keyboard.press('Enter');
  parbaude((await fokuss()).includes('#jautajums'), '"Uz meklēšanu" → fokuss meklēšanas laukā');
  await p.keyboard.type('Ogre, plūdi');
  await p.keyboard.press('Enter');
  await p.waitForSelector('#rezultati:not([hidden]) [data-darbiba="saraksts"]', { timeout: 20000 }).catch(() => {});
  await p.waitForTimeout(3000);
  parbaude(await p.evaluate(() => document.getElementById('rezultati').getAttribute('aria-live') === 'polite'), 'rezultāts aria-live=polite');
  // Tab līdz "Saraksts" rezultāta kartītē
  let atrasts = false;
  for (let i = 0; i < 120 && !atrasts; i++) {
    await p.keyboard.press('Tab');
    atrasts = await p.evaluate(() => !!document.activeElement.closest('#rezultati [data-darbiba="saraksts"]'));
  }
  parbaude(atrasts, 'ar Tab sasniedzama poga "Saraksts" rezultāta kartītē');
  if (!atrasts) console.log(await p.evaluate(() => [...document.querySelectorAll('[data-darbiba="saraksts"]')].map(b => b.outerHTML.slice(0, 120) + ' visible=' + !!b.offsetWidth + ' in=' + (b.closest('[id]')?.id)).join(' || ')), await fokuss());
  if (atrasts) {
    await p.keyboard.press('Enter');
    await p.waitForTimeout(300);
    parbaude(await p.evaluate(() => !!document.querySelector('#saraksts-dialogs[open]')), 'Saraksts atvērts');
    let poga = false;
    for (let i = 0; i < 20 && !poga; i++) { await p.keyboard.press('Tab'); poga = await p.evaluate(() => document.activeElement.matches('[data-objekts]')); }
    parbaude(poga, 'Tab līdz "Rādīt kartē"');
    await p.keyboard.press('Enter');
    await p.waitForTimeout(800);
    parbaude(await p.evaluate(() => !!document.activeElement.closest('.leaflet-popup')), 'fokuss uznirstošajā logā: ' + await fokuss());
    await p.keyboard.press('Escape');
    await p.waitForTimeout(300);
    parbaude(await p.evaluate(() => !document.querySelector('.leaflet-popup')), 'Escape aizver logu');
    parbaude(await p.evaluate(() => document.activeElement.matches('[data-darbiba="saraksts"]')), 'fokuss atpakaļ uz "Saraksts": ' + await fokuss());
  }
  if (w < 800) {
    await p.evaluate(() => Apaksa.atvert('pilna'));
    await p.evaluate(() => document.getElementById('apaksa-rokturis').focus());
    parbaude(await p.evaluate(() => document.getElementById('apaksa').getAttribute('role') === 'dialog'), 'lapa "Pilns" = role=dialog');
    let ara = false;
    for (let i = 0; i < 150; i++) { await p.keyboard.press('Tab'); if (await p.evaluate(() => !document.activeElement.closest('#apaksa'))) { ara = true; break; } }
    parbaude(!ara, 'Tab paliek lapā "Pilns"');
    await p.keyboard.press('Escape');
    parbaude(await p.evaluate(() => Apaksa.stavoklis() === 'puse' && document.activeElement.id === 'apaksa-rokturis'), 'Escape → "Puse", fokuss rokturī');
  }
  const tel = await p.evaluate(() => document.querySelectorAll('a[href^="tel:"]').length);
  parbaude(tel === 0, `nav tel: saišu (${tel})`);
  parbaude(!jsKludas.length, 'nav JS kļūdu ' + jsKludas.join(' | '));
  await ctx.close();
}
await browser.close();
console.log(kluda ? `\n${kluda} kļūdas` : '\nviss OK');
process.exit(kluda ? 1 : 0);
