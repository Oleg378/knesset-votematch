"""User-facing texts of the quiz: the hand-edited file export/quiz_texts.json (contract: export/WEB_CONTRACT.md §7).

The Python reference (quiz_report.py explanations, quiz_match.py notes, the terminal quiz) and the web render the same templates,
so a wording is changed in that file only, never in code.

Template language (the TypeScript side implements the same rules):
  {name}            the value; numbers via str() (0.25 stays «0.25»); a value may be a string, e.g. a filled sub-template;
  {name?one|many}   «one» when the value == 1, else «many»;
  an unknown name raises.
"""
import json, os, re
from functools import lru_cache

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "export", "quiz_texts.json")
_TOKEN = re.compile(r"\{(\w+)(?:\?([^|{}]*)\|([^{}]*))?\}")

@lru_cache(maxsize=None)
def load():
    """The parsed export/quiz_texts.json (read once)."""
    with open(PATH, encoding="utf-8") as f:
        return json.load(f)

def fill(template: str, **values) -> str:
    """Fill a template: {name} -> str(value); {name?one|many} -> one if value == 1 else many. Unknown name -> KeyError."""
    def sub(m):
        name, one, many = m.group(1), m.group(2), m.group(3)
        if name not in values: raise KeyError(f"template placeholder {{{name}}} has no value: {template!r}")
        v = values[name]
        if one is not None: return one if v == 1 else many
        return str(v)
    return _TOKEN.sub(sub, template)
