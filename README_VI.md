# Gehihi V2 - Máy Chủ Quản Trị & Điều Khiển Robot Xiaozhi AI (Render.com)

Hệ thống máy chủ điều khiển thông minh và trung tâm quản trị toàn diện dành cho **Robot AI Xiaozhi (ESP32-S3 Mạch Tím Huyền Thoại)**, hỗ trợ giao diện Web Dashboard quản trị hiện đại bằng **Tiếng Việt**, đồng thời cung cấp đầy đủ các cổng dịch vụ OTA Endpoint, WebSocket AI đàm thoại thời gian thực hai chiều và REST API.

- **Kho mã nguồn GitHub:** [https://github.com/meeyzinh/gehihiv2](https://github.com/meeyzinh/gehihiv2)
- **Link Máy Chủ Trực Tuyến:** [https://gehihiv2.onrender.com/](https://gehihiv2.onrender.com/)
- **Giao Diện Quản Trị Web Dashboard:** [https://gehihiv2.onrender.com/](https://gehihiv2.onrender.com/) (hoặc `/admin`, `/ai`)
- **Cổng Cập Nhật OTA Cho Robot:** `https://gehihiv2.onrender.com/xiaozhi/ota/`
- **Cổng WebSocket AI Đàm Thoại Thời Gian Thực:** `wss://gehihiv2.onrender.com/xiaozhi/v1/`
- **Tải Firmware Trực Tiếp:** `https://gehihiv2.onrender.com/firmware/merged-binary.bin`

---

## 🌟 Tính Năng Nổi Bật

1. **Trung Tâm Quản Trị Web Dashboard (Tiếng Việt Toàn Diện):**
   - **Bảng điều khiển & Giám sát thời gian thực:** Trạng thái kết nối robot (Online/Offline, MAC `14:C1:9F:C4:EE:D0`, IP, FW v2.5.0), số lượt trò chuyện, độ trễ từng chặng (ASR, LLM, TTS).
   - **Màn hình sóng âm thanh & VAD:** Biểu đồ đo mức âm lượng Micro (RMS VU Meter), sàn nhiễu (Noise Floor) và trạng thái phát hiện giọng nói (Speech Active).
   - **Bộ não AI đa nền tảng (Multi-Engine Switcher):** Kích hoạt 1-click giữa Groq (Llama 3.3/Qwen 2.5 siêu tốc < 0.4s), Google Gemini (Gemini 2.5 Flash chuẩn tiếng Việt), DeepSeek (DeepSeek V3/R1) và OpenAI (GPT-4o).
   - **Cấu hình API Key & Lời nhắc hệ thống (Prompt Persona):** Chỉnh sửa trực tiếp tên robot, tính cách, câu lệnh xưng hô ngay trên giao diện web.
   - **Thử nghiệm đàm thoại trực tiếp:** Chat test hai chiều trực tiếp trên trình duyệt web và nghe thử giọng đọc TTS phát qua loa máy tính.
   - **Điều khiển robot từ xa:** Chỉnh âm lượng, đánh thức (Wakeup), ngắt lời (Interrupt), tạm dừng (Standby).

2. **Tương Thích Tuyệt Đối Với Gói Render.com Miễn Phí (Free Cloud):**
   - Tự động nhận diện cổng động `$PORT` do Render cấp phát.
   - Nginx Reverse Proxy điều phối trơn tru cả giao diện Web, WebSocket thời gian thực WSS và OTA API trên một tên miền SSL bảo mật duy nhất.
   - Cơ chế tự nhận diện Host (`X-Forwarded-Host`) giúp WebSocket URL và OTA URL luôn tự thích ứng chính xác theo tên miền triển khai.

3. **Firmware ESP32-S3 Chuẩn Xác 100% Theo "Mạch Tím Huyền Thoại":**
   - Cấu hình theo đúng sơ đồ mạch `Mini ESP32-S3-N16R8` (16MB Flash Octal, 8MB PSRAM Octal).
   - Microphone I2S MEMS (INMP441 / MSM261S) & Loa công suất I2S (NS4168 / MAX98357A có chân kích hoạt PA Enable GPIO 17).
   - Màn hình OLED SSD1306 0.96 inch hiển thị biểu cảm khuôn mặt sống động.
   - Đèn trạng thái WS2812 RGB LED đa sắc (Lắng nghe, Suy nghĩ, Đang nói).

---

## 🛠️ Bảng Sơ Đồ Chân Phần Cứng (ESP32-S3 Mạch Tím)

| Khối Chức Năng | Tên Linh Kiện | Chân ESP32-S3 | Ghi Chú Kỹ Thuật |
| :--- | :--- | :--- | :--- |
| **Vi Điều Khiển (MCU)** | ESP32-S3-WROOM-1 (XH-S3E) | N16R8 | 16MB Flash (DIO/80M), 8MB PSRAM (Octal) |
| **Microphone (Audio In)** | I2S MEMS Microphone | **WS = GPIO 4**<br>**SCK = GPIO 5**<br>**DIN = GPIO 6** | Simplex Mode, 16.000 Hz, 16-bit Mono |
| **Loa & Khuếch Đại (Audio Out)** | I2S Power Amp (NS4168/MAX98357A) | **DOUT = GPIO 7**<br>**BCLK = GPIO 15**<br>**LRCK = GPIO 16**<br>**PA_EN = GPIO 17** | **GPIO 17 bật mức HIGH (1)** để cấp nguồn cho chip khuếch đại loa |
| **Màn Hình (OLED Display)** | 0.96 inch SSD1306 (128x64) | **SDA = GPIO 41**<br>**SCL = GPIO 42** | Giao tiếp I2C Address 0x3C, Clock 400kHz |
| **Nút Nhấn Điều Khiển** | Nút BOOT & Nút Phụ (Touch/PTT) | **BOOT = GPIO 0**<br>**TOUCH = GPIO 47** | Nhấn BOOT đổi trạng thái đàm thoại; Giữ 3s để vào chế độ cài Wi-Fi |
| **Đèn LED Đa Sắc** | WS2812 Addressable RGB LED | **RGB DATA = GPIO 48** | Hiệu ứng xung ánh sáng theo trạng thái Robot |

---

## ⚡ Hướng Dẫn Nạp Firmware Cho Mạch Tím ESP32-S3

Firmware đã được biên dịch hoàn chỉnh thành file nhị phân gộp **`merged-binary.bin`** (bao gồm bootloader, partition-table, ota_data, app xiaozhi và assets giao diện tiếng Việt).

### Cách 1: Nạp Nhanh 1 Dòng Lệnh Bằng `esptool.py` (Khuyến Nghị)

1. Cắm cáp USB Type-C nối máy tính với cổng USB trên mạch tím.
2. Xác định cổng COM (ví dụ: `COM3`, `COM4` trên Windows).
3. Chạy lệnh sau trong PowerShell hoặc Terminal:

```bash
# Nạp 1 file duy nhất vào offset 0x0 (Tất cả trong một):
esptool.py --chip esp32s3 -p COM3 -b 921600 write_flash 0x0 firmware/merged-binary.bin
```

*(Nếu dùng nạp từng phân vùng riêng lẻ)*:
```bash
esptool.py --chip esp32s3 -p COM3 -b 921600 write_flash \
  0x0 firmware/bootloader.bin \
  0x8000 firmware/partition-table.bin \
  0xd000 firmware/ota_data_initial.bin \
  0x20000 firmware/xiaozhi.bin \
  0x800000 firmware/generated_assets.bin
```

### Cách 2: Kết Nối Wi-Fi Lần Đầu Cho Robot
1. Sau khi nạp xong, mở mạch lên. Màn hình OLED sẽ hiển thị thông báo kết nối Wi-Fi.
2. Dùng điện thoại hoặc máy tính tìm mạng Wi-Fi phát ra từ robot (Tên mạng thường có dạng: `Xiaozhi-XXXX` hoặc `Gehihi-XXXX`).
3. Kết nối vào Wi-Fi đó, trình duyệt sẽ tự động mở trang cấu hình tại `192.168.4.1`.
4. Chọn mạng Wi-Fi nhà bạn và nhập mật khẩu.
5. Robot sẽ tự động kết nối Wi-Fi, gửi request đến `https://gehihiv2.onrender.com/xiaozhi/ota/`, nhận link WebSocket và bắt đầu nói chuyện với bạn bằng tiếng Việt!

---

## 🚀 Hướng Dẫn Triển Khai Lên Render.com (Hoàn Toàn Miễn Phí)

### Cách 1: Triển Khai Nhanh Qua Blueprint (Khuyến Nghị Nhất)
1. Đăng nhập vào [Render.com](https://render.com/).
2. Nhấn vào **New +** ở góc trên bên phải -> Chọn **Blueprint**.
3. Kết nối với kho lưu trữ GitHub của bạn: `https://github.com/meeyzinh/gehihiv2`.
4. Render sẽ tự động đọc file `render.yaml` và thiết lập toàn bộ Web Service `gehihiv2` với Docker môi trường chuẩn.
5. Nhấn **Apply** và chờ Render build hoàn tất trong ~2-3 phút!

### Cách 2: Triển Khai Thủ Công (Web Service)
1. Trên Render Dashboard, chọn **New +** -> **Web Service**.
2. Chọn kho GitHub: `meeyzinh/gehihiv2`.
3. Điền các trường cấu hình:
   - **Name:** `gehihiv2`
   - **Region:** `Oregon (US West)` hoặc `Singapore`
   - **Branch:** `main`
   - **Environment:** `Docker`
   - **Dockerfile Path:** `./Dockerfile`
   - **Instance Type:** `Free`
4. Phần **Environment Variables** (Biến môi trường):
   - `PORT`: `10000`
   - `RENDER_EXTERNAL_HOSTNAME`: `gehihiv2.onrender.com`
   - `RENDER_EXTERNAL_URL`: `https://gehihiv2.onrender.com`
   - `WEBSOCKET_URL`: `wss://gehihiv2.onrender.com/xiaozhi/v1/`
   - `GEMINI_API_KEY`: *(Nhập API Key Google Gemini của bạn)*
   - `GROQ_API_KEY`: *(Nhập API Key Groq của bạn nếu có)*
5. Nhấn **Create Web Service** và tận hưởng server riêng của bạn!
