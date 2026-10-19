import { describe, expect, it } from 'vitest';
import { pickReserve, REF_LINES } from './statementReserve';

describe('pickReserve', () => {
  it('the tallest statement now among those within the cap on the reference phone', () => {
    // Lines on the reference phone and heights now (a narrower screen: more lines).
    expect(pickReserve([4, 6, 5], [130, 196, 174], REF_LINES)).toBe(196);
    // The tallest now need not be the longest on the reference phone.
    expect(pickReserve([6, 5], [174, 196], REF_LINES)).toBe(196);
  });

  it('an outlier over the cap is not reserved for', () => {
    expect(pickReserve([4, 7, 6], [130, 218, 196], 6)).toBe(196);
  });

  it('nothing to measure: no reserve', () => {
    expect(pickReserve([], [], REF_LINES)).toBe(0);
    expect(pickReserve([7], [218], 6)).toBe(0);
  });
});
