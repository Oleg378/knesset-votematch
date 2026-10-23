// @vitest-environment jsdom
/**
 * Screen tests: the whole flow through <App/> as a user clicks it, plus the SPEC «never show / never store» rules and the
 * the loading rules of export/WEB_CONTRACT.md §1 (the start page never waits; a screen whose file has not arrived shows a loader).
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
import { dataValues, fill, listsOf, T } from '../texts';
import { HIGHLIGHT } from '../uiConstants';

const methodology = T.methodology;

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
    screen.getByRole('heading', { name: methodology.heading });
    click(methodology.back);
    screen.getByRole('button', { name: S.start.button });
  });

  it('every text comes from quiz_texts.json: the title, the eyebrow and the steps with {n} and {top} filled', () => {
    screen.getByRole('heading', { name: T.start.title });
    screen.getByText(T.app.eyebrow);
    screen.getByText(T.start.tagline);
    const steps = T.start.steps.map((s) => fill(s, { n: planned, top: HIGHLIGHT }));
    expect(steps.join(' ')).not.toMatch(/[{}]/);
    expect(screen.getAllByRole('listitem').map((li) => li.textContent)).toEqual(
      expect.arrayContaining(steps.map((s, i) => `${i + 1}${s}`)));
    screen.getByText(fill(T.start.chipStatements, { n: planned }));
    expect(document.body.textContent).not.toMatch(/[{}]/);
  });
});

describe('methodology (WEB_CONTRACT §7: every text from quiz_texts.json)', () => {
  it('shows the file\'s heading, every section as a card with its title and leads, and the numbers filled from quiz_data', () => {
    render(<App loader={loaded()} />);
    click(S.start.howItWorks);
    screen.getByRole('heading', { name: methodology.heading });
    const v = dataValues(data);
    const open = methodology.sections.filter((s) => !s.collapsed);
    expect(open.length).toBeGreaterThan(0);
    for (const s of open) {
      // every section is a card (the panel of the question card): its title, its bullets and its closing paragraph in it
      const card = screen.getByText(fill(s.title, v), { exact: false }).closest('.panel');
      expect(card).not.toBeNull();
      expect(within(card as HTMLElement).queryByRole('button', { name: s.title })).toBeNull(); // open, no head to press
      for (const b of s.bullets ?? []) within(card as HTMLElement).getByText(fill(b.lead, v), { exact: false });
      if (s.after !== undefined) within(card as HTMLElement).getByText(fill(s.after, v));
    }
    // a bullet reads as one sentence: its lead, a space, its text
    expect(document.querySelector('.screen')!.textContent).toContain(`${v.evaluable} of ${v.lists} lists can be evaluated`);
    // the statements block is a card too: its heading, then (once opened, if collapsed) a row per statement; the data
    // line under it, outside
    const name = fill(methodology.statements.heading, { statements: data.statements.length });
    const statements = screen.getByRole('heading', { name }).closest('.panel') as HTMLElement;
    expect(statements).not.toBeNull();
    if (methodology.statements.collapsed) fireEvent.click(within(statements).getByRole('button', { name: S.results.seeAll }));
    expect(statements.querySelectorAll('.method-rows .accordion')).toHaveLength(data.statements.length);
    const dataLine = screen.getByText(fill(methodology.statements.dataVersion, { generated: data.generated, commit: data.source_commit }));
    expect(dataLine.closest('.panel')).toBeNull();
    expect(document.querySelectorAll('.screen .panel')).toHaveLength(methodology.sections.length + 1);
    expect(document.body.textContent).not.toMatch(/[{}]/);
  });

  it('reference cards (`collapsed`) start closed with «See all» under the title, the content drops down, «Show less» closes it', () => {
    render(<App loader={loaded()} />);
    click(S.start.howItWorks);
    const v = dataValues(data);
    const folded = methodology.sections.filter((s) => s.collapsed);
    expect(folded.map((s) => s.title)).toEqual(['How topics are chosen.', 'Important topics that are not in the quiz, and why']);
    expect(methodology.statements.collapsed).toBe(true);
    const shown = (card: HTMLElement, s: (typeof folded)[number]) => {
      if (s.text !== undefined) within(card).getByText(fill(s.text, v));
      for (const b of s.bullets ?? []) within(card).getByText(fill(b.lead, v), { exact: false });
      if (s.after !== undefined) within(card).getByText(fill(s.after, v));
    };
    const hidden = (card: HTMLElement, s: (typeof folded)[number]) => {
      for (const b of s.bullets ?? []) expect(within(card).queryByText(fill(b.lead, v), { exact: false })).toBeNull();
      if (s.after !== undefined) expect(within(card).queryByText(fill(s.after, v))).toBeNull();
    };
    for (const s of folded) {
      const card = screen.getByText(s.title).closest('.panel') as HTMLElement;
      // the title is not a button; the only control is «See all»
      expect(within(card).queryByRole('button', { name: s.title })).toBeNull();
      hidden(card, s);
      const more = within(card).getByRole('button', { name: S.results.seeAll });
      expect(more.getAttribute('aria-expanded')).toBe('false');
      expect(within(card).getAllByRole('button')).toEqual([more]);
      fireEvent.click(more);
      shown(card, s);
      const less = within(card).getByRole('button', { name: S.results.seeLess });
      expect(less.getAttribute('aria-expanded')).toBe('true');
      expect(document.getElementById(less.getAttribute('aria-controls')!)!.contains(less)).toBe(true);
      expect(within(card).queryByRole('button', { name: S.results.seeAll })).toBeNull();
      fireEvent.click(less);
      hidden(card, s);
      expect(document.activeElement).toBe(within(card).getByRole('button', { name: S.results.seeAll }));
    }
    // the statements block: its heading as on an open card, the rows drop down with «See all»
    const name = fill(methodology.statements.heading, { statements: data.statements.length });
    const card = screen.getByRole('heading', { level: 2, name }).closest('.panel') as HTMLElement;
    expect(within(card).queryByRole('button', { name })).toBeNull();
    expect(card.querySelectorAll('.method-rows .accordion')).toHaveLength(0);
    fireEvent.click(within(card).getByRole('button', { name: S.results.seeAll }));
    expect(card.querySelectorAll('.method-rows .accordion')).toHaveLength(data.statements.length);
    within(card).getByRole('button', { name: data.statements[0]!.title_en });
    fireEvent.click(within(card).getByRole('button', { name: S.results.seeLess }));
    expect(card.querySelectorAll('.method-rows .accordion')).toHaveLength(0);
    within(card).getByRole('button', { name: S.results.seeAll });
  });

  it('«Which lists have a record»: the bullets with the numbers, the lists with no record dropping down in its card', () => {
    render(<App loader={loaded()} />);
    click(S.start.howItWorks);
    const v = dataValues(data);
    const section = methodology.sections.find((s) => s.lists)!;
    expect(section.title).toBe('Which lists have a record.');
    const card = screen.getByText(section.title).closest('.panel') as HTMLElement;
    expect(card).not.toBeNull();
    for (const b of section.bullets!) within(card).getByText(fill(b.lead, v), { exact: false });
    within(card).getByText(`${v.single} ${v.single === 1 ? 'list' : 'lists'} with a single former member`, { exact: false });
    // the lists: those with no former member of the Knesset, in the order of quiz_data
    expect(section.lists!.of).toBe('no_record');
    const names = data.lists.filter((l) => l.status === 'not_evaluated').map((l) => l.name_en);
    expect(names.length).toBe(v.no_record);
    expect(listsOf(data, 'no_record').map((l) => l.name_en)).toEqual(names);
    expect(names.length).toBeGreaterThan(HIGHLIGHT);
    // the line that names them is the last bullet of the card, with the count from the data
    const line = fill(section.lists!.title, { n: names.length });
    expect(line).toBe(`${names.length} lists have no record and are not shown in the results.`);
    const bullets = within(card).getAllByRole('listitem').filter((li) => li.closest('.method-bullets'));
    expect(bullets).toHaveLength(section.bullets!.length + 1);
    expect(bullets.at(-1)!.textContent).toBe(line);
    const shown = () => within(card).getAllByRole('list', { name: line }).flatMap((ul) =>
      within(ul).getAllByRole('listitem').map((li) => li.textContent));
    expect(shown()).toEqual(names.slice(0, HIGHLIGHT));
    expect(within(card).queryByRole('button', { name: S.results.seeLess })).toBeNull();
    const more = within(card).getByRole('button', { name: S.results.seeAll });
    expect(more.getAttribute('aria-expanded')).toBe('false');
    // nothing to press per list: the only buttons of the card are «See all» / «Show less»
    expect(within(card).getAllByRole('button')).toEqual([more]);
    fireEvent.click(more);
    expect(shown()).toEqual(names);
    expect(within(card).queryByRole('button', { name: S.results.seeAll })).toBeNull();
    const less = within(card).getByRole('button', { name: S.results.seeLess });
    expect(card.querySelector('.list-names-drop > :last-child')!.contains(less)).toBe(true);
    fireEvent.click(less);
    expect(shown()).toEqual(names.slice(0, HIGHLIGHT));
    expect(card.querySelector('.list-names-drop')).toBeNull();
    expect(document.activeElement).toBe(within(card).getByRole('button', { name: S.results.seeAll }));
    expect(document.body.textContent).not.toMatch(/[{}]/);
  });

  it('waits for quiz_bills only (its texts are bundled)', () => {
    const { loader, arrive } = manualLoader();
    render(<App loader={loader} />);
    arrive({ core, data });
    click(S.start.howItWorks);
    screen.getByText(S.loading);
    arrive({ bills });
    screen.getByRole('heading', { name: methodology.heading });
  });
});

describe('loading (WEB_CONTRACT «Loading»)', () => {
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

  it('rows follow the engine ranking with formatted closeness; the five closest in the highlighted panel', () => {
    toResults();
    const ranked = match(data, given, {}).filter((r) => r.ranked);
    expect(document.querySelectorAll('.screen ol > li')).toHaveLength(Math.min(5, ranked.length)); // the rest: «See all»
    click(S.results.seeAll);
    const items = [...document.querySelectorAll('.screen ol > li')] as HTMLElement[]; // the panel, then the rest
    expect(items).toHaveLength(ranked.length);
    expect(document.querySelectorAll('.scale-top li')).toHaveLength(Math.min(5, ranked.length));
    expect(document.querySelectorAll('.scale-top.open + .scale-drop ol > li')) // the rest drops down from the panel
      .toHaveLength(ranked.length - Math.min(5, ranked.length));
    screen.getByRole('list', { name: S.results.closest(Math.min(5, ranked.length)) }); // no visible title: named for screen readers
    // «See all» goes away, the focus goes to the first list that dropped down; «Show less» only at the end
    expect(screen.queryByRole('button', { name: S.results.seeAll })).toBeNull();
    expect(document.activeElement).toBe(document.querySelector('.scale-drop button'));
    const less = screen.getByRole('button', { name: S.results.seeLess });
    expect(less.getAttribute('aria-expanded')).toBe('true');
    expect(document.querySelector('.scale-drop > :last-child')!.contains(less)).toBe(true);
    // Trade-offs answered «Equally» change no weights, so the plain ranking applies.
    ranked.forEach((r, i) => {
      expect(items[i]!.textContent).toContain(r.name_en);
      expect(items[i]!.textContent).toContain(formatCloseness(r.closeness!));
    });
    // «Not ranked»: one reason in the divider, no note on each list
    screen.getByText(S.results.notRanked);
    expect(document.querySelectorAll('.scale-low li').length).toBeGreaterThan(0);
    expect(document.querySelectorAll('.scale-low .note')).toHaveLength(0);
    // lists with no record in the Knesset are not shown at all
    const none = match(data, given, {}).filter((r) => !r.evaluated);
    expect(none.length).toBeGreaterThan(0);
    none.forEach((r) => expect(document.querySelector('.screen')!.textContent).not.toContain(r.name_en));
    fireEvent.click(less);
    expect(document.querySelectorAll('.screen ol > li')).toHaveLength(Math.min(5, ranked.length));
    expect(document.querySelector('.scale-drop')).toBeNull();
    expect(document.activeElement).toBe(screen.getByRole('button', { name: S.results.seeAll })); // back to the panel
  });

  it('at the bottom only «Change answers»; it goes back to the statements', () => {
    toResults();
    const bottom = within(document.querySelector('.sticky-actions')!).getAllByRole('button');
    expect(bottom.map((b) => b.textContent)).toEqual([S.results.changeAnswers]);
    fireEvent.click(bottom[0]!);
    screen.getByRole('group', { name: S.question.answersLabel });
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
    menuTo(S.menu.startOver);
    click(S.start.button);
    expect(pressed()).toEqual([]);
  });

  it('Start over in the header, only on Results: clears answers and opens the first question, as Start on Home', () => {
    const inHeader = () => within(screen.getByRole('banner')).queryByRole('button', { name: S.menu.startOver });
    expect(inHeader()).toBeNull(); // Home
    toResults();
    fireEvent.click(inHeader()!);
    screen.getByRole('heading', { name: firstCore.statement_en });
    expect(inHeader()).toBeNull(); // a question
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

  it('menu is a dialog: focus on the dialog itself (no ring around Close), Escape closes', () => {
    click(S.menu.open);
    const dialog = screen.getByRole('dialog');
    expect(document.activeElement).toBe(dialog);
    expect(dialog.tabIndex).toBe(-1);
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
