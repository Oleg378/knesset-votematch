---
name: react-ui-mobile
description: Phone-first viewport, scroll and motion rules for the quiz front end (web/, React + Vite, one column ≤ 480 px). Use when building or changing any screen or component in web/, when adding or fixing an animation (progress bar, question card change, menu drawer, expanding blocks and accordions, the loading screen), when fixing CSS that mentions vh, fixed or sticky positioning, scroll or transitions, and when the customer reports a jumping bottom bar, cut-off content, a drawer that scrolls the page behind it, or jerky motion.
---

# Mobile UI rules for web/

The product is a phone-first quiz: one column ≤ 480 px (`--column-max`). The only other layout is card mode
(width ≥ 600 and height ≥ 480: the column becomes a white card on the brand tint, `web/CLAUDE.md` «Breakpoints», [У]);
no other breakpoints. No inputs, answers live only in memory. Figma says what a screen looks like (`web/CLAUDE.md`);
this skill covers what Figma does not show: viewport, safe areas, scroll, motion, and how to keep the screen tests
green while doing it. Where this skill and an approved decision in `web/CLAUDE.md` or `DECISIONS.md` disagree, the
decision wins; tell the customer about the conflict.

## The page model

Two models exist. The customer chose both, by where the page runs (2026-10-24, `DECISIONS.md` G28): **a browser keeps
the window scroll** (its bars must hide on scroll — «крит»); **an app's built-in viewer on a phone gets the frame**
(`src/inApp.ts` sets `data-frame`): the header outside the scroll, only `.app-scroll` under it scrolls (`html, body` do
not), the bottom bars sticky inside it. `src/scroller.ts` names what scrolls in each case. In both, the bottom safe
area is on `.screen` (a sticky bar stops at a scroller's padding). Card mode always scrolls the window. The two
descriptions below are the general patterns; where they differ from this, the decision wins (e.g. `BottomBar` stays
in the screens).

**Shell (proposed, [А]).** The frame stays, the content moves inside it: header (menu button, progress bar or
counter) and bottom bar are rows of a fixed grid, only the middle row scrolls.

```css
html, body { height: 100%; overflow: hidden; overscroll-behavior: none; }
.shell { height: 100dvh; display: grid; grid-template-rows: auto 1fr auto; }
.shell > main { overflow-y: auto; overflow-x: clip; overscroll-behavior: contain; min-height: 0;
                display: flex; flex-direction: column; }
```

- Gains: the header and bottom bar never move; a card change on a long screen does not bring the browser toolbar
  back mid-motion; the menu needs no scroll lock; pull-to-refresh is blocked, which protects the in-memory answers.
- Costs, to be accepted by the customer: the Safari toolbar never collapses, so long screens (Results, Bills) show
  less; landscape (≈ 320–340 px visible) and 200 % text leave `main` a sliver, so under `@media (max-height: 30rem)`
  the bottom bar moves to the end of `main`'s content; the status-bar tap to scroll up does not work; full-page
  screenshots capture only the viewport, so screenshot `main`'s scroll height for the Figma comparison.
- Migration is one step, its own commit, before any animation: `.app` becomes a `div.shell` with `<Header/>`,
  `<main ref>`, and a bottom-bar slot; `BottomBar` is lifted from `QuestionScreen` and `TradeoffScreen` into `App`
  (otherwise it leaves with the card); `Menu` renders outside `main` (a sibling of the shell or a portal to `body`);
  the boot loader in `index.html` (`bootLoader` in `vite.config.ts`) and `<Loading/>` use the same shell; card mode
  keeps working (the shell is the card, its height `min(var(--desktop-card-height), 100dvh − 2 × --desktop-gap)`);
  safe-area padding moves from `.app` to the rows (top on
  the header, bottom on the bar, sides on the shell); `.push-down` keeps working because `main` is a flex column;
  scroll reset becomes `mainRef.current.scrollTop = 0`; the screen tests stay green.

**Window scroll (today's model, kept if the customer prefers).** Header `position: sticky; top: 0` and bottom bar
`position: sticky; bottom: 0`, page wrapper `.app { min-height: 100dvh }` — the customer's decision (2026-10-17,
`web/CLAUDE.md` «Web: browser bars»): with `svh` an empty strip shows under the buttons while the Safari bar is
collapsed. Do not switch to `svh` or `lvh` on your own. Its cost: `dvh` changes while the browser bar hides or shows,
so the page re-lays out at that moment (see «The browser toolbar» below). Menu locks the page (`overflow: hidden` on
`html` while open, `touch-action: none` on the dim layer, `overscroll-behavior: contain` on the drawer),
`overscroll-behavior-y: none` on `html` to reduce accidental pull-to-refresh. Known weak spots: the toolbar re-layout;
a card change on a long screen (`web/CLAUDE.md` «Card change»: never scroll programmatically around it).

## Hard rules

**Viewport**
- No `vh` units: `100dvh` (the approved choice for both models), `vw` only where a token or `%` cannot do it.
- No `window.innerHeight` / `innerWidth` in layout code, no `resize` handler that writes styles. If a measurement
  is ever needed: `ResizeObserver`, guarded for jsdom. The only exception is the keyboard recipe at the end.
- `viewport-fit=cover` stays in `index.html`; every element glued to a screen edge pads with
  `env(safe-area-inset-*)`, once (today `.app` carries the bottom inset and the bottom bars cancel it with a negative
  margin and add it inside — approved, `web/CLAUDE.md`; after migration only the bar does). Do not add
  `interactive-widget=resizes-content` (Chromium and Firefox only) unless an input appears.
- Overlays (`position: fixed`) render outside `main` and outside any element that animates: an ancestor with
  `transform`, `will-change`, `filter` or `contain: paint` becomes their containing block and clips them.

**Motion**
- Animate only `transform` and `opacity`. Never height, width, top, left, margin, padding, box-shadow,
  background-color on large areas; `transition: all` and `transition-property: all` are banned, list the properties.
  One exception, because there is no compositor-only way to move what sits below a growing block: expand and
  collapse of a block in the flow, done only by the recipe below (`src/expandMotion.ts`: px height over the part on
  screen, auto when settled).
- No `scroll`, `resize` or `touchmove` handlers at all. Reveal-on-scroll, if ever: `IntersectionObserver`.
- Reduced motion: under `(prefers-reduced-motion: reduce)` slides and scales become an opacity crossfade of at most
  a fast duration, or nothing; the state change (new card, new value, closed menu) always happens. JavaScript paths
  check `window.matchMedia?.('(prefers-reduced-motion: reduce)')`.
- Keep the animating element's identity stable during the motion: same key, same parent, class or style applied
  once. (A re-render alone does not restart a CSS transition; a remount or a removed-and-reapplied class does.)
- No `will-change` by default: browsers promote an element on their own while a transition runs, and `will-change`
  on an ancestor breaks `position: fixed` children.
- Figma first for motion too: read the prototype transitions (`get_motion_context`) before inventing values.
  Durations and easings live in `tokens.css` under the project's names: `--menu-in` (menu opening), `--card-time` and
  `--card-ease` (card change). A new motion gets its own token named the same way (`--<what>-time`, `--<what>-ease`;
  below, «fast» means about 150 ms, «base» about 250–300 ms), from Figma, or proposed in `DECISIONS.md` [А] if Figma
  has none. No literal durations in `app.css` or components; JavaScript that animates reads the token
  (`getComputedStyle(document.documentElement).getPropertyValue('--menu-out')`) instead of repeating the number.

**Exit and unmount**
- An element that animates out stays mounted until the first of: `transitionend` with
  `e.target === e.currentTarget && e.propertyName === 'transform'` (or `'opacity'`), a timeout of the duration plus
  50 ms, or immediately when reduced motion is on or the computed duration is 0. Never wait on `transitionend`
  alone: it never fires under reduced motion or in jsdom, it bubbles from children, and it fires once per property.
  An exit done with Web Animations (`element.animate(…).finished`, as the menu does) is equally fine: skip it when
  `element.animate` is missing (jsdom) or reduced motion is on, and still race it against the same timeout.
- The moment an exit starts, the leaving element gets `inert` and `aria-hidden="true"`, so it takes no taps and
  no focus.
- Focus moves to the entering screen's heading when it mounts, not when the exit ends; `focusHeading` must skip the
  leaving card (`main :not([data-leaving]) h1, …` or a ref on the entering screen). This matters only when the
  leaving element stays in the DOM (the enter/exit hook, a motion library); with View Transitions the old screen is
  a snapshot and today's `focusHeading` (first heading in `main`) is right.
- The menu on close leaves the accessibility tree and returns focus to the opener at once, even if its slide-out is
  still running; while it is open, the shell (header and `main`) is `inert`, not only `aria-modal`.

**Testing in jsdom**
- jsdom has no layout, no `transitionend`, no `Element.prototype.scrollTo`, `matchMedia`, `element.animate`,
  `getAnimations`, `ResizeObserver`, `IntersectionObserver`, `document.startViewTransition`. Guard every such call
  (`'startViewTransition' in document`, `matchMedia?.`); reset scroll with `scrollTop = 0`.
- Tests check state and focus, never motion; the exit timeout rule above is what makes a closed menu or a replaced
  card disappear in tests without polyfills. `npm test` must pass without fakes beyond what `screens.test.tsx`
  already stubs.

**Sizes**
- Tap targets ≥ 44 × 44 (`--tap-min`); Figma buttons are 56 (`--button-height`). Non-interactive text may be
  12–13 px (eyebrow, caption); interactive text ≥ 15 px.
- Widths through tokens, `%`, `min()`, flex and grid; no fixed-pixel widths on containers. Intrinsic `width` and
  `height` attributes on images are fine. `min-width: 0` plus `overflow-wrap: anywhere` on every flex or grid child
  that holds long text (Hebrew bill titles already use `dir="auto" lang="he"` and `.he { unicode-bidi: isolate }`).
  Add a global `img, svg { max-width: 100%; height: auto }` (not in `app.css` yet).
- No hover-only states. Pressed state via `:active` and `aria-pressed`; focus ring via `:focus-visible` only;
  `-webkit-tap-highlight-color: transparent` on buttons.

## Motion guidelines this skill follows

When a value or a curve is not in Figma, take it from these, in this order, and name the source in `DECISIONS.md`:
1. **Material Design, «Duration & easing»** (https://m1.material.io/motion/duration-easing.html): mobile transitions
   about 300 ms, entering 225 ms, leaving 195 ms, large full-screen changes up to 375 ms; longer for larger distances
   or surface changes; things that enter or expand decelerate (`--ease-decelerate`, `cubic-bezier(0, 0, 0.2, 1)`),
   things that leave or collapse accelerate (`--ease-accelerate`, `cubic-bezier(0.4, 0, 1, 1)`), growing and shrinking
   in place uses the standard curve.
2. **Braid Design System (SEEK), accordion** (https://github.com/seek-oss/braid-design-system/pull/2144): tall panels
   get a duration from their height, 200–500 ms, so they do not snap; px height while moving, auto when settled;
   no animation with reduced motion or on the first render.
3. **Accordion motion in design systems** (eBay Playbook, https://playbook.ebay.com/design-system/components/accordion?tab=motion,
   known from a search summary, not read in full): the container moves first, the content fades in shortly after.
4. **WebKit and Chromium facts found on the way** (iOS toolbar, viewport units): web.dev «The large, small, and
   dynamic viewport units» (dynamic units are not updated at 60 fps), WebKit bug 297779 and the Chromium explanation
   that Chrome on iOS resizes its web view when its bars move.

Measure, do not guess: for a motion that looks wrong on the phone, sample it per frame in Playwright WebKit with the
iPhone device profile (positions, heights, opacity per `requestAnimationFrame`), and say what the numbers show.

## Motion recipes for this product

- **Progress bar.** Never animate `width`. The fill is `width: 100%` inside the track (`overflow: hidden`,
  `isolation: isolate` if a corner leaks in Safari) and moves with the inline variable the component sets:
  `style={{ '--p': value / max }}` and `transform: translateX(calc((var(--p) - 1) * 100%))`. `scaleX` is wrong here
  because it squashes the rounded ends. Transition on `transform` only. `aria-valuenow` changes at once. Physical
  left-to-right is correct: the document is LTR.
- **Question card change.** Approved and built: `web/CLAUDE.md` «Card change» and `DECISIONS.md` G11 — an iOS
  navigation push with View Transitions, 540 ms (`--card-time`, `--card-ease`), `src/cardTransition.ts` +
  `app.css` «Card change». Those rules win over this section; the hardest one: never scroll the page
  programmatically just before, during or right at the end of the transition (Safari on iPhone applies the scroll
  late and the pictures come out shifted), and `.app` keeps its height through the change (`--card-hold`). Status on
  2026-10-22: the customer rejected how it looks on a real iPhone and the latest attempt is left uncommitted; do not
  reopen it unless the customer does. Visual requirement: header and bottom bar static, the old card leaves and the
  new one enters with `translateX` plus `opacity`, direction by forward or back. `key={sc.i}` stays the source of
  truth for «which card»; the animation never decides state. If the customer asks to revisit the mechanism, these are
  the options (one for every screen change, written in `DECISIONS.md`):
  - View Transitions API (today's choice; Chrome 111, Safari 18, Firefox 144; older browsers get the no-animation
    fallback). The dispatch goes inside `flushSync` in the `startViewTransition` callback; the header and bottom bar
    get their own `view-transition-name` so they stay static; taps during the transition are lost (pointer events go
    to the pseudo-elements — accepted, as iOS does); reduced motion: no transition at all.
  - A small enter/exit hook: enter with `@starting-style` (Chrome 117, Safari 17.5, Firefox 129; older browsers
    show the new state without the enter motion, which is the accepted fallback), exit per the rules above. The
    leaving card sits on `position: absolute; top: 0; left: 0; width: 100%` (natural height, not `inset: 0`),
    shifted by `translateY(-<scrollTop before the reset>)`, then the scroll resets. The card container has
    `position: relative` and `overflow-x: clip`.
  - Motion library (`AnimatePresence`): ≈ 30 KB more against the `check:dist` budget (360 KB gzip; 158.5 KB used on
    2026-10-22 — run `npm run build && npm run check:dist` for today's number),
    needs `MotionConfig reducedMotion="user"`, uses `element.animate` and `matchMedia` which jsdom lacks. Note the
    budget in `DECISIONS.md` and the check before choosing it.
- **Answer press.** `:active` on the button with `transform: scale(0.98)` at a fast duration (its own token); the selected state
  (`aria-pressed`) switches at once, with a short `opacity` or `background-color` transition only on that small
  element. Starting a scroll on a button briefly triggers `:active`; accept the flicker or delay it.
- **Menu.** The drawer slides in with `transform: translateX(-100%) → 0`, the dim layer fades with `opacity`; close
  is the reverse, unmount per the exit rules. The menu renders outside `main`. Approved specifics (`web/CLAUDE.md`
  «04 · Menu»): in 300 ms (`--menu-in`), out 200 ms; the drawer and the dim sit in a frame over the visible part of
  `.app` (the card in card mode), width `min(var(--menu-width), 85%)`. That frame's box should come from CSS
  (`position: fixed` over the column, or the shell row) or a `ResizeObserver`, not from `scroll`/`resize` handlers.
- **Expanding block** (a line that opens into details; the accordion, list details, bill lists). A height reveal
  is a layout animation by nature: everything below moves every frame. Make it cheap instead of avoiding it:
  - Use `expand(el)` / `collapse(el, done)` from `src/expandMotion.ts` (keyframes `.expanding` / `.collapsing` in
    `app.css`, tokens `--expand-*`, `--collapse-ms-per-px`, `--ease-decelerate`, `--ease-accelerate`). Approved by
    the customer 2026-10-23 after the guidelines (Material Design: opening decelerates, closing accelerates and is a
    little quicker, larger changes take longer; Braid (SEEK): px height while moving, auto when settled, duration
    from the height, 200–500 ms).
  - Only the part on screen moves: the block grows from 0 to the distance between its top and the screen's bottom
    (or its own height, if shorter), pushing what is below it down, then takes its full height at once, off
    screen. Closing shrinks from that distance to 0. Why not `grid-template-rows: 0fr → 1fr`: it runs over the whole
    height, so on a body taller than the screen the visible part fills in the first 1–2 frames of opening and
    empties only at the end of closing (measured in WebKit, 2026-10-23: 0 → 278 → 1388 px of 4644) — opening looks
    instant.
  - The content fades in a little after the block starts growing (from 20 % to 70 % of the time) and fades out in
    the first 40 % of closing.
  - Closing from a button at the block's end («Show less» on Results): `scrollBackTo(start)` first — the browser's
    own smooth scroll back to the start, its end found by a per-frame check of the position (Safari before 26 has no
    `scrollend`; a `scrollend`-only wait left a 650 ms pause in WebKit) — then `collapse` on screen (customer
    2026-10-23). What comes back where the block started («See all» and the panel's rounded bottom) rides up on the
    shrinking edge as a lid (`.scale-lid`, a non-interactive copy) and ends exactly where the closed state has it,
    so swapping in the closed state moves nothing (checked to 1 px). Tried and rejected: adding «See all» after the
    block is gone (a pop), growing it at the same time inside the panel (it showed in the middle, above the lists
    still visible, and the panel's corners snapped round at the end). Only the rows fade; the block's background
    stays, or a white band opens between the panel and the lid. A translucent tint doubles where two layers
    overlap: the lid is opaque where it covers the lists and clear where it lies on the panel. Collapsing in place there was measured wrong: the page shortens under the user, the browser pulls
    the scroll, everything slides down, and focusing the start at the end jumps 450 px.
  - The content is mounted while the motion runs: mount, then `expand` in a layout effect (keyframes need no start
    state, no frame to wait for); on close `collapse` and unmount in `done`. The closed block holds its last frame
    until it is unmounted, so no frame shows it at full height. The leaving block is `inert` and `aria-hidden`.
  - Cost control: a long list opens over the screen-high part only, so its cost does not grow with its length.
    Check on a 4× throttled CPU; if it still drops frames, that block opens instantly, with a note in
    `DECISIONS.md`.
  - Never scroll the page when a block opens: the tapped line stays where it was. No `scrollIntoView` on the
    opened block — for a block taller than the screen, `block: 'nearest'` puts its top at the top of the screen,
    and the line the user tapped jumps away (customer 2026-10-23). If a scroller changes while a block opens (a
    short page becomes long), the scroll position goes over to the new scroller.
  - Reduced motion: open and close instantly.
  - Not yet: `interpolate-size: allow-keywords` / `calc-size()` (animating `height: auto`) and `::details-content`
    are Chromium-only at the time of writing; revisit when Safari ships them (they would still need the
    on-screen-part rule above).
- **Loading screen** (see the guideline below). Built, two places (`web/CLAUDE.md` «Your area»): before the JS runs,
  the boot loader in `index.html` (`bootLoader` in `vite.config.ts`: plain HTML + CSS, no script, the same `.app`
  box as the first screen; React replaces it); in the app, `<Loading/>` on a screen whose data file
  (`quiz_core` / `quiz_data` / `quiz_bills`, fetched at run time by `src/data.ts`) has not arrived, and `<LoadError/>`
  (`S.loadError`, reload button) when it failed. The indicator is the Figma dot rings with a running dot
  (`src/components/dotRing.ts`, `.dot-ring` in `app.css`, `rotate` keyframes). Its durations and delay go into
  tokens like every other motion. There is no Suspense and no lazy chunk; if one is ever added, its failure gets an
  error boundary showing the same `<LoadError/>`.

- **Results rows.** Appear with `opacity` plus a small `translateY`, a short stagger via `animation-delay` on the
  first few rows only; no layout animations on the list.

## The browser toolbar on window-scrolled pages

On phones the browser's address bar hides on scroll down and the window height changes with it. A page that
depends on that height jumps when the bar moves; sites that feel fine have nothing sized from the window. (Safari
fires `resize` once, after the bar animation; the usual symptom is one jump at the start of a scroll, sometimes a
visible oscillation when the page is only a few pixels taller than the viewport.) In the shell the document never
scrolls, so the bar stays put; the rules below are for any window-scrolled page an agent touches.

Do not: set anything from `window.innerHeight` on `resize` (the `--vh` «100vh fix» is the classic cause); use
`100vh` or `min-height: 100dvh` on sections or page wrappers; make the page only a few pixels taller than the
viewport; scroll a wrapper sized with `vh`, or a wrapper while `body` can also scroll; change layout from a
`scroll` handler; hijack native scrolling on touch devices with smooth-scroll libraries or `scroll-snap-type` on
`html` or `body`.

**This project today.** `.app { min-height: 100dvh }` (approved, see «The page model») follows the toolbar: while
the bar hides or shows, `dvh` changes, `.app` re-lays out and the sticky bottom bar (`margin-top: auto`) and
everything sized from the window move with it. Script that reacts to `scroll`/`resize` (the menu frame, the bottom
fade, the statement reserve) adds work in exactly those frames. Ways out, each a customer decision, not a fix to make
alone: the shell (the toolbar never moves; costs above); `lvh` on `.app` (constant height, no re-layout; a short page
scrolls by the toolbar's height and the bar then collapses); keep `dvh` and remove only the script work.

Do: pick one scroll model and keep it pure; size full-height things with the unit the customer approved (`dvh`
today); keep
scroll-linked effects read-only (`IntersectionObserver`, `animation-timeline: scroll()` or `view()`, Motion's
`useScroll`); enable scroll libraries or page snapping, if wanted on desktop, only under
`(hover: hover) and (pointer: fine)`.

Diagnosis when a bar already jitters: on a phone, watch what else moves. Content jumps too → the page is sized
from the window (`grep -rnEi "innerHeight|--vh|[0-9.]vh\b" src/`). Only the bar moves → a wrapper scrolls instead of
the document (`grep -rnE "overflow(-y)?: *(auto|scroll)" src/` on page wrappers, `height: 100%` or `100vh` on
`html`, `body`, `#root`). Scrolling feels delayed or floats → a scroll library or a `scroll` handler. Temporarily
adding `html { min-height: 200vh }` separates the first case from the others.

## Loading screens: the guideline

- **Something within 100 ms.** The first thing the user sees is static HTML in `index.html` (frame, background,
  an indicator in plain CSS) that is on screen before any JavaScript runs; React replaces it. `theme-color` and
  the page background are set in `index.html` so the first frame is the product's colour, not browser grey.
- **Show by duration.** Under ≈ 300 ms show only the frame, no indicator (`animation-delay: 300ms`, so a fast
  load flashes nothing). From 300 ms an indeterminate indicator. From ≈ 1 s a text line. From ≈ 10 s an
  explanation and a retry. No minimum display time, no splash that stays for its own sake: the content replaces
  the loader the moment it is ready.
- **Show the right kind.** Known layout → a skeleton of the real screen (same positions, grey blocks), or
  better, the real static parts of the screen with only the data-dependent control disabled. Unknown duration
  → indeterminate motion. Real progress events (uploads, several files) → a determinate bar. Never a determinate
  bar on a timer, never a fake percentage.
- **No shift on handover.** The loader lives in the same frame as the first screen, at the same positions; the
  screen fades in with `opacity` over a fast duration. If the loader's text or hero moves when the app mounts,
  the loader is wrong.
- **Never block on the optional.** Fonts (`font-display: swap` or `optional`), images, analytics and the lazy
  parts of the app load in parallel and never gate the content.
- **Motion rules apply.** `@keyframes` on `transform` or `opacity` only, in CSS; no JavaScript timers for the
  animation; under reduced motion the indicator stands still and the text carries the message.
- **Accessibility.** The text sits in `role="status"` with `aria-live="polite"`, the indicator is
  `aria-hidden="true"`, the container is `aria-busy="true"` until done. The loader never takes focus; on
  handover focus stays where it was (first render) or goes to the screen's heading (later loads).
- **Failure is a state too.** A lazy chunk or a fetch can fail (offline, a deploy between the HTML and the chunk):
  an error boundary shows a message and a reload or retry button, in the same frame. A blank page or a spinner
  that never ends is a bug.
- **The best loader is a shorter load.** Before polishing the loader: code splitting so the first screen needs
  the least data, compression and cache headers on the host, `modulepreload` for the next chunk. Measure on a
  throttled «Slow 4G» profile, not on Wi-Fi: on Wi-Fi nobody ever sees the loader.
- **Test three cases:** slow network (the loader shows and hands over without a shift), offline (the error state
  shows), reduced motion (the indicator is static).

## Workflow for a screen or component

1. States to picture before writing CSS: a long statement (3–4 lines of Fraunces 20 px), long Hebrew bill titles,
   a dozen lists on Results, the trade-off pair, the menu open, 360 px wide, landscape (height ≈ 400 px, the frame
   eats two rows of it), 200 % text size.
2. Styles without a media query are the phone styles (360–430 px). The only other layout is card mode, through the one
   global media query `(min-width: 600px) and (min-height: 480px)` in `.app`; no per-screen breakpoints.
3. Values only through `src/styles/tokens.css`: no hex, no magic pixel numbers, no literal durations in components
   or `app.css`.
4. Check: screenshot at 402 px against the Figma frame (`web/CLAUDE.md`), then 360 and 430 px, then landscape at a
   short height. If no screenshot was taken, say so.
5. Motion check: Chrome DevTools, Performance panel, CPU 4× slowdown, record the card change and the menu: no long
   layout or paint bars during the motion. Rendering panel, «Paint flashing»: nothing repaints while things move,
   at most one flash at the start and end.
6. Anything touching the frame, the menu or full-height layout: DevTools emulation does not reproduce the browser
   toolbar. Before closing the step, ask the customer to open the production build on a phone once
   (`npm run preview -- --host`, same Wi-Fi) and try the card change, the menu, and the toolbar shown and hidden.

## Before a commit (in addition to web/CLAUDE.md)

```
grep -rnEi --include='*.css' --include='*.ts' --include='*.tsx' \
  '[0-9.]vh\b|innerHeight|transition(-property)?:[^;]*\ball\b|addEventListener\(\s*.(scroll|resize|touchmove)|\bon(scroll|resize|touchmove)\b|will-?change' src/
```
and literal durations in CSS (tokens live in `tokens.css`, which is skipped):
```
grep -rnE --include='*.css' --exclude='tokens.css' \
  '(transition|animation)(-duration|-delay)?:[^;]*[0-9.]m?s\b' src/
```
For each: exit code 1 (no match) is clean; exit code 2 means the command itself is wrong. Works with BSD, GNU and
the Claude Code grep. Literal durations in TypeScript (`duration: 200`) are not caught: look at the diff.

## If an input ever appears

iOS zooms when an input's font is under 16 px, and the keyboard moves the visual viewport, not the layout one, so
the bottom bar ends up behind it. This recipe is the one allowed exception to the handler and `innerHeight` rules
(the first grep above will flag it; that hit is expected). Recipe: listen to `window.visualViewport` `resize` and `scroll` (passive), set
`--kb` to `max(0, innerHeight - vv.height - vv.offsetTop)` px on `:root`, and give the bar `bottom: var(--kb, 0px)`.
