const fs = require('fs');
const path = require('path');

const originalHtml = fs.readFileSync('memory_page.html', 'utf8');

// Extract the CSS from memory_page.html
const styleMatch = originalHtml.match(/<style[^>]*>([\s\S]*?)<\/style>/i);
const originalCss = styleMatch ? styleMatch[1] : '';

// Read extracted cards
const cardFiles = fs.readdirSync('pages_extracted');
const cardsHtml = cardFiles.map(file => {
  return fs.readFileSync(path.join('pages_extracted', file), 'utf8');
}).join('\n\n');

// Build the full interactive HTML
const fullHtml = `<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>TRUNG TÂM QUẢN LÝ GMBOT AI - Đầy đủ tất cả các trang Menu</title>
  <style>
${originalCss}

/* Fine-tuning for preview */
body {
  display: flex;
  min-height: 100vh;
  margin: 0;
  background: #0b1f3d;
  color: white;
  font-family: 'Segoe UI', system-ui, sans-serif;
}

.main-content {
  flex: 1;
  margin-left: 240px;
  padding: 20px;
  box-sizing: border-box;
  min-width: 0;
}

@media (max-width: 768px) {
  .main-content {
    margin-left: 0;
    padding: 12px;
  }
}

.sidebar .menu-item {
  cursor: pointer;
  user-select: none;
}

.sidebar .menu-item.active {
  background: #13294b;
  font-weight: bold;
}

.card {
  display: none; /* Controlled by tab switcher */
}

.card.active-card {
  display: block !important;
  animation: fadeIn 0.2s ease-in-out;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(4px); }
  to { opacity: 1; transform: translateY(0); }
}

.overlay {
  display: none;
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.6);
  z-index: 999;
}
.overlay.active {
  display: block;
}
  </style>
</head>
<body>

  <!-- Overlay Mobile -->
  <div id="overlay" class="overlay" onclick="toggleSidebar()"></div>

  <!-- SIDEBAR -->
  <div class="sidebar" id="sidebar">
    <div class="logo">
      <div style="font-size: 16px; font-weight: bold; padding-bottom: 8px;">GMBOT AI</div>
      <div class="user-box">
        <div class="user-name">Xin chào, 330730</div>
        <div class="user-device">330730</div>
        <div style="display:flex;align-items:center;gap:6px;font-size:12px;">
          <span class="status-dot connected"></span>
          <span style="color:#4ade80;">connected</span>
        </div>
        <div class="user-vip" style="margin-top: 4px;">
          <span class="badge vip-badge">👑 VIP</span>
          <span class="vip-timer">335d 18h 4m 51s</span>
        </div>
      </div>
    </div>

    <div class="menu">
      <div class="menu-item active" onclick="switchSection('devices', this)">📡 Thiết bị</div>
      <div class="menu-item" onclick="switchSection('xiaozhiConfig', this)">⚙️ Cấu hình GMbot AI</div>
      <div class="menu-item" onclick="switchSection('englishTutor', this)">📚 HỌC TIẾNG ANH</div>
      <div class="menu-item" onclick="switchSection('memory', this)">🧠 Bộ nhớ</div>
      <div class="menu-item" onclick="switchSection('tasks', this)">📗 Tạo nhiệm vụ</div>
      <div class="menu-item" onclick="switchSection('curriculumSelect', this)">📖 Chọn Bài học</div>
      <div class="menu-item" onclick="switchSection('curriculumCreate', this)">✍️ Tự tạo bài học</div>
      <div class="menu-item" onclick="switchSection('photoLesson', this)">📷 Chụp ảnh tạo bài học</div>
      <div class="menu-item" onclick="switchSection('photoHomework', this)">🎒 Chụp ảnh giải bài tập</div>
      <div class="menu-item" onclick="switchSection('knowledgeBase', this)">📗 Cơ sở tri thức</div>

      <div style="height: 1px; background: rgba(255,255,255,0.1); margin: 8px 0;"></div>

      <div class="menu-item" onclick="openPage('huong-dan.html')">⚙️ Hướng dẫn sử dụng ↗</div>
      <div class="menu-item" onclick="openPage('ha-mcp-guide.html')">🏠 Hướng dẫn kết nối Home Assistant ↗</div>
      <div class="menu-item" onclick="switchSection('wssRequest', this)">🔗 Yêu cầu kết nối Home Assistant</div>
      <div class="menu-item" onclick="switchSection('feedback', this)">💬 Góp ý - Báo lỗi</div>
    </div>

    <div style="margin-top: auto; padding-top: 15px; border-top: 1px solid rgba(255,255,255,0.1); font-size: 13px;">
      <div style="color: #9ca3af; margin-bottom: 6px;">Zalo: <strong style="color: #fbbf24;">0938.396.290</strong></div>
      <div style="color: #ef4444; font-weight: bold; cursor: pointer;">🚪 Đăng xuất</div>
    </div>
  </div>

  <!-- MAIN CONTENT -->
  <div class="main-content">
    <div class="topbar" style="margin-bottom: 16px;">
      <button class="menu-toggle" onclick="toggleSidebar()" style="background:#13294b; color:white; border:none; padding:8px 12px; border-radius:8px; cursor:pointer;">☰ Menu</button>
      <div style="font-size: 13px; color: #9ca3af; margin-left: 10px;">
        &lt;=== Bấm menu bên trái để chuyển qua lại giữa tất cả các trang
      </div>
    </div>

    <!-- CONTAINER TẤT CẢ CÁC TRANG CARD ĐƯỢC BÓC TÁCH -->
    <div id="cardsContainer">
${cardsHtml}
    </div>
  </div>

  <script>
    function toggleSidebar() {
      const sb = document.getElementById('sidebar');
      const ov = document.getElementById('overlay');
      sb.classList.toggle('active');
      ov.classList.toggle('active');
    }

    function openPage(url) {
      window.open(url, '_blank');
    }

    function switchSection(sectionId, el) {
      // Cập nhật menu active
      document.querySelectorAll('.sidebar .menu-item').forEach(m => m.classList.remove('active'));
      if (el) el.classList.add('active');

      // Ẩn tất cả cards
      document.querySelectorAll('#cardsContainer .card').forEach(c => {
        c.classList.remove('active-card');
        c.style.display = 'none';
      });

      // Hiện card tương ứng
      const targetMap = {
        'devices': ['addDeviceCard', 'deviceListCard'],
        'xiaozhiConfig': ['xiaozhiConfigCard'],
        'englishTutor': ['englishTutorCard'],
        'memory': ['memoryCard'],
        'tasks': ['taskCreateCard', 'taskListCard'],
        'curriculumSelect': ['curriculumSelectCard'],
        'curriculumCreate': ['curriculumCreateCard'],
        'photoLesson': ['photoLessonCard'],
        'photoHomework': ['photoHomeworkCard'],
        'knowledgeBase': ['knowledgeBaseCard'],
        'wssRequest': ['wssRequestCard'],
        'feedback': ['feedbackCard']
      };

      const targets = targetMap[sectionId] || [sectionId];
      targets.forEach(id => {
        const card = document.getElementById(id);
        if (card) {
          card.classList.add('active-card');
          card.style.display = 'block';
        }
      });

      // Tự đóng menu mobile nếu có
      if (window.innerWidth < 768) {
        toggleSidebar();
      }
    }

    // Mặc định hiển thị trang Thiết bị
    window.addEventListener('DOMContentLoaded', () => {
      switchSection('devices', document.querySelector('.sidebar .menu-item'));
    });
  </script>
</body>
</html>
`;

fs.writeFileSync('preview.html', fullHtml, 'utf8');
console.log('✅ Generated complete preview.html with all pages!');

