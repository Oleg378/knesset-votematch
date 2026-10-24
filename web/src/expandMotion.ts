/**
 * Opening and closing a block in the flow (accordion bodies, the lists under «See all»), by the guidelines
 * (customer 2026-10-23): Material Design — opening decelerates, closing accelerates and is a little quicker, larger
 * changes take longer; Braid (SEEK) — the height is animated in px while moving, auto when settled, the duration
 * comes from the height (clamped). Only the part on screen moves: a block taller than the screen below its top grows
 * to the screen's bottom (or shrinks from it) and takes its full height (or none) at once, off screen — otherwise the
 * part on screen would fill or empty in the first or last frames. The content fades in a little after the block
 * starts growing, and out before it is gone. Keyframes and tokens: app.css «Expand and collapse», tokens.css.
 * No motion with reduced motion, or where there is no layout (jsdom): the block just is open or closed.
 */
import { cssTime } from './cssTime';
import { screenScroller } from './scroller';

const reducedMotion = () => window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? true;

const token = (name: string) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();
const ms = (name: string) => cssTime(token(name));

/** How long the motion over `px` takes: `rate` ms per px, clamped. */
export function motionTime(px: number, rate: number, min: number, max: number): number {
  return Math.min(Math.max(px * rate, min), max);
}

/** The part of the element on screen, from its top to the screen's bottom (at most its height). */
function onScreen(el: HTMLElement): number {
  const r = el.getBoundingClientRect();
  return Math.min(r.height, Math.max(document.documentElement.clientHeight - r.top, 0));
}

function run(el: HTMLElement, cls: string, px: number, rate: string, done: () => void, hold: boolean): () => void {
  const time = motionTime(px, parseFloat(token(rate)) || 0, ms('--expand-min-time'), ms('--expand-max-time'));
  el.style.setProperty('--motion-px', `${px}px`);
  el.style.setProperty('--motion-time', `${time}ms`);
  el.classList.add(cls);
  let over = false;
  const end = (finished: boolean) => {
    if (over) return;
    over = true;
    el.removeEventListener('animationend', onEnd);
    clearTimeout(timer);
    if (finished && hold) {
      done(); // closed: stays at its last frame (fill-mode) until it is unmounted, no frame at full height
      return;
    }
    el.classList.remove(cls);
    el.style.removeProperty('--motion-px');
    el.style.removeProperty('--motion-time');
    if (finished) done();
  };
  const onEnd = (e: AnimationEvent) => e.target === e.currentTarget && end(true);
  el.addEventListener('animationend', onEnd);
  const timer = setTimeout(() => end(true), time + 50);
  return () => end(false); // cancelled (reopened while closing, unmounted): no `done`
}

/** Call right after the block is in the DOM at its full height, before the next paint (a layout effect). */
export function expand(el: HTMLElement): () => void {
  const px = reducedMotion() ? 0 : onScreen(el);
  if (px <= 0) return () => {};
  return run(el, 'expanding', px, '--expand-ms-per-px', () => {}, false);
}

/** `done` (unmount, or hide) runs when the block is gone; at once without motion. */
export function collapse(el: HTMLElement, done: () => void): () => void {
  const px = reducedMotion() ? 0 : onScreen(el);
  if (px <= 0) {
    done();
    return () => {};
  }
  return run(el, 'collapsing', px, '--collapse-ms-per-px', done, true);
}

/**
 * Brings `el` up to just below the pinned header with the browser's own smooth scroll, then `done` — for closing a
 * block whose button sits at its end, far below where it started («Show less»): first the page goes back to the
 * start, then the block closes on screen. At once with reduced motion or when `el` is already in place.
 *
 * `shrink` = how much shorter the page will be once the block has closed. The scroll goes no further than the page will
 * then allow: otherwise, as the block shrinks, the page becomes too short for the scroll position and the browser pulls
 * the scroll back in the last frames — the whole page jumped down at the end (customer's recording, 2026-10-24). With
 * the limit the page rests where it will end, and the block closes on screen without a jump.
 */
export function scrollBackTo(el: HTMLElement, done: () => void, shrink = 0): void {
  const inner = screenScroller(); // phones: the area under the header; card mode: the window
  const header = document.querySelector('.header')?.getBoundingClientRect().bottom ?? 0;
  const gap = parseFloat(token('--space-4')) || 0;
  const by = el.getBoundingClientRect().top - header - gap;
  const scroller: Element | Window = inner ?? window;
  const from = inner ? inner.scrollTop : window.scrollY;
  const extent = inner ?? document.documentElement;
  const maxAfter = Math.max(extent.scrollHeight - shrink - extent.clientHeight, 0);
  const top = Math.min(Math.max(from + by, 0), maxAfter);
  if (top >= from - 1) {
    done(); // already on screen below the header, or as far up as the closed page allows
    return;
  }
  if (reducedMotion()) {
    scroller.scrollTo({ top });
    done();
    return;
  }
  // The end: the scroll reached the target or stopped (a finger took over) — checked once a frame while it runs, as
  // Safari before 26 has no scrollend; or the timeout.
  const at = () => (inner ? inner.scrollTop : window.scrollY);
  const started = performance.now();
  const limit = ms('--scroll-back-max-time');
  let last = at();
  let still = 0;
  const check = () => {
    const now = at();
    still = Math.abs(now - last) < 0.5 ? still + 1 : 0;
    last = now;
    if (Math.abs(now - top) < 1 || still >= 3 || performance.now() - started > limit) done();
    else requestAnimationFrame(check);
  };
  scroller.scrollTo({ top, behavior: 'smooth' });
  requestAnimationFrame(check);
}
