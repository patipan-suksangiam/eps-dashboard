#!/usr/bin/env python3
"""Hot Jobs = open quotations (Status=Pending) with Chance Expect >= 70%
   AND Expected Order Date within THIS month or NEXT month.
Credentials are passed in (never stored in this file):
    python3 pull_hotjobs_2026.py --user patipan --key xxxxx
Writes RAW_Data/0_EPS_HotJobs_2026.csv and prints a SHORT summary only."""
import argparse, json, hashlib, urllib.parse, urllib.request, datetime, os

CRM_BASE = "https://crm.siamrajpump.com/webservice.php"
_HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(_HERE, "RAW_Data", "0_EPS_HotJobs_2026.csv")
OVERVIEW = os.path.join(_HERE, "RAW_Data", "0_EPS_Overview_2026.csv")

ap = argparse.ArgumentParser()
ap.add_argument("--user", required=True)
ap.add_argument("--key", required=True)
a = ap.parse_args()

today = datetime.date.today()
if today.month == 12:
    this_m, next_m = f"{today.year}-12", f"{today.year+1}-01"
else:
    this_m, next_m = f"{today.year}-{today.month:02d}", f"{today.year}-{today.month+1:02d}"
WINDOW = (this_m, next_m)
print(f"window: {this_m} + {next_m} (chance >= 70%)")

def api(p, m="GET"):
    d = urllib.parse.urlencode(p).encode()
    u = CRM_BASE + (("?" + urllib.parse.urlencode(p)) if m == "GET" else "")
    r = urllib.request.Request(u, data=d if m == "POST" else None, method=m, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(r, timeout=60) as x:
        return json.load(x)

ch = api({"operation": "getchallenge", "username": a.user})
if "result" not in ch:
    raise SystemExit(f"getchallenge failed: {ch}")
tok = ch["result"]["token"]
lg = api({"operation": "login", "username": a.user,
          "accessKey": hashlib.md5((tok + a.key).encode()).hexdigest()}, m="POST")
if not lg.get("success"):
    raise SystemExit(f"login failed: {lg.get('error')}")
sess = lg["result"]["sessionName"]

rows, off, size = [], 0, 100
while True:
    res = api({"operation": "query", "sessionName": sess,
               "query": ("SELECT subject,cf_1063,cf_870,cf_874,hdnGrandTotal FROM Quotes "
                         f"WHERE cf_872='Pending' LIMIT {off}, {size};")})
    b = res.get("result", []) if res.get("success") else []
    if not b:
        break
    rows.extend(b)
    if len(b) < size:
        break
    off += size

def pct(v):
    try:
        return float(str(v).replace('%', '').strip())
    except Exception:
        return 0.0

G, hist = {}, {}
for r in rows:
    g = (r.get("cf_1063") or "?").strip() or "?"
    val = float(r.get("hdnGrandTotal") or 0)
    d = str(r.get("cf_874") or "").strip()
    hist[d[:7] or "blank"] = hist.get(d[:7] or "blank", 0) + 1
    if pct(r.get("cf_870")) >= 70 and d[:7] in WINDOW:
        e = G.setdefault(g, {"n": 0, "v": 0.0})
        e["n"] += 1; e["v"] += val

order = ["A", "B", "C", "D", "PD", "R", "?"]
tn = tv = 0
with open(OUT, "w", encoding="utf-8") as f:
    f.write("group,hot_count,hot_value_m\n")
    for g in order:
        if g not in G:
            continue
        e = G[g]
        f.write(f"{g},{e['n']},{e['v']/1e6:.2f}\n")
        tn += e["n"]; tv += e["v"]
    f.write(f"TOTAL,{tn},{tv/1e6:.2f}\n")

# keep the EPS Overview KPI row in sync (label shows the live window)
import calendar
_mn = lambda ym: calendar.month_abbr[int(ym.split("-")[1])]
_ty = today.year if next_m[:4] == this_m[:4] else f"{today.year}/{next_m[:4]}"
label = f"Hot Jobs (due {_mn(this_m)} & {_mn(next_m)} {_ty})"
try:
    ov = open(OVERVIEW, encoding="utf-8").read().strip().split("\n")
    new = [ov[0]] + [f'FY2026_Hot_Jobs,"{label}",{tv/1e6:.2f},-,M THB,neutral,{tn}']
    for l in ov[1:]:
        if l.startswith("FY2026_Hot_Jobs"):
            continue
        new.append(l)
    open(OVERVIEW, "w", encoding="utf-8").write("\n".join(new) + "\n")
except Exception as e:
    print("overview sync skipped:", e)

print(f"pending quotes scanned : {len(rows)}")
print(f"HOT JOBS in window     : {tn} deals | {tv/1e6:,.2f} M THB")
for g in order:
    if g in G:
        print(f"  {g}: {G[g]['n']} deals | {G[g]['v']/1e6:,.2f} M")
print("date coverage (top):", ", ".join(f"{k}={v}" for k, v in sorted(hist.items(), key=lambda x: -x[1])[:4]))
