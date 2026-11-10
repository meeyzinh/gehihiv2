const fs = require('fs');

const renderedHtml = fs.readFileSync('english_tutor_rendered.html', 'utf8');
const mainCss = fs.readFileSync('english-tutor.css', 'utf8');
const reportCss = fs.readFileSync('english-tutor-parent-report.css', 'utf8');

// Replace external CSS links with inlined style tags
let outputHtml = renderedHtml;

outputHtml = outputHtml.replace(
  /<link rel="stylesheet" href="\/english-tutor\.css[^"]*">/,
  `<style>\n/* === MAIN ENGLISH TUTOR CSS === */\n${mainCss}\n</style>`
);

outputHtml = outputHtml.replace(
  /<link rel="stylesheet" href="\/english-tutor-parent-report\.css[^"]*">/,
  `<style>\n/* === PARENT REPORT CSS === */\n${reportCss}\n</style>`
);

// Remove the external scripts that cause failed network calls on local file://
outputHtml = outputHtml.replace(/<script src="\/english-tutor-starter-roadmap\.js[^"]*"[^>]*><\/script>/, '');
outputHtml = outputHtml.replace(/<script src="\/english-tutor\.js[^"]*"[^>]*><\/script>/, '');

// Ensure #pageLoading is hidden and #app is displayed
outputHtml = outputHtml.replace('id="pageLoading" class="page-loading"', 'id="pageLoading" class="page-loading" style="display:none;" hidden');
outputHtml = outputHtml.replace('id="app" class="app-shell" hidden=""', 'id="app" class="app-shell"');
outputHtml = outputHtml.replace('id="app" class="app-shell" hidden', 'id="app" class="app-shell"');

// Add interactive navigation script
const clientScript = `
<script>
  function showEnglishSection(sectionId, btn) {
    document.querySelectorAll('.side-nav .nav-item').forEach(el => el.classList.remove('active'));
    if (btn) btn.classList.add('active');

    document.querySelectorAll('.content-section').forEach(sec => {
      sec.classList.remove('active');
    });

    const target = document.getElementById('section-' + sectionId);
    if (target) {
      target.classList.add('active');
    }
  }

  function goBackToDashboard() {
    window.location.href = 'preview.html';
  }

  function startRecommendedLesson() {
    alert('Bắt đầu bài học đề xuất: Greeting - Bài 1: Hello!');
  }

  // Toast auto-hide
  setTimeout(() => {
    const toast = document.querySelector('.toast');
    if (toast) toast.style.opacity = '0';
  }, 4000);
</script>
`;

outputHtml = outputHtml.replace('</body>', `${clientScript}\n</body>`);

fs.writeFileSync('english-tutor-app.html', outputHtml, 'utf8');
console.log('✅ Generated standalone english-tutor-app.html with embedded CSS and zero dependencies!');

