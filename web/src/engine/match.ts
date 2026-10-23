/**
 * Port of pipeline/quiz_match.py (list_vec, score, match, is_ranked, ranked_top, tradeoffs). Python is the reference:
 * export/golden.v2.json must be reproduced to 1e-9 (src/engine/golden.test.ts). Keep the arithmetic in the same order.
 */
import { pyPercent0 } from './format';
import type { Answers, ListStatus, Mult, QuizData, QuizList, TradePair } from './types';
import { noteFewMks, noteLowCoverage, noteNoRecord, NOTE_JOIN } from '../strings';

/** Statement q -> list value p = P when K = 0, else P * e / (e + K); only statements whose direction has a position. */
export type ListVec = Map<string, number>;

const vecCache = new WeakMap<QuizData, Map<string, ListVec>>();

export function listVec(data: QuizData, list: QuizList): ListVec {
  let byList = vecCache.get(data);
  if (!byList) {
    byList = new Map();
    vecCache.set(data, byList);
  }
  const cached = byList.get(list.id);
  if (cached) return cached;
  const k = data.params.K;
  const v: ListVec = new Map();
  for (const r of data.statements) {
    const x = list.positions[r.d];
    if (x) v.set(r.q, k === 0 ? x.P : (x.P * x.e) / (x.e + k));
  }
  byList.set(list.id, v);
  return v;
}

/** [closeness (NaN when undefined), coverage]. dk and missing answers are skipped; 0 counts in the answered weight. */
export function score(data: QuizData, answers: Answers, lv: ListVec, mult: Mult = {}): [number, number] {
  let num = 0;
  let uu = 0;
  let pp = 0;
  let wa = 0;
  let wc = 0;
  for (const r of data.statements) {
    const a = answers[r.q];
    if (a === undefined || a === 'dk') continue;
    const u = (a / 2) * r.key;
    const w = r.w * (mult[r.q] ?? 1);
    wa += w;
    const p = lv.get(r.q);
    if (p === undefined) continue;
    wc += w;
    num += w * u * p;
    uu += w * u * u;
    pp += w * p * p;
  }
  const cos = uu > 0 && pp > 0 ? num / Math.sqrt(uu * pp) : Number.NaN;
  return [cos, wa ? wc / wa : 0];
}

export interface MatchRow {
  id: string;
  name_en: string;
  status: ListStatus;
  ex_mks: number;
  /** false for status not_evaluated (Python closeness None). */
  evaluated: boolean;
  /** null when not evaluated or not computable (Python None / NaN). */
  closeness: number | null;
  coverage: number;
  note: string;
  /** quiz_match.is_ranked: a closeness exists, coverage >= MIN_COVERAGE and ex_mks >= MIN_EX_MKS. */
  ranked: boolean;
}

export function match(data: QuizData, answers: Answers, mult: Mult = {}): MatchRow[] {
  const { MIN_COVERAGE: minCov, MIN_EX_MKS: minMks } = data.params;
  const rows: MatchRow[] = data.lists.map((l) => {
    if (l.status === 'not_evaluated') {
      return { id: l.id, name_en: l.name_en, status: l.status, ex_mks: 0, evaluated: false, closeness: null, coverage: 0,
        note: noteNoRecord, ranked: false };
    }
    const [cos, cv] = score(data, answers, listVec(data, l), mult);
    let note = l.status === 'warning' ? noteFewMks(l.ex_mks) : '';
    if (cv < minCov) note = (note ? note + NOTE_JOIN : '') + noteLowCoverage(pyPercent0(cv));
    const finite = !Number.isNaN(cos);
    return { id: l.id, name_en: l.name_en, status: l.status, ex_mks: l.ex_mks, evaluated: true,
      closeness: finite ? cos : null, coverage: cv, note, ranked: finite && cv >= minCov && l.ex_mks >= minMks };
  });
  // key (not ranked, closeness is None, -(closeness if ranked else 0)); Array.prototype.sort is stable (lists order).
  const key = (r: MatchRow): [number, number, number] => [r.ranked ? 0 : 1, r.evaluated ? 0 : 1,
    -(r.ranked ? (r.closeness as number) : 0)];
  return rows
    .map((r) => ({ r, k: key(r) }))
    .sort((x, y) => x.k[0] - y.k[0] || x.k[1] - y.k[1] || cmpNum(x.k[2], y.k[2]))
    .map((x) => x.r);
}

export function rankedTop(data: QuizData, answers: Answers, n: number, mult: Mult = {}): string[] {
  return match(data, answers, mult)
    .filter((r) => r.ranked)
    .slice(0, n)
    .map((r) => r.id);
}

function cmpNum(a: number, b: number): number {
  return a < b ? -1 : a > b ? 1 : 0;
}

/** Python string order (code points); statement numbers are ASCII. */
function cmpStr(a: string, b: string): number {
  return a < b ? -1 : a > b ? 1 : 0;
}

/** Python tuple order of (c, q). */
function cmpTuple(x: [number, string], y: [number, string]): number {
  return cmpNum(x[0], y[0]) || cmpStr(x[1], y[1]);
}

function sameOrder(a: string[], b: string[]): boolean {
  return a.length === b.length && a.every((x, i) => x === b[i]);
}

/**
 * Trade-off pairs (Python tradeoffs()): for each list in the current ranked top (in order, skipping skipLists), the first
 * statement pair (best «plus» vs first «minus») such that doubling either side changes the ordered top TRADE_TOP.
 */
export function tradeoffs(data: QuizData, answers: Answers, mult: Mult = {}, exclude: Iterable<string> = [],
  skipLists: Iterable<string> = []): TradePair[] {
  const { TRADE_TOP, TRADE_W, MAX_TRADE, TRADE_CANDIDATES } = data.params;
  const m: Mult = { ...mult };
  const base = rankedTop(data, answers, TRADE_TOP, m);
  const used = new Set(exclude);
  const skip = new Set(skipLists);
  const out: TradePair[] = [];
  const byId = new Map(data.lists.map((l) => [l.id, l]));
  for (const L of base) {
    if (skip.has(L)) continue;
    const lv = listVec(data, byId.get(L) as QuizList);
    const rows: [number, string][] = [];
    for (const r of data.statements) {
      const a = answers[r.q];
      if (a === undefined || a === 'dk' || a === 0) continue;
      const p = lv.get(r.q);
      if (p === undefined) continue;
      rows.push([((r.w * a) / 2) * r.key * p, r.q]);
    }
    const plus = [...rows].sort((x, y) => cmpTuple(y, x))
      .filter(([c, q]) => c > 0 && !used.has(q)).slice(0, TRADE_CANDIDATES).map(([, q]) => q);
    const minus = [...rows].sort(cmpTuple)
      .filter(([c, q]) => c < 0 && !used.has(q)).slice(0, TRADE_CANDIDATES).map(([, q]) => q);
    for (const qa of plus) {
      let hit: string | null = null;
      for (const qb of minus) {
        const changes = [qa, qb].some((q) =>
          !sameOrder(rankedTop(data, answers, TRADE_TOP, { ...m, [q]: (m[q] ?? 1) * TRADE_W }), base));
        if (changes) {
          hit = qb;
          break;
        }
      }
      if (hit !== null) {
        out.push([qa, hit, L]);
        used.add(qa);
        used.add(hit);
        break;
      }
    }
    if (out.length >= MAX_TRADE) break;
  }
  return out;
}
