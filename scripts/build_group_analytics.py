#!/usr/bin/env python3
"""Build the Group Overview analytics CSVs (Comment 20260924 & 20260928)."""
import csv, json, os, sys
from collections import defaultdict
from datetime import date, datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RAW = os.path.join(ROOT, "RAW_Data")
CORE = os.path.join(ROOT, "_CORE_Private")
sys.path.insert(0, HERE)
import build_group_detail as bgd

TODAY = date.today()
CUT = TODAY - timedelta(days=365)
GROUPS = ["A", "B", "C", "D", "R", "U"]


def rows(name):
    p = os.path.join(RAW, name)
    if not os.path.exists(p):
        return []
    with open(p, encoding="utf-8-sig", errors="ignore") as fh:
        return list(csv.DictReader(fh))


def d10(s):
    s = (s or "")[:10]
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except Exception:
        return None


def num(v):
    try:
        return float(str(v).replace(",", "") or 0)
    except Exception:
        return 0.0


def load_rep_groups():
    p = os.path.join(CORE, "group_reps.json")
    if not os.path.exists(p):
        return {}
    d = json.load(open(p, encoding="utf-8"))
    return {n.strip(): g for g, names in (d.get("reps_by_group") or {}).items() for n in names}


def main():
    by_ind, east, exc, overrides = bgd.load_group_map()
    dbd_prov = bgd.load_dbd_province()
    clients = {r["client_id"]: r for r in rows("9_Client_Master.csv")}
    cgroup = {cid: bgd.client_group(c, by_ind, east, exc, dbd_prov, cid, overrides) for cid, c in clients.items()}

    owner_name_map = {}
    for r in rows("1_CRM_Sales_Person.csv"):
        owner_name_map[r.get("emp_id", "").strip()] = r.get("name", "").strip()

    so_by_client = defaultdict(lambda: [0, 0.0, None])
    so_rows = []
    for r in rows("3_SO_Data.csv"):
        bd = d10(r.get("booking_date")); cid = (r.get("client_id") or "").strip()
        g = cgroup.get(cid, "U"); val = num(r.get("value_thb")); dd = d10(r.get("delivery_date"))
        lead = (dd - bd).days if (bd and dd) else ""
        so_rows.append([g, r.get("so_id", ""), cid, clients.get(cid, {}).get("company_name", r.get("client_name", "")), "%.2f" % val,
                        bd.isoformat() if bd else "", dd.isoformat() if dd else "", lead, r.get("status", "")])
        if bd and bd >= CUT:
            e = so_by_client[cid]; e[0] += 1; e[1] += val
            if e[2] is None or bd > e[2]:
                e[2] = bd

    vis_by_client, vis_by_rep = defaultdict(int), defaultdict(int)
    for r in rows("4_Visit_Report.csv"):
        d = d10(r.get("visit_date"))
        if not (d and d >= CUT):
            continue
        cid = (r.get("client_id") or "").strip(); sid = (r.get("sales_id") or "").strip()
        if cid: vis_by_client[cid] += 1
        if sid: vis_by_rep[sid] += 1

    def qblank():
        return {"n": 0, "won": 0, "lost": 0, "open": 0, "val": 0.0, "won_v": 0.0, "lost_v": 0.0, "open_val": 0.0, "oldest": 0}
    q_by_group, q_by_rep, q_by_client = defaultdict(qblank), defaultdict(qblank), defaultdict(qblank)
    for r in rows("2_Quote_Data.csv"):
        st = (r.get("status") or r.get("stage") or "").strip().lower()
        cid = (r.get("client_id") or "").strip(); sid = (r.get("sales_id") or "").strip()
        g = cgroup.get(cid, "U"); val = num(r.get("value_thb")); cd = d10(r.get("created_date"))
        age = (TODAY - cd).days if cd else 0
        for d in (q_by_group[g], q_by_rep[sid] if sid else None):
            if d is None:
                continue
            d["n"] += 1; d["val"] += val
            if "order" in st:
                d["won"] += 1; d["won_v"] += val
            elif "loss" in st:
                d["lost"] += 1; d["lost_v"] += val
            else:
                d["open"] += 1; d["open_val"] += val
                if age > d["oldest"]:
                    d["oldest"] = age
        if cid:
            c = q_by_client[cid]; c["n"] += 1; c["val"] += val
            if "order" not in st and "loss" not in st:
                c["open"] += 1
                if age > c["oldest"]:
                    c["oldest"] = age

    dbd_all, dbd_by_group, dbd_info = 0, defaultdict(int), {}
    for r in rows("8_DBD_Data.csv"):
        cap = num(r.get("registered_capital_m")); cid = (r.get("client_id") or "").strip()
        dbd_info[cid] = r
        if cap > 100:
            dbd_all += 1
            g = cgroup.get(cid, "U")
            if g != "U":
                dbd_by_group[g] += 1

    sop_by_rep_yr = defaultdict(lambda: {2024: [0, 0.0], 2025: [0, 0.0], 2026: [0, 0.0]})
    for r in rows("3_SO_Data.csv"):
        bd = d10(r.get("booking_date"))
        if not bd:
            continue
        yr = bd.year
        if yr not in (2024, 2025, 2026):
            continue
        sid = (r.get("sales_id") or "").strip() or (clients.get((r.get("client_id") or "").strip(), {}).get("owner_id") or "").strip()
        if sid:
            e = sop_by_rep_yr[sid][yr]
            e[0] += 1; e[1] += num(r.get("value_thb"))

    rep_group = load_rep_groups()
    rep_rows = []
    for r in rows("1_CRM_Sales_Person.csv"):
        if (r.get("is_group") or "").strip().lower() == "yes":
            continue
        sid = (r.get("emp_id") or "").strip(); name = (r.get("name") or "").strip()
        g = rep_group.get(name)
        if not g:
            continue
        q = q_by_rep.get(sid, qblank())
        tot_cnt = q["n"]
        wr_cnt = round(100.0 * q["won"] / tot_cnt, 1) if tot_cnt else 0
        tot_val = q["val"]
        wr_val = round(100.0 * q["won_v"] / tot_val, 1) if tot_val else 0
        sy = sop_by_rep_yr.get(sid, {2024: [0, 0.0], 2025: [0, 0.0], 2026: [0, 0.0]})
        v24 = sy[2024][1] / 1e6; v25 = sy[2025][1] / 1e6; v26 = sy[2026][1] / 1e6
        tot3yr = v24 + v25 + v26
        rep_rows.append([g, sid, name, r.get("email", ""), q["won"], q["lost"], q["open"],
                         wr_cnt, wr_val, q["oldest"],
                         "%.2f" % v24, "%.2f" % v25, "%.2f" % v26, "%.2f" % tot3yr, vis_by_rep.get(sid, 0)])

    client_rows = []
    for cid, c in clients.items():
        so = so_by_client.get(cid); vis = vis_by_client.get(cid, 0); q = q_by_client.get(cid)
        last = so[2] if so else None
        active = bool((so and so[0]) or vis)
        if not (active or (q and q["n"])):
            continue
        dbd = dbd_info.get(cid, {})
        oid = (c.get("owner_id") or "").strip()
        client_rows.append([cgroup.get(cid, "U"), cid, c.get("company_name", ""),
                            dbd_prov.get(cid) or bgd.province_of(c.get("address", "")),
                            c.get("industry_group", ""), "Y" if active else "N",
                            last.isoformat() if last else "",
                            (TODAY - last).days if last else "",
                            so[0] if so else 0, "%.2f" % ((so[1] / 1e6) if so else 0), vis,
                            "Y" if dbd else "N", dbd.get("registered_capital_m", ""),
                            dbd.get("machine_horsepower", ""),
                            q["n"] if q else 0, q["open"] if q else 0, q["oldest"] if q else 0,
                            oid, owner_name_map.get(oid, "")])

    kpi_rows = []
    for g in GROUPS:
        cl = [r for r in client_rows if r[0] == g]
        act = [r for r in cl if r[5] == "Y"]
        q = q_by_group.get(g, qblank())
        dec_cnt = q["won"] + q["lost"]
        wr_cnt = round(100.0 * q["won"] / dec_cnt, 1) if dec_cnt else 0
        dec_val = q["won_v"] + q["lost_v"]
        wr_val = round(100.0 * q["won_v"] / dec_val, 1) if dec_val else 0
        leads = [num(r[7]) for r in cl if r[7] != ""]
        kpi_rows.append([g, len(act), len(cl), dbd_by_group.get(g, 0), dbd_all,
                         sum(int(r[8]) for r in cl), "%.2f" % sum(num(r[9]) for r in cl),
                         q["n"], q["won"], q["lost"], q["open"],
                         wr_cnt, wr_val, q["oldest"],
                         sum(int(r[10]) for r in cl),
                         round(sum(leads) / len(leads)) if leads else ""])

    todo = []
    for g in GROUPS:
        q = q_by_group.get(g, qblank())
        if q["oldest"] > 90:
            todo.append([g, "High", "Clear stalled quotations older than 90 days",
                         "%d open quotes, oldest %d days" % (q["open"], q["oldest"]), "Group %s" % g])
        cl = [r for r in client_rows if r[0] == g]
        inactive = sorted([r for r in cl if r[5] == "N" and r[11] == "Y"], key=lambda x: float(x[12] if x[12] != "" else 0), reverse=True)
        if inactive:
            names = ", ".join(x[2] for x in inactive[:5])
            more = " (+%d more)" % (len(inactive)-5) if len(inactive) > 5 else ""
            todo.append([g, "High", "Re-activate Idle DBD Factories (>100M Capital)",
                         "Targets: %s%s" % (names, more), "Sales Team"])
        nov = sorted([r for r in cl if int(r[10] or 0) == 0 and float(r[9] or 0) > 0], key=lambda x: float(x[9] if x[9] != "" else 0), reverse=True)
        if nov:
            names = ", ".join(x[2] for x in nov[:5])
            more = " (+%d more)" % (len(nov)-5) if len(nov) > 5 else ""
            todo.append([g, "Medium", "Schedule Visit for Active Accounts (Zero Visits YTD)",
                         "Top Value Targets: %s%s" % (names, more), "Sales Team"])
        nodue = [r for r in so_rows if r[0] == g and r[7] == ""]
        if nodue:
            todo.append([g, "Low", "Fill missing delivery dates on sales orders",
                         "%d orders without due date" % len(nodue), "Group %s" % g])

    def w(name, header, data):
        with open(os.path.join(RAW, name), "w", encoding="utf-8", newline="") as fh:
            c = csv.writer(fh); c.writerow(header); c.writerows(data)
        return len(data)

    w("12_Group_KPI.csv", ["group", "active_accounts_12m", "accounts_total", "dbd_factories_gt100m",
                           "dbd_total_gt100m", "so_count_12m", "so_value_12m_m", "quotes_total",
                           "quotes_won", "quotes_lost", "quotes_open", "win_rate_count_pct", "win_rate_value_pct",
                           "oldest_open_quote_days", "visits_12m", "avg_days_since_last_order"], kpi_rows)
    w("13_Rep_Performance.csv", ["group", "emp_id", "name", "email", "quotes_won", "quotes_lost",
                                 "quotes_open", "win_rate_count_pct", "win_rate_value_pct", "oldest_open_quote_days",
                                 "so_value_2024_m", "so_value_2025_m", "so_value_2026_m",
                                 "so_value_3yr_total_m", "visits_12m"], rep_rows)
    w("14_Client_Detail.csv", ["group", "client_id", "company_name", "province", "industry_group",
                               "active_12m", "last_order_date", "days_since_last_order", "so_count_12m",
                               "so_value_12m_m", "visits_12m", "in_dbd", "dbd_capital_m", "dbd_hp",
                               "quotes_total", "quotes_open", "oldest_open_quote_days",
                               "owner_id", "rep_name"], client_rows)
    w("15_SO_Delivery.csv", ["group", "so_id", "client_id", "client_name", "value_thb", "booking_date",
                              "delivery_date", "delivery_days", "status"], so_rows)
    w("16_Todo.csv", ["group", "priority", "task", "reason", "owner"], todo)
    print("build_group_analytics completed successfully")

if __name__ == "__main__":
    main()

