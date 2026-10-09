#!/usr/bin/env python3
"""Rebuild the group-level actuals in RAW_Data/0_EPS_Overview_2026.csv from REAL CRM orders.

Group attribution rules come from _CORE_Private/group_map.json (compiled by Sales
Dashboard AI from Industrial ID.xlsx):
  * industry code (e.g. CH14) -> responsible sales group(s)
  * any account located in an eastern province (ระยอง) -> Group R,
    except a named list of large accounts that stay with Group D.

Only the five Group_*_Revenue `value` cells are rewritten; every other metric
(plan target, Hot Jobs, margins, ...) is preserved from the existing file, so the
daily Hot-Jobs job keeps working.
"""
import csv, json, os, sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RAW = os.path.join(ROOT, "RAW_Data")
CORE = os.path.join(ROOT, "_CORE_Private")

SO = os.path.join(RAW, "3_SO_Data.csv")
CLIENTS = os.path.join(RAW, "9_Client_Master.csv")
GROUPMAP = os.path.join(CORE, "group_map.json")
OVERVIEW = os.path.join(RAW, "0_EPS_Overview_2026.csv")

METRIC_TO_GROUP = {
    "Group_A_Revenue": "A", "Group_B_Revenue": "B", "Group_C_Revenue": "C",
    "Group_D_Revenue": "D", "Group_R_Revenue": "R",
}


def main():
    gm = json.load(open(GROUPMAP, encoding="utf-8"))
    by_ind = gm["by_ind_code"]
    east = gm.get("eastern_provinces", [])
    exc = gm.get("eastern_exceptions_to_D", [])
    overrides = {k: v for k, v in (gm.get("group_overrides_by_name") or {}).items() if not k.startswith("_")}

    def forced_group(name):
        """Explicit per-account group (highest priority) — e.g. PTTGC / PTTME -> R."""
        up = (name or "").upper()
        for k, g in overrides.items():
            if k.upper() in up:
                return g
        return None

    clients = {r["client_id"]: r for r in csv.DictReader(open(CLIENTS, encoding="utf-8-sig"))}
    so = list(csv.DictReader(open(SO, encoding="utf-8")))

    # Province source of truth = factory register (DIW/DBD). The CRM address text is
    # unreliable (many accounts have no address at all), so it is only a fallback.
    dbd_prov = {}
    dbd_path = os.path.join(RAW, "8_DBD_Data.csv")
    if os.path.exists(dbd_path):
        with open(dbd_path, encoding="utf-8") as f:
            for r in csv.DictReader(f):
                p = (r.get("province") or "").strip()
                if p:
                    dbd_prov[r.get("client_id", "")] = p

    def province_text(cid, client):
        p = dbd_prov.get(cid, "")
        return p if p else (client.get("address") or "")

    grp = defaultdict(float)
    unmapped = defaultdict(float)
    for r in so:
        v = float(r.get("value_thb") or 0)
        cid = r.get("client_id", "")
        c = clients.get(cid)
        if not c:
            unmapped["no_client"] += v
            continue
        ptext = province_text(cid, c)
        forced = forced_group(c.get("company_name", ""))
        if forced:
            grp[forced] += v
            continue
        is_east = any(p in ptext for p in east) and not any(e in c.get("company_name", "") for e in exc)
        if is_east:
            grp["R"] += v
            continue
        stars = by_ind.get((c.get("industry_group") or "").strip())
        if not stars:
            unmapped["no_industry"] += v
            continue
        grp[stars[0]] += v

    total = sum(float(r.get("value_thb") or 0) for r in so)
    mapped = sum(grp.values())
    print("real group actuals (M THB):", {k: round(v / 1e6, 2) for k, v in sorted(grp.items())})
    print("unmapped (M THB):", {k: round(v / 1e6, 2) for k, v in unmapped.items()})
    print("coverage: %.1f%% of %.2f M" % (100.0 * mapped / total, total / 1e6))

    # ---- FY2026 plan targets (real: Plan_SalesOrder.csv — amounts carry thousands separators) ----
    plan_total, plan_group = 0.0, defaultdict(float)
    plan_path = os.path.join(ROOT, "Plan_SalesOrder.csv")
    if os.path.exists(plan_path):
        with open(plan_path, encoding="utf-8", errors="ignore") as f:
            for r in csv.DictReader(f):
                if (r.get("Year") or "").strip() != "2026":
                    continue
                try:
                    amt = float((r.get("Plan Amount") or "0").replace(",", "").strip() or 0)
                except ValueError:
                    amt = 0.0
                plan_total += amt
                gname = (r.get("Sales Group") or "").strip()
                for letter in "ABCDR":
                    if ("กรุ๊ป %s" % letter) in gname:
                        plan_group[letter] += amt
                        break

    # ---- KPIs derived from the same SO feed (never hardcoded) ----
    so_orders = len(so)
    so_total = sum(float(r.get("value_thb") or 0) for r in so)
    active_clients = len({r.get("client_id") for r in so if (r.get("client_id") or "").strip()})

    rows = list(csv.reader(open(OVERVIEW, encoding="utf-8")))
    header, body = rows[0], rows[1:]
    idx_value, idx_target = header.index("value"), header.index("target")
    changed = []
    derived = {
        "FY2026_Revenue_YTD": "%.2f" % (so_total / 1e6),
        "FY2026_Sales_Orders": str(so_orders),
        "FY2026_Active_Customers": str(active_clients),
    }
    keep = []
    for r in body:
        metric = r[0]
        # metrics that had no real source (were hardcoded mock) -> removed
        if metric in ("FY2026_Gross_Margin", "FY2026_Win_Rate"):
            changed.append((metric, r[idx_value], "<removed: no real source>"))
            continue
        g = METRIC_TO_GROUP.get(metric)
        if g:
            old = r[idx_value]
            r[idx_value] = "%.2f" % (grp.get(g, 0.0) / 1e6)
            if plan_group.get(g):
                r[idx_target] = "%.2f" % (plan_group[g] / 1e6)
            changed.append(("Group " + g, old, r[idx_value]))
        elif metric in derived:
            old = r[idx_value]
            r[idx_value] = derived[metric]
            if metric == "FY2026_Revenue_YTD" and plan_total:
                r[idx_target] = "%.2f" % (plan_total / 1e6)
            changed.append((metric, old, r[idx_value]))
        keep.append(r)
    body = keep

    with open(OVERVIEW, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(body)

    for g, old, new in changed:
        print("  Group %s: %s -> %s" % (g, old, new))
    print("overview updated ->", OVERVIEW)


if __name__ == "__main__":
    main()
