# web/ — local rules

React + Vite + TypeScript, static SPA (no server, no Next.js). Spec: `SPEC.md`. Pending decisions: `DECISIONS.md`.
Requests to the data side: `DATA_REQUESTS.md`. Data: `../export/quiz_data.v1.json` only.

- `src/engine/` — pure TypeScript port of `pipeline/quiz_match.py` + explanations of `pipeline/quiz_report.py`. No React,
  no DOM. Python is the reference: `../export/golden.v1.json` must pass (`npm test`).
- `src/state/` — `useReducer` state machine of the flow; reducer is pure and tested.
- `src/strings.ts` — every UI string (English). Explanation templates live here too and must reproduce the golden lines.
- `src/components/`, `src/screens/` — mobile first (360–430 px). No desktop layout yet: centered column, max ≈ 480 px.
- `src/styles/tokens.css` — the only place for colors, type scale, spacing, radii (from Figma).
- Hebrew bill titles: `dir="auto"`, never translated. List names: `name_en` as given.
- Never show: coalition/opposition, number of MKs, list logos. Results never go into the URL; no third-party trackers.
- Do not edit `../export/*` by hand; it is produced by `make data`.
- Commands: `npm run dev`, `npm test`, `npm run build`, `npm run typecheck`.
- Keep tasks small: one screen or one component plus its test.
