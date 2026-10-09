#!/usr/bin/env python3
"""Audit every Quote still owned by 19x47 (Patipan Suksangiam) and work out who
should own each one, so the owner can be restored without guessing.

JOM is not a salesperson: a quote carrying his name is an attribution error. The
target owner is the owner of the customer account, and rows whose target is
uncertain are flagged instead of written.

Uncertain = account owner is also 19x47, is the Administrator user, or is a
service/shared account (Shop EPS, EPC services, marketing, MIS, CRM admin).

Usage:
    python3 scripts/audit_assign_to_2026.py                 # summary to stdout
    python3 scripts/audit_assign_to_2026.py --csv out.csv   # also write the detail
    python3 scripts/audit_assign_to_2026.py --year 2026     # filter by created year
"""
import argparse
import csv
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import crm_query as cq  # noqa: E402
from pull_crm_data import paged  # noqa: E402

OWNER = "19x47"
ADMIN = "19x1"
SHARED = {"19x71": "Shop EPS", "19x58": "EPC Services", "19x25": "Marketing EPS",
          "19x40": "Admin EPC", "19x95": "MIS (Titisorn)", "19x48": "CRM Admin (Udomlak)",
          "19x65": "", "19x53": "", "19x64": "", "19x22": "", "19x36": "", "19x54": ""}

FIELDS = "id, subject, account_id, cf_872, createdtime, modifiedtime, assigned_user_id"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, default=0, help="only quotes created in this year")
    ap.add_argument("--csv", default="", help="write the detail to this CSV")
    args = ap.parse_args()

    user, key = cq.creds()
    sess = cq.login(user, key)
    print("login ok as:", user, flush=True)

    quotes = list(paged(sess, FIELDS, "Quotes", "assigned_user_id = '%s'" % OWNER))
    print("quotes still on %s: %d" % (OWNER, len(quotes)), flush=True)

    acc_ids = sorted({q["account_id"] for q in quotes if q.get("account_id")})
    accounts = {}
    for r in paged(sess, "id, accountname, assigned_user_id", "Accounts"):
        if r["id"] in acc_ids:
            accounts[r["id"]] = r
    print("accounts resolved: %d/%d" % (len(accounts), len(acc_ids)), flush=True)

    rows = []
    for q in quotes:
        acc = accounts.get(q.get("account_id"), {})
        target = (acc.get("assigned_user_id") or "").strip()
        created = (q.get("createdtime") or "")[:10]
        if args.year and not created.startswith(str(args.year)):
            continue
        if not target:
            verdict = "ask_no_account_owner"
        elif target == OWNER:
            verdict = "ask_account_is_jom"
        elif target == ADMIN:
            verdict = "ask_admin_owned_account"
        elif target in SHARED:
            verdict = "ask_shared_account:" + (SHARED[target] or target)
        else:
            verdict = "restore"
        rows.append({
            "quote_id": q["id"], "subject": q.get("subject", ""),
            "status": q.get("cf_872", ""), "created": created,
            "modified": (q.get("modifiedtime") or "")[:19],
            "account_id": q.get("account_id", ""),
            "account_name": acc.get("accountname", ""),
            "account_owner_id": target, "verdict": verdict,
        })

    print("\nrows in scope: %d" % len(rows))
    print("verdict:", Counter(r["verdict"].split(":")[0] for r in rows))
    print("by created year:", Counter(r["created"][:4] for r in rows))
    print("by status:", Counter(r["status"] for r in rows))
    print("\ntarget owner distribution (restore rows):",
          Counter(r["account_owner_id"] for r in rows if r["verdict"] == "restore").most_common(12))
    for r in rows:
        if r["verdict"].startswith("ask"):
            print("   ASK", r["quote_id"], "|", r["created"], "|", r["status"], "|",
                  r["account_name"][:32], "| account owner:", r["account_owner_id"], "|", r["verdict"])

    if args.csv:
        with open(args.csv, "w", newline="", encoding="utf-8-sig") as f:
            wr = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            wr.writeheader()
            wr.writerows(rows)
        print("\nwritten:", args.csv)


if __name__ == "__main__":
    main()
