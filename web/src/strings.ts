/**
 * The UI strings, built from export/quiz_texts.json (`T`, src/texts.ts) — no text is written here, only how each one is
 * filled. The explanation templates must reproduce pipeline/quiz_report.py exactly (golden `lines`), the notes
 * pipeline/quiz_match.py: reword those in the file only together with the Python side and the golden file.
 */
import type { AnswerValue } from './engine/types';
import { fill, T } from './texts';
import { HIGHLIGHT } from './uiConstants';

const byAnswer = (m: Record<'2' | '1' | '0' | '-1' | '-2', string>) =>
  ({ 2: m['2'], 1: m['1'], 0: m['0'], [-1]: m['-1'], [-2]: m['-2'] }) as Record<AnswerValue, string>;

// ---- Engine texts (must match the Python reference byte for byte) ----

/** quiz_report.ANS — answers inside sentences */
export const ANS: Record<AnswerValue, string> = byAnswer(T.answers);

export const noteNoRecord = T.notes.noRecord;
/** quiz_match.few_mks_note — the note of a list with status `warning`, by its number of former MKs */
export const noteFewMks = (n: number) => (n === 1 ? T.notes.oneMk : n === 2 ? T.notes.twoMks : T.notes.fewInTopTen);
export const noteLowCoverage = (pct: string) => fill(T.notes.lowCoverage, { pct });
export const NOTE_JOIN = T.notes.join;

/** quiz_report.plural */
export const plural = (n: number, word: string) => `${n} ${word}${n === 1 ? '' : 's'}`;

const E = T.explain;
export const explainText = {
  quote: (s: string) => fill(E.quote, { text: s }),
  sideFor: E.sideFor,
  sideAgainst: E.sideAgainst,
  sideNoClear: E.sideNoClear,
  answer: (ans: string, side: string) => fill(E.answer, { answer: ans, side }),
  // quiz_report.explain: the government's own bills are named only when the list has votes on them [У 2026-10-22]
  votes: (nVotes: number, nOther: number, nGov: number) =>
    fill(E.votes, { votes: nVotes, other: nOther, gov: nGov ? fill(E.votesGov, { gov: nGov }) : '' }),
  basis: (nBills: number, nSame: number, nOpp: number, votes: string) =>
    fill(E.basis, { bills: nBills, same: nSame, opp: nOpp, votes }),
  basisVotesOnly: (votes: string) => fill(E.basisVotesOnly, { votes }),
  weight: E.weight,
  caveatByVotes: E.caveatByVotes,
  caveatPrice: E.caveatPrice,
};

// ---- UI ----

export const S = {
  a11y: {
    newTab: T.app.newTab,
  },
  eyebrow: T.app.eyebrow, // shown upper-case by CSS
  loading: T.app.loading,
  loadError: T.app.loadError,
  reload: T.app.reload,
  start: {
    title: T.start.title,
    tagline: T.start.tagline,
    chipStatements: (n: number) => fill(T.start.chipStatements, { n }),
    chipTime: T.start.chipTime,
    chipAnonymous: T.start.chipAnonymous,
    /** n = planned statements; the last step names the lists highlighted on Results. */
    steps: (n: number) => T.start.steps.map((s) => fill(s, { n, top: HIGHLIGHT })),
    button: T.start.button,
    howItWorks: T.start.howItWorks,
  },
  menu: {
    open: T.menu.open,
    close: T.menu.close,
    title: T.app.name,
    startOver: T.menu.startOver,
    results: T.menu.results,
    methodology: T.menu.methodology,
  },
  nav: {
    back: T.nav.back,
    next: T.nav.next,
  },
  question: {
    progress: (n: number, total: number) => fill(T.question.progress, { n, total }),
    progressLabel: T.question.progressLabel,
    or: T.question.or,
    skip: T.question.skip,
    noAnswers: T.question.noAnswers,
    answersLabel: T.question.answersLabel,
  },
  /** The answer buttons (Neutral and «don't know» are not offered — Figma; kept for completeness of the type). */
  answers: { ...byAnswer(T.answerButtons), dk: T.answerButtons.dk } as Record<AnswerValue | 'dk', string>,
  answerOrder: [2, 1, -1, -2] as AnswerValue[],
  trade: {
    counter: (n: number, max: number) => fill(T.trade.counter, { n, max }),
    lead: T.trade.lead,
    title: T.trade.title,
    explain: T.trade.explain,
    yourAnswer: (ans: string) => fill(T.trade.yourAnswer, { answer: ans }),
    labelA: T.trade.labelA,
    labelB: T.trade.labelB,
    equalTitle: T.trade.equalTitle,
    equalSub: T.trade.equalSub,
  },
  results: {
    heading: T.results.heading,
    scaleFar: T.results.scaleFar,
    scaleClose: T.results.scaleClose,
    closest: (n: number) => (n === 1 ? T.results.closestOne : fill(T.results.closestMany, { n })),
    basedOn: (n: number, total: number, withTrade: boolean) =>
      fill(T.results.basedOn, { n, total, trade: withTrade ? T.results.basedOnTrade : '' }),
    /** Under «Based on…», the row's arrow button between the words: «Tap › for details». */
    hint: [T.results.hintBefore, T.results.hintAfter],
    seeAll: T.results.seeAll,
    seeLess: T.results.seeLess,
    notRanked: T.results.notRanked,
    notComputable: T.results.notComputable,
    noMore: T.results.noMore,
    changeAnswers: T.results.changeAnswers,
    rank: (n: number) => fill(T.results.rank, { n }),
    closenessLabel: T.results.closenessLabel,
  },
  share: {
    title: T.share.title,
    text: T.share.text,
    button: T.share.button,
    copied: T.share.copied,
  },
  details: {
    /** The explanation's «price» caveat, said once for the page, without the period (customer 2026-10-23) */
    priceNote: explainText.caveatPrice.replace(/\.$/, ''),
    back: T.details.back,
    // Not in quiz_texts.json yet (DATA_REQUESTS.md 13): the only text written here until the file has it
    closenessTitle: 'Closeness to you',
    fits: (n: number) => fill(T.details.fits, { n }),
    misfits: (n: number) => fill(T.details.misfits, { n }),
    none: T.details.none,
  },
  bills: {
    yourWay: (n: number) => fill(T.bills.yourWay, { n }),
    otherWay: (n: number) => fill(T.bills.otherWay, { n }),
    none: T.bills.none,
    meta: (knesset: number, role: string, raises: boolean, direction: string) =>
      fill(T.bills.meta, {
        knesset,
        role: role === 'main' ? T.bills.roleMain : T.bills.roleSecondary,
        verb: raises ? T.bills.raises : T.bills.lowers,
        direction,
      }),
    sponsoredBy: (names: string) => fill(T.bills.sponsoredBy, { names }),
    sponsor: (name: string, pos: number) => fill(T.bills.sponsor, { name, pos }),
    link: T.bills.link,
    yourWayMark: T.bills.yourWayMark,
    otherWayMark: T.bills.otherWayMark,
    showMore: (n: number) => fill(T.bills.showMore, { n }),
  },
  /** The rest of the methodology page reads `T.methodology` directly (MethodologyScreen). */
  methodology: {
    heading: T.methodology.heading,
  },
};
