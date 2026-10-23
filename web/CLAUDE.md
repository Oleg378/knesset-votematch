# web/ — rules for the front-end agent

React + Vite + TypeScript, static SPA (no server, no Next.js). Talk to the customer in Russian; the product is English.

## Read first
1. `../CLAUDE.md` — project, principles P0/P1, data contract.
2. `SPEC.md` — screens and behaviour.
3. `DECISIONS.md` — what is approved [У], proposed [А], open [О]. Do not redo an [О] item on your own.
4. Figma: https://www.figma.com/design/TTgHWki3flpBiQ6U9XQF7I/CSS (connector available).

## Your area
- **Edit only `web/` and `.github/`.** `pipeline/`, `export/`, `jef/`, `docs/`, `manual/`, `research/` belong to the data
  session: do not edit, do not commit their changes (they are often uncommitted in the working tree — leave them).
- Missing or wrong data → write it in `DATA_REQUESTS.md` and tell the customer. Never patch `../export/*` by hand.
- Data: `../export/` only; the contract and loading order — `../export/WEB_CONTRACT.md`, page texts — `../export/METHODOLOGY_PAGE.md`. The web
  reads the three current files (`quiz_core` bundled, `quiz_data` and `quiz_bills` fetched — `src/data.ts`).

## Design: Figma first
- **A screen that has a Figma mockup is built exactly as the mockup**: texts, number of answers, buttons, progress,
  menu. Open the frame (`get_design_context` / `get_screenshot`) before writing code; do not invent wording.
- If the mockup conflicts with SPEC or the data (e.g. «60 statements» vs 65 in the data): follow the mockup where it is
  only presentation, and **ask the customer right away** about the rest. Do not silently keep the old behaviour.
- After a screen: screenshot at 402 px wide and compare with the frame.
- Screens without a mockup (Results, List details, Bills, Methodology): Figma tokens and components; layout is the agent's
  proposal, recorded in `DECISIONS.md`.
- `src/styles/tokens.css` is the only place for colors, type, spacing, radii. Mobile first, 360–430 px, column ≤ 480 px.

## Customer decisions (do not change)
- Answers are stored nowhere: no localStorage/sessionStorage/cookies/IndexedDB. Reload = start over.
- The result never goes into the URL. No third-party trackers, fonts or requests (CSP in `public/_headers`).
- Bill titles: Hebrew only, `dir="auto" lang="he"`, plus the direction line. Never show `summary_en`.
- Never show: coalition/opposition, attitude to the government, number of MKs, list logos.
- Exactly two notes (few former MKs: N; position known for only N% of your answers). No votes of lists on Methodology.
  No topic selection.
- Every UI string in `src/strings.ts`. Metrics: only `started` / `finished` via the no-op `track()`.

## Code
- `src/engine/` — pure TypeScript port of `pipeline/quiz_match.py` + `pipeline/quiz_report.py`. No React, no DOM.
- **Python is the reference**: the golden cases of the files the engine reads must pass (1e-9). If a golden case fails because Python looks
  wrong — stop and describe it to the customer; do not «fix» the TS to differ.
- Explanation strings that appear in golden must reproduce it exactly.
- `src/state/` — `useReducer` state machine, pure and tested. No router.
- Screens are tested through `<App/>` in jsdom (`src/screens/screens.test.tsx`), including the privacy rules.

## Before a commit
`npm run typecheck && npm test && npm run build && npm run check:dist` — all green (CI runs the same).

## How to work
- Small steps: one screen or one component plus its test; commit when the step is done and checks pass; one topic per commit.
- Product decisions (wording, what to show, behaviour) — list options and ask (P1). Engineering choices with an obvious
  default — take it and note it in `DECISIONS.md`.
- Budget: $20 subscription — almost no sub-agents.
- Push only when the customer asks.

Commands: `npm run dev`, `npm test`, `npm run build`, `npm run typecheck`, `npm run check:dist`.
