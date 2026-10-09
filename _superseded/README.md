# _superseded — สคริปต์เก่า/เลิกใช้ (2026-09-24)

เก็บไว้เป็นประวัติเท่านั้น **ห้ามรัน** (และไม่ถูก track ขึ้น GitHub)

| ไฟล์ | เหตุผลที่ปลด |
|---|---|
| `update_real_data_2026.py` | มี **ตัวเลข mock ฮาร์ดโค้ด** (D 48.5 / R 38.2 / C 32.1 / B 25.4 / A 18.44) — ถ้ารันจะเขียนทับ `RAW_Data/0_EPS_Overview_2026.csv` ด้วยข้อมูลปลอม |
| `update_with_real_plan.py` | เหมือนข้างบน (mock) + อ่าน `Plan_SalesOrder.csv` ที่คอลัมน์ Plan Amount เป็น 0 ทั้งไฟล์ |
| `process_plan_and_quotes.py` | อ้าง `Plan_2026_SelectedProducts.csv` ที่ไม่มีอยู่ (ทำให้รันไม่ผ่าน) + เคยฝัง credential ตรงในไฟล์ (ลบออกแล้ว) |

**ใช้ตัวแทน:**
- ภาพรวมรายกลุ่ม → `scripts/build_overview.py`
- ดึงข้อมูล CRM → `scripts/pull_crm_data.py`
- ETL รายวัน → `run_sync.py daily` / `etl_script.py`
