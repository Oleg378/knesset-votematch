import { describe, expect, it } from 'vitest';
import { createLoader } from './data';
import { bills, core, data } from './testSources';

const files = { quiz_core: core, quiz_data: data, quiz_bills: bills };
const name = (url: string) => (Object.keys(files) as (keyof typeof files)[]).find((k) => url.includes(k))!;
const settle = async () => {
  for (let i = 0; i < 5; i++) await new Promise((r) => setTimeout(r, 0));
};

describe('createLoader', () => {
  it('fetches quiz_core at once; then quiz_data and quiz_bills only after the start page is drawn', async () => {
    const asked: string[] = [];
    let drawn!: () => void;
    const firstScreen = new Promise<void>((r) => (drawn = r));
    const loader = createLoader(async (url) => {
      asked.push(name(url));
      return files[name(url)];
    }, () => firstScreen);

    loader.start();
    await settle();
    expect(asked).toEqual(['quiz_core']);
    expect(loader.get()).toEqual({ core, data: null, bills: null, failed: false });

    drawn();
    await settle();
    expect(asked).toEqual(['quiz_core', 'quiz_data', 'quiz_bills']);
    expect(loader.get()).toEqual({ core, data, bills, failed: false });
  });

  it('a file from another export fails the load', async () => {
    const loader = createLoader(async (url) => (name(url) === 'quiz_data' ? { ...data, generated: 'other' } : files[name(url)]),
      () => Promise.resolve());
    loader.start();
    await settle();
    expect(loader.get().failed).toBe(true);
    expect(loader.get().data).toBeNull();
  });
});
