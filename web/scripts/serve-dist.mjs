// Phone preview (web/CLAUDE.md, DECISIONS G4): serves the production build in dist/ the way the host does — gzip, the
// headers of public/_headers (CSP, caching) and the SPA fallback to index.html. Pair it with `vite build --watch` and ngrok.
// Usage: node scripts/serve-dist.mjs [port]   (default 4173)
import { createReadStream, existsSync, readFileSync, statSync } from 'node:fs';
import { createServer } from 'node:http';
import { extname, join, normalize } from 'node:path';
import { createGzip } from 'node:zlib';

const port = Number(process.argv[2] ?? 4173);
const dist = new URL('../dist/', import.meta.url).pathname;
const TYPES = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript', '.css': 'text/css', '.json': 'application/json',
  '.svg': 'image/svg+xml', '.woff2': 'font/woff2', '.png': 'image/png', '.webmanifest': 'application/manifest+json', '.txt': 'text/plain' };

/** public/_headers → [[path pattern, headers]]; a pattern is `/*` or `/assets/*`. */
function parseHeaders() {
  const rules = [];
  let cur = null;
  for (const raw of readFileSync(join(dist, '_headers'), 'utf8').split('\n')) {
    const line = raw.replace(/#.*/, '').trimEnd();
    if (!line.trim()) continue;
    if (!line.startsWith(' ')) { cur = { prefix: line.trim().replace(/\*$/, ''), headers: {} }; rules.push(cur); continue; }
    const i = line.indexOf(':');
    if (cur && i > 0) cur.headers[line.slice(0, i).trim()] = line.slice(i + 1).trim();
  }
  return rules;
}

createServer((req, res) => {
  let path = normalize(decodeURIComponent(new URL(req.url, 'http://x').pathname));
  if (path.includes('..')) { res.writeHead(400); return res.end(); }
  let file = join(dist, path);
  if (!existsSync(file) || statSync(file).isDirectory()) { file = join(dist, 'index.html'); path = '/index.html'; }
  const headers = { 'Content-Type': TYPES[extname(file)] ?? 'application/octet-stream', Vary: 'Accept-Encoding' };
  for (const r of parseHeaders()) if (path.startsWith(r.prefix)) Object.assign(headers, r.headers);
  const gzip = /\bgzip\b/.test(req.headers['accept-encoding'] ?? '') && !file.endsWith('.woff2');
  if (gzip) headers['Content-Encoding'] = 'gzip';
  res.writeHead(200, headers);
  const s = createReadStream(file);
  gzip ? s.pipe(createGzip()).pipe(res) : s.pipe(res);
}).listen(port, () => console.log(`dist/ on http://localhost:${port} (gzip, _headers, SPA fallback)`));
