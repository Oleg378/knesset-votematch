// @vitest-environment jsdom
import { afterEach, describe, expect, it, vi } from 'vitest';
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
  afterEach(() => {
    delete doc.startViewTransition;
    delete document.documentElement.dataset.card;
  });

  it('no View Transitions: the card changes at once', () => {
    const update = vi.fn();
    slideCard(update, false);
    expect(update).toHaveBeenCalledOnce();
    expect(document.documentElement.dataset.card).toBeUndefined();
  });

  it('marks the direction for the transition only; a newer change keeps it', async () => {
    const ends: (() => void)[] = [];
    doc.startViewTransition = vi.fn((update: () => void) => {
      update();
      return { finished: new Promise<void>((resolve) => ends.push(resolve)) };
    });
    const update = vi.fn();
    slideCard(update, true);
    expect(update).toHaveBeenCalledOnce();
    expect(document.documentElement.dataset.card).toBe('back');
    slideCard(update, false);
    ends[0]!(); // the first one is skipped by the second
    await Promise.resolve();
    expect(document.documentElement.dataset.card).toBe('next');
    ends[1]!();
    await Promise.resolve();
    expect(document.documentElement.dataset.card).toBeUndefined();
  });

  it('reduced motion: no transition', () => {
    doc.startViewTransition = vi.fn();
    vi.stubGlobal('matchMedia', (query: string) => ({ matches: query.includes('reduce') }));
    const update = vi.fn();
    slideCard(update, false);
    vi.unstubAllGlobals();
    expect(update).toHaveBeenCalledOnce();
    expect(doc.startViewTransition).not.toHaveBeenCalled();
  });
});
