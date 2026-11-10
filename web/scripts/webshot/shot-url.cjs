const puppeteer = require('puppeteer-core');
// usage: node shot-url.cjs <url> <out.png> [scrollToEnd]
const [url, out, toEnd] = process.argv.slice(2);
(async () => {
  const browser = await puppeteer.launch({ executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless: 'shell', args: ['--no-sandbox'] });
  const page = await browser.newPage();
  await page.setViewport({ width: 402, height: 791, deviceScaleFactor: 2, isMobile: true, hasTouch: true });
  await page.emulateMediaFeatures([{ name: 'prefers-reduced-motion', value: 'reduce' }]);
  const cdp = await page.createCDPSession();
  await cdp.send('Emulation.setSafeAreaInsetsOverride', { insets: { top: 62, bottom: 0, left: 0, right: 0 } });
  setTimeout(() => { console.error('timeout'); process.exit(2); }, 60000);
  await page.goto(url, { waitUntil: 'load' });
  await page.waitForSelector('.method-foot, .steps', { timeout: 20000 });
  if (process.env.EXTRA_CSS) await page.addStyleTag({ content: process.env.EXTRA_CSS });
  await new Promise(r => setTimeout(r, 600));
  if (toEnd) { await page.evaluate(() => window.scrollTo(0, document.scrollingElement.scrollHeight)); await new Promise(r => setTimeout(r, 400)); }
  const m = await page.evaluate(() => { const els = [...document.querySelectorAll('footer, .footer, .colophon, .made, .data-line, .meta')]; return els.map(e => { const r = e.getBoundingClientRect(); return { cls: e.className, left: r.left, right: r.right, top: r.top, bottom: r.bottom, text: e.textContent.trim().slice(0, 80) }; }); });
  console.log(JSON.stringify(m));
  await page.screenshot({ path: out });
  await browser.close();
})();
