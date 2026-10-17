# Desktop background — variant L (saved 2026-10-17; not in the code — rolled back to C)

Card as in variant C (white, radius 32, 32 px from the window top and bottom, soft shadow, menu inside the card); the
backdrop is variant L: soft brand blobs in the corners under a «parliament» print. Screenshot: `desktop-L.png`.

Print asset: `src/assets/hero-pattern.svg` = `src/assets/figma/hero.svg` with the «your seat» highlight removed: the
solid blue dot «Your seat» (r 4.8) and its lighter halo (Seat_29/30, Seat_51/52, Seat_77/78 at half their ring's
opacity) all get the normal opacity of their ring (0.28 / 0.18 / 0.1, r 3). Every ring is even — no dot, no hole, no
light spot.

## How to restore
Card tokens and the `.app` / `.menu` desktop rules are the same as in `desktop-C.md`. On top of them:

### `src/styles/tokens.css` — after `--shadow-desktop`
```css
  --desktop-bg: #eef2fb; /* backdrop base */
  --desktop-veil: rgba(238, 242, 251, 0.45); /* softens the print */
  --desktop-print-size: 220px; /* print tile; rows offset by half */
  --desktop-blob-blue: rgba(0, 56, 184, 0.2); /* Brand / Primary */
  --desktop-blob-blue-soft: rgba(0, 56, 184, 0.16);
  --desktop-blob-light: rgba(179, 195, 236, 0.9); /* Brand / Disabled */
  --desktop-blob-light-soft: rgba(179, 195, 236, 0.8);
```

### `src/styles/app.css` — the `body` rule inside the first `@media (min-width: 560px)`
```css
  body {
    background:
      linear-gradient(var(--desktop-veil), var(--desktop-veil)),
      url('../assets/hero-pattern.svg') 0 0 / var(--desktop-print-size) var(--desktop-print-size),
      url('../assets/hero-pattern.svg') calc(var(--desktop-print-size) / 2) calc(var(--desktop-print-size) / 2) /
        var(--desktop-print-size) var(--desktop-print-size),
      radial-gradient(40% 50% at 12% 18%, var(--desktop-blob-blue), transparent 70%),
      radial-gradient(35% 45% at 88% 80%, var(--desktop-blob-blue-soft), transparent 70%),
      radial-gradient(30% 40% at 80% 12%, var(--desktop-blob-light), transparent 70%),
      radial-gradient(35% 40% at 20% 88%, var(--desktop-blob-light-soft), transparent 70%),
      var(--desktop-bg);
    background-attachment: fixed; /* blobs stay put on long screens instead of stretching with the page */
  }
```
