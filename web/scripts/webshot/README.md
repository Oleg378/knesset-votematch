# webshot — screenshots of the site as the customer wants to see them

The customer looks at the site as a **mobile browser**: Safari on iPhone 17 Pro, viewport 402 × 791 with the 62 px status-bar
inset, wrapped in a drawn Safari frame (status bar, bottom address bar) — 402 × 874 at 2× (memory note `show-web-version`,
2026-11-09). Every screenshot sent to the customer is made this way.

## One-time setup
```bash
cd web && npm i --no-save puppeteer-core@24      # not a project dependency; `npm ci` removes it again
cd scripts/webshot && for t in bbox2 crop pair; do swiftc -O -o /tmp/$t $t.swift; done   # measuring tools (macOS)
npm run dev                                       # the dev server on 127.0.0.1:5173 (the scripts read it)
```
Google Chrome must be at `/Applications/Google Chrome.app`.

## Scripts
| Script | What |
|---|---|
| `shot-safari.cjs <height> <topInset> <bottomInset> <out.png>` | Home at 402 × height with the insets; prints `overflow` (page − window), the header / steps / actions boxes, `data-below`. The web version: `791 62 0`; the full phone: `874 62 34`. `EXTRA_CSS='…'` injects a style for a what-if render. |
| `shot-url.cjs <url> <out.png> [1]` | Any page (e.g. `/how-it-works`); `1` scrolls to the end first. Prints the footer boxes. `EXTRA_CSS` as above. |
| `flow-shots.cjs <dir>` | Drives the quiz: writes `p-home`, `p-question`, `p-tradeoff`, `p-results-top`, `p-results` (end). |
| `webframe.sh <page.png> <out.png>` | Wraps a 402 × 791 @2× page screenshot in the Safari frame (`webframe.html`). |
| `bbox2.swift <png> <scale> <x0> <y0> <x1> <y1> [label]` | Bounding boxes (in CSS px) of dark text, accent-blue, faint grey and light-tint pixels inside a rect — how the left edges and gaps were measured «по буквам». |
| `crop.swift <in> <out> <x> <y> <w> <h>` · `pair.swift <left> <right> <out>` | Crop in device pixels; two images side by side. |

Known quirk: puppeteer's `browser.close()` sometimes hangs in `headless: 'shell'`; the scripts exit on a 60 s timer after the
screenshot is written (`shot-url.cjs`). Kill leftovers with `pkill -9 -f "headless=shell"`.
