#!/usr/bin/env python3
"""Build RAW_Data/6_Macroeconomic_Data.csv from real published sources.

Sources
  * Capacity utilisation by sector : OIE (สศอ.) monthly CapU export
        source copy kept at _CORE_Private/Capacity_Utilization_<yyyymm>.csv
        columns: id, TSIC, name, weight, year, month, cap_u_pct
  * Headline MPI index / YoY    : OIE press release, July 2026
  * Policy rate                 : BOT MPC 4/2569 (26 Aug 2026) = 1.00 % p.a.
  * Private investment growth   : NESDC/BOT Q2 2026 = +13.4 % YoY

MPI *index per sector* is not published in the CapU export, so `mpi_index`
stays blank for sector rows (never invented) and is only filled on the
ALL_INDUSTRY row where the official headline number is known.
"""
import csv, glob, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RAW = os.path.join(ROOT, "RAW_Data")
CORE = os.path.join(ROOT, "_CORE_Private")


def newest_src():
    """ไฟล์ Capacity_Utilization_<YYYYMM>.csv ที่ใหม่ที่สุด (สร้างโดย update_capu_from_oie.py)"""
    files = sorted(glob.glob(os.path.join(CORE, "Capacity_Utilization_[0-9][0-9][0-9][0-9][0-9][0-9].csv")))
    return files[-1] if files else os.path.join(CORE, "Capacity_Utilization_202607.csv")


SRC = newest_src()
OUT = os.path.join(RAW, "6_Macroeconomic_Data.csv")

BOT_RATE = 1.00            # % p.a.
PRIVATE_CAPEX = 13.4       # % YoY, Q2 2026
MPI_INDEX = 94.80          # headline (OIE press release) — ค่าคงที่จนกว่าจะดึง MPI จากไฟล์ สศอ.
MPI_YOY = 0.46             # % YoY
CAPU_ALL_FALLBACK = 57.24  # ใช้เฉพาะกรณีไฟล์ต้นทางไม่มีแถว ALL_INDUSTRY


def load_src():
    """Source file has no header row: id, TSIC, name, weight, year, month, cap_u_pct"""
    out = []
    with open(SRC, encoding="utf-8") as f:
        for rec in csv.reader(f, delimiter=","):
            if len(rec) < 7:
                continue
            if rec[4].strip().lower() == "year":   # tolerate a header if one appears
                continue
            out.append({"id": rec[0], "tsic": rec[1], "name": rec[2],
                        "weight": rec[3], "year": rec[4].strip(),
                        "month": rec[5].strip(), "cap_u_pct": rec[6].strip()})
    return out


def main():
    rows = load_src()

    # แถว ALL_INDUSTRY (ภาพรวมทั้งอุตสาหกรรม) — เลือกงวดล่าสุดจากไฟล์ต้นทาง ไม่ hardcode
    all_rows = [r for r in rows if str(r.get("tsic", "")).upper() == "ALL"]
    all_row = max(all_rows, key=lambda r: (int(r["year"]), int(r["month"]))) if all_rows else None
    if all_row:
        period_all = "%s-%02d" % (all_row["year"], int(all_row["month"]))
        capu_all = all_row["cap_u_pct"]
    else:
        period_all, capu_all = "2026-07", "%.2f" % CAPU_ALL_FALLBACK
    # งวดล่าสุดของภาคอุตสาหกรรม (ไม่นับแถว ALL)
    sectors = [r for r in rows if str(r.get("tsic", "")).upper() != "ALL"]

    with open(OUT, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date_period", "industry_sector", "mpi_index", "mpi_yoy_pct",
                    "cap_u_pct", "bot_policy_rate", "private_capex_growth", "source"])
        w.writerow([period_all, "ALL_INDUSTRY", "%.2f" % MPI_INDEX, "%.2f" % MPI_YOY,
                    capu_all, "%.2f" % BOT_RATE, "%.2f" % PRIVATE_CAPEX,
                    "OIE CapU %s (สศอ.) / BOT MPC / NESDC" % period_all])
        for r in sectors:
            period = "%s-%02d" % (r["year"], int(r["month"]))
            name = (r.get("name") or "").strip()
            capu = float(r.get("cap_u_pct") or 0)
            w.writerow([period, name, "", "", "%.2f" % capu, "%.2f" % BOT_RATE,
                        "%.2f" % PRIVATE_CAPEX, "OIE CapU %s (TSIC %s)" % (period, r.get("tsic", ""))])

    print("macro rows: %d (1 all-industry + %d sectors) -> %s" % (len(rows) + 1, len(rows), OUT))
    hot = sorted(rows, key=lambda r: -float(r.get("cap_u_pct") or 0))[:5]
    print("hottest CapU:", ", ".join("%s=%.1f%%" % (r["name"][:34], float(r["cap_u_pct"])) for r in hot))


if __name__ == "__main__":
    main()
