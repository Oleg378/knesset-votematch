"""Sonnet replaces Jev for the stage-5 split choice (basket_split_plan.py -> choice_K.json). Same question and rule as the Jev choice
(jev_split.py one_choice) and the benchmark (local/jef/directions/split/check/SONNET_PROMPT.md, Sonnet 27/30 vs Jev 24/30): best candidate,
a second only if nearly as good, empty if none; sign per chosen candidate. One headless `claude -p --model sonnet` call per chunk of 30
names (fresh context, no tools; the data go in the prompt), PAR in parallel; resumable; a chunk with missing ids is retried once.
-> local/research/basket_split/choice_out_K.json
"""
import glob, json, os, re, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = f"{ROOT}/local/research/{os.environ.get('TAG', 'basket_split')}"
PAR = int(os.environ.get("PAR", 6))
INSTR = """Ниже — законопроекты Кнессета (JSON): название и начало пояснительной записки на иврите, широкое направление (parent), к которому законопроект отнесён, и более узкие кандидаты (candidates) с определениями «+» и «−». Направление — величина, которую закон увеличивает («+») или уменьшает («−»).

ЗАДАЧА (для каждого законопроекта независимо)
Законопроект отнесён к широкой теме. Какую из более узких величин (кандидатов) меняет сам законопроект?
1. Выбери кандидата, который лучше всего описывает, что делает законопроект.
2. Второго кандидата добавь, только если он подходит почти так же хорошо, как первый (законопроект существенно меняет обе величины).
3. Если ни один кандидат не описывает то, что делает законопроект, — пустой список.
4. Для каждого выбранного кандидата — знак: «+», если законопроект увеличивает величину (по определению «+»), «−», если уменьшает.

ФОРМАТ ОТВЕТА — только JSON, без пояснений вокруг:
{"items":[{"id":"...","subs":[{"n":"...","sign":"+|−"}],"note":"одна короткая фраза на русском"}]}
В ответе должны быть все законопроекты входа.

ВХОД:
"""
import threading
STOP = threading.Event()   # set when the subscription session limit is hit: the remaining chunks are skipped, rerun later
PROMPT = open(f"{ROOT}/local/jef/directions/split/check/SONNET_PROMPT.md").read()
def run(f):
    """File mode, as the benchmarked subagent (26–27/30 in three runs; the no-tools prompt mode gave 22–25): Sonnet reads the chunk with
    Read and writes the result with Write, same prompt text as SONNET_PROMPT.md with the paths replaced."""
    out = f.replace("choice_", "choice_out_")
    if os.path.exists(out): return f, "skip"
    if STOP.is_set(): return f, "skipped (limit)"
    ids = {x["id"] for x in json.load(open(f))}
    prompt = PROMPT.replace("/Users/oleg/Documents/elections-research/local/jef/directions/split/check/input.json", f) \
                   .replace("/Users/oleg/Documents/elections-research/local/jef/directions/split/check/sonnet_out.json", out) \
                   .replace("30 законопроектов Кнессета", f"{len(ids)} законопроектов Кнессета").replace("все 30 законопроектов", f"все {len(ids)} законопроектов")
    got = set()
    for attempt in (1, 2):
        r = subprocess.run(["claude", "-p", "--model", "sonnet", "--tools", "Read,Write", "--allowedTools", "Read,Write",
                            "--no-session-persistence", "--output-format", "text"], input=prompt, capture_output=True, text=True, timeout=3600)
        try: got = {x["id"] for x in json.load(open(out))["items"]}
        except Exception: got = set()
        if ids <= got: return f, f"ok (attempt {attempt})"
        if "session limit" in r.stdout or "usage limit" in r.stdout: STOP.set(); return f, "LIMIT: " + r.stdout.strip()[:120]
        if os.path.exists(out): os.rename(out, out.replace(".json", f".bad{attempt}.json"))
    open(out.replace(".json", ".failed.txt"), "w").write(r.stdout + "\n---\n" + r.stderr)
    return f, f"FAILED: missing {len(ids - got)}"
files = sorted(glob.glob(f"{B}/choice_[0-9]*.json"), key=lambda p: int(re.search(r"(\d+)\.json$", p).group(1)))
if len(sys.argv) > 1: files = [p for p in files if re.search(r"choice_(\d+)\.json$", p).group(1) in sys.argv[1:]]
with ThreadPoolExecutor(PAR) as ex:
    for f, s in ex.map(run, files): print(os.path.basename(f), s, flush=True)
