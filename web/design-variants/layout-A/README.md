# Layout — «версия А» (saved 2026-10-17)

Snapshot taken right before the breakpoint system (window size classes) was introduced. The customer named it
«версия А» and may ask to roll back to it («откати к версии А»). Not to be confused with the rejected desktop
background «A» or the margins «option A» — this is the whole layout state.

What it is: card on the brand tint from 560 px wide; card 812 px, centred in tall windows; margins 32 → 16 below 876 px
window height; Home buttons not sticky, at least 64 px above them on desktop; question screens' Back / Next sticky
without a fade.

## Roll back
Copy both files back over the current ones:
```
cp design-variants/layout-A/app.css src/styles/app.css
cp design-variants/layout-A/tokens.css src/styles/tokens.css
```
Only these two files were changed after the snapshot. If other style edits were made later, re-apply them on top.
Then check 1440×900, 1440×818, 1280×620 and the phone emulation 402×874 (insets 62/34).
