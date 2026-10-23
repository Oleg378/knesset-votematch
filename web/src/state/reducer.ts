/**
 * The flow as a pure state machine (same as pipeline/quiz_cli.py):
 * start → question(i) over `shown` (the core statements, then clarifying ones chosen one at a time — src/engine/flow.ts)
 * → tradeoff (0–MAX_TRADE, adaptive) → results ⇄ details(list) → bills(list, q); «Answer more questions» continues the
 * clarifying ones; methodology from any screen (menu). State lives in memory only [У 2026-10-17]: nothing is stored, a
 * reload starts over. Interaction as in the Figma mockups: an answer is selected, «Next» moves on; trade-offs likewise.
 *
 * Data: quiz_core is bundled (given to createReducer); quiz_data and quiz_bills arrive later (FILE_READY). An action that
 * needs a file not yet loaded is kept as `pending` behind the loading screen and replayed when the file arrives.
 */
import { nextClarify, shouldStop } from '../engine/flow';
import { tradeoffs } from '../engine/match';
import type { Answer, AnswerValue, Answers, BillsFile, CoreFile, DataFile, Mult, Statement, TradePair } from '../engine/types';

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

export type Screen =
  | BaseScreen
  | { name: 'methodology'; back: BaseScreen }
  /** A file the next screen needs has not arrived yet; Back cancels. */
  | { name: 'loading'; back: BaseScreen };

type FileName = 'data' | 'bills';

export interface State {
  screen: Screen;
  /** Statements shown so far, in order (answered, skipped or «don't know»); question(i) shows shown[i]. */
  shown: string[];
  answers: Answers;
  mult: Mult;
  done: TradeDone[];
  /** «No answers — nothing to compute» after Finish without any answer other than «don't know»; «No more questions». */
  notice: 'noAnswers' | 'noMore' | null;
  /** Statement to return to on Back from the first trade-off (where the questions were finished). */
  lastQ: number;
  /** After «Answer more questions»: clarifying questions go on until the pool ends (quiz_cli.py flow(until=None)). */
  more: boolean;
  data: DataFile | null;
  bills: BillsFile | null;
  loadFailed: boolean;
  pending: Action | null;
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
  | { type: 'ANSWER_MORE' }
  | { type: 'START_OVER' }
  | { type: 'OPEN_METHODOLOGY' }
  /** Menu «My results»: finish the questions (trade-offs follow) or skip the remaining trade-offs. */
  | { type: 'SHOW_RESULTS' }
  | { type: 'FILE_READY'; name: 'data'; file: DataFile }
  | { type: 'FILE_READY'; name: 'bills'; file: BillsFile }
  | { type: 'LOAD_ERROR' };

export const initialState: State = {
  screen: { name: 'start' }, shown: [], answers: {}, mult: {}, done: [], notice: null, lastQ: 0, more: false,
  data: null, bills: null, loadFailed: false, pending: null,
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

/** The statement q: from quiz_data when loaded, else from the bundled core (which holds only the core statements). */
export function statementOf(core: CoreFile, data: DataFile | null, q: string): Statement | undefined {
  return (data ?? core).statements.find((s) => s.q === q);
}

/** The screen a loading or methodology screen stands in front of. */
export function baseOf(sc: Screen): BaseScreen {
  return sc.name === 'methodology' || sc.name === 'loading' ? sc.back : sc;
}

export function createReducer(core: CoreFile) {
  /** The waiting state for an action that needs files not loaded yet, or null when everything is there. */
  function waitFor(s: State, action: Action, files: FileName[]): State | null {
    if (files.every((f) => s[f] !== null)) return null;
    return { ...s, pending: action, screen: { name: 'loading', back: baseOf(s.screen) } };
  }

  /** Next trade-off as quiz_cli.exchange(): first pair given the statements and lists already used. */
  function nextTrade(s: State): State {
    const data = s.data!;
    if (s.done.length >= data.params.MAX_TRADE) return { ...s, screen: { name: 'results' } };
    const used = s.done.flatMap((d) => [d.qa, d.qb]);
    const lists = s.done.map((d) => d.list);
    const pair = tradeoffs(data, s.answers, s.mult, used, lists)[0];
    return { ...s, screen: pair ? { name: 'tradeoff', pair } : { name: 'results' } };
  }

  function finish(s: State, i: number, action: Action): State {
    if (!hasComputableAnswers(s.answers)) return { ...s, notice: 'noAnswers' };
    return waitFor(s, action, ['data']) ?? nextTrade({ ...s, lastQ: i });
  }

  /** After question i: the next shown statement, else a clarifying one (quiz_flow.next_clarify), else finish. */
  function advance(s: State, i: number, action: Action): State {
    if (i + 1 < s.shown.length) return { ...s, screen: { name: 'question', i: i + 1 } };
    const wait = waitFor(s, action, ['data']);
    if (wait) return wait;
    const data = s.data!;
    if (!s.more && shouldStop(data, s.answers, s.shown.length)) return finish(s, i, action);
    const q = nextClarify(data, s.answers, s.shown);
    if (q === null) return finish(s, i, action);
    return { ...s, shown: [...s.shown, q], screen: { name: 'question', i: i + 1 } };
  }

  /** Back on a trade-off: undo the previous one (its pair is asked again), or return to the statements. */
  function undoTrade(s: State): State {
    const last = s.done[s.done.length - 1];
    if (!last) return { ...s, screen: { name: 'question', i: s.lastQ } };
    const mult = { ...s.mult };
    const q = last.choice === 'A' ? last.qa : last.choice === 'B' ? last.qb : null;
    if (q !== null) {
      mult[q] = (mult[q] ?? 1) / s.data!.params.TRADE_W;
      if (mult[q] === 1) delete mult[q];
    }
    return { ...s, mult, done: s.done.slice(0, -1), screen: { name: 'tradeoff', pair: [last.qa, last.qb, last.list] } };
  }

  return function reducer(state: State, action: Action): State {
    const s: State = state.notice ? { ...state, notice: null } : state;
    const sc = s.screen;
    switch (action.type) {
      case 'FILE_READY': {
        const loaded: State = action.name === 'data' ? { ...s, data: action.file } : { ...s, bills: action.file };
        if (!loaded.pending) return loaded;
        const pending = loaded.pending;
        return reducer({ ...loaded, pending: null, screen: baseOf(loaded.screen) }, pending);
      }

      case 'LOAD_ERROR':
        return { ...s, loadFailed: true };

      case 'START':
        return sc.name === 'start' ? { ...s, shown: [...core.core], screen: { name: 'question', i: 0 } } : state;

      case 'ANSWER': {
        // Selects the answer; «Next» moves on.
        if (sc.name !== 'question') return state;
        return { ...s, answers: { ...s.answers, [s.shown[sc.i]!]: action.value } };
      }

      case 'NEXT': {
        if (sc.name !== 'question' || s.answers[s.shown[sc.i]!] === undefined) return state;
        return advance(s, sc.i, action);
      }

      case 'SKIP': {
        // Skip = no answer (not «don't know»): a previous answer to this statement is removed.
        if (sc.name !== 'question') return state;
        const { [s.shown[sc.i]!]: _removed, ...answers } = s.answers;
        return advance({ ...s, answers }, sc.i, action);
      }

      case 'FINISH':
        return sc.name === 'question' ? finish(s, sc.i, action) : state;

      case 'SHOW_RESULTS': {
        const at = baseOf(sc);
        if (at.name === 'question') return finish(s, at.i, action);
        if (!hasComputableAnswers(s.answers) || at.name === 'start') return state;
        return waitFor(s, action, ['data']) ?? { ...s, screen: { name: 'results' } };
      }

      case 'ANSWER_MORE': {
        if (sc.name !== 'results') return state;
        const wait = waitFor(s, action, ['data']);
        if (wait) return wait;
        const q = nextClarify(s.data!, s.answers, s.shown);
        if (q === null) return { ...s, notice: 'noMore' };
        return { ...s, more: true, shown: [...s.shown, q], screen: { name: 'question', i: s.shown.length } };
      }

      case 'TRADE': {
        if (sc.name !== 'tradeoff') return state;
        const [qa, qb, list] = sc.pair;
        const w = s.data!.params.TRADE_W;
        const mult = { ...s.mult };
        if (action.choice === 'A') mult[qa] = (mult[qa] ?? 1) * w;
        else if (action.choice === 'B') mult[qb] = (mult[qb] ?? 1) * w;
        return nextTrade({ ...s, mult, done: [...s.done, { qa, qb, list, choice: action.choice }] });
      }

      case 'OPEN_DETAILS':
        if (sc.name !== 'results') return state;
        return waitFor(s, action, ['data', 'bills']) ?? { ...s, screen: { name: 'details', list: action.list } };

      case 'OPEN_BILLS':
        if (sc.name !== 'details') return state;
        return waitFor(s, action, ['data', 'bills']) ?? { ...s, screen: { name: 'bills', list: sc.list, q: action.q } };

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
          case 'loading':
            return { ...s, pending: null, screen: sc.back };
          default:
            return state;
        }

      case 'CHANGE_ANSWERS':
        return sc.name === 'results' ? { ...s, screen: { name: 'question', i: 0 } } : state;

      case 'START_OVER':
        return { ...initialState, data: s.data, bills: s.bills, loadFailed: s.loadFailed };

      case 'OPEN_METHODOLOGY': {
        if (sc.name === 'methodology') return state;
        return waitFor(s, action, ['data', 'bills'])
          ?? { ...s, pending: null, screen: { name: 'methodology', back: baseOf(sc) } };
      }
    }
  };
}
