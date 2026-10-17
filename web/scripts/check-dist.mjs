// After `npm run build`: (1) gzip size budget for dist/; (2) no external URLs in the built code except the Knesset site
// (bill links) — a guard against an accidental third-party request or tracker. Fails with exit code 1.
import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join } from 'node:path';
import { gzipSync } from 'node:zlib';

const BUDGET_KB = 360; // all JS + CSS + fonts (woff2), gzip; 323 KB on 2026-10-17 (data ≈ 190 KB of it), ~10 % headroom
const ALLOWED_HOSTS = ['main.knesset.gov.il', 'www.w3.org', 'react.dev', 'reactjs.org'];

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
if (total > BUDGET_KB * 1024) { console.error(`Over budget: ${(total / 1024).toFixed(1)} KB > ${BUDGET_KB} KB`); ok = false; }
if (bad.size) { console.error(`External hosts in dist/: ${[...bad].join(', ')}`); ok = false; }
process.exit(ok ? 0 : 1);
