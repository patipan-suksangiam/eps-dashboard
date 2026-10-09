#!/usr/bin/env python3
"""Pull current-year Sales Orders from CRM -> RAW_Data/3_SO_Data.csv
Credentials are passed in, never stored here:
    python3 pull_so_2026.py --user <u> --key <k> [--year 2026]
"""
import argparse, csv, json, hashlib, urllib.parse, urllib.request, datetime, os

CRM_BASE = "https://crm.siamrajpump.com/webservice.php"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE_DIR, "RAW_Data", "3_SO_Data.csv")

ap = argparse.ArgumentParser()
ap.add_argument("--user", required=True)
ap.add_argument("--key", required=True)
ap.add_argument("--year", default="2026")   # ปีที่ dashboard แสดง (อัปเดตเมื่อขึ้นปีใหม่)
a = ap.parse_args()

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
               "query": ("SELECT salesorder_no, subject, hdnGrandTotal, createdtime, sostatus, account_id "
                         f"FROM SalesOrder WHERE createdtime >= '{a.year}-01-01' LIMIT {off}, {size};")})
    b = res.get("result", []) if res.get("success") else []
    if not b:
        break
    rows.extend(b)
    if len(b) < size:
        break
    off += size

total = 0.0
with open(OUT, "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    w.writerow(["so_id", "quote_ref", "sales_id", "client_id", "client_name",
                "value_thb", "booking_date", "delivery_date", "status"])
    for r in rows:
        v = float(r.get("hdnGrandTotal") or 0)
        total += v
        w.writerow([r.get("salesorder_no", ""), r.get("subject", ""), "", r.get("account_id", ""), "",
                    f"{v:.2f}", r.get("createdtime", ""), "", r.get("sostatus", "")])

print(f"year {a.year}: {len(rows)} sales orders | {total/1e6:,.2f} M THB")
