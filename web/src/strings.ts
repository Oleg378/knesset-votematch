/**
 * Every UI string (English). The explanation templates reproduce pipeline/quiz_report.py exactly (golden `lines`);
 * the notes reproduce pipeline/quiz_match.py. Do not reword those without regenerating the golden file.
 */
import type { AnswerValue } from './engine/types';

// ---- Engine texts (must match the Python reference byte for byte) ----

/** quiz_report.ANS — the same words as the answer buttons [У 2026-10-18] */
export const ANS: Record<AnswerValue, string> = {
  2: 'strongly agree',
  1: 'agree',
  0: 'neutral',
  [-1]: 'disagree',
  [-2]: 'strongly disagree',
} as Record<AnswerValue, string>;

export const noteNoRecord = 'no record in the Knesset';
export const noteFewMks = (n: number) => `few former MKs: ${n}`;
export const noteLowCoverage = (pct: string) => `position known for only ${pct} of your answers`;
export const NOTE_JOIN = '; ';

/** quiz_report.plural */
export const plural = (n: number, word: string) => `${n} ${word}${n === 1 ? '' : 's'}`;

export const explainText = {
  quote: (s: string) => `“${s}”`,
  sideFor: 'points toward this statement',
  sideAgainst: 'points against this statement',
  sideNoClear: 'shows no clear position on this statement',
  answer: (ans: string, side: string) => `Your answer: ${ans}. The record of the list's former MKs ${side}.`,
  // quiz_report.explain: the government's own bills are named only when the list has votes on them [У 2026-10-22]
  votes: (nVotes: number, nOther: number, nGov: number) =>
    `${plural(nVotes, 'vote')} on private bills, ${plural(nOther, 'vote')} on the other camp's bills` +
    (nGov ? ` and ${plural(nGov, 'vote')} on the government's own bills` : '') + ' on this topic',
  basis: (nBills: number, nSame: number, nOpp: number, votes: string) =>
    `Basis: ${plural(nBills, 'bill')} sponsored by the list's former MKs — ${nSame} your way, ${nOpp} the other way; ` +
    `${votes}.`,
  basisVotesOnly: (votes: string) => `Basis: no bills of their own on this topic, only ${votes}.`,
  weight: 'Weight ×2: you chose this topic in a trade-off question.',
  caveatByVotes: "The list's side comes from how its former MKs voted, not from the bills they sponsored.",
  caveatPrice:
    'This shows what their bills and votes pushed for, not whether they accept the price named in the statement.',
};

// ---- UI ----

export const S = {
  a11y: {
    newTab: '(opens in a new tab)',
  },
  // Texts of the Figma mockups (Home, Menu, Questions, Clarifying question), verbatim except the real statement count.
  eyebrow: 'Knesset election 2026', // shown upper-case by CSS
  loading: 'Loading…',
  loadError: 'Could not load the quiz data.',
  reload: 'Reload the page',
  start: {
    title: 'Find your vote match',
    tagline: 'Parties judged by votes, not promises',
    chipStatements: (n: number) => `${n} statements`,
    chipTime: '3–5 min',
    chipAnonymous: 'Anonymous',
    steps: (n: number) => [`Rate ${n} statements`, 'We check their Knesset votes', 'Get your 3 closest parties'],
    button: 'Start the quiz',
    howItWorks: 'Behind the results',
  },
  menu: {
    open: 'Menu',
    close: 'Close menu',
    title: 'Vote Match',
    startOver: 'Start over',
    results: 'My results',
    methodology: 'Methodology',
  },
  nav: {
    back: 'Back',
    next: 'Next',
  },
  question: {
    progress: (n: number, total: number) => `${n}/${total}`,
    progressLabel: 'Progress',
    or: 'or',
    skip: 'Not sure — skip this question',
    noAnswers: 'No answers — nothing to compute.',
    answersLabel: 'Your answer',
  },
  answers: {
    2: 'Strongly agree',
    1: 'Agree',
    0: 'Neutral', // not offered (Figma); kept for completeness of the type
    [-1]: 'Disagree',
    [-2]: 'Strongly disagree',
    dk: "Don't know", // not offered (Figma)
  } as Record<AnswerValue | 'dk', string>,
  answerOrder: [2, 1, -1, -2] as AnswerValue[],
  trade: {
    counter: (n: number, max: number) => `${n}/${max}`,
    lead: 'Thanks! Just a few clarifying questions',
    title: 'Which matters more to you?',
    explain: 'Party A agrees with you on the first statement, Party B on the second. Tap the one that matters more.',
    yourAnswer: (ans: string) => `Your answer: ${ans}`,
    labelA: 'A',
    labelB: 'B',
    equalTitle: 'Both matter equally',
    equalSub: 'No preference between A and B',
  },
  results: {
    heading: 'Your result',
    scaleFar: 'far from you',
    scaleClose: 'close to you',
    closest: (n: number) => (n === 1 ? 'Your closest list' : `Your ${n} closest lists`),
    basedOn: (n: number, total: number, withTrade: boolean) =>
      `Based on ${n} of ${total} answers${withTrade ? ', including trade-offs' : ''}`,
    /** Under «Based on…», the row's arrow button between the words: «Tap › for details». No periods (customer 2026-10-23). */
    hint: ['Tap', 'for details'],
    seeAll: 'See all',
    seeLess: 'Show less',
    notRanked: 'Not ranked: not enough data',
    notComputable: '—',
    noMore: 'No more questions.',
    changeAnswers: 'Change answers',
    rank: (n: number) => `${n}`,
    closenessLabel: 'Closeness',
  },
  details: {
    back: 'Back to results',
    closeness: (c: string) => `closeness ${c}`,
    fits: (n: number) => `Why it fits — ${n} ${n === 1 ? 'match' : 'matches'}`,
    misfits: (n: number) => `Why it doesn't fit — ${n} ${n === 1 ? 'mismatch' : 'mismatches'}`,
    showAll: (n: number) => `Show all (${n} more)`,
    showLess: 'Show fewer',
    none: 'None.',
    openBills: 'See the bills',
  },
  bills: {
    back: 'Back to the list',
    yourWay: (n: number) => `Your way (${n})`,
    otherWay: (n: number) => `The other way (${n})`,
    none: 'None.',
    meta: (knesset: number, role: string, raises: boolean, direction: string) =>
      `Knesset ${knesset} · ${role === 'main' ? 'main' : 'secondary'} topic · ${raises ? 'raises' : 'lowers'} “${direction}”`,
    sponsoredBy: (names: string) => `Sponsored by: ${names}`,
    sponsor: (name: string, pos: number) => `${name} (#${pos} on the list)`,
    link: 'Open on the Knesset website',
    yourWayMark: 'Your way',
    otherWayMark: 'The other way',
    showMore: (n: number) => `Show more (${n} left)`,
  },
};
