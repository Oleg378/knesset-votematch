// @vitest-environment jsdom
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { isCardChange, slideCard } from './cardTransition';
import type { Screen } from './state/reducer';

const q = (i: number): Screen => ({ name: 'question', i });
const trade = (a: string, b: string): Screen => ({ name: 'tradeoff', pair: [a, b] as never });

describe('isCardChange', () => {
  it('one quiz card replacing another', () => {
    expect(isCardChange(q(0), q(1))).toBe(true);
    expect(isCardChange(q(3), q(2))).toBe(true);
    expect(isCardChange(q(14), trade('5', '9'))).toBe(true);
    expect(isCardChange(trade('5', '9'), trade('2', '7'))).toBe(true);
    expect(isCardChange(trade('5', '9'), q(14))).toBe(true);
  });

  it('not the same card, not other screens', () => {
    expect(isCardChange(q(2), q(2))).toBe(false); // an answer selected
    expect(isCardChange({ name: 'start' }, q(0))).toBe(false);
    expect(isCardChange(q(14), { name: 'results' })).toBe(false);
    expect(isCardChange(q(14), { name: 'wait', then: 'next' })).toBe(false);
    expect(isCardChange(trade('5', '9'), { name: 'results' })).toBe(false);
  });
});

describe('slideCard', () => {
  const doc = document as { startViewTransition?: unknown };
  const root = document.documentElement;
  let frames: (() => void)[] = [];
  const nextFrame = () => {
    const run = frames;
    frames = [];
    run.forEach((f) => f());
  };
  const setScrollY = (y: number) => Object.defineProperty(window, 'scrollY', { value: y, configurable: true });
  // A fake transition: runs the update at once; `end(i)` finishes the i-th one.
  let ends: (() => void)[] = [];
  const fakeTransitions = (log: string[] = []) => {
    doc.startViewTransition = vi.fn((update: () => void) => {
      log.push('transition');
      update();
      return { finished: new Promise<void>((resolve) => ends.push(resolve)) };
    });
  };
  const end = async (i: number) => {
    ends[i]!();
    await Promise.resolve();
    await Promise.resolve();
  };

  beforeEach(() => {
    document.body.innerHTML = '<main class="app"><section class="screen"></section></main>';
    frames = [];
    ends = [];
    vi.stubGlobal('requestAnimationFrame', (f: () => void) => frames.push(f));
    setScrollY(0);
  });
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
    delete doc.startViewTransition;
    delete root.dataset.card;
    root.removeAttribute('style');
    document.body.innerHTML = '';
    setScrollY(0);
  });

  it('no View Transitions: the card changes at once', () => {
    const update = vi.fn();
    slideCard(update, false);
    expect(update).toHaveBeenCalledOnce();
    expect(root.dataset.card).toBeUndefined();
  });

  it('marks the direction for the transition only; a newer change keeps it', async () => {
    fakeTransitions();
    const update = vi.fn();
    slideCard(update, true);
    expect(update).toHaveBeenCalledOnce();
    expect(root.dataset.card).toBe('back');
    slideCard(update, false);
    await end(0); // the first one is skipped by the second
    expect(root.dataset.card).toBe('next');
    await end(1);
    expect(root.dataset.card).toBeUndefined();
    nextFrame();
    expect(root.getAttribute('style') ?? '').toBe('');
  });

  it('a page at the top: never scrolled', async () => {
    const scroll = vi.spyOn(window, 'scrollTo').mockImplementation(() => {});
    fakeTransitions();
    slideCard(vi.fn(), false);
    expect(root.style.getPropertyValue('--card-hold')).toBe('');
    await end(0);
    nextFrame();
    expect(scroll).not.toHaveBeenCalled();
  });

  it('a scrolled page keeps its scroll and height through the transition, then goes to the top', async () => {
    const log: string[] = [];
    const scroll = vi.spyOn(window, 'scrollTo').mockImplementation(() => log.push('scroll'));
    fakeTransitions(log);
    setScrollY(120);
    slideCard(vi.fn(), false);
    expect(root.style.getPropertyValue('--card-hold')).not.toBe(''); // held from before the transition
    await end(0);
    expect(log).toEqual(['transition']); // nothing scrolled before, during or right at the end
    nextFrame(); // a frame later: smoothly to the top
    expect(scroll).toHaveBeenCalledWith({ top: 0, behavior: 'smooth' });
    expect(root.style.getPropertyValue('--card-hold')).not.toBe(''); // still held while scrolling
    setScrollY(0);
    nextFrame();
    expect(root.style.getPropertyValue('--card-hold')).toBe(''); // let go at the top: nothing moves
  });

  it('a change during the smooth scroll stops it first and holds the page again', async () => {
    const scroll = vi.spyOn(window, 'scrollTo').mockImplementation(() => {});
    fakeTransitions();
    setScrollY(120);
    slideCard(vi.fn(), false);
    await end(0);
    nextFrame(); // the smooth scroll starts
    setScrollY(60);
    slideCard(vi.fn(), false);
    expect(scroll).toHaveBeenLastCalledWith(0, 60); // stopped where it is
    nextFrame(); // the first one's release is over: it does not let go of the new hold
    expect(root.style.getPropertyValue('--card-hold')).not.toBe('');
  });

  it('reduced motion: no transition', () => {
    doc.startViewTransition = vi.fn();
    vi.stubGlobal('matchMedia', (query: string) => ({ matches: query.includes('reduce') }));
    const update = vi.fn();
    slideCard(update, false);
    expect(update).toHaveBeenCalledOnce();
    expect(doc.startViewTransition).not.toHaveBeenCalled();
  });
});
