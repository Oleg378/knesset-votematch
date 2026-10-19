import { useLayoutEffect, type RefObject } from 'react';

/**
 * Reserve for the statement (customer 2026-10-19): the answers stand in one place on every question instead of
 * jumping with the length of the statement. The statement block is as high as the longest statement at the current
 * width — among the statements that fit in REF_LINES lines on the Figma phone (REF_VIEWPORT px wide). A longer one is
 * an outlier: nothing is reserved for it (short ones would get a large hole), and it pushes the answers down.
 * The reserve takes only free space above the bottom bar: it never makes a screen scroll or hides the card's bottom
 * under the bar (customer 2026-10-19). On a short window it is smaller, and the longest statements push the answers.
 */
export const REF_LINES = 7;
export const REF_VIEWPORT = 402;

/** The tallest height now among the statements within maxLines on the reference phone. */
export function pickReserve(refLines: number[], heights: number[], maxLines: number): number {
  let reserve = 0;
  refLines.forEach((n, i) => {
    if (n <= maxLines) reserve = Math.max(reserve, heights[i] ?? 0);
  });
  return reserve;
}

/** Every text laid out like `sample` (same classes) at each width: border-box heights and line counts, per width. */
function measure(sample: HTMLElement, texts: string[], widths: number[]) {
  const box = document.createElement('div');
  box.setAttribute('aria-hidden', 'true');
  box.style.cssText = 'position:absolute;top:0;left:0;visibility:hidden;pointer-events:none';
  const els = texts.map((t) => {
    const el = document.createElement('div');
    el.className = sample.className;
    el.textContent = t;
    return el;
  });
  box.append(...els);
  document.body.append(box);
  const cs = getComputedStyle(els[0] ?? sample);
  const pad = parseFloat(cs.paddingTop) + parseFloat(cs.paddingBottom);
  const line = parseFloat(cs.lineHeight);
  const out = widths.map((w) => {
    box.style.width = `${w}px`;
    const heights = els.map((el) => el.getBoundingClientRect().height);
    return { heights, lines: heights.map((h) => Math.round((h - pad) / line)) };
  });
  box.remove();
  return out;
}

let cache: { texts: string[]; key: string; reserve: number } | null = null;

function reserveFor(el: HTMLElement, texts: string[]): number {
  const width = el.getBoundingClientRect().width;
  if (!width || !texts.length) return 0;
  const key = `${width}/${document.fonts?.status}`; // measured again once the font has loaded
  if (cache?.texts === texts && cache.key === key) return cache.reserve;
  // On the reference phone the statement is narrower than the window by the screen and card paddings on both sides.
  const root = getComputedStyle(document.documentElement);
  const inset = parseFloat(root.getPropertyValue('--gutter')) + parseFloat(root.getPropertyValue('--panel-pad-x'));
  const [ref, now] = measure(el, texts, [REF_VIEWPORT - 2 * inset, width]);
  const reserve = pickReserve(ref!.lines, now!.heights, REF_LINES);
  cache = { texts, key, reserve };
  return reserve;
}

/**
 * How high the statement block can be without the screen overflowing the window: its natural height, plus the free
 * space above the bottom bar, minus what already overflows. The same on every question (the rest of the card is), so
 * the answers stay in one place as long as a statement fits in it.
 */
function room(el: HTMLElement): number {
  const panel = el.closest('.panel');
  const screen = el.closest('.screen');
  const app = el.closest('.app');
  const bar = screen?.querySelector('.bottom-bar');
  if (!panel || !screen || !app || !bar) return Infinity;
  const over = app.getBoundingClientRect().height - parseFloat(getComputedStyle(app).minHeight);
  const gap = parseFloat(getComputedStyle(screen).rowGap) || 0;
  const above = bar.getBoundingClientRect().top - panel.getBoundingClientRect().bottom - gap;
  const free = over > 0.5 ? 0 : Math.max(0, above);
  return el.getBoundingClientRect().height + free - Math.max(0, over);
}

/** Sets the statement block's min-height before paint; again on resize and when the font arrives. */
export function useStatementReserve(ref: RefObject<HTMLElement | null>, texts: string[]): void {
  useLayoutEffect(() => {
    const el = ref.current;
    if (!el) return;
    let alive = true;
    const apply = () => {
      if (!alive) return;
      el.style.minHeight = '';
      const reserve = Math.min(reserveFor(el, texts), room(el));
      el.style.minHeight = reserve > 0 ? `${reserve}px` : '';
    };
    apply();
    document.fonts?.ready.then(apply);
    window.addEventListener('resize', apply);
    return () => {
      alive = false;
      window.removeEventListener('resize', apply);
    };
  }, [ref, texts]);
}
