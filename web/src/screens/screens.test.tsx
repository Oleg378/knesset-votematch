// @vitest-environment jsdom
/**
 * Screen tests: the whole flow through <App/> as a user clicks it, plus the SPEC «never show / never store» rules and the
 * v2 loading rules (the start page never waits; a screen whose file has not arrived shows a loader).
 * Numbers themselves are covered by the golden tests; here only what reaches the screen.
 */
import { act, cleanup, fireEvent, render, screen, within } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import App from '../App';
import type { Loader, Sources } from '../data';
import { formatCloseness } from '../engine/format';
import { match } from '../engine/match';
import type { Answers } from '../engine/types';
import { S } from '../strings';
import { bills, core, data, loaded } from '../testSources';

const click = (name: string | RegExp) => fireEvent.click(screen.getByRole('button', { name }));
const pressed = () => screen.queryAllByRole('button', { pressed: true }).map((b) => b.textContent);
const planned = data.flow.core + data.flow.clarify;
const byText = new Map(data.statements.map((s) => [s.statement_en, s.q]));
const firstCore = data.statements.find((s) => s.q === data.core[0])!;

const SEQ = [2, -1, 1, -2] as const;
/** What was answered on screen so far (statement → answer). */
let given: Answers = {};

/** Answers the next n statements shown (answer + Next) with a fixed pattern. */
function answer(n: number) {
  for (let i = 0; i < n; i++) {
    const q = byText.get(screen.getByRole('heading', { level: 2 }).textContent!)!;
    const a = SEQ[i % SEQ.length]!;
    given[q] = a;
    click(S.answers[a]);
    click(S.nav.next);
  }
}

const menuTo = (item: string) => {
  click(S.menu.open);
  fireEvent.click(within(screen.getByRole('dialog')).getByRole('button', { name: new RegExp(item) }));
};
const equalCard = () => screen.queryByRole('button', { name: new RegExp(S.trade.equalTitle) });

/** Start → n answers → (menu «My results» if fewer than planned) → «Both matter equally» on every trade-off → results. */
function toResults(n = planned) {
  click(S.start.button);
  answer(n);
  if (n < planned) menuTo(S.menu.results); // the last planned Next finishes by itself
  while (equalCard()) {
    fireEvent.click(equalCard()!);
    click(S.nav.next);
  }
  screen.getByRole('heading', { name: S.results.heading });
}

/** A loader whose files arrive when the test says so. */
function manualLoader() {
  let state: Sources = { core: null, data: null, bills: null, failed: false };
  const ls = new Set<() => void>();
  const loader: Loader = {
    get: () => state,
    subscribe: (f) => {
      ls.add(f);
      return () => ls.delete(f);
    },
    start: () => {},
  };
  const arrive = (patch: Partial<Sources>) => act(() => {
    state = { ...state, ...patch };
    ls.forEach((f) => f());
  });
  return { loader, arrive };
}

beforeEach(() => {
  window.scrollTo = vi.fn() as unknown as typeof window.scrollTo;
  given = {};
});
afterEach(cleanup);

describe('start', () => {
  beforeEach(() => render(<App loader={loaded()} />));

  it('shows the Figma home: title, chips with the planned number of statements, Start and Behind the results', () => {
    screen.getByRole('heading', { name: S.start.title });
    screen.getByText(S.start.chipStatements(planned));
    screen.getByText(S.start.chipTime);
    screen.getByText(S.start.steps(planned)[0]!);
    click(S.start.howItWorks);
    screen.getByRole('heading', { name: S.methodology.heading });
    click(S.methodology.back);
    screen.getByRole('button', { name: S.start.button });
  });
});

describe('loading (V2_HANDOFF «Loading»)', () => {
  it('the start page renders before any data; Start waits for quiz_core, then the first core statement', () => {
    const { loader, arrive } = manualLoader();
    render(<App loader={loader} />);
    screen.getByRole('heading', { name: S.start.title });
    screen.getByRole('button', { name: S.start.button });
    expect(screen.queryByText(S.start.chipStatements(planned))).toBeNull();
    click(S.start.button);
    // The dot ring (customer 2026-10-18): 5 uniform rings, 230 dots, and the running blue dot.
    expect(screen.getByRole('status').querySelectorAll('svg circle')).toHaveLength(231);
    screen.getByText(S.loading);
    arrive({ core });
    screen.getByRole('heading', { name: firstCore.statement_en });
  });

  it('the first clarifying question waits for quiz_data; list details wait for quiz_bills', () => {
    const { loader, arrive } = manualLoader();
    render(<App loader={loader} />);
    arrive({ core });
    click(S.start.button);
    answer(data.flow.core);
    screen.getByRole('status');
    arrive({ data });
    screen.getByText(S.question.progress(data.flow.core + 1, planned));
    answer(data.flow.clarify);
    while (equalCard()) {
      fireEvent.click(equalCard()!);
      click(S.nav.next);
    }
    fireEvent.click(within(screen.getAllByRole('list')[0]!).getAllByRole('button')[0]!);
    screen.getByRole('status');
    arrive({ bills });
    screen.getByRole('button', { name: S.details.back });
  });

  it('a failed file shows an error with a reload button on the screen that needs it', () => {
    const { loader, arrive } = manualLoader();
    render(<App loader={loader} />);
    arrive({ failed: true });
    screen.getByRole('heading', { name: S.start.title });
    click(S.start.button);
    screen.getByRole('alert');
    screen.getByRole('button', { name: S.reload });
  });
});

describe('statements', () => {
  beforeEach(() => render(<App loader={loaded()} />));

  it('four answers as in Figma; a tap selects, Next (inactive until then) advances; Back shows it selected', () => {
    click(S.start.button);
    screen.getByText(S.question.progress(1, planned));
    screen.getByRole('heading', { name: firstCore.statement_en });
    const group = screen.getByRole('group', { name: S.question.answersLabel });
    expect(within(group).getAllByRole('button').map((b) => b.textContent))
      .toEqual(['Strongly agree', 'Agree', 'Disagree', 'Strongly disagree']);
    expect(screen.getByRole('button', { name: S.nav.next })).toHaveProperty('disabled', true);
    click(S.answers[1]);
    expect(pressed()).toEqual([S.answers[1]]);
    screen.getByText(S.question.progress(1, planned));
    click(S.nav.next);
    screen.getByText(S.question.progress(2, planned));
    expect(pressed()).toEqual([]);
    click(S.nav.back);
    screen.getByRole('heading', { name: firstCore.statement_en });
    expect(pressed()).toEqual([S.answers[1]]);
  });

  it('Skip moves on without an answer', () => {
    click(S.start.button);
    click(S.question.skip);
    screen.getByText(S.question.progress(2, planned));
    click(S.nav.back);
    expect(pressed()).toEqual([]);
  });

  it('menu «My results» without answers shows the notice and stays', () => {
    click(S.start.button);
    click(S.question.skip);
    menuTo(S.menu.results);
    screen.getByText(S.question.noAnswers);
    screen.getByText(S.question.progress(2, planned));
  });

  it('after the planned number of statements the questions end by themselves', () => {
    click(S.start.button);
    answer(planned);
    expect(screen.queryByRole('group', { name: S.question.answersLabel })).toBeNull();
  });
});

describe('trade-offs', () => {
  beforeEach(() => render(<App loader={loaded()} />));

  it('Figma «clarifying question»: A / B / equal, Next after a choice, Back undoes; the list is never named', () => {
    click(S.start.button);
    answer(planned);
    if (!screen.queryByRole('heading', { name: S.trade.title })) return; // these answers produced no pair
    screen.getByText(S.trade.counter(1, data.flow.trade));
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
      screen.getByText(S.trade.counter(2, data.flow.trade));
      click(S.nav.back);
      screen.getByText(S.trade.counter(1, data.flow.trade));
      expect(within(screen.getByRole('group', { name: S.trade.title })).getAllByRole('button')[0]!.textContent)
        .toBe(titleA);
    }
  });
});

describe('results', () => {
  beforeEach(() => render(<App loader={loaded()} />));

  it('rows follow the engine ranking with formatted closeness', () => {
    toResults();
    const ranked = match(data, given, {}).filter((r) => r.ranked);
    const items = within(screen.getAllByRole('list')[0]!).getAllByRole('listitem');
    expect(items).toHaveLength(ranked.length);
    // Trade-offs answered «Equally» change no weights, so the plain ranking applies.
    ranked.forEach((r, i) => {
      expect(items[i]!.textContent).toContain(r.name_en);
      expect(items[i]!.textContent).toContain(formatCloseness(r.closeness!));
    });
  });

  it('«Answer more questions» continues with a new statement, counted out of all statements', () => {
    toResults();
    click(S.results.answerMore);
    screen.getByRole('group', { name: S.question.answersLabel });
    screen.getByText(S.question.progress(planned + 1, data.statements.length));
    answer(1);
    menuTo(S.menu.results);
    screen.getByRole('heading', { name: S.results.heading });
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

  it('row → details → bills; Hebrew titles are dir=auto, lang=he; links built from BILL_URL', () => {
    toResults();
    const first = within(screen.getAllByRole('list')[0]!).getAllByRole('button')[0]!;
    fireEvent.click(first);
    screen.getByRole('button', { name: S.details.back });
    const card = [...document.querySelectorAll('button.card')].find((c) => /sponsored by/.test(c.textContent!));
    expect(card).toBeDefined();
    fireEvent.click(card as HTMLElement);
    screen.getByRole('button', { name: S.bills.back });
    for (const t of document.querySelectorAll('.bill-title')) {
      expect(t.getAttribute('dir')).toBe('auto');
      expect(t.getAttribute('lang')).toBe('he');
    }
    const prefix = data.params.BILL_URL.split('{id}')[0]!;
    for (const a of screen.getAllByRole('link')) expect(a.getAttribute('href')!.startsWith(prefix)).toBe(true);
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
  beforeEach(() => render(<App loader={loaded()} />));

  it('focus moves to the new screen heading', () => {
    expect(document.activeElement).toBe(document.body); // not on the first render
    click(S.start.button);
    expect(document.activeElement).toBe(screen.getByRole('heading', { name: firstCore.statement_en }));
    click(S.answers[2]);
    click(S.nav.next);
    expect(document.activeElement).toBe(screen.getByRole('heading', { level: 2 }));
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
  beforeEach(() => render(<App loader={loaded()} />));

  it('nothing is stored and the URL never changes', () => {
    const href = window.location.href;
    const setLocal = vi.spyOn(Storage.prototype, 'setItem');
    toResults();
    const first = within(screen.getAllByRole('list')[0]!).getAllByRole('button')[0]!;
    fireEvent.click(first);
    expect(setLocal).not.toHaveBeenCalled();
    expect(document.cookie).toBe('');
    expect(window.location.href).toBe(href);
  });
});
