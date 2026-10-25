import coreJson from '@export/quiz_core.json';
import type { AnswerValue, QuizCore } from './engine/types';
import { initialState, type State } from './state/reducer';

/**
 * Dev server only, `?demo` (main.tsx): opens List details at once, its first topic open, so a change on that page can be
 * looked at without taking the quiz. Every statement answered by a fixed pattern, every other one weighted ×2 as after a
 * trade-off question (so «Weight ×2» shows); `?demo=<list id>` picks the list (default Be’Yahad). Never in the production build: main.tsx imports this file only under `import.meta.env.DEV`.
 */
const core = coreJson as QuizCore;
const PATTERN: AnswerValue[] = [2, 1, -1, -2, 2, -2, 1];

export function demoState(param: string | null): State {
  const shown = core.statements.map((s) => s.q);
  const answers = Object.fromEntries(shown.map((q, i) => [q, PATTERN[i % PATTERN.length]!]));
  const mult = Object.fromEntries(shown.filter((_, i) => i % 2 === 0).map((q) => [q, 2]));
  return { ...initialState, answers, mult, shown, screen: { name: 'details', list: param || 'רק' } };
}

export function openFirstTopic(): void {
  const t = setInterval(() => {
    const head = document.querySelector<HTMLElement>('.accordion-head');
    if (!head) return;
    clearInterval(t);
    head.click();
  }, 100);
}
