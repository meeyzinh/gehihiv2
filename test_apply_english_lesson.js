const { chromium } = require('./Web_templates/node_modules/playwright');
const path = require('path');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1400, height: 900 } });
  const page = await context.newPage();

  console.log('1. Navigating to http://localhost:8000...');
  await page.goto('http://localhost:8000', { waitUntil: 'networkidle' });
  await page.waitForTimeout(1000);

  console.log('2. Clicking "HỌC TIẾNG ANH" tab...');
  await page.click('.sidebar .menu-item:has-text("HỌC TIẾNG ANH")');
  await page.waitForTimeout(800);

  console.log('3. Selecting lesson "Daily Routine - Bài 1: My day"...');
  await page.click('.curriculum-item:has-text("Daily Routine - Bài 1: My day")');
  await page.waitForTimeout(600);

  console.log('4. Clicking "🚀 Áp dụng kịch bản bài học này vào Robot"...');
  await page.click('#btnApplyEnglish');
  await page.waitForTimeout(2000);

  const btnText = await page.locator('#btnApplyEnglish').innerText();
  console.log('5. Button text after click:', btnText);

  const toastVisible = await page.locator('#toastMessage').isVisible();
  const toastText = await page.locator('#toastMessage').innerText();
  console.log('6. Toast message:', toastText, '(visible:', toastVisible, ')');

  const screenshotPath = path.join(__dirname, 'screenshots_test', 'english_applied_success.png');
  await page.screenshot({ path: screenshotPath });
  console.log('7. Saved screenshot to:', screenshotPath);

  await browser.close();
})();
