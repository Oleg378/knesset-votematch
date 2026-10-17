/**
 * Port of pipeline/quiz_report.py: contributions, evidence, explain. Strings come from src/strings.ts and must reproduce
 * the golden `lines` exactly.
 */
import { ANS, explainText as T } from '../strings';
import { listVec } from './match';
import type { AnswerValue, Answers, Mult, QuizData, QuizList, Role, Sign, Statement } from './types';

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
export function evidence(data: QuizData, listId: string, q: Statement, u: number, contrib: number): Evidence[] {
  const rows: { relevant: boolean; best: number; ev: Evidence }[] = [];
  for (const [bill, sign, role] of data.by_direction[q.d] ?? []) {
    const b = data.bills[bill];
    if (!b) continue;
    const authors: [number, string][] = [];
    for (const m of b.sponsors) {
      const mk = data.mks[m];
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

export interface Explanation {
  lines: string[];
  evidence: Evidence[];
}

/** One explained statement, exactly as quiz_report.explain(). */
export function explain(data: QuizData, listId: string, q: Statement, a: Exclude<AnswerValue, 0>, p: number,
  contrib: number, mult: Mult = {}): Explanation {
  const list = findList(data, listId);
  const ev = evidence(data, listId, q, (a / 2) * q.key, contrib);
  const nSame = ev.filter((e) => e.same).length;
  const nOpp = ev.length - nSame;
  const nVotes = list.positions[q.d]?.n_votes ?? 0;
  const side = p * q.key > 0 ? T.sideFor : T.sideAgainst;
  const lines = [
    T.quote(q.statement_en),
    T.answer(ANS[a], side),
    ev.length ? T.basis(ev.length, nSame, nOpp, nVotes) : T.basisVotesOnly(nVotes),
  ];
  if ((mult[q.q] ?? 1) !== 1) lines.push(T.weight);
  if (ev.length && contrib > 0 && nOpp > nSame) lines.push(T.caveatFits);
  if (ev.length && contrib < 0 && nSame > nOpp) lines.push(T.caveatMisfits);
  return { lines, evidence: ev };
}
