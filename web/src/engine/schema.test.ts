import { describe, expect, it } from 'vitest';
import Ajv2020 from 'ajv/dist/2020';
import schema from '@export/quiz_data.schema.json';
import { bills, core, data } from '../test/files';
import { sameBuild } from '../data';

describe('quiz_core / quiz_data / quiz_bills .json', () => {
  it('merged, validate against quiz_data.schema.json (draft 2020-12)', () => {
    const ajv = new Ajv2020({ allErrors: true, strict: true });
    // The schema uses format "date"; checked here without pulling in ajv-formats.
    ajv.addFormat('date', /^\d{4}-\d{2}-\d{2}$/);
    const validate = ajv.compile(schema as object);
    const ok = validate({ ...core, ...data, ...bills });
    expect(validate.errors ?? []).toEqual([]);
    expect(ok).toBe(true);
  });

  it('come from the same build', () => {
    expect(sameBuild(core, data)).toBe(true);
    expect(sameBuild(core, bills)).toBe(true);
  });
});
