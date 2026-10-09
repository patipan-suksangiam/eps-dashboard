# 🏗️ EPS Dashboard Development Architecture

สถาปัตยกรรมและการแบ่งหน้าในการพัฒนา Dashboard เพื่อความสะดวกในการสร้างทีละหน้าตาม Role-based View

> **อัปเดต 23 ก.ย. 2569:** ข้อมูลตั้งต้นใน `RAW_Data/` เป็น **ข้อมูลจริงทั้ง 10 ไฟล์** แล้ว (ดู `README_Architecture.md` §4) และมีโฟลเดอร์ `scripts/` สำหรับดึง/คำนวณข้อมูล

## โครงสร้างโปรเจกต์
```
AI Dashboard/
├── RAW_Data/                  # ข้อมูลตั้งต้นทั้งหมด (CSV) — จริง 100%
│   ├── 0_EPS_Overview_2026.csv   # KPI + ยอดรายกลุ่ม (คำนวณจาก CRM)
│   ├── 0_EPS_HotJobs_2026.csv    # งานร้อน (Quotes Pending ≥ 70%)
│   ├── 1_CRM_Sales_Person.csv    # พนักงานขาย + ยอดขายรายคน (CRM)
│   ├── 2_Quote_Data.csv          # ใบเสนอราคา (CRM)
│   ├── 3_SO_Data.csv             # ใบสั่งขาย 2026 (CRM)
│   ├── 4_Visit_Report.csv        # กิจกรรมเข้าพบ (CRM Events)
│   ├── 5_Inventory_Supplier.csv  # สต็อก (Google Sheets + clean)
│   ├── 6_Macroeconomic_Data.csv  # CapU/MPI/ดอกเบี้ย (OIE/ธปท.)
│   ├── 7_BOI_Data.csv            # โครงการ BOI
│   ├── 8_DBD_Data.csv            # ทะเบียนโรงงาน DIW + DBD
│   └── 9_Client_Master.csv       # ลูกค้าทั้งหมด (CRM Accounts)
├── scripts/                   # สคริปต์ดึง/คำนวณข้อมูล
│   ├── crm_query.py              # vtiger webservice wrapper (อ่าน credential จากไฟล์ ไม่พิมพ์ออกจอ)
│   ├── pull_crm_data.py          # accounts / visits / owners + helper paged()
│   ├── build_sales_reps.py       # รวม Users + เจ้าของ SO/Quote
│   ├── build_macro.py            # OIE CapU + MPI + ธปท.
│   ├── build_boi.py              # อ่าน .xlsx (stdlib) → BOI CSV
│   ├── build_dbd.py              # join CRM ↔ DIW/DBD
│   ├── build_overview.py         # คำนวณยอดรายกลุ่มจริงจาก SO
│   └── clean_inventory.py        # ล้าง artefact ของ CSV จาก Google Sheets
├── etl_script.py              # ระบบดึงข้อมูลจาก Source แบบ Automation
├── Dashboard_App/             # โฟลเดอร์สำหรับ Web Dashboard Application
│   ├── index.html             # หน้า Login / Landing Page (เลือก Role)
│   ├── css/                   # ไฟล์ CSS หลัก
│   ├── js/                    # ไฟล์ Script สำหรับโหลดข้อมูล (Parse CSV)
│   │   ├── csv-parser.js         # RFC4180-ish parser (stdlib, ไม่พึ่งไลบรารี)
│   │   ├── auth.js               # login/role (test: admin/admin123)
│   │   ├── router.js             # role-based routing + โหลด view HTML
│   │   ├── app.js                # controller + APP_BASE/DATA_BASE
│   │   ├── eps_overview.js       # renderer หน้า EPS Overview (เสร็จ)
│   │   ├── stock.js              # renderer หน้า Stock & PM (เสร็จ)
│   │   └── vendor/               # Chart.js (vendored — ทำงาน offline/GitHub Pages)
│   ├── views/                 # หน้า Dashboard ย่อยแยกตามบทบาท (Roles)
│   │   ├── eps_overview.html     # ✅ เสร็จ (มี renderer)
│   │   ├── stock.html            # ✅ เสร็จ (มี renderer)
│   │   ├── group_a..d/r.html     # ⏳ โครงเท่านั้น — ยังไม่มี renderer
│   │   └── economic.html         # ⏳ โครงเท่านั้น — ยังไม่มี renderer
└── _CORE_Private/             # หลังบ้าน (ไม่ขึ้น GitHub): credential, ไฟล์ต้นทาง, แผนกลยุทธ์
```

## สถานะการพัฒนา
| หน้า | สถานะ | หมายเหตุ |
|:---|:---:|:---|
| EPS Overview | ✅ | KPI + กราฟ 5 กลุ่ม + AI Action Plan (ข้อมูลจริง) |
| Stock & PM | ✅ | KPI + ตาราง + ตัวกรอง (ข้อมูลจริง 449 รายการ) |
| Group A / B / C / D / R | ⏳ | มีแค่กรอบหัวข้อ — ต้องเขียน renderer ต่อยอดจากข้อมูลจริงที่มีแล้ว |
| Economic & BOI | ⏳ | มีแค่กรอบหัวข้อ — ข้อมูล `6_Macroeconomic_Data.csv` + `7_BOI_Data.csv` พร้อมแล้ว |

## แนวทางการพัฒนา (Phased Approach)
เนื่องจากการรวมข้อมูลทั้งหมดไว้ในไฟล์ `.html` เดียวจะทำให้โค้ดยาวและแก้ไขยาก (เหมือนในไฟล์ Demo) เราจึงแยกพัฒนาเป็นทีละไฟล์/ทีละหน้า โดย**ข้อมูลจริงพร้อมครบแล้ว** เหลือเพียงเขียน renderer เพิ่ม

### Phase 1: Core Framework & Data — ✅ เสร็จ
- Layout หลัก (Sidebar/Top Nav, CSS พื้นฐาน) ✅
- JS Engine โหลด `.csv` → JSON ให้ Chart.js ✅
- RAW Data ครบ 10 ไฟล์ **ข้อมูลจริงทั้งหมด** ✅

### Phase 2: Role Views
1. **EPS Overview** ✅ · **Stock & PM** ✅
2. **Group A / B / C / D / R** ⏳ (ใช้ข้อมูลจาก `3_SO_Data` + `9_Client_Master` + `group_map.json`)
3. **Economic & BOI** ⏳ (ใช้ `6_Macroeconomic_Data` + `7_BOI_Data`)
