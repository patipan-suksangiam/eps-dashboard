#!/usr/bin/env python3
"""Build RAW_Data/17_Open_Quotes.csv from Quotes (Pending) with company names & rep names."""
import csv, os, sys
from collections import defaultdict
from datetime import date, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RAW = os.path.join(ROOT, "RAW_Data")
sys.path.insert(0, HERE)
import build_group_detail as bgd

TODAY = date.today()

def rows(name):
    p = os.path.join(RAW, name)
    if not os.path.exists(p): return []
    with open(p, encoding='utf-8', errors='ignore') as fh:
        return list(csv.DictReader(fh))

def main():
    by_ind, east, exc, overrides = bgd.load_group_map()
    dbd_prov = bgd.load_dbd_province()
    clients = {r['client_id']: r for r in rows('9_Client_Master.csv')}
    cgroup = {cid: bgd.client_group(c, by_ind, east, exc, dbd_prov, cid, overrides) for cid, c in clients.items()}
    
    rep_map = {}
    for r in rows('1_CRM_Sales_Person.csv'):
        rep_map[r.get('emp_id', '').strip()] = r.get('name', '').strip()

    open_quotes = []
    for r in rows('2_Quote_Data.csv'):
        st = (r.get('status') or r.get('stage') or '').strip().lower()
        if 'order' in st or 'loss' in st:
            continue
        cid = (r.get('client_id') or '').strip()
        g = cgroup.get(cid, 'U')
        val = float(str(r.get('value_thb') or 0).replace(',', '') or 0)
        cd_str = (r.get('created_date') or '')[:10]
        aging = 0
        if cd_str:
            try:
                cd = datetime.strptime(cd_str, '%Y-%m-%d').date()
                aging = (TODAY - cd).days
            except Exception:
                pass
        sid = (r.get('sales_id') or '').strip()
        rep_name = rep_map.get(sid, sid)
        comp_name = clients.get(cid, {}).get('company_name', r.get('client_name', ''))

        open_quotes.append([
            g, r.get('quote_id', ''), cid, comp_name,
            sid, rep_name, "%.2f" % val,
            r.get('probability_pct', ''), r.get('expected_order_date', ''),
            r.get('created_date', ''), aging, r.get('status', 'Pending')
        ])

    out = os.path.join(RAW, '17_Open_Quotes.csv')
    with open(out, 'w', encoding='utf-8', newline='') as fh:
        w = csv.writer(fh)
        w.writerow(['group', 'quote_id', 'client_id', 'company_name', 'sales_id', 'rep_name',
                    'value_thb', 'probability_pct', 'expected_order_date', 'created_date',
                    'aging_days', 'status'])
        w.writerows(open_quotes)

    print(f"17_Open_Quotes.csv written: {len(open_quotes)} pending quotes")

if __name__ == '__main__':
    main()
