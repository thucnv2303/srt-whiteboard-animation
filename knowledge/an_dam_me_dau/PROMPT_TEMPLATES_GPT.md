# QUY CHUẨN THIẾT KẾ NEGATIVE SPACE & PROMPT GPT SINH ẢNH CHUẨN
## (Áp dụng đồng bộ cho toàn bộ 330 Slot Video kênh "Ăn dặm mẹ Dâu")

> **Mục tiêu tối thượng:** Đảm bảo khi tạo ảnh bằng GPT / DALL-E cho bất kỳ slot nào, hình vẽ luôn được phân bổ vào các vùng an toàn (Safe Visual Zones), giữ lại các khoảng trống vàng (Negative Space Zones) cho hệ thống renderer chèn các khối chữ, huy hiệu vector, ruy băng và khối CTA mà **100% KHÔNG BAO GIỜ XẢY RA HIỆN TƯỢNG CHỮ ĐÈ ẢNH HOẶC CHỮ TRÀN KHUNG**.

---

## 1. NGUYÊN TẮC VÀNG VỀ KHÔNG GIAN BỐ CỤC (CANVAS 1080 × 1920)

Mỗi khung hình dọc 9:16 (1080×1920) được chia thành các dải tọa độ không gian bất biến:

```
+-------------------------------------------------------------+ y = 0
| [VÙNG TRỐNG 1: y = 0 .. 180]                                | 
| -> Dành riêng cho Dải Ruy Băng Tiêu Đề 3D Ribbon Banner     |
+-------------------------------------------------------------+ y = 180
|                                                             |
| [VÙNG NỘI DUNG TRÊN: y = 180 .. 900]                        |
| - Cảnh 1: Khối thẻ cảnh báo (y=180..420), Đỉnh đầu bé (y>500)|
| - Cảnh 2: Dạ dày khỏe mạnh trôi trên dòng sữa mẹ            |
| - Cảnh 3: Bước 1 (Bao gạo bên trái, Card Step 1 bên phải)   |
| - Cảnh 4: Tranh mẹ đút bé ăn (y=180..950)                   |
|                                                             |
+-------------------------------------------------------------+ y = 900
| [VÙNG TRỐNG 2: y = 900 .. 1060]                             |
| -> Dành riêng cho Thẻ Washi Xanh (Cảnh 2) hoặc Card Bước 2  |
+-------------------------------------------------------------+ y = 1060
|                                                             |
| [VÙNG NỘI DUNG DƯỚI: y = 1060 .. 1650]                      |
| - Cảnh 1: Thân ghế ăn dặm & bàn chân bé                     |
| - Cảnh 2: Dạ dày nhăn nhó quá tải (y=1060..1650)            |
| - Cảnh 3: Bước 2 (Nồi ninh bên phải, Card Step 2 bên trái)  |
|           Bước 3 (Bát rây cháo bên trái, Card Step 3 bên phải)
| - Cảnh 4: 3 Huy hiệu thìa/mặt trời/lịch (y=1100..1440)      |
|           Khối CTA Capsule viên nang (y=1500..1650)         |
|                                                             |
+-------------------------------------------------------------+ y = 1650
| [VÙNG TRỐNG 3 / ĐÁY TRANH: y = 1650 .. 1920]                |
| - Cảnh 1: Thẻ kết luận đáy (y=1760..1880)                   |
| - Cảnh 2: Thẻ Washi Đỏ cảnh báo (y=1690..1845)              |
| - Cảnh 4: Doodle nhỏ trái tim & quả dâu tây (y=1680..1850)  |
+-------------------------------------------------------------+ y = 1920
```

---

## 2. QUY CHUẨN TẠO ẢNH CHO TỪNG CẢNH (SCENE-BY-SCENE PROMPT ARCHITECTURE)

### 📌 CẢNH 1: HOOK CẢNH BÁO SAI LẦM
* **Mục đích:** Đặt vấn đề giật mình, cảnh báo sai lầm kinh điển của phụ huynh.
* **Negative Space bắt buộc:**
  * Toàn bộ dải $y \in [0, 500]$ **HOÀN TOÀN TRỐNG TRƠN NỀN GIẤY KEM `#F5EBD7`** (để renderer đặt dải ruy băng $y \in [35, 155]$, thẻ cảnh báo đỏ $y \in [175, 410]$ và huy hiệu y khoa $y \in [430, 485]$).
  * Đỉnh đầu của em bé **BẮT ĐẦU TỪ $y \ge 510$**, đặt ngay chính giữa hoặc hơi lệch trái.
  * Góc dưới đáy $y \in [1750, 1920]$ để trống cho thẻ kết luận.
* **Prompt GPT chuẩn:**
  ```text
  A vertical 9:16 warm watercolor and soft pencil sketch illustration on cream vintage paper (background hex color #F5EBD7). 
  SUBJECT: A cute 6-month-old Vietnamese baby sitting in a wooden high chair, looking surprised and worried with wide curious eyes. Next to the baby is a simple prohibited red medical symbol outline.
  LAYOUT & COMPOSITION:
  - CRITICAL: Keep the TOP 28% of the canvas (from top edge down to 500px) COMPLETELY EMPTY with clean plain cream paper background #F5EBD7 (no drawings, no clouds, no text). The baby's head must start strictly below the upper 28% line.
  - Keep the BOTTOM 10% of the canvas completely empty and clean.
  - Baby is positioned comfortably in the center-lower half.
  - STYLE: Cozy children's picture book illustration, delicate warm watercolor washes, dark pencil outline, gentle pastel tones. ABSOLUTELY NO TEXT, NO LETTERS, NO NUMBERS, NO TYPOGRAPHY ANYWHERE ON THE IMAGE.
  ```

---

### 📌 CẢNH 2: CƠ CHẾ Y KHOA & GIẢI MÃ NGUYÊN NHÂN
* **Mục đích:** So sánh trực quan trạng thái "Hấp thu êm dịu" vs "Quá tải đầy hơi".
* **Negative Space bắt buộc:**
  * Dải trên $y \in [0, 170]$: Trống cho Ruy băng tiêu đề.
  * Dải giữa $y \in [880, 1060]$: **HOÀN TOÀN TRỐNG NỀN GIẤY KEM** (dành cho Thẻ Washi Xanh lá).
  * Dải đáy $y \in [1680, 1920]$: **HOÀN TOÀN TRỐNG NỀN GIẤY KEM** (dành cho Thẻ Washi Đỏ).
  * Hình 1 (Dạ dày vui vẻ): Nằm trọn trong vùng $y \in [180, 850]$.
  * Hình 2 (Dạ dày căng tức): Nằm trọn trong vùng $y \in [1080, 1660]$.
* **Prompt GPT chuẩn:**
  ```text
  A vertical 9:16 watercolor and graphite pencil medical illustration for children, on textured warm cream paper (#F5EBD7).
  TWO CONTRASTING FIGURES ARRANGED VERTICALLY:
  1. UPPER HALF (between 15% and 45% of total height): A cute anthropomorphic human stomach character smiling peacefully, floating blissfully on a soft swirl of warm breast milk, surrounded by small golden sparkle stars.
  2. MIDDLE ZONE (between 46% and 55% of total height): MUST BE 100% EMPTY PLAIN CREAM PAPER BACKGROUND (#F5EBD7) with zero visual elements.
  3. LOWER HALF (between 56% and 86% of total height): A stressed, sad cartoon stomach character clenching its tummy with tiny hands, showing internal gas bubbles and indigestible grains inside, with tiny sweat drops and wavy tummy ache lines.
  4. BOTTOM ZONE (bottom 14% of canvas): MUST BE 100% EMPTY PLAIN CREAM PAPER BACKGROUND.
  STYLE: Charming storybook medical sketch, pastel watercolor accents, warm aesthetic. ABSOLUTELY NO TEXT, NO WORDS, NO CAPTIONS.
  ```

---

### 📌 CẢNH 3: 3 BƯỚC THỰC HÀNH SO LE ZIGZAG
* **Mục đích:** Hướng dẫn 3 bước chuẩn xác định lượng.
* **Negative Space bắt buộc (Bố cục 2 cột so le Zigzag):**
  * Dải trên $y \in [0, 170]$: Trống cho Ruy băng tiêu đề.
  * **Hàng 1 ($y \in [200, 650]$):**
    - Bên trái ($x \in [50, 480]$): Hình bao gạo tẻ / chén gạo và bông lúa.
    - Bên phải ($x \in [500, 1040]$): **TRỐNG 100% NỀN GIẤY KEM** cho Card Bước 1.
  * **Hàng 2 ($y \in [700, 1250]$):**
    - Bên trái ($x \in [50, 580]$): **TRỐNG 100% NỀN GIẤY KEM** cho Card Bước 2.
    - Bên phải ($x \in [520, 1040]$): Hình nồi nấu cháo sứ trên bếp lửa nhỏ liu riu có khói bốc lên.
  * **Hàng 3 ($y \in [1300, 1850]$):**
    - Bên trái ($x \in [50, 490]$): Hình rây lọc mắt nhỏ 0.5mm miết cháo sánh mịn vào bát hoa nhỏ và thìa gỗ.
    - Bên phải ($x \in [510, 1040]$): **TRỐNG 100% NỀN GIẤY KEM** cho Card Bước 3.
* **Prompt GPT chuẩn:**
  ```text
  A vertical 9:16 hand-drawn watercolor illustration on cream paper background (#F5EBD7), showcasing 3 culinary steps arranged in a strict ZIG-ZAG 2-COLUMN layout:
  - ROW 1 (Upper section): On the LEFT half, a rustic burlap bag of premium whole-grain rice spilling glistening white grains, with fresh golden rice ears beside a glass measuring cup. The RIGHT half of Row 1 must be COMPLETELY EMPTY plain cream paper.
  - ROW 2 (Middle section): On the RIGHT half, a charming traditional ceramic cooking pot simmering gently on a small portable gas stove with gentle blue flame and soft aromatic steam rising. The LEFT half of Row 2 must be COMPLETELY EMPTY plain cream paper.
  - ROW 3 (Lower section): On the LEFT half, a fine stainless steel mesh strainer (sieve) pressing smooth rice puree into a lovely ceramic baby bowl, with a small wooden baby spoon lying nearby. The RIGHT half of Row 3 must be COMPLETELY EMPTY plain cream paper.
  - TOP EDGE (top 10% of canvas): Completely empty plain cream background for banner.
  STYLE: Warm culinary watercolor art, soft pencil outlines, authentic paper texture. ABSOLUTELY NO TEXT, NO NUMBERS, NO OVERLAPPING GRAPHICS.
  ```

---

### 📌 CẢNH 4: LỜI KHUYÊN MẸ DÂU & CTA FOLLOW
* **Mục đích:** Khoảnh khắc ấm áp mẹ chăm con, checklist 3 điều cần nhớ và kêu gọi follow.
* **Negative Space bắt buộc:**
  * Dải trên $y \in [0, 170]$: Trống cho Ruy băng tiêu đề.
  * Vùng tranh vẽ nhân vật: $y \in [180, 1000]$ (Mẹ bỉm dịu dàng đang xúc thìa cháo nhỏ đút cho em bé ngồi ghế ăn cười rạng rỡ).
  * Dải $y \in [1050, 1460]$: **HOÀN TOÀN TRỐNG NỀN GIẤY KEM** cho 3 Huy hiệu thìa nhỏ / mặt trời cữ sáng / lịch 3 ngày.
  * Dải $y \in [1480, 1660]$: **HOÀN TOÀN TRỐNG NỀN GIẤY KEM** cho Khối viên nang CTA Follow.
  * Dưới đáy $y \in [1680, 1880]$ ở chính giữa: Hình doodle nhỏ trái tim và quả dâu tây mini dễ thương.
* **Prompt GPT chuẩn:**
  ```text
  A heartwarming vertical 9:16 watercolor and colored pencil illustration on vintage cream paper (#F5EBD7).
  COMPOSITION & SECTIONS:
  - UPPER HALF (from 12% to 52% of canvas height): A loving Vietnamese mother with gentle brown hair in a neat bun, smiling affectionately as she feeds her happy 6-month-old baby in a high chair with a tiny baby spoon. Behind them are tiny, cute decorative doodles of a smiling sun and a baby diaper floating softly.
  - MIDDLE TO LOWER SECTION (from 53% to 86% of canvas height): MUST BE 100% EMPTY PLAIN CREAM PAPER BACKGROUND (#F5EBD7) with absolutely nothing drawn. This area is strictly reserved for UI overlays.
  - BOTTOM EMBELLISHMENT (bottom 12% centered): A pair of tiny, sweet hand-drawn doodles: a pink sketch heart speech bubble and a cute smiling strawberry character with green leaves.
  STYLE: Studio Ghibli inspired warmth, gentle watercolor washes, warm emotional parenting tone. ZERO TEXT, NO LABELS, NO WATERMARKS.
  ```

---

## 3. BẢNG CHECKLIST KIỂM ĐỊNH TRƯỚC KHI RENDER (IMAGE AUDIT CHECKLIST)

Trước khi đưa bất kỳ ảnh nào vào thư mục `raw_gpt_images/` để render hàng loạt, kiểm tra 5 tiêu chí:

| STT | Tiêu chí kiểm định | Yêu cầu bắt buộc | Đạt / Không đạt |
| :---: | :--- | :--- | :---: |
| 1 | **Màu nền Canvas** | Đồng nhất màu giấy kem cổ `#F5EBD7`, không có viền đen, không có nền trắng tinh | [ ] |
| 2 | **100% Không có chữ (Zero Text)** | Tuyệt đối không để AI vẽ chữ tiếng Anh, tiếng Trung hoặc ký tự loằng ngoằng trong tranh | [ ] |
| 3 | **Negative Space dải trên ($y < 180$)** | Trống trơn để đặt dải Ruy băng 3D Tiêu đề | [ ] |
| 4 | **Bố cục so le Zigzag Cảnh 3** | Bao gạo bên trái, Nồi bên phải, Bát rây bên trái — các vùng đối diện trống 100% | [ ] |
| 5 | **Khoảng trống CTA Cảnh 4** | Dải $y \in [1050, 1660]$ hoàn toàn không có nét vẽ đè lên 3 huy hiệu và nút Follow | [ ] |

---

## 4. NGUYÊN TẮC ĐẶT TÊN FILE CHUẨN ĐỂ KHÔNG BAO GIỜ NHẦM LẪN
### (Bắt buộc tuân thủ cho toàn bộ 330 Slot và AI tạo ảnh)

Để đảm bảo quy trình chạy hàng loạt và quản lý tài nguyên tuyệt đối chính xác giữa ChatGPT Project và App Renderer, toàn bộ ảnh tạo ra **BẮT BUỘC** phải tuân theo cấu trúc định danh:

```text
day_{DD}_slot_{SS}_scene_{CC}.jpg
```
* **Trong đó:**
  * `{DD}`: Số thứ tự Ngày (từ `01` đến `30`, 2 chữ số).
  * `{SS}`: Số thứ tự Slot trong ngày (từ `01` đến `11`, 2 chữ số).
  * `{CC}`: Số thứ tự Cảnh trong video (từ `01` đến `04`, 2 chữ số).
* **Ví dụ mẫu chuẩn:**
  * Cảnh 1 Ngày 1 Slot 1: `day_01_slot_01_scene_01.jpg`
  * Cảnh 2 Ngày 1 Slot 1: `day_01_slot_01_scene_02.jpg`
  * Cảnh 3 Ngày 1 Slot 1: `day_01_slot_01_scene_03.jpg`
  * Cảnh 4 Ngày 1 Slot 1: `day_01_slot_01_scene_04.jpg`
  * Cảnh 1 Ngày 1 Slot 2: `day_01_slot_02_scene_01.jpg`
  * Cảnh 3 Ngày 2 Slot 5: `day_02_slot_05_scene_03.jpg`

### Quy định thư mục lưu trữ:
1. **Lưu trữ cục bộ cho dự án từng slot:**
   `projects/day_{DD}_slot_{SS}_golden/raw_gpt_images/`
   * Trong thư mục này, hệ thống hỗ trợ cả 2 cách đặt tên:
     * Cách 1 (Khuyên dùng): `day_{DD}_slot_{SS}_scene_01.jpg` .. `scene_04.jpg`
     * Cách 2 (Tên ngắn gọn): `s1.jpg`, `s2.jpg`, `s3.jpg`, `s4.jpg`
2. **Thư mục tập trung xuất kho hàng loạt:**
   `knowledge/an_dam_me_dau/raw_images/day_{DD}/`
   * Toàn bộ 44 ảnh của 11 slot trong ngày được đặt theo tên chuẩn `day_{DD}_slot_{SS}_scene_{CC}.jpg`.

---

## 5. TÍCH HỢP HÀNG LOẠT VÀO HỆ THỐNG AGENT & TOOLS

1. **Cơ chế Fallback thông minh của `slot_builder.py`:**
   - Khi chạy `python scripts/generate_lively_slot.py --day D --slot S`, hệ thống tự động quét thư mục `raw_gpt_images/`.
   - Nếu có sẵn ảnh vẽ nghệ thuật đúng tên chuẩn, hệ thống **ưu tiên nạp 100% ảnh vẽ GPT**.
   - Nếu chưa có, hệ thống tự động chuyển sang bộ đồ họa vector clean để hoàn thành video mà không gây lỗi dừng tiến trình.
2. **Thuật toán Auto-Fit:**
   - Dù ảnh vẽ GPT có xê dịch nhẹ vài chục pixel, hàm `draw_ribbon_banner`, `draw_step_pill_badge`, `wrap_text` và `draw_cta_capsule` luôn tự động co giãn và căn chỉnh để các thẻ chữ, huy hiệu không bao giờ bị tràn khung hay đè lên tranh vẽ.
