const { chromium } = require('./Web_templates/node_modules/playwright');
const path = require('path');
const fs = require('fs');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1400, height: 900 } });
  const page = await context.newPage();

  const consoleErrors = [];
  page.on('console', msg => {
    if (msg.type() === 'error') {
      consoleErrors.push(msg.text());
    }
  });
  page.on('pageerror', err => {
    consoleErrors.push(err.message);
  });

  console.log('--- 1. Navigating to http://localhost:8000 ---');
  await page.goto('http://localhost:8000', { waitUntil: 'networkidle' });
  await page.waitForTimeout(1000);

  const outDir = path.join(__dirname, 'screenshots_test');
  if (!fs.existsSync(outDir)) fs.mkdirSync(outDir);

  const tabs = [
    { name: 'Cấu hình GMbot AI', selector: '.sidebar .menu-item:has-text("Cấu hình GMbot AI")', sectionId: 'tabXiaozhiConfig' },
    { name: 'Điều khiển D-Pad', selector: '.sidebar .menu-item:has-text("Điều khiển D-Pad")', sectionId: 'tabRemoteControl' },
    { name: 'HỌC TIẾNG ANH', selector: '.sidebar .menu-item:has-text("HỌC TIẾNG ANH")', sectionId: 'tabEnglishTutor' },
    { name: 'Chọn Bài học', selector: '.sidebar .menu-item:has-text("Chọn Bài học")', sectionId: 'tabCurriculums' },
    { name: 'Chọn vai trò GMbot', selector: '.sidebar .menu-item:has-text("Chọn vai trò GMbot")', sectionId: 'tabAiRoleSelect' },
    { name: 'Bộ nhớ', selector: '.sidebar .menu-item:has-text("Bộ nhớ")', sectionId: 'tabMemory' },
    { name: 'Tạo nhiệm vụ & MCP', selector: '.sidebar .menu-item:has-text("Tạo nhiệm vụ & MCP")', sectionId: 'tabTasksMcp' },
    { name: 'Quản lý Thiết bị', selector: '.sidebar .menu-item:has-text("Quản lý Thiết bị")', sectionId: 'tabDevicesManager' }
  ];

  for (const t of tabs) {
    console.log(`\nTesting Tab: [${t.name}]...`);
    const btn = page.locator(t.selector);
    await btn.click();
    await page.waitForTimeout(600);

    const isVisible = await page.locator(`#${t.sectionId}`).isVisible();
    const innerTextLength = (await page.locator(`#${t.sectionId}`).innerText()).length;
    console.log(`  -> Section #${t.sectionId} visible: ${isVisible}, Text length: ${innerTextLength} chars`);

    const imgPath = path.join(outDir, `${t.sectionId}.png`);
    await page.screenshot({ path: imgPath });
    console.log(`  -> Screenshot saved to ${imgPath}`);
  }

  console.log('\n--- Console Errors Check ---');
  if (consoleErrors.length === 0) {
    console.log('✅ PERFECT: 0 console errors during full page navigation and tab clicks!');
  } else {
    console.log(`❌ Found ${consoleErrors.length} console errors:`);
    consoleErrors.forEach(e => console.log('   - ' + e));
  }

  await browser.close();
})();
