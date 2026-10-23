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
- Data: the contract in `../export/` only — `quiz_core.json`, `quiz_data.json`, `quiz_bills.json`, fetched at run time in
  this order by `src/data.ts` (never bundled; content-hashed, never inlined — CSP `connect-src 'self'`).
  Contract and loading order: `../export/WEB_CONTRACT.md`; overview: `../export/README.md`.
- Texts: every text the user reads is in `../export/quiz_texts.json` (§7, edited by hand), **bundled** into the JS on
  purpose (`src/texts.ts`: zod schema with the allowed `{placeholders}` of every key, `T` parsed at load;
  `npm run schema:texts` after changing the structure). Screens use `S` / `explainText` from `src/strings.ts`, which only
  fills templates from `T` — no text in code. The page `<title>` is set from `app.title` by `bootLoader` (vite.config.ts).
- A screen renders only when its file has arrived (App shows a loader for that screen only): Start — nothing; questions —
  quiz_core, clarifying ones and everything after — quiz_data; List details, Bills, Methodology — quiz_bills.
- **The start page loads first** (DECISIONS.md G): `index.html` preloads its fonts, quiz_core and the hero
  (`preloadStartPage` in `vite.config.ts`); quiz_data and quiz_bills start only after it is drawn (`firstScreenShown` in
  `src/data.ts`). A new font or picture on Home → add it to the preload. Measure with a production build (gzip), never
  the dev server: Slow 4G (150 ms, 1.6 Mbit/s), CPU ×4, no cache — Home complete ≈ 1.24 s on 2026-10-18.
- Loading picture = dot rings + a running blue dot (Figma «Frame 9», geometry in `src/components/dotRing.ts`, styles
  `.dot-ring` in `app.css`), in two places: before the JS has drawn anything — `index.html` (`bootLoader` in
  `vite.config.ts`, plain HTML + CSS, no script; React replaces it; same `.app` box as the first screen); in the app —
  `<Loading/>` on a screen waiting for its file. Every ring uniform (no lighter dots around the blue one).
- Phone preview over ngrok points at the production build (`vite build --watch` + a static server with gzip and the CSP
  from `public/_headers`), not at `npm run dev` (unminified React, no compression: 5.4 MB).
  Run: `npx vite build --watch`, `node scripts/serve-dist.mjs 4173`, `ngrok http 4173`.

## Design: Figma first
- **A screen that has a Figma mockup is built exactly as the mockup**: texts, number of answers, buttons, progress,
  menu. Open the frame (`get_design_context` / `get_screenshot`) before writing code; do not invent wording.
- If the mockup conflicts with SPEC or the data (e.g. «60 statements» vs 65 in the data): follow the mockup where it is
  only presentation, and **ask the customer right away** about the rest. Do not silently keep the old behaviour.
- After a screen: screenshot at 402 px wide and compare with the frame.
- Screens without a mockup (Results, List details, Bills, Methodology): Figma tokens and components; layout is the agent's
  proposal, recorded in `DECISIONS.md`.
- `src/styles/tokens.css` is the only place for colors, type, spacing, radii. Mobile first, 360–430 px, column ≤ 480 px.

## Design spec: Figma «Colors & Typography»
Source of truth for colors and text styles: https://www.figma.com/design/TTgHWki3flpBiQ6U9XQF7I/CSS?node-id=20-133
(«все значения взяты из макетов»). If it changes, re-read the node and update `tokens.css` and this section together.

### Colors
| Figma | Value | Token | Used for (Figma) |
|---|---|---|---|
| Brand / Primary | `#0038B8` | `--color-accent` | Next / Start the quiz, selected answer, links, eyebrow, menu icons, counter |
| Brand / Disabled | `#B3C3EC` | `--color-accent-disabled` | Next while no answer is selected |
| Brand / Tint 10% | `#0038B8` @ 10% | `--color-accent-soft` | question panel, chips, steps card, letter badges, back button, progress track, line under the menu title* |
| Brand / Line 20% | `#0038B8` @ 20% | `--color-border` | «or» dividers |
| Surface / Default | `#FFFFFF` | `--color-bg`, `--color-surface` | screens, answer buttons, cards A/B/= |
| Surface / Subtle | `#F5F7FC` | `--color-surface-subtle` | in Figma only the Answer card kit background |
| Text / Primary | `#121212` | `--color-text` | body text |
| Text / Secondary | `#595E6B` | `--color-text-muted` | subtitles, explanations |
| Text / Tertiary | `#8A8F9C` | `--color-text-faint` | «or», small captions |
| Text / On primary | `#FFFFFF` | `--color-accent-text` | text on blue buttons and selected badges |
| Icon / Primary | `#111111` | `--color-icon` | burger, menu close |
| Base / Black | `#000000` | `--color-text-strong` | answer button text; Fraunces texts in the screen frames (Labels/Primary) |
| Overlay / Scrim 40% | `#000000` @ 40% | `--color-dim` | dim under the open menu |

The sheet labels Text / Primary «headings, question», but the screen frames use black for Fraunces texts — we follow
the frames. *The sheet puts the menu line under Line 20%, the Menu frame draws it at 10% — customer 2026-10-17: 10%.

### Typography
Line heights are exact Figma px ÷ size (`calc(22 / 17)`), never rounded ratios. Letter spacing is 0 unless listed.

| Figma style | Font | Size / line height | Class | Where |
|---|---|---|---|---|
| Title/Large | Fraunces 400 | 36 / 42 | `.title-xl` | Home title |
| Title/Medium | Fraunces 400 | 28 / 34 | `.title-lg` | app name in the menu |
| Question | Fraunces 400 | 20 / 22 | `.statement-text`, `.title-md` | statement, clarifying question, section titles in List details, Bills and Methodology |
| Action | Plus Jakarta Sans 600 | 17 / 22, −0.43 px | `.btn-primary`, `.btn-secondary` | Start the quiz, Next, Change answers |
| Button | Plus Jakarta Sans 600 | 17 / 22 | `.answer`, `.btn` | answer options |
| Body/Large | Plus Jakarta Sans 400 | 17 / 24 | `body`, `.tagline` | Home subtitle |
| Menu item | Plus Jakarta Sans 500 | 17 / 22 | `.menu-item`, `.accordion-head`, `.bill-title` | menu items, statement titles in Methodology, bill names |
| Label/Strong | Plus Jakarta Sans 600 | 15 / 20 | `.btn-link`, `.choice-title`, `.step-number`, `.choice-badge`, `.title-sm`, `.list-row-value`, `.scale-top .list-row-name`, `.scale-legend` | Behind the results, Not sure — skip, card titles A/B/=, Details card titles, Results closeness / names in the panel / scale legend |
| Counter | Plus Jakarta Sans 600 | 15 / 22 | `.counter` | progress counter |
| Label/Medium | Plus Jakarta Sans 500 | 15 / 20 | `.step`, `.list-row-name` | Home steps, Results names below the panel |
| Body/Default | Plus Jakarta Sans 400 | 15 / 21 | `.lead`, `.explain`, `.small` | card explanations, intro text, «Based on …», bill details |
| Chip | Plus Jakarta Sans 500 | 13 / 20 | `.chip`, `.note` | chips (N statements, 3–5 min), notes |
| Caption | Plus Jakarta Sans 400 | 13 / 18 | `.choice-sub`, `.xsmall` | «Your answer: …», data version |
| Caption, Medium (not in Figma) | Plus Jakarta Sans 500 | 13 / 18 | `.or-divider` | «or», «Not ranked: not enough data» (customer 2026-10-23) |
| Eyebrow | Plus Jakarta Sans 600 | 12 / 16, 0.72 px (6%), upper case | `.eyebrow` | label above the title |
| — (not in Figma) | Plus Jakarta Sans 800 | 15 / 20 | `.list-row-rank` | Results rank numbers (customer 2026-10-23) |

- **Every text is one of these styles** (check: all screens, computed styles vs this table — 2026-10-22 all match). The
  only exception: bold run-in titles and list labels inside Methodology text (`<strong>`, `<em>`: 600 in Body/Large).
  Bold is 600 — the font is loaded up to SemiBold; a 700 would be faked by the browser. No italics (none in Figma, no
  italic face loaded).
- Fraunces axes for every style: **WONK 1 · SOFT 0 · opsz auto**. They are baked into `src/assets/fonts/fraunces-opsz.woff2`
  (`scripts/subset-fraunces.mjs`: opsz kept, WONK/SOFT/wght pinned, Latin UI subset) — no `font-variation-settings` in CSS.
- `body` has `-webkit-font-smoothing: antialiased`: without it macOS browsers draw text 6–13 % heavier than Figma.
- Checking a text against Figma: export the node at 4x (`use_figma` → `node.screenshot({ scale: 4 })`), render the page at
  DPR 4 and overlay the two; matching ink within ~1 % and no colored fringes = same.

## Design spec: Figma «Layout & Spacing»
Source of truth for layout: https://www.figma.com/design/TTgHWki3flpBiQ6U9XQF7I/CSS?node-id=27-133 (annotated frames of
Home, Question, Clarifying question, Menu). All values in px.

### General rules
- Mockup 402×874 pt (iPhone 16/17 Pro). Web: width 100 %, check 360–430 px.
- Side margins 24 for every block. Exception: burger and close — 44×44 tap area starts at 14 so the 24×24 icon sits at 24.
- Top: 62 in the mockup = iPhone status bar. Web: `padding-top: calc(env(safe-area-inset-top) + 8px)`. Never hard-code 62.
- Bottom: 34 in the mockup = home indicator. Web: `padding-bottom: calc(env(safe-area-inset-bottom) + 16px)`.
  Screen height `min-height: 100dvh` (not `100vh`).
- A screen is a vertical flex: top blocks stacked with fixed gaps → spacer `flex: 1` → bottom button group.
- Bottom buttons are always pinned to the bottom, never at a fixed distance from the content. Longer content scrolls,
  buttons stay (`position: sticky; bottom: 0`).
- Buttons: height 56, radius 28 (capsule). Link-button: height 44 (tap area), text centered.
- Cards: height hugs content, width fills (100 % minus margins).
- Known mockup inaccuracies, fix in code: the bottom group on question screens starts at 31 from the left → use 24;
  the top row with progress ends 29 from the right → use 24.

### 01 · Home
- Header (burger): top 62, height 44; 44×44 area at left 14, icon 24.
- Hero row: 28 after the header. Row flex: title block (`flex: 1`) + graphic 150×150, gap 4, vertically centered.
- Title block: eyebrow (12/16) → 8 → title (36/42).
- Subtitle: 28 after the hero row, line height 24.
- Chips: 20 after. Row, gap 8. Chip: padding 6 12, height 32, radius 16, width hugs text.
- Steps card: 28 after. Padding 20, gap 16, radius 24, width fill. Step: circle 32 + gap 12 + text, vertically centered.
- Spacer `flex: 1` — everything below is pinned to the bottom.
- Start the quiz: height 56, width fill. 8 below — Behind the results, height 44. Under it **16 + safe area** (general
  rule; original Home frame: 0).

### 02 · Question
- Top row: top 61, height 44. Row flex, gap 12, centered: burger 44×44, progress track (`flex: 1`, height 6, radius 3),
  counter «1/10».
- Question card: **32** after the top row (original Questions frame: 37), width fill, radius 24, padding 20
  top/bottom and 14 left/right, height hugs.
- Inside, no gap between blocks: statement block padding 8 8 24 8 → answers (buttons 56, gap 8, width fill) → «or»
  divider (padding-top 8) → skip link (height 44).
- Spacer `flex: 1`.
- Bottom group: pinned to the bottom, 16 above the safe area (50 from the bottom in the mockup). Row flex, gap 12:
  back 56×56 + Next (`flex: 1`, height 56). Margins 24 (31 on the left in the mockup is a mistake).

### 03 · Clarifying question
- Top row: as on the question screen, but no track (`justify-content: space-between`): burger left, counter «1/3» right.
- «Thanks!…» text: **16** after the top row, 15/21 (original Clarifying question frame: 7).
- Card: 16 after, radius 24, padding 20/14. Question block: padding 8 8 24 8; question → 8 → explanation.
- Cards A and B: gap 8, radius 28, padding 14 16, circle 28 + gap 12 + text. Border 2px always (transparent / blue) so
  nothing jumps.
- «or» divider: padding 12 top and bottom. Card «=» is the same as A/B.
- Spacer `flex: 1`. Bottom group: as on the question screen.

### 04 · Menu
- Dim: full screen, black 40 %. Tap on it closes the menu.
- Web (customer 2026-10-18): the drawer and the dim live in a frame over the visible part of `.app` — the screen on a
  phone, the card in card mode (the card behaves as the phone: the drawer slides from its edge, clipped by its corners;
  the page around stays undimmed, a click there closes). Slides in 300 ms (`--menu-in`), out 200 ms (Menu.tsx, Web
  Animations); none with reduced motion. The page does not scroll while it is open. Close = burger point always,
  also on a scrolled long screen.
- Panel: width 320 (max 85 % of the frame), height 100 %, at the left edge. Vertical flex, padding 62 24 34 24 (top and bottom = safe area).
- Close 44×44 at the same point as the burger. On open, focus goes to the dialog itself (`tabIndex=-1`, no ring), not
  to Close: Safari would draw the keyboard focus ring around the X after a click (customer 2026-10-18: no circle).
- Head: padding-top 16, eyebrow → 8 → title (28/34).
- Divider: 1px line, Brand / Tint 10%, 16 above and below.
- Items: height 52, gap 0, icon 24 + gap 12 + text.
- Spacer `flex: 1`. At the bottom GitHub/Behance buttons 48×48, gap 12, pinned to the bottom (34 safe area).
  (Hidden until the links exist — DECISIONS.md D.3.)

## Design spec: Figma «Web: browser bars»
https://www.figma.com/design/TTgHWki3flpBiQ6U9XQF7I/CSS?node-id=28-260 — how the mockup's 62 / 34 translate to a
browser, where the top and bottom are taken by browser bars whose height changes on scroll. Never use 62 and 34 as
numbers: they become `env(safe-area-inset-*)` and the viewport units.

| Environment | Top | Bottom |
|---|---|---|
| iPhone · Safari, bar at the bottom | only the status bar; the page starts under it, `env(top) = 0` → 8 | Safari bar (≈ 88 pt, collapses on scroll); Next sticks to the bottom of the visible area → 16 + `env(bottom)` |
| Android · Chrome, address bar on top | address bar, hides on scroll down → 8 | gesture strip only → 16 |
| Added to Home Screen (PWA) | no browser bars: status bar = `env(top)` (as 62 in the mockup) → `env(top)` + 8 | home indicator = `env(bottom)` (as 34) → `env(bottom)` + 16 |

| What | Mockup (iOS app) | Web |
|---|---|---|
| Space above the header | 62 (status bar) | `calc(env(safe-area-inset-top) + 8px)` |
| Header (burger, progress) | height 44 | height 44 |
| Gaps between blocks | 28 / 20 / 16 / 32 … | same numbers in px |
| Side margins | 24 | `padding-inline: 24px` |
| Space under the bottom buttons | 50 = 34 safe area + 16 | `calc(env(safe-area-inset-bottom) + 16px)` |
| Screen height | 874 | `min-height: 100dvh` — **not `100vh`, not `100svh`** (customer 2026-10-17: with svh an empty strip appears under the buttons when the Safari bar is collapsed) |
| Bottom buttons | pinned to the bottom | `position: sticky; bottom: 0`; white background so content goes under them; **12 px** white band above the buttons (`padding-top`) |
| Menu (drawer) | height 874 | `height: 100dvh`; top / bottom through `env()` as above; width `min(320px, 85vw)` |

The sheet's CSS has no bottom padding on the screen and puts `env(bottom) + 16` only on the bottom bar. Our code keeps
`env(bottom)` on `.app` (screens without a bottom bar need it) and cancels it on the bars with a negative margin — same
result.

Manual check on real devices (from the sheet):
- iPhone, Safari: scroll down and up — Next always visible, never under the Safari bar.
- iPhone: Safari settings → tab bar on top (Single Tab) — the layout must not change.
- Android, Chrome: the address bar hides on scroll — header and buttons do not jump.
- Add the site to the Home Screen and open it — header not under the clock, buttons not under the bottom strip.
- 360 px and 430 px wide — margins stay 24, buttons stretch.

## Breakpoints — rules for every web screen («версия Б», customer 2026-10-17)
Applies to **all screens** (Home, Question, Clarifying question, Menu, Results, List details, Bills, Methodology) and
to any new one. Based on Material 3 window size classes. Previous layout = «версия А», snapshot in
`design-variants/layout-A/` (roll back on request).

### Principles
1. **The layout type changes only at the points; between them everything changes smoothly** (clamped values, no jumps,
   no ad-hoc media queries per screen).
2. **What shrinks first:** outer margins → the free space above the bottom buttons. Text, buttons, tap targets and the
   card width never shrink. Never scale the card down to fit (defeats browser zoom).
3. **Tall windows never stretch a screen:** extra height goes to the margins, the card stays centred.
4. **When even the minimums do not fit, the page scrolls,** and a screen's primary bottom buttons stay visible (sticky
   with a fade). The header (burger, progress, counter) is pinned on top on every screen (customer 2026-10-18).
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
| List details, Bills, Methodology | none (Back link at the top, «Show all» inside the list) | — | — |

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
  header clears the status bar; `.app` has no top padding. `.app` bottom: safe area only; the bottom groups add their own 16.
- **Bottom groups.** Both use `padding-bottom: calc(16px + env(safe-area-inset-bottom))` and
  `margin-bottom: calc(-1 * env(safe-area-inset-bottom))` (the screen's safe area moves inside the group), so they sit
  16 above the safe area (Home too — general rule, not the 0 drawn in the Home frame).
  - Both are **sticky with a fade** («версия Б», see «Breakpoints»): on a short screen the content scrolls under them.
    (In «версия А» Home was not sticky — the customer had disliked the hard cut without a fade.)
- **Burger and close:** `margin-inline-start: calc((24px - var(--tap-min)) / 2)` — icon on the 24 px text column, tap area
  hangs left; the menu close button is at exactly the burger's point.
- **Spacing that differs from the frames:** Question top row → card **32** (frame 37); Clarifying top row → «Thanks!»
  **16** (frame 7). Everything else as in «Layout & Spacing».
- **`.panel` has no gap**: spacing inside the question card comes from its blocks (statement padding 8 8 24, «or»
  padding-top 8, 44 px skip link). In the clarifying card «or» gets `padding-block: 4px` inside the 8 px card stack → 12 / 12.
- **Menu line** under «Vote Match»: Tint 10 % (`--color-accent-soft`), as in the Menu frame.
- **Card mode (see «Breakpoints»):** page background Brand / Tint 10 %, the 480 px column is a white card (radius 32,
  soft shadow, margins 16–32); the menu opens inside the card (see «04 · Menu»). The card's top is
  `max(gap, (100dvh − 812) / 2)` on every screen (not flex-centred: a long screen would start higher and the header jump);
  `overflow: clip` keeps the pinned header's corners inside the radius (never `hidden` — it breaks sticky). No Figma frame — customer chose this variant (C) from
  three rendered options. Never scale the card down to fit (rejected: it defeats browser zoom). Recipes and saved
  alternatives: `design-variants/`.
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
- Bill titles: Hebrew only, `dir="auto" lang="he"`, plus the direction line. Never show `summary_en`.
- Never show: coalition/opposition, attitude to the government, number of MKs, list logos.
- Exactly two notes (few former MKs: N; position known for only N% of your answers). No votes of lists on Methodology.
  No topic selection.
- Every UI string in `../export/quiz_texts.json`, read through `src/strings.ts` / `src/texts.ts`. Metrics: only `started` / `finished` via the no-op `track()`.

## Code
- `src/engine/` — pure TypeScript port of `pipeline/quiz_match.py` + `pipeline/quiz_report.py`. No React, no DOM.
- **Python is the reference**: `../export/golden.json` must pass (1e-9), including the «flow N» question-order cases
  (`src/engine/flow.ts` reproduces numpy's std summation bit for bit). If a golden case fails because Python looks
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
