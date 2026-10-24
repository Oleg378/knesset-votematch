import type { Screen } from './state/reducer';

/** A screen that is one quiz card: a statement or a trade-off. */
const isCard = (s: Screen) => s.name === 'question' || s.name === 'tradeoff';

/** One quiz card replaces another (Next, Skip, Back, a trade-off choice): this change slides. */
export function isCardChange(from: Screen, to: Screen): boolean {
  return isCard(from) && isCard(to) && JSON.stringify(from) !== JSON.stringify(to);
}

let current: ViewTransition | null = null;

/**
 * Any other change of screen (Start → the first question, the last answer → Results, a result → List details and back,
 * the methodology page; customer 2026-10-24: «что-то лёгкое»): a short cross-fade of the whole page through the
 * browser's View Transitions, `--screen-fade` long (app.css «Screen fade»). `update` must change the DOM before it
 * returns (flushSync). No View Transitions (iOS ≤ 17, jsdom) or reduced motion: the screen changes at once. A card change
 * in flight is left alone: the fade is skipped, not stacked on it.
 */
export function fadeScreen(update: () => void): void {
  const reduced = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
  if (typeof document.startViewTransition !== 'function' || reduced || current) {
    update();
    return;
  }
  const root = document.documentElement;
  root.dataset.fade = '';
  const t = document.startViewTransition(update);
  const done = () => {
    if (!root.dataset.card) delete root.dataset.fade;
  };
  t.finished.then(done, done);
}
const CARD_VARS = ['--card-old-y', '--card-clip-top', '--card-visible'];

const box = (selector: string) => document.querySelector(selector)?.getBoundingClientRect();

/**
 * Card change (customer 2026-10-19): an iOS navigation push with the browser's View Transitions (app.css «Card
 * change»). `update` must change the DOM before it returns (flushSync). `data-card` on <html> holds the direction and
 * exists only during the transition: the styles name the screen, the header and the bottom bar only then. No View
 * Transitions (iOS ≤ 17, jsdom) or reduced motion: the card changes at once.
 *
 * The page is never scrolled around the transition: Safari on iPhone applies a scroll a moment later than the change
 * of the page, so a scroll made just before, during or right at the end of a transition draws the screens off by the
 * scrolled distance (text over the header, a missing header, a jerk at the end — customer's videos, 2026-10-19). Both
 * screens are captured at the page's current scroll, which the transition keeps: the app keeps its height (--card-hold,
 * the min-height of .app), so a shorter new screen can neither make the browser pull the scroll up nor lift the bottom
 * bar. Once it has ended, a scrolled page goes smoothly to the top of the new screen (toTop).
 */
export function slideCard(update: () => void, back: boolean): void {
  const reduced = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
  if (typeof document.startViewTransition !== 'function' || reduced) {
    update();
    return;
  }
  const root = document.documentElement;
  const run = ++generation;
  if (smoothing) window.scrollTo(0, window.scrollY); // stops the smooth scroll to the top from the last change
  smoothing = false;
  const app = box('.app');
  if (window.scrollY > 0 && app) root.style.setProperty('--card-hold', `${app.height}px`);
  else root.style.removeProperty('--card-hold');
  const oldTop = box('.screen')?.top ?? 0;
  root.dataset.card = back ? 'back' : 'next';
  const t = document.startViewTransition(() => {
    update();
    const screen = box('.screen');
    if (!screen) return;
    // The old picture is placed with the new screen's box: moved back to where the old screen was.
    root.style.setProperty('--card-old-y', `${oldTop - screen.top}px`);
    // A scrolled screen goes on under the header: clipped there, or it would show beside the column-wide header.
    root.style.setProperty('--card-clip-top', `${Math.max(0, (box('.header')?.bottom ?? 0) - screen.top)}px`);
    // The bottom bar covers the column only: the sliding screens end at its top, so nothing passes beside it.
    root.style.setProperty('--card-visible', `${(box('.bottom-bar')?.top ?? screen.bottom) - screen.top}px`);
  });
  current = t;
  // A newer change skips this one: the attribute stays for the newer one.
  const done = () => {
    if (current !== t) return;
    current = null;
    delete root.dataset.card;
    CARD_VARS.forEach((v) => root.style.removeProperty(v));
    toTop(run);
  };
  t.finished.then(done, done);
}

let generation = 0;
let smoothing = false;

/**
 * After the transition, a scrolled page goes smoothly to the top: the new statement is read from its start. A frame
 * later, so the browser has finished the transition. The page keeps its held height until it is at the top (or for
 * a second at most, if a finger stops the scroll), so letting it go moves nothing.
 */
function toTop(run: number): void {
  const root = document.documentElement;
  requestAnimationFrame(() => {
    if (run !== generation) return;
    if (window.scrollY > 0) {
      smoothing = true;
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
    const start = performance.now();
    const release = () => {
      if (run !== generation) return;
      if (window.scrollY > 0 && performance.now() - start < 1000) {
        requestAnimationFrame(release);
        return;
      }
      smoothing = false;
      root.style.removeProperty('--card-hold');
    };
    release();
  });
}
