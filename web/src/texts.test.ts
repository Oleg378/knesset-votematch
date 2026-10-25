import { describe, expect, it } from 'vitest';
import * as z from 'zod/mini';
import textsRaw from '@export/quiz_texts.json';
import schemaOnDisk from '@export/quiz_texts.schema.json';
import { data } from './testSources';
import {
  DATA_PLACEHOLDERS, dataValues, fill, parseTexts, PLACEHOLDERS, SECTION_LISTS_PLACEHOLDERS, STATEMENT_PLACEHOLDERS,
  STEP_PLACEHOLDERS, T,
  templatePattern, TextsSchema, type Texts,
} from './texts';
import { jsonSchema } from './textsJsonSchema';
import { fewMksNote } from './engine';
import { renderNote, renderNotePart } from './strings';

/** Sample values for the given names: every name gets `v`. */
const sample = (names: readonly string[], v: number | string) => Object.fromEntries(names.map((n) => [n, v]));

/** Every template of the file with the names it may use. */
function allTemplates(t: Texts): [string, string, readonly string[]][] {
  const out: [string, string, readonly string[]][] = [];
  for (const [section, map] of Object.entries(PLACEHOLDERS)) {
    for (const [key, names] of Object.entries(map)) {
      out.push([`${section}.${key}`, (t as unknown as Record<string, Record<string, string>>)[section]![key]!, names]);
    }
  }
  for (const [k, v] of Object.entries(t.answers)) out.push([`answers.${k}`, v, []]);
  for (const [k, v] of Object.entries(t.answerButtons)) out.push([`answerButtons.${k}`, v, []]);
  t.start.steps.forEach((s, i) => out.push([`start.steps.${i}`, s, STEP_PLACEHOLDERS]));
  out.push(['methodology.heading', t.methodology.heading, []]);
  t.methodology.sections.forEach((s, i) => {
    out.push([`methodology.sections.${i}.title`, s.title, []]);
    if (s.text !== undefined) out.push([`methodology.sections.${i}.text`, s.text, DATA_PLACEHOLDERS]);
    if (s.after !== undefined) out.push([`methodology.sections.${i}.after`, s.after, DATA_PLACEHOLDERS]);
    if (s.lists?.title !== undefined) {
      out.push([`methodology.sections.${i}.lists.title`, s.lists.title, SECTION_LISTS_PLACEHOLDERS]);
    }
    s.bullets?.forEach((b, j) => out.push(
      [`methodology.sections.${i}.bullets.${j}.lead`, b.lead, DATA_PLACEHOLDERS],
      [`methodology.sections.${i}.bullets.${j}.text`, b.text, DATA_PLACEHOLDERS],
    ));
  });
  for (const [key, names] of Object.entries(STATEMENT_PLACEHOLDERS)) {
    out.push([`methodology.statements.${key}`, t.methodology.statements[key as keyof typeof STATEMENT_PLACEHOLDERS], names]);
  }
  return out;
}

const ok = (patch: (t: Texts) => unknown) => z.safeParse(TextsSchema, patch(structuredClone(T))).success;

describe('quiz_texts.json', () => {
  it('parses against the zod schema (the app parses it once, at load)', () => {
    expect(() => parseTexts(textsRaw)).not.toThrow();
    expect(T.methodology.sections.length).toBeGreaterThan(5);
    expect(T.start.steps).toHaveLength(3);
  });

  it('export/quiz_texts.schema.json is the schema generated from texts.ts (npm run schema:texts)', () => {
    expect(schemaOnDisk).toEqual(JSON.parse(JSON.stringify(jsonSchema())));
  });

  it('every template fills with sample values for its allowed names and leaves no brace', () => {
    const all = allTemplates(T);
    expect(all.length).toBeGreaterThan(150);
    for (const [where, text, names] of all) {
      for (const v of [1, 2, 'x']) {
        const filled = fill(text, sample(names, v));
        expect(filled, where).not.toMatch(/[{}]/);
        expect(filled.length, where).toBeGreaterThan(0);
      }
    }
  });

  it('the methodology sections fill with the numbers of quiz_data', () => {
    const v = dataValues(data);
    // a bullet as shown: its lead, a space, its text
    const texts = T.methodology.sections.flatMap((s) =>
      [s.text, s.after, ...(s.bullets ?? []).map((b) => `${b.lead} ${b.text}`)].filter((x): x is string => !!x));
    const filled = texts.map((t) => fill(t, v)).join('\n');
    expect(filled).not.toMatch(/[{}]/);
    expect(filled).toContain(`${v.evaluable} of ${v.lists} lists`);
  });

  it('rejects an unknown placeholder, a stray brace, an unknown key and a wrong answers key', () => {
    expect(ok((t) => t)).toBe(true);
    // a placeholder of another key, or a typo
    expect(ok((t) => ({ ...t, details: { ...t.details, fits: '{n} {count}' } }))).toBe(false);
    expect(ok((t) => ({ ...t, explain: { ...t.explain, votes: '{votes} {other}{goverment}' } }))).toBe(false);
    // a key with no placeholders takes none
    expect(ok((t) => ({ ...t, app: { ...t.app, title: 'Quiz {n}' } }))).toBe(false);
    expect(ok((t) => ({ ...t, methodology: { ...t.methodology, statements: { ...t.methodology.statements, topic: '{n}' } } })))
      .toBe(false);
    expect(ok((t) => ({ ...t, start: { ...t.start, steps: ['{n}', '{top}', '{total}'] } }))).toBe(false);
    expect(ok((t) => ({ ...t, methodology: { ...t.methodology, sections: [{ title: 'T', text: '{nonsense}' }] } }))).toBe(false);
    // a section's lists: `of` from the enum, the title takes only {n}
    const listsSection = (lists: unknown) => (t: Texts) =>
      ({ ...t, methodology: { ...t.methodology, sections: [{ title: 'T', text: 'x', lists }] } });
    expect(ok(listsSection({ of: 'no_record', title: 'No record ({n})' }))).toBe(true);
    expect(ok(listsSection({ of: 'single', title: '{n} {n?list|lists}' }))).toBe(true);
    expect(ok(listsSection({ of: 'nonsense', title: 'No record ({n})' }))).toBe(false);
    expect(ok(listsSection({ of: 'no_record', title: 'No record ({x})' }))).toBe(false);
    expect(ok(listsSection({ of: 'no_record', title: 'No record ({lists})' }))).toBe(false);
    expect(ok(listsSection({ of: 'no_record' }))).toBe(true); // no title: the names follow the text
    expect(ok(listsSection({ title: 'No record ({n})' }))).toBe(false);
    expect(ok(listsSection({ of: 'no_record', title: 'T', extra: 1 }))).toBe(false);
    // no `collapsed`: a card collapses by its length (MethodologyScreen.tsx), not by a flag
    expect(ok((t) => ({ ...t, methodology: { ...t.methodology, sections: [{ title: 'T', text: 'x', collapsed: true }] } })))
      .toBe(false);
    expect(ok((t) => ({ ...t, methodology: { ...t.methodology, statements: { ...t.methodology.statements, collapsed: true } } })))
      .toBe(false);
    // a stray brace
    expect(ok((t) => ({ ...t, results: { ...t.results, basedOn: 'Based on {n of {total}' } }))).toBe(false);
    expect(ok((t) => ({ ...t, nav: { ...t.nav, next: 'Next }' } }))).toBe(false);
    // an unknown key, a missing key
    expect(ok((t) => ({ ...t, menu: { ...t.menu, extra: 'x' } }))).toBe(false);
    expect(ok((t) => ({ ...t, extra: {} }))).toBe(false);
    expect(ok((t) => ({ ...t, methodology: { ...t.methodology, sections: [{ title: 'T', text: 'x', extra: 1 }] } }))).toBe(false);
    expect(ok((t) => {
      const { chipTime: _, ...start } = t.start;
      return { ...t, start };
    })).toBe(false);
    // answers: exactly the five values; the buttons also «dk»
    expect(ok((t) => ({ ...t, answers: { ...t.answers, '3': 'x' } }))).toBe(false);
    expect(ok((t) => ({ ...t, answers: { ...t.answers, dk: 'x' } }))).toBe(false);
    expect(ok((t) => {
      const { '-2': _, ...answers } = t.answers;
      return { ...t, answers: { ...answers, '-3': 'x' } };
    })).toBe(false);
    expect(ok((t) => {
      const { dk: _, ...answerButtons } = t.answerButtons;
      return { ...t, answerButtons };
    })).toBe(false);
    // start.steps: exactly three
    expect(ok((t) => ({ ...t, start: { ...t.start, steps: [...t.start.steps, 'Four'] } }))).toBe(false);
    expect(ok((t) => ({ ...t, start: { ...t.start, steps: t.start.steps.slice(0, 2) } }))).toBe(false);
  });
});

describe('fill', () => {
  it('replaces {name} and chooses {name?one|many} by the value', () => {
    expect(fill('{n} {n?list|lists}', { n: 1 })).toBe('1 list');
    expect(fill('{n} {n?list has|lists have}', { n: 22 })).toBe('22 lists have');
    expect(fill('spread {min_spread}', { min_spread: 0.25 })).toBe('spread 0.25');
    expect(fill('a{gov} b', { gov: '' })).toBe('a b');
    expect(fill('“{text}”', { text: 'costs $1 {x}' })).toBe('“costs $1 {x}”');
    expect(() => fill('{other}', { n: 1 })).toThrow(/unknown placeholder/);
  });

  it('the template pattern accepts exactly the listed names', () => {
    const re = new RegExp(templatePattern(DATA_PLACEHOLDERS));
    expect(re.test('plain text, «quotes», 98 % and — dashes')).toBe(true);
    expect(re.test('{lists} {single?list|lists}')).toBe(true);
    expect(re.test('{Lists}')).toBe(false);
    expect(re.test('{single?a|b|c}')).toBe(false);
    const none = new RegExp(templatePattern([]));
    expect(none.test('plain')).toBe(true);
    expect(none.test('{n}')).toBe(false);
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

describe('notes', () => {
  it('fewMksNote chooses the note of a list with status warning by its number of former MKs: 1, 2, 3 or more', () => {
    expect(fewMksNote(1)).toEqual({ key: 'oneMk' });
    expect(fewMksNote(2)).toEqual({ key: 'twoMks' });
    expect(fewMksNote(3)).toEqual({ key: 'fewInTopTen' });
    expect(fewMksNote(7)).toEqual({ key: 'fewInTopTen' });
  });
  it('renderNotePart fills one part from the file (List details: one line each)', () => {
    expect(renderNotePart({ key: 'oneMk' })).toBe(T.notes.oneMk);
    expect(renderNotePart({ key: 'lowCoverage', pct: '40%' })).toBe(fill(T.notes.lowCoverage, { pct: '40%' }));
  });

  it('renderNote fills each part from the file and joins them with notes.join', () => {
    expect(renderNote([])).toBe('');
    expect(renderNote([{ key: 'noRecord' }])).toBe(T.notes.noRecord);
    expect(renderNote([{ key: 'oneMk' }, { key: 'lowCoverage', pct: '40%' }]))
      .toBe(T.notes.oneMk + T.notes.join + fill(T.notes.lowCoverage, { pct: '40%' }));
  });
});
