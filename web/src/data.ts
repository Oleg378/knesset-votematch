/**
 * The data contract v2 (export/V2_HANDOFF.md «Loading»): three static files, not bundled into the JS. The app shell renders
 * at once; the files are fetched one after another — core (preloaded from index.html, see vite.config.ts), then, once the
 * start page is fully drawn, data and bills — while the user answers the core questions. Vite emits them with
 * content-hashed names, so they can be cached for good. Same origin only (CSP).
 */
import billsUrl from '@export/quiz_bills.v2.json?url';
import coreUrl from '@export/quiz_core.v2.json?url';
import dataUrl from '@export/quiz_data.v2.json?url';
import type { QuizBills, QuizCore, QuizData } from './engine/types';

export interface Sources {
  core: QuizCore | null;
  data: QuizData | null;
  bills: QuizBills | null;
  /** A file failed to load, or the three files come from different exports (a deploy mid-session). */
  failed: boolean;
}

export interface Loader {
  get(): Sources;
  subscribe(onChange: () => void): () => void;
  /** Starts the fetches (once). */
  start(): void;
}

type FetchJson = (url: string) => Promise<unknown>;

const fetchJson: FetchJson = async (url) => {
  const r = await fetch(url);
  if (!r.ok) throw new Error(`${url}: ${r.status}`);
  return r.json();
};

const sameExport = (a: QuizCore, b: { version: number; generated: string; source_commit: string }) =>
  a.version === b.version && a.generated === b.generated && a.source_commit === b.source_commit;

/**
 * Resolves when the start page is fully drawn: the page has loaded (the hero picture, and the fonts preloaded from
 * index.html) and the fonts are ready. quiz_data and quiz_bills wait for it, so on a slow network they never take
 * bandwidth from the first screen.
 */
export function firstScreenShown(): Promise<void> {
  return new Promise((resolve) => {
    const fonts = () => {
      const ready = document.fonts ? document.fonts.ready : Promise.resolve();
      ready.then(() => resolve(), () => resolve());
    };
    if (document.readyState === 'complete') fonts();
    else window.addEventListener('load', fonts, { once: true });
  });
}

export function createLoader(get: FetchJson = fetchJson, afterFirstScreen: () => Promise<void> = firstScreenShown): Loader {
  let state: Sources = { core: null, data: null, bills: null, failed: false };
  const listeners = new Set<() => void>();
  let started = false;
  const set = (patch: Partial<Sources>) => {
    state = { ...state, ...patch };
    listeners.forEach((l) => l());
  };
  return {
    get: () => state,
    subscribe(onChange) {
      listeners.add(onChange);
      return () => listeners.delete(onChange);
    },
    start() {
      if (started) return;
      started = true;
      void (async () => {
        try {
          const core = (await get(coreUrl)) as QuizCore;
          set({ core });
          await afterFirstScreen();
          const data = (await get(dataUrl)) as QuizData;
          if (!sameExport(core, data)) throw new Error('quiz_data is from another export');
          set({ data });
          const bills = (await get(billsUrl)) as QuizBills;
          if (!sameExport(core, bills)) throw new Error('quiz_bills is from another export');
          set({ bills });
        } catch {
          set({ failed: true });
        }
      })();
    },
  };
}

/** A loader with everything already in place (tests). */
export function loadedSources(core: QuizCore, data: QuizData, bills: QuizBills): Loader {
  const state: Sources = { core, data, bills, failed: false };
  return { get: () => state, subscribe: () => () => {}, start: () => {} };
}
