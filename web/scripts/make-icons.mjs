// Generates the site's icons and the link-preview picture into public/ (committed: the hosting build has no browser).
// `node scripts/make-icons.mjs` — needs Google Chrome (headless, for the PNGs); run again after changing the hero picture
// (src/assets/figma/hero.svg), the site name or the subtitle (export/quiz_texts.json `app`), or the brand colours.
//
//   favicon.svg          the tab icon: two half-rings, light outside, the brand inside, on a white tile (25 % corners)
//   favicon.ico          the same at 32 and 16 px for browsers that take no SVG
//   apple-touch-icon.png 180 px, the full hero arc on white, for «Add to Home Screen» on iPhone
//   icon-192.png, icon-512.png   the same, for the web app manifest (Android home screen, install prompt)
//   og-image.png         1200×630, the link preview in messengers and social networks: name, subtitle, the hero arc
import { execFileSync } from 'node:child_process';
import { existsSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = fileURLToPath(new URL('..', import.meta.url));
const out = join(root, 'public');
const texts = JSON.parse(readFileSync(join(root, '../export/quiz_texts.json'), 'utf8'));
const hero = readFileSync(join(root, 'src/assets/figma/hero.svg'), 'utf8')
  .replace(/ style="[^"]*"/, '').replace(/ preserveAspectRatio="none"/, '');

const BRAND = '#0038B8';
const CHROME = ['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', 'google-chrome', 'chromium'].find((c) =>
  c.startsWith('/') ? existsSync(c) : true);

// ---- favicon.svg: two half-rings on a white tile with the corners of the tab icons around it (25 %): the outer one light
// (the brand at 55 %), the inner one the brand (customer 2026-10-25, picked from mockups). Their ends on a whole pixel
// at 16 px (y 40 of 64); the light ring 1/16 px longer (y 40.25): a light shape next to a dark one looks shorter.
function faviconSvg() {
  const ring = (R, r, end, opacity) =>
    `<path d="M${32 - R} ${end} L${32 - R} 40 A${R} ${R} 0 0 1 ${32 + R} 40 L${32 + R} ${end} L${32 + r} ${end} L${32 + r} 40 ` +
    `A${r} ${r} 0 0 0 ${32 - r} 40 L${32 - r} ${end} Z" fill="${BRAND}"${opacity < 1 ? ` fill-opacity="${opacity}"` : ''}/>`;
  const tile = '<rect width="64" height="64" rx="16" fill="#fff"/>';
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">${tile}${ring(25, 17, 40.25, 0.55)}${ring(13, 6, 40, 1)}</svg>\n`;
}

// ---- PNGs: an HTML page per picture, screenshot by headless Chrome at the picture's size.
const font = (file) => `url(data:font/woff2;base64,${readFileSync(file).toString('base64')}) format('woff2')`;
const fraunces = font(join(root, 'src/assets/fonts/fraunces-opsz.woff2'));
const jakarta = font(join(root, 'node_modules/@fontsource/plus-jakarta-sans/files/plus-jakarta-sans-latin-500-normal.woff2'));

const page = (w, h, body, css = '') => `<!doctype html><html><head><meta charset="utf-8"><style>
@font-face { font-family: Fraunces; src: ${fraunces}; }
@font-face { font-family: 'Plus Jakarta Sans'; font-weight: 500; src: ${jakarta}; }
html, body { margin: 0; width: ${w}px; height: ${h}px; background: #fff; overflow: hidden; }
body { display: flex; align-items: center; justify-content: center; -webkit-font-smoothing: antialiased; }
svg { display: block; }
${css}</style></head><body>${body}</body></html>`;

// The hero picture at the icon's size, moved up so the arc (rows at y 72…125 of 150) sits in the middle of the icon.
const iconPage = (size) => page(size, size,
  `<div style="transform:translateY(${-size * 0.12}px)">${hero.replace(/width="150" height="150"/, `width="${size}" height="${size}"`)}</div>`);

const ogPage = () => page(1200, 630, `
  <div class="card">
    <div class="text">
      <p class="eyebrow">${texts.app.eyebrow}</p>
      <h1>${texts.app.siteName}</h1>
      <p class="sub">${texts.app.subtitle}</p>
    </div>
    ${hero.replace(/width="150" height="150"/, 'width="420" height="420"')}
  </div>`, `
  .card { width: 1200px; height: 630px; display: flex; align-items: center; justify-content: space-between; padding: 0 96px; box-sizing: border-box; background: #fff; }
  .text { display: flex; flex-direction: column; gap: 24px; }
  .eyebrow { margin: 0; font: 500 26px/1.2 'Plus Jakarta Sans'; letter-spacing: 0.06em; text-transform: uppercase; color: ${BRAND}; }
  h1 { margin: 0; font: 400 88px/1.08 Fraunces; color: #000; max-width: 620px; }
  .sub { margin: 0; font: 500 36px/1.3 'Plus Jakarta Sans'; color: #595E6B; }`);

function shoot(html, w, h, file, transparent = false) {
  const dir = mkdtempSync(join(tmpdir(), 'icons-'));
  const src = join(dir, 'page.html');
  writeFileSync(src, html);
  // its own profile: with the default one it waits for the user's running Chrome and never returns
  execFileSync(CHROME, ['--headless=new', '--disable-gpu', '--hide-scrollbars', `--user-data-dir=${join(dir, 'profile')}`,
    '--force-device-scale-factor=1', ...(transparent ? ['--default-background-color=00000000'] : []),
    `--window-size=${w},${h}`, `--screenshot=${file}`, `file://${src}`], { stdio: 'ignore' });
  rmSync(dir, { recursive: true });
}

// ICO: a container of PNG entries (every browser that takes .ico takes PNG inside it).
function ico(pngs) {
  const header = Buffer.alloc(6);
  header.writeUInt16LE(0, 0); header.writeUInt16LE(1, 2); header.writeUInt16LE(pngs.length, 4);
  let offset = 6 + 16 * pngs.length;
  const entries = [], blobs = [];
  for (const { size, data } of pngs) {
    const e = Buffer.alloc(16);
    e.writeUInt8(size === 256 ? 0 : size, 0); e.writeUInt8(size === 256 ? 0 : size, 1);
    e.writeUInt16LE(1, 4); e.writeUInt16LE(32, 6); e.writeUInt32LE(data.length, 8); e.writeUInt32LE(offset, 12);
    entries.push(e); blobs.push(data); offset += data.length;
  }
  return Buffer.concat([header, ...entries, ...blobs]);
}

writeFileSync(join(out, 'favicon.svg'), faviconSvg());
for (const [name, size] of [['apple-touch-icon.png', 180], ['icon-192.png', 192], ['icon-512.png', 512]]) {
  shoot(iconPage(size), size, size, join(out, name));
}
const dir = mkdtempSync(join(tmpdir(), 'ico-'));
const pngs = [32, 16].map((size) => {
  const file = join(dir, `${size}.png`);
  // transparent around the tile's rounded corners, as favicon.svg (a white square showed on a dark tab strip)
  shoot(page(size, size, faviconSvg().replace('<svg ', `<svg width="${size}" height="${size}" `),
    'html, body { background: transparent; }'), size, size, file, true);
  return { size, data: readFileSync(file) };
});
rmSync(dir, { recursive: true });
writeFileSync(join(out, 'favicon.ico'), ico(pngs));
shoot(ogPage(), 1200, 630, join(out, 'og-image.png'));
console.log('wrote favicon.svg, favicon.ico, apple-touch-icon.png, icon-192.png, icon-512.png, og-image.png to public/');
