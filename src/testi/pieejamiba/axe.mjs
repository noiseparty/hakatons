// Pieejamība: axe-core (WCAG 2.1 A/AA + best-practice) 375x740 un 1280x800 — notes/pieejamiba.md.
// Mapē ārpus repozitorija: npm i playwright @axe-core/playwright; npx playwright install chromium; nokopēt šo failu;
// uv run --no-project --python 3.12 src/demo/lokali.py --port 8761 ; node axe.mjs 8761 rezultats.json
import { chromium } from 'playwright';
import AxeBuilder from '@axe-core/playwright';
import fs from 'node:fs';
import crypto from 'node:crypto';

const PORT = process.argv[2] || '8097';
const OUT = process.argv[3] || 'rezultats.json';
const BASE = `http://127.0.0.1:${PORT}`;
const KESA = process.env.KESA || 'kesa';  // /api atbildes: pirmajā reizē no map.repo.lv (caur lokali.py), pēc tam no diska
fs.mkdirSync(KESA, { recursive: true });

async function marsruti(ctx) {
  await ctx.route(u => !u.href.startsWith('http://127.0.0.1'), r => r.abort());
  await ctx.route(u => u.href.startsWith('http://127.0.0.1') && u.pathname.startsWith('/api/'), async r => {
    const req = r.request();
    if (req.method() !== 'GET') return r.fulfill({ status: 204, body: '' });
    const h = crypto.createHash('sha1').update(req.url().replace(/^https?:\/\/[^/]+/, '')).digest('hex');
    const f = `${KESA}/${h}.json`;
    if (fs.existsSync(f)) {
      const c = JSON.parse(fs.readFileSync(f, 'utf8'));
      return r.fulfill({ status: c.status, contentType: c.tips, body: Buffer.from(c.body, 'base64') });
    }
    let resp; try { resp = await r.fetch({ timeout: 60000 }); } catch { return r.fulfill({ status: 502, body: '{}' }); }
    const body = await resp.body();
    fs.writeFileSync(f, JSON.stringify({ status: resp.status(), tips: resp.headers()['content-type'] || 'application/json', body: body.toString('base64') }));
    return r.fulfill({ status: resp.status(), contentType: resp.headers()['content-type'], body });
  });
}

const STAVOKLI = [
  ['index: tukšs', '/map', async () => {}],
  ['index: Ogre, plūdi', '/map', async p => {
    await p.fill('#jautajums', 'Ogre, plūdi');
    await p.press('#jautajums', 'Enter');
    await p.waitForSelector('#rezultati:not([hidden])');
    await p.waitForTimeout(4000);
  }],
  ['index: popup', '/map', async p => {
    await p.fill('#jautajums', 'Ogre, plūdi');
    await p.press('#jautajums', 'Enter');
    await p.waitForTimeout(4000);
    await p.evaluate(() => Saraksts.atvert());
    await p.waitForTimeout(300);
    const b = p.locator('#saraksts-dialogs [data-objekts]').first();
    if (await b.count()) await b.click(); else await p.keyboard.press('Escape');
    await p.waitForTimeout(800);
  }],
  ['index: Saraksts', '/map', async p => {
    await p.fill('#jautajums', 'Ogre, plūdi');
    await p.press('#jautajums', 'Enter');
    await p.waitForTimeout(4000);
    await p.evaluate(() => Saraksts.atvert());
    await p.waitForTimeout(300);
  }],
  ['index: Datu avoti', '/map', async p => {
    await p.evaluate(() => { if (typeof Lapa !== 'undefined' && Lapa && innerWidth <= 800) { Lapa.cilne('slani'); Apaksa.atvert('pilna'); } document.getElementById('avoti').open = true; });
    await p.waitForTimeout(800);
  }],
  ['index: Ziņot 1. solis', '/map', async p => {
    await p.evaluate(() => document.getElementById('zinot-poga').click());
    await p.waitForTimeout(500);
  }],
  ['info.html', '/info.html', async () => {}],
  ['statuss.html', '/statuss.html', async () => { }],
  ['trukstosie.html', '/trukstosie.html', async () => {}],
  ['slaidi.html', '/slaidi.html', async () => {}],
];

const browser = await chromium.launch();
const rez = {};
for (const [w, h] of [[375, 740], [1280, 800]]) {
  const ctx = await browser.newContext({ viewport: { width: w, height: h }, isMobile: w < 800, hasTouch: w < 800, deviceScaleFactor: 1 });
  await marsruti(ctx);
  for (const [nos, url, darbiba] of STAVOKLI) {
    const p = await ctx.newPage();
    const kludas = [];
    p.on('pageerror', e => kludas.push(String(e)));
    await p.goto(BASE + url, { waitUntil: 'load' });
    await p.waitForTimeout(2500);
    try { await darbiba(p); } catch (e) { kludas.push('darbība: ' + e.message); }
    const a = await new AxeBuilder({ page: p }).withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'best-practice']).analyze();
    const k = `${w} ${nos}`;
    rez[k] = { kludas, v: a.violations.map(v => ({ id: v.id, impact: v.impact, n: v.nodes.length, help: v.help, nodes: v.nodes.slice(0, 6).map(n => n.target.join(' ') + ' :: ' + (n.failureSummary || '').split('\n').slice(1, 2).join('')) })) };
    const sk = s => a.violations.filter(v => v.impact === s).reduce((x, v) => x + v.nodes.length, 0);
    console.log(`${k}: critical ${sk('critical')} serious ${sk('serious')} moderate ${sk('moderate')} minor ${sk('minor')}${kludas.length ? ' JS: ' + kludas.join(' | ') : ''}`);
    await p.close();
  }
  await ctx.close();
}
await browser.close();
fs.writeFileSync(OUT, JSON.stringify(rez, null, 1));
