# ⚠️ DEPRECATED (2026-09-24) — ย้ายไป _superseded/ แล้ว
#   เหตุผล: อ้างไฟล์แผนที่ไม่มีอยู่ (Plan_2026_SelectedProducts.csv) + เคยฝัง credential ในไฟล์
#   ใช้ scripts/pull_crm_data.py แทน
import os, sys, csv, json, hashlib, urllib.parse, urllib.request

plan_path = "/home/jom/SynologyDrive/AI Dashboard/Plan_2026_SelectedProducts.csv"

total_plan = 0
group_plans = {}

with open(plan_path, mode='r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        try:
            amt = float(row.get('Plan Amount', 0) or 0)
        except:
            amt = 0.0
        total_plan += amt
        grp = row.get('Sales Group', 'Unknown')
        group_plans[grp] = group_plans.get(grp, 0.0) + amt

print(f"--- PLAN 2026 ANALYSIS ---")
print(f"Total Annual Plan Amount: {total_plan:,.2f} THB")
for g, val in group_plans.items():
    print(f"  {g}: {val:,.2f} THB")

# Now pull Quotes from CRM for 2026
BASE = "https://crm.siamrajpump.com/webservice.php"
USER = os.environ.get("CRM_USER", "")
KEY = os.environ.get("CRM_KEY", "")

def api(params, method="GET"):
    data = urllib.parse.urlencode(params).encode()
    url = BASE + (("?" + urllib.parse.urlencode(params)) if method == "GET" else "")
    req = urllib.request.Request(url, data=data if method == "POST" else None, method=method, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

def login():
    tok = api({"operation": "getchallenge", "username": USER}).get("result", {}).get("token")
    res = api({"operation": "login", "username": USER, "accessKey": hashlib.md5((tok + KEY).encode()).hexdigest()}, method="POST")
    return res["result"]["sessionName"]

print("\nLogging in to CRM for 2026 Quotes...")
try:
    sess = login()
    all_quotes = []
    offset = 0
    batch_size = 100

    while True:
        query = f"SELECT quote_no, subject, hdnGrandTotal, createdtime, quotestage, account_id FROM Quotes WHERE createdtime >= '2026-01-01' LIMIT {offset}, {batch_size};"
        res = api({"operation": "query", "sessionName": sess, "query": query})
        if not res.get("success"):
            print("Error query quotes:", res)
            break
        batch = res.get("result", [])
        if not batch:
            break
        all_quotes.extend(batch)
        if len(batch) < batch_size:
            break
        offset += batch_size

    print(f"Fetched {len(all_quotes)} Quotes for 2026.")
    
    quote_csv_path = "/home/jom/SynologyDrive/AI Dashboard/RAW_Data/2_Quote_Data.csv"
    with open(quote_csv_path, 'w', encoding='utf-8') as f:
        f.write("quote_id,sales_id,client_id,client_name,equipment_brand,value_thb,stage,probability_pct,created_date,aging_days,status,lost_reason\n")
        for q in all_quotes:
            q_no = q.get('quote_no', '')
            subject = q.get('subject', '')
            total = q.get('hdnGrandTotal', '0')
            account = q.get('account_id', '')
            date = q.get('createdtime', '')
            stage = q.get('quotestage', '')
            f.write(f'"{q_no}","","{account}","","",{total},"{stage}","","{date}","","",""\n')

    total_quote_val = sum(float(q.get('hdnGrandTotal', 0) or 0) for q in all_quotes)
    print(f"Total 2026 Quotes Value: {total_quote_val:,.2f} THB")

except Exception as e:
    print(f"CRM Quotes fetch note: {e}")

