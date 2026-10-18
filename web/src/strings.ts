/**
 * Every UI string (English). The explanation templates reproduce pipeline/quiz_report.py exactly (golden `lines`);
 * the notes reproduce pipeline/quiz_match.py. Do not reword those without regenerating the golden file.
 */
import type { AnswerValue } from './engine/types';

// ---- Engine texts (must match the Python reference byte for byte) ----

/** quiz_report.ANS — the same words as the answer buttons (v2) */
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
  sideFor: 'for this statement',
  sideAgainst: 'against this statement',
  sideNoClear: 'has no clear position on this statement',
  answer: (ans: string, side: string) => `Your answer: ${ans}. The list is ${side}.`,
  basis: (nBills: number, nSame: number, nOpp: number, nVotes: number) =>
    `Basis: ${plural(nBills, 'bill')} sponsored by the list's former MKs — ${nSame} your way, ${nOpp} the other way; ` +
    `${plural(nVotes, 'vote')} on private bills on this topic.`,
  basisVotesOnly: (nVotes: number) =>
    `Basis: no bills of their own on this topic, only ${plural(nVotes, 'vote')} on private bills.`,
  weight: 'Weight ×2: you chose this topic in a trade-off question.',
  caveatByVotes:
    "The list's side comes from how its former MKs voted on private bills, not from the bills they sponsored.",
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
    intro: 'All lists by closeness to your answers (from −1 to +1).',
    basedOn: (n: number, total: number, withTrade: boolean) =>
      `Based on ${n} of ${total} answers${withTrade ? ', including trade-offs' : ''}.`,
    notRanked: 'Not ranked',
    noRecord: (n: number) => `No record in the Knesset (${n})`,
    notComputable: '—',
    answerMore: 'Answer more questions',
    noMore: 'No more questions.',
    changeAnswers: 'Change answers',
    startOver: 'Start over',
    methodology: 'How it works',
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
  methodology: {
    heading: 'How it works',
    back: 'Back',
    paragraphs: [
      "Where positions come from. A list's position on a topic comes only from what its candidates who are former MKs " +
        'did in the 24th and 25th Knesset (2021–2026): the bills they sponsored, and how they voted on private bills. ' +
        'A vote counts a quarter as much as a sponsored bill. New faces on the lists are not visible.',
      'Questions. Everyone starts with the same core statements. Each next one is chosen from your answers so far: ' +
        'the statement on which the lists closest to you disagree most. After the results you can answer more.',
      'No clear position. When a list’s record on a topic points only weakly to one side, the list is shown as having ' +
        'no clear position on the statement.',
      'Closeness. Your answers and each list’s positions are compared statement by statement (only the statements ' +
        'you answered and the list has a position on). The result goes from −1 (completely opposite) to +1 ' +
        '(completely the same). Skipped statements are left out. A trade-off answer doubles the weight of the topic you chose.',
      'Notes. “Few former MKs: N” — the list’s position rests on very few people. “Position known for only N% of your ' +
        'answers” — the list has a position on less than half of what you answered, so it is shown below the others ' +
        'and not ranked. Lists without any former MKs have no record in the Knesset and cannot be compared.',
    ],
    statementsHeading: (n: number) => `All ${n} statements, their topics and the bills behind them`,
    direction: (name: string) => `Topic: ${name}`,
    plus: (s: string) => `Up: ${s}`,
    minus: (s: string) => `Down: ${s}`,
    agreeMeans: (up: boolean) => `Agreeing with the statement counts as ${up ? 'up' : 'down'}.`,
    billsCount: (n: number) => `${plural(n, 'bill')} on this topic`,
    billMeta: (knesset: number, role: string, raises: boolean) =>
      `${raises ? 'Up' : 'Down'} · Knesset ${knesset} · ${role === 'main' ? 'main' : 'secondary'} topic`,
    sponsoringLists: (names: string) => `Sponsors from: ${names}`,
    noSponsors: 'No sponsors among the 2026 candidates.',
    showMore: (n: number) => `Show more (${n} left)`,
    dataVersion: (generated: string, commit: string) => `Data: ${generated} (${commit}).`,
  },
};
