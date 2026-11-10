const fs = require('fs');
const html = fs.readFileSync('memory_page.html', 'utf8');

// Find sidebar element
const idxSidebar = html.indexOf('id="sidebar"');
console.log('Sidebar snippet:');
console.log(html.substring(idxSidebar - 50, idxSidebar + 1200));

// Find app element
const idxApp = html.indexOf('id="app"');
console.log('\nApp snippet:');
console.log(html.substring(idxApp - 50, idxApp + 1500));

