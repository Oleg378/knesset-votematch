import { describe, expect, it } from 'vitest';
import { formatCloseness, pyFixed, pyPercent0 } from './format';

describe('Python-compatible formatting', () => {
  it('percent like f"{x:.0%}" (ties to even on the float x*100)', () => {
    expect(pyPercent0(0)).toBe('0%');
    expect(pyPercent0(1)).toBe('100%');
    expect(pyPercent0(0.125)).toBe('12%'); // 12.5 -> 12 (Python), JS toFixed would give 13
    expect(pyPercent0(0.135)).toBe('14%');
    expect(pyPercent0(0.034482758620689655)).toBe('3%');
    expect(pyPercent0(0.005)).toBe('0%'); // 0.5 -> 0
    expect(pyPercent0(0.015)).toBe('2%'); // 1.5 -> 2
  });
  it('closeness like f"{x:+.1f}" (one decimal, customer 2026-10-18)', () => {
    expect(formatCloseness(0.35925255471495104)).toBe('+0.4');
    expect(formatCloseness(-0.001)).toBe('-0.0');
    expect(formatCloseness(0)).toBe('+0.0');
    expect(formatCloseness(-0)).toBe('-0.0');
    expect(formatCloseness(0.25)).toBe('+0.2'); // tie to even
    expect(formatCloseness(0.35)).toBe('+0.3'); // binary value is below the tie
    expect(formatCloseness(1)).toBe('+1.0');
  });
  it('pyFixed like f"{x:.2f}"', () => {
    expect(pyFixed(0.125, 2)).toBe('0.12');
    expect(pyFixed(0.375, 2)).toBe('0.38');
    expect(pyFixed(2.675, 2)).toBe('2.67'); // binary value is below the tie
    expect(pyFixed(-0.001, 2, true)).toBe('-0.00');
  });
});
