// @vitest-environment jsdom
/**
 * Screen tests: the whole flow through <App/> as a user clicks it, plus the SPEC «never show / never store» rules.
 * Numbers themselves are covered by the golden tests; here only what reaches the screen.
 */
import { cleanup, fireEvent, render, screen, within } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import App from '../App';
import { data } from '../data';
import { formatCloseness } from '../engine/format';
import { match } from '../engine/match';
import { S } from '../strings';

const click = (name: string | RegExp) => fireEvent.click(screen.getByRole('button', { name }));
const pressed = () => screen.queryAllByRole('button', { pressed: true }).map((b) => b.textContent);

const SEQ = [2, -1, 1, -2] as const;

/** Answers the first n statements (answer + Next) with a fixed pattern; stops on statement n + 1. */
function answer(n: number) {
  for (let i = 0; i < n; i++) {
    click(S.answers[SEQ[i % SEQ.length]!]);
    click(S.nav.next);
  }
}

const menuTo = (item: string) => {
  click(S.menu.open);
  fireEvent.click(within(screen.getByRole('dialog')).getByRole('button', { name: new RegExp(item) }));
};
const equalCard = () => screen.queryByRole('button', { name: new RegExp(S.trade.equalTitle) });

/** Start → n answers → (menu «My results» if not all) → «Both matter equally» on every trade-off → results. */
function toResults(n = 20) {
  click(S.start.button);
  answer(n);
  if (n < data.statements.length) menuTo(S.menu.results); // the last Next finishes by itself
  while (equalCard()) {
    fireEvent.click(equalCard()!);
    click(S.nav.next);
  }
  screen.getByRole('heading', { name: S.results.heading });
}

beforeEach(() => {
  window.scrollTo = vi.fn() as unknown as typeof window.scrollTo;
  render(<App />);
});
afterEach(cleanup);

describe('start', () => {
  it('shows the Figma home: title, chips with the real statement count, Start and Behind the results', () => {
    screen.getByRole('heading', { name: S.start.title });
    screen.getByText(S.start.chipStatements(data.statements.length));
    click(S.start.howItWorks);
    screen.getByRole('heading', { name: S.methodology.heading });
    click(S.methodology.back);
    screen.getByRole('button', { name: S.start.button });
  });
});

describe('statements', () => {
  it('four answers as in Figma; a tap selects, Next (inactive until then) advances; Back shows it selected', () => {
    click(S.start.button);
    screen.getByText(S.question.progress(1, data.statements.length));
    screen.getByRole('heading', { name: data.statements[0]!.statement_en });
    const group = screen.getByRole('group', { name: S.question.answersLabel });
    expect(within(group).getAllByRole('button').map((b) => b.textContent))
      .toEqual(['Strongly agree', 'Agree', 'Disagree', 'Strongly disagree']);
    expect(screen.getByRole('button', { name: S.nav.next })).toHaveProperty('disabled', true);
    click(S.answers[1]);
    expect(pressed()).toEqual([S.answers[1]]);
    screen.getByText(S.question.progress(1, data.statements.length));
    click(S.nav.next);
    screen.getByText(S.question.progress(2, data.statements.length));
    expect(pressed()).toEqual([]);
    click(S.nav.back);
    screen.getByRole('heading', { name: data.statements[0]!.statement_en });
    expect(pressed()).toEqual([S.answers[1]]);
  });

  it('Skip moves on without an answer', () => {
    click(S.start.button);
    click(S.question.skip);
    screen.getByText(S.question.progress(2, data.statements.length));
    click(S.nav.back);
    expect(pressed()).toEqual([]);
  });

  it('menu «My results» without answers shows the notice and stays', () => {
    click(S.start.button);
    click(S.question.skip);
    menuTo(S.menu.results);
    screen.getByText(S.question.noAnswers);
    screen.getByText(S.question.progress(2, data.statements.length));
  });
});

describe('trade-offs', () => {
  it('Figma «clarifying question»: A / B / equal, Next after a choice, Back undoes; the list is never named', () => {
    click(S.start.button);
    answer(30);
    menuTo(S.menu.results);
    expect(screen.queryByRole('heading', { name: S.trade.title })).not.toBeNull(); // these answers produce a pair
    screen.getByText(S.trade.counter(1, data.params.MAX_TRADE));
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
      screen.getByText(S.trade.counter(2, data.params.MAX_TRADE));
      click(S.nav.back);
      screen.getByText(S.trade.counter(1, data.params.MAX_TRADE));
      expect(within(screen.getByRole('group', { name: S.trade.title })).getAllByRole('button')[0]!.textContent)
        .toBe(titleA);
    }
  });
});

describe('results', () => {
  it('rows follow the engine ranking with formatted closeness', () => {
    toResults();
    const rows = match(data, Object.fromEntries(
      data.statements.slice(0, 20).map((s, i) => [s.q, SEQ[i % SEQ.length]!]),
    ), {});
    const ranked = rows.filter((r) => r.ranked);
    const items = within(screen.getAllByRole('list')[0]!).getAllByRole('listitem');
    expect(items).toHaveLength(ranked.length);
    // Trade-offs answered «Equally» change no weights, so the plain ranking applies.
    ranked.forEach((r, i) => {
      expect(items[i]!.textContent).toContain(r.name_en);
      expect(items[i]!.textContent).toContain(formatCloseness(r.closeness!));
    });
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

  it('row → details → bills; Hebrew titles are dir=auto, lang=he', () => {
    toResults();
    const first = within(screen.getAllByRole('list')[0]!).getAllByRole('button')[0]!;
    fireEvent.click(first);
    screen.getByRole('button', { name: S.details.back });
    const card = document.querySelector('button.card') as HTMLButtonElement | null;
    expect(card).not.toBeNull();
    fireEvent.click(card!);
    screen.getByRole('button', { name: S.bills.back });
    for (const t of document.querySelectorAll('.bill-title')) {
      expect(t.getAttribute('dir')).toBe('auto');
      expect(t.getAttribute('lang')).toBe('he');
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
    expect(document.activeElement).toBe(screen.getByRole('heading', { name: data.statements[0]!.statement_en }));
    click(S.answers[2]);
    click(S.nav.next);
    expect(document.activeElement).toBe(screen.getByRole('heading', { name: data.statements[1]!.statement_en }));
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
    toResults(65);
    const first = within(screen.getAllByRole('list')[0]!).getAllByRole('button')[0]!;
    fireEvent.click(first);
    expect(setLocal).not.toHaveBeenCalled();
    expect(document.cookie).toBe('');
    expect(window.location.href).toBe(href);
  });
});
