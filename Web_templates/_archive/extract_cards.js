const fs = require('fs');
const path = require('path');

const html = fs.readFileSync('memory_page.html', 'utf8');

const list = [
  'deviceListCard',
  'addDeviceCard',
  'xiaozhiConfigCard',
  'englishTutorCard',
  'memoryCard',
  'taskCreateCard',
  'taskListCard',
  'curriculumSelectCard',
  'curriculumCreateCard',
  'photoLessonCard',
  'photoHomeworkCard',
  'knowledgeBaseCard',
  'wssRequestCard',
  'feedbackCard',
  'aiRoleSelectCard'
];

const outDir = path.resolve(__dirname, 'pages_extracted');
if (!fs.existsSync(outDir)) fs.mkdirSync(outDir, { recursive: true });

list.forEach(id => {
  const searchPattern = `id="${id}"`;
  const pos = html.indexOf(searchPattern);
  if (pos !== -1) {
    const cardStart = html.lastIndexOf('<div', pos);
    let depth = 0;
    let end = cardStart;
    for (let i = cardStart; i < html.length; i++) {
      if (html.slice(i, i + 4) === '<div') {
        depth++;
        i += 3;
      } else if (html.slice(i, i + 6) === '</div>') {
        depth--;
        if (depth === 0) {
          end = i + 6;
          break;
        }
        i += 5;
      }
    }
    const content = html.slice(cardStart, end);
    fs.writeFileSync(path.join(outDir, `${id}.html`), content, 'utf8');
    console.log(`Saved: ${id}.html (${content.length} bytes)`);
  } else {
    console.log(`Not found: ${id}`);
  }
});

