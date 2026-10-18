/// <reference types="vitest/config" />
import { fileURLToPath } from 'node:url';
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// The data contract lives outside web/: ../export (produced by `make data`, never copied by hand).
const exportDir = fileURLToPath(new URL('../export', import.meta.url));

export default defineConfig({
  plugins: [react()],
  resolve: { alias: { '@export': exportDir } },
  // Dev only: lets an ngrok tunnel reach the dev server (preview on a phone).
  server: { fs: { allow: ['.', exportDir] }, allowedHosts: ['.ngrok-free.app', '.ngrok-free.dev', '.ngrok.app'] },
  json: { stringify: true },
  build: {
    // The data files (src/data.ts) are always separate, content-hashed files: a small one (quiz_core, ~2 KB) must not be
    // inlined as a data: URL — the CSP (connect-src 'self') would block fetching it.
    assetsInlineLimit: (file) => (file.endsWith('.json') ? false : undefined),
  },
  // Engine/reducer tests run in node; screen tests (*.test.tsx) opt into jsdom with a file comment.
  test: { environment: 'node', include: ['src/**/*.test.ts', 'src/**/*.test.tsx'] },
});
