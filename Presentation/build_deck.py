# -*- coding: utf-8 -*-
"""EPS Dashboard — Presentation builder
ผังการเก็บข้อมูล + การนำเสนอข้อมูล (ภาษาไทย, 16:9)
"""
import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn
from pptx.oxml import parse_xml

# ---------------- design tokens ----------------
FONT = "Tahoma"
INK     = RGBColor(0x0F, 0x17, 0x2A)
SLATE   = RGBColor(0x1E, 0x29, 0x3B)
MUTED   = RGBColor(0x64, 0x74, 0x8B)
BORDER  = RGBColor(0xE2, 0xE8, 0xF0)
LIGHT   = RGBColor(0xF8, 0xFA, 0xFC)
WHITE   = RGBColor(0xFF, 0xFF, 0xFF)
BLUE    = RGBColor(0x1D, 0x4E, 0xD8)
BLUE_L  = RGBColor(0xEF, 0xF6, 0xFF)
SKY     = RGBColor(0x0E, 0xA5, 0xE9)
TEAL    = RGBColor(0x0D, 0x94, 0x88)
AMBER   = RGBColor(0xD9, 0x77, 0x06)
VIOLET  = RGBColor(0x7C, 0x3A, 0xED)
GREEN   = RGBColor(0x05, 0x96, 0x69)
RED     = RGBColor(0xDC, 0x26, 0x26)
PINK    = RGBColor(0xDB, 0x27, 0x77)

SW, SH = 13.333, 7.5
ML = 0.72                 # left margin
CW = SW - 2 * ML          # content width
BODY_TOP = 1.72

prs = Presentation()
prs.slide_width = Inches(SW)
prs.slide_height = Inches(SH)
BLANK = prs.slide_layouts[6]


# ---------------- primitives ----------------
def slide():
    return prs.slides.add_slide(BLANK)


def rect(s, x, y, w, h, fill=WHITE, line=None, radius=0.04, lw=0.9, shape=MSO_SHAPE.ROUNDED_RECTANGLE):
    sh = s.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    if shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        try:
            sh.adjustments[0] = radius
        except Exception:
            pass
    if fill is None:
        sh.fill.background()
    else:
        sh.fill.solid()
        sh.fill.fore_color.rgb = fill
    if line is None:
        sh.line.fill.background()
    else:
        sh.line.color.rgb = line
        sh.line.width = Pt(lw)
    sh.shadow.inherit = False
    sh.text_frame.word_wrap = True
    return sh


def txt(s, x, y, w, h, text, size=12, bold=False, color=INK, align=PP_ALIGN.LEFT,
        line=1.15, anchor=MSO_ANCHOR.TOP, space_after=0, italic=False):
    tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = anchor
    for i, ln in enumerate(str(text).split("\n")):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.line_spacing = line
        p.space_after = Pt(space_after)
        r = p.add_run()
        r.text = ln
        f = r.font
        f.name = FONT
        f.size = Pt(size)
        f.bold = bold
        f.italic = italic
        f.color.rgb = color
    return tb


def bullets(s, x, y, w, h, items, size=12, gap=7, lead_color=INK, body_color=MUTED,
            bullet_color=BLUE, line=1.25, bchar="▪"):
    """items: list of str | (lead, rest) | (lead, rest, color)"""
    tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    for i, it in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.line_spacing = line
        p.space_after = Pt(gap)
        r0 = p.add_run()
        r0.text = bchar + "  "
        r0.font.name = FONT
        r0.font.size = Pt(size)
        r0.font.color.rgb = bullet_color
        r0.font.bold = True
        if isinstance(it, str):
            r1 = p.add_run()
            r1.text = it
            r1.font.name = FONT
            r1.font.size = Pt(size)
            r1.font.color.rgb = lead_color
        else:
            lead, rest = it[0], it[1]
            rc = it[2] if len(it) > 2 else lead_color
            r1 = p.add_run()
            r1.text = lead
            r1.font.name = FONT
            r1.font.size = Pt(size)
            r1.font.bold = True
            r1.font.color.rgb = rc
            if rest:
                r2 = p.add_run()
                r2.text = rest
                r2.font.name = FONT
                r2.font.size = Pt(size)
                r2.font.color.rgb = body_color
    return tb


def header(s, kicker, title, accent=BLUE):
    rect(s, 0, 0, SW, 0.085, fill=accent, shape=MSO_SHAPE.RECTANGLE)
    txt(s, ML, 0.40, CW, 0.24, kicker, size=10, bold=True, color=MUTED)
    txt(s, ML, 0.68, CW, 0.62, title, size=26, bold=True, color=INK)
    rect(s, ML, 1.42, CW, 0.012, fill=BORDER, shape=MSO_SHAPE.RECTANGLE)
    rect(s, ML, 1.405, 1.1, 0.032, fill=accent, shape=MSO_SHAPE.RECTANGLE)


def footer(s, n, note=""):
    rect(s, ML, 7.06, CW, 0.01, fill=BORDER, shape=MSO_SHAPE.RECTANGLE)
    txt(s, ML, 7.16, 8.6, 0.22, note or "EPS Dashboard · สถาปัตยกรรมการเก็บข้อมูล & การนำเสนอข้อมูล", size=8.5, color=MUTED)
    txt(s, ML + CW - 0.9, 7.16, 0.9, 0.22, f"{n}", size=8.5, bold=True, color=MUTED, align=PP_ALIGN.RIGHT)


def card(s, x, y, w, h, title, big=None, unit="", sub=None, accent=BLUE,
         fill=WHITE, title_size=10.5, big_size=25, sub_size=9.5, bar=True):
    rect(s, x, y, w, h, fill=fill, line=BORDER)
    if bar:
        rect(s, x, y + 0.02, 0.055, h - 0.04, fill=accent, shape=MSO_SHAPE.RECTANGLE)
    px = x + 0.24
    pw = w - 0.42
    # stacked layout — every block is placed below the previous one, measured
    # from the top of the card, so nothing can overlap
    cy = y + 0.15
    txt(s, px, cy, pw, 0.3, title, size=title_size, bold=True, color=MUTED, line=1.05)
    cy += 0.22 if len(str(title)) <= int(pw * 9) else 0.42
    if big is not None:
        bh = big_size / 72.0 * 1.32
        txt(s, px, cy, pw, bh, str(big), size=big_size, bold=True, color=accent)
        cy += bh - 0.02
    if unit:
        txt(s, px, cy, pw, 0.3, unit, size=sub_size, color=MUTED, line=1.15)
    if sub:
        txt(s, px, y + h - 0.62, pw, 0.52, sub, size=sub_size, color=MUTED, line=1.2,
            anchor=MSO_ANCHOR.BOTTOM)


def _cell_border(cell, edge="B", color=BORDER, width_pt=0.9):
    tcPr = cell._tc.get_or_add_tcPr()
    tag = "a:ln" + edge
    for e in tcPr.findall(qn(tag)):
        tcPr.remove(e)
    ln = parse_xml(
        '<%s xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" w="%d" cap="flat" cmpd="sng" algn="ctr">'
        '<a:solidFill><a:srgbClr val="%s"/></a:solidFill><a:prstDash val="solid"/><a:round/></%s>'
        % (tag, int(width_pt * 12700), str(color), tag)
    )
    tcPr.insert_element_before(ln, "a:lnTlToBr", "a:lnBlToTr", "a:cell3D",
                               "a:noFill", "a:solidFill", "a:gradFill", "a:blipFill",
                               "a:pattFill", "a:grpFill", "a:headers", "a:extLst")


def table(s, x, y, w, headers, rows, col_w, row_h=0.33, head_h=0.36,
          size=10, head_size=10, head_fill=SLATE, aligns=None, head_color=WHITE,
          bold_first=False, zebra=None, body_color=INK, pad=0.09):
    n_r, n_c = len(rows) + 1, len(headers)
    shp = s.shapes.add_table(n_r, n_c, Inches(x), Inches(y), Inches(w), Inches(head_h + row_h * len(rows)))
    tbl = shp.table
    # neutral style: no borders, no banding (we draw our own)
    tblPr = shp._element.graphic.graphicData.tbl[0]
    tblPr.set("firstRow", "0")
    tblPr.set("bandRow", "0")
    for el in tblPr.findall(qn("a:tableStyleId")):
        tblPr.remove(el)
    for i, cw in enumerate(col_w):
        tbl.columns[i].width = Inches(cw)
    tbl.rows[0].height = Inches(head_h)
    for r in range(1, n_r):
        tbl.rows[r].height = Inches(row_h)

    aligns = aligns or [PP_ALIGN.LEFT] * n_c
    for c, htext in enumerate(headers):
        cell = tbl.cell(0, c)
        cell.fill.solid()
        cell.fill.fore_color.rgb = head_fill
        cell.margin_left = cell.margin_right = Inches(pad)
        cell.margin_top = cell.margin_bottom = Inches(0.04)
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
        tf = cell.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.alignment = aligns[c]
        r = p.add_run()
        r.text = str(htext)
        r.font.name = FONT
        r.font.size = Pt(head_size)
        r.font.bold = True
        r.font.color.rgb = head_color

    for ri, row in enumerate(rows, start=1):
        for ci, val in enumerate(row):
            cell = tbl.cell(ri, ci)
            if zebra is not None:
                cell.fill.solid()
                cell.fill.fore_color.rgb = LIGHT if ri % 2 == 0 else WHITE
            else:
                cell.fill.solid()
                cell.fill.fore_color.rgb = WHITE
            cell.margin_left = cell.margin_right = Inches(pad)
            cell.margin_top = cell.margin_bottom = Inches(0.03)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            _cell_border(cell, "B", BORDER, 0.9)
            tf = cell.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            p.alignment = aligns[ci]
            r = p.add_run()
            r.text = str(val)
            r.font.name = FONT
            r.font.size = Pt(size)
            r.font.bold = bool(bold_first and ci == 0)
            r.font.color.rgb = body_color
    return tbl


def wire(s, x, y, w, h, items, label_size=8):
    """mini wireframe: items = list of (x, y, w, h, label, kind)"""
    rect(s, x, y, w, h, fill=RGBColor(0xFC, 0xFD, 0xFE), line=BORDER, radius=0.02)
    for (ix, iy, iw, ih, lab, kind) in items:
        fill = {"kpi": BLUE_L, "chart": RGBColor(0xF1, 0xF5, 0xF9), "table": RGBColor(0xF1, 0xF5, 0xF9),
                "panel": RGBColor(0xEC, 0xFD, 0xF5), "filter": RGBColor(0xFE, 0xF9, 0xEC)}.get(kind, LIGHT)
        rect(s, x + ix, y + iy, iw, ih, fill=fill, line=RGBColor(0xCB, 0xD5, 0xE1), radius=0.03)
        txt(s, x + ix + 0.07, y + iy + 0.05, iw - 0.14, ih - 0.08, lab, size=label_size, color=MUTED, line=1.05)


def notes(s, text):
    s.notes_slide.notes_text_frame.text = text


def kpi_row(s, y, items, h=1.28, gap=0.18, x0=ML, total=CW, big_size=25, title_size=10.5):
    n = len(items)
    w = (total - gap * (n - 1)) / n
    for i, (t, big, unit, sub, col) in enumerate(items):
        card(s, x0 + i * (w + gap), y, w, h, t, big, unit, sub, col,
             big_size=big_size, title_size=title_size)
    return w


# =========================================================
# 1 · TITLE
# =========================================================
s = slide()
rect(s, 0, 0, SW, SH, fill=INK, shape=MSO_SHAPE.RECTANGLE)
rect(s, 0, 0, SW, 0.12, fill=BLUE, shape=MSO_SHAPE.RECTANGLE)
# decorative grid blocks
for i, c in enumerate([SKY, TEAL, AMBER, VIOLET, PINK]):
    rect(s, SW - 5.35 + i * 0.62, 1.05, 0.5, 0.5, fill=c, radius=0.12)
txt(s, ML, 1.95, 8.5, 0.3, "SIAM RAJ PLC  ·  EPS BUSINESS UNIT", size=11, bold=True, color=SKY)
txt(s, ML, 2.42, 9.6, 0.9, "EPS Dashboard", size=48, bold=True, color=WHITE)
txt(s, ML, 3.42, 9.8, 1.0, "ผังการเก็บข้อมูล\nและการนำเสนอข้อมูล", size=27, bold=True,
    color=RGBColor(0xE2, 0xE8, 0xF0), line=1.25)
rect(s, ML, 4.86, 1.6, 0.035, fill=SKY, shape=MSO_SHAPE.RECTANGLE)
txt(s, ML, 5.12, 9.0, 0.3, "Interactive Sales & Operational Cockpit · FY 2026", size=12, color=RGBColor(0x94, 0xA3, 0xB8))
txt(s, ML, 5.44, 9.6, 0.3, "ฉบับเดือนตุลาคม 2569  ·  ข้อมูลจริงจาก CRM / OIE / BOI / DIW-DBD ณ 19 ต.ค. 2569",
    size=10.5, color=RGBColor(0x64, 0x74, 0x8B))

stats = [("4", "แหล่งข้อมูลต้นทาง"), ("19", "ไฟล์ CSV ในคลังข้อมูล"),
         ("8", "หน้าแดชบอร์ด + 6 roles"), ("2", "รอบอัปเดตอัตโนมัติ/วัน")]
for i, (num, lab) in enumerate(stats):
    x = ML + i * 3.02
    rect(s, x, 6.08, 2.78, 0.86, fill=RGBColor(0x1E, 0x29, 0x3B), line=RGBColor(0x33, 0x41, 0x55), radius=0.08)
    txt(s, x + 0.22, 6.18, 0.9, 0.5, num, size=22, bold=True, color=SKY)
    txt(s, x + 1.02, 6.24, 1.6, 0.55, lab, size=9, color=RGBColor(0xCB, 0xD5, 0xE1), line=1.15)
notes(s, "เปิดด้วยภาพรวม: ระบบนี้ทำอะไร — เก็บข้อมูลจาก 4 แหล่ง กลั่นเป็น CSV 19 ไฟล์ แล้วนำเสนอเป็นแดชบอร์ด 8 หน้า "
         "โดยทุกตัวเลขบนจอสามารถตรวจย้อนกลับถึงแหล่งต้นทางได้ และอัปเดตอัตโนมัติวันละ 2 รอบ")

# =========================================================
# 2 · AGENDA
# =========================================================
s = slide()
header(s, "สารบัญ", "เนื้อหาการนำเสนอ", BLUE)
agenda = [
    ("01", "ภาพรวมระบบ", "ระบบทั้งหมดทำงานอย่างไรในหน้าเดียว — เก็บ → แปลง → เก็บเป็นไฟล์ → นำเสนอ", SKY),
    ("02", "ผังการเก็บข้อมูล", "แหล่งข้อมูล 4 กลุ่ม · 24 สคริปต์ ETL · คลัง CSV 3 ชั้น · ตารางเวลา cron · กุญแจเชื่อมข้อมูล", TEAL),
    ("03", "การนำเสนอข้อมูล", "สิทธิ์ตามบทบาท · 8 หน้าแดชบอร์ด ทีละหน้า · ที่มาของทุกตัวเลข (traceability)", VIOLET),
    ("04", "คุณภาพข้อมูล & การให้บริการ", "จุดแข็ง ข้อจำกัดที่กระทบตัวเลข · การโฮสต์บน NAS · แผนพัฒนาต่อ", AMBER),
]
y = 1.82
for i, (num, title, desc, col) in enumerate(agenda):
    rect(s, ML, y, CW, 1.12, fill=WHITE, line=BORDER)
    rect(s, ML, y, 0.06, 1.12, fill=col, shape=MSO_SHAPE.RECTANGLE)
    txt(s, ML + 0.34, y + 0.24, 1.0, 0.6, num, size=30, bold=True, color=col)
    txt(s, ML + 1.42, y + 0.22, 9.7, 0.32, title, size=16, bold=True, color=INK)
    txt(s, ML + 1.42, y + 0.62, 9.8, 0.4, desc, size=10.5, color=MUTED, line=1.2)
    y += 1.26
notes(s, "สี่ส่วน: ภาพรวม, การเก็บข้อมูล, การนำเสนอ, และคุณภาพข้อมูลกับการให้บริการ")

# =========================================================
# 3 · BIG PICTURE
# =========================================================
s = slide()
header(s, "ภาพรวมระบบ", "จาก 4 ระบบต้นทาง สู่แดชบอร์ด 8 หน้า", BLUE)
stages = [
    ("1", "เก็บ (Collect)", SKY, ["CRM vtiger 8.0", "Google Sheets PM Master", "สศอ. OIE + ธปท.", "BOI · DIW · DBD"]),
    ("2", "แปลง (Transform)", TEAL, ["24 สคริปต์ Python (stdlib)", "ดึง · ล้าง · join · คำนวณ", "ไม่มี DB server", "รันตาม cron"]),
    ("3", "เก็บเป็นไฟล์ (Store)", VIOLET, ["RAW_Data/ 19 ไฟล์ CSV", "≈96,000 แถว · ≈10 MB", "เปิดตรวจด้วย Excel ได้", "เป็นสัญญากลาง ETL ↔ UI"]),
    ("4", "นำเสนอ (Serve)", AMBER, ["SPA 8 หน้า + 6 roles", "โหลด CSV แล้ววาดกราฟ", "Chart.js (vendored)", "ไทย / อังกฤษ"]),
]
bw = 2.78
gap = (CW - bw * 4) / 3
for i, (num, title, col, items) in enumerate(stages):
    x = ML + i * (bw + gap)
    rect(s, x, 1.78, bw, 3.34, fill=WHITE, line=BORDER)
    rect(s, x, 1.78, bw, 0.5, fill=col, shape=MSO_SHAPE.RECTANGLE)
    txt(s, x + 0.2, 1.9, bw - 0.4, 0.28, f"{num}. {title}", size=12.5, bold=True, color=WHITE)
    yy = 2.46
    for it in items:
        txt(s, x + 0.2, yy, bw - 0.38, 0.5, "· " + it, size=9.8, color=INK, line=1.15)
        yy += 0.62
    if i < 3:
        ar = s.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(x + bw + 0.06), Inches(3.24), Inches(gap - 0.12), Inches(0.36))
        ar.fill.solid()
        ar.fill.fore_color.rgb = RGBColor(0xCB, 0xD5, 0xE1)
        ar.line.fill.background()
        ar.shadow.inherit = False

txt(s, ML, 5.28, CW, 0.26, "หลักการที่ยึดทั้งระบบ", size=11, bold=True, color=INK)
principles = [
    ("CSV เป็นสัญญากลาง ", "— ETL เขียนไฟล์, หน้าเว็บอ่านไฟล์ ไม่ผูกกันด้วย API"),
    ("ทุก KPI คำนวณสด ", "— ไม่มีตัวเลขฮาร์ดโค้ดในหน้าเว็บ; ค่าที่ไม่มีแหล่งข้อมูลถูกถอดออก"),
    ("ตรวจย้อนได้ทุกตัวเลข ", "— กดดูได้ว่าค่ามาจากไฟล์ไหน และไฟล์นั้นมาจากระบบไหน"),
]
bullets(s, ML, 5.62, 5.9, 1.3, principles, size=10.5, gap=6)
rect(s, ML + 6.3, 5.58, CW - 6.3, 1.32, fill=BLUE_L, line=RGBColor(0xBF, 0xDB, 0xFE), radius=0.06)
txt(s, ML + 6.5, 5.7, CW - 6.7, 1.1,
    "ทำไมเลือก CSV ไม่ใช้ Database?\n· ต้นทุนต่ำ ไม่ต้องดูแล server · ทีมเปิดตรวจเองได้ด้วย Excel\n· สำรองข้อมูล = copy โฟลเดอร์ · เพียงพอสำหรับข้อมูลระดับ ~100k แถว",
    size=9.8, color=INK, line=1.3)
notes(s, "ย้ำ 4 ขั้น: Collect → Transform → Store → Serve และหลักการ 3 ข้อที่ทำให้ระบบตรวจสอบได้ "
         "คำถามที่มักโดนถาม: ทำไมไม่ใช้ database — เพราะข้อมูลระดับนี้ CSV พอ และทีมตรวจเองได้")

# =========================================================
# 4 · DIVIDER 01
# =========================================================
def divider(num, title, sub, items, col):
    s = slide()
    rect(s, 0, 0, SW, SH, fill=INK, shape=MSO_SHAPE.RECTANGLE)
    rect(s, 0, 0, 0.14, SH, fill=col, shape=MSO_SHAPE.RECTANGLE)
    txt(s, ML, 1.5, 4.0, 1.6, num, size=110, bold=True, color=RGBColor(0x33, 0x41, 0x55))
    txt(s, ML + 0.06, 3.1, 9.5, 0.8, title, size=38, bold=True, color=WHITE)
    txt(s, ML + 0.08, 4.0, 9.6, 0.8, sub, size=14, color=RGBColor(0x94, 0xA3, 0xB8), line=1.3)
    yy = 5.0
    for it in items:
        txt(s, ML + 0.08, yy, 9.6, 0.3, "— " + it, size=11, color=RGBColor(0xCB, 0xD5, 0xE1))
        yy += 0.36
    return s


s = divider("01", "ผังการเก็บข้อมูล", "ข้อมูลมาจากไหน ถูกแปลงอย่างไร และเก็บไว้ที่ใด",
            ["แหล่งข้อมูล 4 กลุ่ม และรอบการอัปเดต", "เส้นทางการไหล: ระบบต้นทาง → สคริปต์ → ไฟล์ CSV",
             "คลัง CSV 3 ชั้น (ต้นทาง / รายกลุ่ม / วิเคราะห์)", "ตารางเวลา ETL และกุญแจเชื่อมข้อมูล"], SKY)
notes(s, "เข้า part แรก: การเก็บข้อมูล — ตอบคำถามว่า 'ตัวเลขบนแดชบอร์ดมาจากไหน'")

# =========================================================
# 5 · DATA SOURCES
# =========================================================
s = slide()
header(s, "01 · ผังการเก็บข้อมูล", "แหล่งข้อมูล 4 กลุ่ม — ทั้งหมดเชื่อมต่อจริง", SKY)
rows = [
    ["1. CRM (ภายใน)", "vtiger 8.0\nwebservice.php",
     "1_CRM_Sales_Person · 2_Quote_Data\n3_SO_Data · 4_Visit_Report · 9_Client_Master",
     "ใบเสนอราคา 41,181 · SO 1,057\nเข้าพบ 20,006 · ลูกค้า 5,530", "วันละ 2 ครั้ง\n+ รายสัปดาห์/เดือน"],
    ["2. Inventory (PM)", "Google Sheets\nPM Master (Sale tab)",
     "5_Inventory_Supplier", "453 รายการ · 16.73 M THB\nDead stock 195 รายการ · 4.44 M", "วันละ 2 ครั้ง"],
    ["3. เศรษฐกิจมหภาค", "สศอ. (OIE) + ธปท.\nไฟล์รายเดือน 7 ไฟล์",
     "6_Macroeconomic_Data", "15,143 แถว · CapU 129 เซกเตอร์\nMPI · ดอกเบี้ยนโยบาย · Capex", "รายเดือน (วันที่ 1)"],
    ["4. รัฐ / ส่งเสริมการลงทุน", "BOI รายงานอนุมัติ\nDIW ทะเบียนโรงงาน + DBD API",
     "7_BOI_Data · 8_DBD_Data", "BOI 24 โครงการ · ทะเบียนโรงงาน\nจับคู่ลูกค้าได้ ~30%", "รายเดือน"],
]
table(s, ML, 1.78, CW, ["แหล่งข้อมูล", "ระบบต้นทาง", "ไฟล์ปลายทาง (RAW_Data/)", "ปริมาณข้อมูลจริง", "รอบอัปเดต"],
      rows, [1.95, 2.55, 3.33, 2.55, 1.5], row_h=0.82, head_h=0.46, size=9.2, head_size=9.6,
      aligns=[PP_ALIGN.LEFT] * 5, bold_first=True)
rect(s, ML, 5.7, CW, 0.92, fill=RGBColor(0xFE, 0xF9, 0xEC), line=RGBColor(0xFD, 0xE6, 0x8A), radius=0.05)
txt(s, ML + 0.22, 5.83, CW - 0.44, 0.72,
    "สิ่งที่ยังไม่มีในต้นทาง (ทำให้บางตัวเลขยังไม่ครบ):  เป้า Quota ราย supplier & rebate · MPI รายเซกเตอร์ · "
    "เหตุผลชนะ/แพ้ (win-loss) ใน CRM · เบอร์/ผู้ติดต่อลูกค้าใน Client Master",
    size=9.8, color=RGBColor(0x92, 0x40, 0x0E), line=1.35)
footer(s, 5, "ที่มา: data_sources.md · Data_Dictionary_and_Schedule.md · นับแถวจาก RAW_Data/*.csv ณ 19 ต.ค. 2569")
notes(s, "ทั้ง 4 แหล่งเชื่อมต่อจริงแล้ว ไม่มี mock — ตัวเลขในคอลัมน์ 'ปริมาณข้อมูลจริง' นับจากไฟล์จริง "
         "ปิดท้ายด้วยสิ่งที่ไม่ครบ เพื่อไม่ให้เข้าใจผิดว่าข้อมูลสมบูรณ์ 100%")

# =========================================================
# 6 · PIPELINE DIAGRAM
# =========================================================
s = slide()
header(s, "01 · ผังการเก็บข้อมูล", "เส้นทางการไหลของข้อมูล: ระบบต้นทาง → สคริปต์ → ไฟล์ → หน้าเว็บ", SKY)
cols = [
    ("แหล่งข้อมูล", SKY, [("CRM vtiger (webservice)", 1), ("Google Sheets (PM Master)", 1),
                          ("OIE + ธปท. (ไฟล์รายเดือน)", 1), ("BOI · DIW · DBD", 1)]),
    ("สคริปต์ดึง (pull)", TEAL, [("crm_query.py → pull_crm_data.py", 2), ("pull_so_2026 · pull_hotjobs_2026", 2),
                                 ("pull_crm_analytics.py", 1), ("etl_script.py + clean_inventory.py", 2),
                                 ("build_macro · build_boi · build_dbd", 2), ("monthly_oie_update.py", 1)]),
    ("คลัง CSV (RAW_Data/)", VIOLET, [("ชั้นต้นทาง 0–9 (11 ไฟล์)", 1), ("ชั้นรายกลุ่ม 10–11", 1),
                                      ("ชั้นวิเคราะห์ 12–17", 1), ("เขียนทับทุกครั้งที่รัน", 1),
                                      ("ไม่มีการแก้ด้วยมือ", 1)]),
    ("สคริปต์คำนวณ (build) + แอป", AMBER, [("build_overview.py", 1), ("build_group_detail.py", 1),
                                            ("build_group_analytics.py", 1), ("build_open_quotes.py", 1),
                                            ("run_sync.py (cron)", 1), ("serve_raw_data.py", 1),
                                            ("Dashboard_App/ (SPA)", 1)]),
]
CARD_TOP, CARD_H = 2.2, 3.02
bw, gap = 2.72, (CW - 2.72 * 4) / 3
for i, (title, col, items) in enumerate(cols):
    x = ML + i * (bw + gap)
    rect(s, x, 1.76, bw, 0.44, fill=col, shape=MSO_SHAPE.RECTANGLE)
    txt(s, x + 0.16, 1.86, bw - 0.3, 0.26, title, size=10.2, bold=True, color=WHITE)
    rect(s, x, CARD_TOP, bw, CARD_H, fill=WHITE, line=BORDER)
    yy = CARD_TOP + 0.14
    for it, nlines in items:
        txt(s, x + 0.16, yy, bw - 0.3, 0.17 * nlines + 0.06, "▸ " + it, size=8.4, color=INK, line=1.15)
        yy += 0.155 * nlines + 0.215
    if i < 3:
        ar = s.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(x + bw + 0.04), Inches(3.55), Inches(gap - 0.08), Inches(0.28))
        ar.fill.solid(); ar.fill.fore_color.rgb = RGBColor(0xCB, 0xD5, 0xE1)
        ar.line.fill.background(); ar.shadow.inherit = False

rect(s, ML, 5.38, CW, 1.5, fill=LIGHT, line=BORDER, radius=0.05)
txt(s, ML + 0.24, 5.5, CW - 0.48, 0.26, "ลำดับการรันที่ต้องรักษา (ถ้าสลับ ตัวเลขจะค้างของเก่า)", size=10.5, bold=True, color=INK)
order = ["① ดึงข้อมูลต้นทาง\n(CRM / Sheets / ไฟล์ราชการ)",
         "② 3_SO_Data +\n9_Client_Master พร้อม",
         "③ build_overview",
         "④ build_group_detail",
         "⑤ build_group_analytics",
         "⑥ หน้าเว็บ\nอ่านไฟล์ CSV"]
xw = (CW - 0.48 - 5 * 0.16) / 6
for i, o in enumerate(order):
    xx = ML + 0.24 + i * (xw + 0.16)
    rect(s, xx, 5.86, xw, 0.82, fill=WHITE, line=BLUE, radius=0.05)
    txt(s, xx + 0.08, 5.94, xw - 0.16, 0.68, o, size=8.4, color=INK, line=1.2,
        align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
footer(s, 6, "สคริปต์ทั้งหมดใช้ Python stdlib (urllib/csv/json) — รันได้บนเครื่องทั่วไปและบน NAS")
notes(s, "นี่คือผังหลักของงาน: 4 คอลัมน์ = ต้นทาง → ตัวดึง → ไฟล์ → ตัวคำนวณ+แอป "
         "และลำดับ 6 ขั้นด้านล่างคือสิ่งที่ต้องรักษาเวลาแก้ระบบ")

# =========================================================
# 7 · CSV LAYERS
# =========================================================
s = slide()
header(s, "01 · ผังการเก็บข้อมูล", "คลังข้อมูล RAW_Data/ — 19 ไฟล์ แบ่ง 3 ชั้น", SKY)

layers = [
    ("ชั้นที่ 1 · ข้อมูลต้นทาง (0–9) — 11 ไฟล์", SKY, "ดึง/แปลงจากระบบต้นทางโดยตรง ยังไม่ผ่านการสรุป",
     ["0_EPS_Overview_2026 (9)", "0_EPS_HotJobs_2026 (6)", "1_CRM_Sales_Person (60)", "2_Quote_Data (41,181)",
      "3_SO_Data (1,057)", "4_Visit_Report (20,006)", "5_Inventory_Supplier (453)",
      "6_Macroeconomic_Data (15,143)", "7_BOI_Data (24)", "8_DBD_Data (5,530)", "9_Client_Master (5,530)"], 1.62),
    ("ชั้นที่ 2 · ข้อมูลรายกลุ่ม (10–11) — 2 ไฟล์", TEAL, "แยกยอดตามกลุ่มขาย A–D/R จากกติกา group_map.json",
     ["10_Group_Reps (77)  ·  พนักงานขาย + ยอดขายต่อกลุ่ม",
      "11_Group_Clients (578)  ·  ลูกค้า + ยอด + จำนวนครั้งที่เข้าพบ ต่อกลุ่ม"], 1.02),
    ("ชั้นที่ 3 · ข้อมูลวิเคราะห์ / เจาะลึก (12–17) — 6 ไฟล์", VIOLET,
     "คำนวณล่วงหน้าเพื่อให้หน้าเว็บโหลดเร็ว (pre-aggregated)",
     ["12_Group_KPI (6)  ·  KPI รายกลุ่ม 14 ตัวชี้วัด", "13_Rep_Performance (15)  ·  ผลงานรายพนักงานขาย",
      "14_Client_Detail (4,535)  ·  ลูกค้ารายราย + DBD + การเข้าพบ", "15_SO_Delivery (1,057)  ·  กำหนดส่ง vs วันบุ๊คกิ้ง",
      "16_Todo (18)  ·  งานที่ระบบแนะนำให้ทำ", "17_Open_Quotes (1,059)  ·  ใบเสนอราคาค้างพร้อม aging"], 1.62),
]
y = 1.74
for title, col, sub, items, h in layers:
    rect(s, ML, y, CW, h, fill=WHITE, line=BORDER)
    rect(s, ML, y, 0.06, h, fill=col, shape=MSO_SHAPE.RECTANGLE)
    txt(s, ML + 0.26, y + 0.12, CW - 0.5, 0.26, title, size=11.5, bold=True, color=col)
    txt(s, ML + 0.26, y + 0.39, CW - 0.5, 0.22, sub, size=8.8, color=MUTED)
    # items in up to 3 columns
    ncol = 3 if len(items) > 5 else 1
    per = (len(items) + ncol - 1) // ncol
    for ci in range(ncol):
        chunk = items[ci * per:(ci + 1) * per]
        if not chunk:
            continue
        colw = (CW - 0.6) / ncol
        txt(s, ML + 0.28 + ci * colw, y + 0.68, colw - 0.15,
            h - 0.74, "\n".join("· " + c for c in chunk), size=8.4, color=INK, line=1.38)
    y += h + 0.14
footer(s, 7, "ตัวเลขในวงเล็บ = จำนวนแถวข้อมูลจริง (นับด้วย csv.reader ณ 19 ต.ค. 2569) · รวม ≈96,000 แถว ≈10 MB")
notes(s, "อธิบาย 3 ชั้น: ต้นทาง (ห้ามแก้มือ) → รายกลุ่ม (เกิดจาก group_map) → วิเคราะห์ (คำนวณล่วงหน้าเพื่อความเร็ว) "
         "การมีชั้น 12–17 ทำให้หน้าเว็บไม่ต้องประมวลผลหนักในเบราว์เซอร์")

# =========================================================
# 8 · ETL SCHEDULE
# =========================================================
s = slide()
header(s, "01 · ผังการเก็บข้อมูล", "ตารางเวลา ETL — อัปเดตอัตโนมัติผ่าน cron", SKY)
sched = [
    ("ทุกวัน 12:15 และ 00:00", "run_sync.py daily", BLUE,
     "Drive sync → Inventory + SO + HotJobs → CRM analytics → Overview → Group detail → Group analytics"),
    ("ทุกวันอาทิตย์ 00:20", "run_sync.py weekly", TEAL, "Visit Report (CRM Events) — 20,006 กิจกรรมปี 2026"),
    ("วันที่ 1 ของเดือน 00:30", "run_sync.py monthly", VIOLET,
     "Client Master · Sales Person · Macro · BOI · DBD → แล้วรัน Overview ใหม่"),
    ("วันที่ 1 ของเดือน 00:00", "monthly_oie_update.py", AMBER, "ดึงดัชนี สศอ. 7 ไฟล์ → แปลง CapU เข้า 6_Macroeconomic_Data"),
    ("วันที่ 2 ของเดือน 08:30", "run_digest.py --to groups", PINK, "เมลสรุป BOI + CapU ให้ 5 กลุ่มขาย (+Cc 5 คน)"),
]
y = 1.76
for when, cmd, col, detail in sched:
    rect(s, ML, y, CW, 0.74, fill=WHITE, line=BORDER)
    rect(s, ML, y, 0.055, 0.74, fill=col, shape=MSO_SHAPE.RECTANGLE)
    txt(s, ML + 0.24, y + 0.11, 2.55, 0.26, when, size=9.8, bold=True, color=col)
    txt(s, ML + 0.24, y + 0.39, 2.55, 0.24, cmd, size=8.4, color=MUTED)
    txt(s, ML + 2.95, y + 0.13, CW - 3.2, 0.52, detail, size=9.2, color=INK, line=1.25)
    y += 0.8

rect(s, ML, y + 0.04, CW, 0.94, fill=RGBColor(0xF0, 0xFD, 0xF4), line=RGBColor(0xBB, 0xF7, 0xD0), radius=0.05)
txt(s, ML + 0.24, y + 0.12, CW - 0.48, 0.26, "หลักฐานการทำงานจริง — etl_sync.log", size=10, bold=True, color=GREEN)
txt(s, ML + 0.24, y + 0.37, CW - 0.48, 0.54,
    "2026-10-19 00:00:01  === daily sync start ===\n"
    "2026-10-19 00:00:14  SO ok: year 2026: 1057 sales orders | 174.98 M THB\n"
    "2026-10-19 00:00:18  HotJobs ok:  D: 32 deals | 21.49 M  ·  R: 52 deals | 11.21 M   →  done",
    size=8.6, color=RGBColor(0x06, 0x5F, 0x46), line=1.35)
footer(s, 8, "cron บน NAS (JOM-NAS) · ตัวเลือกอื่น: รัน etl_script.py เป็น service ที่ตั้งเวลาในตัว")
notes(s, "ตารางเวลาจริงที่ใช้อยู่ — ชี้ให้ดูว่าวันละ 2 รอบหลัก (12:15 กับ 00:00) และมีรายสัปดาห์/รายเดือน "
         "log ด้านล่างคือหลักฐานว่าวันนี้รันสำเร็จ ได้ SO 1,057 ใบ 174.98 ล้าน")

# =========================================================
# 9 · JOIN KEYS
# =========================================================
s = slide()
header(s, "01 · ผังการเก็บข้อมูล", "กุญแจเชื่อมข้อมูล — หัวใจที่ทำให้ตัวเลขต่อกันได้", SKY)
keys = [
    ("client_id", "11x…", "เชื่อม Quote · SO · Visit · Client Master · DBD", SKY),
    ("emp_id", "19x… / 20x…", "เชื่อม Sales Person · เจ้าของ SO/Quote · ผลงานรายคน", TEAL),
    ("industry_group", "CH14 · FD05", "รหัสอุตสาหกรรม → group_map.json → กลุ่มขาย A–D/R", VIOLET),
    ("ชื่อบริษัท", "ไทย ↔ จดทะเบียน", "จับคู่กับทะเบียนโรงงาน DIW/DBD (จับได้ ~30%)", AMBER),
]
bw = (CW - 3 * 0.2) / 4
for i, (k, sample, desc, col) in enumerate(keys):
    x = ML + i * (bw + 0.2)
    rect(s, x, 1.78, bw, 1.68, fill=WHITE, line=BORDER)
    rect(s, x, 1.78, bw, 0.055, fill=col, shape=MSO_SHAPE.RECTANGLE)
    txt(s, x + 0.2, 1.94, bw - 0.4, 0.28, k, size=11.5, bold=True, color=col)
    txt(s, x + 0.2, 2.24, bw - 0.4, 0.24, sample, size=8.8, color=MUTED)
    txt(s, x + 0.2, 2.56, bw - 0.4, 0.8, desc, size=9.2, color=INK, line=1.25)

txt(s, ML, 3.66, CW, 0.26, "กติกาการแบ่งกลุ่มขาย (group_map.json)", size=11, bold=True, color=INK)
bullets(s, ML, 3.98, 6.2, 2.3, [
    ("1) รหัสอุตสาหกรรม (IndCode) ", "เป็นตัวตัดสินหลักว่าลูกค้าอยู่กลุ่มใด"),
    ("2) จังหวัดระยอง ", "→ กลุ่ม R (Eastern Hub) แม้รหัสจะชี้กลุ่มอื่น"),
    ("3) ชื่อลูกค้า (override) ", "ชนะทุกกติกา เช่น PTTGC / PTTME → กลุ่ม R",),
    ("SV01 / SV04 / OM ", "เป็นงานร่วม (ตามโครงการ) ไม่ผูกกลุ่มเดียว"),
    ("ยอดที่ map ไม่ได้ ", "→ กลุ่ม U (unmapped) และไม่ถูกนับเข้ากลุ่มใด"),
], size=9.6, gap=6)

rect(s, ML + 6.55, 3.94, CW - 6.55, 2.42, fill=RGBColor(0xFE, 0xF2, 0xF2), line=RGBColor(0xFE, 0xCA, 0xCA), radius=0.05)
txt(s, ML + 6.78, 4.08, CW - 7.0, 0.26, "จุดที่ต้องระวัง", size=10.5, bold=True, color=RED)
txt(s, ML + 6.78, 4.40, CW - 7.0, 1.85,
    "· ยอดที่ map กลุ่มไม่ได้ = 82.80 M (≈19% ของยอดปี) อยู่ในกลุ่ม U\n"
    "· ลูกค้าที่ไม่มีรหัสอุตสาหกรรมใน CRM (8%) จะหลุดจากกลุ่ม\n"
    "· ชื่อไทยใน CRM ≠ ชื่อจดทะเบียนเต็ม → DBD จับคู่ได้เพียง ~30%\n"
    "· ยอดใน SO บางใบไม่มี sales_id → ใช้เจ้าของลูกค้า (owner_id) แทน\n"
    "· vtiger ไม่รับ ORDER BY → ต้องไล่หน้าจนว่างแล้ว dedupe ด้วย id",
    size=9, color=RGBColor(0x99, 0x1B, 0x1B), line=1.35)
footer(s, 9, "ที่มา: data_sources.md §join key · README_Architecture.md §4 · _CORE_Private/group_map.json")
notes(s, "นี่คือส่วนที่คนมักข้าม แต่เป็นเหตุผลว่าทำไมยอดรวมของ 5 กลุ่มไม่เท่ายอดทั้งบริษัท "
         "ถ้าถูกถามว่าทำไม Group รวมได้ 91.6 แต่บริษัท 174.98 — เพราะอีก 82.8 ล้าน map กลุ่มไม่ได้")

# =========================================================
# 10 · DATA QUALITY
# =========================================================
s = slide()
header(s, "01 · ผังการเก็บข้อมูล", "คุณภาพข้อมูล — จุดแข็ง และข้อจำกัดที่ต้องอ่านคู่กับตัวเลข", SKY)
rect(s, ML, 1.78, (CW - 0.3) / 2, 4.35, fill=RGBColor(0xF0, 0xFD, 0xF4), line=RGBColor(0xBB, 0xF7, 0xD0), radius=0.04)
txt(s, ML + 0.26, 1.92, 5.2, 0.3, "✓  จุดแข็ง", size=13, bold=True, color=GREEN)
bullets(s, ML + 0.26, 2.34, (CW - 0.3) / 2 - 0.52, 3.6, [
    ("ไม่มี mock เหลือในข้อมูลที่ใช้จริง ", "— ทุกไฟล์เป็นข้อมูลจริง (ตรวจ 24 ก.ย. 2569)"),
    ("ทุก KPI คำนวณสดจาก CSV ", "— ไม่มีค่าฮาร์ดโค้ด; KPI ที่ไม่มีแหล่งข้อมูลถูกถอดออก"),
    ("ตรวจย้อนได้ ", "— ทุกหน้าบอกไฟล์ต้นทาง; เปิดไฟล์ตรวจเองได้"),
    ("อัปเดตอัตโนมัติ ", "— วันละ 2 รอบ + รายสัปดาห์/รายเดือน พร้อม log"),
    ("คำนวณล่วงหน้า ", "— ชั้น 12–17 ทำให้หน้าเว็บเปิดเร็ว"),
], size=9.8, gap=9, bullet_color=GREEN)
rect(s, ML + (CW - 0.3) / 2 + 0.3, 1.78, (CW - 0.3) / 2, 4.35, fill=RGBColor(0xFE, 0xF2, 0xF2),
     line=RGBColor(0xFE, 0xCA, 0xCA), radius=0.04)
txt(s, ML + (CW - 0.3) / 2 + 0.56, 1.92, 5.2, 0.3, "!  ข้อจำกัด", size=13, bold=True, color=RED)
bullets(s, ML + (CW - 0.3) / 2 + 0.56, 2.34, (CW - 0.3) / 2 - 0.52, 3.6, [
    ("industry ไม่ครบ 100% ", "— 92% ของลูกค้ามีรหัส, ที่เหลือหลุดจากกลุ่ม"),
    ("ยอด map กลุ่มไม่ได้ 82.80 M ", "— 20.9% ของยอดปี อยู่ในกลุ่ม U"),
    ("DBD จับคู่ ~30% ", "— บริษัทเทรดดิ้งที่ไม่มีโรงงานจะไม่เจอ"),
    ("contact_person ว่าง ", "— ยังไม่ได้ join CRM Contacts (8,453 ราย)"),
    ("ไม่มี win/loss reason ", "— CRM ไม่ได้เก็บ จึงวิเคราะห์สาเหตุแพ้ไม่ได้"),
    ("ค่า macro บางค่าคงที่ในสคริปต์ ", "— MPI / ดอกเบี้ย ควรตรวจกับต้นฉบับก่อนใช้ตัดสินใจ"),
], size=9.8, gap=7, bullet_color=RED)
footer(s, 10, "ที่มา: README.md §ความถูกต้องของข้อมูล · Data_Dictionary_and_Schedule.md §ข้อที่ยังต่อยอดได้")
notes(s, "ความน่าเชื่อถือของสไลด์นี้สำคัญ: บอกทั้งของดีและของที่ยังขาด "
         "ถ้าผู้บริหารถามเลข 19% ที่หาย — คำตอบคือลูกค้าที่ไม่มีรหัสอุตสาหกรรม ให้กรอกใน CRM")

# =========================================================
# 11 · DIVIDER 02
# =========================================================
s = divider("02", "การนำเสนอข้อมูล", "จากไฟล์ CSV สู่หน้าจอที่คนใช้งานได้จริง",
            ["สิทธิ์การเข้าถึงตามบทบาท (role-based)", "แดชบอร์ด 8 หน้า — เห็นอะไร และอ่านอย่างไร",
             "ที่มาของทุกตัวเลขบนหน้าจอ", "การโฮสต์ และแผนพัฒนาต่อ"], VIOLET)
notes(s, "เข้า part ที่สอง: การนำเสนอ — ทีละหน้า")

# =========================================================
# 12 · ROLES
# =========================================================
s = slide()
header(s, "02 · การนำเสนอข้อมูล", "ใครเห็นอะไร — สิทธิ์ตามบทบาท (Role-based)", VIOLET)
flow = [("Login", "auth.js"), ("Role", "6 บทบาท"), ("เมนู", "router.renderNav"), ("หน้า", "views/*.html"), ("ข้อมูล", "RAW_Data/*.csv")]
xw = (CW - 4 * 0.42) / 5
for i, (a, b) in enumerate(flow):
    x = ML + i * (xw + 0.42)
    rect(s, x, 1.8, xw, 0.86, fill=WHITE, line=VIOLET, radius=0.06)
    txt(s, x + 0.12, 1.92, xw - 0.24, 0.26, a, size=11, bold=True, color=VIOLET, align=PP_ALIGN.CENTER)
    txt(s, x + 0.12, 2.22, xw - 0.24, 0.26, b, size=8.6, color=MUTED, align=PP_ALIGN.CENTER)
    if i < 4:
        ar = s.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(x + xw + 0.09), Inches(2.12), Inches(0.24), Inches(0.22))
        ar.fill.solid(); ar.fill.fore_color.rgb = RGBColor(0xCB, 0xD5, 0xE1)
        ar.line.fill.background(); ar.shadow.inherit = False

rows = [
    ["admin", "8 หน้า — ภาพรวม + กลุ่ม A/B/C/D/R + สต็อก + เศรษฐกิจ/BOI", "ใช้เป็นบัญชีกลางของทีม (ล็อกอินอัตโนมัติ)"],
    ["group_a … group_r", "กลุ่มของตัวเอง + สต็อก + เศรษฐกิจ/BOI", "หัวหน้ากลุ่มเห็นเฉพาะยอดกลุ่มตน"],
    ["หน้า Open Quotations", "ล็อกกลุ่มอัตโนมัติตาม role", "หัวหน้ากลุ่มเห็นเฉพาะดีลค้างของกลุ่มตัวเอง"],
]
table(s, ML, 3.0, CW, ["บัญชี / สิทธิ์", "หน้าที่เข้าถึงได้", "หมายเหตุการใช้งาน"], rows,
      [2.35, 5.05, 4.52], row_h=0.62, head_h=0.36, size=9.8, bold_first=True)

rect(s, ML, 5.42, CW, 1.42, fill=RGBColor(0xFE, 0xF9, 0xEC), line=RGBColor(0xFD, 0xE6, 0x8A), radius=0.05)
txt(s, ML + 0.24, 5.54, CW - 0.48, 0.26, "ข้อควรรู้เรื่องความปลอดภัย", size=10.5, bold=True, color=RGBColor(0x92, 0x40, 0x0E))
txt(s, ML + 0.24, 5.86, CW - 0.48, 0.9,
    "การล็อกอินทำที่ฝั่งเบราว์เซอร์ (js/auth.js) — รหัสอยู่ในไฟล์ที่ใครเปิด View Source ก็เห็น "
    "จึงใช้เพื่อ “แบ่งหน้าจอตามบทบาท” ไม่ใช่กำแพงป้องกันข้อมูล\n"
    "ชั้นป้องกันจริงต้องมาจากเครือข่าย: เปิดเฉพาะใน Tailscale / LAN หรือใส่ Cloudflare Access หน้าเว็บ",
    size=9.4, color=RGBColor(0x92, 0x40, 0x0E), line=1.35)
footer(s, 12, "ที่มา: Dashboard_App/js/auth.js · router.js · open_quotes.js")
notes(s, "พูดตรง ๆ เรื่อง auth: ตอนนี้เป็น client-side ใช้แบ่ง view ได้ แต่ไม่ใช่ความปลอดภัยจริง "
         "ถ้าจะเปิดให้คนนอกบริษัทใช้ ต้องมีชั้น network หรือ Cloudflare Access")

# =========================================================
# 13 · PAGE 1 EPS OVERVIEW
# =========================================================
s = slide()
header(s, "02 · การนำเสนอข้อมูล · หน้า 1/4", "EPS Overview — ภาพรวมทั้งธุรกิจ (หน้าแรกที่ทุกคนเห็น)", VIOLET)
txt(s, ML, 1.72, 6.4, 0.26, "มีอะไรบนหน้านี้", size=11, bold=True, color=INK)
bullets(s, ML, 2.06, 6.15, 1.7, [
    ("KPI 4 ใบ ", "— Revenue YTD · จำนวน SO · ลูกค้าที่ยังซื้อ · Hot Jobs"),
    ("กราฟ 5 กลุ่ม ", "— ยอดจริงเทียบเป้าแผนปี 2026"),
    ("กราฟสะสม ", "— Revenue สะสมรายเดือนเทียบเส้นเป้า (คำนวณสดจาก 3_SO_Data)"),
    ("AI Action Plan ", "— ระบบสร้างข้อเสนอเชิงปฏิบัติจากช่องว่างเป้า + สถานะดีล"),
    ("Hot Jobs ", "— ดีล Pending ที่มีโอกาส ≥ 70% รวม 176 ดีล / 72.02 M"),
], size=9.6, gap=6, bullet_color=VIOLET)


def kpi_tile(x, y, w, h, title, big, unit, col):
    rect(s, x, y, w, h, fill=WHITE, line=BORDER)
    rect(s, x, y + 0.02, 0.055, h - 0.04, fill=col, shape=MSO_SHAPE.RECTANGLE)
    txt(s, x + 0.22, y + 0.13, w - 0.4, 0.24, title, size=9.5, bold=True, color=MUTED)
    txt(s, x + 0.22, y + 0.4, 1.45, 0.42, big, size=21, bold=True, color=col)
    txt(s, x + 1.5, y + 0.44, w - 1.72, 0.44, unit, size=8.6, color=MUTED, line=1.2)


tiles = [("Revenue YTD (2026)", "174.98", "M THB · เป้า 453.55 M = 39%", BLUE),
         ("Sales Orders", "1,057", "ใบ · ปี 2026", SKY),
         ("Active Customers", "359", "ราย", TEAL),
         ("Hot Jobs", "72.02", "M THB · 176 ดีล", AMBER)]
tw = (6.15 - 0.16) / 2
for i, (t, b, u, c) in enumerate(tiles):
    kpi_tile(ML + (i % 2) * (tw + 0.16), 3.62 + (i // 2) * 1.0, tw, 0.9, t, b, u, c)
txt(s, ML, 5.72, 6.15, 0.6, "ที่มาของตัวเลข: 0_EPS_Overview_2026.csv (สร้างโดย build_overview.py) + 3_SO_Data.csv + 0_EPS_HotJobs_2026.csv",
    size=8.6, color=MUTED, line=1.25)

wire(s, 7.15, 1.76, 5.42, 4.5, [
    (0.14, 0.16, 2.45, 0.2, "EPS OVERVIEW — FY 2026", "panel"),
    (0.14, 0.44, 1.2, 0.62, "KPI", "kpi"), (1.42, 0.44, 1.2, 0.62, "KPI", "kpi"),
    (2.7, 0.44, 1.2, 0.62, "KPI", "kpi"), (3.98, 0.44, 1.3, 0.62, "KPI", "kpi"),
    (0.14, 1.18, 2.6, 1.55, "กราฟ 5 กลุ่ม: actual vs target", "chart"),
    (2.86, 1.18, 2.42, 1.55, "กราฟสะสม vs เป้า", "chart"),
    (0.14, 2.85, 5.14, 1.5, "AI Action Plan (ข้อเสนอเชิงปฏิบัติ)", "panel"),
], label_size=8)
footer(s, 13, "ภาพจำลองเลย์เอาต์ (wireframe) — หน้าจริงมีตัวเลขและกราฟจริงตามข้อมูล CSV")
notes(s, "หน้าแรกที่ทุกคนเห็น: KPI 4 ใบ + กราฟ 5 กลุ่ม + กราฟสะสม + AI Action Plan "
         "ตัวเลข 174.98 จากเป้า 453.55 = 39% — คือช่องว่างที่ต้องปิด")

# =========================================================
# 14 · PAGE 2 GROUPS
# =========================================================
s = slide()
header(s, "02 · การนำเสนอข้อมูล · หน้า 2/4", "Group A / B / C / D / R — เจาะลึกรายกลุ่มขาย", VIOLET)
txt(s, ML, 1.7, 6.4, 0.26, "KPI 4 ใบต่อกลุ่ม (ตัวอย่าง: กลุ่ม A)", size=11, bold=True, color=INK)
kpi_row(s, 2.0, [
    ("Revenue 12 เดือน", "24.34", "M THB · เป้า 73.85 M · ขาด 49.51 M", None, SKY),
    ("Active Accounts", "138", "จาก 472 · โรงงาน >100M ที่ครอบคลุม 143/940", None, TEAL),
    ("Win Rate", "82.0%", "นับจำนวน / 64.4% นับมูลค่า", None, VIOLET),
], h=1.62, x0=ML, total=6.15)
card(s, ML, 3.78, 6.15, 1.05, "Open Quotations (กลุ่ม A)", "623",
     "ดีลค้าง · ใบเก่าสุด 742 วัน · กดเข้าไปดู aging ได้", accent=AMBER)
txt(s, ML, 5.02, 6.15, 0.26, "เจาะลึกได้ 4 ชั้น (drill-down)", size=10.5, bold=True, color=INK)
bullets(s, ML, 5.32, 6.15, 1.6, [
    ("Top 10 accounts ต่อพนักงานขาย ", "— เรียงตามยอด พร้อมจังหวัด/อุตสาหกรรม/จำนวนเยี่ยม"),
    ("รายชื่อลูกค้าทั้งกลุ่ม ", "— สถานะ active/idle, ยอด 12 เดือน, วันสั่งซื้อล่าสุด"),
    ("ใบเสนอราคาค้าง ", "— เรียงตามอายุ พร้อมโอกาสปิด"),
    ("SO & กำหนดส่ง + To-Do ที่ระบบแนะนำ ", "— งานที่ควรทำก่อนในกลุ่มนี้"),
], size=9.4, gap=6, bullet_color=VIOLET)
wire(s, 7.15, 1.76, 5.42, 4.6, [
    (0.14, 0.16, 3.4, 0.2, "GROUP A OVERVIEW", "panel"),
    (0.14, 0.44, 1.28, 0.56, "KPI", "kpi"), (1.54, 0.44, 1.28, 0.56, "KPI", "kpi"),
    (2.94, 0.44, 1.28, 0.56, "KPI", "kpi"), (4.34, 0.44, 0.94, 0.56, "KPI", "kpi"),
    (0.14, 1.1, 2.5, 1.2, "ตาราง Top 10 — Rep 1", "table"),
    (2.78, 1.1, 2.5, 1.2, "ตาราง Top 10 — Rep 2", "table"),
    (0.14, 2.42, 2.5, 1.0, "ใบเสนอราคาค้าง (aging)", "table"),
    (2.78, 2.42, 2.5, 1.0, "SO / กำหนดส่ง", "table"),
    (0.14, 3.54, 5.14, 0.9, "To-Do ที่ระบบแนะนำ (18 รายการ)", "panel"),
], label_size=8)
footer(s, 14, "กลุ่ม: A Feed & Agri · B Chem & Wastewater · C Cosmetic/Pharma/Rubber · D Oil&Gas/Power · R Rayong/Eastern Hub")
notes(s, "ทั้ง 5 กลุ่มใช้เลย์เอาต์เดียวกัน ต่างกันที่ข้อมูล — ตัวอย่างกลุ่ม A: 24.34 จากเป้า 73.85 "
         "จุดขายของหน้านี้คือ drill-down 4 ชั้น ลงไปถึงรายลูกค้าและรายดีล")

# =========================================================
# 15 · PAGE 3 STOCK
# =========================================================
s = slide()
header(s, "02 · การนำเสนอข้อมูล · หน้า 3/4", "Stock & Product Management — สต็อกและ Dead Stock", VIOLET)
kpi_row(s, 1.78, [
    ("มูลค่าสต็อกรวม (Sale Sheet)", "16.73", "M THB · 453 รายการ", None, BLUE),
    ("Dead Stock (> 3 ปี)", "4.44", "M THB · 195 รายการ = 26.5% ของมูลค่า", None, RED),
], h=1.36, x0=ML, total=6.15, big_size=22)
txt(s, ML, 3.32, CW, 0.26, "อ่านอย่างไร", size=11, bold=True, color=INK)
bullets(s, ML, 3.62, 6.0, 2.6, [
    ("ตัวกรอง 3 ชั้น ", "— แบรนด์ · สถานะ (ทั้งหมด/เฉพาะ dead) · ค้นหา code หรือคำอธิบาย"),
    ("ตาราง ", "— Brand, Code, Description, Qty, มูลค่ารวม, Type, Status (สีแดง = dead)"),
    ("สถานะจริงที่พบ ", "— For Sell · Aging Monitor · Dead Stock · ว่าง"),
    ("ใช้ตัดสินใจ ", "— ของที่ควรระบายก่อน / สินค้าที่ควรหยุดสั่งเพิ่ม"),
    ("ต้นทาง ", "— Google Sheets PM Master (Sale tab) → etl_script.py + clean_inventory.py"),
], size=9.6, gap=8, bullet_color=VIOLET)
wire(s, 7.15, 1.76, 5.42, 4.6, [
    (0.14, 0.16, 3.6, 0.2, "STOCK & PM", "panel"),
    (0.14, 0.44, 2.5, 0.6, "KPI มูลค่าสต็อก", "kpi"), (2.78, 0.44, 2.5, 0.6, "KPI dead stock", "kpi"),
    (0.14, 1.14, 1.2, 0.34, "แบรนด์", "filter"), (1.44, 1.14, 1.2, 0.34, "สถานะ", "filter"),
    (2.74, 1.14, 2.54, 0.34, "ค้นหา", "filter"),
    (0.14, 1.6, 5.14, 2.84, "ตารางสินค้า 453 รายการ (เลื่อน/เรียงได้)", "table"),
], label_size=8)
footer(s, 15, "ตัวเลขคำนวณจาก 5_Inventory_Supplier.csv ณ 19 ต.ค. 2569 (Total price)")
notes(s, "หน้าสต็อก: 16.73 ล้าน มูลค่ารวม โดย 4.44 ล้าน (195 รายการ) เป็น dead stock เกิน 3 ปี "
         "ตัวกรอง 3 ชั้นทำให้เซลส์หาของที่ลูกค้าถามได้เร็ว")

# =========================================================
# 16 · PAGE 4 ECONOMIC + OPEN QUOTES
# =========================================================
s = slide()
header(s, "02 · การนำเสนอข้อมูล · หน้า 4/4", "Economic & BOI/DBD และ Open Quotations Pipeline", VIOLET)
kpi_row(s, 1.74, [
    ("MPI Index", "94.80", "+0.46% YoY", None, SKY),
    ("Capacity Utilization", "129", "เซกเตอร์", None, AMBER),
    ("BOT Policy Rate", "1.00%", "กนง. 4/2569", None, GREEN),
    ("Private Capex", "+13.4%", "Q2/2569", None, VIOLET),
], h=1.3, x0=ML, total=5.95, big_size=19, title_size=9.6)
txt(s, ML, 3.2, 5.95, 0.26, "บนหน้านี้ยังมี", size=10.5, bold=True, color=INK)
bullets(s, ML, 3.52, 5.9, 2.0, [
    ("กราฟ CapU 12 เซกเตอร์สูงสุด ", "— ดูว่าอุตสาหกรรมไหนเดินเครื่องหนัก"),
    ("BOI Investment Radar ", "— 24 โครงการ พร้อมบริษัท/โซน/มูลค่าลงทุน"),
    ("DBD coverage ", "— จับคู่ลูกค้ากับทะเบียนโรงงานได้กี่ % กี่ราย"),
    ("คลิกอุตสาหกรรม → รายชื่อโรงงาน ", "— สีเขียว = เคยเข้าไปพบแล้ว (join กับ Visit)"),
], size=9.4, gap=6, bullet_color=VIOLET)
rect(s, ML, 5.24, 5.95, 1.3, fill=BLUE_L, line=RGBColor(0xBF, 0xDB, 0xFE), radius=0.05)
txt(s, ML + 0.2, 5.36, 5.55, 0.26, "Open Quotations Pipeline (17_Open_Quotes.csv)", size=10, bold=True, color=BLUE)
txt(s, ML + 0.2, 5.68, 5.55, 0.76,
    "1,059 ดีลค้าง · กรองตามกลุ่ม/ค้นหา · คอลัมน์: Quote ID, บริษัท, เซลส์, มูลค่า, โอกาสปิด, วันคาดสั่ง, aging",
    size=9, color=INK, line=1.3)
wire(s, 6.95, 1.74, 5.62, 4.6, [
    (0.14, 0.16, 3.4, 0.2, "ECONOMIC & BOI/DBD", "panel"),
    (0.14, 0.44, 1.18, 0.56, "KPI", "kpi"), (1.4, 0.44, 1.18, 0.56, "KPI", "kpi"),
    (2.66, 0.44, 1.18, 0.56, "KPI", "kpi"), (3.92, 0.44, 1.36, 0.56, "KPI", "kpi"),
    (0.14, 1.1, 5.14, 1.1, "กราฟ Capacity Utilization รายเซกเตอร์", "chart"),
    (0.14, 2.3, 2.5, 1.05, "ตาราง BOI 24 โครงการ", "table"),
    (2.78, 2.3, 2.5, 1.05, "DBD by industry (คลิกได้)", "table"),
    (0.14, 3.45, 5.14, 1.0, "เจาะรายชื่อโรงงานในอุตสาหกรรม (เขียว = เคยเข้าพบ)", "panel"),
], label_size=8)
footer(s, 16, "ที่มา: 6_Macroeconomic_Data.csv · 7_BOI_Data.csv · 8_DBD_Data.csv · 4_Visit_Report.csv · 17_Open_Quotes.csv")
notes(s, "หน้านี้เชื่อม 'ภายนอก' กับ 'ภายใน': เศรษฐกิจมหภาค + โครงการ BOI + ทะเบียนโรงงาน "
         "แล้วคลิกดูได้ว่าโรงงานเหล่านั้นเราเคยเข้าไปพบหรือยัง — เป็นมุมหาลูกค้าใหม่")

# =========================================================
# 17 · PAGE ↔ FILE MAP
# =========================================================
s = slide()
header(s, "02 · การนำเสนอข้อมูล", "แผนที่ “หน้า ↔ ไฟล์ข้อมูล” — ตรวจย้อนได้ทุกตัวเลข", VIOLET)
rows = [
    ["🏢 EPS Overview", "0_EPS_Overview_2026 · 0_EPS_HotJobs_2026 · 3_SO_Data", "Revenue vs plan · SO · active customers · hot jobs · กราฟสะสม"],
    ["📊 Group A–D/R", "12_Group_KPI · 13_Rep_Performance · 14_Client_Detail · 15_SO_Delivery · 16_Todo · 17_Open_Quotes · 0_EPS_Overview",
     "Revenue 12m · active accounts · win rate · open quotes · drill-down"],
    ["📦 Stock & PM", "5_Inventory_Supplier", "มูลค่าสต็อก · dead stock · ตาราง/ตัวกรอง"],
    ["📈 Economic & BOI/DBD", "6_Macroeconomic_Data · 7_BOI_Data · 8_DBD_Data · 4_Visit_Report", "MPI · CapU · ดอกเบี้ย · capex · BOI · DBD coverage"],
    ["🧾 Open Quotations", "17_Open_Quotes", "ดีลค้าง · โอกาสปิด · aging · กรองตามกลุ่ม"],
]
table(s, ML, 1.76, CW, ["หน้าแดชบอร์ด", "ไฟล์ที่อ่าน", "สิ่งที่แสดง"], rows,
      [2.3, 5.2, 4.42], row_h=0.66, head_h=0.4, size=8.8, bold_first=True)
rect(s, ML, 5.5, CW, 1.32, fill=LIGHT, line=BORDER, radius=0.05)
txt(s, ML + 0.24, 5.62, CW - 0.48, 0.26, "อ่านผังนี้อย่างไร", size=10, bold=True, color=INK)
txt(s, ML + 0.24, 5.92, CW - 0.48, 0.8,
    "ทุกหน้าโหลด CSV ตรงจากโฟลเดอร์ RAW_Data/ ผ่าน fetch (มี ?t=timestamp กัน cache ค้าง) → แปลงด้วย csv-parser.js → วาดกราฟด้วย Chart.js\n"
    "ไม่มีตัวเลขฝังในโค้ดหน้าเว็บ ดังนั้น “แก้ข้อมูลที่ไฟล์” = “หน้าจอเปลี่ยนตาม” ไม่ต้องแก้โค้ด",
    size=9.2, color=INK, line=1.35)
footer(s, 17, "ตรวจได้เอง: เปิด Dashboard_App/js/*.js แล้วค้นชื่อไฟล์ CSV ที่หน้าเหล่านั้นอ่าน")
notes(s, "สไลด์นี้คือคำตอบของคำถาม 'ตัวเลขนี้มาจากไหน' — ทุกหน้าอ่านไฟล์ที่ระบุไว้ ไม่มีค่าฮาร์ดโค้ด")

# =========================================================
# 18 · HOSTING
# =========================================================
s = slide()
header(s, "04 · คุณภาพข้อมูล & การให้บริการ", "ระบบรันอยู่ที่ไหน และป้องกันข้อมูลอย่างไร", AMBER)
rect(s, ML, 1.76, (CW - 0.3) / 2, 3.1, fill=WHITE, line=BORDER, radius=0.04)
txt(s, ML + 0.26, 1.9, 5.4, 0.3, "แบบที่ใช้อยู่: NAS เสิร์ฟทั้งแอปและข้อมูล", size=11.5, bold=True, color=BLUE)
bullets(s, ML + 0.26, 2.28, (CW - 0.3) / 2 - 0.52, 2.4, [
    ("ตัวให้บริการ ", "scripts/serve_raw_data.py (Python stdlib, ไม่ต้องติดตั้งอะไร)"),
    ("เข้าได้ 2 ทาง ", "LAN 192.168.1.5:8090 · public URL ผ่าน Tailscale Funnel"),
    ("ข้อดี ", "ข้อมูลลูกค้าไม่ออกจากบริษัท · origin เดียว ไม่มีปัญหา CORS"),
    ("ข้อแลก ", "ถ้า NAS หรือเน็ตออฟฟิศล่ม ทุกคนเข้าไม่ได้"),
], size=9.4, gap=8, bullet_color=BLUE)

rect(s, ML + (CW - 0.3) / 2 + 0.3, 1.76, (CW - 0.3) / 2, 3.1, fill=WHITE, line=BORDER, radius=0.04)
txt(s, ML + (CW - 0.3) / 2 + 0.56, 1.9, 5.4, 0.3, "แบบทางเลือก: GitHub Pages + NAS (เฉพาะข้อมูล)", size=11.5, bold=True, color=TEAL)
bullets(s, ML + (CW - 0.3) / 2 + 0.56, 2.28, (CW - 0.3) / 2 - 0.52, 2.4, [
    ("ตัวเว็บ ", "GitHub Pages (static, ไม่มีข้อมูลลูกค้า)"),
    ("ข้อมูล ", "NAS + serve_raw_data.py (CORS เฉพาะ origin ของแดชบอร์ด)"),
    ("ตั้งค่า ", "Dashboard_App/js/config.js → window.EPS_DATA_BASE = 'https://…/' "),
    ("ข้อควรระวัง ", "RAW_Data เคยถูก push ขึ้น repo สาธารณะ — การลบไม่ลบประวัติ"),
], size=9.4, gap=8, bullet_color=TEAL)

txt(s, ML, 5.02, CW, 0.26, "สิ่งที่ตัวให้บริการไฟล์บล็อกไว้ให้อัตโนมัติ", size=10.5, bold=True, color=INK)
blocks = [("_CORE_Private/", "credential CRM"), (".git/", "ประวัติ repo"), ("*.py · *.md · *.log", "ไฟล์งาน/บันทึก"),
          ("path traversal", "../ นอกโฟลเดอร์"), ("directory listing", "ไม่แสดงรายชื่อไฟล์")]
xw = (CW - 4 * 0.16) / 5
for i, (a, b) in enumerate(blocks):
    x = ML + i * (xw + 0.16)
    rect(s, x, 5.34, xw, 0.72, fill=RGBColor(0xFE, 0xF2, 0xF2), line=RGBColor(0xFE, 0xCA, 0xCA), radius=0.05)
    txt(s, x + 0.12, 5.42, xw - 0.24, 0.26, "✕ " + a, size=8.8, bold=True, color=RED)
    txt(s, x + 0.12, 5.68, xw - 0.24, 0.26, b, size=8.2, color=MUTED)
rect(s, ML, 6.2, CW, 0.68, fill=RGBColor(0xFE, 0xF9, 0xEC), line=RGBColor(0xFD, 0xE6, 0x8A), radius=0.05)
txt(s, ML + 0.2, 6.3, CW - 0.4, 0.5,
    "ข้อสรุป: ข้อมูลอ่อนไหวควรอยู่ในบริษัท (NAS) — ถ้าต้องเปิดให้เข้าจากที่ไหนก็ได้โดยไม่ติดตั้งอะไร ต้องมี public URL (Tailscale Funnel / Cloudflare Tunnel) — ยังไงก็ต้องมีชั้น network กันหน้าเว็บ",
    size=9.2, color=RGBColor(0x92, 0x40, 0x0E), line=1.3)
footer(s, 18, "ที่มา: DATA_HOSTING_Synology.md · deploy/synology/README.md · scripts/serve_raw_data.py")
notes(s, "คำถามที่พบบ่อย: ข้อมูลปลอดภัยไหม — ตอนนี้ข้อมูลอยู่ใน NAS ของบริษัท ตัวไฟล์เสิร์ฟมี allowlist บล็อกโฟลเดอร์ลับ "
         "แต่ auth ของแอปยังเป็น client-side จึงควรจำกัดการเข้าถึงที่ระดับเครือข่าย")

# =========================================================
# 19 · SUMMARY + ROADMAP
# =========================================================
s = slide()
header(s, "สรุป", "สามบรรทัดที่ต้องจำ + สิ่งที่ควรทำต่อ", AMBER)
summary = [
    ("เก็บ ", "— 4 ระบบต้นทาง → 24 สคริปต์ → CSV 3 ชั้น (19 ไฟล์, ≈96,000 แถว) ตาม cron วันละ 2 รอบ"),
    ("นำเสนอ ", "— 8 หน้า แยกตาม 6 บทบาท; KPI/กราฟ/ตาราง ทุกค่าคำนวณสดจาก CSV ไม่มีค่าฮาร์ดโค้ด"),
    ("ตรวจย้อน ", "— ทุกหน้าบอกไฟล์ต้นทาง และทุกไฟล์บอกระบบที่มา; ข้อจำกัด (U 82.8 M, DBD 30%) ระบุชัด"),
]
y = 1.76
for lead, rest in summary:
    rect(s, ML, y, CW, 0.78, fill=WHITE, line=BORDER)
    txt(s, ML + 0.24, y + 0.2, 1.5, 0.34, lead, size=12, bold=True, color=BLUE)
    txt(s, ML + 1.78, y + 0.22, CW - 2.0, 0.5, rest, size=9.8, color=INK, line=1.2)
    y += 0.9

txt(s, ML, 4.5, CW, 0.26, "แผนพัฒนาต่อ (เรียงตามผลกระทบ)", size=11, bold=True, color=INK)
road = [
    ("1", "เติม industry ที่ขาดใน CRM", "ลดยอดกลุ่ม U 82.80 M ให้เข้ากลุ่มจริง"),
    ("2", "join CRM Contacts", "ได้ผู้ติดต่อ/เบอร์โทรใน Client Master"),
    ("3", "Auth จริงก่อนเปิด public", "Cloudflare Access / Basic Auth ที่ตัวเสิร์ฟ"),
    ("4", "หน้า Win/Loss", "ต้องเริ่มเก็บเหตุผลชนะ/แพ้ใน CRM ก่อน"),
    ("5", "แจ้งเตือนเชิงรุก", "LINE/อีเมลเมื่องานค้างเกิน 90 วัน"),
]
xw = (CW - 4 * 0.16) / 5
for i, (n, t, d) in enumerate(road):
    x = ML + i * (xw + 0.16)
    rect(s, x, 4.84, xw, 1.86, fill=WHITE, line=BORDER, radius=0.05)
    txt(s, x + 0.16, 4.95, xw - 0.3, 0.3, n, size=18, bold=True, color=AMBER)
    txt(s, x + 0.16, 5.32, xw - 0.3, 0.62, t, size=9.6, bold=True, color=INK, line=1.2)
    txt(s, x + 0.16, 5.98, xw - 0.3, 0.64, d, size=8.6, color=MUTED, line=1.25)
footer(s, 19, "Roadmap มาจากข้อจำกัดที่ระบุในสไลด์ 10 — ทุกรายการอ้างอิงได้จากเอกสารในโฟลเดอร์งาน")
notes(s, "ปิดด้วย 3 บรรทัดและ 5 สิ่งที่ทำต่อ — ถ้าต้องเลือกทำอย่างเดียว เลือกข้อ 1 เพราะกระทบตัวเลขมากที่สุด")

# =========================================================
# 20 · CLOSING
# =========================================================
s = slide()
rect(s, 0, 0, SW, SH, fill=INK, shape=MSO_SHAPE.RECTANGLE)
rect(s, 0, 0, SW, 0.12, fill=SKY, shape=MSO_SHAPE.RECTANGLE)
txt(s, ML, 1.7, 8.0, 0.3, "ขอบคุณ", size=13, bold=True, color=SKY)
txt(s, ML, 2.05, 9.5, 0.9, "คำถาม / ข้อเสนอแนะ", size=40, bold=True, color=WHITE)
txt(s, ML, 3.1, 9.8, 0.6, "เอกสารอ้างอิงทั้งหมดอยู่ในโฟลเดอร์ “AI Dashboard”", size=13, color=RGBColor(0x94, 0xA3, 0xB8))
refs = [("README.md", "ภาพรวมโปรเจกต์ + ความถูกต้องของข้อมูล"),
        ("Data_Dictionary_and_Schedule.md", "คอลัมน์จริงของทุกไฟล์ + ตาราง ETL"),
        ("app_architecture.md", "โครงสร้างแอป/Renderer แต่ละหน้า"),
        ("DATA_HOSTING_Synology.md", "การโฮสต์ข้อมูลบน NAS + ความปลอดภัย"),
        ("deploy/synology/README.md", "คู่มือติดตั้งบน NAS ทีละขั้น")]
y = 4.0
for a, b in refs:
    txt(s, ML, y, 3.9, 0.26, a, size=10, bold=True, color=SKY)
    txt(s, ML + 4.0, y, 6.0, 0.26, b, size=9.6, color=RGBColor(0xCB, 0xD5, 0xE1))
    y += 0.34
rect(s, ML, 5.9, 6.0, 0.02, fill=RGBColor(0x33, 0x41, 0x55), shape=MSO_SHAPE.RECTANGLE)
txt(s, ML, 6.06, 10.0, 0.3, "EPS Business Unit · Siam Raj Public Company Limited · ตุลาคม 2569",
    size=9.6, color=RGBColor(0x64, 0x74, 0x8B))
notes(s, "ปิดการนำเสนอ — ชี้ให้ดูว่าเอกสารอ้างอิงอยู่ในโฟลเดอร์งานเดียวกันทั้งหมด ใครอยากตรวจต่อทำได้เลย")

# ---------------- save ----------------
out_dir = os.path.dirname(os.path.abspath(__file__))
out = os.path.join(out_dir, "EPS_Dashboard_Data_and_Presentation_TH.pptx")
prs.save(out)
print("saved:", out)
print("slides:", len(prs.slides.__iter__.__self__._sldIdLst))
