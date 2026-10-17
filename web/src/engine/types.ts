/** Types of export/quiz_data.v1.json (see export/quiz_data.v1.schema.json). */

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
  url: string;
  /** Always null [У 2026-10-17]: no per-bill English summary; never rendered. */
  summary_en: string | null;
  sponsors: string[];
}

export type BillRef = [bill: string, sign: Sign, role: Role];

export interface QuizData {
  version: 1;
  generated: string;
  source_commit: string;
  params: Params;
  statements: Statement[];
  directions: Record<string, Direction>;
  lists: QuizList[];
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
