const fs = require('fs');
const html = fs.readFileSync('pages_extracted/xiaozhiConfigCard.html', 'utf8');

const query = 'Nhận dạng người nói';
let idx = 0;
while ((idx = html.indexOf(query, idx)) !== -1) {
  console.log(`=== FOUND AT ${idx} ===`);
  console.log(html.substring(idx - 100, idx + 1000));
  idx += query.length;
}

