import { describe, expect, it } from 'vitest';
import { nextClarify } from '../engine/flow';
import { tradeoffs } from '../engine/match';
import type { Answers } from '../engine/types';
import { bills, core, data, golden, loaded } from '../test/files';
import { createReducer, initialState, type Action, type State } from './reducer';

const reducer = createReducer(core);
const run = (s: State, ...actions: Action[]) => actions.reduce(reducer, s);
const CORE = core.core;
const TOTAL = core.flow.core + core.flow.clarify;
const full = golden.cases.find((c) => c.name === 'full')!;
const step2 = golden.cases.find((c) => c.name === 'full, adaptive step 2')!;
const flow0 = golden.cases.find((c) => c.name === 'flow 0')!;

/** State (files loaded) on question i of the core with the given answers. */
const at = (i: number, answers: Answers = {}): State => ({ ...loaded, answers, shown: [...CORE], screen: { name: 'question', i } });

/** Answers the current question (or skips it when the answer set has none) and presses Next. */
function answerAndNext(s: State, answers: Answers): State {
  if (s.screen.name !== 'question') return s;
  const q = s.shown[s.screen.i]!;
  const a = answers[q];
  return a === undefined ? run(s, { type: 'SKIP' }) : run(s, { type: 'ANSWER', value: a }, { type: 'NEXT' });
}

describe('reducer: statements (core, then clarifying — quiz_flow)', () => {
  it('Start opens the first core statement', () => {
    const s = run(loaded, { type: 'START' });
    expect(s.screen).toEqual({ name: 'question', i: 0 });
    expect(s.shown).toEqual(CORE);
  });

  it('an answer is selected (stays); Next advances; Next without an answer does nothing', () => {
    const s = run(at(0), { type: 'ANSWER', value: 2 });
    expect(s.answers).toEqual({ [CORE[0]!]: 2 });
    expect(s.screen).toEqual({ name: 'question', i: 0 });
    expect(run(s, { type: 'ANSWER', value: -1 }).answers).toEqual({ [CORE[0]!]: -1 });
    expect(run(s, { type: 'NEXT' }).screen).toEqual({ name: 'question', i: 1 });
    expect(run(at(0), { type: 'NEXT' })).toEqual(at(0));
  });

  it('Back keeps the previous answer (shown selected) and goes back; from the first statement to Start', () => {
    const s = run(at(0), { type: 'ANSWER', value: -1 }, { type: 'NEXT' }, { type: 'BACK' });
    expect(s.screen).toEqual({ name: 'question', i: 0 });
    expect(s.answers[CORE[0]!]).toBe(-1);
    expect(run(s, { type: 'BACK' }).screen).toEqual({ name: 'start' });
  });

  it('Skip leaves the statement unanswered (removes an earlier answer) and advances', () => {
    const s = run(at(0, { [CORE[0]!]: 1, [CORE[1]!]: 'dk' }), { type: 'SKIP' });
    expect(s.answers).toEqual({ [CORE[1]!]: 'dk' });
    expect(s.screen).toEqual({ name: 'question', i: 1 });
  });

  it("«don't know» is an answer, not a skip", () => {
    expect(run(at(3), { type: 'ANSWER', value: 'dk' }).answers).toEqual({ [CORE[3]!]: 'dk' });
  });

  it('Finish without answers, or with only «don\'t know», shows the notice and stays', () => {
    const s = run(at(4), { type: 'FINISH' });
    expect(s.notice).toBe('noAnswers');
    expect(s.screen).toEqual({ name: 'question', i: 4 });
    const dk = run(at(4, { [CORE[0]!]: 'dk' }), { type: 'FINISH' });
    expect(dk.notice).toBe('noAnswers');
    expect(run(dk, { type: 'BACK' }).notice).toBeNull();
  });

  it('after the last core statement the next one is the clarifying statement of quiz_flow.next_clarify', () => {
    const answers: Answers = { [CORE[0]!]: 2, [CORE[1]!]: -2 };
    const s = run(at(CORE.length - 1, answers), { type: 'ANSWER', value: 1 }, { type: 'NEXT' });
    expect(s.screen).toEqual({ name: 'question', i: CORE.length });
    expect(s.shown).toHaveLength(CORE.length + 1);
    expect(s.shown[CORE.length]).toBe(nextClarify(data, { ...answers, [CORE[CORE.length - 1]!]: 1 }, CORE));
  });

  it('a skipped or «don\'t know» statement counts as shown and is never asked again', () => {
    let s = run(loaded, { type: 'START' });
    for (let i = 0; i < TOTAL; i++) {
      expect(s.screen).toEqual({ name: 'question', i });
      s = run(s, i % 3 === 0 ? { type: 'SKIP' } : { type: 'ANSWER', value: i % 3 === 1 ? 'dk' : 2 }, { type: 'NEXT' });
    }
    expect(new Set(s.shown).size).toBe(TOTAL);
  });

  it('golden «flow 0»: the questions asked, in order, then the first trade-off pair', () => {
    let s = run(loaded, { type: 'START' });
    while (s.screen.name === 'question') s = answerAndNext(s, flow0.answers);
    expect(s.shown).toEqual([...flow0.flow!.core, ...flow0.flow!.clarifying]);
    expect(s.answers).toEqual(flow0.answers);
    const pair = flow0.tradeoffs.pairs[0];
    expect(s.screen).toEqual(pair ? { name: 'tradeoff', pair } : { name: 'results' });
  });

  it('Next on the last question (core + clarify) finishes', () => {
    let s = run(loaded, { type: 'START' });
    for (let i = 0; i < TOTAL; i++) s = run(s, { type: 'ANSWER', value: i % 2 ? 2 : -2 }, { type: 'NEXT' });
    expect(['tradeoff', 'results']).toContain(s.screen.name);
    expect(s.shown).toHaveLength(TOTAL);
  });

  it('Back then a changed answer keeps the questions already chosen (no re-pick)', () => {
    let s = run(loaded, { type: 'START' });
    for (let i = 0; i < CORE.length + 2; i++) s = run(s, { type: 'ANSWER', value: 2 }, { type: 'NEXT' });
    const shown = s.shown;
    s = run(s, { type: 'BACK' }, { type: 'BACK' }, { type: 'ANSWER', value: -2 }, { type: 'NEXT' });
    expect(s.shown).toEqual(shown);
    expect(s.screen).toEqual({ name: 'question', i: CORE.length + 1 });
  });

  it('menu «My results» on a statement = Finish', () => {
    const s = run(at(5, full.answers), { type: 'SHOW_RESULTS' });
    expect(s.screen).toEqual(run(at(5, full.answers), { type: 'FINISH' }).screen);
    expect(run(at(4), { type: 'SHOW_RESULTS' }).notice).toBe('noAnswers');
  });
});

describe('reducer: data files arrive while answering', () => {
  const fresh = run(initialState, { type: 'START' });

  it('the core questions need no file; the first clarifying one waits for quiz_data, then continues', () => {
    let s = fresh;
    for (let i = 0; i < CORE.length - 1; i++) s = run(s, { type: 'ANSWER', value: 2 }, { type: 'NEXT' });
    expect(s.screen).toEqual({ name: 'question', i: CORE.length - 1 });
    s = run(s, { type: 'ANSWER', value: -2 }, { type: 'NEXT' });
    expect(s.screen).toEqual({ name: 'loading', back: { name: 'question', i: CORE.length - 1 } });
    expect(s.pending).toEqual({ type: 'NEXT' });
    const after = run(s, { type: 'FILE_READY', name: 'data', file: data });
    expect(after.pending).toBeNull();
    expect(after.screen).toEqual({ name: 'question', i: CORE.length });
    expect(after.shown).toHaveLength(CORE.length + 1);
    expect(after.data).toBe(data);
  });

  it('Back on the loading screen cancels the waiting action', () => {
    let s = fresh;
    for (let i = 0; i < CORE.length; i++) s = run(s, { type: 'ANSWER', value: 2 }, { type: 'NEXT' });
    expect(s.screen.name).toBe('loading');
    const back = run(s, { type: 'BACK' });
    expect(back.screen).toEqual({ name: 'question', i: CORE.length - 1 });
    expect(back.pending).toBeNull();
    const later = run(back, { type: 'FILE_READY', name: 'data', file: data });
    expect(later.screen).toEqual(back.screen);
  });

  it('Finish waits for quiz_data; list details wait for quiz_bills; a file arriving with nothing pending changes no screen', () => {
    const s = run(fresh, { type: 'ANSWER', value: 2 }, { type: 'FINISH' });
    expect(s.screen).toEqual({ name: 'loading', back: { name: 'question', i: 0 } });
    const t = run(s, { type: 'FILE_READY', name: 'data', file: data });
    expect(['tradeoff', 'results']).toContain(t.screen.name);
    let r = t;
    while (r.screen.name === 'tradeoff') r = run(r, { type: 'TRADE', choice: '=' });
    const L = data.lists[0]!.id;
    const d = run(r, { type: 'OPEN_DETAILS', list: L });
    expect(d.screen).toEqual({ name: 'loading', back: { name: 'results' } });
    const opened = run(d, { type: 'FILE_READY', name: 'bills', file: bills });
    expect(opened.screen).toEqual({ name: 'details', list: L });
    expect(run(opened, { type: 'FILE_READY', name: 'bills', file: bills }).screen).toEqual(opened.screen);
  });

  it('Methodology waits for both files; a load error is remembered', () => {
    const s = run(initialState, { type: 'OPEN_METHODOLOGY' });
    expect(s.screen).toEqual({ name: 'loading', back: { name: 'start' } });
    const m = run(s, { type: 'FILE_READY', name: 'data', file: data }, { type: 'FILE_READY', name: 'bills', file: bills });
    expect(m.screen).toEqual({ name: 'methodology', back: { name: 'start' } });
    expect(run(initialState, { type: 'LOAD_ERROR' }).loadFailed).toBe(true);
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

  it('stops at MAX_TRADE or when no pair is left; statements and lists are not reused', () => {
    let s = run(at(5, full.answers), { type: 'FINISH' });
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
    const answers = { [CORE[0]!]: 2 } as Answers;
    expect(tradeoffs(data, answers)).toEqual([]);
    expect(run(at(5, answers), { type: 'FINISH' }).screen).toEqual({ name: 'results' });
  });
});

describe('reducer: results, details, bills, more questions, methodology', () => {
  const results: State = { ...loaded, answers: full.answers, shown: [...CORE], screen: { name: 'results' } };
  const L = full.tradeoffs.pairs[0]![2];
  const q0 = CORE[0]!;

  it('results → details → bills → back → back', () => {
    const d = run(results, { type: 'OPEN_DETAILS', list: L });
    expect(d.screen).toEqual({ name: 'details', list: L });
    const b = run(d, { type: 'OPEN_BILLS', q: q0 });
    expect(b.screen).toEqual({ name: 'bills', list: L, q: q0 });
    expect(run(b, { type: 'BACK' }).screen).toEqual({ name: 'details', list: L });
    expect(run(b, { type: 'BACK' }, { type: 'BACK' }).screen).toEqual({ name: 'results' });
  });

  it('«Answer more questions» continues the clarifying questions until the pool ends (no fixed stop)', () => {
    const r: State = { ...loaded, answers: { [CORE[0]!]: 2, [CORE[1]!]: -2 }, shown: [...CORE], screen: { name: 'results' } };
    const s = run(r, { type: 'ANSWER_MORE' });
    expect(s.more).toBe(true);
    expect(s.screen).toEqual({ name: 'question', i: CORE.length });
    expect(s.shown[CORE.length]).toBe(nextClarify(data, r.answers, CORE));
    // well past core + clarify the questions go on
    let t = s;
    for (let i = 0; i < TOTAL + 5; i++) t = run(t, { type: 'ANSWER', value: 1 }, { type: 'NEXT' });
    expect(t.screen).toEqual({ name: 'question', i: CORE.length + TOTAL + 5 });
    expect(new Set(t.shown).size).toBe(t.shown.length);
  });

  it('«Answer more questions» with the pool exhausted shows the notice and stays', () => {
    const all = data.statements.map((s) => s.q);
    const r: State = { ...loaded, answers: full.answers, shown: all, screen: { name: 'results' } };
    const s = run(r, { type: 'ANSWER_MORE' });
    expect(s.screen).toEqual({ name: 'results' });
    expect(s.notice).toBe('noMore');
    expect(s.shown).toBe(all);
  });

  it('Change answers keeps answers and trade-off weights and returns to the first statement', () => {
    const s = run({ ...results, mult: { [q0]: 2 } }, { type: 'CHANGE_ANSWERS' });
    expect(s.screen).toEqual({ name: 'question', i: 0 });
    expect(s.answers).toBe(full.answers);
    expect(s.mult).toEqual({ [q0]: 2 });
  });

  it('Start over clears everything but the loaded files', () => {
    const s = run({ ...results, mult: { [q0]: 2 }, done: [{ qa: q0, qb: CORE[1]!, list: L, choice: 'A' }], more: true },
      { type: 'START_OVER' });
    expect(s).toEqual(loaded);
  });

  it('methodology opens from any screen (menu) and returns there', () => {
    for (const from of [loaded, at(3), results, run(results, { type: 'OPEN_DETAILS', list: L }),
      run(at(5, full.answers), { type: 'FINISH' })]) {
      const m = run(from, { type: 'OPEN_METHODOLOGY' });
      expect(m.screen.name).toBe('methodology');
      expect(run(m, { type: 'BACK' }).screen).toEqual(from.screen);
    }
  });

  it('actions that do not belong to the current screen change nothing', () => {
    expect(run(loaded, { type: 'ANSWER', value: 2 })).toBe(loaded);
    expect(run(loaded, { type: 'TRADE', choice: 'A' })).toBe(loaded);
    expect(run(results, { type: 'START' })).toBe(results);
    expect(run(loaded, { type: 'SHOW_RESULTS' })).toBe(loaded);
    expect(run(loaded, { type: 'ANSWER_MORE' })).toBe(loaded);
  });
});
