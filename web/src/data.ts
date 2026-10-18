/**
 * The data contract v2 (export/V2_HANDOFF.md «Loading»): three static files, not bundled into the JS. The app shell renders
 * at once; the files are fetched one after another from page load — core, then data, then bills — while the user answers
 * the core questions. Vite emits them with content-hashed names, so they can be cached for good. Same origin only (CSP).
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

export function createLoader(get: FetchJson = fetchJson): Loader {
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
