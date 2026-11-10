const fs = require('fs');

function updateFiles() {
  const templates = JSON.parse(fs.readFileSync('all_english_templates.json', 'utf8'));
  const lessons = templates.lessons || [];
  const roleplay = templates.roleplay || [];

  // 1. UPDATE preview.html
  let previewHtml = fs.readFileSync('preview.html', 'utf8');

  // Insert banner inside englishTutorCard
  const banner = `
    <!-- BANNER KẾT NỐI SANG ỨNG DỤNG GMBOT ENGLISH TUTOR -->
    <div style="background: linear-gradient(135deg, #1e3a8a, #2563eb); border-radius: 12px; padding: 16px 20px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 4px 16px rgba(37,99,235,0.3); border: 1px solid rgba(255,255,255,0.15);">
      <div>
        <div style="font-size: 16px; font-weight: bold; color: #ffffff; display: flex; align-items: center; gap: 8px;">
          🚀 <span>Ứng dụng chuyên sâu: GMBOT English Tutor</span>
          <span style="font-size: 11px; background: rgba(255,255,255,0.25); padding: 2px 8px; border-radius: 20px; color: #fff;">Full Features</span>
        </div>
        <div style="font-size: 13px; color: #dbeafe; margin-top: 4px;">
          Đầy đủ 5 phân hệ: Hôm nay, Lộ trình 50 bài, Giáo trình & Nhập vai, Tự tạo bài giảng, Báo cáo học tập.
        </div>
      </div>
      <a href="english-tutor-app.html" style="display: inline-flex; align-items: center; gap: 6px; background: #ffffff; color: #1e3a8a; font-weight: bold; padding: 10px 18px; border-radius: 8px; text-decoration: none; font-size: 13px; box-shadow: 0 2px 8px rgba(0,0,0,0.15); transition: transform 0.2s; white-space: nowrap;">
        Mở Giao Diện English Tutor ↗
      </a>
    </div>
  `;

  if (!previewHtml.includes('GMBOT English Tutor')) {
    previewHtml = previewHtml.replace('<div class="card" id="englishTutorCard" style="display:none;">', '<div class="card" id="englishTutorCard" style="display:none;">\n' + banner);
  }

  // Update sidebar menu item to also have an open button or shortcut
  previewHtml = previewHtml.replace(
    '<div class="menu-item" onclick="switchSection(\'englishTutor\', this)">📚 HỌC TIẾNG ANH</div>',
    '<div class="menu-item" onclick="switchSection(\'englishTutor\', this)">📚 HỌC TIẾNG ANH</div>\n      <div class="menu-item" onclick="window.location.href=\'english-tutor-app.html\'" style="font-size:12px; color:#60a5fa; padding-left:28px;">↳ Mở English Tutor App ↗</div>'
  );

  // Add the script for preview.html to populate English Tutor list & details
  const previewScript = `
  <script>
    // Dữ liệu và tương tác Học tiếng Anh trong preview.html
    const PREVIEW_LESSONS = ${JSON.stringify(lessons)};
    const PREVIEW_ROLEPLAY = ${JSON.stringify(roleplay)};
    let currentPreviewTutorId = PREVIEW_LESSONS[0] ? PREVIEW_LESSONS[0].id : null;
    let previewTutorBoxState = { lesson: true, roleplay: false };

    function renderPreviewEnglishTemplates() {
      const level = document.getElementById('englishTemplateLevel') ? document.getElementById('englishTemplateLevel').value : '';
      
      const lessonBox = document.getElementById('englishLessonTemplateList');
      const roleplayBox = document.getElementById('englishRoleplayTemplateList');
      if (!lessonBox || !roleplayBox) return;

      const filteredLessons = PREVIEW_LESSONS.filter(t => !level || (t.level || '').toLowerCase() === level.toLowerCase());
      const filteredRoleplay = PREVIEW_ROLEPLAY.filter(t => !level || (t.level || '').toLowerCase() === level.toLowerCase());

      // Render lessons
      lessonBox.innerHTML = filteredLessons.map(t => {
        const isActive = t.id === currentPreviewTutorId;
        return \`
          <div class="curriculum-item \${isActive ? 'active' : ''}" onclick="selectPreviewTemplate('\${t.id}', 'lesson')">
            <div style="display:flex; justify-content:space-between; align-items:center; gap:8px;">
              <span style="flex:1; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">📘 \${t.title}</span>
              \${isActive ? '<span style="color:#4ade80; font-size:11px;">✔ Đang xem</span>' : ''}
            </div>
          </div>
        \`;
      }).join('');

      // Render roleplay
      roleplayBox.innerHTML = filteredRoleplay.map(t => {
        const isActive = t.id === currentPreviewTutorId;
        return \`
          <div class="curriculum-item \${isActive ? 'active' : ''}" onclick="selectPreviewTemplate('\${t.id}', 'roleplay')">
            <div style="display:flex; justify-content:space-between; align-items:center; gap:8px;">
              <span style="flex:1; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">🎭 \${t.title}</span>
              \${isActive ? '<span style="color:#4ade80; font-size:11px;">✔ Đang xem</span>' : ''}
            </div>
          </div>
        \`;
      }).join('');

      // Headers count
      const lessonH = document.querySelector('[onclick*="toggleEnglishTemplateBox(\\'lesson\\')"] span:first-child');
      if (lessonH) lessonH.innerText = '📚 Giáo trình có sẵn (' + filteredLessons.length + ')';
      const roleplayH = document.querySelector('[onclick*="toggleEnglishTemplateBox(\\'roleplay\\')"] span:first-child');
      if (roleplayH) roleplayH.innerText = '🎭 Tình huống nhập vai (' + filteredRoleplay.length + ')';

      // Update box open/close classes
      lessonBox.classList.toggle('open', previewTutorBoxState.lesson);
      roleplayBox.classList.toggle('open', previewTutorBoxState.roleplay);
      const iconL = document.getElementById('icon-english-lesson');
      if (iconL) iconL.style.transform = previewTutorBoxState.lesson ? 'rotate(90deg)' : '';
      const iconR = document.getElementById('icon-english-roleplay');
      if (iconR) iconR.style.transform = previewTutorBoxState.roleplay ? 'rotate(90deg)' : '';
    }

    function toggleEnglishTemplateBox(type) {
      previewTutorBoxState[type] = !previewTutorBoxState[type];
      const box = document.getElementById(type === 'lesson' ? 'englishLessonTemplateList' : 'englishRoleplayTemplateList');
      const icon = document.getElementById(type === 'lesson' ? 'icon-english-lesson' : 'icon-english-roleplay');
      if (box) box.classList.toggle('open', previewTutorBoxState[type]);
      if (icon) icon.style.transform = previewTutorBoxState[type] ? 'rotate(90deg)' : '';
    }

    function onEnglishTemplateLevelChange() {
      renderPreviewEnglishTemplates();
    }

    function selectPreviewTemplate(id, type) {
      currentPreviewTutorId = id;
      const all = PREVIEW_LESSONS.concat(PREVIEW_ROLEPLAY);
      const item = all.find(x => x.id === id);
      if (item) {
        showPreviewTemplateDetail(item, type);
      }
      renderPreviewEnglishTemplates();
    }

    function showPreviewTemplateDetail(t, type) {
      const container = document.getElementById('englishTemplateDetail');
      if (!container) return;

      const words = Array.isArray(t.target_words) ? t.target_words : [];
      const phrases = Array.isArray(t.target_phrases) ? t.target_phrases : [];
      const isRoleplay = type === 'roleplay' || t.mode === 'roleplay';

      container.innerHTML = \`
        <div style="background:#0f2140; padding:16px; border-radius:10px; border:1px solid rgba(37,99,235,0.3);">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
            <strong style="font-size:16px; color:white;">\${isRoleplay ? '🎭' : '📚'} \${t.title}</strong>
            <span style="font-size:11px; background:#2563eb; color:white; padding:2px 8px; border-radius:20px; font-weight:bold;">
              \${(t.level || 'starter').toUpperCase()}
            </span>
          </div>
          <div style="font-size:12px; color:#94a3b8; margin-bottom:12px;">
            Chủ đề: <strong style="color:#e2e8f0;">\${t.topic || 'General'}</strong> · Chế độ: <strong style="color:#e2e8f0;">\${isRoleplay ? 'Nhập vai luyện nói' : 'Bài học'}</strong>
          </div>

          \${t.scenario ? \`
            <div style="margin-bottom:12px; padding:10px; border-radius:8px; background:rgba(168,85,247,0.15); border:1px solid rgba(216,180,254,0.2); font-size:13px; line-height:1.5;">
              <strong style="color:#d8b4fe;">🎭 Tình huống:</strong><br>\${t.scenario}
            </div>
          \` : ''}

          <div style="margin-bottom:12px; font-size:13px; line-height:1.6; background:#07152b; padding:12px; border-radius:8px;">
            <div style="font-weight:bold; color:#60a5fa; margin-bottom:4px;">🎯 Từ mục tiêu:</div>
            <div>\${words.length ? words.map(w => '<span style="display:inline-block; background:rgba(59,130,246,0.2); color:#93c5fd; padding:2px 8px; border-radius:12px; margin:2px 4px 2px 0;">' + w + '</span>').join('') : 'Không có'}</div>

            <div style="font-weight:bold; color:#60a5fa; margin-top:10px; margin-bottom:4px;">💬 Câu luyện nói:</div>
            <div>\${phrases.length ? phrases.map(p => '<div style="color:#e2e8f0;">• ' + p + '</div>').join('') : 'Không có'}</div>
          </div>

          \${t.tutor_note ? \`
            <div style="margin-bottom:14px; padding:10px; border-radius:8px; background:rgba(59,130,246,0.12); border:1px solid rgba(96,165,250,0.2); font-size:12px; line-height:1.5; color:#cbd5e1;">
              <strong style="color:#93c5fd;">📝 Ghi chú gia sư:</strong><br>\${t.tutor_note}
            </div>
          \` : ''}

          <div style="display:flex; gap:10px;">
            <button class="primary" onclick="alert('Đã áp dụng bài học: ' + '\${t.title}');" style="flex:1; padding:10px; font-weight:bold; border-radius:8px; background:#2563eb; color:white; border:none; cursor:pointer;">
              🚀 Áp dụng bài này
            </button>
            <a href="english-tutor-app.html" style="display:inline-flex; align-items:center; justify-content:center; padding:10px 14px; font-weight:bold; font-size:12px; border-radius:8px; background:#1e293b; color:#93c5fd; border:1px solid rgba(147,197,253,0.3); text-decoration:none;">
              Mở App Full ↗
            </a>
          </div>
        </div>
      \`;
    }

    // Hook vào render khi vào tab englishTutor
    const prevHookSwitch = window.switchSection;
    window.switchSection = function(sectionId, el) {
      prevHookSwitch(sectionId, el);
      if (sectionId === 'englishTutor') {
        renderPreviewEnglishTemplates();
        if (PREVIEW_LESSONS.length > 0) {
          selectPreviewTemplate(PREVIEW_LESSONS[0].id, 'lesson');
        }
      }
    };
  </script>
  `;

  previewHtml = previewHtml.replace('</body>', previewScript + '\n</body>');
  fs.writeFileSync('preview.html', previewHtml, 'utf8');
  fs.writeFileSync('index.html', previewHtml, 'utf8');
  console.log('preview.html & index.html successfully updated!');

  // 2. UPDATE english-tutor-standalone.html & english-tutor-app.html
  let appHtml = fs.readFileSync('english-tutor-standalone.html', 'utf8');

  // Add click handler to goBackToDashboard to return to preview.html or window.history.back()
  appHtml = appHtml.replace(
    /function goBackToDashboard\(\) \{[\s\S]*?\}/,
    `function goBackToDashboard() {
      if (window.history.length > 1 && document.referrer) {
        window.history.back();
      } else {
        window.location.href = 'preview.html';
      }
    }`
  );

  // Ensure button back has explicit link fallbacks
  appHtml = appHtml.replace(
    /<button class="icon-button" type="button" onclick="goBackToDashboard\(\)" aria-label="Quay lại trung tâm quản lý">←<\/button>/g,
    `<button class="icon-button" type="button" onclick="goBackToDashboard()" title="Quay về Trung tâm GMBOT AI" aria-label="Quay lại trung tâm quản lý">←</button>`
  );

  appHtml = appHtml.replace(
    /<button class="nav-item nav-back" onclick="goBackToDashboard\(\)">/g,
    `<button class="nav-item nav-back" onclick="goBackToDashboard()" title="Quay về Trung tâm GMBOT AI">`
  );

  fs.writeFileSync('english-tutor-standalone.html', appHtml, 'utf8');
  fs.writeFileSync('english-tutor-app.html', appHtml, 'utf8');
  fs.writeFileSync('english-tutor.html', appHtml, 'utf8');
  console.log('english-tutor-standalone.html, english-tutor-app.html & english-tutor.html updated with 2-way navigation!');
}

updateFiles();

