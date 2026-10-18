/// <reference types="vitest/config" />
import { fileURLToPath } from 'node:url';
import { defineConfig, type HtmlTagDescriptor, type Plugin } from 'vite';
import react from '@vitejs/plugin-react';
import { dotRingSvg } from './src/components/dotRing';
import { S } from './src/strings';

// The data contract lives outside web/: ../export (produced by `make data`, never copied by hand).
const exportDir = fileURLToPath(new URL('../export', import.meta.url));

// Dev and preview only: lets an ngrok tunnel reach the server (preview on a phone).
const allowedHosts = ['.ngrok-free.app', '.ngrok-free.dev', '.ngrok.app'];

/**
 * The start page in one wave: index.html preloads what it needs besides the JS — its fonts (Fraunces, Plus Jakarta Sans
 * 400/500/600), quiz_core (the number of statements on the chips) and the hero picture. Without this they start only after
 * the JS has run
 * (+0.6 s on a slow phone network, and the text first shows in a fallback font). Build only: names are content-hashed.
 */
function preloadStartPage(): Plugin {
  let base = '/';
  return {
    name: 'preload-start-page',
    apply: 'build',
    configResolved(c) {
      base = c.base;
    },
    transformIndexHtml: {
      order: 'post',
      handler(_html, ctx) {
        const files = Object.keys(ctx.bundle ?? {});
        const fonts = files.filter((f) => /\/(fraunces-opsz|plus-jakarta-sans-latin-(400|500|600)-normal)-[\w-]+\.woff2$/.test(f));
        const core = files.filter((f) => /\/quiz_core\.v2-[\w-]+\.json$/.test(f));
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
          link(hero[0]!, { as: 'image' }),
        ];
      },
    },
  };
}

/**
 * What the page shows until the JS has drawn the first screen (customer 2026-10-18): the loading dot ring
 * (src/components/dotRing.ts) in an empty .app. Plain HTML + CSS (`.boot`, `.dot-ring` in app.css), no script — the CSP
 * allows none inline. React replaces it on its first render (createRoot clears #root).
 */
function bootLoader(): Plugin {
  const svg = dotRingSvg(S.loading);
  return {
    name: 'boot-loader',
    transformIndexHtml(html) {
      if (!html.includes('<div id="root"></div>')) throw new Error('boot-loader: <div id="root"></div> not found');
      return html.replace('<div id="root"></div>', `<div id="root"><main class="app boot">${svg}</main></div>`);
    },
  };
}

export default defineConfig({
  plugins: [react(), preloadStartPage(), bootLoader()],
  resolve: { alias: { '@export': exportDir } },
  server: { fs: { allow: ['.', exportDir] }, allowedHosts },
  preview: { allowedHosts },
  json: { stringify: true },
  build: {
    // The data files (src/data.ts) are always separate, content-hashed files: a small one (quiz_core, ~2 KB) must not be
    // inlined as a data: URL — the CSP (connect-src 'self') would block fetching it.
    assetsInlineLimit: (file) => (file.endsWith('.json') ? false : undefined),
  },
  // Engine/reducer tests run in node; screen tests (*.test.tsx) opt into jsdom with a file comment.
  test: { environment: 'node', include: ['src/**/*.test.ts', 'src/**/*.test.tsx'] },
});
