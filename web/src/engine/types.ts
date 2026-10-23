/**
 * Types of the data contract (export/quiz_data.schema.json, export/WEB_CONTRACT.md). Three files, fetched in order:
 * quiz_core (enough to start answering) → quiz_data (positions, everything for ranking) → quiz_bills (list details only).
 */

export type Sign = 1 | -1;
export type Role = 'main' | 'secondary';
export type ListStatus = 'ok' | 'warning' | 'not_evaluated';

export interface Params {
  K: number;
  MIN_COVERAGE: number;
  /** A list ranks only with at least this many former MKs (otherwise «Not ranked» with its note). */
  MIN_EX_MKS: number;
  MAX_TRADE: number;
  TRADE_TOP: number;
  TRADE_W: number;
  TRADE_CANDIDATES: number;
  VOTE_WEIGHT: number;
  /** A position is clear when |p| >= CLOSE, n_mk >= MIN_CLEAR_MKS and n_names >= MIN_CLEAR_BILLS. */
  CLOSE: number;
  MIN_CLEAR_MKS: number;
  MIN_CLEAR_BILLS: number;
  /** Bill page; `{id}` is replaced with the bill id. */
  BILL_URL: string;
}

/** Order of questions (pipeline/quiz_flow.py FLOW). Never hard-code these numbers. */
export interface Flow {
  core: number;
  clarify: number;
  trade: number;
  /** How the core was built — already applied in `core`, informational. */
  core_axes: number;
  core_slots: number[];
  core_r_max: number;
  core_gov_share: number;
  gov_r: number;
  core_min_interest: number;
  core_area_cap: number;
  /** false: a statement on which every clear list position is on one side is not in the core (precomputed in `core`). */
  core_one_sided: boolean;
  /** Clarifying (quiz_flow.next_clarify): a candidate's score × (interest / 5) ** interest_alpha. */
  interest_alpha: number;
  clarify_top: number;
  /** A ranked list is a contender of the leader within pair_gap; its weight is 1 / (gap + pair_eps). */
  pair_gap: number;
  pair_eps: number;
  /** A candidate with |r| ≥ near_dup_r to a shown statement is skipped (if anything else is left). */
  near_dup_r: number;
  /** false: the previous question's area is skipped (if anything else is left). */
  same_area_in_row: boolean;
  /** No two statements of one sim_group among the shown ones. */
  sim_groups: boolean;
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
  /** How much a voter cares (1–5), the broad area, statements that feel like one question: only for the order of questions. */
  interest: number;
  area: string;
  sim_group: string | null;
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
  /** Votes on the other camp's bills. */
  n_other: number;
  /** Votes on the coalition's own government bills (G, export round 7). */
  n_gov: number;
  /** Distinct bills (by name, sponsored or voted) behind the position. */
  n_names: number;
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
  generated: string;
  source_commit: string;
}

/** quiz_core.json: the flow numbers, the core order and the core statements. */
export interface QuizCore extends Head {
  flow: Flow;
  core: string[];
  statements: Statement[];
}

/** quiz_data.json: everything the ranking, trade-offs and clarifying questions need. */
export interface QuizData extends Head {
  params: Params;
  flow: Flow;
  core: string[];
  statements: Statement[];
  directions: Record<string, Direction>;
  lists: QuizList[];
}

/** quiz_bills.json: only for List details, «Bills of one statement» and Methodology. */
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
