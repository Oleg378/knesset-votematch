/**
 * Types of the v2 data contract (export/quiz_data.v2.schema.json, export/V2_HANDOFF.md). Three files, fetched in order:
 * quiz_core (enough to start answering) → quiz_data (positions, everything for ranking) → quiz_bills (list details only).
 */

export type Sign = 1 | -1;
export type Role = 'main' | 'secondary';
export type ListStatus = 'ok' | 'warning' | 'not_evaluated';

export interface Params {
  K: number;
  MIN_COVERAGE: number;
  MAX_TRADE: number;
  TRADE_TOP: number;
  TRADE_W: number;
  TRADE_CANDIDATES: number;
  VOTE_WEIGHT: number;
  /** |p| below it: «has no clear position on this statement». */
  CLOSE: number;
  /** Bill page; `{id}` is replaced with the bill id. */
  BILL_URL: string;
}

/** Order of questions (pipeline/quiz_flow.py FLOW). Never hard-code these numbers. */
export interface Flow {
  core: number;
  clarify: number;
  trade: number;
  core_r_max: number;
  core_gov_share: number;
  gov_r: number;
  clarify_top: number;
  /** null: a fixed number of clarifying questions; a number: the optional stopping rule. */
  stop_gap: number | null;
  min_questions: number;
  max_questions: number;
}

export interface Statement {
  q: string;
  title_en: string;
  statement_en: string;
  key: Sign;
  d: string;
  w: number;
}

export interface Direction {
  name_en: string;
  plus_en: string;
  minus_en: string;
}

export interface Position {
  P: number;
  /** The authorship part of P (sponsored bills); used for the «side comes from votes» caveat. */
  P_bills: number;
  e: number;
  n_mk: number;
  n_votes: number;
}

export interface QuizList {
  id: string;
  name_en: string;
  status: ListStatus;
  ex_mks: number;
  positions: Record<string, Position>;
}

export interface Mk {
  name_en: string;
  list: string;
  list_position: number;
}

export interface Bill {
  name_he: string;
  knesset: number;
  sponsors: string[];
}

export type BillRef = [bill: string, sign: Sign, role: Role];

interface Head {
  version: 2;
  generated: string;
  source_commit: string;
}

/** quiz_core.v2.json: the flow numbers, the core order and the core statements. */
export interface QuizCore extends Head {
  flow: Flow;
  core: string[];
  statements: Statement[];
}

/** quiz_data.v2.json: everything the ranking, trade-offs and clarifying questions need. */
export interface QuizData extends Head {
  params: Params;
  flow: Flow;
  core: string[];
  statements: Statement[];
  directions: Record<string, Direction>;
  lists: QuizList[];
}

/** quiz_bills.v2.json: only for List details, «Bills of one statement» and Methodology. */
export interface QuizBills extends Head {
  mks: Record<string, Mk>;
  by_direction: Record<string, BillRef[]>;
  bills: Record<string, Bill>;
}

/** 2 strongly agree … -2 strongly disagree; 'dk' don't know. A missing key = not answered (skipped). */
export type AnswerValue = 2 | 1 | 0 | -1 | -2;
export type Answer = AnswerValue | 'dk';
export type Answers = Record<string, Answer>;
/** Weight multipliers from trade-off questions (statement q -> ×TRADE_W^n). */
export type Mult = Record<string, number>;
/** A trade-off pair: statement A (list agrees with the user), statement B (list disagrees), list id. */
export type TradePair = [qa: string, qb: string, list: string];
