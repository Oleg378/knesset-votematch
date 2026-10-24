import { describe, expect, it } from 'vitest';
import { cssTime } from './cssTime';

describe('cssTime', () => {
  it('reads milliseconds and seconds, as written and as the minifier writes them', () => {
    expect(cssTime('200ms')).toBe(200);
    expect(cssTime(' 200ms ')).toBe(200);
    expect(cssTime('.2s')).toBe(200);
    expect(cssTime('0.54s')).toBe(540);
    expect(cssTime('540ms')).toBe(540);
  });

  it('is 0 for nothing or nonsense', () => {
    expect(cssTime('')).toBe(0);
    expect(cssTime('auto')).toBe(0);
  });
});
