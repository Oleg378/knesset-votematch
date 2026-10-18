"""Minimal client for Knesset OData v2 (verbose JSON). Works only from Israeli IPs."""
import json, re, sys, time, urllib.parse, urllib.request
from datetime import datetime, timezone

BASE = "https://knesset.gov.il/Odata/"
HDR = {"Accept": "application/json;odata=verbose", "User-Agent": "elections-research/0.1"}

def get(url, retries=3):
    for i in range(retries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=HDR), timeout=120) as r:
                return json.load(r)
        except Exception as e:
            if i == retries - 1: raise
            time.sleep(2 * (i + 1))

def build(service, entity, **params):
    q = urllib.parse.urlencode({f"${k}": v for k, v in params.items()}, quote_via=urllib.parse.quote)
    return f"{BASE}{service}/{entity}" + (f"?{q}" if q else "")

def fetch_all(service, entity, verbose=False, **params):
    """Follow __next links; returns list of rows."""
    url, rows = build(service, entity, **params), []
    while url:
        d = get(url)["d"]
        batch = d["results"] if isinstance(d, dict) and "results" in d else d
        rows.extend(batch)
        url = d.get("__next") if isinstance(d, dict) else None
        if verbose: print(len(rows), file=sys.stderr)
    for r in rows: r.pop("__metadata", None)
    return rows

def odate(s):
    """'/Date(1066608000000)/' -> ISO date string."""
    if not s: return None
    ms = int(re.search(r"-?\d+", s).group())
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
