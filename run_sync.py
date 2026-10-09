#!/usr/bin/env python3
"""EPS Dashboard — one-shot sync runner (สำหรับ cron / automation)

ใช้งาน:
    python3 run_sync.py daily      # Drive (Database_EPS) + Inventory + SO + HotJobs + Overview
    python3 run_sync.py weekly     # Visit Report (CRM Events)
    python3 run_sync.py monthly    # Sales Person / Macro / BOI / DBD / Client Master + Overview
    python3 run_sync.py gdrive     # เฉพาะซิงค์โฟลเดอร์ Database_EPS จาก Google Drive

ต่างจาก etl_script.py: ตัวนี้ "รันครั้งเดียวแล้วจบ" เหมาะกับการเรียกจาก cron
(etl_script.py เป็น loop ที่ตั้งเวลาเอง ใช้เมื่อรันเป็น service)
"""
import os
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable or "python3"
SCRIPTS = os.path.join(BASE, "scripts")


def run(args, label):
    """รันสคริปต์ย่อย แล้ว log ผลแบบสั้น"""
    print(f"[{label}] start: {' '.join(os.path.basename(a) for a in args)}", flush=True)
    try:
        p = subprocess.run(args, cwd=BASE, capture_output=True, text=True, timeout=1800)
    except Exception as e:  # noqa: BLE001
        print(f"[{label}] FAILED: {e}", flush=True)
        return False
    tail = [ln for ln in (p.stdout or "").strip().splitlines() if ln.strip()][-2:]
    if p.returncode == 0:
        print(f"[{label}] ok: " + " | ".join(tail), flush=True)
        return True
    print(f"[{label}] FAILED rc={p.returncode}: {(p.stderr or '').strip()[:300]}", flush=True)
    return False


def gdrive():
    """ซิงค์โฟลเดอร์ Database_EPS (Google Drive) ลง _CORE_Private/GDrive_Database_EPS/

    อัปเดตบน Drive: SO/PO/Invoice/GLREF รับเมล FORMA ~09:00/~15:30 · Dashboard อื่น ๆ ทุก 30-60 นาที
    """
    run([PY, os.path.join(SCRIPTS, "pull_gdrive_database_eps.py")], "gdrive")


def daily():
    # 0) ข้อมูลต้นทางจาก Google Drive (Database_EPS) — ต้องมาก่อน build ทุกตัว
    gdrive()
    # 1) ETL หลัก: Inventory + Sales Orders + Hot Jobs (ใช้ฟังก์ชันจาก etl_script)
    sys.path.insert(0, BASE)
    import etl_script  # noqa: PLC0415
    etl_script.job_daily()
    # 2) CRM analytics: quote status + SO due date/owner (feeds the Group pages)
    run([PY, os.path.join(SCRIPTS, "pull_crm_analytics.py"), "all"], "crm_analytics")
    # 3) Overview ต้องรัน "หลัง" SO เสร็จเสมอ
    run([PY, os.path.join(SCRIPTS, "build_overview.py")], "overview")
    # 4) Group detail (หน้า Group A/B/C/D/R) ต้องรันหลัง SO/Visits/Clients พร้อม
    run([PY, os.path.join(SCRIPTS, "build_group_detail.py")], "group_detail")
    # 5) Group analytics: rolling-12m active, DBD coverage, win rate, quotes, To-Do
    run([PY, os.path.join(SCRIPTS, "build_group_analytics.py")], "group_analytics")


def weekly():
    run([PY, os.path.join(SCRIPTS, "pull_crm_data.py"), "visits", "--year", "2026"], "visits")


def monthly():
    run([PY, os.path.join(SCRIPTS, "pull_crm_data.py"), "accounts"], "client_master")
    run([PY, os.path.join(SCRIPTS, "build_sales_reps.py")], "sales_reps")
    run([PY, os.path.join(SCRIPTS, "build_macro.py")], "macro")
    run([PY, os.path.join(SCRIPTS, "build_boi.py")], "boi")
    run([PY, os.path.join(SCRIPTS, "build_dbd.py")], "dbd")
    run([PY, os.path.join(SCRIPTS, "build_overview.py")], "overview")


MODES = {"daily": daily, "weekly": weekly, "monthly": monthly, "gdrive": gdrive}


def main():
    mode = (sys.argv[1] if len(sys.argv) > 1 else "daily").lower()
    fn = MODES.get(mode)
    if not fn:
        sys.exit(f"usage: {os.path.basename(__file__)} [{'|'.join(MODES)}]")
    print(f"=== EPS Dashboard sync: {mode} ===", flush=True)
    fn()
    print(f"=== {mode} done ===", flush=True)


if __name__ == "__main__":
    main()
