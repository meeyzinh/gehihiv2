const { chromium } = require('playwright');
const fs = require('fs');
const readline = require('readline');
const path = require('path');

// Hàm dừng terminal chờ người dùng nhấn Enter sau khi đã đăng nhập
function waitForEnter(promptText) {
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
  });

  return new Promise((resolve) => {
    rl.question(promptText, () => {
      rl.close();
      resolve();
    });
  });
}

// Hàm tự động cuộn trang từ trên xuống dưới để load đầy đủ ảnh lazy-load và hiệu ứng
async function autoScroll(page) {
  console.log('🔄 Đang tự động cuộn trang để kích hoạt toàn bộ lazy-load...');
  await page.evaluate(async () => {
    await new Promise((resolve) => {
      let totalHeight = 0;
      const distance = 300;
      const timer = setInterval(() => {
        const scrollHeight = document.body.scrollHeight;
        window.scrollBy(0, distance);
        totalHeight += distance;

        if (totalHeight >= scrollHeight) {
          clearInterval(timer);
          window.scrollTo(0, 0); // Cuộn lại lên đầu trang
          resolve();
        }
      }, 150);
    });
  });
  // Đợi thêm 2 giây để các animation và ảnh ổn định
  await page.waitForTimeout(2000);
}

(async () => {
  const targetUrl = 'https://memory.gmbot.name.vn/';
  console.log('\n======================================================');
  console.log('🚀 Đang khởi động trình duyệt Chromium...');
  console.log('======================================================\n');

  // Khởi chạy trình duyệt thật (có giao diện đồ họa)
  const browser = await chromium.launch({
    headless: false,
    args: ['--start-maximized'], // Mở toàn màn hình cho dễ thao tác
  });

  const context = await browser.newContext({
    viewport: null, // Sử dụng kích thước cửa sổ thực tế
    deviceScaleFactor: 1,
  });

  const page = await context.newPage();

  console.log(`🌐 Đang mở trang: ${targetUrl}`);
  await page.goto(targetUrl, { waitUntil: 'domcontentloaded', timeout: 60000 });

  console.log('\n******************************************************');
  console.log('👉 BƯỚC 1: Hãy đăng nhập tài khoản trên cửa sổ trình duyệt.');
  console.log('👉 BƯỚC 2: Khi đã vào được trang chính, quay lại terminal này.');
  console.log('👉 BƯỚC 3: Nhấn phím [ENTER] để tiếp tục cào toàn bộ dữ liệu.');
  console.log('******************************************************\n');

  await waitForEnter('Nhấn phím [ENTER] khi bạn đã đăng nhập xong: ');

  console.log('\n⏳ Đang xử lý cào trang, vui lòng chờ trong giây lát...');

  // Đợi mạng ổn định
  await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {
    console.log('⚠️ Network chưa hoàn toàn idle, vẫn tiếp tục lấy dữ liệu...');
  });

  // Tự động cuộn trang để load lazy-load
  await autoScroll(page);

  // 1. Lưu mã nguồn HTML đầy đủ
  console.log('💾 Đang lưu mã nguồn HTML render đầy đủ...');
  const htmlContent = await page.content();
  const htmlPath = path.resolve(__dirname, 'memory_page.html');
  fs.writeFileSync(htmlPath, htmlContent, 'utf-8');
  console.log(`✅ Đã tạo file HTML thành công: memory_page.html`);

  // 2. Chụp ảnh toàn bộ chiều dài trang (fullPage screenshot)
  console.log('📸 Đang chụp ảnh toàn bộ chiều dài trang...');
  const screenshotPath = path.resolve(__dirname, 'memory_full.png');
  await page.screenshot({
    path: screenshotPath,
    fullPage: true,
  });
  console.log(`✅ Đã tạo ảnh chụp màn hình thành công: memory_full.png`);

  console.log('\n🎉 Hoàn thành xuất sắc Bước 1! Đang đóng trình duyệt...');
  await browser.close();
  console.log('👉 Bạn đã có 2 file memory_page.html và memory_full.png trong thư mục dự án.\n');
})();
