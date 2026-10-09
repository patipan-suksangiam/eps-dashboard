#!/usr/bin/env python3
"""Pull the CRM fields the Group Overview pages need (Comment 20260924).

Why: the current 2_Quote_Data.csv has blank status -> no win rate possible, and
3_SO_Data.csv has blank delivery_date/sales_id -> no delivery-time view.

Writes:
  RAW_Data/2_Quote_Data.csv   (+ status=cf_872, probability_pct=cf_870, group_code=cf_1063,
                                  expected_order_date=cf_874)
  RAW_Data/3_SO_Data.csv      (delivery_date=duedate, sales_id=assigned_user_id)

Run in the FOREGROUND (long pulls get killed in background runners).
"""
import csv, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import crm_query as cq

RAW = os.path.join(ROOT, "RAW_Data")
PAGE = 100


def paged(sess, select, table, where=""):
    off, seen = 0, set()
    while True:
        q = "SELECT %s FROM %s%s LIMIT %d, %d;" % (
            select, table, (" WHERE " + where) if where else "", off, PAGE)
        res = cq.api({"operation": "query", "sessionName": sess, "query": q})
        if not res.get("success"):
            sys.exit("query failed: %s" % res.get("error"))
        batch = res.get("result", [])
        if not batch:
            break
        for r in batch:
            rid = r.get("id")
            if rid is not None:
                if rid in seen:
                    continue
                seen.add(rid)
            yield r
        off += PAGE


def f(v, default=0.0):
    try:
        return float(v)
    except Exception:
        return default


def pull_quotes(sess):
    cols = ("id,subject,cf_1063,cf_872,cf_870,cf_874,cf_884,hdnGrandTotal,account_id,assigned_user_id")
    out = os.path.join(RAW, "2_Quote_Data.csv")
    n = 0
    with open(out + ".tmp", "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["quote_id", "sales_id", "client_id", "client_name", "equipment_brand",
                    "value_thb", "stage", "probability_pct", "created_date", "aging_days",
                    "status", "lost_reason", "group_code", "expected_order_date"])
        for r in paged(sess, cols, "Quotes"):
            status = (r.get("cf_872") or "").strip()
            w.writerow([r.get("subject", ""), (r.get("assigned_user_id") or "").strip(),
                        (r.get("account_id") or "").strip(), "", "",
                        "%.2f" % f(r.get("hdnGrandTotal")), status,
                        (r.get("cf_870") or "").strip(),
                        (r.get("cf_884") or "").strip(), "",
                        status, "", (r.get("cf_1063") or "").strip(),
                        (r.get("cf_874") or "").strip()])
            n += 1
            if n % 2000 == 0:
                print("  quotes ...", n, flush=True)
    os.replace(out + ".tmp", out)
    print("quotes written: %d" % n, flush=True)


def pull_so(sess):
    cols = "id,salesorder_no,subject,hdnGrandTotal,createdtime,duedate,sostatus,account_id,assigned_user_id"
    out = os.path.join(RAW, "3_SO_Data.csv")
    n = 0
    with open(out + ".tmp", "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["so_id", "quote_ref", "sales_id", "client_id", "client_name",
                    "value_thb", "booking_date", "delivery_date", "status"])
        for r in paged(sess, cols, "SalesOrder", "createdtime >= '2026-01-01'"):
            w.writerow([r.get("salesorder_no", ""), r.get("subject", ""),
                        (r.get("assigned_user_id") or "").strip(),
                        (r.get("account_id") or "").strip(), "",
                        "%.2f" % f(r.get("hdnGrandTotal")),
                        (r.get("createdtime") or "").strip(),
                        (r.get("duedate") or "").strip(),
                        (r.get("sostatus") or "").strip()])
            n += 1
    os.replace(out + ".tmp", out)
    print("SO written: %d" % n, flush=True)


def main():
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    u, k = cq.creds()
    sess = cq.login(u, k)
    t0 = time.time()
    if what in ("quotes", "all"):
        pull_quotes(sess)
    if what in ("so", "all"):
        pull_so(sess)
    print("done in %.0fs" % (time.time() - t0), flush=True)


if __name__ == "__main__":
    main()
