#!/bin/sh
# eps-watch.sh — ช่องรับคำสั่งของ NAS ผ่านไฟล์ที่ sync มาจาก Google Drive
#
# หลักการ: เขียนชื่องานลงไฟล์  <โฟลเดอร์งาน>/_control/request.txt  (จากเครื่องไหนก็ได้)
#          ไฟล์จะ sync ไป NAS ภายใน ~1-3 นาที แล้วตัวนี้ (cron ทุก 1 นาที) จะรันงานให้
#          ผลลัพธ์ถูกเขียนกลับเป็น  _control/result-<งาน>.txt  (sync กลับมาให้อ่าน)
#
# งานที่รองรับ (เท่านี้เท่านั้น — ไม่รับคำสั่ง shell อะไรทั้งสิ้น):
#   daily | weekly | monthly   = รัน ETL โหมดนั้น
#   health                     = รายงานสถานะเซิร์ฟเวอร์ + cron + ไฟล์รหัส
#   restart                    = สั่งปิดเซิร์ฟเวอร์ (cron จะปลุกใหม่ใน ~1 นาที)
#
# ไฟล์ที่ติดตั้งโดย: nas-bootstrap.sh (v7+)

PROJ="/volume1/Work/Jom Work/JOM/AI Dashboard"
CTL="$PROJ/_control"
REQ="$CTL/request.txt"
LOG="$CTL/watch.log"
BEAT="$CTL/watch-heartbeat.txt"
ALLOWED="daily weekly monthly health restart"

[ -d "$CTL" ] || exit 0

# --- heartbeat (เขียนอย่างมากทุก 5 นาที ไม่ให้ sync รกเกินไป) ---
NOW=$(date +%s)
LAST=$(cat "$BEAT" 2>/dev/null | tr -dc '0-9')
[ -z "$LAST" ] && LAST=0
if [ $((NOW - LAST)) -gt 300 ]; then
    echo "$NOW" > "$BEAT" 2>/dev/null
fi

[ -f "$REQ" ] || exit 0

JOB=$(tr -d '\r\n\t ' < "$REQ" | head -c 40)

case " $ALLOWED " in
    *" $JOB "*)
        # ตรงกับงานที่รองรับ → รัน
        ;;
    *)
        # ไม่ตรง: ถ้าเป็นคำขึ้นต้นของงานที่รองรับ = ไฟล์ยัง sync ไม่ครบ → รอรอบหน้า
        for w in $ALLOWED; do
            case "$w" in
                "$JOB"*) exit 0 ;;
            esac
        done
        # เป็นคำที่ไม่รองรับจริง ๆ → ย้ายไปเก็บไว้ ไม่รัน
        mkdir -p "$CTL/rejected" 2>/dev/null
        BAD=$(printf '%s' "$JOB" | tr -c 'A-Za-z0-9._-' '_')
        mv -f "$REQ" "$CTL/rejected/$(date +%Y%m%d-%H%M%S)-$BAD.txt" 2>/dev/null || rm -f "$REQ"
        exit 0
        ;;
esac

# ย้าย request ออกก่อนทำงาน เพื่อกันรันซ้ำ (cron ทุก 1 นาที)
mv -f "$REQ" "$CTL/last-request.txt" 2>/dev/null || exit 0

OUT="$CTL/result-$JOB.txt"
{
    echo "=== job: $JOB ==="
    echo "start : $(date '+%F %T')"
    echo "host  : $(hostname)   user: $(id -un)"
    echo
    case "$JOB" in
        daily|weekly|monthly)
            cd "$PROJ" || exit 1
            python3 run_sync.py "$JOB" 2>&1
            ;;
        health)
            echo "--- listening :8090 ---"
            netstat -lnt 2>/dev/null | grep ':8090 '
            echo "--- crontab (eps-*) ---"
            grep 'eps-' /etc/crontab 2>/dev/null
            echo "--- auth file ---"
            ls -l /etc/eps-auth 2>/dev/null
            awk -F: '{print "user=" $1 " passlen=" length($2)}' /etc/eps-auth 2>/dev/null
            echo "--- server log (tail) ---"
            tail -5 /tmp/eps-serve.log 2>/dev/null
            echo "--- python / data ---"
            python3 -V
            ls -lt "$PROJ/RAW_Data" 2>/dev/null | head -5
            ;;
        restart)
            pkill -f eps-serve.py 2>/dev/null
            echo "server stopped — eps-dash.sh (cron) will relaunch within 1 minute"
            ;;
    esac
    echo
    echo "end   : $(date '+%F %T')"
} > "$OUT" 2>&1

echo "$(date '+%F %T') job=$JOB -> $OUT" >> "$LOG" 2>/dev/null
exit 0
