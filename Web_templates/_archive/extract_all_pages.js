const fs = require('fs');

const html = fs.readFileSync('memory_page.html', 'utf8');

const cards = [
  { id: 'xiaozhiConfigCard', name: 'Cấu hình GMbot AI' },
  { id: 'englishTutorCard', name: 'Học tiếng Anh (Card)' },
  { id: 'memoryCard', name: 'Bộ nhớ' },
  { id: 'taskCreateCard', name: 'Tạo nhiệm vụ' },
  { id: 'taskListCard', name: 'Danh sách nhiệm vụ' },
  { id: 'curriculumSelectCard', name: 'Chọn Bài học' },
  { id: 'curriculumCreateCard', name: 'Tự tạo bài học' },
  { id: 'photoLessonCard', name: 'Chụp ảnh tạo bài học' },
  { id: 'photoHomeworkCard', name: 'Chụp ảnh giải bài tập' },
  { id: 'knowledgeBaseCard', name: 'Cơ sở tri thức' },
  { id: 'wssRequestCard', name: 'Yêu cầu kết nối Home Assistant' },
  { id: 'feedbackCard', name: 'Góp ý - Báo lỗi' },
  { id: 'aiRoleSelectCard', name: 'Chọn vai trò cho AI' },
  { id: 'customRoleCard', name: 'Tự tạo vai trò AI' }
];

cards.forEach(c => {
  const startTag = `id="${c.id}"`;
  const idx = html.indexOf(startTag);
  if (idx !== -1) {
    // Find the opening <div
    const divStart = html.lastIndexOf('<div', idx);
    // Find matching content roughly (first 500 chars)
    console.log(`\n================== [${c.name} (${c.id})] ==================`);
    console.log(html.substring(divStart, divStart + 600).replace(/\s+/g, ' ').slice(0, 300));
  } else {
    console.log(`\n❌ NOT FOUND: ${c.name} (${c.id})`);
  }
});

