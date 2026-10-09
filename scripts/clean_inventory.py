#!/usr/bin/env python3
"""Clean RAW_Data/5_Inventory_Supplier.csv (PM Master "Sale" tab export).

The Google-Sheets CSV export carries two artefacts:
  1. the last header cell contains an embedded newline ("For \npump model")
  2. hundreds of padding rows at the bottom with only Qty=0 / Total price=0.00

This script normalises the header and drops rows that carry no item identity
(no Products, no CODE, no Description and no value). Real data is never altered.
A timestamped copy is written next to the file before the first change.
"""
import csv, os, shutil, sys, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RAW = os.path.join(ROOT, "RAW_Data")
SRC = os.path.join(RAW, "5_Inventory_Supplier.csv")


def main():
    rows = list(csv.reader(open(SRC, encoding="utf-8")))
    header, body = rows[0], rows[1:]
    header = [h.replace("\n", " ").strip() for h in header]

    kept, dropped = [], 0
    for r in body:
        r = (r + [""] * len(header))[: len(header)]
        ident = [r[0], r[1], r[2]] if len(r) > 2 else r[:2]
        has_id = any(x.strip() for x in ident)
        has_val = len(r) > 5 and r[5].strip() not in ("", "0", "0.00")
        if has_id or has_val:
            kept.append(r)
        else:
            dropped += 1

    if dropped:
        bak = SRC + ".bak_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        shutil.copyfile(SRC, bak)
        print("backup ->", bak)

    with open(SRC, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(kept)

    print("header fixed:", header[-1])
    print("rows kept: %d | padding rows dropped: %d -> %s" % (len(kept), dropped, SRC))


if __name__ == "__main__":
    main()
