#!/usr/bin/env python3
"""Monthly OIE (สศอ.) refresh — 1st of month, 00:00.

ทำอะไร
  1. เรียก fetch_oie_data.py ของ Playbook เพื่อดาวน์โหลด 7 ไฟล์ดัชนีของ สศอ.
     (ต้องได้ 7/7 — ถ้าไม่ครบ ถือว่า "ยังไม่ออก" และไม่แตะข้อมูลเดิม)
  2. วางไฟล์ต้นทางลง "โฟลเดอร์งาน" ของเดือนนั้น: @Work 2026/<YYYY-MM> BOI & Cap U/
  3. คัดลอกเฉพาะไฟล์ที่ EPS Dashboard ต้องใช้เข้า _CORE_Private/ (Capacity_Utilization_<YYYYMM>.csv)

หมายเหตุ: การสร้างรายงาน SA/Scoring (Industrial_Indicators_*.xlsx) ต้องใช้ openpyxl
          ซึ่งเครื่องนี้ยังติดตั้งไม่ได้ — สคริปต์นี้จึงทำเท่าที่ทำได้และรายงานส่วนที่เหลือ
"""
import datetime
import glob
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DASH = os.path.dirname(HERE)                       # AI Dashboard
CORE = os.path.join(DASH, "_CORE_Private")
PLAYBOOK = "/home/jom/SynologyDrive/MD File/BOI-Monthly-Playbook/scripts"
FETCH = os.path.join(PLAYBOOK, "fetch_oie_data.py")
WORK_ROOT = "/home/jom/SynologyDrive/@Work 2026"

FILES = ["capidx.xlsx", "prodidx1.xlsx", "shipidx.xlsx", "invidx.xlsx",
         "invratio.xlsx", "labidx.xlsx", "labaprod2.xlsx"]


def main():
    now = datetime.datetime.now()
    ym = now.strftime("%Y-%m")
    work_dir = os.path.join(WORK_ROOT, "%s BOI & Cap U" % ym)
    os.makedirs(work_dir, exist_ok=True)

    print("=== OIE monthly refresh %s ===" % ym, flush=True)
    print("work folder:", work_dir, flush=True)

    # 1) fetch
    if not os.path.exists(FETCH):
        sys.exit("fetch script not found: %s" % FETCH)
    r = subprocess.run([sys.executable, FETCH, "--out", work_dir],
                       capture_output=True, text=True, timeout=1800)
    out = (r.stdout or "") + (r.stderr or "")
    print(out[-600:], flush=True)

    got = [f for f in FILES if os.path.exists(os.path.join(work_dir, f))]
    print("downloaded %d/%d" % (len(got), len(FILES)), flush=True)
    if len(got) < len(FILES):
        print("!! incomplete — สศอ. อาจยังไม่ออกงวดใหม่; ไม่แตะข้อมูลเดิม", flush=True)
        return 0

    # 2) แปลง capidx.xlsx -> Capacity_Utilization_<YYYYMM>.csv (ใช้ LibreOffice ไม่ต้องมี openpyxl)
    conv = os.path.join(HERE, "update_capu_from_oie.py")
    if os.path.exists(conv):
        rc = subprocess.run([sys.executable, conv], capture_output=True, text=True, timeout=1800)
        print(((rc.stdout or "") + (rc.stderr or ""))[-700:], flush=True)
    else:
        print("!! update_capu_from_oie.py not found — ข้ามการแปลง CapU", flush=True)

    # 3) report the newest artifacts so the digest/ETL can pick them up
    print("artifacts in work folder:")
    for f in sorted(glob.glob(os.path.join(work_dir, "*"))):
        print("   ", os.path.basename(f), os.path.getsize(f), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
