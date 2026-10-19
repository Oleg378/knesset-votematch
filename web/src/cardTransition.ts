import type { Screen } from './state/reducer';

/** A screen that is one quiz card: a statement or a trade-off. */
const isCard = (s: Screen) => s.name === 'question' || s.name === 'tradeoff';

/** One quiz card replaces another (Next, Skip, Back, a trade-off choice): this change slides. */
export function isCardChange(from: Screen, to: Screen): boolean {
  return isCard(from) && isCard(to) && JSON.stringify(from) !== JSON.stringify(to);
}

let current: ViewTransition | null = null;

/**
 * Card change (customer 2026-10-19): an iOS navigation push with the browser's View Transitions (app.css «Card
 * change»). `update` must change the DOM before it returns (flushSync). `data-card` on <html> holds the direction and
 * exists only during the transition: the styles name the screen, the header and the bottom bar only then. No View
 * Transitions (iOS ≤ 17, jsdom) or reduced motion: the card changes at once.
 */
export function slideCard(update: () => void, back: boolean): void {
  const reduced = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
  if (typeof document.startViewTransition !== 'function' || reduced) {
    update();
    return;
  }
  const root = document.documentElement;
  root.dataset.card = back ? 'back' : 'next';
  const t = document.startViewTransition(update);
  current = t;
  // A newer change skips this one: the attribute stays for the newer one.
  const done = () => {
    if (current !== t) return;
    current = null;
    delete root.dataset.card;
  };
  t.finished.then(done, done);
}
