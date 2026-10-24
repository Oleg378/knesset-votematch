/**
 * Every text the user reads on the site (export/WEB_CONTRACT.md §7) comes from export/quiz_texts.json, edited by hand:
 * the app name and title, the answers, the notes, the explanation lines, every screen's labels and the methodology page.
 * Nothing of it is written in the code: src/strings.ts builds the UI strings from `T`, the screens render the structure and
 * fill the numbers.
 *
 * The file is bundled into the JS (imported, parsed once at module load), not fetched: it is small (~5 KB gzip) and the
 * start page needs it before any data file. A file that breaks the schema fails the tests and the build, never the live
 * page.
 *
 * Templates: `{name}` is replaced by the value; `{name?one|many}` by `one` when the value is 1, else `many`
 * («{single} {single?list|lists}»). The names each text may use are listed here, per key (PLACEHOLDERS, STEP_PLACEHOLDERS,
 * DATA_PLACEHOLDERS for the methodology sections, STATEMENT_PLACEHOLDERS for its statements block) — never derived from the
 * file, so a typo in the file fails the schema. A key with no names takes no placeholder and no brace at all.
 * export/quiz_texts.schema.json is generated from this schema (src/textsJsonSchema.ts, `npm run schema:texts`).
 * zod/mini: the app bundles only the checks it uses (~3 KB gzip, not the whole of zod).
 *
 * The import uses a relative path with the JSON import attribute (not the '@export' alias): the same module is loaded by
 * Vite, by vite.config.ts (bootLoader: the page title and the loading text) and by plain Node (scripts/texts-schema.ts),
 * and only a relative path resolves in all three.
 */
import * as z from 'zod/mini';
import raw from '../../export/quiz_texts.json' with { type: 'json' };
import type { QuizData } from './engine/types';

/** Numbers of the data the methodology sections may name, all read from quiz_data. */
export const DATA_PLACEHOLDERS = [
  'lists', 'evaluable', 'single', 'no_record', 'close', 'statements', 'core', 'clarify', 'vote_ratio',
  'min_lists', 'min_mks', 'min_spread', 'min_names', 'min_ex_mks',
] as const;

/** Placeholders of each label of the methodology statements block (filled by the screen per statement or bill). */
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

/** Placeholders of the title of a section's list of lists (`lists.title`: n = how many lists it names). */
export const SECTION_LISTS_PLACEHOLDERS = ['n'] as const;

/** Placeholders of each item of `start.steps` (n = planned statements, top = lists highlighted on Results). */
export const STEP_PLACEHOLDERS = ['n', 'top'] as const;

/** The plain sections of the file: each key → the placeholders its text may use. */
export const PLACEHOLDERS = {
  app: {
    /** The page title (<title>, set by vite.config.ts). */
    title: [],
    /** The app name (the menu title). */
    name: [],
    eyebrow: [],
    loading: [],
    loadError: [],
    reload: [],
    newTab: [],
  },
  /** The notes of a list on Results (must match pipeline/quiz_match.py, golden). */
  notes: {
    noRecord: [],
    fewMks: ['n'],
    lowCoverage: ['pct'],
    join: [],
  },
  /** The explanation lines of List details (must match pipeline/quiz_report.py, golden `lines`). */
  explain: {
    quote: ['text'],
    sideFor: [],
    sideAgainst: [],
    sideNoClear: [],
    answer: ['answer', 'side'],
    votes: ['votes', 'other', 'gov'],
    votesGov: ['gov'],
    basis: ['bills', 'same', 'opp', 'votes'],
    basisVotesOnly: ['votes'],
    weight: [],
    caveatByVotes: [],
    caveatPrice: [],
  },
  start: {
    title: [],
    tagline: [],
    chipStatements: ['n'],
    chipTime: [],
    chipAnonymous: [],
    button: [],
    howItWorks: [],
  },
  menu: {
    open: [],
    close: [],
    startOver: [],
    results: [],
    methodology: [],
  },
  nav: {
    back: [],
    next: [],
  },
  question: {
    progress: ['n', 'total'],
    progressLabel: [],
    or: [],
    skip: [],
    noAnswers: [],
    answersLabel: [],
  },
  trade: {
    counter: ['n', 'max'],
    lead: [],
    title: [],
    explain: [],
    yourAnswer: ['answer'],
    labelA: [],
    labelB: [],
    equalTitle: [],
    equalSub: [],
  },
  results: {
    heading: [],
    scaleFar: [],
    scaleClose: [],
    closestOne: [],
    closestMany: ['n'],
    basedOn: ['n', 'total', 'trade'],
    basedOnTrade: [],
    hintBefore: [],
    hintAfter: [],
    seeAll: [],
    seeLess: [],
    notRanked: [],
    notComputable: [],
    noMore: [],
    changeAnswers: [],
    rank: ['n'],
    closenessLabel: [],
  },
  details: {
    back: [],
    closeness: ['c'],
    fits: ['n'],
    misfits: ['n'],
    showAll: ['n'],
    showLess: [],
    none: [],
    openBills: [],
  },
  bills: {
    back: [],
    yourWay: ['n'],
    otherWay: ['n'],
    none: [],
    meta: ['knesset', 'role', 'verb', 'direction'],
    roleMain: [],
    roleSecondary: [],
    raises: [],
    lowers: [],
    sponsoredBy: ['names'],
    sponsor: ['name', 'pos'],
    link: [],
    yourWayMark: [],
    otherWayMark: [],
    showMore: ['n'],
  },
} as const;

/** A text that uses only the given placeholders: `{name}` or `{name?one|many}`, no stray braces. */
export function templatePattern(names: readonly string[]): string {
  const name = names.length ? `(?:${names.join('|')})` : '(?!)';
  return `^(?:[^{}]|\\{${name}(?:\\?[^{}|]*\\|[^{}|]*)?\\})*$`;
}

const template = (names: readonly string[]) =>
  z.string().check(z.minLength(1), z.regex(new RegExp(templatePattern(names)), { error: `only {${names.join('|')}} may be used` }));

type Template = ReturnType<typeof template>;

/** One template per key of the map, each with its own placeholders. */
const templateShape = <M extends Record<string, readonly string[]>>(map: M) =>
  Object.fromEntries(Object.entries(map).map(([k, names]) => [k, template(names)])) as { [K in keyof M]: Template };

/** A strict object of templates (no key missing, no key added). */
const templates = <M extends Record<string, readonly string[]>>(map: M) => z.strictObject(templateShape(map));

const plain = template([]);
const sectionText = template(DATA_PLACEHOLDERS);

export const BulletSchema = z.strictObject({
  /** Shown in italics, as the run-in start of the bullet. */
  lead: sectionText,
  text: sectionText,
});

export const SectionSchema = z.strictObject({
  /** Shown in bold as the run-in start of the paragraph, with its own punctuation. */
  title: plain,
  text: z.optional(sectionText),
  bullets: z.optional(z.array(BulletSchema).check(z.minLength(1))),
  /** A paragraph after the bullets. */
  after: z.optional(sectionText),
  /**
   * The names of some lists, after the bullets and before `after`, each name an item of the card: `title` ({n} = how
   * many), if given, is drawn as the last bullet; without it the names follow the text directly. `no_record` — the
   * lists with no former member of the Knesset (not evaluated); `single` — evaluated with fewer than `MIN_EX_MKS`
   * former members (shown, not ranked). In the order of quiz_data.
   */
  lists: z.optional(z.strictObject({
    of: z.enum(['no_record', 'single']),
    title: z.optional(template(SECTION_LISTS_PLACEHOLDERS)),
  })),
});

const answerKeys = { '2': plain, '1': plain, '0': plain, '-1': plain, '-2': plain };

export const TextsSchema = z.strictObject({
  /** Date of the last change of the texts (ISO). */
  updated: z.string().check(z.regex(/^\d{4}-\d{2}-\d{2}$/)),
  app: templates(PLACEHOLDERS.app),
  /** Answers inside sentences («Your answer: agree»), by answer value (must match pipeline/quiz_report.py ANS). */
  answers: z.strictObject(answerKeys),
  /** The answer buttons, by answer value, and «don't know». */
  answerButtons: z.strictObject({ ...answerKeys, dk: plain }),
  notes: templates(PLACEHOLDERS.notes),
  explain: templates(PLACEHOLDERS.explain),
  start: z.strictObject({
    ...templateShape(PLACEHOLDERS.start),
    /** The three numbered steps of the start page. */
    steps: z.tuple([template(STEP_PLACEHOLDERS), template(STEP_PLACEHOLDERS), template(STEP_PLACEHOLDERS)]),
  }),
  menu: templates(PLACEHOLDERS.menu),
  nav: templates(PLACEHOLDERS.nav),
  question: templates(PLACEHOLDERS.question),
  trade: templates(PLACEHOLDERS.trade),
  results: templates(PLACEHOLDERS.results),
  details: templates(PLACEHOLDERS.details),
  bills: templates(PLACEHOLDERS.bills),
  methodology: z.strictObject({
    heading: plain,
    back: plain,
    sections: z.array(SectionSchema).check(z.minLength(1)),
    /** Labels of the block «All N statements and their bills». */
    statements: templates(STATEMENT_PLACEHOLDERS),
  }),
});

export type Texts = z.infer<typeof TextsSchema>;
export type Section = z.infer<typeof SectionSchema>;
export type SectionLists = NonNullable<Section['lists']>;

export const parseTexts = (value: unknown): Texts => z.parse(TextsSchema, value);

/** The texts of the site, checked against the schema once, when the app loads. */
export const T: Texts = parseTexts(raw);

export type Values = Record<string, string | number>;

/** Fills `{name}` and `{name?one|many}`; an unknown name throws (the schema makes it unreachable for the file in git). */
export function fill(text: string, values: Values): string {
  return text.replace(/\{([a-z_]+)(?:\?([^{}|]*)\|([^{}|]*))?\}/g, (_, name: string, one?: string, many?: string) => {
    if (!(name in values)) throw new Error(`unknown placeholder {${name}}`);
    const v = values[name]!;
    return one === undefined ? String(v) : v === 1 ? one : many!;
  });
}

/** The lists a section names (`lists.of`), in the order of quiz_data — the same groups `single` and `no_record` count. */
export function listsOf(data: QuizData, of: SectionLists['of']): QuizData['lists'] {
  return of === 'no_record'
    ? data.lists.filter((l) => l.status === 'not_evaluated')
    : data.lists.filter((l) => l.status !== 'not_evaluated' && l.ex_mks < data.params.MIN_EX_MKS);
}

/** The numbers of DATA_PLACEHOLDERS, from quiz_data. */
export function dataValues(data: QuizData): Record<(typeof DATA_PLACEHOLDERS)[number], number> {
  const p = data.params;
  const single = listsOf(data, 'single').length;
  const noRecord = listsOf(data, 'no_record').length;
  return {
    lists: data.lists.length,
    evaluable: data.lists.length - single - noRecord,
    single,
    no_record: noRecord,
    close: p.CLOSE,
    statements: data.statements.length,
    core: data.flow.core,
    clarify: data.flow.clarify,
    vote_ratio: Math.round(1 / p.VOTE_WEIGHT),
    min_lists: p.SELECT_MIN_LISTS,
    min_mks: p.SELECT_MIN_MKS,
    min_spread: p.SELECT_MIN_SPREAD,
    min_names: p.SELECT_MIN_NAMES,
    min_ex_mks: p.MIN_EX_MKS,
  };
}
