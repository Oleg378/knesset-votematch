import { describe, expect, it } from 'vitest';
import Ajv2020 from 'ajv/dist/2020';
import schema from '@export/quiz_data.schema.json';
import { bills, core, data } from '../testSources';

describe('the three data files', () => {
  it('quiz_data + quiz_bills merged validate against quiz_data.schema.json (draft 2020-12)', () => {
    const ajv = new Ajv2020({ allErrors: true, strict: true });
    // The schema uses format "date"; checked here without pulling in ajv-formats.
    ajv.addFormat('date', /^\d{4}-\d{2}-\d{2}$/);
    const validate = ajv.compile(schema as object);
    const ok = validate({ ...data, ...bills });
    expect(validate.errors ?? []).toEqual([]);
    expect(ok).toBe(true);
  });

  it('quiz_core is the head of quiz_data: same export, flow and core, the core statements in core order', () => {
    for (const k of ['generated', 'source_commit'] as const) {
      expect(core[k]).toBe(data[k]);
      expect(bills[k]).toBe(data[k]);
    }
    expect(core.flow).toEqual(data.flow);
    expect(core.core).toEqual(data.core);
    const byQ = new Map(data.statements.map((s) => [s.q, s]));
    for (const s of core.statements) expect(s).toEqual(byQ.get(s.q));
    expect(new Set(core.statements.map((s) => s.q))).toEqual(new Set(core.core));
  });
});
