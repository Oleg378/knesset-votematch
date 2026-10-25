# web/ — design spec from Figma

The three Figma specs the front end is built from: colors and text styles, layout and spacing of the four mocked-up screens,
and how the mockup's browser bars translate to a real browser. Values in px unless stated. Rules of work, breakpoints and the
approved implementation stay in `CLAUDE.md`; decisions in `DECISIONS.md`. When Figma changes, re-read the node and update
`src/styles/tokens.css` and this file together.

## Design spec: Figma «Colors & Typography»
Source of truth for colors and text styles: https://www.figma.com/design/TTgHWki3flpBiQ6U9XQF7I/CSS?node-id=20-133
(«все значения взяты из макетов»). If it changes, re-read the node and update `tokens.css` and this section together.

### Colors
| Figma | Value | Token | Used for (Figma) |
|---|---|---|---|
| Brand / Primary | `#0038B8` | `--color-accent` | Next / Start the quiz, selected answer, links, eyebrow, menu icons, counter |
| Brand / Disabled | `#B3C3EC` | `--color-accent-disabled` | Next while no answer is selected |
| Brand / Tint 10% | `#0038B8` @ 10% | `--color-accent-soft` | question panel, chips, steps card, letter badges, back button, progress track, line under the menu title* |
| — (Brand / Tint 10% as one solid colour) | `#E5EBF8` | `--color-page-tint` | page around the card in card mode, also past its ends when scrolled beyond them (not in Figma, customer 2026-10-24) |
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
| Question | Fraunces 400 | 20 / 22 | `.statement-text`, `.title-md`, `.header-title` | statement, clarifying question, section titles in List details and Methodology, «Your result» in the header |
| Action | Plus Jakarta Sans 600 | 17 / 22, −0.43 px | `.btn-primary`, `.btn-secondary` | Start the quiz, Next, Change answers |
| Button | Plus Jakarta Sans 600 | 17 / 22 | `.answer`, `.btn` | answer options |
| Body/Large | Plus Jakarta Sans 400 | 17 / 24 | `body`, `.tagline` | Home subtitle |
| Menu item | Plus Jakarta Sans 500 | 17 / 22 | `.menu-item`, `.bill-title` | menu items, bill names |
| Label/Strong | Plus Jakarta Sans 600 | 15 / 20 | `.btn-link`, `.choice-title`, `.step-number`, `.choice-badge`, `.title-sm`, `.list-row-value`, `.scale-top .list-row-name`, `.scale-legend`, `.details-group .accordion-head` | Behind the results, Not sure — skip, card titles A/B/=, Details card titles, Results closeness / names in the panel / scale legend |
| Counter | Plus Jakarta Sans 600 | 15 / 22 | `.counter` | progress counter |
| Label/Medium | Plus Jakarta Sans 500 | 15 / 20 | `.step`, `.list-row-name`, `.list-names-rows`, `.accordion-head`, `.details-head .note` | Home steps, Results names below the panel, names of lists and statement titles in Methodology; List details, a list's note — blue on the blue tint band (customer 2026-10-25) |
| — (not in Figma) | Plus Jakarta Sans 500 | 15 / 21 | `.fact-value` | List details, the value of a fact under its label (text, customer 2026-10-25) |
| Body/Default | Plus Jakarta Sans 400 | 15 / 21 | `.lead`, `.explain`, `.small`, `.details-row .list-row-name` | card explanations, intro text, «Based on …», bill details, List details «Closeness to you» (text/tertiary) |
| Chip | Plus Jakarta Sans 500 | 13 / 20 | `.chip`, `.note` | chips (N statements, 3–5 min), the question screen's notice |
| Caption | Plus Jakarta Sans 400 | 13 / 18 | `.choice-sub`, `.xsmall` | «Your answer: …», data version |
| Caption, Medium (not in Figma) | Plus Jakarta Sans 500 | 13 / 18 | `.or-divider` | «or», «Not ranked: not enough data» (customer 2026-10-23) |
| Eyebrow | Plus Jakarta Sans 600 | 12 / 16, 0.72 px (6%), upper case | `.eyebrow`, `.fact-label` | label above the title; List details, the label of a fact in an opened topic (text/tertiary, customer 2026-10-25) |
| — (not in Figma) | Plus Jakarta Sans 800 | 15 / 20 | `.list-row-rank` | Results rank numbers (customer 2026-10-23) |
| — (not in Figma) | Plus Jakarta Sans 800 | 22 / 26 | `.details-row .list-row-value` | List details closeness percent (customer 2026-10-24) |
| — (not in Figma) | Fraunces 400 | 32 / 38 | `.details-section` | List details «Why it fits» / «Why it doesn't fit», no count, `--color-text-section` #26282E (customer 2026-10-24) |
| — (not in Figma) | Fraunces 400 | 26 / 32, lines balanced | `.details-title` | List details list name, a 3 px blue line on its left (customer 2026-10-24) |
| — (not in Figma) | Plus Jakarta Sans 400 italic | 15 / 21 | `.hint`, `.details-caveat` | Results «Tap › for details», List details «This shows …», text/tertiary (customer 2026-10-23, 2026-10-24) |

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
- Side margins 24 for every block. Exception: burger, close and Back in the burger's place — 44×44 tap area starts at 14
  so the 24×24 icon sits at 24.
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
