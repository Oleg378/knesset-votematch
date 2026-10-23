/**
 * Migration tests Python -> TypeScript for the order of questions: the six «flow N» cases of export/golden.v2.json
 * (computed by pipeline/quiz_flow.py) must be reproduced question by question, and the ranked lists of every case must
 * match (ids and closeness to the golden tolerance). Python is the reference.
 */
import { describe, expect, it } from 'vitest';
import { core, data, golden } from '../test/files';
import { nextClarify, rankedLists, shouldStop } from './flow';
import type { Answers } from './types';

describe('golden.v2.json: order of questions (pipeline/quiz_flow.py)', () => {
  it('has six flow cases; the bundled core agrees with quiz_data', () => {
    expect(golden.cases.filter((c) => c.flow).length).toBe(6);
    expect(data.core).toEqual(core.core);
    expect(data.flow).toEqual(core.flow);
    expect(data.core.length).toBe(data.flow.core);
    expect(core.statements.map((s) => s.q).sort()).toEqual([...core.core].sort());
    for (const s of core.statements) expect(data.statements.find((x) => x.q === s.q)).toEqual(s);
  });

  for (const gc of golden.cases) {
    describe(gc.name, () => {
      it('ranked lists: order and closeness', () => {
        const rows = rankedLists(data, gc.answers, gc.mult);
        const expected = gc.ranking.filter((r) => r.ranked);
        expect(rows.map((r) => r.id)).toEqual(expected.map((r) => r.id));
        rows.forEach((r, i) => {
          expect(Math.abs(r.closeness - (expected[i]!.closeness as number)), `${r.id}`).toBeLessThanOrEqual(golden.tolerance);
        });
      });

      if (gc.flow) {
        const flow = gc.flow;
        it('core, then every clarifying statement in order', () => {
          expect(flow.core).toEqual(data.core);
          const shown = [...flow.core];
          const ans: Answers = {};
          for (const q of shown) if (gc.answers[q] !== undefined) ans[q] = gc.answers[q]!;
          const got: string[] = [];
          while (!shouldStop(data, ans, shown.length)) {
            const q = nextClarify(data, ans, shown);
            if (q === null) break;
            got.push(q);
            shown.push(q);
            if (gc.answers[q] !== undefined) ans[q] = gc.answers[q]!;
          }
          expect(got).toEqual(flow.clarifying);
          expect(shown.length).toBe(data.flow.core + data.flow.clarify);
        });
      }
    });
  }

  it('skips a statement of the same sim_group as a shown one, and the previous area, when alternatives exist', () => {
    const fc = golden.cases.find((c) => c.flow)!;
    const shown = [...fc.flow!.core];
    const ans: Answers = {};
    for (const q of shown) if (fc.answers[q] !== undefined) ans[q] = fc.answers[q]!;
    const q = nextClarify(data, ans, shown)!;
    const byQ = new Map(data.statements.map((s) => [s.q, s]));
    const picked = byQ.get(q)!;
    const last = byQ.get(shown[shown.length - 1]!)!;
    expect(picked.area).not.toBe(last.area);
    for (const s of shown) {
      const g = byQ.get(s)!.sim_group;
      if (g) expect(picked.sim_group).not.toBe(g);
    }
  });

  it('with nothing answered yet the pool still yields a statement; shown statements are never repeated', () => {
    const shown = [...data.core];
    for (let i = 0; i < 20; i++) {
      const q = nextClarify(data, {}, shown);
      expect(q).not.toBeNull();
      expect(shown).not.toContain(q);
      shown.push(q!);
    }
  });
});
