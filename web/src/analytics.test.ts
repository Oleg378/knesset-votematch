import { afterEach, describe, expect, it, vi } from 'vitest';
import { COUNT_PATH, track } from './analytics';

describe('track', () => {
  afterEach(() => vi.unstubAllGlobals());

  it('sends the event name alone to the site\'s own address, nothing else', () => {
    const sendBeacon = vi.fn(() => true);
    vi.stubGlobal('navigator', { sendBeacon });
    track('started');
    track('finished');
    expect(sendBeacon.mock.calls).toEqual([[`${COUNT_PATH}started`], [`${COUNT_PATH}finished`]]);
  });

  it('does nothing where beacons do not exist, and never throws', () => {
    vi.stubGlobal('navigator', {});
    expect(() => track('started')).not.toThrow();
    vi.stubGlobal('navigator', { sendBeacon: () => { throw new Error('blocked'); } });
    expect(() => track('finished')).not.toThrow();
  });
});
