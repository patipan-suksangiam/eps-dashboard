#!/usr/bin/env python3
"""Convert the OIE (สศอ.) CapU workbook -> Capacity_Utilization_<YYYYMM>.csv

ไม่ใช้ openpyxl / Excel — ใช้ LibreOffice (OpenOffice) แปลง .xlsx -> .csv แล้ว parse ด้วย stdlib
ใช้ได้กับไฟล์ต้นทาง: capidx.xlsx (ชีท 'รายเดือน')

ผลลัพธ์ (ฟอร์แมตที่ scripts/build_macro.py อ่าน):
    id,TSIC,name,weight,year,month,cap_u_pct
    <row>,<tsic>,<ชื่อ>,<น้ำหนัก>,<ค.ศ.>,<เดือน 1-12>,<ค่า>

ค่า 'ดัชนี้รวมยังไม่ได้ปรับฤดูกาล' จะถูกส่งออกเป็นแถวพิเศษ sector='ALL_INDUSTRY'
เพื่อให้ build_macro.py ดึงภาพรวมทั้งอุตสาหกรรมได้โดยไม่ต้อง hardcode
"""
import csv
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CORE = os.path.join(ROOT, "_CORE_Private")
WORK_ROOT = "/home/jom/SynologyDrive/@Work 2026"

MONTH_NUM = {"ม.ค.": 1, "ก.พ.": 2, "มี.ค.": 3, "เม.ย.": 4, "พ.ค.": 5, "มิ.ย.": 6,
             "ก.ค.": 7, "ส.ค.": 8, "ก.ย.": 9, "ต.ค.": 10, "พ.ย.": 11, "ธ.ค.": 12}


def find_source():
    """ไฟล์ capidx.xlsx ล่าสุด — จากโฟลเดอร์งานเดือนล่าสุด หรือสำเนาใน _CORE_Private"""
    cands = []
    for d in [CORE, WORK_ROOT]:
        if not os.path.isdir(d):
            continue
        for root, _dirs, files in os.walk(d):
            if root.count(os.sep) - d.count(os.sep) > 2:
                continue
            for f in files:
                if f.lower() == "capidx.xlsx":
                    cands.append(os.path.join(root, f))
    cands.sort(key=os.path.getmtime, reverse=True)
    return cands[0] if cands else None


def to_csv(xlsx, outdir):
    os.makedirs(outdir, exist_ok=True)
    subprocess.run(["soffice", "--headless", "--norestore",
                    "-env:UserInstallation=file:///tmp/lo_capu",
                    "--convert-to", "csv:Text - txt - csv (StarCalc):44,34,76,1,,0,false,true,true",
                    "--outdir", outdir, xlsx],
                   capture_output=True, text=True, timeout=600)
    out = os.path.join(outdir, os.path.splitext(os.path.basename(xlsx))[0] + ".csv")
    if not os.path.exists(out):
        raise RuntimeError("LibreOffice did not produce a CSV for " + xlsx)
    return out


def parse(csv_path):
    rows = list(csv.reader(open(csv_path, encoding="utf-8")))
    yi = next((i for i, r in enumerate(rows) if r and r[0].strip().startswith("ผลิตภัณฑ์")), None)
    if yi is None:
        raise RuntimeError("ไม่พบแถวหัวตาราง (ผลิตภัณฑ์) ใน " + csv_path)
    mi = yi + 1

    cols, year = {}, None
    for c in range(2, len(rows[yi])):
        y = rows[yi][c].strip()
        if y.isdigit():
            year = int(y) - 543                      # พ.ศ. -> ค.ศ.
        m = (rows[mi][c].strip().rstrip("*").strip() if c < len(rows[mi]) else "")
        if year and m in MONTH_NUM:
            cols[c] = (year, MONTH_NUM[m])

    out, overall = [], []
    rid = 0
    for r in rows[mi + 1:]:
        if not r or not r[0].strip():
            continue
        label = r[0].strip()
        weight = r[1].strip() if len(r) > 1 else ""
        if "ดัชนีรวม" in label:                      # แถวภาพรวม (ปรับ/ไม่ปรับฤดูกาล)
            if "ยังไม่ได้ปรับ" in label:
                for c, (y, m) in cols.items():
                    v = (r[c] if c < len(r) else "").strip().rstrip("*")
                    if v:
                        overall.append((y, m, v))
            continue
        tsic = None
        mm = re.match(r"TSIC\s*:\s*(\d+)", label)
        if mm:
            tsic = mm.group(1)
        else:
            mm = re.match(r"(\d{4,5})\s", label)
            if mm:
                tsic = mm.group(1)
        if not tsic:
            continue
        name = re.sub(r"^TSIC\s*:\s*\d+\s*", "", label)
        name = re.sub(r"^\d{4,5}\s*", "", name).strip()
        for c, (y, m) in sorted(cols.items()):
            v = (r[c] if c < len(r) else "").strip().rstrip("*")
            if not v:
                continue
            rid += 1
            out.append([rid, tsic, name, weight, y, m, v])

    latest = max((y, m) for y, m, _ in overall) if overall else None
    # ส่งออกแถว ALL ทุกงวด เพื่อให้เทียบ Δ เดือนก่อนได้
    for y, m, v in sorted(overall):
        rid += 1
        out.append([rid, "ALL", "ภาพรวมทั้งอุตสาหกรรม (ยังไม่ปรับฤดูกาล)", "100.00", y, m, v])
    return out, latest


def main():
    src = find_source()
    if not src:
        sys.exit("ไม่พบ capidx.xlsx — รัน scripts/monthly_oie_update.py ก่อน")
    print("source:", src)

    tmp = "/tmp/capu_csv"
    shutil.rmtree(tmp, ignore_errors=True)
    csv_path = to_csv(src, tmp)
    print("converted:", csv_path, os.path.getsize(csv_path), "bytes")

    rows, latest = parse(csv_path)
    if not rows:
        sys.exit("แปลงแล้วได้ 0 แถว — ตรวจโครงสร้างไฟล์ต้นทาง")

    ym = "%04d%02d" % latest if latest else "latest"
    out = os.path.join(CORE, "Capacity_Utilization_%s.csv" % ym)
    with open(out, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        for r in rows:
            w.writerow(r)
    print("wrote:", out, "| rows:", len(rows), "| latest period:", latest)

    # คัดลอก CSV ที่ได้ไปไว้ในโฟลเดอร์งานเดือนล่าสุดด้วย
    folder = os.path.join(WORK_ROOT, "%s BOI & Cap U" % "%04d-%02d" % latest)
    if os.path.isdir(folder):
        shutil.copy2(out, folder)
        print("copied to work folder:", folder)
    return 0


if __name__ == "__main__":
    sys.exit(main())
