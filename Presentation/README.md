# 📊 Presentation — ผังการเก็บข้อมูล & การนำเสนอข้อมูล (EPS Dashboard)

ชุดนำเสนอ 20 หน้า อธิบายว่าระบบ EPS Dashboard เก็บข้อมูลจากไหน ผ่าน ETL อย่างไร เก็บเป็นไฟล์อะไร
แล้วนำเสนอออกมาเป็นหน้าแดชบอร์ดแบบใด — ทุกตัวเลขอ้างอิงไฟล์จริงใน `RAW_Data/` ณ 19 ต.ค. 2569

## ไฟล์ในโฟลเดอร์นี้

| ไฟล์ | ใช้ทำอะไร |
|---|---|
| `EPS_Dashboard_Data_and_Presentation_TH.pptx` | ตัวนำเสนอ (PowerPoint, 16:9, มี speaker notes ทุกหน้า) |
| `EPS_Dashboard_Data_and_Presentation_TH.pdf` | ฉบับ PDF สำหรับส่ง/พรีวิว (20 หน้า) |
| `build_deck.py` | สคริปต์สร้างสไลด์ทั้งชุด (python-pptx) — แก้ข้อความ/ตัวเลขแล้วรันใหม่ได้ |
| `export_png.py` | ส่งออก PNG รายสไลด์ไปที่ `render/` (ใช้ตรวจเลย์เอาต์ ต้องมี PowerPoint) |
| `export_pdf.py` | ส่งออก PDF (ต้องมี PowerPoint) |
| `render/slide01.png … slide20.png` | ภาพสไลด์รายหน้า 1600×900 |

## โครงเรื่อง 20 หน้า

1. ปก · 2. สารบัญ · 3. ภาพรวมระบบ (เก็บ → แปลง → ไฟล์ → นำเสนอ)
4–10. **ส่วนที่ 1 ผังการเก็บข้อมูล** — แหล่งข้อมูล 4 กลุ่ม · เส้นทางการไหล · คลัง CSV 3 ชั้น ·
ตารางเวลา ETL · กุญแจเชื่อมข้อมูล · คุณภาพข้อมูล/ข้อจำกัด
11–17. **ส่วนที่ 2 การนำเสนอข้อมูล** — สิทธิ์ตามบทบาท · EPS Overview · Group A–D/R ·
Stock & PM · Economic & BOI/DBD + Open Quotations · แผนที่หน้า ↔ ไฟล์ข้อมูล
18. การโฮสต์ (NAS + Tailscale / GitHub Pages) · 19. สรุป + Roadmap · 20. ปิดท้าย/เอกสารอ้างอิง

## วิธีอัปเดตสไลด์

```bash
# แก้ข้อความ/ตัวเลขใน build_deck.py แล้ว
python build_deck.py        # → .pptx
python export_pdf.py        # → .pdf  (ทางเลือก)
python export_png.py        # → render/*.png (ทางเลือก, ตรวจเลย์เอาต์)
```

ต้องมี `python-pptx` (`python -m pip install python-pptx`) และ `pywin32` ถ้าจะ export ผ่าน PowerPoint

## แหล่งอ้างอิงของเนื้อหา

`README.md` · `Data_Dictionary_and_Schedule.md` · `app_architecture.md` · `data_sources.md` ·
`DATA_HOSTING_Synology.md` · `deploy/synology/README.md` · `group_map.json` ·
และนับแถวจริงจาก `RAW_Data/*.csv` (สคริปต์นับ: csv.reader, 19 ต.ค. 2569)

> ตัวเลขสำคัญ: Revenue YTD 174.98 M (เป้า 453.55 M = 39%) · SO 1,057 ใบ · ลูกค้า 5,530 ราย ·
> Hot Jobs 72.02 M / 176 ดีล · สต็อก 16.73 M (dead stock 4.44 M) · ยอดที่ map กลุ่มไม่ได้ 82.80 M (≈19%)
