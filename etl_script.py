#!/usr/bin/env python3
"""EPS Dashboard ETL service (v2)
Daily 12:15 & 00:00 : Inventory (Google Sheets) + Sales Orders (CRM) + Hot Jobs (CRM)
Sunday 00:00        : Visit report slot (reserved)
1st of month 00:00  : Monthly masters: sales person / macro / BOI / DBD (reserved)
Credentials: _CORE_Private/crm_credentials.json (gitignored) or env CRM_USER / CRM_KEY
"""
import os, sys, json, time, datetime, logging, urllib.request, subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(BASE_DIR, "RAW_Data")
LOG_FILE = os.path.join(BASE_DIR, "etl_sync.log")
CRED_FILE = os.path.join(BASE_DIR, "_CORE_Private", "crm_credentials.json")
SHEET_URL = ("https://docs.google.com/spreadsheets/d/12lxhhodM5u2IpuafCfsznm-Ul-gat-zLoffGdPhqPuA"
             "/export?format=csv&gid=1430193901")

logging.basicConfig(filename=LOG_FILE, level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s")

def log(msg):
    logging.info(msg)
    print(f"[{datetime.datetime.now():%Y-%m-%d %H:%M:%S}] {msg}", flush=True)

def creds():
    u, k = os.environ.get("CRM_USER"), os.environ.get("CRM_KEY")
    if u and k:
        return u, k
    try:
        d = json.load(open(CRED_FILE, encoding="utf-8"))
        return d["user"], d["key"]
    except Exception as e:
        log(f"CRM credentials unavailable ({e}) — CRM steps skipped")
        return None, None

def fetch_inventory():
    dest = os.path.join(RAW_DIR, "5_Inventory_Supplier.csv")
    try:
        req = urllib.request.Request(SHEET_URL, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=90) as r:
            data = r.read()
        tmp = dest + ".tmp"
        with open(tmp, "wb") as f:
            f.write(data)
        os.replace(tmp, dest)          # atomic swap: readers never see a half file
        log(f"inventory ok ({len(data):,} bytes)")
    except Exception as e:
        log(f"inventory FAILED: {e}")

def run_script(script, u, k, label):
    try:
        p = subprocess.run([sys.executable, os.path.join(BASE_DIR, script), "--user", u, "--key", k],
                           capture_output=True, text=True, timeout=1200)
        if p.returncode == 0:
            tail = [l for l in p.stdout.strip().split("\n") if l.strip()][-3:]
            log(f"{label} ok: " + " | ".join(tail))
        else:
            log(f"{label} FAILED rc={p.returncode}: {p.stderr.strip()[:200]}")
    except Exception as e:
        log(f"{label} FAILED: {e}")

def job_daily():
    log("=== daily sync start ===")
    fetch_inventory()
    u, k = creds()
    if u:
        run_script("pull_so_2026.py", u, k, "SO")
        run_script("pull_hotjobs_2026.py", u, k, "HotJobs")
    log("=== daily sync done ===")

def job_weekly():
    log("=== weekly sync (visit reports) — reserved slot ===")

def job_monthly():
    log("=== monthly sync (sales person / macro / BOI / DBD) — reserved slot ===")

if __name__ == "__main__":
    log("EPS Dashboard ETL v2 started — daily 12:15 & 00:00")
    job_daily()                     # initial sync right away

    last_1215 = last_0000 = last_week = last_month = None
    while True:
        now = datetime.datetime.now()
        d, hm = now.strftime("%Y-%m-%d"), now.strftime("%H:%M")
        if hm == "12:15" and last_1215 != d:
            job_daily(); last_1215 = d
        if hm == "00:00" and last_0000 != d:
            job_daily(); last_0000 = d
            if now.weekday() == 6 and last_week != d:
                job_weekly(); last_week = d
            if now.day == 1 and last_month != d:
                job_monthly(); last_month = d
        time.sleep(30)
