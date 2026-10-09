# 🗄️ Database Schema & ETL Schedule

เอกสารแสดงรอบการอัปเดตข้อมูลและโครงสร้างของ RAW Data สำหรับใช้สร้าง EPS Interactive Dashboard

> **สถานะ 23 ก.ย. 2569:** `RAW_Data/*.csv` ทั้ง 10 ไฟล์เป็น **ข้อมูลจริง** แล้ว (เดิมเป็น mock/หัวตารางว่าง) ดูสคริปต์และข้อจำกัดใน `README_Architecture.md` §4

## 🔄 รอบการอัปเดตข้อมูล (ETL Schedule)

| ลำดับ | แหล่งข้อมูล (Data Source) | ไฟล์ปลายทาง | ความถี่การอัปเดต | เวลา | สถานะ | แหล่งที่มา / สคริปต์ |
|:---:|:---|:---|:---|:---|:---:|:---|
| 1 | CRM Sales Person | `1_CRM_Sales_Person.csv` | รายเดือน (ทุกวันที่ 1) | 00:00 น. | ✅ | CRM `Users` (admin) + เจ้าของ SO → `build_sales_reps.py` |
| 2 | Quote Data (ใบเสนอราคา) | `2_Quote_Data.csv` | วันละ 2 ครั้ง | 12:15 น., 00:00 น. | ✅ | CRM `Quotes` → `process_plan_and_quotes.py` |
| 3 | SO Data (ใบสั่งขาย) | `3_SO_Data.csv` | วันละ 2 ครั้ง | 12:15 น., 00:00 น. | ✅ | CRM `SalesOrder` → `pull_so_2026.py` |
| 4 | Visit Report (รายงานเข้าพบ) | `4_Visit_Report.csv` | รายสัปดาห์ (ทุกวันอาทิตย์) | 00:00 น. | ✅ | CRM `Events` (Meeting/Call) → `pull_crm_data.py visits` |
| 5 | Inventory & Supplier Data | `5_Inventory_Supplier.csv` | วันละ 2 ครั้ง | 12:15 น., 00:00 น. | ✅ | [Google Sheets (PM Master)](https://docs.google.com/spreadsheets/d/12lxhhodM5u2IpuafCfsznm-Ul-gat-zLoffGdPhqPuA/edit?gid=1430193901#gid=1430193901) → `etl_script.py` + `clean_inventory.py` |
| 6 | Macroeconomic Data | `6_Macroeconomic_Data.csv` | รายเดือน (ทุกวันที่ 1) | 00:00 น. | ✅ | OIE CapU/MPI + ธปท. → `build_macro.py` |
| 7 | BOI Investment Data | `7_BOI_Data.csv` | รายเดือน (ทุกวันที่ 1) | 00:00 น. | ✅ | `BOI_Projects_September_2026.xlsx` → `build_boi.py` |
| 8 | DBD / กรมโรงงานฯ Data | `8_DBD_Data.csv` | รายเดือน / รายไตรมาส | 00:00 น. | ✅ | DIW register + DBD cache → `build_dbd.py` |
| 9 | Client Master | `9_Client_Master.csv` | วันละ 1 ครั้ง | 00:00 น. | ✅ | CRM `Accounts` → `pull_crm_data.py accounts` |
| 10 | EPS Overview (สรุปยอด) | `0_EPS_Overview_2026.csv` | ทุกวัน (หลัง SO) | 00:15 น. | ✅ | คำนวณจาก SO + `group_map.json` → `build_overview.py` |
| 11 | Hot Jobs (งานร้อน) | `0_EPS_HotJobs_2026.csv` | วันละ 2 ครั้ง | 12:15 น., 00:00 น. | ✅ | CRM `Quotes` (Pending, chance ≥ 70%) → `pull_hotjobs_2026.py` |
| 12 | Rep Mapping | `10_Group_Reps.csv` | ตามความเหมาะสม | ทันที | ✅ | ยึดตาม `group_reps.json` (Re-mapped 29 ก.ย. 2569) |

## 📚 Data Dictionary — คอลัมน์จริงของแต่ละไฟล์

| ไฟล์ | คอลัมน์ | หมายเหตุ |
|:---|:---|:---|
| `0_EPS_Overview_2026.csv` | metric, label, value, target, unit, trend, trend_value | `Group_*_Revenue` = ยอดจริงจาก CRM (หักเฉพาะที่ map กลุ่มได้ 79%) |
| `0_EPS_HotJobs_2026.csv` | group, hot_count, hot_value_m | แยกตามกลุ่ม A–D/R |
| `1_CRM_Sales_Person.csv` | emp_id, name, role_tier, territory, monthly_target_thb, phone, email, status, group_hint, is_group, so_count, so_value_total_m, so_count_2026, so_value_2026_m, quote_count | `emp_id` = CRM owner id (19x…/20x…); `is_group=yes` = เจ้าของเป็นกลุ่ม ไม่ใช่บุคคล |
| `2_Quote_Data.csv` | quote_id, sales_id, client_id, client_name, equipment_brand, value_thb, stage, probability_pct, created_date, aging_days, status, lost_reason | ดิบจาก CRM — หลายคอลัมน์ยังว่าง (CRM ไม่ได้กรอก) |
| `3_SO_Data.csv` | so_id, quote_ref, sales_id, client_id, client_name, value_thb, booking_date, delivery_date, status | ยอดปี 2026 รวม 162.68 ลบ. |
| `4_Visit_Report.csv` | visit_id, sales_id, client_id, client_name, visit_date, visit_type, objective, outcome, next_action_date | `visit_type` = Meeting / Online Meeting / Mobile Call |
| `5_Inventory_Supplier.csv` | Products, CODE, Description, Qty, Unit Price, Total price, Min, Comment, TYPE, Status, LM VIKING, ORDER STOCK, REMARK, For pump model | ผ่าน `clean_inventory.py` แล้ว (ตัด 493 แถวว่าง) |
| `6_Macroeconomic_Data.csv` | date_period, industry_sector, mpi_index, mpi_yoy_pct, cap_u_pct, bot_policy_rate, private_capex_growth, source | แถว `ALL_INDUSTRY` = ตัวเลขหัวกระดาษ; รายเซกเตอร์มีแค่ CapU |
| `7_BOI_Data.csv` | project_id, company_name, industry_type, project_detail, investment_value_m, zone, approval_period, status, source_sheet, note | มูลค่าเป็นล้านบาทตามต้นฉบับ |
| `8_DBD_Data.csv` | client_id, company_name, registered_capital_m, machine_horsepower, tsic_code, revenue_latest_year, province, match_source, dbd_status | `match_source` = DIW register / DBD API / ว่าง (จับชื่อไม่ตรง) |
| `9_Client_Master.csv` | client_id, company_name, industry_group, address, contact_person, phone, email, status, owner_id, annual_revenue, employees, source, website | `industry_group` = รหัส picklist (เช่น CH14, FD05) — 92% มีค่า |

## 💡 ข้อที่ยังต่อยอดได้
1. **`contact_person`** ใน Client Master ยังว่าง — ต้อง join กับ CRM `Contacts` (8,453 ราย)
2. **`machine_horsepower` / `revenue_latest_year`** ใน DBD ยังว่าง — ต้นทางไม่มีให้ (DIW มีแรงม้าแต่ต้องจับชื่อให้ตรงก่อน)
3. **ยอดที่ map กลุ่มไม่ได้ ~33.7 ลบ.** (20.9%) เพราะลูกค้าไม่มีรหัสอุตสาหกรรมใน CRM — ต้องกรอก industry ให้ครบก่อน (แคมเปญ CRM)
