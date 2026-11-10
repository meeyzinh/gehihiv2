const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

async function captureAllPages() {
  console.log('🔄 Đang lấy captcha và đăng nhập...');
  const capRes = await fetch('https://memory.gmbot.name.vn/api/captcha?t=' + Date.now());
  const capData = await capRes.json();
  const captchaCode = [...capData.svg.matchAll(/<text[^>]*>([^<]+)<\/text>/g)].map(m => m[1].trim()).join('');

  const loginRes = await fetch('https://memory.gmbot.name.vn/api/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      username: '330730',
      password: '123456',
      captchaId: capData.captchaId,
      captchaCode
    })
  });

  const loginData = await loginRes.json();
  if (!loginRes.ok) throw new Error('Login failed: ' + JSON.stringify(loginData));
  const token = loginData.token;
  console.log('✅ Đăng nhập thành công! Token:', token.slice(0, 20) + '...');

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();

  await page.addInitScript((t) => {
    localStorage.setItem('token', t);
  }, token);

  console.log('🌐 Đang mở english-tutor.html...');
  await page.goto('https://memory.gmbot.name.vn/english-tutor.html', { waitUntil: 'networkidle', timeout: 60000 });
  await page.waitForTimeout(2000);

  const tabs = [
    { id: 'today', name: 'Hôm nay', btnSelector: '.side-nav button[data-section="today"]' },
    { id: 'roadmap', name: 'Lộ trình', btnSelector: '.side-nav button[data-section="roadmap"]' },
    { id: 'library', name: 'Giáo trình', btnSelector: '.side-nav button[data-section="library"]' },
    { id: 'create', name: 'Tự tạo bài', btnSelector: '.side-nav button[data-section="create"]' },
    { id: 'report', name: 'Báo cáo', btnSelector: '.side-nav button[data-section="report"]' },
  ];

  for (const tab of tabs) {
    console.log(`📸 Đang chụp tab: ${tab.name} (${tab.id})...`);
    await page.click(tab.btnSelector);
    await page.waitForTimeout(1000);

    const shotPath = path.resolve(__dirname, `et_tab_${tab.id}.png`);
    await page.screenshot({ path: shotPath, fullPage: true });
    console.log(`✅ Đã lưu ảnh: ${shotPath}`);
  }

  // Lưu toàn bộ DOM sau khi đã render tất cả các tab
  const fullHtml = await page.content();
  const htmlPath = path.resolve(__dirname, 'english_tutor_full_rendered.html');
  fs.writeFileSync(htmlPath, fullHtml, 'utf8');
  console.log(`💾 Đã lưu full HTML tại: ${htmlPath}`);

  await browser.close();
  console.log('🎉 Hoàn thành xuất sắc việc cào full các trang English Tutor!');
}

captureAllPages().catch(err => {
  console.error('Lỗi:', err);
});

