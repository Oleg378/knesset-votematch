/// <reference types="vitest/config" />
import { createHash } from 'node:crypto';
import { readFileSync, rmSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { build, defineConfig, type HtmlTagDescriptor, type Plugin, type ResolvedConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { T } from './src/texts';

// The data contract lives outside web/: ../export (produced by `make data`, never copied by hand).
const exportDir = fileURLToPath(new URL('../export', import.meta.url));
/** The first 8 hex of a public/ file's SHA-256: the version in the address of the tab icons. */
const fileHash = (name: string) =>
  createHash('sha256').update(readFileSync(fileURLToPath(new URL(`public/${name}`, import.meta.url)))).digest('hex').slice(0, 8);

// Dev and preview only: lets an ngrok tunnel reach the server (preview on a phone).
const allowedHosts = ['.ngrok-free.app', '.ngrok-free.dev', '.ngrok.app'];

/**
 * The start page in one wave: index.html preloads what it needs besides the JS — its fonts (Fraunces, Plus Jakarta Sans
 * 400/500/600), quiz_core (the number of statements on the chips) and the hero picture. Without this they start only after
 * the JS has run
 * (+0.6 s on a slow phone network, and the text first shows in a fallback font). Build only: names are content-hashed.
 * how-it-works.html preloads the fonts and quiz_core (the loader starts with it), not the hero.
 */
function preloadStartPage(): Plugin {
  let base = '/';
  return {
    name: 'preload-start-page',
    apply: (_c, env) => env.command === 'build' && !env.isSsrBuild,
    configResolved(c) {
      base = c.base;
    },
    transformIndexHtml: {
      order: 'post',
      handler(_html, ctx) {
        const files = Object.keys(ctx.bundle ?? {});
        const fonts = files.filter((f) => /\/(fraunces-opsz|plus-jakarta-sans-latin-(400|500|600)-normal)-[\w-]+\.woff2$/.test(f));
        const core = files.filter((f) => /\/quiz_core-[\w-]+\.json$/.test(f));
        const hero = files.filter((f) => /\/hero-[\w-]+\.svg$/.test(f));
        if (fonts.length !== 4 || core.length !== 1 || hero.length !== 1) {
          throw new Error(`preload-start-page: found ${fonts.length} fonts, ${core.length} quiz_core, ${hero.length} hero`);
        }
        // crossorigin: fonts and fetch() are CORS requests; without it the preloaded file is not reused.
        const link = (href: string, attrs: HtmlTagDescriptor['attrs']): HtmlTagDescriptor => ({
          tag: 'link',
          attrs: { rel: 'preload', href: base + href, ...attrs },
          injectTo: 'head',
        });
        return [
          ...fonts.map((f) => link(f, { as: 'font', type: 'font/woff2', crossorigin: true })),
          link(core[0]!, { as: 'fetch', crossorigin: true }),
          ...(ctx.path === '/index.html' ? [link(hero[0]!, { as: 'image' })] : []),
        ];
      },
    },
  };
}

const TITLE_PLACEHOLDER = '<title>%APP_TITLE%</title>';
const escapeHtml = (s: string) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

/** The page title: the page's entry of PAGES (export/quiz_texts.json) replaces the placeholder in its HTML file. */
function pageTitle(): Plugin {
  return {
    name: 'page-title',
    apply: (_c, env) => !env.isSsrBuild,
    transformIndexHtml: {
      order: 'pre',
      handler(html, ctx) {
        if (!html.includes(TITLE_PLACEHOLDER)) throw new Error(`page-title: ${TITLE_PLACEHOLDER} not found in ${ctx.path}`);
        return html.replace(TITLE_PLACEHOLDER, `<title>${escapeHtml(pageOf(ctx.path).title)}</title>`);
      },
    },
  };
}

/**
 * What search engines, messengers and phones read besides the page (customer 2026-10-24, DECISIONS.md H): the description,
 * the canonical address, the Open Graph / Twitter card (name, description, og-image.png — the preview of a shared link),
 * the icons and the web app manifest; and three files at the root — manifest.webmanifest, robots.txt, sitemap.xml.
 * Every text is from export/quiz_texts.json `app`. Absolute addresses come only from SITE_URL (the hosting sets it,
 * e.g. https://knessetvotematch.org, no slash at the end); without it (CI, a local build) the tags that need an absolute
 * address are left out — a preview needs none, a deploy must have it (scripts/check-dist.mjs).
 */
const SITE_URL = (process.env.SITE_URL ?? '').replace(/\/+$/, '');
/**
 * The pages of the site: path → title. Each is its own HTML file at the root (index.html, how-it-works.html), served at the
 * path without «.html» (Cloudflare Pages does that by itself); both load the same app, which opens the page's screen
 * (src/main.tsx), and both are prerendered (src/prerender.tsx, prerenderPages below).
 */
const PAGES: Record<string, { title: string }> = {
  '/': { title: T.app.title },
  '/how-it-works': { title: `${T.methodology.heading} · ${T.app.siteName}` },
};
const pageOf = (htmlPath: string) => {
  const path = htmlPath.replace(/^\/index\.html$/, '/').replace(/\.html$/, '');
  const page = PAGES[path];
  if (!page) throw new Error(`no page for ${htmlPath}`);
  return { path, ...page };
};

function siteHead(): Plugin {
  const abs = (path: string) => SITE_URL + path;
  let base = '/';
  const meta = (name: string, content: string): HtmlTagDescriptor => ({ tag: 'meta', attrs: { name, content }, injectTo: 'head' });
  const prop = (property: string, content: string): HtmlTagDescriptor => ({ tag: 'meta', attrs: { property, content }, injectTo: 'head' });
  const link = (rel: string, href: string, attrs: HtmlTagDescriptor['attrs'] = {}): HtmlTagDescriptor =>
    ({ tag: 'link', attrs: { rel, href, ...attrs }, injectTo: 'head' });
  return {
    name: 'site-head',
    apply: (_c, env) => !env.isSsrBuild,
    configResolved(c) {
      base = c.base;
    },
    transformIndexHtml: {
      order: 'post',
      handler(_html, ctx) {
        const { path, title } = pageOf(ctx.path);
        const description = T.app.description;
        const tags = [
          meta('description', description),
          // the file's hash in the address: browsers keep a tab icon long after a reload (Safari in its own cache), a new
          // icon comes with a new address (2026-10-25: the new icon did not show)
          link('icon', `${base}favicon.ico?v=${fileHash('favicon.ico')}`, { sizes: '32x32' }),
          link('icon', `${base}favicon.svg?v=${fileHash('favicon.svg')}`, { type: 'image/svg+xml' }),
          link('apple-touch-icon', `${base}apple-touch-icon.png`),
          link('manifest', `${base}manifest.webmanifest`),
          prop('og:type', 'website'),
          prop('og:locale', 'en_US'),
          prop('og:site_name', T.app.siteName),
          prop('og:title', title),
          prop('og:description', description),
          meta('twitter:card', 'summary_large_image'),
          meta('twitter:title', title),
          meta('twitter:description', description),
        ];
        if (SITE_URL) {
          tags.push(
            link('canonical', abs(path)),
            prop('og:url', abs(path)),
            prop('og:image', abs('/og-image.png')),
            prop('og:image:width', '1200'),
            prop('og:image:height', '630'),
            prop('og:image:alt', `${T.app.siteName}: ${T.app.subtitle}`),
            meta('twitter:image', abs('/og-image.png')),
          );
        }
        // Structured data (schema.org): what the site is, in a form search engines read; not a script (CSP allows it).
        if (SITE_URL) {
          const ld = {
            '@context': 'https://schema.org',
            '@type': 'WebApplication',
            name: T.app.siteName,
            headline: title,
            url: abs(path),
            description,
            inLanguage: 'en',
            isAccessibleForFree: true,
            applicationCategory: 'Quiz',
            operatingSystem: 'Any',
            browserRequirements: 'Requires JavaScript',
            image: abs('/og-image.png'),
            author: T.methodology.credits.people.map((p) => ({ '@type': 'Person', name: p.name, sameAs: p.url })),
          };
          tags.push({ tag: 'script', attrs: { type: 'application/ld+json' }, children: JSON.stringify(ld), injectTo: 'head' });
        }
        return tags;
      },
    },
    generateBundle() {
      const manifest = {
        name: T.app.siteName,
        short_name: T.app.name,
        description: T.app.description,
        start_url: base,
        display: 'standalone',
        background_color: '#ffffff',
        theme_color: '#ffffff',
        icons: [
          { src: `${base}icon-192.png`, sizes: '192x192', type: 'image/png' },
          { src: `${base}icon-512.png`, sizes: '512x512', type: 'image/png' },
        ],
      };
      this.emitFile({ type: 'asset', fileName: 'manifest.webmanifest', source: JSON.stringify(manifest, null, 1) + '\n' });
      // /count/ is the metrics beacon (src/analytics.ts), not a page.
      const robots = ['User-agent: *', 'Allow: /', 'Disallow: /count/', ...(SITE_URL ? [`Sitemap: ${abs('/sitemap.xml')}`] : [])];
      this.emitFile({ type: 'asset', fileName: 'robots.txt', source: robots.join('\n') + '\n' });
      const lastmod = new Date().toISOString().slice(0, 10); // the pages change with every build (the data, the texts)
      const urls = Object.keys(PAGES).map((p) => `  <url><loc>${abs(p)}</loc><lastmod>${lastmod}</lastmod></url>`);
      const sitemap = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">', ...urls, '</urlset>'];
      this.emitFile({ type: 'asset', fileName: 'sitemap.xml', source: sitemap.join('\n') + '\n' });
    },
  };
}

/**
 * The pages as ready HTML (DECISIONS.md H5): after the client build — every build, `vite build --watch` too — the pages
 * are rendered by a build-time bundle of src/prerender.tsx (`vite build --ssr` into a temporary folder, removed after)
 * and each page's markup goes into its HTML file in dist/ in place of the empty <div id="root"></div>.
 * scripts/check-dist.mjs checks that every page holds its screen.
 */
function prerenderPages(): Plugin {
  const ROOT = '<div id="root"></div>';
  let config: ResolvedConfig;
  return {
    name: 'prerender-pages',
    apply: (_c, env) => env.command === 'build' && !env.isSsrBuild,
    configResolved(c) {
      config = c;
    },
    async closeBundle() {
      const ssrDir = join(config.root, 'dist-ssr');
      await build({ root: config.root, logLevel: 'warn', build: { ssr: 'src/prerender.tsx', outDir: ssrDir, emptyOutDir: true, copyPublicDir: false } });
      // A fresh module every time (watch mode): the file's address carries the build's time.
      const mod = await import(`${pathToFileURL(join(ssrDir, 'prerender.js')).href}?t=${Date.now()}`) as
        { render: (path: string) => string; PAGE_PATHS: Record<string, string> };
      rmSync(ssrDir, { recursive: true, force: true });
      for (const path of Object.values(mod.PAGE_PATHS)) {
        if (!PAGES[path]) throw new Error(`prerender: ${path} is not in PAGES`);
        const file = join(config.root, config.build.outDir, path === '/' ? 'index.html' : `${path.slice(1)}.html`);
        const html = readFileSync(file, 'utf8');
        if (!html.includes(ROOT)) throw new Error(`prerender: ${file} has no ${ROOT}`);
        writeFileSync(file, html.replace(ROOT, `<div id="root">${mod.render(path)}</div>`));
        config.logger.info(`prerendered ${path}`);
      }
    },
  };
}

export default defineConfig({
  plugins: [react(), preloadStartPage(), pageTitle(), siteHead(), prerenderPages()],
  resolve: { alias: { '@export': exportDir } },
  server: { fs: { allow: ['.', exportDir] }, allowedHosts },
  preview: { allowedHosts },
  json: { stringify: true },
  build: {
    rollupOptions: { input: ['index.html', 'how-it-works.html'] },
    // The data files (src/data.ts) are always separate, content-hashed files: a small one (quiz_core, ~2 KB) must not be
    // inlined as a data: URL — the CSP (connect-src 'self') would block fetching it. (This concerns only the files imported
    // with `?url`. The texts of the site, export/quiz_texts.json, are imported as a module by src/texts.ts and are part of
    // the JS bundle on purpose.)
    assetsInlineLimit: (file) => (file.endsWith('.json') ? false : undefined),
  },
  // Engine/reducer tests run in node; screen tests (*.test.tsx) opt into jsdom with a file comment.
  test: { environment: 'node', include: ['src/**/*.test.ts', 'src/**/*.test.tsx'] },
});
