# 📁 AI Dashboard — โฟลเดอร์หลัก (Single Source of Truth)

> **อัปเดต:** 24 ก.ย. 2569 · โปรเจกต์: **EPS Interactive Dashboard** (Siamraj PLC)
> **นโยบาย:** งานทั้งหมดของ Dashboard อยู่ในโฟลเดอร์นี้ **ที่เดียว** — เพื่อ backup ง่าย ไม่มีสำเนาซ้ำซ้อน

**ที่อยู่:** `/home/jom/SynologyDrive/AI Dashboard`
ข้อยกเว้นเดียว: `_CORE_Private/` (ข้อมูลลับ) ถูก `.gitignore` ไม่ขึ้น GitHub แต่ยังอยู่ในโฟลเดอร์นี้เพื่อ backup บน Synology

---

## 📂 โครงสร้างโฟลเดอร์

| เส้นทาง | คืออะไร |
|---|---|
| `Dashboard_App/` | เว็บแอป (SPA) — `index.html`, `js/`, `css/`, `views/` — renderer: `eps_overview.js`, `stock.js`, `groups.js` (Group A–D/R), `economic.js` |
| `RAW_Data/` | ข้อมูล CSV ทั้ง 10 ชุดที่ Dashboard ใช้ (ข้อมูลจริง) |
| `scripts/` | สคริปต์ดึง/ประกอบ/ปรับปรุงข้อมูล **17 ตัว** — `build_boi`, `build_dbd`, `build_group_analytics`, `build_group_detail`, `build_macro`, `build_open_quotes`, `build_overview`, `build_sales_reps`, `clean_inventory`, `close_old_quotes`, `close_stale_quotes_final`, `crm_query`, `monthly_oie_update`, `pull_crm_analytics`, `pull_crm_data`, `update_capu_from_oie`, `write_groups_file` |
| `_CORE_Private/` | ข้อมูลลับ/กลยุทธ์ (credential, BOI, DIW, Capacity, Core Plan) — **ห้ามขึ้น GitHub** |
| `venv/` | Python venv สำหรับรันสคริปต์ |
| `etl_script.py` | ETL service (loop ตั้งเวลาเอง) ดึง Inventory + SO + Hot Jobs |
| `run_sync.py` | **ตัวรันหนึ่งครั้ง** (`daily`/`weekly`/`monthly`) สำหรับ cron |
| `pull_so_2026.py`, `pull_hotjobs_2026.py` | สคริปต์ดึงข้อมูลเดิม (ยังใช้อยู่) |
| `_superseded/` | สคริปต์เก่า/มี mock data — **ห้ามรัน** (ดู `_superseded/README.md`) |
| `etl_sync.log` | บันทึกการรัน ETL ล่าสุด |
| `*.md` | เอกสาร: `README_Architecture.md`, `README_ETL_Service.md`, `Data_Dictionary_and_Schedule.md`, `data_sources.md`, `data_cleaning_notes.md`, `app_architecture.md`, `HANDOFF_ปลาวาฬ_2026-09-23.md` |
| `EPS_Dashboard_Architecture.drawio` | แผนผังสถาปัตยกรรม |

---

## 🗄️ ชุดข้อมูล (`RAW_Data/`)

| ไฟล์ | เนื้อหา |
|---|---|
| `0_EPS_Overview_2026.csv` | ภาพรวมยอดขายรายกลุ่ม |
| `0_EPS_HotJobs_2026.csv` | ดีลร้อน (Pending + Chance สูง) |
| `1_CRM_Sales_Person.csv` | พนักงานขาย + ยอดขาย |
| `2_Quote_Data.csv` | ใบเสนอราคาจาก CRM |
| `3_SO_Data.csv` | ใบสั่งขายปี 2026 |
| `4_Visit_Report.csv` | รายงานเยี่ยมลูกค้า (Events) |
| `5_Inventory_Supplier.csv` | คลังสินค้า / Dead Stock |
| `6_Macroeconomic_Data.csv` | เศรษฐกิจมหภาค (OIE/MPI/ธปท.) |
| `7_BOI_Data.csv` | โครงการ BOI |
| `8_DBD_Data.csv` | ทะเบียนโรงงาน DIW / DBD |
| `9_Client_Master.csv` | ทะเบียนลูกค้า (Accounts) |
| `10_Group_Reps.csv` | พนักงานขาย + ยอดขาย แยกตามกลุ่ม (สร้างโดย `build_group_detail.py`) |
| `11_Group_Clients.csv` | ลูกค้า + ยอดขาย/เยี่ยม แยกตามกลุ่ม (สร้างโดย `build_group_detail.py`) |

---

## ⚙️ การตั้งค่า Path (config)

สคริปต์ทุกตัวอ้าง path แบบ absolute มาที่โฟลเดอร์นี้แล้ว:

```
BASE_DIR = "/home/jom/SynologyDrive/AI Dashboard"
```

ไฟล์ที่กำหนด path: `etl_script.py`, `etl_test_sync.py`, `pull_so_2026.py`, `pull_hotjobs_2026.py`, `process_plan_and_quotes.py`, `update_with_real_plan.py`, `update_real_data_2026.py`

- `Dashboard_App/js/app.js` → `DATA_BASE` คำนวณจาก URL เอง (รองรับทั้ง local server และ GitHub Pages) ชี้ไป `../RAW_Data/`
- **ถ้าย้ายโฟลเดอร์นี้** ต้องแก้ `BASE_DIR`/path ในไฟล์ข้างบนให้ตรงที่ใหม่

### ▶️ วิธีรัน (local)
```bash
cd "/home/jom/SynologyDrive/AI Dashboard"
python3 -m http.server 8080          # แล้วเปิด http://localhost:8080/Dashboard_App/index.html
./venv/bin/python etl_script.py      # รัน ETL (loop ตามตารางเวลา)
```

---

## ⏰ Automation / ETL

- **สถานะ:** ✅ ตั้งเป็น **crontab** เรียบร้อย (2026-09-24) — log อยู่ที่ `etl_cron.log`

| เวลา | คำสั่ง |
|---|---|
| ทุกวัน 12:15 และ 00:00 | `run_sync.py daily` (Inventory + SO + HotJobs + Overview) |
| อาทิตย์ 00:20 | `run_sync.py weekly` (Visit Report) |
| วันที่ 1 ของเดือน 00:30 | `run_sync.py monthly` (Sales Person / Macro / BOI / DBD / Client Master + Overview) |
| **วันที่ 1 ของเดือน 00:00** | `scripts/monthly_oie_update.py` — ดึงดัชนี สศอ. 7 ไฟล์ → โฟลเดอร์งาน + แปลง CapU |
| **วันที่ 1 ของเดือน 01:00** | automation *EPS BOI monthly research* — ค้นข่าว BOI ที่อนุมัติใน 1 เดือนที่ผ่านมา → อัปเดต `7_BOI_Data.csv` |
| **วันที่ 2 ของเดือน 08:30** | `run_digest.py --to groups` — เมลสรุป BOI+CapU ถึง 5 กลุ่ม + Cc 5 คน |

- ดู/แก้: `crontab -l` / `crontab -e` (บล็อก `# >>> EPS Dashboard ETL >>>`)
- รันมือได้: `cd "/home/jom/SynologyDrive/AI Dashboard" && python3 run_sync.py daily`
- ทางเลือกอื่น: รัน `etl_script.py` เป็น service ที่ตั้งเวลาในตัว (เหมาะกับ Synology NAS)

---

## ⚠️ ข้อควรระวัง

- `_CORE_Private/` มี credential — **ห้าม commit / ห้ามแชร์**
- สคริปต์ใช้ **Python stdlib เท่านั้น** (`urllib`, `csv`, `json`) — รันด้วย `python3` ระบบได้เลย ไม่ต้องพึ่ง `requests`
- vtiger API ไม่รับ `ORDER BY` และอาจส่งหน้ากลับไม่ครบ 100 แถว → ใช้ helper `paged()` ใน `scripts/pull_crm_data.py` เท่านั้น
- **ยังไม่มี git repo / CI** สำหรับขึ้น GitHub Pages (ต้องตั้งแยก + ทำชั้น Auth ก่อน ตาม `README_Architecture.md`)

---

## ✅ ความถูกต้องของข้อมูล (Data integrity — ตรวจ 24 ก.ย. 2569)

**ไม่มี mockup เหลือในข้อมูลที่ใช้จริง** — ทุกตัวเลขบนหน้าเว็บมาจากแหล่งจริง:

| KPI | ที่มา |
|---|---|
| Revenue YTD / Sales Orders / Active Customers | คำนวณสดจาก `3_SO_Data.csv` (CRM) |
| เป้าแผน (453.55M + แยกรายกลุ่ม) | `Plan_SalesOrder.csv` (ปี 2026) |
| ยอดขายรายกลุ่ม | `build_overview.py` + `group_map.json` |
| Hot Jobs | CRM Quotes (Pending, chance ≥ 70%) |
| Macro / BOI / DBD | OIE · BOI workbook · DIW/DBD |

**ที่ปลดออก/แก้ไปรอบนี้:**
- `RAW_Data/0_EPS_Overview.csv` (mock เก่า) → ย้ายไป `_superseded/`
- `_CORE_Private/0_EPS_Overview_10Year_CORE.csv` → เปลี่ยนชื่อเป็น `_MOCK_DO_NOT_USE_...` (เนื้อหาเป็น mock ไม่ใช่ข้อมูล 10 ปีจริง)
- ลบ KPI `FY2026_Gross_Margin` และ `FY2026_Win_Rate` ออกจาก CSV + หน้าเว็บ เพราะ **ไม่มีแหล่งข้อมูลจริง** (เดิมเป็นค่าฮาร์ดโค้ด) — ถ้ามีแหล่ง (เช่น จากฝ่ายบัญชี) ค่อยเติมกลับ
- `eps_overview.js` เลิกใช้ตัวเลข/กราฟฮาร์ดโค้ด → กราฟสะสมรายเดือนคำนวณสดจาก `3_SO_Data.csv`
- `index.html` ลบประกาศ/วันที่สมมติ และเลิกแสดง test credential บนหน้า login

⚠️ ยังต้องยืนยันแยก: ค่าคงที่ใน `scripts/build_macro.py` (MPI 94.80 · BOT 1.00% · capex 13.4%) มาจากข่าวทางการที่อ้างในเอกสาร — ควรตรวจกับต้นฉบับก่อนใช้ตัดสินใจ

---

1. ~~เขียน renderer หน้า Group A/B/C/D/R + Economic~~ ✅ **เสร็จ 24 ก.ย. 2569** (`js/groups.js`, `js/economic.js`)
2. ชั้น Auth ก่อนขึ้น GitHub Pages (ตอนนี้รหัสอยู่ใน `js/auth.js` ฝั่ง client — View Source เห็น)
3. Data quality: เติม `industry` ลูกค้าที่เหลือ / `contact_person`

---

## 🌐 GitHub Pages & การแยกข้อมูล (2026-10-09)

- **เว็บที่เผยแพร่:** https://patipan-suksangiam.github.io/eps-dashboard/ (repo: `patipan-suksangiam/eps-dashboard`, Public)
- **2 ภาษา:** `Dashboard_App/js/i18n.js` + ปุ่ม `🌐 TH / EN` บน header (ค่าเริ่มต้น ไทย, เก็บใน `localStorage.eps_lang`)
- **Asset version:** `APP_VERSION` ใน `js/app.js` + `?v=` ใน `index.html`/`views/*.html` — **ต้อง bump พร้อมกันทุกไฟล์** ไม่งั้นเบราว์เซอร์จะใช้ไฟล์เก่าจาก cache
- **ที่อยู่ข้อมูล:** `Dashboard_App/js/config.js` → `window.EPS_DATA_BASE`
  ว่าง = โหลด `RAW_Data/` จากเครื่องเดียวกัน · ใส่ URL = โหลดจากโฮสต์ภายนอก
- **แผนแยกข้อมูลออกจาก GitHub:** ดู `DATA_HOSTING_Synology.md` (Synology + Cloudflare Tunnel, ตัวให้บริการไฟล์คือ `scripts/serve_raw_data.py`)
- ⚠️ `RAW_Data/` เคยถูก push ขึ้น repo สาธารณะแล้ว — การลบในคอมมิตใหม่ไม่ลบประวัติ ต้องล้าง history หรือสร้าง repo ใหม่

### 🖥️ ทางเลือก: เสิร์ฟทั้งเว็บจาก NAS (ไม่ใช้ GitHub)
```bash
python3 scripts/serve_raw_data.py --port 8090 --bind 0.0.0.0 --root "<โฟลเดอร์โปรเจกต์>"
# → http://<nas>:8090/  (app + data origin เดียว ไม่ต้องมี CORS)
```
บล็อก `.git/`, `_CORE_Private/`, ไฟล์ `.py/.md/.env/.log` และ path traversal อัตโนมัติ · ดู `deploy/synology/README.md` หัวข้อ 6
