const fs = require('fs');
const html = fs.readFileSync('memory_page.html', 'utf8');

const idx = html.indexOf('localStorage.setItem("token"');
if (idx !== -1) {
  console.log(html.substring(idx - 300, idx + 200));
}

