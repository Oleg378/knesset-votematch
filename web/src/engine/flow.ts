/**
 * Port of pipeline/quiz_flow.py (next_clarify, should_stop; rule of 2026-10-21): the order of questions —
 * core (read from the export) → clarifying, one at a time from the answers so far → trade-offs (match.ts).
 * Written by the data side (export/V2_HANDOFF.md section 0a, «do not re-port»); here only typed with the web's v2 types.
 * Python is the reference: the six «flow N» cases of export/golden.v2.json must be reproduced (flow.test.ts,
 * golden.test.ts). Keep the arithmetic in the same order as the Python.
 */
import type { Answers, Flow, Mult, Position, QuizData, QuizList } from './types';

interface Ctx {
  qs: string[];
  qi: Map<string, number>;
  /** Evaluated lists (status ok), in file order. */
  ok: QuizList[];
  okIndex: Map<string, number>;
  /** p[list][statement]: the list's value on the statement (NaN = no position); same for every ranked list. */
  p: Map<string, Float64Array>;
  clear: boolean[][];
  /** |r| between statements over evaluated lists that have both (0 if fewer than 3 or a constant column). */
  r: Float64Array[];
}

const ctxCache = new WeakMap<QuizData, Ctx>();

/** quiz_match.list_vec: p = P when K = 0, else P * e / (e + K). */
function listValue(x: Position, k: number): number {
  return k === 0 ? x.P : (x.P * x.e) / (x.e + k);
}

function isClear(data: QuizData, x: Position): boolean {
  const { CLOSE, MIN_CLEAR_MKS, MIN_CLEAR_BILLS } = data.params;
  return Math.abs(x.P) >= CLOSE && x.n_mk >= MIN_CLEAR_MKS && x.n_names >= MIN_CLEAR_BILLS;
}

function ctxOf(data: QuizData): Ctx {
  const cached = ctxCache.get(data);
  if (cached) return cached;
  const qs = data.statements.map((s) => s.q);
  const qi = new Map(qs.map((q, i) => [q, i]));
  const ok = data.lists.filter((l) => l.status === 'ok');
  const okIndex = new Map(ok.map((l, i) => [l.id, i]));
  const p = new Map<string, Float64Array>();
  for (const l of data.lists) {
    if (l.status === 'not_evaluated') continue;
    const v = new Float64Array(qs.length).fill(Number.NaN);
    data.statements.forEach((s, j) => {
      const x = l.positions[s.d];
      if (x) v[j] = listValue(x, data.params.K);
    });
    p.set(l.id, v);
  }
  const clear = ok.map((l) => data.statements.map((s) => {
    const x = l.positions[s.d];
    return x ? isClear(data, x) : false;
  }));
  // pairwise |r| (numpy corrcoef) over evaluated lists with both positions
  const r = qs.map(() => new Float64Array(qs.length));
  const cols = qs.map((_, j) => ok.map((l) => p.get(l.id)![j]!));
  for (let a = 0; a < qs.length; a++) {
    for (let b = a + 1; b < qs.length; b++) {
      const xs: number[] = [];
      const ys: number[] = [];
      ok.forEach((_, i) => {
        const x = cols[a]![i]!;
        const y = cols[b]![i]!;
        if (!Number.isNaN(x) && !Number.isNaN(y)) { xs.push(x); ys.push(y); }
      });
      if (xs.length < 3) continue;
      const mx = xs.reduce((s, v) => s + v, 0) / xs.length;
      const my = ys.reduce((s, v) => s + v, 0) / ys.length;
      let sxy = 0; let sxx = 0; let syy = 0;
      for (let i = 0; i < xs.length; i++) {
        const dx = xs[i]! - mx; const dy = ys[i]! - my;
        sxy += dx * dy; sxx += dx * dx; syy += dy * dy;
      }
      if (sxx === 0 || syy === 0) continue;
      const v = Math.abs(sxy / Math.sqrt(sxx * syy));
      r[a]![b] = v; r[b]![a] = v;
    }
  }
  const ctx: Ctx = { qs, qi, ok, okIndex, p, clear, r };
  ctxCache.set(data, ctx);
  return ctx;
}

export interface RankedRow { id: string; closeness: number; }

/**
 * Ranked lists in order with their closeness — the rule of the Results screen (quiz_match.match / is_ranked):
 * cosine over answered statements the list has a position on; ranked when finite, coverage >= MIN_COVERAGE and
 * ex_mks >= MIN_EX_MKS. Sort key (-closeness), stable: ties keep the file order of lists.
 */
export function rankedLists(data: QuizData, answers: Answers, mult: Mult = {}): RankedRow[] {
  const ctx = ctxOf(data);
  const rows: RankedRow[] = [];
  for (const l of data.lists) {
    if (l.status === 'not_evaluated' || l.ex_mks < data.params.MIN_EX_MKS) continue;
    const v = ctx.p.get(l.id)!;
    let num = 0; let uu = 0; let pp = 0; let wa = 0; let wc = 0;
    data.statements.forEach((s, j) => {
      const a = answers[s.q];
      if (a === undefined || a === 'dk') return;
      const u = (a / 2) * s.key;
      const w = s.w * (mult[s.q] ?? 1);
      wa += w;
      const pv = v[j]!;
      if (Number.isNaN(pv)) return;
      wc += w;
      num += w * u * pv; uu += w * u * u; pp += w * pv * pv;
    });
    const cos = uu > 0 && pp > 0 ? num / Math.sqrt(uu * pp) : Number.NaN;
    const cov = wa ? wc / wa : 0;
    if (Number.isNaN(cos) || cov < data.params.MIN_COVERAGE) continue;
    rows.push({ id: l.id, closeness: cos });
  }
  return rows.sort((x, y) => y.closeness - x.closeness);
}

/** Questions asked before the trade-offs while the fixed number is used (the counter's total). */
export function plannedQuestions(flow: Flow): number {
  return flow.core + flow.clarify;
}

/**
 * quiz_flow.should_stop: true when no more clarifying questions are needed. nAsked: core + clarifying shown so far.
 * With the fixed number (stop_gap null) the data file is not needed yet.
 */
export function shouldStop(flow: Flow, data: QuizData | null, answers: Answers, nAsked: number, mult: Mult = {}): boolean {
  if (flow.stop_gap === null) return nAsked >= flow.core + flow.clarify;
  if (nAsked >= flow.max_questions) return true;
  if (nAsked < flow.min_questions || !data) return false;
  const rows = rankedLists(data, answers, mult);
  return rows.length > 1 && rows[0]!.closeness - rows[1]!.closeness >= flow.stop_gap;
}

/**
 * quiz_flow.next_clarify: the next clarifying statement, or null when the pool is exhausted.
 * shown: statements already shown (answered, skipped or «don't know»), in the order shown.
 */
export function nextClarify(data: QuizData, answers: Answers, shown: string[], mult: Mult = {}): string | null {
  const ctx = ctxOf(data);
  const f = data.flow;
  const st = data.statements;
  const shownSet = new Set(shown);
  const shownI = shown.filter((q) => ctx.qi.has(q)).map((q) => ctx.qi.get(q)!);
  let cand = st.map((_, j) => j).filter((j) => !shownSet.has(ctx.qs[j]!));
  const sameGroup = (a: number, b: number) => {
    const g = st[a]!.sim_group;
    return g !== null && g !== '' && g === st[b]!.sim_group;
  };
  if (f.sim_groups) {
    const c = cand.filter((j) => !shownI.some((s) => sameGroup(j, s)));
    if (c.length) cand = c;
  }
  if (shownI.length) {
    const last = f.same_area_in_row ? null : st[shownI[shownI.length - 1]!]!.area;
    const far = (j: number) => shownI.every((s) => ctx.r[j]![s]! < f.near_dup_r);
    const c1 = cand.filter((j) => st[j]!.area !== last && far(j));
    const c0 = cand.filter((j) => st[j]!.area !== last);
    cand = c1.length ? c1 : c0.length ? c0 : cand;
  }
  const answered = Object.values(answers).some((v) => v !== 'dk');
  const ranked = answered ? rankedLists(data, answers, mult) : [];
  const top = ranked.slice(0, f.clarify_top).filter((r) => ctx.okIndex.has(r.id)).map((r) => ctx.okIndex.get(r.id)!);
  if (top.length >= 2) {
    const c2 = cand.filter((j) => {
      const c = top.filter((i) => ctx.clear[i]![j]).map((i) => ctx.p.get(ctx.ok[i]!.id)![j]!);
      return c.length > 0 && c.some((x) => x > 0) && c.some((x) => x < 0);
    });
    if (c2.length) cand = c2;
  }
  if (!cand.length) return null;
  const okRanked = ranked.filter((r) => ctx.okIndex.has(r.id));
  const score = new Float64Array(st.length).fill(Number.NEGATIVE_INFINITY);
  if (okRanked.length >= 2) {
    const lead = okRanked[0]!;
    const rest = okRanked.slice(1, f.clarify_top);
    let cont = rest.filter((r) => lead.closeness - r.closeness < f.pair_gap);
    if (!cont.length) cont = rest.slice(0, 1);
    const pl = ctx.p.get(lead.id)!;
    for (const j of cand) {
      if (Number.isNaN(pl[j]!)) continue;
      let s = 0;
      for (const c of cont) {
        const pc = ctx.p.get(c.id)![j]!;
        if (Number.isNaN(pc)) continue;
        s += Math.abs(pl[j]! - pc) / (lead.closeness - c.closeness + f.pair_eps);
      }
      if (s > 0) score[j] = s;
    }
  } else {
    for (const j of cand) {
      const v = ctx.ok.map((l) => ctx.p.get(l.id)![j]!).filter((x) => !Number.isNaN(x));
      if (v.length < 2) continue;
      const m = v.reduce((a, b) => a + b, 0) / v.length;
      score[j] = Math.sqrt(v.reduce((a, b) => a + (b - m) * (b - m), 0) / v.length);
    }
  }
  for (const j of cand) {
    const s = score[j]!;
    if (Number.isFinite(s) && s > 0) score[j] = s * Math.pow(st[j]!.interest / 5, f.interest_alpha);
  }
  let best = cand[0]!;
  for (const j of cand) {
    const sj = score[j]!; const sb = score[best]!;
    if (sj > sb || (sj === sb && Number(ctx.qs[j]) < Number(ctx.qs[best]))) best = j;
  }
  return Number.isFinite(score[best]!) ? ctx.qs[best]! : null;
}
