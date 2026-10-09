#!/usr/bin/env python3
"""BOI + CapU monthly digest — build the email from real dashboard data and send it.

Usage
    python3 run_digest.py --to test      # ส่งหา patipan@siamrajplc.com เท่านั้น (ทดสอบ)
    python3 run_digest.py --to groups    # ส่งเข้า eps_group_a..r@siamrajplc.com
    python3 run_digest.py --to none      # สร้างไฟล์อย่างเดียว ไม่ส่ง (preview)

Data (updated by the monthly ETL on the 1st)
    RAW_Data/7_BOI_Data.csv            BOI projects (all source sheets of the workbook)
    RAW_Data/6_Macroeconomic_Data.csv  OIE capacity utilisation by sector

Credentials (never committed): _CORE_Private/mail_credentials.json
    {"user": "patipan", "password": "...", "from": "patipan@siamrajplc.com"}
"""
import argparse
import csv
import datetime
import glob
import json
import os
import smtplib
import sys
import time
from collections import OrderedDict
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "RAW_Data")
CORE = os.path.join(HERE, "_CORE_Private")
OUTBOX = os.path.join(HERE, "outbox")

SMTP_HOST, SMTP_PORT = "mail.siamrajplc.com", 587
GROUPS = ["eps_group_a@siamrajplc.com", "eps_group_b@siamrajplc.com", "eps_group_c@siamrajplc.com",
          "eps_group_d@siamrajplc.com", "eps_group_r@siamrajplc.com"]
CC = ["nussara@siamrajplc.com", "udomlak@siamrajplc.com", "naphon@siamrajplc.com",
      "Thanyathon@siamrajplc.com", "satika@siamrajplc.com"]
TEST_TO = ["patipan@siamrajplc.com"]

TH_MONTHS = ["มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน",
             "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"]


def read_csv(path):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def num(v):
    try:
        return float((v or "0").replace(",", "").strip() or 0)
    except ValueError:
        return 0.0


def fmt(v):
    return "{:,.0f}".format(v)


def card(title, value, unit, sub, color):
    return ('<td style="padding:10px;width:25%;vertical-align:top;">'
            '<div style="background:#fff;border:1px solid #e2e8f0;border-left:4px solid ' + color + ';border-radius:8px;padding:14px;">'
            '<div style="font-size:12px;color:#64748b;font-weight:600;">' + title + '</div>'
            '<div style="font-size:22px;font-weight:800;color:#0f172a;margin-top:6px;">' + value
            + '<span style="font-size:12px;color:#64748b;font-weight:600;"> ' + unit + '</span></div>'
            '<div style="font-size:11px;color:#64748b;margin-top:6px;">' + sub + '</div></div></td>')


def build_html(boi, capu):
    now = datetime.datetime.now()
    period = "%s %d" % (TH_MONTHS[now.month - 1], now.year + 543)

    # --- group BOI rows by workbook sheet ---
    sheets = OrderedDict()
    for r in boi:
        sheets.setdefault((r.get("source_sheet") or "BOI").strip(), []).append(r)

    # --- KPI cards: rows that are programme-level figures ---
    kpis = []
    for r in boi:
        nm = (r.get("company_name") or "")
        v = num(r.get("investment_value_m"))
        if not v:
            continue
        if "H1/2026" in nm or "ภาพรวมเงินลงทุนจริง" in nm:
            kpis.append(("เงินลงทุนจริง H1/" + str(now.year), fmt(v), "ลบ.", "ม.ค.–มิ.ย. " + str(now.year + 543), "#0ea5e9"))
        elif "FastPass" in nm:
            kpis.append(("Thailand FastPass", fmt(v), "ลบ.", "โครงการยุทธศาสตร์", "#10b981"))
        elif "EV" in nm or "BEV" in nm:
            kpis.append(("แผนลงทุน EV/Hybrid", fmt(v), "ลบ.", "ค่ายรถยนต์รายใหญ่", "#8b5cf6"))
    mega = sheets.get("Strategic Megaprojects") or next((v for k, v in sheets.items() if "Strategic" in k), [])
    if mega:
        tot = sum(num(r.get("investment_value_m")) for r in mega)
        kpis.insert(0, ("Megaprojects กลุ่มเป้าหมาย", fmt(tot), "ลบ.", "%d โครงการหลัก" % len(mega), "#f59e0b"))

    html = ['<div style="font-family:\'Sarabun\',Tahoma,Arial,sans-serif;max-width:900px;margin:0 auto;background:#f1f5f9;padding:20px;">']
    html.append('<div style="background:#0f172a;color:#fff;border-radius:10px;padding:20px 24px;margin-bottom:16px;">'
                '<div style="font-size:20px;font-weight:800;">BOI INVESTMENT DASHBOARD</div>'
                '<div style="font-size:13px;color:#94a3b8;margin-top:4px;">สรุปโครงการส่งเสริมการลงทุน BOI และแนวโน้มกลุ่มอุตสาหกรรมไทย</div>'
                '<div style="font-size:12px;color:#64748b;margin-top:4px;">ประจำเดือน ' + period
                + ' • ข้อมูลจาก BOI และ สศอ. (อัปเดตอัตโนมัติจาก EPS Dashboard)</div></div>')

    if kpis:
        html.append('<table style="width:100%;border-collapse:separate;border-spacing:0;"><tr>')
        for k in kpis[:4]:
            html.append(card(*k))
        html.append('</tr></table>')

    # --- one table per workbook sheet ---
    for sheet, rows in sheets.items():
        n = len(rows)
        tot = sum(num(r.get("investment_value_m")) for r in rows)
        html.append('<div style="background:#fff;border:1px solid #e2e8f0;border-radius:10px;padding:18px;margin-top:16px;">')
        head = sheet + ' — ' + str(n) + ' โครงการ'
        if tot:
            head += ' • รวม ' + fmt(tot) + ' ลบ.'
        html.append('<div style="font-size:15px;font-weight:800;color:#0f172a;margin-bottom:10px;">' + head + '</div>')
        html.append('<table style="width:100%;border-collapse:collapse;font-size:12px;">'
                    '<tr style="background:#f1f5f9;color:#475569;">'
                    '<th style="text-align:left;padding:7px;border-bottom:1px solid #e2e8f0;">บริษัท / โครงการ</th>'
                    '<th style="text-align:left;padding:7px;border-bottom:1px solid #e2e8f0;">กลุ่มอุตสาหกรรม</th>'
                    '<th style="text-align:left;padding:7px;border-bottom:1px solid #e2e8f0;">รายละเอียด</th>'
                    '<th style="text-align:right;padding:7px;border-bottom:1px solid #e2e8f0;">มูลค่า (ลบ.)</th></tr>')
        for r in rows:
            v = num(r.get("investment_value_m"))
            html.append('<tr>'
                        '<td style="padding:7px;border-bottom:1px solid #f1f5f9;"><b>' + (r.get("company_name") or "-") + '</b></td>'
                        '<td style="padding:7px;border-bottom:1px solid #f1f5f9;">' + (r.get("industry_type") or "-") + '</td>'
                        '<td style="padding:7px;border-bottom:1px solid #f1f5f9;">' + (r.get("project_detail") or "-")[:90] + '</td>'
                        '<td style="padding:7px;border-bottom:1px solid #f1f5f9;text-align:right;">' + (fmt(v) if v else "-") + '</td></tr>')
        html.append('</table></div>')

    # --- CapU section — full detail, grouped by TSIC level (2/4/5 หลัก) ---
    idx = {}
    for r in capu:
        if len(r) < 7:
            continue
        try:
            y, m = int(r[4]), int(r[5])
        except ValueError:
            continue
        idx[(r[1], (y, m))] = num(r[6])

    periods = sorted({p for (_t, p) in idx})
    latest = periods[-1] if periods else None
    prev = periods[-2] if len(periods) > 1 else None
    allv = idx.get(("ALL", latest)) if latest else None
    allp = idx.get(("ALL", prev)) if prev else None

    rows_by_level = {2: [], 4: [], 5: []}
    for r in capu:
        if len(r) < 7 or r[1] == "ALL" or len(r[1]) not in rows_by_level:
            continue
        try:
            y, m = int(r[4]), int(r[5])
        except ValueError:
            continue
        if (y, m) != latest:
            continue
        pv = idx.get((r[1], prev)) if prev else None
        rows_by_level[len(r[1])].append({"tsic": r[1], "name": r[2], "v": num(r[6]), "prev": pv})
    for k in rows_by_level:
        rows_by_level[k].sort(key=lambda x: -x["v"])

    period_label = "%02d/%d" % (latest[1], latest[0] + 543) if latest else "-"
    html.append('<div style="background:#fff;border:1px solid #e2e8f0;border-radius:10px;padding:18px;margin-top:16px;">'
                '<div style="font-size:15px;font-weight:800;color:#0f172a;margin-bottom:10px;">'
                'แนวโน้มกลุ่มอุตสาหกรรม — อัตราการใช้กำลังการผลิต (CapU) งวด ' + period_label
                + ' • ที่มา: สศอ. (ค่ายังไม่ปรับฤดูกาล)</div>')
    if allv is not None:
        d = ("%+.2f" % (allv - allp)) if allp is not None else "-"
        html.append('<div style="font-size:13px;color:#334155;margin-bottom:6px;">ภาพรวมทั้งอุตสาหกรรม: <b>'
                    + "%.2f" % allv + '%</b> (เดือนก่อน '
                    + ("%.2f" % allp if allp is not None else "-") + ' · Δ ' + d + ')</div>')
    html.append('<div style="font-size:12px;color:#64748b;margin-bottom:4px;">⭐ = CapU ≥ 70% (ใกล้เต็มกำลัง — สัญญาณลงทุน) '
                '· Δ = เทียบเดือนก่อน</div>')

    def capu_table(title, items, limit=None):
        shown = items[:limit] if limit else items
        h = ['<div style="font-size:13px;font-weight:800;color:#0f172a;margin:14px 0 6px;">'
             + title + ' (' + str(len(items)) + ' รายการ)</div>']
        h.append('<table style="width:100%;border-collapse:collapse;font-size:12px;">'
                 '<tr style="background:#f1f5f9;color:#475569;">'
                 '<th style="text-align:left;padding:6px;border-bottom:1px solid #e2e8f0;">TSIC</th>'
                 '<th style="text-align:left;padding:6px;border-bottom:1px solid #e2e8f0;">กลุ่มอุตสาหกรรม</th>'
                 '<th style="text-align:right;padding:6px;border-bottom:1px solid #e2e8f0;">CapU (%)</th>'
                 '<th style="text-align:right;padding:6px;border-bottom:1px solid #e2e8f0;">Δ</th></tr>')
        for it in shown:
            dv = ("%+.2f" % (it["v"] - it["prev"])) if it["prev"] is not None else "-"
            col = "#B91C1C" if (it["prev"] is not None and it["v"] < it["prev"]) else "#047857"
            star = " ⭐" if it["v"] >= 70 else ""
            h.append('<tr><td style="padding:6px;border-bottom:1px solid #f1f5f9;font-family:monospace;">' + it["tsic"] + '</td>'
                     '<td style="padding:6px;border-bottom:1px solid #f1f5f9;">' + it["name"] + star + '</td>'
                     '<td style="padding:6px;border-bottom:1px solid #f1f5f9;text-align:right;"><b>' + "%.2f" % it["v"] + '</b></td>'
                     '<td style="padding:6px;border-bottom:1px solid #f1f5f9;text-align:right;color:' + col + ';">' + dv + '</td></tr>')
        h.append('</table>')
        return "".join(h)

    html.append(capu_table("TSIC 2 หลัก — ภาพรวมรายอุตสาหกรรม", rows_by_level[2]))
    html.append(capu_table("TSIC 4 หลัก", rows_by_level[4]))
    html.append(capu_table("TSIC 5 หลัก — รายละเอียดสินค้า", rows_by_level[5]))
    html.append('</div>')

    html.append('<div style="font-size:11px;color:#94a3b8;text-align:center;margin-top:16px;">'
                'ส่งอัตโนมัติจาก EPS Dashboard • Siamraj PLC • สร้างเมื่อ '
                + now.strftime("%d/%m/%Y %H:%M") + '</div></div>')
    return "".join(html), period


def read_rows(path):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return [r for r in csv.reader(f) if r]


def newest_capu():
    """ไฟล์ CapU ต้นทางที่ใหม่ที่สุด (มีคอลัมน์ TSIC ครบ 2/4/5 หลั ก)"""
    files = sorted(glob.glob(os.path.join(CORE, "Capacity_Utilization_[0-9][0-9][0-9][0-9][0-9][0-9].csv")))
    return files[-1] if files else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--to", choices=["test", "groups", "none"], default="none")
    a = ap.parse_args()

    boi = read_csv(os.path.join(RAW, "7_BOI_Data.csv"))
    capu_src = newest_capu()
    capu = read_rows(capu_src) if capu_src else []
    if not boi and not capu:
        sys.exit("no source data — run `python3 run_sync.py monthly` first")
    print("capu source:", capu_src, "| rows:", len(capu))

    # newspaper digest logic
    html_path = os.path.join(OUTBOX, "Newspaper_Digest.html")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            html = f.read()
        period = datetime.datetime.now().strftime("%B %Y")
    else:
        html, period = build_html(boi, capu)

    os.makedirs(OUTBOX, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y-%m")
    path = os.path.join(OUTBOX, "BOI_CapU_digest_%s.html" % stamp)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print("digest built:", path, "(%d bytes)" % len(html))

    if a.to == "none":
        print("dry run — not sending")
        return

    cred_path = os.path.join(CORE, "mail_credentials.json")
    creds = json.load(open(cred_path, encoding="utf-8")) if os.path.exists(cred_path) else {}
    user = creds.get("user") or os.environ.get("SMTP_USER", "")
    pwd = creds.get("password") or os.environ.get("SMTP_PASS", "")
    sender = creds.get("from") or (user + "@siamrajplc.com")
    if not user or not pwd:
        sys.exit("mail credentials missing -> create _CORE_Private/mail_credentials.json")

    to = TEST_TO if a.to == "test" else GROUPS
    cc = [] if a.to == "test" else CC
    subject = "Dashboard สรุปโครงการ BOI และแนวโน้มกลุ่มอุตสาหกรรม ประจำเดือน " + period

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = ", ".join(to)
    if cc:
        msg["Cc"] = ", ".join(cc)
    msg.attach(MIMEText(html, "html", "utf-8"))

    s = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=180)
    s.starttls()
    s.login(user, pwd)
    # SMTP ของ mail.siamrajplc.com ตอบช้า/ตัดการเชื่อมต่อเป็นครั้งคราว -> ลองซ้ำอัตโนมัติ
    last_err = None
    for attempt in range(1, 4):
        try:
            s.sendmail(sender, to + cc, msg.as_string())
            last_err = None
            break
        except Exception as e:  # noqa: BLE001
            last_err = e
            print("send attempt %d/3 failed: %s" % (attempt, e), flush=True)
            if attempt < 3:
                time.sleep(15 * attempt)
                try:
                    s.quit()
                except Exception:  # noqa: BLE001
                    pass
                s = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=180)
                s.starttls()
                s.login(user, pwd)
    if last_err:
        raise last_err
    s.quit()
    print("sent -> TO:", ", ".join(to), ("| CC: " + ", ".join(cc)) if cc else "| (no CC)")


if __name__ == "__main__":
    main()
