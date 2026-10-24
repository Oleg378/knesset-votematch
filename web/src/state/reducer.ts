/**
 * The flow as a pure state machine (pipeline/quiz_cli.py, the order of questions of pipeline/quiz_flow.py):
 * start → core questions → clarifying questions (chosen one at a time, quiz_flow.next_clarify) → trade-offs (0–flow.trade,
 * adaptive) → results ⇄ details(list) (the bills open inside it); «Answer more questions» on results continues clarifying questions
 * until the pool ends; methodology from any screen (menu). When a step needs a data file that has not arrived yet, the
 * screen is «wait» and DATA_READY resumes it. State lives in memory only [У 2026-10-17]: nothing is stored.
 * Interaction as in the Figma mockups: an answer is selected, «Next» moves on; trade-offs likewise, with «Back».
 */
import { nextClarify, shouldStop } from '../engine/flow';
import { tradeoffs } from '../engine/match';
import type { Answer, AnswerValue, Answers, Mult, QuizCore, QuizData, TradePair } from '../engine/types';

export type TradeChoice = 'A' | 'B' | '=';

export interface TradeDone {
  qa: string;
  qb: string;
  list: string;
  choice: TradeChoice;
}

export type BaseScreen =
  | { name: 'start' }
  /** shown[i] */
  | { name: 'question'; i: number }
  /** Waiting for a data file: then «next» picks the next question, «finish» goes to trade-offs / results. */
  | { name: 'wait'; then: 'next' | 'finish' }
  | { name: 'tradeoff'; pair: TradePair }
  | { name: 'results' }
  | { name: 'details'; list: string };

export type Screen = BaseScreen | { name: 'methodology'; back: BaseScreen };

export interface State {
  screen: Screen;
  answers: Answers;
  mult: Mult;
  done: TradeDone[];
  /** Statements shown so far, in order (core, then clarifying); answered or skipped. Back and Next move along it. */
  shown: string[];
  /** «Answer more questions»: clarifying questions go on until the pool ends (no stopping rule). */
  more: boolean;
  /** «No answers — nothing to compute» after Finish without any answer other than «don't know». */
  notice: 'noAnswers' | null;
  /** Index in `shown` to return to on Back from the first trade-off (where the questions were finished). */
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
  | { type: 'CHANGE_ANSWERS' }
  | { type: 'START_OVER' }
  /** Results header «Start over»: clear everything and go straight to the first question, as Start on Home. */
  | { type: 'RESTART' }
  | { type: 'OPEN_METHODOLOGY' }
  /** Menu «My results»: finish the questions (trade-offs follow) or skip the remaining trade-offs. */
  | { type: 'SHOW_RESULTS' }
  /** Results «Answer more questions». */
  | { type: 'MORE' }
  /** A data file has arrived: resume a «wait» screen. */
  | { type: 'DATA_READY' };

export const initialState: State = {
  screen: { name: 'start' }, answers: {}, mult: {}, done: [], shown: [], more: false, notice: null, lastQ: 0,
};

/** The pages of the site and their addresses (src/prerender.tsx renders them; the links of the app point at them). */
export const PAGE_PATHS = { start: '/', methodology: '/how-it-works' } as const;

/** The state the app starts in on a page: «/how-it-works» opens the methodology (Back → the start page); any other — the start. */
export function initialStateFor(path: string): State {
  return path === PAGE_PATHS.methodology ? { ...initialState, screen: { name: 'methodology', back: { name: 'start' } } } : initialState;
}

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

/** quiz_cli.flow: the statements shown so far, in order, then any answered but not shown (quiz_flow skips the last one's area). */
export function shownSoFar(s: Pick<State, 'answers' | 'shown'>): string[] {
  return [...s.shown, ...Object.keys(s.answers).filter((q) => !s.shown.includes(q))];
}

/** What the reducer can use: the core file (flow, core order) and, once it has arrived, the data file. */
export interface FlowSources {
  core: QuizCore | null;
  data: QuizData | null;
}

/** The next new question after `shown` (quiz_cli.flow): the rest of the core, then a clarifying one; null = stop. */
export function nextQuestion(src: FlowSources, s: Pick<State, 'answers' | 'shown' | 'more'>): string | null | 'wait' {
  if (!src.core) return 'wait';
  const { flow, core } = src.core;
  const rest = core.filter((q) => !s.shown.includes(q) && s.answers[q] === undefined);
  if (rest.length) return rest[0]!;
  if (!s.more) {
    if (flow.stop_gap !== null && !src.data) return 'wait';
    if (shouldStop(flow, src.data, s.answers, s.shown.length)) return null;
  }
  if (!src.data) return 'wait';
  return nextClarify(src.data, s.answers, shownSoFar(s));
}

export function createReducer(src: FlowSources) {
  /** Next trade-off as quiz_cli.exchange(): first pair given the statements and lists already used; at most flow.trade. */
  function nextTrade(s: State, data: QuizData): State {
    if (s.done.length >= data.flow.trade) return { ...s, screen: { name: 'results' } };
    const used = s.done.flatMap((d) => [d.qa, d.qb]);
    const lists = s.done.map((d) => d.list);
    const pair = tradeoffs(data, s.answers, s.mult, used, lists)[0];
    return { ...s, screen: pair ? { name: 'tradeoff', pair } : { name: 'results' } };
  }

  /** End of the questions: trade-offs then results (after «Answer more» — straight to results, as the reference). */
  function finish(s: State, i: number): State {
    if (!hasComputableAnswers(s.answers)) return { ...s, notice: 'noAnswers', screen: { name: 'question', i } };
    if (!src.data) return { ...s, lastQ: i, screen: { name: 'wait', then: 'finish' } };
    const t = { ...s, lastQ: i, more: false };
    return s.more ? { ...t, screen: { name: 'results' } } : nextTrade(t, src.data);
  }

  /** After the question at index i (answered or skipped): the next shown one, or a new one, or the end. */
  function advance(s: State, i: number): State {
    if (i + 1 < s.shown.length) return { ...s, screen: { name: 'question', i: i + 1 } };
    const q = nextQuestion(src, s);
    if (q === 'wait') return { ...s, screen: { name: 'wait', then: 'next' } };
    if (q === null) return finish(s, Math.max(i, 0));
    return { ...s, shown: [...s.shown, q], screen: { name: 'question', i: s.shown.length } };
  }

  /** Back on a trade-off: undo the previous one (its pair is asked again), or return to the statements. */
  function undoTrade(s: State, data: QuizData): State {
    const last = s.done[s.done.length - 1];
    if (!last) return { ...s, screen: { name: 'question', i: s.lastQ } };
    const mult = { ...s.mult };
    const q = last.choice === 'A' ? last.qa : last.choice === 'B' ? last.qb : null;
    if (q !== null) {
      mult[q] = (mult[q] ?? 1) / data.params.TRADE_W;
      if (mult[q] === 1) delete mult[q];
    }
    return { ...s, mult, done: s.done.slice(0, -1), screen: { name: 'tradeoff', pair: [last.qa, last.qb, last.list] } };
  }

  return function reducer(state: State, action: Action): State {
    const s: State = state.notice ? { ...state, notice: null } : state;
    const sc = s.screen;
    switch (action.type) {
      case 'START':
        return sc.name === 'start' ? advance(s, -1) : state;

      case 'ANSWER': {
        // Selects the answer; «Next» moves on.
        if (sc.name !== 'question') return state;
        return { ...s, answers: { ...s.answers, [s.shown[sc.i]!]: action.value } };
      }

      case 'NEXT': {
        if (sc.name !== 'question' || s.answers[s.shown[sc.i]!] === undefined) return state;
        return advance(s, sc.i);
      }

      case 'SKIP': {
        // Skip = no answer (not «don't know»): a previous answer to this statement is removed.
        if (sc.name !== 'question') return state;
        const { [s.shown[sc.i]!]: _removed, ...answers } = s.answers;
        return advance({ ...s, answers }, sc.i);
      }

      case 'FINISH':
        return sc.name === 'question' ? finish(s, sc.i) : state;

      case 'SHOW_RESULTS': {
        const at = sc.name === 'methodology' ? sc.back : sc;
        if (at.name === 'question') return finish(s, at.i);
        if (at.name === 'wait') return finish(s, Math.max(s.shown.length - 1, 0));
        if (!hasComputableAnswers(s.answers) || at.name === 'start') return state;
        return { ...s, screen: { name: 'results' } };
      }

      case 'TRADE': {
        if (sc.name !== 'tradeoff' || !src.data) return state;
        const [qa, qb, list] = sc.pair;
        const mult = { ...s.mult };
        const w = src.data.params.TRADE_W;
        if (action.choice === 'A') mult[qa] = (mult[qa] ?? 1) * w;
        else if (action.choice === 'B') mult[qb] = (mult[qb] ?? 1) * w;
        return nextTrade({ ...s, mult, done: [...s.done, { qa, qb, list, choice: action.choice }] }, src.data);
      }

      case 'MORE': {
        if (sc.name !== 'results') return state;
        return advance({ ...s, more: true }, s.shown.length - 1);
      }

      case 'DATA_READY':
        if (sc.name !== 'wait') return state;
        return sc.then === 'next' ? advance(s, s.shown.length - 1) : finish(s, Math.max(s.shown.length - 1, 0));

      case 'OPEN_DETAILS':
        return sc.name === 'results' ? { ...s, screen: { name: 'details', list: action.list } } : state;

      case 'BACK':
        switch (sc.name) {
          case 'question':
            return { ...s, screen: sc.i > 0 ? { name: 'question', i: sc.i - 1 } : { name: 'start' } };
          case 'wait':
            return { ...s, more: false,
              screen: s.shown.length ? { name: 'question', i: s.shown.length - 1 } : { name: 'start' } };
          case 'tradeoff':
            return src.data ? undoTrade(s, src.data) : state;
          case 'details':
            return { ...s, screen: { name: 'results' } };
          case 'methodology':
            return { ...s, screen: sc.back };
          default:
            return state;
        }

      case 'CHANGE_ANSWERS':
        return sc.name === 'results' && s.shown.length ? { ...s, screen: { name: 'question', i: 0 } } : state;

      case 'START_OVER':
        return initialState;

      case 'RESTART':
        return sc.name === 'results' ? advance(initialState, -1) : state;

      case 'OPEN_METHODOLOGY':
        return sc.name === 'methodology' ? state : { ...s, screen: { name: 'methodology', back: sc } };
    }
  };
}
