# NAS Deployment Runbook — EPS Dashboard บน Synology (JOM-NAS)

> อัปเดตล่าสุด: **2026-10-09** · ใช้คู่กับ `deploy/synology/nas-bootstrap.sh` (v6)
> เอกสารนี้ **ไม่มีรหัสผ่าน/token** โดยตั้งใจ (repo นี้เป็น public) — รหัสดูใน `G:\My Drive\JOM\MD File\ปลาวาฬ-คู่มือ-NAS-EPS-Dashboard.md`

---

## 1. ภาพรวมสถาปัตยกรรม

```
CRM / Google Sheets / DBD  ──(ETL รันบน NAS ตาม cron)──►  RAW_Data/*.csv
        ▲                                                      │
        │                                          Google Drive  G:\My Drive\JOM\AI Dashboard
        │                                                      │  (sync ↔ NAS เกือบ real-time ~1-3 นาที)
        └──────────────►  แดชบอร์ดถูกเสิร์ฟจาก NAS เอง (:8090) ◄─┘
                                   │
                    ┌──────────────┴───────────────┐
              Tailscale (ในทีม)             Tailscale Funnel (สาธารณะ)
              http://100.66.192.63:8090     หน้าเว็บ + รหัส Basic Auth
```

- `serve_raw_data.py` โหมด `--root` = เสิร์ฟ **ทั้งแอป + ข้อมูล** จาก origin เดียว (ไม่ต้องใช้ CORS)
- เสิร์ฟทุกอย่างผ่าน **รหัส Basic Auth** — ไฟล์ซีเคร็ต (`_CORE_Private/*`, `*.py`, `*.md`, `.git/*`) ตอบ 404
- **GitHub เก็บแค่โค้ด** — ไม่มีข้อมูลบริษัท, ปิด GitHub Pages แล้ว (2026-10-09)

---

## 2. ของที่ติดตั้งบน NAS

| ไฟล์ | หน้าที่ |
|---|---|
| `/usr/local/bin/eps-serve.py` | ตัวเซิร์ฟเวอร์ (สำเนาของ `scripts/serve_raw_data.py`) |
| `/usr/local/bin/eps-dash.sh` | ปลุกเซิร์ฟเวอร์ถ้ายังไม่รัน — cron ตรวจทุก 1 นาที |
| `/usr/local/bin/eps-etl.sh [daily\|weekly\|monthly]` | รัน ETL |
| `/etc/eps-auth` | รหัส Basic Auth (โหมด 600, อ่านได้เฉพาะ root) |
| `/tmp/eps-serve.log` · `/tmp/eps-etl-daily.log` | log ของเซิร์ฟเวอร์ / ETL |

`/etc/crontab` (บรรทัดที่ระบบนี้เพิ่ม):
```cron
* * * * *   root  /usr/local/bin/eps-dash.sh
15 12 * * * root  /usr/local/bin/eps-etl.sh daily
0 0 * * *   root  /usr/local/bin/eps-etl.sh daily
0 0 * * 0   root  /usr/local/bin/eps-etl.sh weekly     # visit report
0 0 1 * *   root  /usr/local/bin/eps-etl.sh monthly    # client master / macro / BOI / DBD
```

---

## 3. เข้าใช้งาน

| ทาง | ที่อยู่ | หมายเหตุ |
|---|---|---|
| ในออฟฟิศ (LAN) | `http://192.168.1.5:8090/` | เร็วสุด |
| Tailscale (ทุกที่ ไม่ผ่านเน็ตสาธารณะ) | `http://100.66.192.63:8090/` | ต้องติดตั้ง Tailscale + ล็อกอินบัญชีบริษัท |
| สาธารณะ (Funnel) | URL + รหัส → ดูในโน้ตส่วนตัว (`MD File`) | สำหรับคนที่ไม่มี Tailscale |

> ลิงก์ GitHub Pages เดิม (`patipan-suksangiam.github.io/eps-dashboard`) **ใช้ไม่ได้แล้ว** โดยตั้งใจ

---

## 4. เปลี่ยนรหัสแดชบอร์ด

```sh
echo 'eps:รหัสใหม่' > /etc/eps-auth
chmod 600 /etc/eps-auth
pkill -f eps-serve.py        # cron จะปลุกใหม่ภายใน ~1 นาที
```
รหัสเป็นแบบ HTTP Basic Auth → เบราว์เซอร์จะจำไว้จนปิดโปรแกรม

---

## 5. ติดตั้ง / ซ่อม / รีเฟรช

1. DSM → **Control Panel → Task Scheduler → task `EPS bootstrap` → Run**
2. สคริปต์เป็น **idempotent** — ดาวน์โหลดโค้ดเซิร์ฟเวอร์ใหม่ + เขียน launcher + เติม cron ที่ขาด (รหัสเดิมไม่ถูกทับ)
3. ผลลัพธ์: `/tmp/eps_bootstrap_report.txt`

> ระบบนี้ **ไม่มี SSH** (ปิดไว้เพื่อความปลอดภัย) — DSM Task Scheduler คือช่องทางเดียวในการรันคำสั่งบน NAS

## 5b. สั่งงานผ่านไฟล์ (ช่องทางหลัก — ไม่ต้อง SSH ไม่ต้องกดอะไร)

`eps-watch.sh` (cron ทุก 1 นาที) เฝ้าดู `<โฟลเดอร์งาน>/_control/request.txt` ซึ่ง sync มาจาก Google Drive:

```sh
# จากเครื่องไหนก็ได้ (เช่น Windows):
echo monthly > "G:/My Drive/JOM/AI Dashboard/_control/request.txt"
# รอ 1-3 นาที (sync) + 1 นาที (cron) → งานรัน → ผลอยูที่ _control/result-monthly.txt
```

| request | ทำอะไร |
|---|---|
| `daily` / `weekly` / `monthly` | รัน ETL โหมดนั้น (ผลใน `result-<โหมด>.txt`) |
| `health` | รายงานสถานะ: พอร์ต 8090, cron, ไฟล์รหัส, log, ไฟล์ข้อมูลล่าสุด |
| `restart` | ปิดเซิร์ฟเวอร์ (cron จะปลุกใหม่ใน ~1 นาที) |

- รับ **เฉพาะคำในรายการนี้เท่านั้น** — คำสั่ง shell หรือคำอื่นจะถูกย้ายไป `_control/rejected/` โดยไม่รัน (ทดสอบแล้ว)
- `_control/watch-heartbeat.txt` = เวลาที่ watcher ทำงานล่าสุด (เขียนทุก ~5 นาที) → ใช้ยืนยันว่าระบบยังอยู่
- โฟลเดอร์ `_control/` ไม่ถูก commit (อยู่ใน `.gitignore`)

---

## 6. ตรวจสุขภาพระบบ (แก้ปัญหาเร็ว)

```sh
netstat -lnt | grep ':8090 '            # ต้องมี LISTEN  (DSM ไม่มี pgrep!)
tail -20 /tmp/eps-etl-daily.log         # ต้องเจอ '=== daily done ==='
curl -I http://127.0.0.1:8090/          # 401 = ปกติ (ต้องใส่รหัส)
curl -u eps:รหัส -I http://127.0.0.1:8090/   # 200 = ปกติ
```

**ทดสอบ self-heal** (พิสูจน์ว่ากลับมาเองได้):
```sh
pkill -f eps-serve.py ; sleep 60 ; netstat -lnt | grep ':8090 '   # กลับมาใน ~15-60 วิ
```

**ทดสอบ ETL เดี๋ยวนี้โดยไม่รอ cron** (แบบไม่ให้ค้าง — ใช้ cron เป็นตัวรัน):
```sh
touch /tmp/eps-etl.once
printf '* * * * *\troot\t/usr/local/bin/eps-etl-once.sh\n' >> /etc/crontab
# โดย eps-etl-once.sh = ลบ marker แล้วเรียก eps-etl.sh daily  (ยิงครั้งเดียว)
# เสร็จแล้วอย่าลืม: sed -i '/eps-etl-once/d' /etc/crontab
```
> ETL ใช้เวลา ~4-6 นาที (ขั้น `pull_crm_analytics` นานสุด) — อย่าตัดสินว่า "ตาย" จาก `ps`

---

## 7. กับดักที่เจอจริง (อ่านก่อนแก้)

| เรื่อง | อาการ | ทางแก้ |
|---|---|---|
| **DSM ไม่มี `pgrep`** | สคริปต์เช็คโปรเซสล้มเงียบ ๆ แล้วสตาร์ทซ้อน | ใช้ `netstat -lnt \| grep ':8090 '` |
| **`ps` มองไม่เห็น process ของ cron** | เข้าใจผิดว่าตายแล้วสั่งรันซ้ำ | ดูจาก log/mtime ของไฟล์แทน |
| **Tailscale SSH กับ Synology** | เชื่อมไม่ได้ | ตัวโปรแกรมตอบเองว่า *"The Tailscale SSH server does not run on Synology"* → ใช้ Task Scheduler |
| **SSH ของ DSM** | ปฏิเสธทุกรหัส/ทุญแจ (แม้ root) | เป็นข้อจำกัดที่ชั้น PAM ของ DSM — อย่าเสียเวลาต่อสู้ |
| **สั่งรัน process เบื้องหลังผ่านช่องทาง remote** | คำสั่งค้างจนหมดเวลา | อย่าทำ — ยัดลง cron ให้รันเองแทน |
| **`pkill -f <pattern>`** | ฆ่าตัวเอง (pattern อยู่ใน argv ของคำสั่งเอง) | ใช้ trick วงเล็บ เช่น `serve_raw_[d]ata.py` |
| **`git filter-branch` บนพาธ Google Drive** | `fatal: not a git repository` (MSYS แปลงพาธไม่ได้) | ใช้ `git checkout --orphan` → `git add -A` → `git branch -M` (squash ประวัติแทน) |
| **คำสั่ง bash ฝังใน Task Scheduler** | เครื่องหมายคำพูดพัง | ใช้ไฟล์ `.sh` แล้วให้ task เรียกไฟล์ |

---

## 8. กฎความปลอดภัย (ห้ามลืม)

- **ห้าม commit**: `RAW_Data/`, `CRM_AssignTo_*.csv`, `Plan_SalesOrder.csv`, `_CORE_Private/`, `.env`, token/รหัสใด ๆ — กันไว้ใน `.gitignore` แล้ว
- **ห้ามฝัง token ของ agent ลงสคริปต์ที่จะขึ้น repo public** — เคยพลาด 2026-10-09 (ถอด agent + ล้างประวัติ git แล้ว)
- ไฟล์ที่ต้องตอบ **404** เสมอ: `_CORE_Private/*`, `*.py`, `*.md`, `.git/*`
- ข้อมูลบริษัทออกนอกบริษัทได้เฉพาะช่องทางที่มีรหัส (NAS) เท่านั้น

---

## 9. บั๊กที่แก้แล้ว (กันกลับมา)

| อาการใน log | สาเหตุ | วิธีแก้ |
|---|---|---|
| `SO FAILED rc=1: NameError: name 'BASE' is not defined` | `pull_so_2026.py` อ้างตัวแปร `BASE` ที่ไม่มีอยู่ | ประกาศ `CRM_BASE = "https://crm.siamrajpump.com/webservice.php"` แล้วเรียกใช้ |
| ยอด SO ผิดช่วงปี | `--year` default = `2024` | ตั้ง default = ปีที่แดชบอร์ดแสดง (2026 → อัปเดตเมื่อขึ้นปีใหม่) |
| `inventory FAILED` / `gdrive FAILED` บน NAS | `rclone` ไม่มีบน NAS | ไม่ต้องใช้ — โฟลเดอร์ sync ผ่าน Google Drive ของ Synology อยู่แล้ว |

---

## 10. ลิงก์
- โค้ด: `github.com/patipan-suksangiam/eps-dashboard` (public — โค้ดเท่านั้น)
- โน้ต/รหัส (ส่วนตัว): `G:\My Drive\JOM\MD File\ปลาวาฬ-คู่มือ-NAS-EPS-Dashboard.md`
- สถานะเครื่อง: `G:\My Drive\JOM\MD File\ปลาวาฬ-เครื่องที่-3.md`
