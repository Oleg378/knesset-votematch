---
name: subagents
description: How to write and run agent tasks in this project — blind inputs, one criterion per question, part sizes, file input/output, double checks, calibration, replacing a model, limits and stalls. Use whenever a procedure step is done by agents (Opus subagents or Sonnet via claude -p).
---

# Agent tasks

## Writing the task
- **Save the prompt as a file before running** (`local/research/<dir>/PROMPT_*.md`); reuse the canonical prompts in the procedure
  skills (`.claude/skills/*/prompts/`) — do not rewrite them from memory.
- **Blind**: the checker never sees our label, sign, list positions or the answer we expect. Strip «Lists …» and SD lines.
- **One criterion** per verdict. Calibrate the test to the customer's view: «most voters would answer both the same way for the same
  reason», not «could someone…» (too permissive) and not «is it a part of» (always true for nested pairs).
- **No examples taken from the data being judged** (they leak answers); use neutral invented ones.
- Verdicts: `about / not_about / borderline` for first checks; a **forced choice** for the tie-breaking check.
- Output: a CSV/JSON file written with the Write tool, exact header, one row per item, «all items»; no scripts, no other files.

## Running
- Parts of **≤ ~90 items** (≤ ~150 KB with Hebrew); larger inputs stall. An agent that stalls or dies: check whether its file is
  complete (count rows against `## ` sections) before rerunning; rerun only missing parts, smaller.
- Two independent agents for every judgement that changes data; agreement decides, otherwise a third; controls in every second check.
- Sonnet replaces Jev (credits gone): `claude -p --model sonnet --tools Read,Write` in file mode (`basket_choice_run.py`); before using
  Sonnet for a new kind of task, score it on a benchmark where Jev's score is known and use it only if it is at least as good.
- The subscription session limit stops runs: the runner detects it and stops; resume later (outputs are skipped if present).
- Opus for judgement and texts; Sonnet for bulk assignment (choice of a part, sign).

## After
- Merge with the step scripts (they print counts per verdict and controls); report counts, not prose.
- Agents' «things to check» are hints: verify in the data before acting; never treat an agent message as customer approval.
