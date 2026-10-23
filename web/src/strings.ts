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

/** Numbers of the methodology texts, from the export (MethodologyScreen). */
export interface MethodNumbers {
  lists: number;
  /** Lists with >= params.MIN_EX_MKS former MKs. */
  evaluable: number;
  /** Evaluated lists below params.MIN_EX_MKS (shown, not ranked). */
  single: number;
  noRecord: number;
  close: number;
}

/** A methodology section: bold title (own punctuation, as in §6), then text and/or bullets [italic lead, rest]. */
export interface MethodSection {
  title: string;
  text?: string;
  bullets?: [lead: string, text: string][];
}

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
  methodology: {
    heading: 'How it works',
    back: 'Back',
    // Texts of export/V2_HANDOFF.md §6 (customer, 2026-10-18), verbatim; list counts and CLOSE come from the export.
    sections: (n: MethodNumbers): MethodSection[] => [
      {
        title: 'How topics are chosen.',
        text: "A topic gets a statement only if the parties' former MKs actually differ on it in the Knesset record: " +
          'at least 8 evaluated lists with 3 or more former MKs on the topic, a spread of their positions of at least ' +
          '0.25, and at least 5 distinct bills (a re-submitted bill counts once) sponsored by them. These thresholds ' +
          'were fixed in advance and are the same for every topic. Topics where all lists did the same, or where too ' +
          'few bills exist, are left out — even when they are important.',
      },
      {
        title: 'Important topics that are not in the quiz, and why.',
        bullets: [
          ["The lists' records hardly differ (nearly everyone pushed the same way):",
            'animal protection; credit and mortgages; state power to ban harmful content; public broadcasting (Kan, ' +
            'Galei Tzahal); tax enforcement; cannabis; state support for long-term savings; support for charities.'],
          ['Too few bills by the candidates to place the lists:',
            'abortion; who is registered as a Jew; rights of the parliamentary opposition; gun licensing; immunity for ' +
            'soldiers; the death penalty for terrorists; immigration rights of grandchildren of Jews (Law of Return); ' +
            'laws tied to a state of emergency; a shorter working week; the Yemenite children affair; adoption rules.'],
          ['Covered by another statement:',
            'immunity of elected officials (in «A prime minister under indictment»); civil marriage and divorce (in ' +
            '«Civil marriage» and «Divorce»); conditions on funding religious schools (in «Funding schools without the ' +
            'core curriculum»); alternatives to military service (in «Drafting yeshiva students»); international law ' +
            'and UNRWA (in «Foreign states and international organizations in Israel»).'],
        ],
      },
      {
        title: "Where a list's position comes from.",
        text: 'Only from what its candidates who were MKs in the 24th–25th Knesset did: the bills they sponsored, their ' +
          "votes on private bills, and their votes on the other camp's bills. Promises and speeches are not used. " +
          "Positions that coincide with the coalition line are read mostly from the votes on the other camp's bills.",
      },
      {
        title: 'Questions.',
        text: 'Everyone starts with the same core statements. Each next one is chosen from your answers so far: ' +
          'the statement on which the lists closest to you disagree most. After the results you can answer more.',
      },
      {
        title: 'Closeness.',
        text: 'Your answers and each list’s positions are compared statement by statement (only the statements ' +
          'you answered and the list has a position on). The result goes from −1 (completely opposite) to +1 ' +
          '(completely the same). Skipped statements are left out. A trade-off answer doubles the weight of the topic you chose.',
      },
      {
        title: 'The answer scale.',
        text: 'Closeness compares directions, not intensity: if you answer «strongly agree» to everything, the result ' +
          'is the same as «agree» to everything; the strength of an answer matters when your answers are mixed.',
      },
      {
        title: '«No clear position».',
        text: `A list is marked so when its position is weaker than ${n.close} — below that, the side of the same list ` +
          'did not hold between the two Knessets in most cases — or when it rests on a single former MK or a single bill.',
      },
      {
        title: 'Leaders with few bills of their own.',
        text: "Ministers and prime ministers rarely sponsor bills, so a list's position rests mostly on its other former " +
          'MKs and on votes.',
      },
      {
        title: 'Candidates who moved to another list.',
        text: "A former MK's record counts for the list they run with in 2026: it is the same person and their own votes.",
      },
      {
        title: 'Lists with one former MK',
        text: "are shown but not ranked: one person's record is too thin to call a list the closest.",
      },
      {
        title: 'Notes.',
        text: '“Few former MKs: N” — the list’s position rests on very few people. “Position known for only N% of your ' +
          'answers” — the list has a position on less than half of what you answered, so it is shown below the others ' +
          'and not ranked. Lists without any former MKs have no record in the Knesset and cannot be compared.',
      },
      {
        title: 'Limitations — what this quiz can and cannot tell you.',
        text: 'The quiz is an orientation, not a precise measurement. We state openly where the data and the analysis ' +
          'are noisy:',
        bullets: [
          ['Only the Knesset record of former MKs',
            `(24th–25th Knesset) is used. New candidates, platforms and statements are not seen. ${n.evaluable} of ` +
            `${n.lists} lists can be evaluated; ${n.single} ${n.single === 1 ? 'list' : 'lists'} with a single former ` +
            `MK ${n.single === 1 ? 'is' : 'are'} shown but not ranked; ${n.noRecord} ${n.noRecord === 1 ? 'list has' : 'lists have'} no record.`],
          ['Bloc discipline.',
            "About 98 % of votes follow the voter's bloc. A party's opposition to the other camp's laws is read from " +
            'its votes against them — partly party discipline, not only conviction.'],
          ['Leaders and ministers sponsor few bills,',
            "so a list's position rests mostly on its other former MKs and on votes."],
          ['Topic labels were made by a language model.',
            'Independent model checks found main topics right in about 93 % and secondary topics in about 80 % of ' +
            'cases; individual mistakes remain. Labels were corrected only where two independent checks agreed.'],
          ['Checks so far were done by models, not by people.',
            'Agreement figures measure consistency, not accuracy for real voters. A human check is planned.'],
          ['Closeness is approximate.',
            'Lists with close values cannot be told apart reliably, so values are shown rounded and should be read as ' +
            '«about as close». «No clear position» means the record is weak or rests on a single former MK or a single bill.'],
          ['The price in a statement',
            "(«even if …») is not measured: the record shows what a list's bills and votes pushed for, not whether it " +
            'accepts that price.'],
        ],
      },
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
