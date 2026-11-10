const fs = require('fs');

let html = fs.readFileSync('english_tutor_full_rendered.html', 'utf8');
const css1 = fs.readFileSync('english-tutor.css', 'utf8');
const css2 = fs.readFileSync('english-tutor-parent-report.css', 'utf8');

// Replace external stylesheets or insert them directly
const inlineStyles = `<style>
${css1}
${css2}
/* Extra styling to ensure clean layout & tab switching */
.hidden { display: none !important; }
.side-nav button.active {
  background: #2563eb !important;
  color: #ffffff !important;
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.4);
}
</style>`;

if (html.includes('</head>')) {
  html = html.replace('</head>', inlineStyles + '\n</head>');
} else {
  html = inlineStyles + '\n' + html;
}

const tabSwitcherScript = `
<script>
  function switchTab(sectionName) {
    const sections = ['today', 'roadmap', 'library', 'create', 'report'];
    sections.forEach(s => {
      const el = document.getElementById('section-' + s);
      if (el) {
        if (s === sectionName) {
          el.classList.remove('hidden');
          el.style.display = 'block';
        } else {
          el.classList.add('hidden');
          el.style.display = 'none';
        }
      }
    });

    document.querySelectorAll('.side-nav button, .nav-btn, [data-section]').forEach(btn => {
      const sec = btn.getAttribute('data-section');
      if (sec === sectionName) {
        btn.classList.add('active');
        btn.setAttribute('aria-selected', 'true');
      } else if (sec) {
        btn.classList.remove('active');
        btn.setAttribute('aria-selected', 'false');
      }
    });

    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  window.showEnglishSection = function(secId, btn) {
    const name = secId.replace('section-', '');
    switchTab(name);
  };

  document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.side-nav button, [data-section]').forEach(btn => {
      btn.addEventListener('click', function(e) {
        const sec = this.getAttribute('data-section');
        if (sec) {
          e.preventDefault();
          switchTab(sec);
        }
      });
    });

    // Default to 'today' tab
    switchTab('today');
  });
</script>
`;

if (html.includes('</body>')) {
  html = html.replace('</body>', tabSwitcherScript + '\n</body>');
} else {
  html += tabSwitcherScript;
}

fs.writeFileSync('english-tutor-all-pages.html', html, 'utf8');
console.log('Successfully created english-tutor-all-pages.html! File size:', fs.statSync('english-tutor-all-pages.html').size);

