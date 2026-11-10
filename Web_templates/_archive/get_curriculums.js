const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const readline = require('readline');

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

(async () => {
  console.log('🚀 Đang khởi động Chromium...');
  const browser = await chromium.launch({
    headless: false,
    args: ['--start-maximized'],
  });

  const context = await browser.newContext({ viewport: null });
  const page = await context.newPage();

  console.log('🌐 Đang mở trang web: https://memory.gmbot.name.vn/');
  await page.goto('https://memory.gmbot.name.vn/', { waitUntil: 'domcontentloaded' });

  console.log('\n=============================================================');
  console.log('👉 Nếu trang yêu cầu đăng nhập, hãy đăng nhập trên trình duyệt.');
  console.log('👉 Khi đã ở trong trang chính, quay lại terminal này nhấn [ENTER].');
  console.log('=============================================================\n');

  await waitForEnter('Nhấn phím [ENTER] khi đã đăng nhập: ');

  console.log('⏳ Đang gọi API lấy danh sách toàn bộ bài học (curriculums)...');

  const curriculums = await page.evaluate(async () => {
    const token = localStorage.getItem('token');
    const res = await fetch('/api/curriculums', {
      headers: {
        'Authorization': 'Bearer ' + token
      }
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.error || 'Lỗi khi gọi API /api/curriculums');
    }
    return await res.json();
  });

  console.log(`✅ Lấy thành công ${curriculums.length} bài học!`);

  // Lưu file JSON
  const jsonPath = path.resolve(__dirname, 'curriculums_full.json');
  fs.writeFileSync(jsonPath, JSON.stringify(curriculums, null, 2), 'utf-8');
  console.log(`📁 Đã lưu file JSON tại: ${jsonPath}`);

  // Lưu thêm file Markdown dễ đọc
  const mdPath = path.resolve(__dirname, 'curriculums_full.md');
  let mdContent = `# DANH SÁCH BÀI HỌC GMBOT AI (Tổng số: ${curriculums.length} bài)\n\n`;
  curriculums.forEach((c, index) => {
    mdContent += `## ${index + 1}. ${c.name}\n`;
    mdContent += `- **ID:** \`${c.id}\`\n`;
    mdContent += `- **Loại:** ${c.is_public ? '🌍 Public' : '👤 Cá nhân'}\n`;
    mdContent += `- **Ngày tạo:** ${c.created_at || 'N/A'}\n\n`;
    mdContent += `### Nội dung chi tiết & Prompt hướng dẫn:\n\`\`\`\n${c.content}\n\`\`\`\n\n---\n\n`;
  });
  fs.writeFileSync(mdPath, mdContent, 'utf-8');
  console.log(`📄 Đã lưu file Markdown tại: ${mdPath}`);

  await browser.close();
  console.log('\n🎉 Hoàn thành xuất sắc!');
})();

