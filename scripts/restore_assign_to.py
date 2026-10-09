#!/usr/bin/env python3
"""Restore only the "Assign To" (assigned_user_id) of the quotes that
scripts/close_old_quotes.py reassigned to 19x47 on 2026-09-28.

Reads CRM_AssignTo_Review_20261006.csv (rows flagged suspect_reassigned = YES) and
writes back the account owner's user id, using the Web Service `revise` operation so
that ONLY assigned_user_id is sent — status (cf_872) and every other field the CRM
admins are editing stay untouched.

Usage:
    python3 scripts/restore_assign_to.py                 # dry run (default)
    python3 scripts/restore_assign_to.py --apply --limit 1   # single-record check
    python3 scripts/restore_assign_to.py --apply         # full restore, batched

Every run appends to CRM_AssignTo_Restore_log_<timestamp>.csv with the owner seen
before the write, the owner written, and the owner read back afterwards.
"""
import argparse
import csv
import datetime
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import crm_query as cq  # noqa: E402

REVIEW_CSV = os.path.join(BASE_DIR, "CRM_AssignTo_Review_20261006.csv")
BAD_OWNER = "19x47"          # Patipan Suksangiam — the owner written by the buggy script
BATCH = 40                   # records per round; re-run until nothing is left


def review_rows():
    with open(REVIEW_CSV, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    return [r for r in rows if (r.get("suspect_reassigned") or "").strip() == "YES"]


def audit_rows(path):
    """Rows from scripts/audit_assign_to_2026.py --csv, i.e. everything still on 19x47."""
    with open(path, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def retrieve(sess, quote_id):
    res = cq.api({"operation": "retrieve", "sessionName": sess, "id": quote_id})
    return res.get("result") if res.get("success") else None


def revise_owner(sess, quote_id, owner_id):
    """Send ONLY assigned_user_id — never status, never other fields."""
    element = json.dumps({"id": quote_id, "assigned_user_id": owner_id})
    return cq.api({"operation": "revise", "sessionName": sess, "element": element},
                  method="POST")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="write to the CRM (default: dry run)")
    ap.add_argument("--limit", type=int, default=0, help="stop after N records")
    ap.add_argument("--owner", default="", help="force one target owner id (default: account owner)")
    ap.add_argument("--audit-csv", default="", help="input from audit_assign_to_2026.py --csv")
    ap.add_argument("--include", action="append", default=[],
                    help="audit verdicts to act on (repeatable), e.g. restore")
    args = ap.parse_args()

    if args.audit_csv:
        rows = audit_rows(args.audit_csv)
        keep = set(args.include) or {"restore"}
        todo = [(r["quote_id"], (args.owner or r["account_owner_id"]).strip(), r)
                for r in rows if r.get("verdict", "").split(":")[0] in keep]
    else:
        rows = review_rows()
        todo = []
        for r in rows:
            target = args.owner or (r.get("account_owner_id") or "").strip()
            if not target or target == BAD_OWNER:
                continue
            todo.append((r["quote_id"], target, r))
    if args.limit:
        todo = todo[:args.limit]

    print("records in review list (YES): %d | to restore: %d | mode: %s"
          % (len(rows), len(todo), "APPLY" if args.apply else "DRY RUN"), flush=True)
    if not args.apply:
        by_owner = {}
        for _, target, _ in todo:
            by_owner[target] = by_owner.get(target, 0) + 1
        for owner, n in sorted(by_owner.items(), key=lambda x: -x[1]):
            print("   -> %s : %d quotes" % (owner, n), flush=True)
        print("dry run only — nothing written. add --apply to write.", flush=True)
        return

    user, key = cq.creds()
    sess = cq.login(user, key)
    print("login ok as:", user, flush=True)

    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = os.path.join(BASE_DIR, "CRM_AssignTo_Restore_log_%s.csv" % stamp)
    log = open(log_path, "w", newline="", encoding="utf-8-sig")
    wr = csv.writer(log)
    wr.writerow(["quote_id", "subject", "status_before", "owner_before",
                 "owner_written", "owner_after", "result"])

    done = skipped = failed = 0
    for i, (quote_id, target, row) in enumerate(todo, 1):
        rec = retrieve(sess, quote_id)
        if not rec:
            wr.writerow([quote_id, row.get("subject", ""), "", "", target, "", "retrieve_failed"])
            failed += 1
            continue
        owner_before = rec.get("assigned_user_id", "")
        status_before = rec.get("cf_872", "")
        if owner_before != BAD_OWNER:
            wr.writerow([quote_id, row.get("subject", ""), status_before, owner_before,
                         "", owner_before, "skipped_owner_already_changed"])
            skipped += 1
            continue
        res = revise_owner(sess, quote_id, target)
        if not res.get("success"):
            wr.writerow([quote_id, row.get("subject", ""), status_before, owner_before,
                         target, "", "revise_failed: %s" % (res.get("error") or "")[:120]])
            failed += 1
            if failed <= 5:
                print("   FAIL", quote_id, res.get("error"), flush=True)
            continue
        check = retrieve(sess, quote_id) or {}
        after = check.get("assigned_user_id", "")
        status_after = check.get("cf_872", "")
        ok = (after == target) and (status_after == status_before)
        wr.writerow([quote_id, row.get("subject", ""), status_before, owner_before,
                     target, after, "ok" if ok else "verify_mismatch"])
        done += 1 if ok else 0
        failed += 0 if ok else 1
        log.flush()
        if i % 10 == 0:
            print("   %d/%d  ok=%d skipped=%d failed=%d" % (i, len(todo), done, skipped, failed),
                  flush=True)
        time.sleep(0.15)

    log.close()
    print("DONE. ok=%d skipped=%d failed=%d | log: %s" % (done, skipped, failed, log_path), flush=True)


if __name__ == "__main__":
    main()
