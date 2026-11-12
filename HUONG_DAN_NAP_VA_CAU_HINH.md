# HƯỚNG DẪN NẠP FIRMWARE & SỬ DỤNG WEB ADMIN CHO ROBOT MINI ESP32-S3 (MẠCH TÍM)

Firmware này được biên dịch trực tiếp từ bộ mã nguồn **Xiaozhi ESP32** theo đúng sơ đồ phần cứng **"Mạch Tím Huyền Thoại" (XH-S3E WiFi+BT N16R8)**, hỗ trợ đầy đủ **Tiếng Việt**, kết nối trực tiếp đến máy chủ AI **`https://gehihiv2.onrender.com`**, và tích hợp sẵn **Web Admin Control Panel** trên cổng **`8080`** (`http://192.168.4.1:8080`).

---

## 📌 1. Bảng phân bổ chân GPIO mặc định ("Mạch Tím Huyền Thoại")

| Khối chức năng | Ngoại vi | Chân ESP32-S3 | Ghi chú kỹ thuật |
| :--- | :--- | :--- | :--- |
| **Âm thanh Ra (Loa)** | **MAX98357A** | **DIN = GPIO 7**, **BCLK = GPIO 15**, **LRC = GPIO 16**, **PA_EN = GPIO 17** | PA_EN kích hoạt công suất IC khuếch đại (Fix lỗi không ra tiếng) |
| **Âm thanh Vào (Mic)** | **INMP441** | **SD = GPIO 6**, **SCK = GPIO 5**, **WS = GPIO 4** | Lọc DC-Blocker IIR & Stereo tự động nhận kênh |
| **Màn hình hiển thị** | **OLED I2C 0.96"** | **SDA = GPIO 41**, **SCL = GPIO 42** | Socket 4 chân hàn sẵn trên mạch XH-S3E (SSD1306 / SH1106 128x64) |
| **Động cơ bánh xe** | **MX1616 (Trái)** | **IN1 = GPIO 1**, **IN2 = GPIO 2** | Điều xung LEDC PWM |
| | **MX1616 (Phải)** | **IN3 = GPIO 9**, **IN4 = GPIO 10** | Tránh trùng chân màn hình 41/42 |
| **Nút nhấn & Cảm biến chạm**| **BOOT & TTP223** | **GPIO 0** | Nhấn 1 lần: Bật/Tắt chat; Giữ 3s khi bật nguồn: Khôi phục chân mặc định |
| **Đèn LED** | **WS2812 RGB** | **DIN = GPIO 48** (8 bóng) | Hiển thị trạng thái AI |
| | **Đèn sợi đốt COB** | **GPIO 21** | Bật/tắt bằng giọng nói qua MCP Tool |
| **Cảm biến mở rộng** | **Cảm biến khoảng cách Laser** | **SDA = GPIO 10**, **SCL = GPIO 11** | VL53L0X ToF |
| | **Cảm biến siêu âm** | **TRIG = GPIO 13**, **ECHO = GPIO 12** | HC-SR04 |
| | **Đo điện áp pin ADC** | **GPIO 14** | ADC2_CH3 |
| | **Thẻ nhớ Micro SD SPI** | **CS = 47**, **CLK = 39**, **MOSI = 38**, **MISO = 40** | Khe thẻ nhớ SPI |

*(Toàn bộ các chân trên đều có thể thay đổi linh hoạt trong trang Web Admin mà không cần nạp lại code)*

---

## 🌐 2. Hướng dẫn truy cập & sử dụng Web Admin Quản trị (Cổng 8080)

Trang quản trị được thiết kế theo đúng giao diện chuẩn trong thư mục `SoDoMach/HostAdmin`:

### Cách vào trang cấu hình:
1. **Khi Robot chưa kết nối WiFi (hoặc đang phát sóng AP):**
   - Dùng điện thoại hoặc máy tính kết nối vào sóng Wi-Fi của Robot: `Xiaozhi-XXXX` (hoặc `Megabot-XXXX`).
   - Mở trình duyệt web truy cập: **`http://192.168.4.1:8080`**
2. **Khi Robot đã kết nối WiFi nhà:**
   - Xem địa chỉ IP của Robot (hiển thị trên OLED hoặc router).
   - Truy cập: **`http://<IP-ROBOT>:8080`** (Ví dụ: `http://192.168.1.123:8080`).

### 3 Tab quản trị chính:
* 🗺️ **Bản đồ chân GPIO (Tab 1):** Tùy chỉnh bất kỳ chân nào của Động cơ IN1..IN4, Màn hình SDA/SCL, Micro, Loa, LED, Cảm biến, v.v. Nhấn **"💾 LƯU VÀO CHIP"** hoặc **"💾 LƯU & KHỞI ĐỘNG LẠI"**.
* ⚙️ **Hiệu chỉnh động cơ (Tab 2):** Cân bằng lực bánh trái/phải (`Left Trim`, `Right Trim`), ngưỡng khởi động `Min PWM`, và chọn loại Driver (`MX1616` / `DRV8833` / `L298N Mini`).
* 🛡️ **Cảm biến an toàn & Pin (Tab 3):** Cài đặt ngưỡng dừng khi gặp vật cản (cm), ngưỡng phát hiện mép bàn chống rơi (mm), hiệu chuẩn thang đo điện áp Pin.
* 🎮 **Thanh điều khiển nhanh:** Nút bấm thử nghiệm chuyển động: **LẮC LƯ**, **NHẢY MÚA**, **TỰ ĐI**, **DỪNG**, cùng bàn phím ảo (W, A, S, D, Q, E, Space).

> [!IMPORTANT]
> **Cơ chế an toàn (Safe Reset):** Nếu vô tình đổi sai chân làm màn hình không lên hoặc chập chân, chỉ cần **giữ nút BOOT (GPIO 0) trong 3 giây khi vừa bật nguồn**, robot sẽ tự động xóa sạch bộ nhớ NVS và khôi phục toàn bộ chân cắm về trạng thái ban đầu của "Mạch Tím Huyền Thoại"!

---

## 🚀 3. Hướng dẫn nạp Firmware (Cổng 0x0)

File nạp duy nhất: **`firmware_robot_0x0.bin`** (đã gộp sẵn Bootloader, Partition Table, OTA Data, Assets Tiếng Việt và App).

### CÁCH 1: Dùng Tool 1-Click tự động (Khuyên dùng)
1. Cắm cáp USB nối mạch ESP32-S3 với máy tính.
2. Mở file **`flash_robot_0x0.bat`**.
3. Nhập tên cổng COM của robot (ví dụ: `COM3`, `COM5`, `COM8`) rồi nhấn **Enter**.
4. Tool sẽ tự động xoá nạp toàn bộ firmware tại địa chỉ `0x0`.

### CÁCH 2: Nạp bằng trình duyệt Web (Không cần cài phần mềm)
1. Dùng Google Chrome hoặc Microsoft Edge truy cập: [https://espressif.github.io/esptool-js/](https://espressif.github.io/esptool-js/)
2. Đặt Baudrate: `460800` $\rightarrow$ Nhấn **Connect** $\rightarrow$ Chọn cổng COM của mạch.
3. Ở dòng đầu tiên:
   - Điền địa chỉ: **`0x0`**
   - Bấm **Choose file** $\rightarrow$ Chọn file `firmware_robot_0x0.bin`.
4. Nhấn **Program** và đợi thanh tiến trình chạy đến 100%.

### CÁCH 3: Nạp bằng lệnh esptool (Dòng lệnh)
```bash
python -m esptool --chip esp32s3 -p COMx -b 460800 write-flash 0x0 firmware_robot_0x0.bin
```

---

## 🤖 4. Trạng thái kết nối Server AI (Mô hình Wrapper Thông minh: Control Plane + MCP)
- **Luồng Âm thanh & Hội thoại AI (ASR, LLM, TTS):** Kết nối trực tiếp máy chủ gốc **`wss://api.tenclass.net/xiaozhi/v1/`** (Đảm bảo 100% giọng chuẩn nữ Tiểu Song / Minimax, cực mượt, không trễ, miễn phí).
- **Máy chủ OTA:** **`https://gehihiv2.onrender.com/xiaozhi/ota/`** (Tự động cấp phát URL cụm gốc cho Robot khi khởi động).
- **Endpoint MCP Server (Công cụ mở rộng):** **`https://gehihiv2.onrender.com/mcp`** (Cung cấp các công cụ: Báo giờ, Thời tiết, Điều khiển xe, Đèn LED, Ghi chú, CPU máy tính, Phát nhạc YouTube).
- **Trang Quản trị & Control Plane:** **`https://gehihiv2.onrender.com`** (Bàn điều khiển D-Pad, Giám sát COM8, Phát nhạc, Quản lý thiết bị).
- **Ngôn ngữ:** Tiếng Việt (thông báo khởi động, kết nối Wi-Fi, trạng thái đối thoại AI).
