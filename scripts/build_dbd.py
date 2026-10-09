#!/usr/bin/env python3
"""Build RAW_Data/8_DBD_Data.csv by joining CRM accounts to Thai factory registers,
Customer ID mapping (qryCOOR), and DBD Open API cache via Tax ID.

Sources (all real):
  * RAW_Data/9_Client_Master.csv                    -- CRM accounts
  * _CORE_Private/DIW_Factory_Database.xlsx         -- กรมโรงงานอุตสาหกรรม register
  * _CORE_Private/GDrive_Database_EPS/Customer ID.xlsx -- qryCOOR (Name -> Tax ID & Capital)
  * _CORE_Private/dbd_cache.json                    -- DBD Open API cache keyed by 13-digit tax id
"""
import csv, json, os, glob, re, sys

REGIONAL_DIR = "G:/My Drive/JOM/รายชื่ออุตสาหกรรมทั่วประเทศ (จอม)"

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from build_boi import read_xlsx  # noqa: E402

RAW = os.path.join(ROOT, "RAW_Data")
CORE = os.path.join(ROOT, "_CORE_Private")
CLIENTS = os.path.join(RAW, "9_Client_Master.csv")
DIW = os.path.join(CORE, "DIW_Factory_Database.xlsx")
CUST_XLSX = os.path.join(CORE, "GDrive_Database_EPS", "Customer ID.xlsx")
DBDC = os.path.join(CORE, "dbd_cache.json")
OUT = os.path.join(RAW, "8_DBD_Data.csv")

PREFIX = ["บริษัท", "บจก.", "บจก", "ห้างหุ้นส่วนจำกัด", "หจก.", "หจก", "ห้างหุ้นส่วนสามัญ"]
SUFFIX = ["จำกัด(มหาชน)", "จำกัด(มหาชน", "จำกัด", "มหาชน", "publiccompanylimited",
          "companylimited", "co.,ltd.", "co.,ltd", "co.ltd.", "ltd.", "ltd"]


def norm(name):
    s = str(name or "").lower()
    s = re.sub(r"[()\[\].,\"'/\\-]", "", s)
    s = re.sub(r"\s+", "", s)
    for p in PREFIX:
        if s.startswith(p.replace(".", "")):
            s = s[len(p.replace(".", "")):]
    for suf in SUFFIX:
        suf_c = re.sub(r"[().,\s]", "", suf)
        if suf_c and s.endswith(suf_c):
            s = s[: -len(suf_c)]
    return s.strip()


def load_diw():
    out = {}
    files_to_load = [DIW]
    if os.path.exists(REGIONAL_DIR):
        files_to_load.extend(glob.glob(os.path.join(REGIONAL_DIR, "*.xlsx")))

    for fpath in files_to_load:
        if not os.path.exists(fpath):
            continue
        try:
            rows = read_xlsx(fpath)
            for sheet, body in rows.items():
                if not body:
                    continue
                header = body[0]
                idx = {str(h).strip(): i for i, h in enumerate(header) if h is not None}
                name_col = None
                for col in ("ชื่อโรงงาน", "ผู้ประกอบการ"):
                    if col in idx:
                        name_col = idx[col]
                        break
                cap_col = idx.get("เงินทุน")
                hp_col = idx.get("แรงม้า")
                tsic_col = idx.get("TSIC")
                prov_col = idx.get("จังหวัด")

                for r in body[1:]:
                    if name_col is not None and name_col < len(r):
                        name_val = str(r[name_col] or "").strip()
                        n = norm(name_val)
                        if not n:
                            continue
                        cap = str(r[cap_col] if cap_col is not None and cap_col < len(r) else "").replace(",", "").strip()
                        try:
                            cap_m = float(cap) / 1e6 if cap else ""
                        except ValueError:
                            cap_m = ""
                        hp = str(r[hp_col] if hp_col is not None and hp_col < len(r) else "").strip()
                        tsic = str(r[tsic_col] if tsic_col is not None and tsic_col < len(r) else "").strip()
                        prov = str(r[prov_col] if prov_col is not None and prov_col < len(r) else "").strip()
                        out.setdefault(n, {
                            "name": name_val,
                            "capital_m": cap_m,
                            "hp": hp,
                            "tsic": tsic,
                            "province": prov,
                        })
        except Exception as e:
            print(f"Warning reading {fpath}: {e}")
    return out


def load_qry_coor():
    if not os.path.exists(CUST_XLSX):
        return {}
    sheets = read_xlsx(CUST_XLSX)
    qry = sheets.get("qryCOOR", [])
    if not qry:
        return {}
    header = qry[0]
    idx = {h: i for i, h in enumerate(header)}
    out = {}
    for r in qry[1:]:
        name = r[idx["ชื่อ"]] if idx.get("ชื่อ") is not None and len(r) > idx["ชื่อ"] else ""
        n = norm(name)
        if not n:
            continue
        tid = r[idx["เลขผู้เสียภาษี"]].strip() if idx.get("เลขผู้เสียภาษี") is not None and len(r) > idx["เลขผู้เสียภาษี"] else ""
        cap = r[idx["เงินทุน"]].strip() if idx.get("เงินทุน") is not None and len(r) > idx["เงินทุน"] else ""
        tsic = r[idx["TSIC"]] if idx.get("TSIC") is not None and len(r) > idx["TSIC"] else ""
        prov = r[idx["ที่อยู่"]] if idx.get("ที่อยู่") is not None and len(r) > idx["ที่อยู่"] else ""
        out[n] = {"tax_id": tid, "capital": cap, "tsic": tsic, "province": prov}
    return out


def main():
    diw = load_diw()
    print("DIW register entries indexed: %d" % len(diw))

    coor_map = load_qry_coor()
    print("Customer ID qryCOOR entries indexed: %d" % len(coor_map))

    dbdc = {}
    if os.path.exists(DBDC):
        dbdc = json.load(open(DBDC, encoding="utf-8"))
    print("DBD API cache entries: %d" % len(dbdc))

    clients = list(csv.DictReader(open(CLIENTS, encoding="utf-8")))
    matched = 0
    with open(OUT, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["client_id", "company_name", "registered_capital_m",
                    "machine_horsepower", "tsic_code", "revenue_latest_year",
                    "province", "match_source", "dbd_status"])
        for c in clients:
            key = norm(c.get("company_name"))
            
            # 1. Try DIW Register
            d = diw.get(key)
            if d:
                matched += 1
                w.writerow([c["client_id"], c["company_name"], d["capital_m"], d["hp"],
                            d["tsic"], "", d["province"], "DIW register", ""])
                continue

            # 2. Try Customer ID (qryCOOR) -> Tax ID -> DBD Cache
            coor = coor_map.get(key)
            if coor and coor["tax_id"] and coor["tax_id"] in dbdc:
                b = dbdc[coor["tax_id"]]
                matched += 1
                cap = b.get("dbdRegisterCapital")
                cap_m = round(float(cap) / 1e6, 2) if cap else ""
                if not cap_m and coor["capital"]:
                    try:
                        cap_m = round(float(coor["capital"]) / 1e6, 2)
                    except ValueError:
                        pass
                w.writerow([c["client_id"], c["company_name"], cap_m,
                            "", b.get("dbdBusinessCode") or coor["tsic"], "",
                            b.get("dbdProvince") or "", "DBD API (TaxID)", b.get("dbdStatus", "")])
                continue

            # 3. Try Customer ID qryCOOR direct capital if available
            if coor and coor["capital"]:
                try:
                    cap_val = float(coor["capital"])
                    if cap_val > 0:
                        matched += 1
                        w.writerow([c["client_id"], c["company_name"], round(cap_val / 1e6, 2),
                                    "", coor["tsic"], "", "", "Customer ID (Direct)", ""])
                        continue
                except ValueError:
                    pass

            # Unmatched
            w.writerow([c["client_id"], c["company_name"], "", "", "", "", "", "", ""])

    print("rows written: %d | matched: %d (%.1f%%) -> %s"
          % (len(clients), matched, 100.0 * matched / max(len(clients), 1), OUT))


if __name__ == "__main__":
    main()
