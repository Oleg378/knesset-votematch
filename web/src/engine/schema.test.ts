import { describe, expect, it } from 'vitest';
import Ajv2020 from 'ajv/dist/2020';
import schema from '@export/quiz_data.v1.schema.json';
import raw from '@export/quiz_data.v1.json';

describe('quiz_data.v1.json', () => {
  it('validates against quiz_data.v1.schema.json (draft 2020-12)', () => {
    const ajv = new Ajv2020({ allErrors: true, strict: true });
    // The schema uses format "date"; checked here without pulling in ajv-formats.
    ajv.addFormat('date', /^\d{4}-\d{2}-\d{2}$/);
    const validate = ajv.compile(schema as object);
    const ok = validate(raw);
    expect(validate.errors ?? []).toEqual([]);
    expect(ok).toBe(true);
  });
});
