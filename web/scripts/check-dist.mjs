// After `npm run build`: (1) gzip size budget for dist/; (2) no external URLs in the built code except the Knesset site
// (bill links) — a guard against an accidental third-party request or tracker; (3) what search engines and link previews
// need is in place (vite.config.ts siteHead): the files at the root, the head tags of every page, and — when SITE_URL is
// set, as on the hosting — the canonical address and the preview picture with absolute addresses. Fails with exit code 1.
import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join } from 'node:path';
import { gzipSync } from 'node:zlib';

const BUDGET_KB = 360; // all JS + CSS + fonts (woff2), gzip; data files (*.json, fetched at run time) are not counted —
// the texts of the site (export/quiz_texts.json) are in the JS bundle and are counted;
// 152 KB on 2026-10-18 after the data left the bundle (was 340 KB with it)
const ALLOWED_HOSTS = ['main.knesset.gov.il', 'www.w3.org', 'react.dev', 'reactjs.org', 'www.sitemaps.org', 'schema.org', 'www.linkedin.com', 'linkedin.com'];
const SITE_URL = (process.env.SITE_URL ?? '').replace(/\/+$/, '');
if (SITE_URL) ALLOWED_HOSTS.push(new URL(SITE_URL).hostname);
const ROOT_FILES = ['favicon.ico', 'favicon.svg', 'apple-touch-icon.png', 'icon-192.png', 'icon-512.png', 'og-image.png',
  'manifest.webmanifest', 'robots.txt', 'sitemap.xml', '_headers'];
const HEAD_TAGS = ['<meta name="description"', '<link rel="icon"', '<link rel="apple-touch-icon"', '<link rel="manifest"',
  '<meta property="og:title"', '<meta name="twitter:card"'];
const HEAD_TAGS_DEPLOY = ['<link rel="canonical"', '<meta property="og:url"', '<meta property="og:image"'];
// Each page holds its screen as HTML (prerenderPages in vite.config.ts): a mark of the screen's markup.
const PRERENDERED = { 'index.html': 'class="screen start"', 'how-it-works.html': 'class="method-title"' };

const dist = new URL('../dist/', import.meta.url).pathname;
const files = [];
const walk = (d) => readdirSync(d).forEach((f) => (statSync(join(d, f)).isDirectory() ? walk(join(d, f)) : files.push(join(d, f))));
walk(dist);

let total = 0;
const bad = new Set();
for (const f of files) {
  if (!/\.(js|css|html|woff2)$/.test(f)) continue;
  const buf = readFileSync(f);
  const gz = f.endsWith('.woff2') ? buf.length : gzipSync(buf).length;
  total += gz;
  console.log(`${(gz / 1024).toFixed(1).padStart(7)} KB  ${f.slice(dist.length)}`);
  if (f.endsWith('.woff2')) continue;
  for (const m of buf.toString('utf8').matchAll(/https?:\/\/([a-z0-9.-]+)/gi)) {
    if (!ALLOWED_HOSTS.includes(m[1].toLowerCase())) bad.add(m[1]);
  }
}
console.log(`${(total / 1024).toFixed(1).padStart(7)} KB  total (budget ${BUDGET_KB} KB)`);
let ok = true;
for (const f of ROOT_FILES) {
  if (!files.includes(join(dist, f))) { console.error(`Missing in dist/: ${f}`); ok = false; }
}
for (const f of files.filter((f) => f.endsWith('.html'))) {
  const html = readFileSync(f, 'utf8');
  const need = SITE_URL ? [...HEAD_TAGS, ...HEAD_TAGS_DEPLOY] : HEAD_TAGS;
  for (const tag of need) {
    if (!html.includes(tag)) { console.error(`${f.slice(dist.length)}: no ${tag}`); ok = false; }
  }
  const mark = PRERENDERED[f.slice(dist.length)];
  if (!mark) { console.error(`${f.slice(dist.length)}: unknown page`); ok = false; }
  else if (!html.includes(mark)) { console.error(`${f.slice(dist.length)}: not prerendered (no ${mark})`); ok = false; }
  for (const m of html.matchAll(/(?:src|href)="\/(assets\/[^"]+)"/g)) {
    if (!files.includes(join(dist, m[1]))) { console.error(`${f.slice(dist.length)}: ${m[1]} is not in dist/`); ok = false; }
  }
  if (SITE_URL && !html.includes(`<meta property="og:image" content="${SITE_URL}/og-image.png">`)) {
    console.error(`${f.slice(dist.length)}: og:image is not ${SITE_URL}/og-image.png`); ok = false;
  }
}
if (!SITE_URL) console.log('SITE_URL not set: canonical, og:url and og:image not checked (a deploy sets it)');
if (total > BUDGET_KB * 1024) { console.error(`Over budget: ${(total / 1024).toFixed(1)} KB > ${BUDGET_KB} KB`); ok = false; }
if (bad.size) { console.error(`External hosts in dist/: ${[...bad].join(', ')}`); ok = false; }
process.exit(ok ? 0 : 1);
