"""Download bill texts (DOCX preferred: Hebrew RTL extracts cleanly) and keep the explanatory notes.

Usage: python3 pipeline/bill_texts.py BILL_ID [BILL_ID ...]   -> data/bill_texts/<bill_id>.json
       python3 pipeline/bill_texts.py --file ids.txt
Needs an Israeli IP (fs.knesset.gov.il). Cached: existing files are skipped.

Private bills: notes from the DOCX. Government and committee bills have no DOCX with notes: the notes are taken from the
PDF booklet of the first reading («הצעות חוק הממשלה»), where every page carries the law text on top and, under the
heading «ד ב ר י ה ס ב ר», the notes in two columns (right column first). `text_source` records where the text came from.
"""
import json, os, re, sys, urllib.request, zipfile, io
import pymupdf
from odata4 import fetch_all

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data/bill_texts")
# Prefer the version the plenum discussed first; later stages repeat or replace the notes.
GROUP_ORDER = ["הצעת חוק לדיון מוקדם", "הצעת חוק לקריאה הראשונה", "הצעת חוק לקריאה השנייה והשלישית"]

def docx_text(blob):
    xml = zipfile.ZipFile(io.BytesIO(blob)).read("word/document.xml").decode("utf8")
    paras = re.findall(r"<w:p[ >].*?</w:p>", xml, re.S)
    return "\n".join(t for t in ("".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", p)).strip() for p in paras) if t)

def explanatory_notes(text):
    i = text.find("דברי הסבר")
    return text[i:] if i >= 0 else ""

NOTES_HEADING = "ד ב ר י ה ס ב ר"

TITLE = re.compile(r"(?<![\u05d0-\u05ea])הצעת חוק")

def title_core(name):
    """Distinctive words of a bill name for finding its title in a booklet: the name before the first bracket or comma,
    without «הצעת»/«חוק», plus the amendment number if there is one."""
    core = re.split(r"[(,]", re.sub(r"^(הצעת\s+)?חוק[\s־-]*", "", name), 1)[0]
    num = re.search(r"תיקון מס'?\s*(\d+)", name)
    return [w for w in re.split(r"[\s־-]+", core) if len(w) > 1] + ([num.group(1)] if num else [])

def booklet_notes(blob, name):
    """Notes of one bill from a booklet PDF. Every page: law text on top, notes under the heading «ד ב ר י ה ס ב ר»
    in two columns (right first), footnotes below a short rule. A booklet may hold several bills: titles are blocks with
    «הצעת חוק» in the law-text part of a page; the bill's part runs from its title to the next title.
    Returns (notes, info): info = {"bills_in_booklet": n, "segment": "single" | "matched" | "unmatched"}."""
    doc = pymupdf.open(stream=blob, filetype="pdf")
    pages, titles = [], []
    for pn, page in enumerate(doc):
        blocks = sorted(page.get_text("blocks"), key=lambda b: b[1])
        heads = [b for b in blocks if NOTES_HEADING in b[4]]
        top = heads[0][3] if heads else None
        law = [b for b in blocks if top is None or b[3] <= heads[0][1]]
        for i, b in enumerate(law):
            # page 0 is the cover with the table of contents; «מתפרסמת בזה הצעת חוק» is the booklet preamble
            if pn > 0 and TITLE.search(b[4]) and "מתפרסמ" not in b[4]:
                titles.append((pn, b[1], b[4] + " " + (law[i + 1][4] if i + 1 < len(law) else "")))
        notes = []
        if top is not None:
            rules = [d["rect"].y0 for d in page.get_drawings() if d["rect"].height < 2 and d["rect"].width < page.rect.width / 2]
            bottom = min([y for y in rules if y > top] or [page.rect.height - 40])
            mid = page.rect.width / 2
            body = [b for b in blocks if b[1] >= top and b[3] <= bottom + 1 and NOTES_HEADING not in b[4]]
            for col in (lambda b: b[0] >= mid, lambda b: b[0] < mid):
                notes += [b[4].strip() for b in sorted(filter(col, body), key=lambda b: b[1])]
        pages.append(notes)
    # several title lines of one bill (a title wraps) count once: keep titles on different pages or far apart
    starts = [t for i, t in enumerate(titles) if i == 0 or t[0] != titles[i - 1][0] or t[1] - titles[i - 1][1] > 60]
    if len(starts) <= 1:
        return "\n".join(sum(pages, [])), {"bills_in_booklet": len(starts), "segment": "single"}
    core = title_core(name)
    hit = [i for i, t in enumerate(starts) if all(w in t[2] for w in core)]
    if len(hit) != 1:
        return "\n".join(sum(pages, [])), {"bills_in_booklet": len(starts), "segment": "unmatched"}
    first = starts[hit[0]][0]
    last = starts[hit[0] + 1][0] if hit[0] + 1 < len(starts) else len(pages) - 1
    # a page shared by two bills keeps its notes in both parts: they cannot be split by layout
    return "\n".join(sum(pages[first:last + 1], [])), {"bills_in_booklet": len(starts), "segment": "matched"}

def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "elections-research/0.1"}), timeout=60) as r:
        return r.read()

def fetch_pdf(bill_id, docs, rec, name):
    first = [d for d in docs if d["GroupTypeDesc"] == "הצעת חוק לקריאה הראשונה" and d["FilePath"].lower().endswith(".pdf")]
    for d in first:
        url = d["FilePath"].replace("\\", "/")
        try: notes, info = booklet_notes(get(url), name)
        except Exception as e: rec["error"] = str(e); continue
        if notes:
            rec.update(source=url, group=d["GroupTypeDesc"], notes=notes, text_source="pdf_booklet", booklet=info); return rec
    rec["text_source"] = "none"
    return rec

_names = {}
def bill_name(bill_id):
    import duckdb
    if not _names:
        con = duckdb.connect(os.path.join(ROOT, "knesset.duckdb"), read_only=True)
        _names.update(con.sql("select bill_id, name from bills").fetchall())
    return _names.get(bill_id, "")

def fetch(bill_id):
    path = os.path.join(OUT, f"{bill_id}.json")
    if os.path.exists(path):
        rec = json.load(open(path))
        if rec["notes"] and rec.get("text_source") != "pdf_booklet" or rec.get("text_source") == "none" or "booklet" in rec: return rec
    all_docs = fetch_all("KNS_DocumentBill", filter=f"BillID eq {bill_id}")
    docs = [d for d in all_docs if (d["ApplicationDesc"] or "").upper() in ("DOCX", "DOC") and d["FilePath"].lower().endswith(".docx")]
    docs.sort(key=lambda d: GROUP_ORDER.index(d["GroupTypeDesc"]) if d["GroupTypeDesc"] in GROUP_ORDER else 99)
    rec = {"bill_id": bill_id, "source": None, "group": None, "notes": "", "text_chars": 0}
    for d in docs:
        url = d["FilePath"].replace("\\", "/")
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "elections-research/0.1"}), timeout=60) as r:
                text = docx_text(r.read())
        except Exception as e:
            rec["error"] = str(e); continue
        rec.update(source=url, group=d["GroupTypeDesc"], notes=explanatory_notes(text), text_chars=len(text))
        if rec["notes"]: rec["text_source"] = "docx_notes"; break
    if not rec["notes"]: rec = fetch_pdf(bill_id, all_docs, rec, bill_name(bill_id))
    os.makedirs(OUT, exist_ok=True)
    json.dump(rec, open(path, "w"), ensure_ascii=False)
    return rec

if __name__ == "__main__":
    from concurrent.futures import ThreadPoolExecutor
    ids = [int(x) for x in (open(sys.argv[2]).read().split() if sys.argv[1] == "--file" else sys.argv[1:])]
    # 2 workers: 4 parallel clients trip the Knesset anti-bot layer (HTTP 481) within minutes.
    with ThreadPoolExecutor(2) as ex:
        for n, _ in enumerate(ex.map(fetch, ids), 1):
            if n % 50 == 0 or n == len(ids): print(n, len(ids), file=sys.stderr, flush=True)
