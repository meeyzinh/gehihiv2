const fs = require('fs');
const html = fs.readFileSync('english-tutor.html', 'utf8');

const matches = [...html.matchAll(/id="(section-[^"]+)"/g)].map(m => m[1]);
console.log('Sections:', matches);

// Check nav items
const navMatches = [...html.matchAll(/data-section="([^"]+)"/g)].map(m => m[1]);
console.log('Nav data-sections:', navMatches);

