/// <reference types="vitest/config" />
import { fileURLToPath } from 'node:url';
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// The data contract lives outside web/: ../export (produced by `make data`, never copied by hand).
const exportDir = fileURLToPath(new URL('../export', import.meta.url));

export default defineConfig({
  plugins: [react()],
  resolve: { alias: { '@export': exportDir } },
  server: { fs: { allow: ['.', exportDir] } },
  json: { stringify: true },
  build: { chunkSizeWarningLimit: 2500 },
  // Engine/reducer tests run in node; screen tests (*.test.tsx) opt into jsdom with a file comment.
  test: { environment: 'node', include: ['src/**/*.test.ts', 'src/**/*.test.tsx'] },
});
