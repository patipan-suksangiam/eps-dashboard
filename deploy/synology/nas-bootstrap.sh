#!/bin/sh
# EPS Dashboard — NAS bootstrap v7 (รันเป็น root จาก DSM Task Scheduler)
#
# v7 = v6 + ช่องรับคำสั่งผ่านโฟลเดอร์ _control (sync ผ่าน Google Drive) → ไม่ต้อง SSH อีก
# v6 ติดตั้งเฉพาะของถาวร — ไม่มี agent ระยะไกล และไม่มีรหัส/token ฝังในไฟล์:
#   1) /usr/local/bin/eps-serve.py  — ตัวเซิร์ฟเวอร์แดชบอร์ด (ดาวน์โหลดจาก GitHub)
#   2) /etc/eps-auth                — รหัส Basic Auth (สร้างให้เฉพาะเมื่อยังไม่มี)
#   3) /usr/local/bin/eps-dash.sh   — ตัวปลุกเซิร์ฟเวอร์ + crontab ตรวจทุก 1 นาที
#   4) /usr/local/bin/eps-etl.sh    — ตัวรัน ETL + crontab (12:15, 00:00, อาทิตย์, วันที่ 1)
#
# รันซ้ำได้เสมอ (idempotent) · ผลลัพธ์เขียนไว้ที่ $REPORT
#
# เปลี่ยนรหัสแดชบอร์ด:
#     echo 'eps:รหัสใหม่' > /etc/eps-auth ; chmod 600 /etc/eps-auth
#     pkill -f eps-serve.py     # แล้วรอ ~1 นาที ให้ cron ปลุกกลับมา
#
# ถอดออกทั้งหมด:
#     sed -i '/eps-dash.sh/d;/eps-etl.sh/d' /etc/crontab
#     rm -f /usr/local/bin/eps-serve.py /usr/local/bin/eps-dash.sh /usr/local/bin/eps-etl.sh /etc/eps-auth

PROJ="/volume1/Work/Jom Work/JOM/AI Dashboard"
PORT=8090
AUTHFILE=/etc/eps-auth
RAW=https://raw.githubusercontent.com/patipan-suksangiam/eps-dashboard/master/scripts/serve_raw_data.py
RAW_WATCH=https://raw.githubusercontent.com/patipan-suksangiam/eps-dashboard/master/deploy/synology/eps-watch.sh
REPORT=/tmp/eps_bootstrap_report.txt

: > "$REPORT"
say() { echo "$@" >> "$REPORT"; }

say "=== EPS NAS bootstrap v7 ==="
say "date        : $(date)"
say "who         : $(id)"

# ---------- 1) server code ----------
if curl -fsSL "$RAW" -o /usr/local/bin/eps-serve.py && python3 -m py_compile /usr/local/bin/eps-serve.py; then
    say "server code : ok ($(wc -c < /usr/local/bin/eps-serve.py) bytes)"
else
    say "server code : FAILED — ตรวจการเชื่อมต่ออินเทอร์เน็ต/GitHub"
fi

# ---------- 1b) command watcher — รับงานผ่านโฟลเดอร์ _control ที่ sync มา ----------
if curl -fsSL "$RAW_WATCH" -o /usr/local/bin/eps-watch.sh && sh -n /usr/local/bin/eps-watch.sh; then
    chmod 755 /usr/local/bin/eps-watch.sh
    mkdir -p "$PROJ/_control"
    grep -q 'eps-watch.sh' /etc/crontab 2>/dev/null || \
        printf '* * * * *\troot\t/usr/local/bin/eps-watch.sh >/dev/null 2>&1\n' >> /etc/crontab
    say "watcher     : ok — รับงานจาก /_control/request.txt (daily|weekly|monthly|health|restart)"
else
    say "watcher     : FAILED — ตรวจการเชื่อมต่ออินเทอร์เน็ต/GitHub"
fi

# ---------- 2) credentials (สร้างครั้งเดียว ไม่ทับของเดิม) ----------
if [ ! -f "$AUTHFILE" ]; then
    printf 'eps:CHANGE_ME\n' > "$AUTHFILE"
    say "auth file   : created (รหัสเริ่มต้น CHANGE_ME — เปลี่ยนตามวิธีด้านบน)"
else
    say "auth file   : มีอยู่แล้ว (คงรหัสเดิมไว้)"
fi
chmod 600 "$AUTHFILE"

# ---------- 3) dashboard launcher + cron ----------
printf '%s\n' '#!/bin/sh' \
  "P=\"$PROJ\"" \
  "if netstat -lnt 2>/dev/null | grep -q \":$PORT \"; then exit 0; fi" \
  'cd "$P" || exit 1' \
  "setsid nohup python3 /usr/local/bin/eps-serve.py --port $PORT --bind 0.0.0.0 --root \"\$P\" --auth-file $AUTHFILE >> /tmp/eps-serve.log 2>&1 < /dev/null &" \
  > /usr/local/bin/eps-dash.sh
chmod 755 /usr/local/bin/eps-dash.sh

if [ -f /etc/crontab ]; then
    grep -q 'eps-dash.sh' /etc/crontab 2>/dev/null || \
        printf '* * * * *\troot\t/usr/local/bin/eps-dash.sh >/dev/null 2>&1\n' >> /etc/crontab
fi
say "crontab     : $(grep -c 'eps-dash.sh' /etc/crontab 2>/dev/null) dash line(s)"

# ---------- 4) ETL runner + cron ----------
printf '%s\n' '#!/bin/sh' \
  "cd \"$PROJ\" || exit 1" \
  'MODE="${1:-daily}"' \
  'python3 run_sync.py "$MODE" >> "/tmp/eps-etl-$MODE.log" 2>&1' \
  > /usr/local/bin/eps-etl.sh
chmod 755 /usr/local/bin/eps-etl.sh

if [ -f /etc/crontab ]; then
    grep -q 'eps-etl.sh' /etc/crontab 2>/dev/null || \
        printf '15 12 * * *\troot\t/usr/local/bin/eps-etl.sh daily\n0 0 * * *\troot\t/usr/local/bin/eps-etl.sh daily\n0 0 * * 0\troot\t/usr/local/bin/eps-etl.sh weekly\n0 0 1 * *\troot\t/usr/local/bin/eps-etl.sh monthly\n' >> /etc/crontab
fi
say "crontab     : $(grep -c 'eps-etl.sh' /etc/crontab 2>/dev/null) etl line(s)"

# ---------- 5) start now + verify ----------
/usr/local/bin/eps-dash.sh
sleep 3
say "serving     : $(netstat -lnt 2>/dev/null | grep \":$PORT \" | tr -s ' ' | head -1)"
say "check       : curl -I http://127.0.0.1:$PORT/            -> 401 = ต้องใส่รหัส (ปกติ)"
say "              curl -u user:pass -I http://127.0.0.1:$PORT/  -> 200"
say "=== end v7 ==="

cat "$REPORT"
