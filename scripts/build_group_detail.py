#!/usr/bin/env python3
"""Build public group-detail CSVs for the Group A/B/C/D/R dashboard pages.

Why: the attribution rules live in `_CORE_Private/group_map.json`, which is
private and NOT served to the browser. This script materialises the derived,
shareable view into `RAW_Data/` so the SPA can filter by group.

Attribution rules (same as build_overview.py):
  * account in an "eastern province" (ระยอง) -> Group R
    (except a named list of large accounts that stay with Group D)
  * otherwise industry code (e.g. CH14) -> responsible group = by_ind_code[code][0]
  * anything unmapped -> group "U"

Outputs:
  RAW_Data/10_Group_Reps.csv     group,emp_id,name,email,status,so_count_2026,so_value_2026_m,quote_count,visits_2026
  RAW_Data/11_Group_Clients.csv  group,client_id,company_name,province,industry_group,so_count_2026,so_value_2026_m,visits_2026
"""
import csv
import json
import os
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RAW = os.path.join(ROOT, "RAW_Data")
CORE = os.path.join(ROOT, "_CORE_Private")

YEAR = "2026"
GROUPS = ["A", "B", "C", "D", "R", "U"]


def load_group_map():
    gm = json.load(open(os.path.join(CORE, "group_map.json"), encoding="utf-8"))
    overrides = {k: v for k, v in (gm.get("group_overrides_by_name") or {}).items() if not k.startswith("_")}
    return (gm.get("by_ind_code", {}), gm.get("eastern_provinces", []),
            gm.get("eastern_exceptions_to_D", []), overrides)


def client_group(client, by_ind, east, exc, dbd_prov=None, cid="", overrides=None):
    """Group attribution (priority: explicit name override -> province -> industry code).

    Province source of truth = factory register (DIW/DBD) via 8_DBD_Data.csv; the CRM
    address text is only a fallback because many accounts have no address at all.
    """
    if not client:
        return "U"
    name = client.get("company_name", "") or ""
    up = name.upper()
    for k, g in (overrides or {}).items():      # e.g. PTTGC / PTTME -> R
        if k.upper() in up:
            return g
    prov = (dbd_prov or {}).get(cid, "") or (client.get("address", "") or "")
    if any(p in prov for p in east) and not any(e in name for e in exc):
        return "R"
    stars = by_ind.get((client.get("industry_group") or "").strip())
    return stars[0] if stars else "U"


def load_dbd_province():
    """client_id -> province, from the DIW/DBD factory register (rows with a province)."""
    out = {}
    path = os.path.join(RAW, "8_DBD_Data.csv")
    if not os.path.exists(path):
        return out
    with open(path, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            p = (r.get("province") or "").strip()
            if p:
                out[r.get("client_id", "")] = p
    return out


def province_of(addr):
    for p in ["ระยอง", "ชลบุรี", "ฉะเชิงเทรา", "สมุทรปราการ", "กรุงเทพ", "ปทุมธานี",
              "นครราชสีมา", "ขอนแก่น", "สงขลา", "ภูเก็ต", "เชียงใหม่", "สระบุรี",
              "นครปฐม", "สมุทรสาคร", "พระนครศรีอยุธยา", "ราชบุรี", "ลพบุรี", "จันทบุรี"]:
        if p in addr:
            return p
    return ""


def main():
    by_ind, east, exc, overrides = load_group_map()
    dbd_prov = load_dbd_province()
    clients = {}
    with open(os.path.join(RAW, "9_Client_Master.csv"), encoding="utf-8") as f:
        for r in csv.DictReader(f):
            clients[r.get("client_id", "")] = r

    cgroup = {cid: client_group(c, by_ind, east, exc, dbd_prov, cid, overrides) for cid, c in clients.items()}
    # 3_SO_Data.csv ไม่มี sales_id (ว่าง) -> ใช้เจ้าของลูกค้า (owner_id) เป็นตัว attribute แทน
    owner_of = {cid: (c.get("owner_id") or "").strip() for cid, c in clients.items()}

    # ---- aggregate Sales Orders (2026) ----
    so_by_client = defaultdict(lambda: [0, 0.0])
    so_by_rep_group = defaultdict(lambda: [0, 0.0])
    with open(os.path.join(RAW, "3_SO_Data.csv"), encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if not (r.get("booking_date", "") or "").startswith(YEAR):
                continue
            cid = r.get("client_id", "")
            val = float(r.get("value_thb") or 0)
            g = cgroup.get(cid, "U")
            so_by_client[cid][0] += 1
            so_by_client[cid][1] += val
            sid = (r.get("sales_id") or "").strip() or owner_of.get(cid, "")
            if sid:
                so_by_rep_group[(sid, g)][0] += 1
                so_by_rep_group[(sid, g)][1] += val

    # ---- aggregate visits (2026) ----
    vis_by_client = defaultdict(int)
    vis_by_rep = defaultdict(int)
    with open(os.path.join(RAW, "4_Visit_Report.csv"), encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if not (r.get("visit_date", "") or "").startswith(YEAR):
                continue
            cid = r.get("client_id", "")
            sid = r.get("sales_id", "")
            if cid:
                vis_by_client[cid] += 1
            if sid:
                vis_by_rep[sid] += 1

    # ---- sales people (skip CRM group pseudo-rows) ----
    reps = []
    with open(os.path.join(RAW, "1_CRM_Sales_Person.csv"), encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if (r.get("is_group") or "").strip().lower() == "yes":
                continue
            reps.append(r)

    # ---- write group reps ----
    cols = ["group", "emp_id", "name", "email", "status", "so_count_2026", "so_value_2026_m", "quote_count", "visits_2026"]
    with open(os.path.join(RAW, "10_Group_Reps.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for r in reps:
            sid = r.get("emp_id", "")
            by_group = {g: so_by_rep_group.get((sid, g)) for g in GROUPS}
            if any(by_group.values()):
                for g in GROUPS:
                    v = by_group.get(g)
                    if not v:
                        continue
                    w.writerow([g, sid, r.get("name", ""), r.get("email", ""), r.get("status", ""),
                                v[0], "%.2f" % (v[1] / 1e6), r.get("quote_count", ""), vis_by_rep.get(sid, 0)])
            else:
                w.writerow(["U", sid, r.get("name", ""), r.get("email", ""), r.get("status", ""),
                            0, "0.00", r.get("quote_count", ""), vis_by_rep.get(sid, 0)])

    # ---- write group clients ----
    cols = ["group", "client_id", "company_name", "province", "industry_group",
            "so_count_2026", "so_value_2026_m", "visits_2026"]
    with open(os.path.join(RAW, "11_Group_Clients.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for cid, c in clients.items():
            so = so_by_client.get(cid)
            vis = vis_by_client.get(cid, 0)
            if not so and not vis:
                continue  # keep the file small — only active accounts
            w.writerow([cgroup.get(cid, "U"), cid, c.get("company_name", ""), dbd_prov.get(cid) or province_of(c.get("address", "")),
                        c.get("industry_group", ""), so[0] if so else 0,
                        "%.2f" % ((so[1] / 1e6) if so else 0), vis])

    # ---- report ----
    tot = defaultdict(float)
    for (sid, g), v in so_by_rep_group.items():
        tot[g] += v[1]
    print("group reps:", len(reps), "| clients written:", sum(1 for _ in open(os.path.join(RAW, "11_Group_Clients.csv"), encoding="utf-8")) - 1)
    print("SO by group (M THB):", {g: round(tot.get(g, 0) / 1e6, 2) for g in GROUPS})


if __name__ == "__main__":
    main()
