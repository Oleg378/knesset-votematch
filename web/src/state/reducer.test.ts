import { describe, expect, it } from 'vitest';
import goldenRaw from '@export/golden.v2.json';
import { nextClarify } from '../engine/flow';
import { tradeoffs } from '../engine/match';
import type { Answer, Answers, Mult, TradePair } from '../engine/types';
import { core, data } from '../testSources';
import { createReducer, initialState, shownSoFar, type Action, type State } from './reducer';

const reducer = createReducer({ core, data });
const run = (s: State, ...actions: Action[]) => actions.reduce(reducer, s);
const golden = goldenRaw as {
  cases: { name: string; answers: Answers; mult: Mult; tradeoffs: { pairs: TradePair[] };
    flow?: { core: string[]; clarifying: string[] } }[];
};
const full = golden.cases.find((c) => c.name === 'full')!;
const step2 = golden.cases.find((c) => c.name === 'full, adaptive step 2')!;
const flow0 = golden.cases.find((c) => c.name === 'flow 0')!;
const C = data.core;
const planned = data.flow.core + data.flow.clarify;

/** State on shown[i] with the given answers (shown = the core). */
const at = (i: number, answers: Answers = {}): State => ({ ...initialState, answers, shown: [...C],
  screen: { name: 'question', i } });

/** Answers whatever is asked from `answers` (missing = Skip) until the screen is no longer a question. */
function answerAll(s: State, answers: Answers): State {
  let guard = 0;
  while (s.screen.name === 'question' && guard++ < 200) {
    const q = s.shown[s.screen.i]!;
    const a: Answer | undefined = answers[q];
    s = a === undefined ? run(s, { type: 'SKIP' }) : run(s, { type: 'ANSWER', value: a }, { type: 'NEXT' });
  }
  return s;
}

describe('reducer: order of questions (core → clarifying, quiz_flow)', () => {
  it('Start opens the first core statement', () => {
    const s = run(initialState, { type: 'START' });
    expect(s.screen).toEqual({ name: 'question', i: 0 });
    expect(s.shown).toEqual([C[0]]);
  });

  it('the core in the exported order, then the clarifying statements of golden «flow 0», then trade-offs', () => {
    const s = answerAll(run(initialState, { type: 'START' }), flow0.answers);
    expect(s.shown).toEqual([...flow0.flow!.core, ...flow0.flow!.clarifying]);
    expect(s.shown).toHaveLength(planned);
    const pair = tradeoffs(data, flow0.answers, {})[0];
    expect(s.screen).toEqual(pair ? { name: 'tradeoff', pair } : { name: 'results' });
  });

  it('without quiz_core Start waits; without quiz_data the first clarifying question waits; DATA_READY resumes', () => {
    const none = createReducer({ core: null, data: null });
    const w = none(initialState, { type: 'START' });
    expect(w.screen).toEqual({ name: 'wait', then: 'next' });
    const coreOnly = createReducer({ core, data: null });
    let s = coreOnly(w, { type: 'DATA_READY' });
    expect(s.screen).toEqual({ name: 'question', i: 0 });
    for (let i = 0; i < C.length; i++) s = [{ type: 'ANSWER', value: 1 } as Action, { type: 'NEXT' } as Action].reduce(coreOnly, s);
    expect(s.screen).toEqual({ name: 'wait', then: 'next' });
    s = reducer(s, { type: 'DATA_READY' });
    expect(s.screen).toEqual({ name: 'question', i: C.length });
    expect(s.shown[C.length]).toBe(nextClarify(data, s.answers, [...C]));
    expect(reducer(s, { type: 'DATA_READY' })).toBe(s); // nothing to resume
  });

  it('Back from a wait returns to the last question', () => {
    const coreOnly = createReducer({ core, data: null });
    const s = coreOnly(at(C.length - 1, { [C[0]!]: 1 }), { type: 'SKIP' });
    expect(s.screen.name).toBe('wait');
    expect(coreOnly(s, { type: 'BACK' }).screen).toEqual({ name: 'question', i: C.length - 1 });
  });
});

describe('reducer: answering', () => {
  it('an answer is selected (stays); Next advances; Next without an answer does nothing', () => {
    const s = run(at(0), { type: 'ANSWER', value: 2 });
    expect(s.answers).toEqual({ [C[0]!]: 2 });
    expect(s.screen).toEqual({ name: 'question', i: 0 });
    expect(run(s, { type: 'ANSWER', value: -1 }).answers).toEqual({ [C[0]!]: -1 });
    expect(run(s, { type: 'NEXT' }).screen).toEqual({ name: 'question', i: 1 });
    expect(run(at(0), { type: 'NEXT' })).toEqual(at(0));
  });

  it('Back keeps the previous answer (shown selected) and goes back; from the first statement to Start', () => {
    const s = run(at(0), { type: 'ANSWER', value: -1 }, { type: 'NEXT' }, { type: 'BACK' });
    expect(s.screen).toEqual({ name: 'question', i: 0 });
    expect(s.answers[C[0]!]).toBe(-1);
    expect(run(s, { type: 'BACK' }).screen).toEqual({ name: 'start' });
  });

  it('Back and Next move along the statements already shown; new ones are added only at the end', () => {
    const s = answerAll(run(initialState, { type: 'START' }), flow0.answers);
    const shown = s.shown;
    const back = run({ ...s, screen: { name: 'question', i: 5 } }, { type: 'SKIP' });
    expect(back.screen).toEqual({ name: 'question', i: 6 });
    expect(back.shown).toBe(shown);
  });

  it('Skip leaves the statement unanswered (removes an earlier answer) and advances', () => {
    const s = run(at(0, { [C[0]!]: 1, [C[1]!]: 'dk' }), { type: 'SKIP' });
    expect(s.answers).toEqual({ [C[1]!]: 'dk' });
    expect(s.screen).toEqual({ name: 'question', i: 1 });
  });

  it("«don't know» is an answer, not a skip", () => {
    expect(run(at(3), { type: 'ANSWER', value: 'dk' }).answers).toEqual({ [C[3]!]: 'dk' });
  });

  it('Finish without answers, or with only «don\'t know», shows the notice and stays', () => {
    const s = run(at(4), { type: 'FINISH' });
    expect(s.notice).toBe('noAnswers');
    expect(s.screen).toEqual({ name: 'question', i: 4 });
    const dk = run(at(4, { [C[0]!]: 'dk' }), { type: 'FINISH' });
    expect(dk.notice).toBe('noAnswers');
    expect(run(dk, { type: 'BACK' }).notice).toBeNull();
  });

  it('menu «My results» on a statement = Finish', () => {
    const s = run(at(5, full.answers), { type: 'SHOW_RESULTS' });
    expect(s.screen).toEqual(run(at(5, full.answers), { type: 'FINISH' }).screen);
    expect(run(at(4), { type: 'SHOW_RESULTS' }).notice).toBe('noAnswers');
  });
});

describe('reducer: trade-offs (as quiz_cli.exchange)', () => {
  it('first pair = tradeoffs()[0]; A doubles qa; next pair is adaptive (golden «full, adaptive step 2»)', () => {
    const s1 = run(at(5, full.answers), { type: 'FINISH' });
    expect(s1.screen).toEqual({ name: 'tradeoff', pair: full.tradeoffs.pairs[0] });
    const s2 = run(s1, { type: 'TRADE', choice: 'A' });
    expect(s2.mult).toEqual(step2.mult);
    expect(s2.done).toHaveLength(1);
    expect(s2.screen).toEqual({ name: 'tradeoff', pair: step2.tradeoffs.pairs[0] });
  });

  it('Back undoes the previous trade-off (weights restored, its pair asked again); from the first, to the statements', () => {
    const s1 = run(at(5, full.answers), { type: 'FINISH' });
    const s2 = run(s1, { type: 'TRADE', choice: 'A' });
    const back = run(s2, { type: 'BACK' });
    expect(back.screen).toEqual(s1.screen);
    expect(back.mult).toEqual({});
    expect(back.done).toEqual([]);
    expect(run(back, { type: 'BACK' }).screen).toEqual({ name: 'question', i: 5 });
  });

  it('menu «My results» on a trade-off skips the rest', () => {
    const s1 = run(at(5, full.answers), { type: 'FINISH' });
    expect(run(s1, { type: 'SHOW_RESULTS' }).screen).toEqual({ name: 'results' });
  });

  it('B doubles qb, «equally» changes nothing', () => {
    const s1 = run(at(5, full.answers), { type: 'FINISH' });
    const [, qb] = full.tradeoffs.pairs[0]!;
    expect(run(s1, { type: 'TRADE', choice: 'B' }).mult).toEqual({ [qb]: data.params.TRADE_W });
    expect(run(s1, { type: 'TRADE', choice: '=' }).mult).toEqual({});
  });

  it('stops at flow.trade or when no pair is left; statements and lists are not reused', () => {
    let s = run(at(5, full.answers), { type: 'FINISH' });
    let guard = 0;
    while (s.screen.name === 'tradeoff' && guard++ < 10) s = run(s, { type: 'TRADE', choice: '=' });
    expect(s.screen.name).toBe('results');
    expect(s.done.length).toBeLessThanOrEqual(data.flow.trade);
    const used = s.done.flatMap((d) => [d.qa, d.qb]);
    expect(new Set(used).size).toBe(used.length);
    expect(new Set(s.done.map((d) => d.list)).size).toBe(s.done.length);
  });

  it('no pair at all: straight to results', () => {
    const answers = { [C[0]!]: 2 } as Answers;
    expect(tradeoffs(data, answers)).toEqual([]);
    expect(run(at(5, answers), { type: 'FINISH' }).screen).toEqual({ name: 'results' });
  });
});

describe('reducer: «Answer more questions»', () => {
  const done = (): State => {
    let s = answerAll(run(initialState, { type: 'START' }), flow0.answers);
    let guard = 0;
    while (s.screen.name === 'tradeoff' && guard++ < 10) s = run(s, { type: 'TRADE', choice: '=' });
    return s;
  };

  it('continues with the next clarifying statement; Finish goes straight to results (no new trade-offs)', () => {
    const r = done();
    expect(r.screen).toEqual({ name: 'results' });
    const m = run(r, { type: 'MORE' });
    expect(m.more).toBe(true);
    expect(m.screen).toEqual({ name: 'question', i: planned });
    expect(m.shown[planned]).toBe(nextClarify(data, r.answers, shownSoFar(r)));
    const back = run(m, { type: 'ANSWER', value: 2 }, { type: 'FINISH' });
    expect(back.screen).toEqual({ name: 'results' });
    expect(back.more).toBe(false);
    expect(back.done).toEqual(r.done);
  });

  it('goes on until the pool ends, then results', () => {
    let s = run(done(), { type: 'MORE' });
    let guard = 0;
    while (s.screen.name === 'question' && guard++ < 200) s = run(s, { type: 'SKIP' });
    expect(s.screen).toEqual({ name: 'results' });
    expect(nextClarify(data, s.answers, shownSoFar(s))).toBeNull();
    expect(s.shown.length).toBeLessThanOrEqual(data.statements.length);
  });
});

describe('reducer: results, details, bills, methodology', () => {
  const results: State = { ...initialState, answers: full.answers, shown: [...C], screen: { name: 'results' } };
  const L = full.tradeoffs.pairs[0]![2];

  it('results → details → bills → back → back', () => {
    const d = run(results, { type: 'OPEN_DETAILS', list: L });
    expect(d.screen).toEqual({ name: 'details', list: L });
    const b = run(d, { type: 'OPEN_BILLS', q: C[0]! });
    expect(b.screen).toEqual({ name: 'bills', list: L, q: C[0] });
    expect(run(b, { type: 'BACK' }).screen).toEqual({ name: 'details', list: L });
    expect(run(b, { type: 'BACK' }, { type: 'BACK' }).screen).toEqual({ name: 'results' });
  });

  it('Change answers keeps answers and trade-off weights and returns to the first statement', () => {
    const s = run({ ...results, mult: { [C[0]!]: 2 } }, { type: 'CHANGE_ANSWERS' });
    expect(s.screen).toEqual({ name: 'question', i: 0 });
    expect(s.answers).toBe(full.answers);
    expect(s.mult).toEqual({ [C[0]!]: 2 });
  });

  it('Start over clears everything', () => {
    const s = run({ ...results, mult: { [C[0]!]: 2 }, done: [{ qa: C[0]!, qb: C[1]!, list: L, choice: 'A' }] },
      { type: 'START_OVER' });
    expect(s).toEqual(initialState);
  });

  it('methodology opens from any screen (menu) and returns there', () => {
    for (const from of [initialState, at(3), results, run(results, { type: 'OPEN_DETAILS', list: L }),
      run(at(5, full.answers), { type: 'FINISH' })]) {
      const m = run(from, { type: 'OPEN_METHODOLOGY' });
      expect(m.screen.name).toBe('methodology');
      expect(run(m, { type: 'BACK' }).screen).toEqual(from.screen);
    }
  });

  it('Results header «Start over»: everything cleared, straight to the first question as Start on Home', () => {
    expect(run(results, { type: 'RESTART' })).toEqual(run(initialState, { type: 'START' }));
  });

  it('actions that do not belong to the current screen change nothing', () => {
    expect(run(initialState, { type: 'ANSWER', value: 2 })).toBe(initialState);
    expect(run(initialState, { type: 'TRADE', choice: 'A' })).toBe(initialState);
    expect(run(results, { type: 'START' })).toBe(results);
    expect(run(initialState, { type: 'RESTART' })).toBe(initialState);
    expect(run(initialState, { type: 'SHOW_RESULTS' })).toBe(initialState);
    expect(run(initialState, { type: 'MORE' })).toBe(initialState);
  });
});
