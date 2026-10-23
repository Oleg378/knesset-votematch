import { describe, expect, it } from 'vitest';
import * as z from 'zod/mini';
import methodologyRaw from '@export/quiz_methodology.json';
import schemaOnDisk from '@export/quiz_methodology.schema.json';
import { data, methodology } from './testSources';
import { DATA_PLACEHOLDERS, dataValues, fill, MethodologySchema, parseMethodology, templatePattern } from './methodology';
import { jsonSchema } from './methodologyJsonSchema';

describe('quiz_methodology.json', () => {
  it('parses against the zod schema', () => {
    expect(() => parseMethodology(methodologyRaw)).not.toThrow();
    expect(methodology.sections.length).toBeGreaterThan(5);
  });

  it('export/quiz_methodology.schema.json is the schema generated from methodology.ts (npm run schema:methodology)', () => {
    expect(schemaOnDisk).toEqual(JSON.parse(JSON.stringify(jsonSchema())));
  });

  it('every text of the file fills with the numbers of quiz_data, with no placeholder left', () => {
    const v = dataValues(data);
    const texts: string[] = [];
    for (const s of methodology.sections) {
      texts.push(fill(s.title, v));
      if (s.text) texts.push(fill(s.text, v));
      if (s.after) texts.push(fill(s.after, v));
      for (const b of s.bullets ?? []) texts.push(fill(b.lead, v), fill(b.text, v));
    }
    for (const t of texts) expect(t).not.toMatch(/[{}]/);
    expect(texts.join('\n')).toContain(`${v.evaluable} of ${v.lists} lists can be evaluated`);
  });

  it('rejects an unknown placeholder, a stray brace and an unknown field', () => {
    const bad = (section: object) => z.safeParse(MethodologySchema, { ...methodology, sections: [section] }).success;
    expect(bad({ title: 'T', text: 'ok {lists}' })).toBe(true);
    expect(bad({ title: 'T', text: '{nonsense}' })).toBe(false);
    expect(bad({ title: 'T', text: 'a { b' })).toBe(false);
    expect(bad({ title: 'T', text: 'x', extra: 1 })).toBe(false);
    expect(z.safeParse(MethodologySchema, { ...methodology, statements: { ...methodology.statements, topic: '{n}' } }).success)
      .toBe(false);
  });
});

describe('fill', () => {
  it('replaces {name} and chooses {name?one|many} by the value', () => {
    expect(fill('{n} {n?list|lists}', { n: 1 })).toBe('1 list');
    expect(fill('{n} {n?list has|lists have}', { n: 22 })).toBe('22 lists have');
    expect(fill('spread {min_spread}', { min_spread: 0.25 })).toBe('spread 0.25');
    expect(() => fill('{other}', { n: 1 })).toThrow(/unknown placeholder/);
  });

  it('the template pattern accepts exactly the listed names', () => {
    const re = new RegExp(templatePattern(DATA_PLACEHOLDERS));
    expect(re.test('plain text, «quotes», 98 % and — dashes')).toBe(true);
    expect(re.test('{lists} {single?list|lists}')).toBe(true);
    expect(re.test('{Lists}')).toBe(false);
    expect(re.test('{single?a|b|c}')).toBe(false);
  });
});

describe('dataValues', () => {
  it('counts the lists as the results do and reads the thresholds from params', () => {
    const v = dataValues(data);
    expect(v.evaluable + v.single + v.no_record).toBe(data.lists.length);
    expect(v.vote_ratio).toBe(Math.round(1 / data.params.VOTE_WEIGHT));
    expect(v.min_lists).toBe(data.params.SELECT_MIN_LISTS);
    expect(v.core).toBe(data.flow.core);
  });
});
