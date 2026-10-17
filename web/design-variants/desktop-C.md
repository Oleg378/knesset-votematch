# Desktop background — variant C (saved 2026-10-17; in the code)

Customer's chosen variant, saved so it can be restored exactly («откати к варианту C»). Screenshot: `desktop-C.png`.

Window ≥ 560 px: page background Brand / Tint 10 %, the 480 px column is a white card (radius 32, 32 px from the window
top and bottom, soft shadow), the menu opens inside the card. Phones are not affected.

## How to restore
Replace whatever desktop variant is in the code with the three blocks below (same places). Coming back from variant L
(`desktop-L.md`): put back the `body` rule from block 2 and delete the `--desktop-bg`, `--desktop-veil`, `--desktop-print-size`,
`--desktop-blob-*` tokens (`src/assets/hero-pattern.svg` can stay — unused). Then check at 1440×900,
960×460 (scroll to the end) and 402×874 (must be unchanged).

### 1. `src/styles/tokens.css` — the end of the file: last tokens of `:root` (after `--menu-item-height`) and the media block after it
```css
  /* desktop (window ≥ 560 px): the column becomes a card on the brand tint (customer 2026-10-17, variant C; not in Figma) */
  --desktop-gap: 32px; /* card margin from the window top and bottom */
  --radius-desktop: 32px; /* card corners */
  --shadow-desktop: 0 12px 48px rgba(0, 56, 184, 0.12);
  --desktop-card-height: 812px; /* Figma screen without the status bar (874 − 62): the card keeps the phone proportions */
  --desktop-min-gap: 64px; /* Home in a short or zoomed window: at least this much between the steps and the buttons */
}

/* A window lower than the card with full margins (812 + 2 × 32 = 876 px; most laptops — the browser bars take ~100 px
   of the screen): thinner margins leave more room for the card (customer 2026-10-17, option A). */
@media (min-width: 560px) and (max-height: 875px) {
  :root {
    --desktop-gap: 16px;
  }
}
```

### 2. `src/styles/app.css` — right after the `.app { … }` rule
```css
/* Desktop: the mobile column is a white card on the brand tint, so the window is not empty around it (customer
   2026-10-17, variant C). 560 px = column 480 + room for the background on both sides. Phones are not affected. */
@media (min-width: 560px) {
  body {
    background: linear-gradient(var(--color-accent-soft), var(--color-accent-soft)), var(--color-bg); /* Brand / Tint 10% */
  }

  /* The card keeps the phone proportions (customer 2026-10-17): the Figma screen height, never stretched to a tall
     window (it is centred instead). In a short or zoomed window it shrinks to the window, but Home keeps at least
     --desktop-min-gap above the buttons (end of file); a longer screen simply scrolls. */
  #root {
    min-height: 100dvh;
    display: flex;
    flex-direction: column;
    justify-content: center;
  }

  .app {
    min-height: min(var(--desktop-card-height), calc(100dvh - 2 * var(--desktop-gap)));
    margin-block: var(--desktop-gap);
    background: var(--color-bg);
    border-radius: var(--radius-desktop);
    box-shadow: var(--shadow-desktop);
  }
}
```

### 3. `src/styles/app.css` — at the very end of the file (must come after the `.menu` rules)
```css
/* Desktop (see .app above): the menu opens inside the card, not from the window edge; the dim covers the whole window */
@media (min-width: 560px) {
  .menu {
    /* matches a centred card of --desktop-card-height; a taller card is scrolled, and the menu fills the window */
    inset-block: max(var(--desktop-gap), calc((100dvh - var(--desktop-card-height)) / 2));
    inset-inline-start: calc(50% - var(--column-max) / 2);
    border-start-start-radius: var(--radius-desktop);
    border-end-start-radius: var(--radius-desktop);
  }

  /* Short or zoomed window: the card shrinks, Home keeps --desktop-min-gap (screen gap 16 + this) above the buttons */
  .start .sticky-actions {
    padding-top: calc(var(--desktop-min-gap) - var(--space-4));
  }
}
```

Card sizing (added 2026-10-17, part of C): the card is 812 px (Figma screen without the status bar), centred in a
tall window and never stretched. A window lower than 876 px (most laptops) gets 16 px margins instead of 32; a short or
zoomed window shrinks the card to the window, but Home keeps at least 64 px between the steps and the buttons.
Gap to «Start the quiz»: 158 px at 860 px window height and taller, 132 px at 818 (a typical laptop Safari), 64 px at
700 and lower (the page scrolls a little). Burger and menu close are at the same point in all of them.
