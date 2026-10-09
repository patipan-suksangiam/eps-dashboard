import csv
from collections import defaultdict

clients = list(csv.DictReader(open('RAW_Data/11_Group_Clients.csv', encoding='utf-8')))
clients.sort(key=lambda x: float(x.get('so_value_2026_m') or 0), reverse=True)

print("Top 10 clients in Group A:")
for r in [c for c in clients if c['group']=='A'][:10]:
    print("  %s : %s M THB (%s orders, prov: %s, ind: %s)" % (
        r['company_name'], r['so_value_2026_m'], r['so_count_2026'], r['province'], r['industry_group']))

tot = defaultdict(float)
for c in clients:
    tot[c['group']] += float(c['so_value_2026_m'] or 0)

print("\nTotal SO value by group:")
for g, v in sorted(tot.items()):
    print("  Group %s: %.2f M THB" % (g, v))
