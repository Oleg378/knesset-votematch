# web/ — rules for the front-end agent

React + Vite + TypeScript, static SPA (no server, no Next.js). Talk to the customer in Russian; the product is English.

## Read first
1. `../CLAUDE.md` — project, principles P0/P1, data contract.
2. `SPEC.md` — screens and behaviour; `DESIGN_SPEC.md` — the Figma values (colors, type, spacing, browser bars).
3. `DECISIONS.md` — what is approved [У], proposed [А], open [О]. Do not redo an [О] item on your own.
4. Figma: https://www.figma.com/design/TTgHWki3flpBiQ6U9XQF7I/CSS (connector available).

## Your area
- **Edit only `web/` and `.github/`.** `pipeline/`, `export/`, `data/`, `docs/`, `manual/`, `research/` belong to the data
  session: do not edit, do not commit their changes (they are often uncommitted in the working tree — leave them).
- Missing or wrong data → write it in `DATA_REQUESTS.md` and tell the customer. Never patch `../export/*` by hand.
- Data: the contract in `../export/` only — `quiz_core.json`, `quiz_data.json`, `quiz_bills.json`, fetched at run time in
  this order by `src/data.ts` (never bundled; content-hashed, never inlined — CSP `connect-src 'self'`).
  Contract and loading order: `../export/WEB_CONTRACT.md`; overview: `../export/README.md`.
- Texts: every text the user reads is in `../export/quiz_texts.json` (§7, edited by hand), **bundled** into the JS on
  purpose (`src/texts.ts`: zod schema with the allowed `{placeholders}` of every key, `T` parsed at load;
  `npm run schema:texts` after changing the structure). Screens use `S` / `explainText` from `src/strings.ts`, which only
  fills templates from `T` — no text in code. The page `<title>`, description, Open Graph tags, manifest, robots and
  sitemap come from `app.*` through `pageTitle` / `siteHead` (vite.config.ts); absolute addresses only from `SITE_URL`.
- A screen renders only when its file has arrived (App shows a loader for that screen only): Start — nothing; questions —
  quiz_core, clarifying ones and everything after — quiz_data; List details (with the bills inside), Methodology — quiz_bills.
- **The start page loads first** (DECISIONS.md G): `index.html` preloads its fonts, quiz_core and the hero
  (`preloadStartPage` in `vite.config.ts`); quiz_data and quiz_bills start only after it is drawn (`firstScreenShown` in
  `src/data.ts`). A new font or picture on Home → add it to the preload. Measure with a production build (gzip), never
  the dev server: Slow 4G (150 ms, 1.6 Mbit/s), CPU ×4, no cache — Home complete ≈ 1.24 s on 2026-10-18.
- **Two pages, both ready HTML** (DECISIONS.md H5–H6): `/` (`index.html`) and `/how-it-works` (`how-it-works.html`) are
  rendered at build time from the same components (`src/prerender.tsx`, `prerenderPages` in `vite.config.ts`, every build including `--watch`);
  React draws the same markup over it. `src/prerender.test.tsx` fails when the app's shell or the screen drifts from the
  prerendered page — keep them the same. The path opens its screen (`initialStateFor`); the address follows the
  methodology screen only.
- Loading picture = dot rings + a running blue dot (Figma «Frame 9», geometry in `src/components/dotRing.ts`, styles
  `.dot-ring` in `app.css`): `<Loading/>` on a screen waiting for its file. Every ring uniform (no lighter dots around
  the blue one). Nothing waits before the JS: the pages themselves are ready HTML.
- Phone preview over ngrok points at the production build (`vite build --watch` + a static server with gzip and the CSP
  from `public/_headers`), not at `npm run dev` (unminified React, no compression: 5.4 MB).
  Run: `npx vite build --watch`, `node scripts/serve-dist.mjs 4173`, `ngrok http 4173`.

## Design: Figma first
- **A screen that has a Figma mockup is built exactly as the mockup**: texts, number of answers, buttons, progress,
  menu. Open the frame (`get_design_context` / `get_screenshot`) before writing code; do not invent wording.
- If the mockup conflicts with SPEC or the data (e.g. «60 statements» vs 65 in the data): follow the mockup where it is
  only presentation, and **ask the customer right away** about the rest. Do not silently keep the old behaviour.
- After a screen: screenshot at 402 px wide and compare with the frame.
- Screens without a mockup (Results, List details, Methodology): Figma tokens and components; layout is the agent's
  proposal, recorded in `DECISIONS.md`.
- `src/styles/tokens.css` is the only place for colors, type, spacing, radii. Mobile first, 360–430 px, column ≤ 480 px.

## Design spec: Figma
Colors and typography, layout and spacing of Home / Question / Clarifying question / Menu, and the browser-bars rule are in
`DESIGN_SPEC.md` (nodes 20-133, 27-133, 28-260 of the Figma file). Read it before touching `tokens.css` or a screen's layout;
when Figma changes, update `tokens.css` and that file together. Never use the mockup's 62 / 34 as numbers: they are
`env(safe-area-inset-*)` and the viewport units.

## Breakpoints — rules for every web screen («версия Б», customer 2026-10-17)
Applies to **all screens** (Home, Question, Clarifying question, Menu, Results, List details, Methodology) and
to any new one. Based on Material 3 window size classes. Previous layout = «версия А», snapshot in git at the tag `layout-A`
(`git show layout-A:web/design-variants/layout-A/README.md`; roll back on request).

### Principles
1. **The layout type changes only at the points; between them everything changes smoothly** (clamped values, no jumps,
   no ad-hoc media queries per screen).
2. **What shrinks first:** outer margins → the free space above the bottom buttons. Text, buttons, tap targets and the
   card width never shrink. Never scale the card down to fit (defeats browser zoom).
3. **Tall windows never stretch a screen:** extra height goes to the margins, the card stays centred.
4. **When even the minimums do not fit, the screen scrolls,** and a screen's primary bottom buttons stay visible (sticky
   with a fade). The header (burger, progress, counter) is pinned on top on every screen (customer 2026-10-18). In a
   browser the window scrolls (its bars hide); in an app's built-in viewer (Telegram, LinkedIn, …; `src/inApp.ts`) on
   a phone, the frame: the page never scrolls, the header stands outside the scroll and only `.app-scroll` scrolls
   (customer 2026-10-24, DECISIONS.md G28). Card mode always scrolls the window.
6. **The header never moves between screens:** same place on every screen of one window — on phones safe area + 8, in
   card mode the card's top is where a Figma-height card sits centred; a long screen grows downwards.
5. **Browser zoom needs no special handling:** zooming in only makes the CSS viewport smaller, the same rules apply.

### Width / height points (global, in `.app` — every screen gets them automatically)
| Window | Layout |
|---|---|
| width < 600 **or** height < 480 | phone layout: column full width, no backdrop, no card |
| width ≥ 600 and height ≥ 480 | card (480 wide, at least 812 high) on the brand tint, centred; menu inside the card |

| Window height (card mode) | Card margin | Free space above the bottom buttons | Scroll |
|---|---|---|---|
| ≥ 876 | ≥ 32, card centred | maximum (as in Figma) | no |
| 844–876 | 32 → 16 | maximum | no |
| below 844 | 16 | shrinks to the screen's minimum | no, until the minimum is reached |
| content + minimum + 2 × 16 does not fit | 16 | minimum | yes; primary bottom buttons stick |

Phone layout follows the same order without the card margins. For Home: maximum 158 (Figma), minimum 64, scrolling
starts below ~750 px.

### Bottom buttons — two kinds
- **Primary bottom group** (the screen's main action, the screen is built around it): `position: sticky; bottom: 0`,
  white background, 32 px white fade above (`::before`, `--cta-fade`), padding `12` on top and `16 + safe area` below,
  negative bottom margin of the safe area. It only visibly sticks when the content does not fit. The fade shows only
  while some of the page is under the buttons — it does not fit and is not scrolled to its end (`data-below` on
  `<html>`, set by `src/bottomFade.ts` in every browser; customer 2026-10-19, 2026-10-22: a card that fits stays crisp
  even right above the buttons). Use `BottomBar` or `.sticky-actions` with these rules.
- **Actions at the end of a long scrolling list** (read first, act after): not sticky — they would permanently cover
  part of the list. They sit after the content with the normal screen gap (customer 2026-10-17).

### Every screen
| Screen | Bottom buttons | Kind | Minimum space above them |
|---|---|---|---|
| Home | Start the quiz · Behind the results | primary, sticky | 64 (`--cta-min-gap`, margin under `.steps`) |
| Question | Back · Next | primary, sticky | 28 (screen gap 16 + bar padding 12) |
| Clarifying question | Back · Next | primary, sticky | 28 |
| Menu | (GitHub / Behance, hidden for now) | drawer — fills its own height, no scroll of the page | — |
| Results | Change answers · Start over · Methodology | end of a long list, not sticky (customer 2026-10-17) | screen gap 16 |
| List details | none (Back in the header, in the menu's place; topics open in place) | — | — |
| Methodology | none (no Back: the system Back or the menu; «See all» inside the cards) | — | — |

### Implementation
- Tokens: `--desktop-gap: clamp(16px, (100dvh − 812px) / 2, 32px)`, `--desktop-card-height`, `--cta-min-gap`,
  `--cta-fade`. Card-mode media query: `(min-width: 600px) and (min-height: 480px)` — the only layout media query.
- Check matrix after any layout change (puppeteer, see «How to verify» below): iPhone 402×874 (insets 62/34), 393×660,
  375×560, 844×390, 768×1024, 1920×940, 1440×900, 1440×818, 1440×750, 1366×650, zoom 150 % (960×545 @1.5),
  zoom 200 % (720×409 @2). Primary bottom buttons (Start / Behind the results, Back / Next) must be visible without
  scrolling in all of them; the card mode / phone layout must switch exactly at 600 / 480.
- Known trade-off (accepted by the customer): at window heights ~390–550 (phone in landscape, zoom ≥ 150 %) the stuck
  buttons with the fade take ~170 px of the screen; the pinned header takes another 52 (+ 16 fade).

## Approved implementation (customer, 2026-10-17 — do not change without asking)
Full list with reasons: `DECISIONS.md` section E. Where the code differs from a mockup, it is on purpose.
- **Safe areas.** Mockup 62 on top / 34 at the bottom = `env(safe-area-inset-*)` (`viewport-fit=cover`); never add 34 by
  hand — in a browser the toolbar already covers the home indicator. Top of every screen and of the menu:
  `calc(env(safe-area-inset-top) + 8px)` — on screens it is the pinned `.header`'s padding-top (white), so a stuck
  header clears the status bar; `.app` has no top padding. Bottom: the safe area is `.screen`'s (not the scrolling area's:
  a sticky bar stops at a scroller's padding); the bottom groups add their own 16.
- **Bottom groups.** Both use `padding-bottom: calc(16px + env(safe-area-inset-bottom))` and
  `margin-bottom: calc(-1 * env(safe-area-inset-bottom))` (the screen's safe area moves inside the group), so they sit
  16 above the safe area (Home too — general rule, not the 0 drawn in the Home frame).
  - Both are **sticky with a fade** («версия Б», see «Breakpoints»): on a short screen the content scrolls under them.
    (In «версия А» Home was not sticky — the customer had disliked the hard cut without a fade.)
- **Burger and close:** `margin-inline-start: calc((24px - var(--tap-min)) / 2)` — icon on the 24 px text column, tap area
  hangs left; the menu close button is at exactly the burger's point.
- **Spacing that differs from the frames:** Question top row → card **32** (frame 37); Clarifying top row → «Thanks!»
  **16** (frame 7). Everything else as in «Layout & Spacing» of `DESIGN_SPEC.md`.
- **`.panel` has no gap**: spacing inside the question card comes from its blocks (statement padding 8 8 24, «or»
  padding-top 8, 44 px skip link). In the clarifying card «or» gets `padding-block: 4px` inside the 8 px card stack → 12 / 12.
- **Menu line** under «Vote Match»: Tint 10 % (`--color-accent-soft`), as in the Menu frame.
- **Card mode (see «Breakpoints»):** page background Brand / Tint 10 % as a solid colour (`--color-page-tint`: past the page's ends the browser draws only the background colour), the 480 px column is a white card (radius 32,
  soft shadow, margins 16–32); the menu opens inside the card (see «04 · Menu» in `DESIGN_SPEC.md`). The card's top is
  `max(gap, (100dvh − 812) / 2)` on every screen (not flex-centred: a long screen would start higher and the header jump);
  `overflow: clip` keeps the pinned header's corners inside the radius (never `hidden` — it breaks sticky). No Figma frame — customer chose this variant (C) from
  three rendered options. Never scale the card down to fit (rejected: it defeats browser zoom). Recipes and saved
  alternatives: in git at the tag `desktop-L` (`web/design-variants/` there).
- **Card change** (customer 2026-10-19, DECISIONS.md G11): one quiz card replacing another (question / trade-off; Next,
  Skip, Back, system Back) moves like an iOS navigation push — the new screen slides in from the right edge over the old
  one, which moves a third to the left and fades out (Back: mirrored; the screen on top stays opaque and fades only
  at the end — no strip of old text lingers at the edge while the motion settles), 540 ms (`--card-time`,
  `--card-ease`). View Transitions:
  `src/cardTransition.ts` decides (`isCardChange`; a new card-like screen goes there) and puts `data-card` on `<html>`
  for the transition only; names and keyframes — `app.css` «Card change». Header and bottom bar stay; the screen is
  clipped by the edges of `.app`. No dimming of the screen underneath (grey strips beside the column-wide bars). No View
  Transitions (iOS ≤ 17) or reduced motion: instant. Frames: after `startViewTransition(…).ready`, pause
  `document.getAnimations()` and set `currentTime`.
  **Never scroll the page programmatically just before, during or right at the end of a transition**: Safari on iPhone
  applies a scroll a moment after the page changes, so the pictures come out off by the scrolled distance (text over
  the header, a missing header, a jerk at the end — three customer videos, 2026-10-19). Both screens are captured at
  the current scroll; `.app` keeps its height (`--card-hold` in its min-height) so a shorter new screen cannot pull
  the scroll or lift the bottom bar; a frame after the end a scrolled page goes smoothly to the top and the hold is let
  go there. The screens are
  clipped under the header (`--card-clip-top`) and at the bottom bar's top (`--card-visible`). Taps during the 0.54 s
  are not taken (the transition's overlay catches them, as iOS does): a tap on the old card must not answer the new
  one. Check a change here in Chrome (puppeteer: frames + pixels) and in Playwright WebKit (positions only — its
  screenshots leave the new pictures of named elements blank): scrolled 0 / 3 px / to the bottom, Back, trade-offs,
  desktop with a low window.
- **Statement reserve** (customer 2026-10-19, DECISIONS.md G12): on question screens the statement block keeps the
  height of the longest statement at the current width, among those within 7 lines on the Figma phone (`REF_LINES`,
  `REF_VIEWPORT` in `src/statementReserve.ts`; measured in the browser over all statements of the data), so the answers
  stay in one place on every screen (customer 2026-10-22): where the card does not fit the window, it goes on under the
  bottom buttons with the fade; where it fits, its bottom is crisp. Never limit it to the free space (on short screens
  the answers jumped). The statement itself is always shown whole (no inner scroll: its end, «even if …», must be read).
- **Home on narrow phones:** the hero picture is 150 px (Figma) from ~390 px wide; narrower, it shrinks
  (`width: min(150px, 100% − 184px − 4px)`) so «Find your / vote match» always stays on two lines. Never three lines.
- **Fonts:** Fraunces only from `src/assets/fonts/fraunces-opsz.woff2` (regenerate with `node scripts/subset-fraunces.mjs`);
  Plus Jakarta Sans from `@fontsource` 400/500/600 Latin. `body` has `-webkit-font-smoothing: antialiased`.
  `.btn-primary` letter-spacing −0.43 px; all other text 0 except the eyebrow.
- **How to verify a layout change:** puppeteer-core with the local Chrome, viewport 402×874, `isMobile`, and
  `Emulation.setSafeAreaInsetsOverride({ insets: { top: 62, bottom: 34, left: 0, right: 0 } })` — then element
  coordinates are directly comparable with the Figma frame. Reference (measured 2026-10-17): burger 70–114; Home
  Start the quiz 716–772, Behind the results 780–824; Question card top 146, Next 768–824. Compare distances, not just
  positions, and also check a browser viewport (insets 0) and a short screen (375×560).

## Customer decisions (do not change)
- Answers are stored nowhere: no localStorage/sessionStorage/cookies/IndexedDB. Reload = start over.
- The result never goes into the URL. No third-party trackers, fonts or requests (CSP in `public/_headers`).
- Bill titles: Hebrew only, `dir="auto" lang="he"`, right-aligned; under them the Knesset and the sponsors, no direction line
  (customer 2026-10-25). Never show `summary_en`.
- Never show: coalition/opposition, attitude to the government, number of MKs, list logos.
- Notes only on List details, none on Results (customer 2026-10-25): the warning note (only one / only two Knesset
  members, few Knesset members in the top ten) and «position known for only N% of your answers». No votes of lists on Methodology.
  No topic selection.
- Every UI string in `../export/quiz_texts.json`, read through `src/strings.ts` / `src/texts.ts`. Metrics: only `started` /
  `finished` via `track()` — a beacon to the site's own `/count/<event>`, nothing else (DECISIONS.md H7).
- Share (Results) shares the site's address and one sentence, never the result (H8).
- Entries that lead to a page with an address (Methodology) are real links that act in the app (`LinkButton`, H10); never hidden text for search engines.

## Code
- `src/engine/` — pure TypeScript port of `pipeline/quiz_match.py` + `pipeline/quiz_report.py`. No React, no DOM.
- **Python is the reference**: `../export/golden.json` must pass (1e-9), including the «flow N» question-order cases
  (`src/engine/flow.ts` reproduces numpy's std summation bit for bit). If a golden case fails because Python looks
  wrong — stop and describe it to the customer; do not «fix» the TS to differ.
- Explanation strings that appear in golden must reproduce it exactly.
- `src/state/` — `useReducer` state machine, pure and tested. No router.
- A CSS time token read from JavaScript goes through `src/cssTime.ts` (the production minifier writes `200ms` as `.2s`; `parseFloat` alone gave 0.2 ms, H12).
- Screen changes: a card change slides (G11, `slideCard`), any other change of screen cross-fades (H13, `fadeScreen`); both in `src/cardTransition.ts`, both skipped with reduced motion.
- Screens are tested through `<App/>` in jsdom (`src/screens/screens.test.tsx`), including the privacy rules.

## Before a commit
`npm run typecheck && npm test && npm run build && npm run check:dist` — all green (CI runs the same).

## How to work
- Small steps: one screen or one component plus its test; commit when the step is done and checks pass; one topic per commit.
- Product decisions (wording, what to show, behaviour) — list options and ask (P1). Engineering choices with an obvious
  default — take it and note it in `DECISIONS.md`.
- Budget: $20 subscription — almost no sub-agents.
- Push only when the customer asks.

Commands: `npm run dev`, `npm test`, `npm run build` (includes the prerender), `npm run typecheck`, `npm run check:dist`,
`node scripts/make-icons.mjs` (icons and the link-preview picture into `public/`, needs Chrome).
Hosting (Cloudflare Pages): root directory `web`, `npm run build`, output `dist`, environment variable `SITE_URL`;
`wrangler.toml` binds the Analytics Engine dataset of the metrics function (`functions/count/[event].js`).
