---
name: react-ui-mobile
description: Phone-first viewport, scroll and motion rules for the quiz front end (web/, React + Vite, one column ≤ 480 px). Use when building or changing any screen or component in web/, when adding or fixing an animation (progress bar, question card change, menu drawer, expanding blocks and accordions, the loading screen), when fixing CSS that mentions vh, fixed or sticky positioning, scroll or transitions, and when the customer reports a jumping bottom bar, cut-off content, a drawer that scrolls the page behind it, or jerky motion.
---

# Mobile UI rules for web/

The product is a phone-first quiz: one column ≤ 480 px (`--column-max`), centred on desktop. No desktop layout, no
inputs, answers live only in memory. Figma says what a screen looks like (`web/CLAUDE.md`); this skill covers what
Figma does not show: viewport, safe areas, scroll, motion, and how to keep the screen tests green while doing it.

## The page model

Two models exist. The customer chooses one; it is recorded in `DECISIONS.md` with its costs. Until then the code
stays as it is (window scroll, sticky bottom bar).

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
  the Suspense fallback in `main.tsx` uses the same shell; safe-area padding moves from `.app` to the rows (top on
  the header, bottom on the bar, sides on the shell); `.push-down` keeps working because `main` is a flex column;
  scroll reset becomes `mainRef.current.scrollTop = 0`; the screen tests stay green.

**Window scroll (today's model, kept if the customer prefers).** Header `position: sticky; top: 0` and bottom bar
`position: sticky; bottom: 0`, page wrapper `min-height: 100svh` (not `dvh`: on a window-scrolled page `dvh`
re-lays out while the toolbar moves), menu locks the page (`body { overflow: hidden }` while open, `touch-action:
none` on the dim layer, `overscroll-behavior: contain` on the drawer), `overscroll-behavior-y: none` on `html` to
reduce accidental pull-to-refresh. Known weak spot: a card change on a long screen resets scroll, Safari brings
the toolbar back during the motion.

## Hard rules

**Viewport**
- No `vh` units. Shell: `100dvh`. Window-scrolled page: `svh`. `vw` is fine (`.menu` width).
- No `window.innerHeight` / `innerWidth` in layout code, no `resize` handler that writes styles. If a measurement
  is ever needed: `ResizeObserver`, guarded for jsdom.
- `viewport-fit=cover` stays in `index.html`; every element glued to a screen edge pads with
  `env(safe-area-inset-*)`, once (today `.app` and `.bottom-bar` both add the bottom inset; after migration only
  the bar does). Do not add `interactive-widget=resizes-content` (Chromium and Firefox only) unless an input appears.
- Overlays (`position: fixed`) render outside `main` and outside any element that animates: an ancestor with
  `transform`, `will-change`, `filter` or `contain: paint` becomes their containing block and clips them.

**Motion**
- Animate only `transform` and `opacity`. Never height, width, top, left, margin, padding, box-shadow,
  background-color on large areas; `transition: all` and `transition-property: all` are banned, list the properties.
  One exception, because there is no compositor-only way to move what sits below a growing block: expand and
  collapse of a block in the flow, done only by the recipe below (`grid-template-rows`), never by `height`.
- No `scroll`, `resize` or `touchmove` handlers at all. Reveal-on-scroll, if ever: `IntersectionObserver`.
- Reduced motion: under `(prefers-reduced-motion: reduce)` slides and scales become an opacity crossfade of at most
  `--motion-fast`, or nothing; the state change (new card, new value, closed menu) always happens. JavaScript paths
  check `window.matchMedia?.('(prefers-reduced-motion: reduce)')`.
- Keep the animating element's identity stable during the motion: same key, same parent, class or style applied
  once. (A re-render alone does not restart a CSS transition; a remount or a removed-and-reapplied class does.)
- No `will-change` by default: browsers promote an element on their own while a transition runs, and `will-change`
  on an ancestor breaks `position: fixed` children.
- Figma first for motion too: read the prototype transitions (`get_motion_context`) before inventing values. Then
  add `--motion-fast` (presses), `--motion-base` (card change, menu), `--ease-out`, `--ease-in-out` to `tokens.css`
  from Figma, or propose values in `DECISIONS.md` [А] if Figma has none. No literal milliseconds in `app.css`.

**Exit and unmount**
- An element that animates out stays mounted until the first of: `transitionend` with
  `e.target === e.currentTarget && e.propertyName === 'transform'` (or `'opacity'`), a timeout of the duration plus
  50 ms, or immediately when reduced motion is on or the computed duration is 0. Never wait on `transitionend`
  alone: it never fires under reduced motion or in jsdom, it bubbles from children, and it fires once per property.
- The moment an exit starts, the leaving element gets `inert` and `aria-hidden="true"`, so it takes no taps and
  no focus.
- Focus moves to the entering screen's heading when it mounts, not when the exit ends; `focusHeading` must skip the
  leaving card (`main :not([data-leaving]) h1, …` or a ref on the entering screen). Today it takes the first
  heading in DOM order, which would be the old one.
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

## Motion recipes for this product

- **Progress bar.** Never animate `width`. The fill is `width: 100%` inside the track (`overflow: hidden`,
  `isolation: isolate` if a corner leaks in Safari) and moves with the inline variable the component sets:
  `style={{ '--p': value / max }}` and `transform: translateX(calc((var(--p) - 1) * 100%))`. `scaleX` is wrong here
  because it squashes the rounded ends. Transition on `transform` only. `aria-valuenow` changes at once. Physical
  left-to-right is correct: the document is LTR.
- **Question card change.** Visual requirement: header and bottom bar static, the old card leaves and the new one
  enters with `translateX` plus `opacity`, direction by forward or back. `key={sc.i}` stays the source of truth for
  «which card»; the animation never decides state. Mechanism is an engineering choice, one for every screen change,
  written in `DECISIONS.md`:
  - View Transitions API (Chrome 111, Safari 18, Firefox 144; older browsers get the no-animation fallback). The
    dispatch goes inside `flushSync` in the `startViewTransition` callback; the header and bottom bar get their own
    `view-transition-name` so they stay static; taps during the ≈ 250 ms are lost (pointer events go to the
    pseudo-elements); reduced motion is handled in CSS on `::view-transition-*`.
  - A small enter/exit hook: enter with `@starting-style` (Chrome 117, Safari 17.5, Firefox 129; older browsers
    show the new state without the enter motion, which is the accepted fallback), exit per the rules above. The
    leaving card sits on `position: absolute; top: 0; left: 0; width: 100%` (natural height, not `inset: 0`),
    shifted by `translateY(-<scrollTop before the reset>)`, then the scroll resets. The card container has
    `position: relative` and `overflow-x: clip`.
  - Motion library (`AnimatePresence`): ≈ 30 KB more against the `check:dist` budget (360 KB gzip, ≈ 323 used),
    needs `MotionConfig reducedMotion="user"`, uses `element.animate` and `matchMedia` which jsdom lacks. Note the
    budget in `DECISIONS.md` and the check before choosing it.
- **Answer press.** `:active` on the button with `transform: scale(0.98)` at `--motion-fast`; the selected state
  (`aria-pressed`) switches at once, with a short `opacity` or `background-color` transition only on that small
  element. Starting a scroll on a button briefly triggers `:active`; accept the flicker or delay it.
- **Menu.** The drawer slides in with `transform: translateX(-100%) → 0`, the dim layer fades with `opacity`; close
  is the reverse, unmount per the exit rules. The menu renders outside `main`.
- **Expanding block** (a line that opens into details; the accordion, list details, bill lists). A height reveal
  is a layout animation by nature: everything below moves every frame. Make it cheap instead of avoiding it:
  - Wrapper `display: grid; grid-template-rows: 0fr; transition: grid-template-rows var(--motion-base)`; open
    state `grid-template-rows: 1fr`; the single child has `min-height: 0; overflow: hidden`. No measuring of
    `scrollHeight`, no `height: auto` tricks, no `max-height: 999px` (its timing is wrong).
  - The content is mounted while the motion runs: mount before opening (next frame, so the transition sees the
    change), unmount after the collapse per the exit rules. Today's `Accordion` renders children only while open;
    it keeps that for the open state and defers the unmount on close.
  - The chevron rotates with `transform`; the body content fades with `opacity` over the same duration, so a long
    list does not pop in half-drawn.
  - Cost control: keep expanding bodies short on screen (details of one list, a few lines). A long bill list
    (dozens of rows) opens with the grid motion at `--motion-fast` and its rows fade in; if it still drops frames
    on a 4× throttled CPU, that block opens instantly, with a note in `DECISIONS.md`.
  - After opening a block near the bottom of the screen, one-off `scrollIntoView({ block: 'nearest' })` on the
    block (guarded for jsdom), so the details do not open off-screen.
  - Reduced motion: open and close instantly.
  - Not yet: `interpolate-size: allow-keywords` / `calc-size()` (animating `height: auto`) and `::details-content`
    are Chromium-only at the time of writing; revisit when Safari ships them.
- **Loading screen** (wanted by the customer; see the guideline below). Today it is the Suspense fallback in
  `main.tsx` while the app chunk with the bundled data downloads (`DECISIONS.md` C2). Project specifics: the
  screen renders before `App` exists, so it is entry-chunk only, CSS only, no data import, no library; its frame
  is the app's frame (shell rows or today's `.app` column) so nothing shifts on handover; the indicator is the
  quiz's own progress track with a sliding segment (`translateX` keyframes) or a spinner (`rotate`), whichever
  Figma shows; the text is `S.loading`; a failed chunk load (offline, deploy in between) shows `S.loadError` with
  a reload button through an error boundary around `Suspense`, never a blank page. If bill lists are ever
  fetched after Start (C2 option а), the same indicator is reused inside that screen.

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

Do: pick one scroll model and keep it pure; size full-height things with `svh` on window-scrolled pages; keep
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
  screen fades in with `opacity` over `--motion-fast`. If the loader's text or hero moves when the app mounts,
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
2. Styles without a media query are the phone styles (360–430 px). The only desktop behaviour is centring the column;
   no desktop breakpoints.
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
Exit code 1 (no match) is clean; exit code 2 means the command itself is wrong. Works with BSD, GNU and the
Claude Code grep.

## If an input ever appears

iOS zooms when an input's font is under 16 px, and the keyboard moves the visual viewport, not the layout one, so
the bottom bar ends up behind it. Recipe: listen to `window.visualViewport` `resize` and `scroll` (passive), set
`--kb` to `max(0, innerHeight - vv.height - vv.offsetTop)` px on `:root`, and give the bar `bottom: var(--kb, 0px)`.
