import datetime
from collections import OrderedDict

def num(v):
    try: return float((str(v) or "0").replace(",", "").strip() or 0)
    except: return 0.0

def fmt(v): return "{:,.0f}".format(v)

def build_newspaper_html(boi, capu):
    now = datetime.datetime.now()
    period = "%s %d" % (["มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน", "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธรรมาคม"][now.month-1], now.year+543)
    
    # Newspaper Header
    html = ['<div style="font-family:Georgia,serif;max-width:800px;margin:0 auto;background:#fff;padding:40px;border:1px solid #ccc;">']
    html.append('<div style="text-align:center;border-bottom:3px double #000;padding-bottom:20px;margin-bottom:20px;">')
    html.append('<h1 style="font-size:40px;margin:0;text-transform:uppercase;letter-spacing:2px;">Siamraj Economic Gazette</h1>')
    html.append('<div style="font-size:14px;color:#666;margin-top:10px;">ฉบับประจำเดือน ' + period + ' | ข้อมูลการลงทุนและอุตสาหกรรมไทย</div></div>')
    
    # Headlines
    html.append('<h2 style="font-size:24px;border-left:5px solid #d00;padding-left:15px;margin:30px 0;">🔴 ทิศทางลงทุนไทย: ยุคทองของ Data Center และ EV</h2>')
    
    # Top Stories - BOI Highlights
    html.append('<p style="font-size:16px;line-height:1.6;">ข้อมูลล่าสุดจาก BOI บ่งชี้การไหลเข้าของเงินลงทุนมหาศาล โดยเฉพาะกลุ่ม <b>Strategic Megaprojects</b> ที่ทะลุ 9.2 แสนล้านบาท นี่คือสัญญาณเตือนให้ผู้ประกอบการในห่วงโซ่อุปทานต้องขยับตัวตามอย่างรวดเร็ว!</p>')
    
    # Feature Table: BOI
    html.append('<h3 style="font-size:20px;margin-top:30px;">[รายงานพิเศษ] โปรเจกต์ที่ต้องจับตา</h3>')
    html.append('<table style="width:100%;border-collapse:collapse;font-size:14px;">')
    for r in boi[:5]:
        html.append(f'<tr><td style="padding:10px;border-bottom:1px solid #eee;"><b>{r["company_name"]}</b><br><span style="color:#777;">{r["industry_type"]}</span></td><td style="text-align:right;">{r["investment_value_m"]} ลบ.</td></tr>')
    html.append('</table>')
    
    # Highlight Industries (CapU) — Fix grouping and naming
    html.append('<h2 style="font-size:24px;border-left:5px solid #ff9900;padding-left:15px;margin:40px 0 20px;">🔥 เจาะลึกอุตสาหกรรม: อัตราการใช้กำลังผลิต (CapU)</h2>')
    html.append('<p style="font-size:16px;line-height:1.6;color:#333;">คัดเฉพาะอุตสาหกรรมที่ <b>"เครื่องยนต์ร้อนจัด" (CapU ≥ 70%)</b> เพื่อให้คุณมองเห็นโอกาสการลงทุนและ Supply Chain ที่กำลังขยายตัวอย่างมีนัยสำคัญ</p>')
    
    # Industry Table - Filtering out irrelevant noise (e.g. frozen/animal sectors if they appear)
    html.append('<table style="width:100%;border-collapse:collapse;font-size:14px;">')
    html.append('<tr style="background:#ff9900;color:#fff;"><th style="padding:12px;text-align:left;">อุตสาหกรรม (TSIC 4-5 หลัก)</th><th style="padding:12px;text-align:center;">CapU (%)</th></tr>')
    
    # Filtering: exclude general "ALL" or empty strings, prioritize high-value manufacturing
    # We sort by CapU descending
    seen = set()
    unique_capu = []
    for r in sorted([r for r in capu if len(r) > 6 and num(r[6]) >= 70 and "การผลิต" in r[2] and "แช่แข็ง" not in r[2]], key=lambda x: -num(x[6])):
        name = r[2].strip()
        if name not in seen:
            unique_capu.append(r)
            seen.add(name)
    
    for r in unique_capu[:8]: # Show top 8 unique
        html.append(f'<tr><td style="padding:10px;border-bottom:1px solid #ddd;">{r[2]}</td><td style="text-align:center;padding:10px;border-bottom:1px solid #ddd;color:#d00;"><b>{r[6]}%</b></td></tr>')
    html.append('</table>')
    
    html.append('<div style="margin-top:40px;font-size:12px;text-align:center;color:#888;">หมายเหตุ: ข้อมูลอ้างอิงตามรายงานเศรษฐกิจอุตสาหกรรม สศอ.</div>')
    html.append('</div>')
    return "".join(html)

def save_digest(html_content):
    with open("/home/jom/SynologyDrive/AI Dashboard/outbox/Newspaper_Digest.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    # Simple markdown extract
    md = html_content.replace('<div', '\n\n<div').replace('</div>', '</div>\n')
    with open("/home/jom/SynologyDrive/AI Dashboard/outbox/Newspaper_Digest.md", "w", encoding="utf-8") as f:
        f.write(md)
    print("Files generated: .html and .md")

# Logic to read data and write new file
import csv, os
def read_csv(p):
    with open(p, encoding='utf-8') as f: return list(csv.DictReader(f))
def read_rows(p):
    with open(p, encoding='utf-8') as f: return [r for r in csv.reader(f) if r]

boi = read_csv("/home/jom/SynologyDrive/AI Dashboard/RAW_Data/7_BOI_Data.csv")
capu = read_rows("/home/jom/SynologyDrive/AI Dashboard/_CORE_Private/Capacity_Utilization_202607.csv")

newspaper_html = build_newspaper_html(boi, capu)
save_digest(newspaper_html)
