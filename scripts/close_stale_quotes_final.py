import json, sys
from datetime import date, datetime
sys.path.insert(0, '/home/jom/SynologyDrive/AI Dashboard/scripts')
import crm_query as cq

TODAY = date.today()
u, k = cq.creds()
sess = cq.login(u, k)
print('login ok as:', u, flush=True)

contact_cache = {}

def contact_for(acc):
    if not acc: return None
    if acc in contact_cache: return contact_cache[acc]
    q = "SELECT id FROM Contacts WHERE account_id = '%s' LIMIT 1;" % acc
    r = cq.api({'operation': 'query', 'sessionName': sess, 'query': q})
    b = r.get('result', []) if r.get('success') else []
    contact_cache[acc] = b[0]['id'] if b else None
    return contact_cache[acc]

def stale_pending():
    ids, off = [], 0
    while True:
        q = "SELECT id, createdtime FROM Quotes WHERE cf_872 = 'Pending' LIMIT %d, 100;" % off
        r = cq.api({'operation': 'query', 'sessionName': sess, 'query': q})
        b = r.get('result', []) if r.get('success') else []
        if not b: break
        for x in b:
            cd = (x.get('createdtime') or '')[:10]
            if cd:
                try:
                    d = datetime.strptime(cd, '%Y-%m-%d').date()
                    if (TODAY - d).days > 180: ids.append(x['id'])
                except Exception: pass
        off += 100
        if len(b) < 100: break
    return ids

updated, skipped, failed = 0, 0, 0
for rnd in range(1, 8):
    ids = stale_pending()
    if not ids:
        print('round %d: no stale pending left' % rnd, flush=True)
        break
    print('round %d: %d stale quotes to close' % (rnd, len(ids)), flush=True)
    for qid in ids:
        ret = cq.api({'operation': 'retrieve', 'sessionName': sess, 'id': qid})
        rec = ret.get('result', {}) if ret.get('success') else {}
        if not rec:
            failed += 1; continue
        rec['cf_872'] = 'Loss'
        if not str(rec.get('comment') or '').strip():
            rec['comment'] = '-'
        if not str(rec.get('contact_id') or '').strip():
            c = contact_for(rec.get('account_id'))
            if not c:
                skipped += 1
                continue
            rec['contact_id'] = c
        upd = cq.api({'operation': 'update', 'sessionName': sess, 'element': json.dumps(rec)}, method='POST')
        if upd.get('success'): updated += 1
        else:
            failed += 1
            if failed <= 3: print('  fail', qid, upd.get('error'), flush=True)

print('DONE. updated=%d skipped_no_contact=%d failed=%d' % (updated, skipped, failed), flush=True)
