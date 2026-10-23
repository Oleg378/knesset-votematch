// @vitest-environment jsdom
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { watchBottomFade } from './bottomFade';

describe('watchBottomFade', () => {
  const root = document.documentElement;
  let frames: (() => void)[] = [];
  const nextFrame = () => {
    const run = frames;
    frames = [];
    run.forEach((f) => f());
  };
  const page = (height: number, scrollY: number) => {
    Object.defineProperty(root, 'scrollHeight', { value: height, configurable: true });
    Object.defineProperty(window, 'scrollY', { value: scrollY, configurable: true });
    Object.defineProperty(window, 'innerHeight', { value: 660, configurable: true });
  };
  let stop = () => {};

  beforeEach(() => {
    frames = [];
    vi.stubGlobal('requestAnimationFrame', (f: () => void) => frames.push(f));
    vi.stubGlobal('cancelAnimationFrame', () => {});
  });
  afterEach(() => {
    stop();
    vi.unstubAllGlobals();
  });

  it('everything fits: no fade', () => {
    page(660, 0);
    stop = watchBottomFade();
    expect(root.hasAttribute('data-below')).toBe(false);
  });

  it('the card goes on under the buttons: fade; scrolled to the end: crisp again', () => {
    page(760, 0);
    stop = watchBottomFade();
    expect(root.hasAttribute('data-below')).toBe(true);
    page(760, 100);
    window.dispatchEvent(new Event('scroll'));
    nextFrame();
    expect(root.hasAttribute('data-below')).toBe(false);
    page(760, 60);
    window.dispatchEvent(new Event('scroll'));
    nextFrame();
    expect(root.hasAttribute('data-below')).toBe(true);
  });

  it('a window that grows to fit: no fade; stopping clears it', () => {
    page(760, 0);
    stop = watchBottomFade();
    page(660, 0);
    window.dispatchEvent(new Event('resize'));
    nextFrame();
    expect(root.hasAttribute('data-below')).toBe(false);
    page(760, 0);
    window.dispatchEvent(new Event('resize'));
    nextFrame();
    stop();
    expect(root.hasAttribute('data-below')).toBe(false);
  });
});
