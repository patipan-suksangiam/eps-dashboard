# 🖥️ ติดตั้งฝั่ง Synology — EPS Dashboard Data Host

ทำตามลำดับ ใช้เวลา ~30 นาที (ไม่รวมรอโดเมน Active)
เป้าหมาย: NAS เสิร์ฟไฟล์ `RAW_Data/*.csv` พร้อม CORS → Cloudflare Tunnel → แดชบอร์ดบน GitHub Pages อ่านได้

---

## 0) เตรียมของบน NAS

1. **คัดลอกไฟล์ใหม่เข้า NAS** — โฟลเดอร์งานบน NAS (ที่ ETL รันอยู่) เช่น
   `/volume1/homes/jom/SynologyDrive/AI Dashboard/`
   ต้องมีไฟล์เหล่านี้ (อัปโหลดผ่าน File Station หรือรอ sync):
   - `scripts/serve_raw_data.py` ← **ตัวใหม่ ลำคัญสุด**
   - `deploy/synology/docker-compose.yml`, `.env.example`
2. ติดตั้ง **Container Manager** (Package Center → ค้นหา → Install) — ต้องมี DSM 7.2 ขึ้นไป
3. เช็คว่า `RAW_Data/` มีไฟล์ CSV อยู่จริง (ให้ ETL เขียนไว้แล้ว)

---

## 1) วิธี A — Container Manager (แนะนำ)

เปิด Container Manager → **Project → Create**

| ช่อง | ใส่ |
|---|---|
| Project name | `eps-data` |
| Path | `/docker/eps-data` (สร้างใหม่) |
| Source | **Create docker-compose.yml** (วางเนื้อหาจากไฟล์ในโปรเจกต์) |

วางเนื้อหา `docker-compose.yml` แล้วสร้างไฟล์ `.env` ในโฟลเดอร์โปรเจกต์เดียวกัน
(ใช้ `.env.example` เป็นต้นแบบ — แก้ `RAW_DIR`, `SCRIPTS_DIR`, `TUNNEL_TOKEN`)

> ตั้ง Project ให้ **Auto-restart = Yes** เพื่อให้กลับมาทำงานเองหลังรีบูต DSM

กด **Build/Start** แล้วรอ 2 คอนเทนเนอร์เป็นสีเขียว: `eps-data`, `eps-tunnel`

**ทดสอบบน NAS (ผ่าน SSH หรือ Task Scheduler → Run Now):**
```bash
curl -sD - -o /dev/null \
  -H "Origin: https://patipan-suksangiam.github.io" \
  http://127.0.0.1:8091/0_EPS_Overview_2026.csv | grep -i access-control
# ต้องเห็น: Access-Control-Allow-Origin: https://patipan-suksangiam.github.io
```

---

## 2) วิธี B — Task Scheduler (ไม่ใช้ Docker)

ใช้เมื่อมี `python3` ใน NAS อยู่แล้ว (เช็คก่อนด้วย `python3 --version`)

**Control Panel → Task Scheduler → Create → Triggered Task → Boot-up**

- User: `root`
- Task Settings → User-defined script:
```bash
nohup /usr/local/bin/python3 "/volume1/homes/jom/SynologyDrive/AI Dashboard/scripts/serve_raw_data.py" \
  --port 8091 \
  --dir "/volume1/homes/jom/SynologyDrive/AI Dashboard/RAW_Data" \
  --allow-origin https://patipan-suksangiam.github.io \
  >> "/volume1/homes/jom/SynologyDrive/AI Dashboard/data_host.log" 2>&1 &
```
- ถ้า `python3` ไม่มี → ใช้ **วิธี A** แทน (ใน container มี Python ให้แน่นอน)
- ทดสอบด้วย `curl` แบบเดียวกับข้อ 1

---

## 3) ต่อ Cloudflare Tunnel

1. Zero Trust → **Networks → Tunnels → Create a tunnel** → Cloudflared → ชื่อ `eps-data`
2. แท็บ Docker → คัดลอก token → ใส่ใน `.env` (`TUNNEL_TOKEN=...`)
3. แท็บ **Public Hostname → Add a public hostname**
   - Subdomain `data` · Domain `<โดเมนที่อยู่บน Cloudflare>`
   - Service **HTTP** → `127.0.0.1:8091`
4. Restart โปรเจกต์ → เปิด `https://data.<โดเมน>/0_EPS_Overview_2026.csv` ต้องได้ CSV

---

## 4) ทดสอบจากเครื่องอื่น

```bash
# ต้องได้ header CORS + ข้อมูล
curl -sD - -o /dev/null -H "Origin: https://patipan-suksangiam.github.io" \
  https://data.<โดเมน>/0_EPS_Overview_2026.csv | grep -i "access-control\|HTTP"
```
แล้วส่ง URL `https://data.<โดเมน>/` ให้ผม → ผมตั้ง `config.js` + push + ทำ cutover ให้

---

## 5) ปัญหาที่เจอบ่อย

| อาการ | สาเหตุ / แก้ |
|---|---|
| 502 จาก Cloudflare | `eps-data` ยังไม่ขึ้น หรือ Service ใน hostname ผิดพอร์ต (ต้องเป็น `127.0.0.1:8091`) |
| โหลด CSV ได้ แต่แดชบอร์ดขึ้นค่าว่าง | CORS: `ALLOW_ORIGIN` ต้องตรงเป๊ะ (มี `https://` แต่ **ห้ามมี `/` ปิดท้าย**) |
| `permission denied` อ่าน CSV | สิทธิ์โฟลเดอร์ — mount แบบ read-only แล้วต้องให้ user ที่ container ใช้เข้าถึงได้ (ใน Docker เป็น root) |
| tunnel ต่อไม่ติด | token ผิด/หมดอายุ → สร้างใหม่ใน Zero Trust แล้วอัปเดต `.env` + restart |
| แก้ค่าแล้วไม่เปลี่ยน | Container Manager → Project → **Action → Build/Restart** (แก้ `.env` ต้อง restart) |

---

## 6) ทางเลือก: เสิร์ฟ "ทั้งเว็บ" จาก NAS (ไม่ใช้ GitHub เลย)

สคริปต์ตัวเดียวกันรองรับโหมดเสิร์ฟทั้งแอป + ข้อมูลจาก origin เดียว (ไม่ต้องมี CORS):

```bash
python3 "<โฟลเดอร์งาน>/scripts/serve_raw_data.py" \
  --port 8090 --bind 0.0.0.0 \
  --root "<โฟลเดอร์งาน>"          # โฟลเดอร์โปรเจกต์ (ที่มี Dashboard_App/ และ RAW_Data/)
```
เปิดที่ `http://<nas>:8090/` → redirect เข้า `Dashboard_App/index.html` เอง

ถ้าใช้ Container Manager ให้แก้ `command:` ของบริการ `eps-data` เป็น:
```yaml
    command: >
      python /app/serve_raw_data.py
      --bind 0.0.0.0 --port 8090 --root /data
    volumes:
      - "${PROJECT_DIR}:/data:ro"     # โฟลเดอร์โปรเจกต์ ไม่ใช่แค่ RAW_Data
      - "${SCRIPTS_DIR}:/app:ro"
    ports:
      - "8090:8090"                   # ให้เครื่องในวง LAN เข้าได้ (หรือ 127.0.0.1 ถ้าใช้แต่ tunnel)
```

**ความปลอดภัยในโหมดนี้** — สคริปต์บล็อกให้อัตโนมัติ: โฟลเดอร์/ไฟล์ที่ขึ้นต้นด้วย `.` หรือ `_` (เช่น `.git/`, `_CORE_Private/`),
ไฟล์นอก allowlist (`.py`, `.md`, `.env`, `.log`, `.xlsx`), path traversal, และไม่มีการ list directory
(ทดสอบแล้ว: `_CORE_Private/crm_credentials.json`, `.git/config`, `README.md`, `scripts/*.py` → 404 ทั้งหมด)

**วิธีเผยแพร่ให้คนอื่นเข้า** (เลือกอย่างเดียว):
- **Tailscale Funnel** → `tailscale funnel 8090` ได้ URL `https://<nas>.<tailnet>.ts.net/` (ไม่ต้องมีโดเมน)
- **เฉพาะคนใน tailnet** → `http://<nas-tailnet-ip>:8090/` ปลอดภัยสุด แต่คนใช้ต้องติดตั้ง Tailscale
  (แผนฟรีให้ 3 users — ถ้าทั้งทีมเกินนี้ต้องดูแผนเสียเงิน)
