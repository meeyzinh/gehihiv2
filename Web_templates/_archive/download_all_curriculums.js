const fs = require('fs');
const path = require('path');

async function downloadCurriculums() {
  console.log('🔄 Đang lấy mã Captcha...');
  const capRes = await fetch('https://memory.gmbot.name.vn/api/captcha?t=' + Date.now());
  const capData = await capRes.json();
  const captchaId = capData.captchaId;
  const captchaCode = [...capData.svg.matchAll(/<text[^>]*>([^<]+)<\/text>/g)].map(m => m[1].trim()).join('');

  console.log(`🔐 Giải Captcha tự động thành công: [${captchaCode}]`);
  console.log('🔑 Đang đăng nhập tài khoản 330730...');

  const loginRes = await fetch('https://memory.gmbot.name.vn/api/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      username: '330730',
      password: '123456',
      captchaId,
      captchaCode
    })
  });

  const loginData = await loginRes.json();
  if (!loginRes.ok) {
    throw new Error('Đăng nhập thất bại: ' + JSON.stringify(loginData));
  }

  const token = loginData.token;
  console.log('✅ Đăng nhập thành công! Đã lấy JWT Token.');

  console.log('📥 Đang tải toàn bộ dữ liệu bài học từ /api/curriculums...');
  const curRes = await fetch('https://memory.gmbot.name.vn/api/curriculums', {
    headers: { 'Authorization': 'Bearer ' + token }
  });

  const curriculums = await curRes.json();
  console.log(`🎉 Đã lấy trọn vẹn toàn bộ ${curriculums.length} bài học!`);

  // Sort từ SP-01 đến SP-20
  curriculums.sort((a, b) => {
    return a.name.localeCompare(b.name, 'vi', { numeric: true, sensitivity: 'base' });
  });

  // 1. Lưu file JSON đầy đủ
  const jsonPath = path.resolve(__dirname, 'curriculums_full.json');
  fs.writeFileSync(jsonPath, JSON.stringify(curriculums, null, 2), 'utf-8');
  console.log(`💾 Đã lưu file JSON: ${jsonPath}`);

  // 2. Lưu file Markdown trình bày chi tiết
  const mdPath = path.resolve(__dirname, 'curriculums_full.md');
  let md = `# 📚 TOÀN BỘ DANH SÁCH BÀI HỌC GMBOT AI (TỔNG CỘNG ${curriculums.length} BÀI)\n\n`;
  md += `> Ngày trích xuất: ${new Date().toLocaleString('vi-VN')}\n`;
  md += `> Tài khoản: 330730\n\n---\n\n`;

  curriculums.forEach((c, idx) => {
    md += `## ${idx + 1}. ${c.name}\n\n`;
    md += `- **ID bài học:** \`${c.id}\`\n`;
    md += `- **Phân loại:** ${c.is_public ? '🌍 Public (Có sẵn)' : '👤 Cá nhân'}\n`;
    if (c.created_at) md += `- **Thời gian:** ${c.created_at}\n`;
    md += `\n### 📝 Kịch bản chi tiết & System Prompt của Robot:\n\n`;
    md += `\`\`\`text\n${c.content}\n\`\`\`\n\n`;
    md += `---\n\n`;
  });

  fs.writeFileSync(mdPath, md, 'utf-8');
  console.log(`📄 Đã lưu file Markdown: ${mdPath}`);

  return curriculums;
}

downloadCurriculums().catch(err => {
  console.error('Lỗi:', err);
});

