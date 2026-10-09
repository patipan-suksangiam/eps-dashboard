import csv, json, os, sys
from datetime import date, datetime

sys.path.insert(0, '/home/jom/SynologyDrive/AI Dashboard/scripts')
import crm_query as cq

TODAY = date.today()
u, k = cq.creds()
sess = cq.login(u, k)
api_user_id = '19x47'

off = 0
updated_cnt = 0
failed_cnt = 0
contact_cache = {}

def get_contact_for_account(sess, account_id):
    if not account_id: return None
    if account_id in contact_cache: return contact_cache[account_id]
    q = "SELECT id FROM Contacts WHERE account_id = '%s' LIMIT 1;" % account_id
    res = cq.api({'operation': 'query', 'sessionName': sess, 'query': q})
    batch = res.get('result', []) if res.get('success') else []
    cid = batch[0].get('id') if batch else None
    contact_cache[account_id] = cid
    return cid

while True:
    q = f"SELECT id, subject, createdtime, assigned_user_id, account_id, cf_872 FROM Quotes WHERE cf_872 = 'Pending' LIMIT {off}, 100;"
    res = cq.api({'operation': 'query', 'sessionName': sess, 'query': q})
    batch = res.get('result', []) if res.get('success') else []
    if not batch: break
    
    for r in batch:
        cd_str = (r.get('createdtime') or '')[:10]
        if cd_str:
            try:
                cd = datetime.strptime(cd_str, '%Y-%m-%d').date()
                if (TODAY - cd).days > 180:
                    qid = r.get('id')
                    acc_id = r.get('account_id')
                    ret = cq.api({'operation': 'retrieve', 'sessionName': sess, 'id': qid})
                    if ret.get('success') and ret.get('result'):
                        rec = ret['result']
                        rec['cf_872'] = 'Loss'
                        rec['assigned_user_id'] = api_user_id
                        if not rec.get('comment'):
                            rec['comment'] = '-'
                        if not rec.get('contact_id'):
                            c_id = get_contact_for_account(sess, rec.get('account_id') or acc_id)
                            rec['contact_id'] = c_id or '12x1'
                        
                        upd = cq.api({
                            'operation': 'update',
                            'sessionName': sess,
                            'element': json.dumps(rec)
                        }, method='POST')
                        if upd.get('success'):
                            updated_cnt += 1
                        else:
                            failed_cnt += 1
                    else:
                        failed_cnt += 1
            except Exception as e:
                failed_cnt += 1
    off += 100
    if len(batch) < 100: break
    print(f"Progress (>180d): updated={updated_cnt}, failed={failed_cnt}", flush=True)

print(f"DONE. Updated to Loss (>180 days): {updated_cnt}, Failed: {failed_cnt}")
