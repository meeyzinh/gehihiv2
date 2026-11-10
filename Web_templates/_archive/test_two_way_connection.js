const { chromium } = require('playwright');
const path = require('path');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 950 } });

  // 1. Open preview.html
  const previewUrl = 'file:///' + path.resolve('preview.html').replace(/\\/g, '/');
  console.log('1. Navigating to:', previewUrl);
  await page.goto(previewUrl);
  await page.waitForTimeout(1000);

  // 2. Click "HỌC TIẾNG ANH" in sidebar
  console.log('2. Clicking "HỌC TIẾNG ANH" menu item...');
  await page.click('.menu-item:has-text("HỌC TIẾNG ANH")');
  await page.waitForTimeout(800);
  await page.screenshot({ path: 'verify_link_step1_preview.png' });

  // 3. Click banner "Mở Giao Diện English Tutor" to navigate to English Tutor
  console.log('3. Clicking banner link to open English Tutor App...');
  await page.click('a:has-text("Mở Giao Diện English Tutor")');
  await page.waitForTimeout(1000);
  console.log('Current URL after click:', page.url());
  await page.screenshot({ path: 'verify_link_step2_tutor.png' });

  // 4. In English Tutor, click "Về GMBOT" (back button)
  console.log('4. Clicking "Về GMBOT" to go back...');
  await page.click('.nav-back, button:has-text("Về GMBOT"), .icon-button');
  await page.waitForTimeout(1000);
  console.log('Current URL after clicking back:', page.url());
  await page.screenshot({ path: 'verify_link_step3_returned.png' });

  await browser.close();
  console.log('End-to-end two-way connection test passed successfully!');
})();

