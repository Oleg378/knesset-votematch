"""Budget packages (SU 23a): label second-reading votes on sections of the 8 omnibus laws with the current scheme.

Per vote «סעיף N» / «סעיפים N–M»:
  - section text: the unofficial DOCX of the final law (raw/package_texts/lsh_<bill>.docx); sections are the paragraphs
    «N.» numbered consecutively (numbers inside quoted amendments break the sequence and are skipped);
  - notes: the 2nd/3rd-reading booklet has none, so the notes of the first reading (raw/bill_texts/<bill>.json) are
    cut into windows; the window most similar to the section text (TF-IDF, cosine) with the 1,000 characters before it,
    then the next most similar windows, up to 3,000 characters;
    the similarity of the best window and its margin over the runner-up are kept for the spot check;
  - Jev input: title = package name — chapter — section headings; notes = the matched windows; section text (3,000 chars).
Reservations (הסתייגות) and votes whose sections are not in the final text are skipped and listed.

Usage: python3 pipeline/labeling/jev_packages.py build          -> data/directions/labels/packages_input.jsonl (no Jev)
       python3 pipeline/labeling/jev_packages.py label [N]      -> data/directions/labels/packages.jsonl (resumable; N = first N only)
       python3 pipeline/labeling/jev_packages.py whole          -> data/directions/labels/packages_whole.jsonl
Jev labels of sections were rejected after the spot check (SU 23a); sections are labeled by an Opus agent
(local/jef/directions/pkg_agent/ -> labels/packages_agent.jsonl). «whole» (customer decision B, 2026-10-13): topics of the votes on
a whole package (first and third reading) = the main topics of its sections; the sign is the common sign of that topic
over the sections where it is main («?» ignored); if the sections disagree, the sign is unknown.
"""
import asyncio, json, os, re, sys
import duckdb
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typesafe_sdk import AsyncTypeSafeClient
from bill_texts import docx_text
from jef_run import ROOT, USD_PER_INPUT_TOKEN, load_env
import jev_directions_test as j
import jev_label as jl

PACKAGES = ["2161820", "2161821", "2203821", "2203827", "2224904", "1046680", "1046681"]
# 2025: the programme (2224906) and the efficiency law (2224904) were merged into one law (2224904,
# «חוק להשגת יעדי התקציב וליישום המדיניות הכלכלית לשנת התקציב 2025»); its notes are those of both first readings
NOTES_FROM = {"2224904": ["2224904", "2224906"]}
TEXTS = os.path.join(ROOT, "raw/package_texts")
OUT = os.path.join(ROOT, "data/directions/labels")
CHARS, WINDOW, STEP = 3000, 1000, 500
CHAPTER = re.compile(r"^פרק [א-ת]{1,2}[׳'\"]?[א-ת]?\s*[:–-]")

def sections(bill):
    lines = docx_text(open(os.path.join(TEXTS, f"lsh_{bill}.docx"), "rb").read()).split("\n")
    out, cur, chap = {}, 0, ""
    for i, l in enumerate(lines):
        s = l.strip()
        m = re.match(r"^(\d+)\.$", s)
        if m and int(m.group(1)) == cur + 1:
            cur += 1
            out[cur] = {"chapter": chap, "head": lines[i - 1].strip(), "text": []}
            continue
        if CHAPTER.match(s) and len(s) < 120: chap = s
        if cur: out[cur]["text"].append(l)
    return lines[0].strip().rstrip("*"), out

def numbers(subject):
    s = subject.replace("–", "-").replace("—", "-")
    out = set()
    for a, b in re.findall(r"(\d+)\s*-\s*(\d+)", s):
        a, b = sorted((int(a), int(b))); out |= set(range(a, b + 1))
    out |= {int(x) for x in re.findall(r"(?<![\d(])(\d+)(?![\d)])", re.sub(r"\d+\s*-\s*\d+", "", s))}
    return sorted(out)

def windows(notes):
    return [notes[i:i + WINDOW] for i in range(0, max(1, len(notes) - WINDOW // 2), STEP)]

def build():
    con = duckdb.connect(os.path.join(ROOT, "knesset.duckdb"), read_only=True)
    rows, skipped = [], []
    for bill in PACKAGES:
        title, sec = sections(bill)
        notes = "\n".join(json.load(open(os.path.join(ROOT, f"raw/bill_texts/{b}.json")))["notes"] for b in NOTES_FROM.get(bill, [bill]))
        win = windows(notes)
        votes = con.sql(f"select vote_id, subject from votes where bill_id = {bill} and stage = 'second' order by vote_ts").fetchall()
        items = []
        for vid, sub in votes:
            n = numbers(sub or "")
            if "הסתייגות" in (sub or "") or not n or not all(x in sec for x in n):
                skipped.append({"package": bill, "vote_id": vid, "subject": sub}); continue
            chapters = list(dict.fromkeys(sec[x]["chapter"] for x in n if sec[x]["chapter"]))
            heads = list(dict.fromkeys(sec[x]["head"] for x in n))
            text = "\n".join(f"{x}. {sec[x]['head']}\n" + "\n".join(sec[x]["text"]) for x in n)
            items.append({"package": bill, "vote_id": vid, "subject": sub, "sections": n, "chapters": chapters,
                          "title": " — ".join([title] + chapters + heads)[:600], "section_text": text})
        vec = TfidfVectorizer(token_pattern=r"[א-ת]{2,}|\d{2,}", sublinear_tf=True).fit(win + [x["section_text"] for x in items])
        W = vec.transform(win)
        for x in items:
            sim = cosine_similarity(vec.transform([x["section_text"]]), W)[0]
            order = sim.argsort()[::-1]
            # the best window together with the 1,000 characters before it (a chapter's «כללי» purpose usually precedes
            # the paragraph-by-paragraph notes), then the next best windows
            k0 = int(order[0])
            picked, used = [notes[max(0, k0 * STEP - WINDOW): k0 * STEP + WINDOW]], [k0, k0 - 1, k0 - 2]
            for k in order[1:]:
                if len("\n…\n".join(picked)) >= CHARS: break
                if any(abs(k - u) < WINDOW // STEP for u in used): continue
                picked.append(win[k]); used.append(int(k))
            x["notes"] = "\n…\n".join(picked)[:CHARS]
            x["match"] = {"best": round(float(sim[order[0]]), 3), "second_window": round(float(sim[order[1]]), 3), "windows": used}
            rows.append(x)
    with open(os.path.join(OUT, "packages_input.jsonl"), "w") as f:
        for x in rows: f.write(json.dumps(x, ensure_ascii=False) + "\n")
    json.dump(skipped, open(os.path.join(OUT, "packages_skipped.json"), "w"), ensure_ascii=False, indent=1)
    print(f"{len(rows)} votes, {len(skipped)} skipped", file=sys.stderr)

async def label(limit=None):
    load_env()
    dirs = {str(d["n"]): d for d in j.directions_final()}
    rows = [json.loads(l) for l in open(os.path.join(OUT, "packages_input.jsonl"))][:limit]
    path = os.path.join(OUT, "packages.jsonl")
    done = {json.loads(l)["vote_id"] for l in open(path)} if os.path.exists(path) else set()
    tok = 0
    async with AsyncTypeSafeClient(model="jev-latest") as client:
        with open(path, "a") as out:
            for x in rows:
                if x["vote_id"] in done: continue
                st = {"bill_title_hebrew": x["title"], "bill_type": "government",
                      "explanatory_notes_hebrew": x["notes"], "law_section_text_hebrew": x["section_text"][:CHARS]}
                jl.state = lambda b, st=st: (st, True)
                rec = await jl.label(client, {"bill_id": x["package"]}, dirs)
                rec = {"vote_id": x["vote_id"], "package": x["package"], "subject": x["subject"], "sections": x["sections"],
                       "match": x["match"], **{k: v for k, v in rec.items() if k not in ("bill_id", "has_notes")}}
                out.write(json.dumps(rec, ensure_ascii=False) + "\n"); out.flush()
                tok += rec["tokens"]
    print(json.dumps({"tokens": tok, "usd": round(tok * USD_PER_INPUT_TOKEN, 4)}))

# the 2025 programme (2224906) had its own first reading and was then merged into 2224904
WHOLE_FROM = {"2224906": "2224904"}

def whole():
    con = duckdb.connect(os.path.join(ROOT, "knesset.duckdb"), read_only=True)
    secs = [json.loads(l) for l in open(os.path.join(OUT, "packages_agent.jsonl"))]
    out = []
    for bill in PACKAGES + list(WHOLE_FROM):
        src = WHOLE_FROM.get(bill, bill)
        mine = [x for x in secs if x["package"] == src]
        signs, count = {}, {}
        for x in mine:
            for m in x["main"]:
                count[m["n"]] = count.get(m["n"], 0) + 1
                if m["sign"] in ("+", "−"): signs.setdefault(m["n"], set()).add(m["sign"])
        main = [{"n": n, "sign": next(iter(signs[n])) if len(signs.get(n, ())) == 1 else None, "sections_main": c}
                for n, c in sorted(count.items(), key=lambda kv: -kv[1])]
        # kind = 'bill' only: one third-reading vote (2161821) is classified as a confidence vote in vote_attrs
        votes = con.sql(f"select vote_id, stage from vote_attrs where bill_id = {bill} and kind = 'bill' and stage in ('first', 'third') order by vote_date, vote_id").fetchall()
        out.append({"bill_id": bill, "topics_from": src, "votes": [{"vote_id": v, "stage": st} for v, st in votes],
                    "section_votes": len(mine), "technical_sections": sum(x["technical"] for x in mine), "main": main})
    with open(os.path.join(OUT, "packages_whole.jsonl"), "w") as f:
        for x in out: f.write(json.dumps(x, ensure_ascii=False) + "\n")
    for x in out:
        print(x["bill_id"], len(x["votes"]), "votes,", len(x["main"]), "topics, sign unknown", sum(m["sign"] is None for m in x["main"]), file=sys.stderr)

if __name__ == "__main__":
    if sys.argv[1] == "build": build()
    elif sys.argv[1] == "whole": whole()
    else: asyncio.run(label(int(sys.argv[2]) if len(sys.argv) > 2 else None))
