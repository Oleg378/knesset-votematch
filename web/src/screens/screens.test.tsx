// @vitest-environment jsdom
/**
 * Screen tests: the whole flow through <App/> as a user clicks it, plus the SPEC «never show / never store» rules.
 * Numbers themselves are covered by the golden tests; here only what reaches the screen. The two fetched data files are
 * served by a fetch stub from the export.
 */
import { act, cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import App from '../App';
import { formatCloseness } from '../engine/format';
import { match } from '../engine/match';
import type { AnswerValue } from '../engine/types';
import { createReducer, statementOf, type State } from '../state/reducer';
import { S } from '../strings';
import { bills, core, data, loaded } from '../test/files';

const click = (name: string | RegExp) => fireEvent.click(screen.getByRole('button', { name }));
const pressed = () => screen.queryAllByRole('button', { pressed: true }).map((b) => b.textContent);

const SEQ: AnswerValue[] = [2, -1, 1, -2];
const TOTAL = core.flow.core + core.flow.clarify;
const first = statementOf(core, null, core.core[0]!)!;

/** Answers the first n statements (answer + Next) with a fixed pattern; stops on statement n + 1. */
function answer(n: number) {
  for (let i = 0; i < n; i++) {
    click(S.answers[SEQ[i % SEQ.length]!]);
    click(S.nav.next);
  }
}

/** The state the reducer reaches with the same n answers: what the screens must show. */
function expected(n: number): State {
  const reducer = createReducer(core);
  let s = reducer(loaded, { type: 'START' });
  for (let i = 0; i < n; i++) s = reducer(reducer(s, { type: 'ANSWER', value: SEQ[i % SEQ.length]! }), { type: 'NEXT' });
  return s;
}

const menuTo = (item: string) => {
  click(S.menu.open);
  fireEvent.click(within(screen.getByRole('dialog')).getByRole('button', { name: new RegExp(item) }));
};
const equalCard = () => screen.queryByRole('button', { name: new RegExp(S.trade.equalTitle) });

/** Start → n answers → (menu «My results» if not all) → «Both matter equally» on every trade-off → results. */
function toResults(n = TOTAL) {
  click(S.start.button);
  answer(n);
  if (n < TOTAL) menuTo(S.menu.results); // the last Next finishes by itself
  while (equalCard()) {
    fireEvent.click(equalCard()!);
    click(S.nav.next);
  }
  screen.getByRole('heading', { name: S.results.heading });
}

const fetchMock = vi.fn(async (url: string) => {
  const body = url.includes('quiz_bills') ? bills : url.includes('quiz_data') ? data : null;
  if (!body) return { ok: false, status: 404, json: async () => ({}) };
  return { ok: true, status: 200, json: async () => body };
});

beforeEach(async () => {
  window.scrollTo = vi.fn() as unknown as typeof window.scrollTo;
  fetchMock.mockClear();
  vi.stubGlobal('fetch', fetchMock);
  render(<App />);
  // both files arrive (the stub answers at once); let the dispatches settle
  await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
  await act(async () => { await new Promise((r) => setTimeout(r, 0)); });
});
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe('start', () => {
  it('shows the Figma home: title, chips with the number of questions asked, Start and Behind the results', () => {
    screen.getByRole('heading', { name: S.start.title });
    screen.getByText(S.start.chipStatements(TOTAL));
    click(S.start.howItWorks);
    screen.getByRole('heading', { name: S.methodology.heading });
    screen.getByRole('heading', { name: S.methodology.statementsHeading(data.statements.length) });
    click(S.methodology.back);
    screen.getByRole('button', { name: S.start.button });
  });

  it('fetches quiz_data, then quiz_bills, by their asset URLs, once', () => {
    expect(fetchMock.mock.calls.map((c) => String(c[0]).replace(/^.*\//, ''))).toEqual([
      expect.stringMatching(/^quiz_data.*\.json$/), expect.stringMatching(/^quiz_bills.*\.json$/),
    ]);
  });
});

describe('statements', () => {
  it('four answers as in Figma; a tap selects, Next (inactive until then) advances; Back shows it selected', () => {
    click(S.start.button);
    screen.getByText(S.question.progress(1, TOTAL));
    screen.getByRole('heading', { name: first.statement_en });
    const group = screen.getByRole('group', { name: S.question.answersLabel });
    expect(within(group).getAllByRole('button').map((b) => b.textContent))
      .toEqual(['Strongly agree', 'Agree', 'Disagree', 'Strongly disagree']);
    expect(screen.getByRole('button', { name: S.nav.next })).toHaveProperty('disabled', true);
    click(S.answers[1]);
    expect(pressed()).toEqual([S.answers[1]]);
    screen.getByText(S.question.progress(1, TOTAL));
    click(S.nav.next);
    screen.getByText(S.question.progress(2, TOTAL));
    expect(pressed()).toEqual([]);
    click(S.nav.back);
    screen.getByRole('heading', { name: first.statement_en });
    expect(pressed()).toEqual([S.answers[1]]);
  });

  it('the core statements come first, in the exported order, then the clarifying ones chosen by the engine', () => {
    click(S.start.button);
    const exp = expected(TOTAL);
    for (let i = 0; i < TOTAL; i++) {
      screen.getByText(S.question.progress(i + 1, TOTAL));
      screen.getByRole('heading', { name: statementOf(core, data, exp.shown[i]!)!.statement_en });
      click(S.answers[SEQ[i % SEQ.length]!]);
      click(S.nav.next);
    }
    expect(screen.queryByText(S.loading)).toBeNull();
    expect(screen.queryByRole('heading', { name: S.trade.title }) ?? screen.queryByRole('heading', { name: S.results.heading }))
      .not.toBeNull();
  });

  it('Skip moves on without an answer', () => {
    click(S.start.button);
    click(S.question.skip);
    screen.getByText(S.question.progress(2, TOTAL));
    click(S.nav.back);
    expect(pressed()).toEqual([]);
  });

  it('menu «My results» without answers shows the notice and stays', () => {
    click(S.start.button);
    click(S.question.skip);
    menuTo(S.menu.results);
    screen.getByText(S.question.noAnswers);
    screen.getByText(S.question.progress(2, TOTAL));
  });
});

describe('trade-offs', () => {
  it('Figma «clarifying question»: A / B / equal, Next after a choice, Back undoes; the list is never named', () => {
    click(S.start.button);
    answer(TOTAL);
    expect(screen.queryByRole('heading', { name: S.trade.title })).not.toBeNull(); // these answers produce a pair
    screen.getByText(S.trade.counter(1, core.flow.trade));
    const text = document.body.textContent!;
    for (const l of data.lists) expect(text).not.toContain(l.name_en);
    const next = screen.getByRole('button', { name: S.nav.next });
    expect(next).toHaveProperty('disabled', true);
    const [cardA] = within(screen.getByRole('group', { name: S.trade.title })).getAllByRole('button');
    const titleA = cardA!.textContent;
    fireEvent.click(cardA!);
    expect(next).toHaveProperty('disabled', false);
    click(S.nav.next);
    if (screen.queryByRole('heading', { name: S.trade.title })) {
      screen.getByText(S.trade.counter(2, core.flow.trade));
      click(S.nav.back);
      screen.getByText(S.trade.counter(1, core.flow.trade));
      expect(within(screen.getByRole('group', { name: S.trade.title })).getAllByRole('button')[0]!.textContent)
        .toBe(titleA);
    }
  });
});

describe('results', () => {
  it('rows follow the engine ranking with closeness to one decimal', () => {
    toResults();
    const rows = match(data, expected(TOTAL).answers, {});
    const ranked = rows.filter((r) => r.ranked);
    const items = within(screen.getAllByRole('list')[0]!).getAllByRole('listitem');
    expect(items).toHaveLength(ranked.length);
    // Trade-offs answered «Equally» change no weights, so the plain ranking applies.
    ranked.forEach((r, i) => {
      expect(items[i]!.textContent).toContain(r.name_en);
      expect(items[i]!.textContent).toContain(formatCloseness(r.closeness!));
    });
    screen.getByText(S.results.basedOn(TOTAL, false));
  });

  it('shows only the two allowed notes and nothing about government, coalition or seats', () => {
    toResults();
    const text = document.body.textContent!.toLowerCase();
    for (const w of ['coalition', 'opposition', 'government', 'seats', 'mandat']) expect(text).not.toContain(w);
    for (const el of document.querySelectorAll('.note')) {
      expect(el.textContent).toMatch(/^(few former MKs: \d+)?(; )?(position known for only \d+% of your answers)?$/);
    }
    expect(document.querySelectorAll('.screen img')).toHaveLength(0); // no logos (only the header's menu icon)
  });

  it('«Answer more questions» continues with a new statement beyond the fixed count', () => {
    toResults();
    click(S.results.answerMore);
    screen.getByText(S.question.progressMore(TOTAL + 1));
    const exp = expected(TOTAL);
    for (const q of exp.shown) expect(screen.queryByRole('heading', { name: statementOf(core, data, q)!.statement_en })).toBeNull();
  });

  it('row → details → bills; Hebrew titles are dir=auto, lang=he; bill links go to the Knesset site', () => {
    toResults();
    const firstRow = within(screen.getAllByRole('list')[0]!).getAllByRole('button')[0]!;
    fireEvent.click(firstRow);
    screen.getByRole('button', { name: S.details.back });
    const card = document.querySelector('button.card') as HTMLButtonElement | null;
    expect(card).not.toBeNull();
    fireEvent.click(card!);
    screen.getByRole('button', { name: S.bills.back });
    for (const t of document.querySelectorAll('.bill-title')) {
      expect(t.getAttribute('dir')).toBe('auto');
      expect(t.getAttribute('lang')).toBe('he');
    }
    for (const a of screen.queryAllByRole('link')) {
      expect(a.getAttribute('href')).toMatch(/^https:\/\/main\.knesset\.gov\.il\/.*lawitemid=\d+$/);
    }
    click(S.bills.back);
    click(S.details.back);
    screen.getByRole('heading', { name: S.results.heading });
  });

  it('Start over clears answers', () => {
    toResults();
    click(S.results.startOver);
    click(S.start.button);
    expect(pressed()).toEqual([]);
  });
});

describe('accessibility', () => {
  it('focus moves to the new screen heading', () => {
    expect(document.activeElement).toBe(document.body); // not on the first render
    click(S.start.button);
    expect(document.activeElement).toBe(screen.getByRole('heading', { name: first.statement_en }));
    click(S.answers[2]);
    click(S.nav.next);
    const second = statementOf(core, null, core.core[1]!)!;
    expect(document.activeElement).toBe(screen.getByRole('heading', { name: second.statement_en }));
  });

  it('menu is a dialog: focus on Close, Escape closes', () => {
    click(S.menu.open);
    const dialog = screen.getByRole('dialog');
    expect(document.activeElement).toBe(within(dialog).getByRole('button', { name: S.menu.close }));
    fireEvent.keyDown(document, { key: 'Escape' });
    expect(screen.queryByRole('dialog')).toBeNull();
  });

  it('closeness has a spoken label; external links say they open a new tab', () => {
    toResults();
    const row = within(screen.getAllByRole('list')[0]!).getAllByRole('button')[0]!;
    expect(row.textContent).toContain(S.results.closenessLabel);
    fireEvent.click(row);
    const card = [...document.querySelectorAll('button.card')].find((c) => /sponsored by/.test(c.textContent!));
    fireEvent.click(card as HTMLElement);
    const links = screen.getAllByRole('link');
    expect(links.length).toBeGreaterThan(0);
    for (const a of links) {
      expect(a.textContent).toContain(S.a11y.newTab);
      expect(a.getAttribute('rel')).toContain('noreferrer');
    }
  });
});

describe('privacy', () => {
  it('nothing is stored and the URL never changes', () => {
    const href = window.location.href;
    const setLocal = vi.spyOn(Storage.prototype, 'setItem');
    toResults(TOTAL);
    const firstRow = within(screen.getAllByRole('list')[0]!).getAllByRole('button')[0]!;
    fireEvent.click(firstRow);
    expect(setLocal).not.toHaveBeenCalled();
    expect(document.cookie).toBe('');
    expect(window.location.href).toBe(href);
  });
});

describe('loading', () => {
  it('a screen whose file has not arrived shows the loader, then the screen once it arrives', async () => {
    cleanup();
    let release: (() => void) | null = null;
    const slow = vi.fn(async (url: string) => {
      if (url.includes('quiz_bills')) await new Promise<void>((r) => { release = r; });
      return { ok: true, status: 200, json: async () => (url.includes('quiz_bills') ? bills : data) };
    });
    vi.stubGlobal('fetch', slow);
    render(<App />);
    await waitFor(() => expect(slow).toHaveBeenCalledTimes(2));
    await act(async () => { await new Promise((r) => setTimeout(r, 0)); });
    toResults();
    fireEvent.click(within(screen.getAllByRole('list')[0]!).getAllByRole('button')[0]!);
    screen.getByRole('status');
    screen.getByText(S.loading);
    await act(async () => { release!(); await new Promise((r) => setTimeout(r, 0)); });
    screen.getByRole('button', { name: S.details.back });
  });
});
