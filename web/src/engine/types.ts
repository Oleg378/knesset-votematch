/** Types of the v2 data contract: export/quiz_core.v2.json, quiz_data.v2.json, quiz_bills.v2.json (export/quiz_data.v2.schema.json). */

export type Sign = 1 | -1;
export type Role = 'main' | 'secondary';
export type ListStatus = 'ok' | 'warning' | 'not_evaluated';

export interface Params {
  K: number;
  MIN_COVERAGE: number;
  MIN_EX_MKS: number;
  MAX_TRADE: number;
  TRADE_TOP: number;
  TRADE_W: number;
  TRADE_CANDIDATES: number;
  VOTE_WEIGHT: number;
  CLOSE: number;
  MIN_CLEAR_MKS: number;
  MIN_CLEAR_BILLS: number;
  /** Link to a bill on the Knesset website: `{id}` is replaced by the bill id. */
  BILL_URL: string;
}

/** pipeline/quiz_flow.py FLOW — the numbers of the order of questions (never hard-coded on the web). */
export interface FlowParams {
  core: number;
  clarify: number;
  trade: number;
  clarify_top: number;
  pair_gap: number;
  pair_eps: number;
  near_dup_r: number;
  same_area_in_row: boolean;
  sim_groups: boolean;
  interest_alpha: number;
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
  /** interest / area / sim_group: metadata for the order of questions only. */
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
  /** The part of P from the list's own bills (authorship). */
  P_bills: number;
  e: number;
  n_mk: number;
  n_votes: number;
  n_other: number;
  n_gov: number;
  /** Distinct bills (sponsored or voted) behind the position. */
  n_names: number;
}

export interface Composition {
  party_en: string;
  ex_mks: number;
}

export interface QuizList {
  id: string;
  name_en: string;
  status: ListStatus;
  ex_mks: number;
  positions: Record<string, Position>;
  composition: Composition[];
}

export interface Mk {
  name_en: string;
  list: string;
  list_position: number;
  party_en: string | null;
}

export interface Bill {
  name_he: string;
  knesset: number;
  /** MK ids among the 2026 candidates who sponsored the bill (sorted). */
  sponsors: string[];
}

export type BillRef = [bill: string, sign: Sign, role: Role];
/** votes[list][direction]: bill, its sign on the direction, whose bill (own camp / the other camp), MKs for, MKs against. */
export type VoteRow = [bill: string, sign: Sign, camp: 'own' | 'other', votesFor: number, votesAgainst: number];

export interface FileHead {
  version: 2;
  generated: string;
  source_commit: string;
}

/** quiz_core.v2.json: enough to start answering (bundled with the app). */
export interface CoreFile extends FileHead {
  flow: FlowParams;
  core: string[];
  statements: Statement[];
}

/** quiz_data.v2.json: everything for matching, the order of questions and the trade-offs. */
export interface DataFile extends FileHead {
  params: Params;
  flow: FlowParams;
  core: string[];
  statements: Statement[];
  directions: Record<string, Direction>;
  lists: QuizList[];
}

/** quiz_bills.v2.json: what only the list details, the bills of one statement and the methodology need. */
export interface BillsFile extends FileHead {
  mks: Record<string, Mk>;
  by_direction: Record<string, BillRef[]>;
  votes: Record<string, Record<string, VoteRow[]>>;
  bills: Record<string, Bill>;
}

/** The engine's input for closeness, trade-offs and the order of questions. */
export type QuizData = DataFile;

/** 2 strongly agree … -2 strongly disagree; 'dk' don't know. A missing key = not answered (skipped). */
export type AnswerValue = 2 | 1 | 0 | -1 | -2;
export type Answer = AnswerValue | 'dk';
export type Answers = Record<string, Answer>;
/** Weight multipliers from trade-off questions (statement q -> ×TRADE_W^n). */
export type Mult = Record<string, number>;
/** A trade-off pair: statement A (list agrees with the user), statement B (list disagrees), list id. */
export type TradePair = [qa: string, qb: string, list: string];

/** params.BILL_URL with the bill id. */
export function billUrl(params: Params, id: string): string {
  return params.BILL_URL.replace('{id}', id);
}
