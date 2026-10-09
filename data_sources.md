# แหล่งข้อมูลสำหรับ Dashboard (EPS Interactive Dashboard Demo)

> **อัปเดต 23 ก.ย. 2569:** แหล่งข้อมูลทั้งหมดด้านล่าง **เชื่อมต่อจริงแล้ว** ✅ ทุกไฟล์ใน `RAW_Data/` มีข้อมูลจริง ไม่ใช่ mock — ดูสคริปต์ที่ใช้ดึงใน `README_Architecture.md` §4 และคอลัมน์จริงใน `Data_Dictionary_and_Schedule.md`

จากการวิเคราะห์ไฟล์ `EPS_Interactive_Dashboard_Demo.html` แหล่งข้อมูลที่จำเป็นต้องใช้ในการสร้าง Dashboard นี้ แบ่งออกเป็น 4 แหล่งหลักดังนี้:

## 1. CRM & Sales Data (Internal) — ✅ LIVE
- **ระบบ/แหล่งที่มา:** CRM สยามราช (vtiger 8.0, `crm.siamrajpump.com/webservice.php`)
- **สคริปต์:** `scripts/pull_crm_data.py`, `scripts/build_sales_reps.py`, `pull_so_2026.py`, `process_plan_and_quotes.py`, `pull_hotjobs_2026.py`
- **ข้อมูลที่ได้จริง:**
  - ยอดขาย YTD (SO 2026 = 162.68 ลบ.) · จำนวนใบสั่งขาย 966 ใบ
  - ใบเสนอราคา 18,270 ใบ · มูลค่า Pipeline
  - ลูกค้าทั้งหมด 5,511 ราย (industry 92%) · `9_Client_Master.csv`
  - ประวัติเข้าพบลูกค้า/นัดหมาย 17,948 กิจกรรมปี 2026 · `4_Visit_Report.csv`
  - พนักงานขาย 56 เจ้าของงาน (ชื่อจริง 38) + ยอดขายรายคน · `1_CRM_Sales_Person.csv`
- **ข้อจำกัด:** module `Users` ต้องใช้ admin (udomlak) · `cf_892` (industry) ถูกปฏิเสธแม้เป็น admin · Win/Loss reason ยังไม่มีใน CRM

## 2. Inventory & Supplier Data (Product Management) — ✅ LIVE
- **ระบบ/แหล่งที่มา:** Google Sheets (PM Master — Sale tab)
- **สคริปต์:** `etl_script.py` (ดาวน์โหลด CSV) + `clean_inventory.py` (ลบแถวว่าง, แก้ header)
- **ข้อมูลที่ได้จริง:** 449 รายการ · มูลค่าสต็อกรวม 17.60 ลบ. · Dead Stock 4.44 ลบ.
- **ยังขาด:** เป้า Quota ราย Supplier (Annual Commitment) และจำนวน Rebate — ยังไม่มีในชีตต้นทาง

## 3. Macroeconomic & Industry Data (External — BOT & OIE) — ✅ LIVE
- **ระบบ/แหล่งที่มา:** สำนักงานเศรษฐกิจอุตสาหกรรม (สศอ./OIE) + ธนาคารแห่งประเทศไทย
- **สคริปต์:** `scripts/build_macro.py`
- **ข้อมูลที่ได้จริง:** CapU รายเซกเตอร์ 129 รายการ (ก.ค. 2569) · MPI 94.80 (+0.46% YoY) · ดอกเบี้ยนโยบาย 1.00% ต่อปี (กนง. 4/2569) · ลงทุนเอกชน Q2 +13.4%
- **ยังขาด:** MPI index รายเซกเตอร์ (สศอ. ไม่เผยแพร่รายเซกเตอร์ในไฟล์ CapU)

## 4. Government Incentive & Business Registration (External — BOI & DBD/DIW) — ✅ LIVE
- **ระบบ/แหล่งที่มา:** BOI (รายงานรายเดือน) · กรมโรงงานอุตสาหกรรม (ทะเบียนโรงงาน) · กรมพัฒนาธุรกิจการค้า (DBD Open API + ประกาศจดทะเบียนรายเดือน)
- **สคริปต์:** `scripts/build_boi.py`, `scripts/build_dbd.py`
- **ข้อมูลที่ได้จริง:**
  - BOI 24 โครงการ/มาตรการ (Data Center, Electronics, EV, Clean Energy, กองทุน Transform)
  - DIW ทะเบียนโรงงาน 62,623 ราย (เงินทุน + แรงม้า + TSIC) + DBD cache 1,358 ราย → จับคู่กับ CRM ได้ 1,668 ราย (30.3%)
- **ข้อจำกัด:** จับคู่ด้วยชื่อบริษัท (CRM ชื่อไทย vs ทะเบียนชื่อยาว) → บริษัทเทรดดิ้งที่ไม่มีโรงงานจะไม่เจอ

## 🔗 การเชื่อมโยงข้ามตาราง (Join key)
| คีย์ | ใช้เชื่อม |
|:---|:---|
| `client_id` (CRM account id, เช่น 11x1010) | Quote · SO · Visit · Client Master · DBD |
| `emp_id` (CRM owner id, เช่น 19x23) | Sales Person · เจ้าของ SO/Quote |
| `industry_group` (รหัส picklist เช่น CH14) | Client Master → กลุ่มขาย A–R ผ่าน `_CORE_Private/group_map.json` |
