import { describe, expect, it } from 'vitest';
import { needsInnerScroll } from './shortScroll';

// iPhone 12 mini, Chrome: 100svh = 631, 100lvh = 730 (customer 2026-10-23).
const S = 631;
const L = 730;

describe('needsInnerScroll', () => {
  it('content that fits the window with the bars shown: no scroll at all', () => {
    expect(needsInnerScroll(600, S, L)).toBe(false);
    expect(needsInnerScroll(631, S, L)).toBe(false);
  });

  it('a little longer: scrolls inside .app, the bars stay', () => {
    expect(needsInnerScroll(707, S, L)).toBe(true);
    expect(needsInnerScroll(828, S, L)).toBe(true);
  });

  it('longer: the document scrolls, the bars hide', () => {
    expect(needsInnerScroll(829, S, L)).toBe(false);
    expect(needsInnerScroll(1500, S, L)).toBe(false);
  });

  it('no bars that hide (svh = lvh): the document scrolls as before', () => {
    expect(needsInnerScroll(718, 700, 700)).toBe(false);
  });
});
