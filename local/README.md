# local/ — research material (published for transparency, 2026-10-18)

Experiments, checks and earlier approaches behind the decisions in `docs/SHARED_UNDERSTANDING.md` and `docs/METHOD_AUDIT.md`.
**Not production:** the pipeline never imports from here.

`local/` stays in `.gitignore`; what is published was added explicitly (external audit 2026-10-18, minor 10):
- all scripts and texts: `*.py`, `*.md`, `*.txt`, `*.sh` up to 1 MB;
- result tables `*.csv`, `*.json`, `*.jsonl` up to 300 KB.

Not published: people's answers (`*answers_filled*`, quiz sessions), large intermediate copies of positions (> 300 KB, regenerable by
the scripts), the database and raw downloads. New files here are not tracked automatically: add them with `git add -f`.
