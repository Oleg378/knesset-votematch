import type { Screen } from './state/reducer';

/** A screen that is one quiz card: a statement or a trade-off. */
const isCard = (s: Screen) => s.name === 'question' || s.name === 'tradeoff';

/** One quiz card replaces another (Next, Skip, Back, a trade-off choice): this change slides. */
export function isCardChange(from: Screen, to: Screen): boolean {
  return isCard(from) && isCard(to) && JSON.stringify(from) !== JSON.stringify(to);
}

let current: ViewTransition | null = null;
const CARD_VARS = ['--card-hold', '--card-lift', '--card-old-y', '--card-visible'];

const screenTop = () => document.querySelector('.screen')?.getBoundingClientRect().top ?? 0;

/**
 * Card change (customer 2026-10-19): an iOS navigation push with the browser's View Transitions (app.css «Card
 * change»). `update` must change the DOM before it returns (flushSync). `data-card` on <html> holds the direction and
 * exists only during the transition: the styles name the screen, the header and the bottom bar only then. No View
 * Transitions (iOS ≤ 17, jsdom) or reduced motion: the card changes at once.
 *
 * The screens move only sideways: the old one leaves from where it was, the new one opens at its top. The page is
 * never scrolled during the transition — Safari then draws everything off by the scrolled distance and jumps back at
 * the end. Instead the new page is shown as at the top by moving it down by the page's scroll (--card-lift), the page
 * keeps at least its old height (--card-hold: a shorter new screen would make the browser pull the scroll up), and at
 * the end both go and the page scrolls to the top in one step, which changes nothing on screen.
 */
export function slideCard(update: () => void, back: boolean): void {
  const reduced = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
  if (typeof document.startViewTransition !== 'function' || reduced) {
    update();
    return;
  }
  const root = document.documentElement;
  const oldTop = screenTop();
  root.style.setProperty('--card-hold', `${root.scrollHeight}px`);
  root.dataset.card = back ? 'back' : 'next';
  const t = document.startViewTransition(() => {
    update();
    root.style.setProperty('--card-lift', `${window.scrollY}px`);
    const top = screenTop();
    // The old picture is placed with the new screen's box: moved back to where the old screen was.
    root.style.setProperty('--card-old-y', `${oldTop - top}px`);
    // The bottom bar covers the column only: the sliding screens end at its top, so nothing passes beside it.
    const bar = document.querySelector('.bottom-bar');
    if (bar) root.style.setProperty('--card-visible', `${bar.getBoundingClientRect().top - top}px`);
  });
  current = t;
  // A newer change skips this one: the attribute and the lift stay for the newer one.
  const done = () => {
    if (current !== t) return;
    current = null;
    delete root.dataset.card;
    CARD_VARS.forEach((v) => root.style.removeProperty(v));
    window.scrollTo(0, 0);
  };
  t.finished.then(done, done);
}
