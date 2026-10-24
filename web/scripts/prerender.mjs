// After `vite build`: renders the pages (src/prerender.tsx) with a build-time bundle (`vite build --ssr`, into a temporary
// folder) and puts each page's markup into its HTML file in dist/ — index.html and how-it-works.html — in place of the
// empty <div id="root"></div>. Part of `npm run build`; scripts/check-dist.mjs checks the result.
import { readFileSync, rmSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { build } from 'vite';

const root = fileURLToPath(new URL('..', import.meta.url));
const ssrDir = join(root, 'dist-ssr');
const ROOT = '<div id="root"></div>';

await build({ root, logLevel: 'warn', build: { ssr: 'src/prerender.tsx', outDir: ssrDir, emptyOutDir: true, copyPublicDir: false } });
const { render, PAGE_PATHS } = await import(pathToFileURL(join(ssrDir, 'prerender.js')).href);
rmSync(ssrDir, { recursive: true, force: true });

for (const path of Object.values(PAGE_PATHS)) {
  const file = join(root, 'dist', path === '/' ? 'index.html' : `${path.slice(1)}.html`);
  const html = readFileSync(file, 'utf8');
  if (!html.includes(ROOT)) throw new Error(`prerender: ${file} has no ${ROOT}`);
  writeFileSync(file, html.replace(ROOT, `<div id="root">${render(path)}</div>`));
  console.log(`prerendered ${path} -> ${file.slice(root.length)}`);
}
