#!/usr/bin/env python3
"""Pull real CRM data into RAW_Data/*.csv for the EPS Dashboard.

Sub-commands:
    accounts  -> RAW_Data/9_Client_Master.csv      (+ /tmp/acc_map.json for joins)
    visits    -> RAW_Data/4_Visit_Report.csv       (Events in a given --year)
    owners    -> RAW_Data/1_CRM_Sales_Person.csv   (distinct record owners, names TBD)

Credentials come from _CORE_Private/crm_credentials.json.
Always run in the FOREGROUND (background runners have killed long pulls).
"""
import argparse, csv, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import crm_query as cq  # noqa: E402

RAW = os.path.join(ROOT, "RAW_Data")
PAGE = 100


def paged(sess, select, table, where=""):
    """Yield rows using LIMIT offset,100.

    This vtiger has no ORDER BY, so a page can legitimately come back SHORT
    (e.g. 99 rows) without being the last page. Never stop on a short page:
    keep going until an empty batch. Rows are de-duplicated by `id` because
    the unstable ordering can repeat a row across pages.
    """
    off = 0
    seen = set()
    while True:
        q = "SELECT %s FROM %s%s LIMIT %d, %d;" % (
            select, table, (" WHERE " + where) if where else "", off, PAGE)
        res = cq.api({"operation": "query", "sessionName": sess, "query": q})
        if not res.get("success"):
            sys.exit("query failed: %s" % json.dumps(res.get("error"), ensure_ascii=False))
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


def do_accounts(sess):
    rows = list(paged(sess,
        "id,accountname,industry,phone,email1,bill_street,bill_city,bill_state,bill_code,"
        "ship_city,assigned_user_id,rating,source,annual_revenue,employees,website",
        "Accounts"))
    acc_map = {}
    out = os.path.join(RAW, "9_Client_Master.csv")
    with open(out, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["client_id", "company_name", "industry_group", "address",
                    "contact_person", "phone", "email", "status",
                    "owner_id", "annual_revenue", "employees", "source", "website"])
        for r in rows:
            cid = r.get("id", "")
            name = (r.get("accountname") or "").strip()
            acc_map[cid] = name
            addr = " ".join(x for x in [
                (r.get("bill_street") or "").strip(),
                (r.get("bill_city") or "").strip(),
                (r.get("bill_state") or "").strip(),
                (r.get("bill_code") or "").strip()] if x)
            w.writerow([cid, name, (r.get("industry") or "").strip(), addr, "",
                        (r.get("phone") or "").strip(), (r.get("email1") or "").strip(),
                        (r.get("rating") or "").strip(), (r.get("assigned_user_id") or "").strip(),
                        r.get("annual_revenue", ""), r.get("employees", ""),
                        (r.get("source") or "").strip(), (r.get("website") or "").strip()])
    acc_map_path = os.path.join(ROOT, "_CORE_Private", "acc_map.json")
    json.dump(acc_map, open(acc_map_path, "w", encoding="utf-8"), ensure_ascii=False)
    print("accounts written: %d -> %s" % (len(rows), out))
    return acc_map


def do_visits(sess, year, acc_map):
    where = ("date_start >= '%d-01-01' AND date_start < '%d-01-01' AND "
             "activitytype IN ('Meeting','Online Meeting','Call','Mobile Call')" % (year, year + 1))
    rows = list(paged(sess,
        "id,subject,activitytype,eventstatus,date_start,time_start,due_date,time_end,"
        "parent_id,assigned_user_id,contact_id,location,description", "Events", where))
    out = os.path.join(RAW, "4_Visit_Report.csv")
    with open(out, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["visit_id", "sales_id", "client_id", "client_name", "visit_date",
                    "visit_type", "objective", "outcome", "next_action_date"])
        for r in rows:
            pid = (r.get("parent_id") or "").strip()
            w.writerow([r.get("id", ""), (r.get("assigned_user_id") or "").strip(),
                        pid, acc_map.get(pid, ""),
                        ((r.get("date_start") or "") + " " + (r.get("time_start") or "")).strip(),
                        (r.get("activitytype") or "").strip(),
                        (r.get("subject") or "").strip(),
                        (r.get("eventstatus") or "").strip(),
                        (r.get("due_date") or "").strip()])
    print("visits written: %d -> %s" % (len(rows), out))


def do_owners(sess):
    so_owners, q_owners = {}, {}
    for r in paged(sess, "assigned_user_id", "SalesOrder"):
        oid = (r.get("assigned_user_id") or "").strip()
        so_owners[oid] = so_owners.get(oid, 0) + 1
    for r in paged(sess, "assigned_user_id", "Quotes"):
        oid = (r.get("assigned_user_id") or "").strip()
        q_owners[oid] = q_owners.get(oid, 0) + 1
    all_ids = sorted(set(list(so_owners) + list(q_owners)))
    out = os.path.join(RAW, "1_CRM_Sales_Person.csv")
    with open(out, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["emp_id", "name", "role_tier", "territory",
                    "monthly_target_thb", "phone", "email", "status",
                    "so_count", "quote_count"])
        for oid in all_ids:
            w.writerow([oid, "", "", "", "", "", "", "active",
                        so_owners.get(oid, 0), q_owners.get(oid, 0)])
    print("owners written: %d -> %s" % (len(all_ids), out))
    print("owner ids:", ", ".join(all_ids))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["accounts", "visits", "owners", "all"])
    ap.add_argument("--year", type=int, default=2026)
    a = ap.parse_args()
    u, k = cq.creds()
    sess = cq.login(u, k)
    acc_map = {}
    if a.what in ("accounts", "all"):
        acc_map = do_accounts(sess)
    if a.what in ("visits", "all"):
        if not acc_map and os.path.exists("/tmp/acc_map.json"):
            acc_map = json.load(open("/tmp/acc_map.json", encoding="utf-8"))
        do_visits(sess, a.year, acc_map)
    if a.what in ("owners", "all"):
        do_owners(sess)


if __name__ == "__main__":
    main()
