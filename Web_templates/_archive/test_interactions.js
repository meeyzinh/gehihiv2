const { chromium } = require('playwright');
const path = require('path');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 950 } });
  
  const fileUrl = 'file:///' + path.resolve('english-tutor-standalone.html').replace(/\\/g, '/');
  console.log('Navigating to:', fileUrl);
  await page.goto(fileUrl);
  await page.waitForTimeout(1000);
  
  // 1. Capture Hôm nay
  await page.screenshot({ path: 'verify_today.png' });
  
  // 2. Click Giáo trình
  await page.click('button[data-section="library"]');
  await page.waitForTimeout(600);
  await page.screenshot({ path: 'verify_library_lesson.png' });
  
  // 3. Click Nhập vai tab
  await page.click('#modeRoleplayButton');
  await page.waitForTimeout(600);
  await page.screenshot({ path: 'verify_library_roleplay.png' });

  // 4. Click a roleplay card (e.g. At the zoo)
  const cards = await page.$$('.template-card');
  console.log('Cards found in roleplay:', cards.length);
  if (cards.length > 0) {
    await cards[0].click();
    await page.waitForTimeout(400);
  }
  await page.screenshot({ path: 'verify_library_selected.png' });

  // 5. Switch back to Bài học
  await page.click('#modeLessonButton');
  await page.waitForTimeout(400);
  await page.screenshot({ path: 'verify_library_lesson_back.png' });

  // 6. Test Lộ trình
  await page.click('button[data-section="roadmap"]');
  await page.waitForTimeout(600);
  await page.screenshot({ path: 'verify_roadmap.png' });

  // 7. Test Tự tạo bài & Điền bài mẫu
  await page.click('button[data-section="create"]');
  await page.waitForTimeout(600);
  await page.click('button:has-text("Điền bài mẫu")');
  await page.waitForTimeout(400);
  await page.screenshot({ path: 'verify_create_filled.png' });

  // 8. Test Báo cáo
  await page.click('button[data-section="report"]');
  await page.waitForTimeout(600);
  await page.screenshot({ path: 'verify_report.png' });

  await browser.close();
  console.log('All tabs verified and captured successfully!');
})();

