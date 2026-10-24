/**
 * The pages of the site as ready HTML (customer 2026-10-24, DECISIONS.md H): the start page and «How it works» are
 * rendered at build time from the same components the app draws, with the data of the same export (export/ is in git and
 * deployed with the site), and put into index.html / how-it-works.html in place of an empty page (scripts/prerender.mjs).
 * A search engine, a link preview or a reader without JavaScript gets the text; the app, once loaded, draws the same
 * markup in its place (src/main.tsx). The shell must be the one App renders — src/prerender.test.tsx compares them.
 *
 * Built only by `vite build --ssr` (scripts/prerender.mjs); the app never imports this module. The data files are
 * imported here as JSON (bundled into the build-time module only), not fetched.
 */
import type React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { Header } from './components/Header';
import type { QuizBills, QuizCore, QuizData } from './engine/types';
import { MethodologyScreen } from './screens/MethodologyScreen';
import { StartScreen } from './screens/StartScreen';
import { initialStateFor } from './state/reducer';
import { S } from './strings';
import coreJson from '@export/quiz_core.json';
import dataJson from '@export/quiz_data.json';
import billsJson from '@export/quiz_bills.json';

const core = coreJson as QuizCore;
const data = dataJson as QuizData;
const bills = billsJson as QuizBills;
const noop = () => {};

/** React's server renderer puts a preload of the hero picture before the markup; index.html preloads it itself (vite.config.ts). */
const markup = (node: React.ReactNode) => renderToStaticMarkup(node).replace(/^(?:<link rel="preload"[^>]*>)+/, '');

/** The paths of the pages and the screen each one opens (src/main.tsx reads the same map). */
export const PAGE_PATHS = { start: '/', methodology: '/how-it-works' } as const;

export function render(path: string): string {
  switch (path) {
    case PAGE_PATHS.start:
      return markup(
        <main className="app">
          <Header onMenu={noop} />
          <div className="app-scroll"><StartScreen core={core} dispatch={noop} /></div>
        </main>,
      );
    case PAGE_PATHS.methodology:
      return markup(
        <main className="app">
          <Header onMenu={noop} title={S.methodology.heading} />
          <div className="app-scroll">
            <MethodologyScreen data={data} bills={bills} state={initialStateFor(path)} dispatch={noop} />
          </div>
        </main>,
      );
    default:
      throw new Error(`prerender: unknown page ${path}`);
  }
}
