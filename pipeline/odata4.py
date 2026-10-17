"""Minimal client for Knesset OData v4 (ParliamentInfo). Works only from Israeli IPs.
Server caps pages at 100 rows and paginates via @odata.nextLink ($skip).
$skip gets linearly slower with depth (page 40 takes ~4 s), so large tables use keyset paging."""
import json, sys, time, urllib.error, urllib.parse, urllib.request

BASE = "https://knesset.gov.il/OdataV4/ParliamentInfo/"
HDR = {"Accept": "application/json", "User-Agent": "elections-research/0.1"}

def build(entity, **params):
    q = urllib.parse.urlencode({f"${k}": v for k, v in params.items()}, quote_via=urllib.parse.quote)
    return BASE + entity + (f"?{q}" if q else "")

def get(url, retries=7):
    """Retries with backoff up to ~2 min: the anti-bot layer answers bursts with HTTP 481 or an HTML page."""
    for i in range(retries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=HDR), timeout=120) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 400 or i == retries - 1: raise
        except Exception:
            if i == retries - 1: raise
        time.sleep(min(2 ** (i + 1), 120))

def fetch_all(entity, progress=False, **params):
    """Follow @odata.nextLink. Always orders by Id: $skip paging without $orderby is unstable
    (rows get duplicated and others skipped between pages)."""
    params.setdefault("orderby", "Id")
    url, rows = build(entity, **params), []
    while url:
        d = get(url)
        rows.extend(d["value"])
        url = d.get("@odata.nextLink")
        if progress and len(rows) % 2000 == 0: print(entity, len(rows), file=sys.stderr)
    return rows

def fetch_keyset(entity, filter=None, key="Id", progress=False):
    """Page by `key gt <last>` ordered by key: constant ~0.5 s/page at any depth."""
    rows, last = [], 0
    while True:
        f = f"{key} gt {last}" + (f" and ({filter})" if filter else "")
        batch = get(build(entity, filter=f, orderby=key, top=100))["value"]
        if not batch: return rows
        rows.extend(batch); last = batch[-1][key]
        if progress and len(rows) % 10000 < 100: print(entity, len(rows), file=sys.stderr)

def count(entity, **params):
    return get(build(entity, count="true", top=0, **params))["@odata.count"]
