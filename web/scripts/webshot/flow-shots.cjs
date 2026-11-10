const puppeteer = require('puppeteer-core');
const out = process.argv[2];
const sleep = (ms) => new Promise(r => setTimeout(r, ms));
setTimeout(() => { console.error('timeout'); process.exit(2); }, 90000);
(async () => {
  const browser = await puppeteer.launch({ executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless: 'shell', args: ['--no-sandbox'] });
  const page = await browser.newPage();
  await page.setViewport({ width: 402, height: 791, deviceScaleFactor: 2, isMobile: true, hasTouch: true });
  await page.emulateMediaFeatures([{ name: 'prefers-reduced-motion', value: 'reduce' }]);
  const cdp = await page.createCDPSession();
  await cdp.send('Emulation.setSafeAreaInsetsOverride', { insets: { top: 62, bottom: 0, left: 0, right: 0 } });
  await page.goto('http://127.0.0.1:5173/', { waitUntil: 'networkidle0' });
  await page.waitForSelector('.steps'); await sleep(300);
  await page.screenshot({ path: `${out}/p-home.png` });
  await page.click('.start .btn-primary');
  await page.waitForSelector('.screen.question .answer'); await sleep(300);
  await page.click('.screen.question .answer'); await sleep(150);
  await page.screenshot({ path: `${out}/p-question.png` });
  let n = 0, kind = '';
  for (let i = 0; i < 40; i++) {
    if (await page.$('.screen.results')) { kind = 'results'; break; }
    if (await page.$('.choice')) { kind = 'tradeoff'; break; }
    const a = await page.$('.screen.question .answer');
    if (!a) break;
    const pressed = await page.$('.screen.question .answer[aria-pressed="true"]');
    if (!pressed) await a.click();
    await sleep(120);
    await page.click('.bottom-bar .btn-primary'); n++;
    await sleep(250);
  }
  console.log('after', n, 'questions:', kind);
  if (kind === 'tradeoff') {
    await page.click('.choice'); await sleep(150);
    await page.screenshot({ path: `${out}/p-tradeoff.png` });
    for (let i = 0; i < 40; i++) {
      if (await page.$('.screen.results')) break;
      if (await page.$('.choice')) { const p = await page.$('.choice[aria-pressed="true"]'); if (!p) await page.click('.choice'); }
      else if (await page.$('.screen.question .answer')) { const p = await page.$('.screen.question .answer[aria-pressed="true"]'); if (!p) await page.click('.screen.question .answer'); }
      else break;
      await sleep(120); await page.click('.bottom-bar .btn-primary'); await sleep(250);
    }
  }
  if (await page.$('.screen.results')) {
    await sleep(500);
    const sh = await page.evaluate(() => [document.scrollingElement.scrollHeight, innerHeight]); console.log('results page', JSON.stringify(sh));
    await page.screenshot({ path: `${out}/p-results-top.png` });
    await page.evaluate(() => window.scrollTo(0, document.scrollingElement.scrollHeight));
    await sleep(400);
    const m = await page.evaluate(() => { const b = document.querySelector('.results .sticky-actions'); const r = b && b.getBoundingClientRect(); return r ? [Math.round(r.top), Math.round(r.bottom), innerHeight] : null; });
    console.log('results actions', JSON.stringify(m));
    await page.screenshot({ path: `${out}/p-results.png` });
  } else console.log('no results screen reached');
  await browser.close();
})().catch(e => { console.error(e.message); process.exit(1); });
