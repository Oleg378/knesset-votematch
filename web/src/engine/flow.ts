/**
 * Port of pipeline/quiz_flow.py: the order of questions — core (fixed, from the export) → clarifying (next_clarify, one at a
 * time from the answers so far) → trade-offs. Python is the reference: the golden «flow N» cases replay the sequence.
 */
import { match, rankedTop, listVec } from './match';
import type { Answers, Flow, Mult, QuizData } from './types';

/**
 * numpy's float64 sum (np.add.reduce): the first element, plus the pairwise sum of the rest (8 accumulators for blocks of
 * up to 128). Reproduced so that the standard deviations — and the ties between them — are bit-identical to Python.
 */
function pairwise(a: number[], from: number, n: number): number {
  if (n < 8) {
    let res = 0;
    for (let i = from; i < from + n; i++) res += a[i]!;
    return res;
  }
  if (n <= 128) {
    const r = a.slice(from, from + 8);
    let i = 8;
    for (; i < n - (n % 8); i += 8) for (let j = 0; j < 8; j++) r[j]! += a[from + i + j]!;
    let res = ((r[0]! + r[1]!) + (r[2]! + r[3]!)) + ((r[4]! + r[5]!) + (r[6]! + r[7]!));
    for (; i < n; i++) res += a[from + i]!;
    return res;
  }
  let n2 = Math.floor(n / 2);
  n2 -= n2 % 8;
  return pairwise(a, from, n2) + pairwise(a, from + n2, n - n2);
}

function npSum(a: number[]): number {
  return a.length ? a[0]! + pairwise(a, 1, a.length - 1) : 0;
}

/** np.std (population): sqrt(mean((x - mean(x))²)). */
export function npStd(a: number[]): number {
  const mean = npSum(a) / a.length;
  return Math.sqrt(npSum(a.map((x) => (x - mean) * (x - mean))) / a.length);
}

/** Questions asked before the trade-offs while the fixed number is used (the counter's total). */
export function plannedQuestions(flow: Flow): number {
  return flow.core + flow.clarify;
}

/** quiz_flow.should_stop: true when no more clarifying questions are needed. nAsked: core + clarifying shown so far. */
export function shouldStop(flow: Flow, data: QuizData | null, answers: Answers, nAsked: number, mult: Mult = {}): boolean {
  if (flow.stop_gap === null) return nAsked >= flow.core + flow.clarify;
  if (nAsked >= flow.max_questions) return true;
  if (nAsked < flow.min_questions || !data) return false;
  const rows = match(data, answers, mult).filter((r) => r.ranked);
  return rows.length > 1 && (rows[0]!.closeness as number) - (rows[1]!.closeness as number) >= flow.stop_gap;
}

/**
 * quiz_flow.next_clarify: among statements not asked yet, the one on which the compared lists differ most (population SD of
 * their values, at least 2 lists with a position); ties → the lower statement number. Compared lists: the top clarify_top
 * of the current ranking, or — with fewer than 2 ranked (e.g. nothing answered) — all lists with status ok.
 * null when the pool is exhausted. Like the reference flow, the trade-off weights are not used here.
 */
export function nextClarify(data: QuizData, answers: Answers, asked: ReadonlySet<string>): string | null {
  const answered = Object.values(answers).some((v) => v !== 'dk');
  const top = answered ? rankedTop(data, answers, data.flow.clarify_top) : [];
  const ids = top.length >= 2 ? top : data.lists.filter((l) => l.status === 'ok').map((l) => l.id);
  const byId = new Map(data.lists.map((l) => [l.id, l]));
  const vecs = ids.map((id) => listVec(data, byId.get(id)!));
  let best: { sd: number; n: number; q: string } | null = null;
  for (const st of data.statements) {
    if (asked.has(st.q)) continue;
    const p: number[] = [];
    for (const v of vecs) {
      const x = v.get(st.q);
      if (x !== undefined) p.push(x);
    }
    if (p.length < 2) continue;
    const sd = npStd(p);
    const n = Number.parseInt(st.q, 10);
    if (!best || sd > best.sd || (sd === best.sd && n < best.n)) best = { sd, n, q: st.q };
  }
  return best ? best.q : null;
}
