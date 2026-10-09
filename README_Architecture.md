# EPS Dashboard: Architecture & Deployment Guide (GitHub Pages)

ระบบ Dashboard ถูกพัฒนาให้เป็น **Single Page Application (SPA)** สำหรับโฮสต์บน **GitHub Pages** โดยมีการแยกลำดับชั้นตาม Role ของพนักงาน

## 🗺️ Flowchart โครงสร้างระบบ
โครงสร้างระบบและ Data Flow ถูกวาดไว้ในไฟล์ `EPS_Dashboard_Architecture.drawio`

**สรุป Flow การทำงานหลัก 3 ส่วน:**

### 1. Local Data Processing (เครื่อง Local / Synology)
- `etl_script.py` จะดึงข้อมูลจากแหล่งต่างๆ (CRM, ERP, Google Sheets) มาเก็บไว้ใน `RAW_Data/*.csv`
- ระบบจะทำการ `git push` ไฟล์ข้อมูล (CSV) และ Web App (HTML/JS) ขึ้นไปบน GitHub Repository แบบอัตโนมัติ

### 2. CI/CD & Hosting (GitHub)
- **GitHub Repository (Private)** ใช้เก็บซอร์สโค้ดและ CSV
- **GitHub Pages** ทำหน้าที่เสิร์ฟหน้าเว็บแบบ Static
- **Authentication:** เนื่องจากหน้าเว็บเป็นแบบ Static จึงใช้ระบบ Login ฝั่ง Client (Javascript/Firebase) ในการควบคุม Router หากไม่ระบุตัวตน จะมองไม่เห็นข้อมูลใดๆ

### 3. Client Application (SPA)
โครงสร้างแอปพลิเคชัน:
- `index.html`: เป็นจุดศูนย์กลางที่มีระบบ Login เมื่อล็อกอินผ่าน จะแสดงเมนูที่ต่างกันตามสิทธิ์ (Role)
- **Dynamic Routing:** ไฟล์ `js/router.js` จะคอยดึงเนื้อหา (HTML) จากโฟลเดอร์ `views/` มาแสดงตรงกลางจอ (SPA) ทำให้เว็บทำงานเร็วและไม่ต้องเขียนโค้ดซ้ำ
- **Data Fetching:** Javascript ฝั่ง Client (ในเว็บเบราว์เซอร์) จะโหลดไฟล์ `RAW_Data/*.csv` ไปวาดเป็นกราฟ Chart.js

---

## 4. Data Pipeline — Real Data (อัปเดต 23 ก.ย. 2569)

ตอนนี้ `RAW_Data/*.csv` **ทั้ง 10 ไฟล์เป็นข้อมูลจริงทั้งหมด** ไม่มี mock เหลืออยู่ ดึงผ่านสคริปต์ในโฟลเดอร์ `scripts/`:

| ไฟล์ปลายทาง | แถว | สคริปต์ที่ดึง | แหล่งข้อมูลจริง |
|:---|---:|:---|:---|
| `0_EPS_Overview_2026.csv` | 11 | `build_overview.py` (+ `pull_hotjobs_2026.py`) | คำนวณจาก CRM SalesOrder + `group_map.json` |
| `1_CRM_Sales_Person.csv` | 56 (ชื่อจริง 38) | `build_sales_reps.py` | CRM `Users` (ต้องใช้ admin) + เจ้าของใบสั่งขาย |
| `2_Quote_Data.csv` | 18,270 | `process_plan_and_quotes.py` | CRM `Quotes` |
| `3_SO_Data.csv` | 966 | `pull_so_2026.py` | CRM `SalesOrder` |
| `4_Visit_Report.csv` | 17,948 | `pull_crm_data.py visits` | CRM `Events` (Meeting / Call) |
| `5_Inventory_Supplier.csv` | 449 | `etl_script.py` + `clean_inventory.py` | Google Sheets (PM Master, Sale tab) |
| `6_Macroeconomic_Data.csv` | 130 | `build_macro.py` | OIE CapU 129 เซกเตอร์ + MPI 94.80 + ธปท. 1.00% |
| `7_BOI_Data.csv` | 24 | `build_boi.py` | `BOI_Projects_September_2026.xlsx` |
| `8_DBD_Data.csv` | 5,511 (match 30.3%) | `build_dbd.py` | กรมโรงงานอุตสาหกรรม 62,623 โรงงาน + DBD cache |
| `9_Client_Master.csv` | 5,511 | `pull_crm_data.py accounts` | CRM `Accounts` (industry 92%) |

### สคริปต์กลาง
- `scripts/crm_query.py` — wrapper vtiger webservice (อ่าน credential จาก `_CORE_Private/crm_credentials.json` ไม่พิมพ์ออกจอ)
- `scripts/pull_crm_data.py` — ดึง Accounts / Events / owners และมี helper `paged()` ที่ **กันบั๊ก vtiger หน้าที่ส่งกลับไม่ครบ 100 แถว**

### ⚠️ ข้อจำกัดที่ต้องรู้
1. **vtiger ไม่รับ `ORDER BY`** → บางหน้าส่งกลับ 99 แถว แทนที่จะเป็น 100 **ห้ามหยุด loop เมื่อหน้าไหนสั้นกว่า PAGE** ให้ไล่จนกว่าจะได้หน้าว่าง แล้ว dedupe ด้วย `id`
2. **`Users` ต้องใช้ admin (udomlak)** — บัญชีปกติโดน `ACCESS_DENIED`
3. **`cf_892` (industry) โดน `ACCESS_DENIED` ทั้ง user ปกติและ admin** → ใช้ picklist `industry` ของ Accounts แทน (มี 92%)
4. **macOS Cloud File Provider** — ไฟล์ที่ยังไม่ถูก materialize อ่านด้วยสคริปต์ไม่ได้ (`errno 11 Resource deadlock avoided`) → ต้องตั้งโฟลเดอร์เป็น Available offline หรือคัดลอกลงดิสก์ก่อน

### วิธีรัน (runbook)
```bash
cd "AI Dashboard"
python3 scripts/pull_crm_data.py accounts        # 9_Client_Master
CRM_USER=<admin> CRM_KEY=<key> python3 scripts/build_sales_reps.py   # 1_ + user_map
python3 scripts/pull_crm_data.py visits --year 2026                 # 4_
python3 scripts/build_macro.py                   # 6_
python3 scripts/build_boi.py                     # 7_
python3 scripts/build_dbd.py                     # 8_
python3 scripts/build_overview.py                # 0_ (ต้องรันหลัง 3_ + 9_)
```

---

## 5. 🔐 Security Notes (สำคัญก่อนขึ้น GitHub Pages)

1. **`_CORE_Private/` ต้องไม่ขึ้น GitHub** — เก็บ credential CRM, ไฟล์ต้นทาง, แผนกลยุทธ์ และ `users_credentials.md` ไว้ที่นี่ มี `.gitignore` กันไว้แล้ว แต่ **ต้องตรวจ `git status` ก่อน push ทุกครั้ง**
2. **Login ฝั่ง Client ไม่ใช่ความปลอดภัยจริง** — รหัสอยู่ใน `js/auth.js` ซึ่งเบราว์เซอร์โหลดไปทั้งหมด ใครเปิด View Source หรือโหลด `js/auth.js` ก็เห็น (ปัจจุบันเป็น demo credential: admin/admin123 ฯลฯ) → ใช้เป็นเพียงการแบ่ง view ไม่ใช่การป้องกันข้อมูล
3. **ข้อมูล CSV ก็เป็นสาธารณะถ้าโฮสต์แบบ static** — ถ้าต้องการจำกัดการเข้าถึงจริง ต้องมีชั้น Auth ด้านหน้า เช่น Cloudflare Access, Netlify/Vercel password protection หรือ Firebase Auth ก่อนโหลด `RAW_Data/*.csv`
4. **ห้ามเก็บรหัสผ่านระบบอื่น (เช่น อีเมล) เป็น plaintext ในโฟลเดอร์งาน** — ใช้ password manager แทน
