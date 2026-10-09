#!/usr/bin/env python3
"""Build RAW_Data/7_BOI_Data.csv from the BOI monthly workbook.

Source workbook: BOI_Projects_September_2026.xlsx (4 sheets, Aug-Sep 2026).
Values in the workbook are already in million THB, matching `investment_value_m`.

Reads .xlsx with the standard library only (zipfile + ElementTree).
"""
import csv, os, re, sys, xml.etree.ElementTree as ET
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RAW = os.path.join(ROOT, "RAW_Data")
SRC = os.path.join(ROOT, "_CORE_Private", "BOI_Projects_September_2026.xlsx")
OUT = os.path.join(RAW, "7_BOI_Data.csv")

NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
RNS = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
PKG = "{http://schemas.openxmlformats.org/package/2006/relationships}"


def col_index(ref):
    letters = re.match(r"([A-Z]+)", ref or "A").group(1)
    n = 0
    for ch in letters:
        n = n * 26 + (ord(ch) - 64)
    return n - 1


def read_xlsx(path):
    """Return {sheet_name: [[cell, ...], ...]} in workbook order."""
    z = zipfile.ZipFile(path)
    shared = []
    if "xl/sharedStrings.xml" in z.namelist():
        root = ET.fromstring(z.read("xl/sharedStrings.xml"))
        for si in root.findall(NS + "si"):
            shared.append("".join(t.text or "" for t in si.iter(NS + "t")))
    rels = {}
    rroot = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
    for rel in rroot:
        rels[rel.get("Id")] = rel.get("Target")
    wb = ET.fromstring(z.read("xl/workbook.xml"))
    sheets = {}
    for sh in wb.iter(NS + "sheet"):
        name = sh.get("name")
        target = rels.get(sh.get(RNS + "id"), "").lstrip("/")
        if not target.startswith("xl/"):
            target = "xl/" + target
        root = ET.fromstring(z.read(target))
        rows = []
        for row in root.iter(NS + "row"):
            cells = []
            for c in row.findall(NS + "c"):
                idx = col_index(c.get("r"))
                while len(cells) <= idx:
                    cells.append("")
                t = c.get("t")
                v = c.find(NS + "v")
                if t == "s" and v is not None:
                    val = shared[int(v.text)]
                elif t == "inlineStr":
                    val = "".join(x.text or "" for x in c.iter(NS + "t"))
                else:
                    val = v.text if v is not None else ""
                cells[idx] = (val or "").strip()
            rows.append(cells)
        sheets[name] = rows
    return sheets


def num(s):
    m = re.search(r"([\d,]+(?:\.\d+)?)", str(s or "").replace("\u00a0", " "))
    return float(m.group(1).replace(",", "")) if m else ""


def main():
    src = SRC if os.path.exists(SRC) else sys.argv[1]
    sheets = read_xlsx(src)
    period = "2026-09"
    rows_out = []
    seq = 0

    def add(sheet, company, industry, detail, zone, value, note=""):
        nonlocal seq
        seq += 1
        rows_out.append(["BOI-%s-%02d" % (period.replace("-", ""), seq), company, industry,
                         detail, value, zone, period, "Approved", sheet, note])

    for name, rows in sheets.items():
        body = rows[1:] if rows else []
        if name.startswith("Strategic"):
            for r in body:
                if len(r) < 5 or not r[0]:
                    continue
                add(name, r[0], r[1], r[2], r[3], num(r[4]), "BOI board approval")
        elif name.startswith("Electronics"):
            for r in body:
                if len(r) < 4 or not r[0]:
                    continue
                add(name, r[0], r[1], r[2], r[3], "", "no investment value published")
        elif name.startswith("Biotech"):
            for r in body:
                if len(r) < 4 or not r[0]:
                    continue
                add(name, r[0], r[1], r[2], r[3], num(r[3]), "measure / fund")
        elif name.startswith("August"):
            for r in body:
                if len(r) < 4 or not r[0]:
                    continue
                add(name, r[0], r[1], r[2], r[3], num(r[3]), "monthly performance")

    with open(OUT, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["project_id", "company_name", "industry_type", "project_detail",
                    "investment_value_m", "zone", "approval_period", "status",
                    "source_sheet", "note"])
        w.writerows(rows_out)

    print("BOI rows: %d -> %s" % (len(rows_out), OUT))
    tot = sum(r[4] for r in rows_out if isinstance(r[4], float))
    print("sum of published values: %,.2f M THB".replace("%,", "%,") % tot if False else
          "sum of published values: {:,.2f} M THB".format(tot))


if __name__ == "__main__":
    main()
