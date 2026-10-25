/**
 * Migration tests Python -> TypeScript: every case of export/golden.json (computed by pipeline/quiz_match.py,
 * pipeline/quiz_flow.py and pipeline/quiz_report.py) must be reproduced. Python is the reference.
 */
import { describe, expect, it } from 'vitest';
import goldenRaw from '@export/golden.json';
import { bills, data } from '../testSources';
import { contributions, explain, match, nextClarify, shouldStop, tradeoffs } from './index';
import type { LineItem, NotePart } from './index';
import type { Answers, Mult, Role, Sign } from './types';

interface GoldenCase {
  name: string;
  answers: Answers;
  mult: Mult;
  ranking: { id: string; closeness: number | null; coverage: number; notes: NotePart[]; ranked: boolean }[];
  tradeoffs: { exclude: string[]; skip_lists: string[]; pairs: [string, string, string][] };
  details: {
    id: string;
    items: {
      q: string;
      contribution: number;
      p: number;
      lines: LineItem[];
      evidence: { bill: string; sign: Sign; role: Role; same: boolean; authors: [number, string][] }[];
    }[];
  }[];
  /** «flow N» cases: the statements asked, in order (quiz_flow.core, then next_clarify one at a time). */
  flow?: { core: string[]; clarifying: string[] };
}

const golden = goldenRaw as { tolerance: number; cases: GoldenCase[] };
const tol = golden.tolerance;

function close(actual: number | null, expected: number | null, what: string) {
  if (expected === null) {
    expect(actual, what).toBeNull();
    return;
  }
  expect(actual, what).not.toBeNull();
  expect(Math.abs((actual as number) - expected), `${what}: ${actual} vs ${expected}`).toBeLessThanOrEqual(tol);
}

describe('golden.json', () => {
  it('has the expected cases, including the flow cases', () => {
    expect(golden.cases.length).toBeGreaterThanOrEqual(34);
    expect(golden.cases.filter((c) => c.flow).length).toBeGreaterThanOrEqual(6);
  });

  for (const gc of golden.cases) {
    describe(gc.name, () => {
      it('ranking: order, closeness, coverage, notes, ranked flags', () => {
        const rows = match(data, gc.answers, gc.mult);
        expect(rows.map((r) => r.id)).toEqual(gc.ranking.map((r) => r.id));
        rows.forEach((r, i) => {
          const g = gc.ranking[i]!;
          close(r.closeness, g.closeness, `${r.id} closeness`);
          close(r.coverage, g.coverage, `${r.id} coverage`);
          expect(r.notes, `${r.id} notes`).toEqual(g.notes);
          expect(r.ranked, `${r.id} ranked`).toBe(g.ranked);
        });
      });

      it('trade-off pairs', () => {
        const t = gc.tradeoffs;
        expect(tradeoffs(data, gc.answers, gc.mult, t.exclude, t.skip_lists)).toEqual(t.pairs);
      });

      it('details: items, contributions, lines, evidence', () => {
        for (const d of gc.details) {
          const items = contributions(data, d.id, gc.answers, gc.mult);
          expect(items.map((x) => x.statement.q), `${d.id} item order`).toEqual(d.items.map((x) => x.q));
          items.forEach((x, i) => {
            const g = d.items[i]!;
            close(x.c, g.contribution, `${d.id}/${g.q} contribution`);
            close(x.p, g.p, `${d.id}/${g.q} p`);
            const ex = explain(data, bills, d.id, x.statement, x.a, x.p, x.c, gc.mult);
            expect(ex.lines, `${d.id}/${g.q} lines`).toEqual(g.lines);
            expect(ex.evidence, `${d.id}/${g.q} evidence`).toEqual(g.evidence);
          });
        }
      });

      if (gc.flow) {
        it('question order: the core, then every clarifying statement chosen from the answers so far', () => {
          const flow = gc.flow!;
          expect(flow.core).toEqual(data.core);
          // Replays export.flow_case(): the user answers what is asked; answers hold only those (incl. «don't know», 0).
          const asked = [...flow.core];
          const ans: Answers = {};
          for (const q of asked) if (gc.answers[q] !== undefined) ans[q] = gc.answers[q]!;
          const steps: string[] = [];
          while (!shouldStop(data.flow, data, ans, asked.length)) {
            const q = nextClarify(data, ans, asked);
            if (q === null) break;
            asked.push(q);
            if (gc.answers[q] !== undefined) ans[q] = gc.answers[q]!;
            steps.push(q);
          }
          expect(steps).toEqual(flow.clarifying);
          expect(ans).toEqual(gc.answers);
        });
      }
    });
  }
});
