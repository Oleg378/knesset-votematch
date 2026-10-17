/**
 * The flow as a pure state machine (same as pipeline/quiz_cli.py):
 * start → question(i) → tradeoff (0–MAX_TRADE, adaptive) → results ⇄ details(list) → bills(list, q); methodology from
 * any screen (menu). State lives in memory only [У 2026-10-17]: nothing is stored, a reload starts over.
 * Interaction as in the Figma mockups: an answer is selected, «Next» moves on; trade-offs likewise, with «Back».
 */
import { tradeoffs } from '../engine/match';
import type { Answer, AnswerValue, Answers, Mult, QuizData, TradePair } from '../engine/types';

export type TradeChoice = 'A' | 'B' | '=';

export interface TradeDone {
  qa: string;
  qb: string;
  list: string;
  choice: TradeChoice;
}

export type BaseScreen =
  | { name: 'start' }
  | { name: 'question'; i: number }
  | { name: 'tradeoff'; pair: TradePair }
  | { name: 'results' }
  | { name: 'details'; list: string }
  | { name: 'bills'; list: string; q: string };

export type Screen = BaseScreen | { name: 'methodology'; back: BaseScreen };

export interface State {
  screen: Screen;
  answers: Answers;
  mult: Mult;
  done: TradeDone[];
  /** «No answers — nothing to compute» after Finish without any answer other than «don't know». */
  notice: 'noAnswers' | null;
  /** Statement to return to on Back from the first trade-off (where the questions were finished). */
  lastQ: number;
}

export type Action =
  | { type: 'START' }
  | { type: 'ANSWER'; value: Answer }
  | { type: 'NEXT' }
  | { type: 'SKIP' }
  | { type: 'BACK' }
  | { type: 'FINISH' }
  | { type: 'TRADE'; choice: TradeChoice }
  | { type: 'OPEN_DETAILS'; list: string }
  | { type: 'OPEN_BILLS'; q: string }
  | { type: 'CHANGE_ANSWERS' }
  | { type: 'START_OVER' }
  | { type: 'OPEN_METHODOLOGY' }
  /** Menu «My results»: finish the questions (trade-offs follow) or skip the remaining trade-offs. */
  | { type: 'SHOW_RESULTS' };

export const initialState: State = {
  screen: { name: 'start' }, answers: {}, mult: {}, done: [], notice: null, lastQ: 0,
};

export function hasComputableAnswers(answers: Answers): boolean {
  return Object.values(answers).some((v) => v !== 'dk');
}

/** Number of answers the result is based on: everything except «don't know» (as quiz_cli.py). */
export function answeredCount(answers: Answers): number {
  return Object.values(answers).filter((v) => v !== 'dk').length;
}

export function isAnswerValue(v: Answer): v is AnswerValue {
  return v !== 'dk';
}

export function createReducer(data: QuizData) {
  const n = data.statements.length;
  const { MAX_TRADE, TRADE_W } = data.params;

  /** Next trade-off as quiz_cli.exchange(): first pair given the statements and lists already used. */
  function nextTrade(s: State): State {
    if (s.done.length >= MAX_TRADE) return { ...s, screen: { name: 'results' } };
    const used = s.done.flatMap((d) => [d.qa, d.qb]);
    const lists = s.done.map((d) => d.list);
    const pair = tradeoffs(data, s.answers, s.mult, used, lists)[0];
    return { ...s, screen: pair ? { name: 'tradeoff', pair } : { name: 'results' } };
  }

  function finish(s: State, i: number): State {
    if (!hasComputableAnswers(s.answers)) return { ...s, notice: 'noAnswers' };
    return nextTrade({ ...s, lastQ: i });
  }

  /** Back on a trade-off: undo the previous one (its pair is asked again), or return to the statements. */
  function undoTrade(s: State): State {
    const last = s.done[s.done.length - 1];
    if (!last) return { ...s, screen: { name: 'question', i: s.lastQ } };
    const mult = { ...s.mult };
    const q = last.choice === 'A' ? last.qa : last.choice === 'B' ? last.qb : null;
    if (q !== null) {
      mult[q] = (mult[q] ?? 1) / TRADE_W;
      if (mult[q] === 1) delete mult[q];
    }
    return { ...s, mult, done: s.done.slice(0, -1), screen: { name: 'tradeoff', pair: [last.qa, last.qb, last.list] } };
  }

  return function reducer(state: State, action: Action): State {
    const s: State = state.notice ? { ...state, notice: null } : state;
    const sc = s.screen;
    switch (action.type) {
      case 'START':
        return sc.name === 'start' ? { ...s, screen: { name: 'question', i: 0 } } : state;

      case 'ANSWER': {
        // Selects the answer; «Next» moves on.
        if (sc.name !== 'question') return state;
        return { ...s, answers: { ...s.answers, [data.statements[sc.i]!.q]: action.value } };
      }

      case 'NEXT': {
        if (sc.name !== 'question' || s.answers[data.statements[sc.i]!.q] === undefined) return state;
        return sc.i + 1 < n ? { ...s, screen: { name: 'question', i: sc.i + 1 } } : finish(s, sc.i);
      }

      case 'SKIP': {
        // Skip = no answer (not «don't know»): a previous answer to this statement is removed.
        if (sc.name !== 'question') return state;
        const { [data.statements[sc.i]!.q]: _removed, ...answers } = s.answers;
        const next: State = { ...s, answers };
        return sc.i + 1 < n ? { ...next, screen: { name: 'question', i: sc.i + 1 } } : finish(next, sc.i);
      }

      case 'FINISH':
        return sc.name === 'question' ? finish(s, sc.i) : state;

      case 'SHOW_RESULTS': {
        const at = sc.name === 'methodology' ? sc.back : sc;
        if (at.name === 'question') return finish(s, at.i);
        if (!hasComputableAnswers(s.answers) || at.name === 'start') return state;
        return { ...s, screen: { name: 'results' } };
      }

      case 'TRADE': {
        if (sc.name !== 'tradeoff') return state;
        const [qa, qb, list] = sc.pair;
        const mult = { ...s.mult };
        if (action.choice === 'A') mult[qa] = (mult[qa] ?? 1) * TRADE_W;
        else if (action.choice === 'B') mult[qb] = (mult[qb] ?? 1) * TRADE_W;
        return nextTrade({ ...s, mult, done: [...s.done, { qa, qb, list, choice: action.choice }] });
      }

      case 'OPEN_DETAILS':
        return sc.name === 'results' ? { ...s, screen: { name: 'details', list: action.list } } : state;

      case 'OPEN_BILLS':
        return sc.name === 'details' ? { ...s, screen: { name: 'bills', list: sc.list, q: action.q } } : state;

      case 'BACK':
        switch (sc.name) {
          case 'question':
            return { ...s, screen: sc.i > 0 ? { name: 'question', i: sc.i - 1 } : { name: 'start' } };
          case 'tradeoff':
            return undoTrade(s);
          case 'details':
            return { ...s, screen: { name: 'results' } };
          case 'bills':
            return { ...s, screen: { name: 'details', list: sc.list } };
          case 'methodology':
            return { ...s, screen: sc.back };
          default:
            return state;
        }

      case 'CHANGE_ANSWERS':
        return sc.name === 'results' ? { ...s, screen: { name: 'question', i: 0 } } : state;

      case 'START_OVER':
        return initialState;

      case 'OPEN_METHODOLOGY':
        return sc.name === 'methodology' ? state : { ...s, screen: { name: 'methodology', back: sc } };
    }
  };
}
