#!/usr/bin/env python3
"""ดึงโฟลเดอร์ Database_EPS จาก Google Drive ลงเครื่อง (สำหรับ ETL / cron)

โฟลเดอร์ต้นทาง (Drive): "Database_EPS [on workSpace]"
    https://drive.google.com/drive/folders/1F0SB3qCn5hHzn_1L7h_0bNh2AaRadNEs
    ข้อมูล: qryExportSO / qryExportQT / qryCOOR_Active / qryGLREF_All / Customer ID /
            Plan/ / qryExportPO*/ / qryExportSOInv*/ / SOItem/ / Dashboard/

ปลายทาง (local):  _CORE_Private/GDrive_Database_EPS/   (อยู่ในโฟลเดอร์งานเดียว, gitignore)
    * ห้ามย้าย/เปลี่ยนชื่อโฟลเดอร์ต้นทางบน Drive — dashboard อีกชุดอ้าง path ตรงจากที่นั่น

ใช้งาน:
    python3 scripts/pull_gdrive_database_eps.py              # mirror (เพิ่ม/ทับของเดิม)
    python3 scripts/pull_gdrive_database_eps.py --list       # ดูรายการจาก Drive เฉย ๆ ไม่ดาวน์โหลด
    python3 scripts/pull_gdrive_database_eps.py --prune      # ลบไฟล์ local ที่ต้นทางลบแล้วด้วย
    python3 scripts/pull_gdrive_database_eps.py --dry-run    # ดูว่าจะคัดลอกอะไร

ต้องมี: rclone ที่ล็อกอิน Drive ไว้แล้ว (rclone config → remote "gdrive")
        ค่า default: /home/jom/.local/bin/rclone  (~/.config/rclone/rclone.conf)
ใช้ Python stdlib เท่านั้น (เรียก rclone ผ่าน subprocess)
"""
import argparse
import csv
import datetime
import json
import os
import subprocess
import sys

BASE_DIR = "/home/jom/SynologyDrive/AI Dashboard"
RCLONE = os.environ.get("RCLONE_BIN", "/home/jom/.local/bin/rclone")
REMOTE = os.environ.get("EPS_GDRIVE_REMOTE", "gdrive:")
FOLDER_ID = os.environ.get("EPS_GDRIVE_FOLDER_ID", "1F0SB3qCn5hHzn_1L7h_0bNh2AaRadNEs")

DEST = os.path.join(BASE_DIR, "_CORE_Private", "GDrive_Database_EPS")
MANIFEST = os.path.join(BASE_DIR, "_CORE_Private", "GDrive_Database_EPS_manifest.csv")
LOG = os.path.join(BASE_DIR, "gdrive_sync.log")

# Google Docs/Sheets/Slides (sizeless) ต้อง export — เก็บนามสกุลให้ตรงกับที่ทีมใช้
EXPORT_FORMATS = "xlsx,docx,csv,pptx"

# ไฟล์ที่อัปเดตบ่อยที่สุด (ใช้รายงานใน log ว่า "ข้อมูลสดจริงไหม")
FRESH_FILES = ["qryExportSO.xlsx", "qryExportQT.xlsx", "qryGLREF_All.xlsx", "qm_data.js"]


def log(msg):
    stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = "[%s] %s" % (stamp, msg)
    print(line, flush=True)
    try:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass


def rclone(args, timeout=3600):
    cmd = [RCLONE] + args
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                       env=dict(os.environ, RCLONE_CONFIG=os.path.expanduser("~/.config/rclone/rclone.conf")))
    return p


def remote_path():
    return "%s" % REMOTE


def base_args():
    # อ้างโฟลเดอร์ด้วย ID เพื่อไม่ต้องพึ่ง path/ชื่อบน Drive (ชื่อมี "[on workSpace]" ชนกับ syntax)
    return ["--drive-root-folder-id", FOLDER_ID, "--drive-export-formats", EXPORT_FORMATS]


def fetch_manifest():
    """อ่านรายการไฟล์ทั้งหมดจาก Drive (path, size, mtime, id)"""
    p = rclone(["lsjson", "-R", remote_path(), "--no-mimetype"] + base_args())
    if p.returncode != 0:
        raise RuntimeError("rclone lsjson failed rc=%d: %s" % (p.returncode, (p.stderr or "")[:300]))
    rows = json.loads(p.stdout)
    out = []
    for r in rows:
        if r.get("IsDir"):
            continue
        out.append({
            "path": r.get("Path", ""),
            "bytes": max(int(r.get("Size") or 0), 0),
            "mtime": (r.get("ModTime") or "")[:19],
            "drive_id": r.get("ID", ""),
        })
    return out


def read_previous():
    if not os.path.exists(MANIFEST):
        return {}
    with open(MANIFEST, encoding="utf-8-sig") as f:
        # key = path + drive_id : กันกรณีบน Drive มีทั้งไฟล์อัปโหลดจริงและ Google Sheet ชื่อเดียวกัน
        return {(r["path"], r["drive_id"]): r for r in csv.DictReader(f)}


def write_manifest(rows):
    os.makedirs(os.path.dirname(MANIFEST), exist_ok=True)
    with open(MANIFEST, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["path", "bytes", "mtime", "drive_id"])
        w.writeheader()
        w.writerows(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true", help="แสดงรายการจาก Drive ไม่ดาวน์โหลด")
    ap.add_argument("--prune", action="store_true", help="ลบไฟล์ local ที่ต้นทางลบแล้ว (ใช้ sync)")
    ap.add_argument("--dry-run", action="store_true", help="แสดงสิ่งที่จะคัดลอก ไม่เขียนไฟล์")
    a = ap.parse_args()

    if not os.path.exists(RCLONE):
        sys.exit("rclone not found at %s (ตั้ง RCLONE_BIN=... หรือติดตั้งก่อน)" % RCLONE)

    log("=== gdrive sync start === remote=%s folder=%s" % (REMOTE, FOLDER_ID))

    try:
        remote_rows = fetch_manifest()
    except Exception as e:  # noqa: BLE001
        log("FAILED: %s" % e)
        return 1

    prev = read_previous()
    key = lambda r: (r["path"], r["drive_id"])  # noqa: E731
    added = [r for r in remote_rows if key(r) not in prev]
    changed = [r for r in remote_rows
               if key(r) in prev and (prev[key(r)]["bytes"] != str(r["bytes"])
                                      or (prev[key(r)]["mtime"] or "") != r["mtime"])]
    removed = [k for k in prev if k not in {key(r) for r in remote_rows}]
    total = sum(r["bytes"] for r in remote_rows)
    unique = len({r["path"] for r in remote_rows})
    dups = {}
    for r in remote_rows:
        dups.setdefault(r["path"], []).append(r)
    dups = {k: v for k, v in dups.items() if len(v) > 1}
    log("remote: %d รายการ / %d ชื่อไฟล์ไม่ซ้ำ / %.1f MB | ใหม่ %d | เปลี่ยน %d | หายจากต้นทาง %d"
        % (len(remote_rows), unique, total / 1e6, len(added), len(changed), len(removed)))
    if dups:
        # ต้นทางมีทั้งไฟล์ที่อัปโหลดจริง และ Google Sheet/Doc ชื่อเดียวกัน -> rclone เลือกตัวเดียว
        log("   ⚠ ชื่อซ้ำบนต้นทาง %d ชื่อ (ได้มา 1 ตัวต่อชื่อ): %s"
            % (len(dups), ", ".join(sorted(dups)[:6]) + (" …" if len(dups) > 6 else "")))
    for r in (added + changed)[:8]:
        log("   • %s (%s bytes, %s)" % (r["path"][:80], "{:,}".format(r["bytes"]), r["mtime"]))

    if a.list:
        for r in sorted(remote_rows, key=lambda x: x["path"]):
            print("%12s  %s  %s" % ("{:,}".format(r["bytes"]), r["mtime"], r["path"]))
        log("list only — ไม่ได้ดาวน์โหลด")
        return 0

    os.makedirs(DEST, exist_ok=True)
    mode = "sync" if a.prune else "copy"
    args = [mode, remote_path(), DEST,
            "--transfers", "8", "--checkers", "16", "--drive-chunk-size", "32M",
            "--stats", "30s", "--stats-one-line", "--log-level", "INFO"] + base_args()
    if a.dry_run:
        args.append("--dry-run")
    p = rclone(args, timeout=5400)
    out = (p.stdout or "").strip().splitlines()
    for line in out[-4:]:
        log("   rclone: %s" % line.strip()[:200])
    if p.returncode != 0:
        log("FAILED rc=%d: %s" % (p.returncode, (p.stderr or "")[:400]))
        return 1

    if not a.dry_run:
        write_manifest(remote_rows)
        stale = [f for f in FRESH_FILES
                 if not os.path.exists(os.path.join(DEST, f))]
        log("local: %d ไฟล์" % sum(1 for _r, _d, fs in os.walk(DEST) for _f in fs))
        if stale:
            log("   ⚠ ไม่พบไฟล์ที่ควรมี: %s" % ", ".join(stale))
    log("=== gdrive sync done ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
