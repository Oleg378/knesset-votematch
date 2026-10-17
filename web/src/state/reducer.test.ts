import { describe, expect, it } from 'vitest';
import goldenRaw from '@export/golden.v1.json';
import { data } from '../data';
import { tradeoffs } from '../engine/match';
import type { Answers, Mult, TradePair } from '../engine/types';
import { createReducer, initialState, type Action, type State } from './reducer';

const reducer = createReducer(data);
const run = (s: State, ...actions: Action[]) => actions.reduce(reducer, s);
const qs = data.statements.map((s) => s.q);
const N = qs.length;
const golden = goldenRaw as {
  cases: { name: string; answers: Answers; mult: Mult; tradeoffs: { pairs: TradePair[] } }[];
};
const full = golden.cases.find((c) => c.name === 'full')!;
const step2 = golden.cases.find((c) => c.name === 'full, adaptive step 2')!;

/** State on question i with the given answers. */
const at = (i: number, answers: Answers = {}): State => ({ ...initialState, answers, screen: { name: 'question', i } });

describe('reducer: statements', () => {
  it('Start opens the first statement', () => {
    expect(run(initialState, { type: 'START' }).screen).toEqual({ name: 'question', i: 0 });
  });

  it('an answer is selected (stays); Next advances; Next without an answer does nothing', () => {
    const s = run(at(0), { type: 'ANSWER', value: 2 });
    expect(s.answers).toEqual({ [qs[0]!]: 2 });
    expect(s.screen).toEqual({ name: 'question', i: 0 });
    expect(run(s, { type: 'ANSWER', value: -1 }).answers).toEqual({ [qs[0]!]: -1 });
    expect(run(s, { type: 'NEXT' }).screen).toEqual({ name: 'question', i: 1 });
    expect(run(at(0), { type: 'NEXT' })).toEqual(at(0));
  });

  it('Back keeps the previous answer (shown selected) and goes back; from the first statement to Start', () => {
    const s = run(at(0), { type: 'ANSWER', value: -1 }, { type: 'NEXT' }, { type: 'BACK' });
    expect(s.screen).toEqual({ name: 'question', i: 0 });
    expect(s.answers[qs[0]!]).toBe(-1);
    expect(run(s, { type: 'BACK' }).screen).toEqual({ name: 'start' });
  });

  it('Skip leaves the statement unanswered (removes an earlier answer) and advances', () => {
    const s = run(at(0, { [qs[0]!]: 1, [qs[1]!]: 'dk' }), { type: 'SKIP' });
    expect(s.answers).toEqual({ [qs[1]!]: 'dk' });
    expect(s.screen).toEqual({ name: 'question', i: 1 });
  });

  it("«don't know» is an answer, not a skip", () => {
    expect(run(at(3), { type: 'ANSWER', value: 'dk' }).answers).toEqual({ [qs[3]!]: 'dk' });
  });

  it('Finish without answers, or with only «don\'t know», shows the notice and stays', () => {
    const s = run(at(4), { type: 'FINISH' });
    expect(s.notice).toBe('noAnswers');
    expect(s.screen).toEqual({ name: 'question', i: 4 });
    const dk = run(at(4, { [qs[0]!]: 'dk' }), { type: 'FINISH' });
    expect(dk.notice).toBe('noAnswers');
    expect(run(dk, { type: 'BACK' }).notice).toBeNull();
  });

  it('Next on the last statement finishes', () => {
    const s = run(at(N - 1, { [qs[0]!]: 2, [qs[1]!]: -2 }), { type: 'ANSWER', value: 1 }, { type: 'NEXT' });
    expect(['tradeoff', 'results']).toContain(s.screen.name);
  });

  it('menu «My results» on a statement = Finish', () => {
    const s = run(at(10, full.answers), { type: 'SHOW_RESULTS' });
    expect(s.screen).toEqual(run(at(10, full.answers), { type: 'FINISH' }).screen);
    expect(run(at(4), { type: 'SHOW_RESULTS' }).notice).toBe('noAnswers');
  });
});

describe('reducer: trade-offs (as quiz_cli.exchange)', () => {
  it('first pair = tradeoffs()[0]; A doubles qa; next pair is adaptive (golden «full, adaptive step 2»)', () => {
    const s1 = run(at(10, full.answers), { type: 'FINISH' });
    expect(s1.screen).toEqual({ name: 'tradeoff', pair: full.tradeoffs.pairs[0] });
    const s2 = run(s1, { type: 'TRADE', choice: 'A' });
    expect(s2.mult).toEqual(step2.mult);
    expect(s2.done).toHaveLength(1);
    expect(s2.screen).toEqual({ name: 'tradeoff', pair: step2.tradeoffs.pairs[0] });
  });

  it('Back undoes the previous trade-off (weights restored, its pair asked again); from the first, to the statements', () => {
    const s1 = run(at(10, full.answers), { type: 'FINISH' });
    const s2 = run(s1, { type: 'TRADE', choice: 'A' });
    const back = run(s2, { type: 'BACK' });
    expect(back.screen).toEqual(s1.screen);
    expect(back.mult).toEqual({});
    expect(back.done).toEqual([]);
    expect(run(back, { type: 'BACK' }).screen).toEqual({ name: 'question', i: 10 });
  });

  it('menu «My results» on a trade-off skips the rest', () => {
    const s1 = run(at(10, full.answers), { type: 'FINISH' });
    expect(run(s1, { type: 'SHOW_RESULTS' }).screen).toEqual({ name: 'results' });
  });

  it('B doubles qb, «equally» changes nothing', () => {
    const s1 = run(at(10, full.answers), { type: 'FINISH' });
    const [, qb] = full.tradeoffs.pairs[0]!;
    expect(run(s1, { type: 'TRADE', choice: 'B' }).mult).toEqual({ [qb]: 2 });
    expect(run(s1, { type: 'TRADE', choice: '=' }).mult).toEqual({});
  });

  it('stops at MAX_TRADE or when no pair is left; statements and lists are not reused', () => {
    let s = run(at(10, full.answers), { type: 'FINISH' });
    let guard = 0;
    while (s.screen.name === 'tradeoff' && guard++ < 10) s = run(s, { type: 'TRADE', choice: '=' });
    expect(s.screen.name).toBe('results');
    expect(s.done.length).toBeLessThanOrEqual(data.params.MAX_TRADE);
    const used = s.done.flatMap((d) => [d.qa, d.qb]);
    expect(new Set(used).size).toBe(used.length);
    expect(new Set(s.done.map((d) => d.list)).size).toBe(s.done.length);
    // finishing again after «Change answers» asks nothing more once MAX_TRADE is reached or no pair remains
    const again = run(s, { type: 'CHANGE_ANSWERS' }, { type: 'FINISH' });
    if (s.done.length >= data.params.MAX_TRADE) expect(again.screen.name).toBe('results');
  });

  it('no pair at all: straight to results', () => {
    const answers = { [qs[0]!]: 2 } as Answers;
    expect(tradeoffs(data, answers)).toEqual([]);
    expect(run(at(5, answers), { type: 'FINISH' }).screen).toEqual({ name: 'results' });
  });
});

describe('reducer: results, details, bills, methodology', () => {
  const results: State = { ...initialState, answers: full.answers, screen: { name: 'results' } };
  const L = full.tradeoffs.pairs[0]![2];

  it('results → details → bills → back → back', () => {
    const d = run(results, { type: 'OPEN_DETAILS', list: L });
    expect(d.screen).toEqual({ name: 'details', list: L });
    const b = run(d, { type: 'OPEN_BILLS', q: '61' });
    expect(b.screen).toEqual({ name: 'bills', list: L, q: '61' });
    expect(run(b, { type: 'BACK' }).screen).toEqual({ name: 'details', list: L });
    expect(run(b, { type: 'BACK' }, { type: 'BACK' }).screen).toEqual({ name: 'results' });
  });

  it('Change answers keeps answers and trade-off weights and returns to the first statement', () => {
    const s = run({ ...results, mult: { '61': 2 } }, { type: 'CHANGE_ANSWERS' });
    expect(s.screen).toEqual({ name: 'question', i: 0 });
    expect(s.answers).toBe(full.answers);
    expect(s.mult).toEqual({ '61': 2 });
  });

  it('Start over clears everything', () => {
    const s = run({ ...results, mult: { '61': 2 }, done: [{ qa: '61', qb: '18', list: L, choice: 'A' }] },
      { type: 'START_OVER' });
    expect(s).toEqual(initialState);
  });

  it('methodology opens from any screen (menu) and returns there', () => {
    for (const from of [initialState, at(3), results, run(results, { type: 'OPEN_DETAILS', list: L }),
      run(at(10, full.answers), { type: 'FINISH' })]) {
      const m = run(from, { type: 'OPEN_METHODOLOGY' });
      expect(m.screen.name).toBe('methodology');
      expect(run(m, { type: 'BACK' }).screen).toEqual(from.screen);
    }
  });

  it('actions that do not belong to the current screen change nothing', () => {
    expect(run(initialState, { type: 'ANSWER', value: 2 })).toBe(initialState);
    expect(run(initialState, { type: 'TRADE', choice: 'A' })).toBe(initialState);
    expect(run(results, { type: 'START' })).toBe(results);
    expect(run(initialState, { type: 'SHOW_RESULTS' })).toBe(initialState);
  });
});
