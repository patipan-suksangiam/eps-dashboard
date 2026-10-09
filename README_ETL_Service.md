# 🛠️ EPS Dashboard ETL Service

สคริปต์นี้มีหน้าที่ดึงข้อมูลและอัปเดตไฟล์แบบอัตโนมัติ (Automated Data Pipeline) ตามรอบเวลา (ETL Schedule) ที่กำหนดไว้ เพื่อใช้เป็นฐานข้อมูลหลังบ้านสำหรับ Dashboard

> **อัปเดต 23 ก.ย. 2569:** pipeline ทำงานกับข้อมูลจริงครบทุกแหล่งแล้ว — เพิ่มสคริปต์ในโฟลเดอร์ `scripts/` (ดูรายละเอียดใน `README_Architecture.md` §4)

## 📌 โครงสร้างการทำงาน

**สคริปต์หลักเดิม:**
- `etl_script.py` — ตัวจัดตารางเวลา (loop ตรวจเวลาเอง) ดาวน์โหลด Inventory จาก Google Sheets และเรียก `pull_so_2026.py` / `pull_hotjobs_2026.py`
- `pull_so_2026.py` — ใบสั่งขายปีปัจจุบันจาก CRM
- `pull_hotjobs_2026.py` — Quotes ที่ Pending + Chance ≥ 70% และกำหนดปิดงานเดือนนี้/เดือนหน้า → อัปเดต `0_EPS_HotJobs_2026.csv` และแก้แถว `FY2026_Hot_Jobs` ใน overview ให้ตรงกัน
- `process_plan_and_quotes.py` — ใบเสนอราคา + วิเคราะห์ Plan
- `etl_test_sync.py` — ทดสอบดึง Inventory แบบ manual

**สคริปต์ที่เพิ่มรอบนี้ (โฟลเดอร์ `scripts/`):**
| สคริปต์ | ทำอะไร | ปลายทาง |
|:---|:---|:---|
| `crm_query.py` | wrapper vtiger API (อ่าน credential จาก `_CORE_Private/crm_credentials.json`) | — |
| `pull_crm_data.py` | `accounts` / `visits` / `owners` + helper `paged()` กันบั๊กหน้าไม่ครบ 100 | `9_`, `4_`, `1_` |
| `build_sales_reps.py` | รวมชื่อจาก `Users` (admin) + ยอดขายจากเจ้าของ SO/Quote | `1_CRM_Sales_Person.csv` |
| `build_macro.py` | OIE CapU + MPI + ธปท. | `6_Macroeconomic_Data.csv` |
| `build_boi.py` | อ่าน `BOI_Projects_*.xlsx` ด้วย stdlib | `7_BOI_Data.csv` |
| `build_dbd.py` | join CRM ↔ ทะเบียนโรงงาน DIW + DBD cache | `8_DBD_Data.csv` |
| `build_overview.py` | คำนวณยอดรายกลุ่มจริงจาก SO + `group_map.json` | `0_EPS_Overview_2026.csv` |
| `clean_inventory.py` | ล้างแถวว่าง/แก้หัวคอลัมน์ของ CSV จาก Google Sheets | `5_Inventory_Supplier.csv` |

## ⏰ รอบเวลาที่ตั้งไว้ (ETL Schedule)
*   **ทุกวัน (12:15 และ 00:00 น.):** อัปเดต Quote, SO, Hot Jobs และ Inventory (Google Sheets)
*   **ทุกวัน (00:15 น.):** รัน `build_overview.py` (ต้องรันหลัง SO เสร็จ)
*   **ทุกวันอาทิตย์ (00:00 น.):** อัปเดต Visit Report (`pull_crm_data.py visits`)
*   **ทุกวันที่ 1 ของเดือน (00:00 น.):** อัปเดต Sales Person, Macroeconomic, BOI, DBD และ Client Master

## ⚠️ ข้อควรระวังก่อนตั้ง automation ให้รันเอง

1. **macOS Cloud File Provider** — ถ้าโปรเจกต์ยังอยู่บน Synology/Google Drive และไฟล์เป็น placeholder สคริปต์จะอ่านไม่ได้ (`errno 11 Resource deadlock avoided`) → ต้องตั้งโฟลเดอร์เป็น **Available offline** หรือย้ายโปรเจกต์ไปดิสก์ local ก่อน
2. **Credential** — `build_sales_reps.py` ต้องใช้สิทธิ์ admin (module `Users`) ส่งผ่าน env `CRM_USER` / `CRM_KEY` ห้าม commit ค่าลงไฟล์
3. **ลำดับการรัน** — `build_overview.py` ต้องรันหลัง `3_SO_Data.csv` และ `9_Client_Master.csv` อัปเดตแล้วเสมอ
4. **ห้ามหยุด loop เมื่อหน้า API สั้นกว่า 100 แถว** — vtiger ไม่รับ ORDER BY จึงส่งหน้าย่อยไม่ครบได้ (helper `paged()` จัดการให้แล้ว)

## 🚀 ทางเลือกที่เสถียรกว่าในระยะยาว
ย้าย ETL ไปรันบน Synology NAS (สคริปต์เดิมชี้ path `/home/jom/SynologyDrive/AI Dashboard` อยู่แล้ว) → ไฟล์เป็นของจริง 100% ไม่มีปัญหา placeholder และรันได้แม้ปิด MacBook
