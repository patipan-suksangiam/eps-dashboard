#!/usr/bin/env python3
"""Thin CRM (vtiger) query helper for the EPS Dashboard ETL.

Reads credentials from _CORE_Private/crm_credentials.json (never prints them).
Usage:
    python3 scripts/crm_query.py "SELECT count(*) FROM Accounts;"
    python3 scripts/crm_query.py --describe Accounts
"""
import argparse, hashlib, json, os, sys, urllib.parse, urllib.request

BASE = "https://crm.siamrajpump.com/webservice.php"
HERE = os.path.dirname(os.path.abspath(__file__))
CRED_FILE = os.path.join(os.path.dirname(HERE), "_CORE_Private", "crm_credentials.json")


def creds():
    u, k = os.environ.get("CRM_USER"), os.environ.get("CRM_KEY")
    if u and k:
        return u, k
    d = json.load(open(CRED_FILE, encoding="utf-8"))
    return d["user"], d["key"]


def api(params, method="GET"):
    data = urllib.parse.urlencode(params).encode()
    url = BASE + (("?" + urllib.parse.urlencode(params)) if method == "GET" else "")
    req = urllib.request.Request(url, data=data if method == "POST" else None,
                                 method=method, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def login(user, key):
    ch = api({"operation": "getchallenge", "username": user})
    tok = ch.get("result", {}).get("token")
    if not tok:
        sys.exit("getchallenge failed: %s" % ch)
    res = api({"operation": "login", "username": user,
               "accessKey": hashlib.md5((tok + key).encode()).hexdigest()}, method="POST")
    if not res.get("success"):
        sys.exit("login failed: %s" % res.get("error"))
    return res["result"]["sessionName"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("query", nargs="?", default="")
    ap.add_argument("--describe", default="")
    a = ap.parse_args()
    user, key = creds()
    sess = login(user, key)
    if a.describe:
        res = api({"operation": "describe", "sessionName": sess, "elementType": a.describe})
    else:
        res = api({"operation": "query", "sessionName": sess, "query": a.query})
    print(json.dumps(res, ensure_ascii=False))


if __name__ == "__main__":
    main()
