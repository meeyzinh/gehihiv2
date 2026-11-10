const fs = require('fs');

const rawHtml = fs.readFileSync('english-tutor.html', 'utf8');
const rawCss = fs.readFileSync('english-tutor.css', 'utf8');
const reportCss = fs.readFileSync('english-tutor-parent-report.css', 'utf8');
const roadmapJs = fs.readFileSync('english-tutor-starter-roadmap.js', 'utf8');
let parentReportJs = fs.readFileSync('english-tutor-parent-report.js', 'utf8');
let tutorJs = fs.readFileSync('english-tutor.js', 'utf8');
const fullState = JSON.parse(fs.readFileSync('english_tutor_full_state.json', 'utf8'));

// Patch parentReportJs requestReport
parentReportJs = parentReportJs.replace(
  /async function requestReport\(url\) \{[\s\S]*?return response\.json\(\);\s*\}/,
  `async function requestReport(url) {
    console.log('[Offline Parent Report]', url);
    const offline = window.__OFFLINE_STATE__ || {};
    return offline.report || {
      profile: { known_words: [], weak_words: [], weak_phrases: [], streak_days: 0 },
      stats: { total_sessions: 0, completed_sessions: 0, abandoned_sessions: 0, started_sessions: 0, total_seconds: 0, avg_score: 0 },
      sessions: []
    };
  }`
);

// Patch tutorJs login check
tutorJs = tutorJs.replace(
  /if \(!state\.token\) \{[\s\S]*?return;\s*\}/,
  `if (!state.token) {
    state.token = "mock_tutor_token_330730";
  }
  state.user = { username: "330730", role: "user" };`
);

// Patch tutorJs apiFetch
tutorJs = tutorJs.replace(
  /async function apiFetch\(url, options = \{\}\) \{[\s\S]*?const data = await response\.json\(\)\.catch\(\(\) => \(\{\}\)\);/,
  `async function apiFetch(url, options = {}) {
    const offline = window.__OFFLINE_STATE__ || {};
    console.log('[API Call]', url, options.method || 'GET');

    await new Promise(r => setTimeout(r, 100));

    if (url.includes('/api/devices')) {
      return offline.devices || [{ id: 'endpoint-1788747076580-giosy', name: '330730', status: 'connected' }];
    }
    if (url.includes('/api/english-tutor/report')) {
      return offline.report || {};
    }
    if (url.includes('/api/english-tutor/active')) {
      return offline.active || {};
    }
    if (url.includes('/api/english-tutor/recommendation')) {
      return offline.recommendation || {};
    }
    if (url.includes('/api/english-tutor/templates')) {
      if (url.includes('mode=roleplay')) {
        return { templates: offline.roleplayTemplates || [] };
      }
      return { templates: offline.lessonTemplates || [] };
    }
    if (url.includes('/api/english-tutor/activate-template') || url.includes('/api/english-tutor/activate')) {
      let body = {};
      try { body = typeof options.body === 'string' ? JSON.parse(options.body) : options.body; } catch(e){}
      
      let title = body.title;
      let words = body.targetWords || '';
      let phrases = body.targetPhrases || '';
      let note = body.note || '';

      if (body.templateId) {
        const t = (offline.lessonTemplates || []).concat(offline.roleplayTemplates || []).find(item => item.id === body.templateId);
        if (t) {
          title = t.title;
          words = (t.target_words || []).join(', ');
          phrases = (t.target_phrases || []).join('\\n');
          note = t.tutor_note || t.scenario || '';
        }
      }

      offline.active = {
        activeId: 'active-' + Date.now(),
        title: title || 'Bài học tiếng Anh',
        content: '[ENGLISH_TUTOR][' + Date.now() + '] Tiêu đề: ' + (title || 'Bài học tiếng Anh') + '\\nTrình độ: ' + (body.level || 'starter') + '\\nChủ đề: ' + (body.topic || 'General') + '\\n\\nTừ mục tiêu:\\n' + (words.split(',').map(w => '- ' + w.trim()).join('\\n')) + '\\n\\nCâu mục tiêu:\\n' + (phrases.split('\\n').map(p => '- ' + p.trim()).join('\\n')) + '\\n\\nGhi chú cho gia sư:\\n' + note,
        createdAt: new Date().toISOString()
      };
      offline.recommendation = {
        success: true,
        type: 'active',
        title: title || 'Bài học tiếng Anh',
        reason: 'Robot đang có một bài học chưa kết thúc. Hãy gọi Sophia để tiếp tục bài này.',
        estimatedMinutes: 10,
        level: body.level || 'starter',
        topic: body.topic || 'General',
        mode: body.mode || 'lesson',
        activeId: offline.active.activeId,
        createdAt: offline.active.createdAt
      };
      return { success: true, activeId: offline.active.activeId };
    }
    if (url.includes('/api/english-tutor/deactivate')) {
      offline.active = null;
      offline.recommendation = {
        success: true,
        type: 'empty',
        title: 'Chưa có bài học',
        reason: 'Hãy chọn một bài trong thư viện hoặc lộ trình để bắt đầu.'
      };
      return { success: true };
    }
    if (url.includes('/api/english-tutor/quick-review')) {
      offline.active = {
        activeId: 'review-' + Date.now(),
        title: '⚡ Ôn nhanh 5 phút',
        content: '[ENGLISH_TUTOR][' + Date.now() + '] Tiêu đề: Ôn tập nhanh điểm yếu\\nThời lượng: 5 phút',
        createdAt: new Date().toISOString()
      };
      return { success: true, activeLesson: offline.active };
    }

    const data = {};`
);

tutorJs = tutorJs.replace(
  /throw new Error\("Phiên đăng nhập đã hết hạn\."\);/,
  `return {};`
);

// Auto select template and detail view
tutorJs = tutorJs.replace(
  /function selectTemplate\(templateId\) \{[\s\S]*?renderTemplateLibrary\(\);\s*\}/,
  `function selectTemplate(templateId) {
    state.selectedTemplateId = templateId;
    renderTemplateLibrary();
    if (window.innerWidth < 800) {
      document.getElementById("templateDetail")?.scrollIntoView({ behavior: 'smooth' });
    }
}`
);

// Prepare full master HTML
let masterHtml = rawHtml;
masterHtml = masterHtml.replace(/<link[^>]*rel="stylesheet"[^>]*>/gi, '');
masterHtml = masterHtml.replace(/<script[^>]*src="[^"]*"[^>]*><\/script>/gi, '');

const masterCss = `
<style>
${rawCss}
${reportCss}

/* Custom interactive tweaks */
.template-card {
  cursor: pointer;
  transition: all 0.2s ease;
}
.template-card:hover {
  transform: translateY(-2px);
  border-color: #2563eb !important;
  box-shadow: 0 8px 24px rgba(37, 99, 235, 0.2);
}
.template-card.active {
  border-color: #3b82f6 !important;
  background: rgba(37, 99, 235, 0.16) !important;
  box-shadow: 0 0 0 2px #2563eb, 0 10px 25px rgba(37, 99, 235, 0.25);
}
.template-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}
.library-layout {
  display: grid;
  grid-template-columns: 1fr 380px;
  gap: 24px;
  align-items: start;
}
@media (max-width: 1024px) {
  .library-layout {
    grid-template-columns: 1fr;
  }
}
.detail-card {
  position: sticky;
  top: 80px;
  background: #0f244a;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
}
</style>
`;

masterHtml = masterHtml.replace('</head>', `${masterCss}\n</head>`);

const bundleScripts = `
<script>
window.__OFFLINE_STATE__ = ${JSON.stringify(fullState, null, 2)};
</script>
<script>
${roadmapJs}
</script>
<script>
${parentReportJs}
</script>
<script>
${tutorJs}
</script>
<script>
// Auto select the first template once library renders if none selected
const origRenderLibrary = window.renderTemplateLibrary;
window.renderTemplateLibrary = function() {
  origRenderLibrary();
  if (!state.selectedTemplateId) {
    const source = state.libraryMode === 'roleplay' ? state.roleplayTemplates : state.lessonTemplates;
    if (source && source.length > 0) {
      selectTemplate(source[0].id);
    }
  }
};
</script>
`;

masterHtml = masterHtml.replace('</body>', `${bundleScripts}\n</body>`);

fs.writeFileSync('english-tutor-standalone.html', masterHtml, 'utf8');
console.log('Successfully written english-tutor-standalone.html with size:', fs.statSync('english-tutor-standalone.html').size);

