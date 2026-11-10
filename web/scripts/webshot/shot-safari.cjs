const puppeteer = require('puppeteer-core');
// usage: node shot-safari.cjs <height> <topInset> <bottomInset> <out.png>
const [h, top, bottom, out] = process.argv.slice(2);
setTimeout(() => { console.error('timeout'); process.exit(2); }, 90000);
(async () => {
  const browser = await puppeteer.launch({ executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless: 'shell', args: ['--no-sandbox'] });
  const page = await browser.newPage();
  await page.setViewport({ width: 402, height: Number(h), deviceScaleFactor: 2, isMobile: true, hasTouch: true });
  const cdp = await page.createCDPSession();
  await cdp.send('Emulation.setSafeAreaInsetsOverride', { insets: { top: Number(top), bottom: Number(bottom), left: 0, right: 0 } }).catch(e => console.log('no inset override:', e.message));
  await page.goto('http://127.0.0.1:5173/', { waitUntil: 'networkidle0' });
  await page.waitForSelector('.steps');
  if (process.env.EXTRA_CSS) await page.addStyleTag({ content: process.env.EXTRA_CSS });
  await new Promise(r => setTimeout(r, 600));
  const m = await page.evaluate(() => {
    const se = document.scrollingElement; const r = (s) => { const e = document.querySelector(s); if (!e) return null; const b = e.getBoundingClientRect(); return [Math.round(b.top), Math.round(b.bottom)]; };
    return { innerHeight, scrollHeight: se.scrollHeight, overflow: se.scrollHeight - innerHeight, header: r('.header'), steps: r('.steps'), actions: r('.start .sticky-actions'), start: r('.start .btn-primary'), below: document.documentElement.hasAttribute('data-below') };
  });
  console.log(h, top, bottom, JSON.stringify(m));
  await page.screenshot({ path: out });
  await browser.close();
})();
