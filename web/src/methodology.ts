/**
 * The methodology page (export/WEB_CONTRACT.md §7): every text of the page — heading, sections, bullets, the labels of the
 * statements block — comes from export/quiz_methodology.json. Nothing of it is written in the code: the page renders the
 * structure and fills the numbers.
 *
 * Templates: `{name}` is replaced by the value; `{name?one|many}` by `one` when the value is 1, else `many`
 * («{single} {single?list|lists}»). The names a text may use are fixed here (DATA_PLACEHOLDERS for the sections, one set
 * per label of the statements block) and enforced by the schema, so a typo in the file fails the tests and `make check`,
 * never the live page. export/quiz_methodology.schema.json is generated from this schema (src/methodologyJsonSchema.ts,
 * `npm run schema:methodology`). zod/mini: the app bundles only the checks it uses (~3 KB gzip, not the whole of zod).
 */
import * as z from 'zod/mini';
import type { QuizData } from './engine/types';

/** Numbers of the data the sections may name, all read from quiz_data. */
export const DATA_PLACEHOLDERS = [
  'lists', 'evaluable', 'single', 'no_record', 'close', 'statements', 'core', 'clarify', 'vote_ratio',
  'min_lists', 'min_mks', 'min_spread', 'min_names',
] as const;

/** Placeholders of each label of the statements block (filled by the screen per statement or bill). */
export const STATEMENT_PLACEHOLDERS = {
  heading: ['statements'],
  topic: ['name'],
  up: ['text'],
  down: ['text'],
  agreeCountsUp: [],
  agreeCountsDown: [],
  billsCount: ['n'],
  billMeta: ['side', 'knesset', 'role'],
  sideUp: [],
  sideDown: [],
  roleMain: [],
  roleSecondary: [],
  sponsors: ['names'],
  noSponsors: [],
  showMore: ['n'],
  billLink: [],
  dataVersion: ['generated', 'commit'],
} as const;

/** A text that uses only the given placeholders: `{name}` or `{name?one|many}`, no stray braces. */
export function templatePattern(names: readonly string[]): string {
  const name = names.length ? `(?:${names.join('|')})` : '(?!)';
  return `^(?:[^{}]|\\{${name}(?:\\?[^{}|]*\\|[^{}|]*)?\\})*$`;
}

const template = (names: readonly string[]) =>
  z.string().check(z.minLength(1), z.regex(new RegExp(templatePattern(names)), { error: `only {${names.join('|')}} may be used` }));

const sectionText = template(DATA_PLACEHOLDERS);

const nonEmpty = z.string().check(z.minLength(1));

export const BulletSchema = z.strictObject({
  /** Shown in italics, as the run-in start of the bullet. */
  lead: sectionText,
  text: sectionText,
});

export const SectionSchema = z.strictObject({
  /** Shown in bold as the run-in start of the paragraph, with its own punctuation. */
  title: nonEmpty,
  text: z.optional(sectionText),
  bullets: z.optional(z.array(BulletSchema).check(z.minLength(1))),
  /** A paragraph after the bullets. */
  after: z.optional(sectionText),
});

const labels = Object.fromEntries(
  Object.entries(STATEMENT_PLACEHOLDERS).map(([k, names]) => [k, template(names)]),
) as { [K in keyof typeof STATEMENT_PLACEHOLDERS]: ReturnType<typeof template> };

export const MethodologySchema = z.strictObject({
  /** Date of the last change of the texts (ISO). */
  updated: z.string().check(z.regex(/^\d{4}-\d{2}-\d{2}$/)),
  heading: nonEmpty,
  back: nonEmpty,
  sections: z.array(SectionSchema).check(z.minLength(1)),
  /** Labels of the block «All N statements, their topics and the bills behind them». */
  statements: z.strictObject(labels),
});

export type Methodology = z.infer<typeof MethodologySchema>;
export type Section = z.infer<typeof SectionSchema>;

export const parseMethodology = (raw: unknown): Methodology => z.parse(MethodologySchema, raw);

export type Values = Record<string, string | number>;

/** Fills `{name}` and `{name?one|many}`; an unknown name throws (the schema makes it unreachable for the files in git). */
export function fill(text: string, values: Values): string {
  return text.replace(/\{([a-z_]+)(?:\?([^{}|]*)\|([^{}|]*))?\}/g, (_, name: string, one?: string, many?: string) => {
    if (!(name in values)) throw new Error(`unknown placeholder {${name}}`);
    const v = values[name]!;
    return one === undefined ? String(v) : v === 1 ? one : many!;
  });
}

/** The numbers of DATA_PLACEHOLDERS, from quiz_data. */
export function dataValues(data: QuizData): Record<(typeof DATA_PLACEHOLDERS)[number], number> {
  const p = data.params;
  const evaluated = data.lists.filter((l) => l.status !== 'not_evaluated');
  const evaluable = evaluated.filter((l) => l.ex_mks >= p.MIN_EX_MKS).length;
  return {
    lists: data.lists.length,
    evaluable,
    single: evaluated.length - evaluable,
    no_record: data.lists.length - evaluated.length,
    close: p.CLOSE,
    statements: data.statements.length,
    core: data.flow.core,
    clarify: data.flow.clarify,
    vote_ratio: Math.round(1 / p.VOTE_WEIGHT),
    min_lists: p.SELECT_MIN_LISTS,
    min_mks: p.SELECT_MIN_MKS,
    min_spread: p.SELECT_MIN_SPREAD,
    min_names: p.SELECT_MIN_NAMES,
  };
}
