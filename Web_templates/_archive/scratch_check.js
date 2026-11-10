const fs = require('fs');
const html = fs.readFileSync('memory_page.html', 'utf8');

// Find memoryList and device functions
const searchStrings = ['renderMemory', 'renderDevices', 'memory-item', 'device-item', 'loadMemories'];
for (const s of searchStrings) {
  const pos = html.indexOf(s);
  if (pos !== -1) {
    console.log(`=== FOUND: ${s} ===`);
    console.log(html.substring(pos, pos + 700));
  }
}

