#!/usr/bin/env python3
"""แปลงไฟล์ Excel (.xlsx) จาก Google Drive (ใน _CORE_Private/GDrive_Database_EPS/)
โดยใช้ LibreOffice (soffice) แปลงเป็น CSV แล้วแปลงต่อเป็น RAW_Data/ CSV ที่ Dashboard ใช้
"""
import csv
import os
import subprocess

BASE = "/home/jom/SynologyDrive/AI Dashboard"
GDRIVE_DIR = os.path.join(BASE, "_CORE_Private", "GDrive_Database_EPS")
RAW_DIR = os.path.join(BASE, "RAW_Data")
TMP_DIR = "/tmp/eps_gdrive_csv"


def convert_to_csv(filename):
    xlsx_path = os.path.join(GDRIVE_DIR, filename)
    if not os.path.exists(xlsx_path):
        print(f"Error: {xlsx_path} not found")
        return None
    os.makedirs(TMP_DIR, exist_ok=True)
    subprocess.run([
        "soffice", "--headless", "--norestore",
        "-env:UserInstallation=file:///tmp/lo_prof_conv",
        "--convert-to", "csv", "--outdir", TMP_DIR, xlsx_path
    ], capture_output=True, timeout=120)
    base = os.path.splitext(filename)[0] + ".csv"
    csv_path = os.path.join(TMP_DIR, base)
    if os.path.exists(csv_path):
        return csv_path
    return None


def clean_dict(raw_row):
    return {k.replace("\ufeff", "").strip(): str(v).strip() for k, v in raw_row.items() if k}


def process_so():
    csv_path = convert_to_csv("qryExportSO.xlsx")
    if not csv_path:
        return
    out_csv = os.path.join(RAW_DIR, "3_SO_Data.csv")
    count = 0
    tot = 0.0
    with open(csv_path, encoding="utf-8-sig", errors="replace") as fin, \
         open(out_csv, "w", encoding="utf-8", newline="") as fout:
        r = csv.DictReader(fin)
        w = csv.writer(fout)
        w.writerow(["so_id", "quote_ref", "sales_id", "client_id", "client_name",
                    "value_thb", "booking_date", "delivery_date", "status"])
        for raw_row in r:
            row = clean_dict(raw_row)
            dt = str(row.get("Date", "") or "")
            if not dt.startswith("2026"):
                continue
            v = float((row.get("Amount") or "0").replace(",", "").strip() or 0)
            tot += v
            count += 1
            w.writerow([
                row.get("DocNo", ""),
                row.get("RefNo", ""),
                row.get("Sales", ""),
                "",
                row.get("Customer", ""),
                f"{v:.2f}",
                dt[:19],
                str(row.get("DeliveryDueDate", ""))[:10],
                "Created"
            ])
    print(f"3_SO_Data.csv updated from GDrive: {count} rows (2026), {tot/1e6:,.2f} M THB")


def process_quotes():
    csv_path = convert_to_csv("qryExportQT.xlsx")
    if not csv_path:
        return
    out_csv = os.path.join(RAW_DIR, "2_Quote_Data.csv")
    count = 0
    with open(out_csv, "w", encoding="utf-8", newline="") as fout:
        fin = open(csv_path, encoding="utf-8-sig", errors="replace")
        r = csv.DictReader(fin)
        w = csv.writer(fout)
        w.writerow(["quote_id", "sales_id", "client_id", "client_name", "equipment_brand",
                    "value_thb", "stage", "probability_pct", "created_date", "aging_days", "status", "lost_reason", "group_code", "expected_order_date"])
        for raw_row in r:
            row = clean_dict(raw_row)
            count += 1
            v = float((row.get("Sub Total") or "0").replace(",", "").strip() or 0)
            created = str(row.get("Created Time", "") or "")[:10]
            w.writerow([
                row.get("QS Number", ""),
                row.get("Assigned To", ""),
                "",
                row.get("Organization Name", ""),
                row.get("Product", ""),
                f"{v:.2f}",
                row.get("Status", "Pending"),
                row.get("Chance Expect", "50%"),
                created,
                "",
                row.get("Status", "Pending"),
                "",
                "",
                str(row.get("Expected Order Date", ""))[:10]
            ])
        fin.close()
    print(f"2_Quote_Data.csv updated from GDrive: {count} rows")


def process_clients():
    csv_path = convert_to_csv("qryCOOR_Active.xlsx")
    if not csv_path:
        return
    out_csv = os.path.join(RAW_DIR, "9_Client_Master.csv")
    count = 0
    with open(out_csv, "w", encoding="utf-8", newline="") as fout:
        fin = open(csv_path, encoding="utf-8-sig", errors="replace")
        r = csv.DictReader(fin)
        w = csv.writer(fout)
        w.writerow(["client_id", "company_name", "industry_group", "address", "contact_person", "phone", "email", "status"])
        for raw_row in r:
            row = clean_dict(raw_row)
            count += 1
            w.writerow([
                row.get("รหัส", ""),
                row.get("ชื่อ", ""),
                row.get("Industry", ""),
                row.get("ที่อยู่", ""),
                row.get("ชื่อผู้ติดต่อ", ""),
                row.get("โทร", "") or row.get("มือถือ", ""),
                row.get("Email", ""),
                "Active"
            ])
        fin.close()
    print(f"9_Client_Master.csv updated from GDrive: {count} rows")


def main():
    print("=== Converting GDrive Excel files via LibreOffice ===")
    process_so()
    process_quotes()
    process_clients()
    print("=== Conversion complete ===")


if __name__ == "__main__":
    main()
