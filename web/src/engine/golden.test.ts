/**
 * Migration tests Python -> TypeScript: every case of export/golden.v1.json (computed by pipeline/quiz_match.py and
 * pipeline/quiz_report.py) must be reproduced. Python is the reference.
 */
import { describe, expect, it } from 'vitest';
import goldenRaw from '@export/golden.v1.json';
import { data } from '../data';
import { contributions, explain, match, tradeoffs } from './index';
import type { Answers, Mult, Role, Sign } from './types';

interface GoldenCase {
  name: string;
  answers: Answers;
  mult: Mult;
  ranking: { id: string; closeness: number | null; coverage: number; note: string; ranked: boolean }[];
  tradeoffs: { exclude: string[]; skip_lists: string[]; pairs: [string, string, string][] };
  details: {
    id: string;
    items: {
      q: string;
      contribution: number;
      p: number;
      lines: string[];
      evidence: { bill: string; sign: Sign; role: Role; same: boolean; authors: [number, string][] }[];
    }[];
  }[];
}

const golden = goldenRaw as { version: number; tolerance: number; cases: GoldenCase[] };
const tol = golden.tolerance;

function close(actual: number | null, expected: number | null, what: string) {
  if (expected === null) {
    expect(actual, what).toBeNull();
    return;
  }
  expect(actual, what).not.toBeNull();
  expect(Math.abs((actual as number) - expected), `${what}: ${actual} vs ${expected}`).toBeLessThanOrEqual(tol);
}

describe('golden.v1.json', () => {
  it('has the expected version and cases', () => {
    expect(golden.version).toBe(1);
    expect(golden.cases.length).toBeGreaterThanOrEqual(28);
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
            const ex = explain(data, d.id, x.statement, x.a, x.p, x.c, gc.mult);
            expect(ex.lines, `${d.id}/${g.q} lines`).toEqual(g.lines);
            expect(ex.evidence, `${d.id}/${g.q} evidence`).toEqual(g.evidence);
          });
        }
      });
    });
  }
});
