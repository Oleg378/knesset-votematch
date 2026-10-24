/**
 * Port of pipeline/quiz_report.py: contributions, evidence, explain. Strings come from src/strings.ts and must reproduce
 * the golden `lines` exactly. Evidence needs quiz_bills (sponsors, bills by direction).
 */
import { listVec } from './match';
import type { AnswerValue, Answers, Mult, Params, QuizBills, QuizData, QuizList, Role, Sign, Statement } from './types';

const EPS = 1e-9; // quiz_report.EPS

export interface Contribution {
  /** Contribution to the closeness numerator: w * mult * u * p. */
  c: number;
  statement: Statement;
  a: Exclude<AnswerValue, 0>;
  u: number;
  p: number;
}

function findList(data: QuizData, id: string): QuizList {
  const l = data.lists.find((x) => x.id === id);
  if (!l) throw new Error(`unknown list ${id}`);
  return l;
}

/** The Knesset page of a bill: params.BILL_URL with {id} replaced. */
export function billUrl(params: Params, id: string): string {
  return params.BILL_URL.replace('{id}', id);
}

/** Answered statements (not dk, not 0) where the list has a value, largest contribution first (stable). */
export function contributions(data: QuizData, listId: string, answers: Answers, mult: Mult = {}): Contribution[] {
  const lv = listVec(data, findList(data, listId));
  const rows: Contribution[] = [];
  for (const q of data.statements) {
    const a = answers[q.q];
    if (a === undefined || a === 'dk' || a === 0) continue;
    const p = lv.get(q.q);
    if (p === undefined) continue;
    const u = (a / 2) * q.key;
    rows.push({ c: q.w * (mult[q.q] ?? 1) * u * p, statement: q, a, u, p });
  }
  return rows
    .map((r) => ({ r, k: -r.c }))
    .sort((x, y) => (x.k < y.k ? -1 : x.k > y.k ? 1 : 0))
    .map((x) => x.r);
}

export interface Evidence {
  bill: string;
  sign: Sign;
  role: Role;
  /** Pushes the same way as the user's answer. */
  same: boolean;
  /** [position on the list, name], sorted. */
  authors: [number, string][];
}

/** Bills on the statement's direction with ≥1 sponsor among the list's ex-MKs; relevant first, then best list position. */
export function evidence(bills: QuizBills, listId: string, q: Statement, u: number, contrib: number): Evidence[] {
  const rows: { relevant: boolean; best: number; ev: Evidence }[] = [];
  for (const [bill, sign, role] of bills.by_direction[q.d] ?? []) {
    const b = bills.bills[bill];
    if (!b) continue;
    const authors: [number, string][] = [];
    for (const m of b.sponsors) {
      const mk = bills.mks[m];
      if (mk && mk.list === listId) authors.push([mk.list_position, mk.name_en]);
    }
    if (!authors.length) continue;
    const same = sign * (u > 0 ? 1 : -1) > 0;
    authors.sort((x, y) => x[0] - y[0] || (x[1] < y[1] ? -1 : x[1] > y[1] ? 1 : 0));
    rows.push({ relevant: contrib < 0 ? !same : same, best: authors[0]![0], ev: { bill, sign, role, same, authors } });
  }
  return rows
    .sort((x, y) => Number(!x.relevant) - Number(!y.relevant) || x.best - y.best)
    .map((x) => x.ev);
}

/** quiz_report.is_clear: one rule for «the list has a clear position». */
export function isClear(params: Params, p: number, nMk: number, nNames: number): boolean {
  return Math.abs(p) >= params.CLOSE && nMk >= params.MIN_CLEAR_MKS && nNames >= params.MIN_CLEAR_BILLS;
}

export type Side = 'for' | 'against' | 'noClear';
export interface VoteCounts { votes: number; other: number; gov: number }
/** One explanation line: a key of quiz_texts.json «explain» with its parameters (quiz_report.py explain()); strings.renderLines draws them. */
export type LineItem =
  | { key: 'quote'; text: string }
  | { key: 'answer'; answer: Exclude<AnswerValue, 0>; side: Side }
  | { key: 'basis'; bills: number; same: number; opp: number; votes: VoteCounts }
  | { key: 'basisVotesOnly'; votes: VoteCounts }
  | { key: 'weight' }
  | { key: 'caveatByVotes' }
  | { key: 'caveatPrice' };

export interface Explanation {
  lines: LineItem[];
  evidence: Evidence[];
}

/** One explained statement, exactly as quiz_report.explain(). */
export function explain(data: QuizData, bills: QuizBills, listId: string, q: Statement, a: Exclude<AnswerValue, 0>,
  p: number, contrib: number, mult: Mult = {}): Explanation {
  const list = findList(data, listId);
  const ev = evidence(bills, listId, q, (a / 2) * q.key, contrib);
  const nSame = ev.filter((e) => e.same).length;
  const nOpp = ev.length - nSame;
  const pos = list.positions[q.d];
  const close = !isClear(data.params, p, pos?.n_mk ?? 0, pos?.n_names ?? 0);
  const toward = !close && p * q.key > 0;
  const side: Side = close ? 'noClear' : toward ? 'for' : 'against';
  const votes: VoteCounts = { votes: pos?.n_votes ?? 0, other: pos?.n_other ?? 0, gov: pos?.n_gov ?? 0 };
  const lines: LineItem[] = [
    { key: 'quote', text: q.statement_en },
    { key: 'answer', answer: a, side },
    ev.length ? { key: 'basis', bills: ev.length, same: nSame, opp: nOpp, votes } : { key: 'basisVotesOnly', votes },
  ];
  if ((mult[q.q] ?? 1) !== 1) lines.push({ key: 'weight' });
  // The list's own bills give nothing or the other side: its side comes from the votes.
  const byVotes = ev.length > 0 && !!pos && (Math.abs(pos.P_bills) <= EPS || (pos.P_bills > 0) !== (pos.P > 0));
  if (!close && byVotes) lines.push({ key: 'caveatByVotes' });
  if (toward) lines.push({ key: 'caveatPrice' });
  return { lines, evidence: ev };
}
