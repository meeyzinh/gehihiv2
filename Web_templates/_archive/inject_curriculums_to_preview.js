const fs = require('fs');

let previewHtml = fs.readFileSync('preview.html', 'utf8');
const curriculums = JSON.parse(fs.readFileSync('curriculums_full.json', 'utf8'));

// Embed the real curriculums data and dynamic renderer into preview.html
const injectionScript = `
  <!-- DỮ LIỆU THỰC TẾ 20 BÀI HỌC -->
  <script>
    const REAL_CURRICULUMS = ${JSON.stringify(curriculums)};

    function renderCurriculumPage() {
      const publicBox = document.getElementById('publicCurriculumList');
      const detailCard = document.getElementById('curriculumDetailCard');
      const detailBox = document.getElementById('curriculumDetail');
      if (!publicBox) return;

      publicBox.innerHTML = '';
      REAL_CURRICULUMS.forEach((c, idx) => {
        const item = document.createElement('div');
        item.className = 'curriculum-item' + (idx === 0 ? ' selected' : '');
        item.style.padding = '10px 12px';
        item.style.marginBottom = '6px';
        item.style.borderRadius = '8px';
        item.style.cursor = 'pointer';
        item.style.background = idx === 0 ? '#2563eb' : '#0f2140';
        item.style.fontSize = '14px';
        item.style.fontWeight = '600';
        item.style.transition = 'all 0.15s';
        item.innerText = c.name;

        item.onmouseenter = () => {
          if (!item.classList.contains('selected')) item.style.background = '#1a3a6b';
        };
        item.onmouseleave = () => {
          if (!item.classList.contains('selected')) item.style.background = '#0f2140';
        };

        item.onclick = () => {
          document.querySelectorAll('.curriculum-item').forEach(el => {
            el.classList.remove('selected');
            el.style.background = '#0f2140';
          });
          item.classList.add('selected');
          item.style.background = '#2563eb';
          showCurriculumDetailInPreview(c);
        };

        publicBox.appendChild(item);
      });

      // Hiển thị bài đầu tiên mặc định
      if (REAL_CURRICULUMS.length > 0) {
        showCurriculumDetailInPreview(REAL_CURRICULUMS[0]);
      }
    }

    function showCurriculumDetailInPreview(c) {
      const detailCard = document.getElementById('curriculumDetailCard');
      const detailBox = document.getElementById('curriculumDetail');
      if (!detailBox) return;
      if (detailCard) detailCard.style.display = 'block';

      detailBox.innerHTML = \`
        <div style="background:#0f2140; padding:16px; border-radius:10px; border:1px solid rgba(37,99,235,0.3);">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
            <strong style="font-size:17px; color:white;">\${c.name}</strong>
            <span style="font-size:11px; background:#16a34a; color:white; padding:2px 8px; border-radius:20px; font-weight:bold;">
              \${c.is_public ? '🌍 Public' : '👤 Cá nhân'}
            </span>
          </div>

          <div style="margin-top:12px; white-space:pre-line; font-size:13px; line-height:1.6; color:#e2e8f0; background:#07152b; padding:12px; border-radius:8px; border:1px solid rgba(255,255,255,0.08); max-height:480px; overflow-y:auto;">
            \${c.content}
          </div>

          <div style="margin-top:14px;">
            <button class="primary" onclick="alert('Đã áp dụng bài học: ' + '\${c.name}')" style="width:100%; padding:10px; font-weight:bold; font-size:14px; border-radius:8px; background:#2563eb; color:white; border:none; cursor:pointer;">
              Áp dụng bài học
            </button>
          </div>
        </div>
      \`;
    }

    // Hook vào switchSection
    const originalSwitchSection = window.switchSection;
    window.switchSection = function(sectionId, el) {
      originalSwitchSection(sectionId, el);
      if (sectionId === 'curriculumSelect') {
        renderCurriculumPage();
      }
    };
  </script>
</body>
`;

previewHtml = previewHtml.replace('</body>', injectionScript);
fs.writeFileSync('preview.html', previewHtml, 'utf8');
console.log('✅ Injected real curriculum data into preview.html!');

