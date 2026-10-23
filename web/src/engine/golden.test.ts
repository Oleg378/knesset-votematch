/**
 * Migration tests Python -> TypeScript: every case of export/golden.json (computed by pipeline/quiz_match.py and
 * pipeline/quiz_report.py) must be reproduced: ranking, trade-off pairs, list details. Python is the reference.
 * The question order of the «flow N» cases is checked in flow.test.ts.
 */
import { describe, expect, it } from 'vitest';
import { bills, data, golden } from '../test/files';
import { contributions, explain, match, tradeoffs } from './index';

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
  it('has the expected version and cases', () => {
    expect(golden.cases.length).toBeGreaterThanOrEqual(34);
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
          expect(r.note, `${r.id} note`).toBe(g.note);
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
    });
  }

  it('a list resting on fewer than MIN_EX_MKS former MKs is shown but never ranked', () => {
    const few = data.lists.filter((l) => l.status !== 'not_evaluated' && l.ex_mks < data.params.MIN_EX_MKS);
    expect(few.length).toBeGreaterThan(0);
    const answers = Object.fromEntries(data.statements.map((s) => [s.q, 2 as const]));
    for (const r of match(data, answers)) {
      if (few.some((l) => l.id === r.id)) expect(r.ranked, r.id).toBe(false);
    }
  });
});
