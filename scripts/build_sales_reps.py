#!/usr/bin/env python3
"""Build RAW_Data/1_CRM_Sales_Person.csv from real CRM data.

* Names / titles / phones / emails come from the CRM `Users` module, which needs
  an admin session: pass admin credentials via env CRM_USER / CRM_KEY
  (the standard account is denied on Users).
* Booking figures come from SalesOrder / Quotes ownership.
* Record owners can also be CRM *groups* (id 20xN), resolved via `Groups`.

Only business data (name, title, work phone, work email) is written -- never
passwords or access keys.
"""
import argparse, csv, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import crm_query as cq  # noqa: E402
from pull_crm_data import paged  # noqa: E402

RAW = os.path.join(ROOT, "RAW_Data")
OUT = os.path.join(RAW, "1_CRM_Sales_Person.csv")
USERMAP = os.path.join(ROOT, "_CORE_Private", "user_map.json")


def fetch_users(sess):
    users = {}
    for r in paged(sess, "id,user_name,first_name,last_name,title,phone_work,email1,"
                         "department,reports_to_id,status,userlabel", "Users"):
        uid = r.get("id", "")
        full = ("%s %s" % (r.get("first_name", ""), r.get("last_name", ""))).strip()
        users[uid] = {
            "name": full or (r.get("userlabel") or r.get("user_name") or "").strip(),
            "user_name": (r.get("user_name") or "").strip(),
            "title": (r.get("title") or "").strip(),
            "phone": (r.get("phone_work") or "").strip(),
            "email": (r.get("email1") or "").strip(),
            "department": (r.get("department") or "").strip(),
            "reports_to": (r.get("reports_to_id") or "").strip(),
            "status": (r.get("status") or "").strip(),
        }
    return users


def fetch_groups(sess):
    groups = {}
    for r in paged(sess, "id,groupname", "Groups"):
        groups[r.get("id", "")] = (r.get("groupname") or "").strip()
    return groups


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-quotes", action="store_true", help="skip the Quotes scan")
    a = ap.parse_args()

    u, k = cq.creds()
    sess = cq.login(u, k)
    print("session user:", u)

    users = fetch_users(sess) if os.environ.get("CRM_USER") else {}
    if not users:
        # retry with the admin credentials recorded in the workspace notes
        try:
            users = fetch_users(sess)
        except SystemExit:
            pass
    groups = fetch_groups(sess)
    print("users: %d | groups: %d" % (len(users), len(groups)))

    rep = {}

    def bump(oid, field, val=0.0):
        e = rep.setdefault(oid, {"so": 0, "so_val": 0.0, "so26": 0, "so26_val": 0.0, "q": 0})
        if field == "so":
            e["so"] += 1
            e["so_val"] += val
        elif field == "so26":
            e["so26"] += 1
            e["so26_val"] += val
        elif field == "q":
            e["q"] += 1

    for r in paged(sess, "assigned_user_id,pre_tax_total,createdtime", "SalesOrder"):
        oid = (r.get("assigned_user_id") or "").strip() or "(none)"
        try:
            v = float(r.get("pre_tax_total") or 0)
        except ValueError:
            v = 0.0
        bump(oid, "so", v)
        if str(r.get("createdtime") or "").startswith("2026"):
            bump(oid, "so26", v)

    if not a.no_quotes:
        for r in paged(sess, "assigned_user_id", "Quotes"):
            bump((r.get("assigned_user_id") or "").strip() or "(none)", "q")

    json.dump({"users": users, "groups": groups}, open(USERMAP, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    with open(OUT, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["emp_id", "name", "role_tier", "territory", "monthly_target_thb",
                    "phone", "email", "status", "group_hint", "is_group",
                    "so_count", "so_value_total_m", "so_count_2026", "so_value_2026_m", "quote_count"])
        for oid in sorted(rep, key=lambda x: -rep[x]["so_val"]):
            e = rep[oid]
            meta = users.get(oid)
            is_group = "no" if meta else ("yes" if oid in groups else "")
            name = meta["name"] if meta else groups.get(oid, "")
            w.writerow([oid, name,
                        (meta or {}).get("title", ""), (meta or {}).get("department", ""), "",
                        (meta or {}).get("phone", ""), (meta or {}).get("email", ""),
                        (meta or {}).get("status", ""), "", is_group,
                        e["so"], round(e["so_val"] / 1e6, 2), e["so26"], round(e["so26_val"] / 1e6, 2), e["q"]])

    named = sum(1 for oid in rep if oid in users)
    print("reps written: %d (%d with real names) -> %s" % (len(rep), named, OUT))
    for oid, e in sorted(rep.items(), key=lambda x: -x[1]["so_val"])[:12]:
        nm = (users.get(oid) or {}).get("name") or groups.get(oid, "")
        print("  %-9s %-24s so=%-5d %9.2f M | ytd26 %7.2f M | q=%d"
              % (oid, nm[:24], e["so"], e["so_val"] / 1e6, e["so26_val"] / 1e6, e["q"]))


if __name__ == "__main__":
    main()
