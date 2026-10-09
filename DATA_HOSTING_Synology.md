# 🔐 แยก RAW_Data ออกจาก GitHub — โฮสต์บน Synology + Cloudflare Tunnel

**เป้าหมาย:** ตัวเว็บแดชบอร์ด (โค้ด) อยู่บน GitHub Pages แต่ไฟล์ CSV จริง (`RAW_Data/`) เก็บไว้ใน Synology ของบริษัทเท่านั้น
— GitHub ไม่มีข้อมูลลูกค้า/ยอดขายอีกต่อไป

**สถานะปัจจุบัน (2026-10-09):** เตรียมฝั่งโค้ดเสร็จแล้ว ⏳ รอตั้งค่าฝั่ง Synology

---

## 1) ฝั่ง Synology — ให้บริการไฟล์ CSV

ไฟล์ `scripts/serve_raw_data.py` (ใช้ Python stdlib ล้วน ไม่ต้อง `pip install` อะไรเลย)

```bash
cd "/volume1/.../AI Dashboard"            # โฟลเดอร์งานจริงบน NAS
python3 scripts/serve_raw_data.py \
    --port 8091 \
    --dir "/volume1/.../AI Dashboard/RAW_Data" \
    --allow-origin https://patipan-suksangiam.github.io
```

ทดสอบในเครื่อง NAS เอง:
```bash
curl -I "http://127.0.0.1:8091/0_EPS_Overview_2026.csv" -H "Origin: https://patipan-suksangiam.github.io"
# ต้องเห็น  Access-Control-Allow-Origin: https://patipan-suksangiam.github.io
```

> **ทางเลือก:** ถ้าใช้ **Web Station** (nginx) แทนสคริปต์ ให้เพิ่ม header นี้ในเว็บไซต์ที่ชี้ไปโฟลเดอร์ `RAW_Data`:
> ```nginx
> add_header Access-Control-Allow-Origin "https://patipan-suksangiam.github.io" always;
> add_header Access-Control-Allow-Methods "GET, HEAD, OPTIONS" always;
> add_header Cache-Control "public, max-age=300" always;
> ```

**ให้รันอัตโนมัติ:** เพิ่มใน Task Scheduler ของ DSM (หรือ crontab เดิมที่มีอยู่) ให้รันตอน boot
```cron
@reboot /usr/local/bin/python3 "/volume1/.../AI Dashboard/scripts/serve_raw_data.py" --port 8091 --dir "/volume1/.../AI Dashboard/RAW_Data" >> "/volume1/.../AI Dashboard/data_host.log" 2>&1
```

---

## 2) ฝั่ง Cloudflare — Tunnel + Access

1. **Cloudflare Tunnel** (Zero Trust → Networks → Tunnels) สร้าง tunnel ชี้ไป `http://127.0.0.1:8091`
   แล้วตั้ง Public Hostname เช่น `data.siamrajpcl.com` (หรือ hostname อะไรก็ได้ในโดเมนที่มี)
2. **Cloudflare Access** (Zero Trust → Access → Applications) ใส่ policy ป้องกัน hostname นี้
   อนุญาตเฉพาะอีเมลในบริษัท เช่น `*@siamrajplc.com`
   - ⚠️ ถ้าเปิด Access แบบล็อกอินหน้าเว็บ เบราว์เซอร์จะขอ cookie ของ `data.…` แยกจากหน้าแดชบอร์ด
     ครั้งแรกที่เปิดแดชบอร์ดให้เข้า `https://data.….…/0_EPS_Overview_2026.csv` แล้วล็อกอินก่อน 1 ครั้ง
   - ถ้าไม่อยากให้มีขั้นตอนนี้ ใช้วิธี "URL ไม่บอกใคร" (obscure hostname) + จำกัด `--allow-origin` เท่านั้น
3. ทดสอบ: เปิด `https://data.….…/9_Client_Master.csv` ต้องได้ไฟล์ CSV

---

## 3) ฝั่ง Dashboard — ชี้ไปที่โฮสต์ใหม่

แก้ไฟล์ `Dashboard_App/js/config.js` (บรรทัดเดียว):
```js
window.EPS_DATA_BASE = 'https://data.….…/';
```
commit + push → GitHub Pages จะโหลด CSV จาก Synology แทน (ต้องมี `/` ปิดท้าย)

> ยังไม่ตั้งค่านี้ = โหลดจากเครื่องเดียวกันเหมือนเดิม (local / Synology) — ไม่มีอะไรพังระหว่างเตรียมการ

---

## 4) Cutover — เอา RAW_Data ออกจาก repo

ทำ **หลัง** ข้อ 3 ใช้งานได้แล้วเท่านั้น (ถ้าลบก่อน หน้า GitHub Pages จะไม่เหลือข้อมูล)

```bash
cd "/path/to/AI Dashboard"
printf 'RAW_Data/\n' >> .gitignore
git rm -r --cached RAW_Data
git commit -m "Stop publishing RAW_Data (served from Synology instead)"
git push origin master
```

### ⚠️ ต้องรู้ก่อน: การลบไม่ได้ทำให้ข้อมูลหายจาก GitHub
`RAW_Data/` ถูก push ขึ้น repo สาธารณะไปแล้ว (คอมมิต `53028aa`, `94ee541`) — ประวัติยังอยู่และดาวน์โหลดได้
ตัวเลือกที่จะเอาออก "จริง":

| วิธี | ผล |
|---|---|
| `git filter-repo` / BFG แล้ว force-push | ล้างทุกคอมมิต — แต่ fork/cache ของ GitHub อาจยังมีชั่วคราว |
| สร้าง repo ใหม่สะอาด ๆ (แนะนำ) | ไม่มีประวัติเดิมติดมาเลย — ลบ repo เก่าทิ้ง แล้ว Pages ตั้งใหม่ |
| ติดต่อ GitHub Support ให้ purge cache | ใช้เมื่อต้องการให้ลบแน่นอน 100% |

---

## Checklist

- [ ] Synology รัน `serve_raw_data.py` และ curl ทดสอบผ่าน (มี header CORS)
- [ ] Cloudflare Tunnel + Access ตั้งเสร็จ เปิด URL ข้อมูลได้
- [ ] แก้ `config.js` → `EPS_DATA_BASE` แล้ว push, เปิดหน้าแดชบอร์ดยืนยันข้อมูลขึ้นครบทุกหน้า
- [ ] `git rm -r --cached RAW_Data` + `.gitignore` (cutover)
- [ ] ตัดสินใจเรื่องประวัติเก่า (repo ใหม่ / purge)
- [ ] ไม่เปิด `--port 8091` สู่วงนอกนอกจากผ่าน tunnel (bind `127.0.0.1` เท่านั้น)

---

# ภาคผนวก: Cloudflare Tunnel ฉบับละเอียด

**Cloudflare Tunnel คืออะไร:** ตัวเชื่อม (connector) ที่รันอยู่ในเครื่องเรา แล้ว**เปิดการเชื่อมต่อออกไป**หายัง Cloudflare
ทำให้ Cloudflare เรียกกลับมาที่เครื่องเราได้ โดย**ไม่ต้องเปิด port ที่ router และไม่ต้องมี public IP**
ข้อดี: HTTPS อัตโนมัติ, ปิด/เปิดการเข้าถึงได้แค่หยุดคอนเทนเนอร์, ใช้ฟรี

## ⚠️ ข้อกำหนดที่ต้องตัดสินใจก่อน: โดเมนต้องอยู่บน Cloudflare
Tunnel ใช้ได้เฉพาะโดเมนที่ **ย้าย Nameserver มาที่ Cloudflare** เท่านั้น

| ทางเลือก | ผลกระทบ |
|---|---|
| **ซื้อโดเมนใหม่ใช้เฉพาะงานนี้** (แนะนำ, ~400 บาท/ปี) | ไม่กระทบเมล/เว็บบริษัทเลย |
| ใช้โดเมนบริษัท (`siamrajplc.com`) | ต้องคัดลอก DNS record เดิม **ทั้งหมด** (MX, SPF, DKIM, DMARC, A, CNAME, TXT) ไป Cloudflare ให้ครบ **ก่อน** เปลี่ยน NS ที่ registrar — ตกหล่น = เมลล่มทันที |

## ขั้นตอน

**A. เอาโดเมนเข้า Cloudflare**
1. สมัคร cloudflare.com → **Add a site** → ใส่โดเมน → เลือกแผน **Free**
2. Cloudflare จะให้ Nameserver 2 ตัว → เอาไปเปลี่ยนที่ registrar ของโดเมน
3. รอสถานะเป็น **Active** (ปกติ 5 นาที – 24 ชม.)
4. ถ้าเป็นโดเมนบริษัท: ที่หน้า **DNS → Records** ตรวจว่ามี MX/TXT/A/CNAME ครบเหมือนเดิมก่อนเปลี่ยน NS

**B. เปิด Zero Trust + สร้าง Tunnel**
1. Dashboard → **Zero Trust** → ตั้ง team name (ฟรี ไม่ต้องใส่บัตร)
2. **Networks → Tunnels → Create a tunnel** → เลือก **Cloudflared** → ตั้งชื่อ เช่น `eps-data`
3. หน้า Configure → แท็บ **Docker** → คัดลอกคำสั่ง `docker run ... --token eyJ...` เก็บไว้

**C. รัน connector บน Synology (DSM 7.2 = Container Manager)**
- File Station สร้างโฟลเดอร์ `/docker/cloudflared/`
- Container Manager → **โปรเจกต์ → สร้าง** แล้ววาง:
  ```yaml
  services:
    cloudflared:
      image: cloudflare/cloudflared:latest
      restart: unless-stopped
      command: tunnel --no-autoupdate run --token <โทเคนจาก B3>
  ```
- ทางเลือกอื่น: Package จาก SynoCommunity (`Cloudflare Tunnel`) หรือ SSH รันคำสั่ง `docker run` ที่คัดลอกมาตรง ๆ

**D. ประกาศ Public Hostname**
1. กลับไปที่ Tunnels → แท็บ **Public Hostname → Add a public hostname**
2. Subdomain `data` · Domain `<โดเมน>` · Service: **HTTP** → `127.0.0.1:8091`
   *(ให้ `serve_raw_data.py` รันอยู่บน NAS ที่พอร์ต 8091 — ถ้าใช้ Web Station ให้ชี้ `https://127.0.0.1:443` แล้วติ๊ก No TLS Verify)*
3. เปิด `https://data.<โดเมน>/0_EPS_Overview_2026.csv` → ต้องได้ไฟล์ CSV

**E. ใส่ Cloudflare Access (บังคับล็อกอินก่อนอ่านข้อมูล)**
- Zero Trust → **Access → Applications → Add an application → Self-hosted**
- Application domain = `data.<โดเมน>`
- Policy: Action **Allow** · Include → **Emails** → `*@siamrajplc.com`
- Login method: **One-time PIN** (Cloudflare ส่งรหัสเข้าอีเมล ไม่ต้องต่อ IdP) · Free plan รองรับถึง 50 ผู้ใช้

> ⚠️ **ข้อควรรู้ทางเทคนิค:** ถ้าเปิด Access ตัวแดชบอร์ด (origin `patipan-suksangiam.github.io`) จะ `fetch` ข้ามโดเมน
> แล้ว browser **ไม่ส่ง cookie ของ `data.<โดเมน>` ให้โดยอัตโนมัติ** → ต้อง (1) เปิด `https://data.<โดเมน>/` แล้วล็อกอิน Access 1 ครั้ง
> และ (2) ให้ฝั่งโค้ด `fetch` ใช้ `credentials: 'include'` + ฝั่งข้อมูลส่ง `Access-Control-Allow-Credentials: true`
> **ทางที่ง่ายกว่า:** ยังไม่ต้องเปิด Access รอบแรก — ใช้ hostname ที่ไม่บอกใคร + จำกัด `--allow-origin` ให้เฉพาะ origin ของแดชบอร์ด
> แล้วค่อยเพิ่ม Access ทีหลัง (แจ้งผมได้ ผมจะปรับ `fetch` ให้รองรับ)

## ทางเลือกอื่นถ้าไม่อยากยุ่งกับโดเมน
- **Tailscale Funnel** — ใช้โดเมน `*.ts.net` ของ Tailscale เอง ไม่ต้องมีโดเมน และล็อกอินด้วยบัญชี Tailscale
- **Cloudflare Pages** — ย้ายตัวเว็บขึ้น Cloudflare Pages แล้วเปิด Access ทั้งเว็บ (โค้ด+ข้อมูลอยู่ที่เดียว)
- **ใช้ในวง LAN/VPN เท่านั้น** — ไม่ต้อง tunnel เลย เปิดจากในออฟฟิศหรือผ่าน VPN บริษัท

---

# ทำไมใช้ QuickConnect เป็นที่โหลดข้อมูลให้แดชบอร์ดไม่ได้

QuickConnect มีไว้ให้ **คน** เข้าไปใช้บริการของ Synology — ไม่ใช่ช่องทางให้บริการอื่นออกอินเทอร์เน็ต

| ประเด็น | QuickConnect | Cloudflare Tunnel |
|---|---|---|
| เปิดให้บริการที่เราเขียนเอง (พอร์ต 8091) | ❌ เปิดได้เฉพาะแอปของ Synology (DSM, File Station, Drive, Photos…) เลือกใน Control Panel → External Access → QuickConnect → Advanced | ✅ ประกาศ public hostname ชี้พอร์ตไหนก็ได้ |
| CORS header | ❌ คุมไม่ได้ | ✅ `serve_raw_data.py` ใส่ให้ |
| การเข้าถึง | ต้องล็อกอิน DSM (session/cookie) | ✅ URL ตรง + ใส่ Access ได้ถ้าต้องการ |
| SSH/SFTP | ❌ ไม่ proxy ให้ | ✅ (ผ่าน tunnel TCP ได้) |
| ต้องมีโดเมน | ❌ ไม่ต้อง | ✅ ต้องมี |

**สรุป:** QuickConnect = "ทางเข้าห้องเครื่อง" (ใช้ตั้งค่า DSM จากระยะไกลได้) แต่ไม่ใช่ "ทางออกของข้อมูล"

## ถ้าอยากให้ปลาวาฬช่วยตั้งค่าจากระยะไกล
QuickConnect เปิดให้ได้แค่ **หน้า DSM** (ไม่ proxy SSH) — ทางที่แก้ได้ทั้งสองเรื่องพร้อมกันคือ **Tailscale**:
- ติดตั้ง Tailscale บน NAS → ได้ IP ส่วนตัว + เข้า SSH ได้จากทุกที่ → ปลาวาฬช่วยตั้งค่าได้
- เปิด **Tailscale Funnel** → ได้ URL `https://<ชื่อ>.<tailnet>.ts.net` เป็นที่โหลด CSV **โดยไม่ต้องมีโดเมนเลย**
- ทางเลือกแทน: ให้เครื่องที่อยู่วงเดียวกับ NAS (เครื่องออฟฟิศ) เป็นทางเข้า

⚠️ ถ้าเปิด QuickConnect: ควรเปิด **2FA**, จำกัด app ที่อนุญาต (ปิดตัวที่ไม่ใช้), และปิด relay service ถ้าไม่จำเป็น
(QuickConnect เป็นจุดที่ถูกยิง brute-force บ่อย และ relay อาจช้ากว่าปกติ)

---

# ใช้ NAS แทน GitHub ทั้งหมดได้ไหม

ได้ — และทำได้เลยด้วยสคริปต์ตัวเดิมในโหมด `--root` (เสิร์ฟทั้งแอป + ข้อมูลจาก origin เดียว ไม่มี CORS)

| ประเด็น | GitHub Pages + NAS (ข้อมูล) | **NAS อย่างเดียว** |
|---|---|---|
| ความลับข้อมูล | ✅ ข้อมูลอยู่ในบริษัท | ✅ เหมือนกัน |
| ความเร็ว/ความเสถียร | ✅ CDN ทั่วโลก ตัวเว็บไม่ล่ม | ⚠️ ขึ้นกับ NAS + เน็ตออฟฟิศ (ไฟดับ/เน็ตล่ม = ทุกคนเข้าไม่ได้) |
| จำนวนคนเข้า | ไม่จำกัด | Tailscale ฟรี 3 users · ถ้าเกินใช้ public URL หรือจ่ายรายหัว |
| การเข้าถึงจากนอกออฟฟิศ | ต้องมี tunnel เหมือนกัน | ต้องมี tunnel เหมือนกัน |
| อัปเดตโค้ด | `git push` → เห็นทันที | ต้องเข้า NAS (ปลาวาฬทำผ่าน Tailscale ได้) |
| Auth | client-side (`js/auth.js`) เห็นใน View Source | เหมือนกัน — แต่ถ้าเปิดเฉพาะใน tailnet จะได้กำแพงชั้นที่สองจากเครือข่าย |
| จำนวนที่ต้องดูแล | 2 ที่ | 1 ที่ |

**ข้อสรุปที่แนะนำ**
- **ทีมเล็กในบริษัท + ข้อมูลอ่อนไหว** → ใช้ NAS อย่างเดียว + เปิดเฉพาะใน tailnet ปลอดภัยที่สุด
- **ต้องให้เซลส์เปิดจากที่ไหนก็ได้ โดยไม่ติดตั้งอะไร** → ต้องมี public URL (Tailscale Funnel หรือ Cloudflare Tunnel) อยู่ดี
- **อยากให้ตัวเว็บเสถียรที่สุด** → เก็บโค้ดบน GitHub Pages (ไม่มีข้อมูล) แล้วเหลือแค่ข้อมูลบน NAS
- ไม่ว่าทางไหน **auth ของแอปตอนนี้ยังเป็น client-side** — ถ้าจะเปิด public จริงควรเปลี่ยนเป็น Basic Auth ที่ตัวเสิร์ฟ หรือ Cloudflare Access
