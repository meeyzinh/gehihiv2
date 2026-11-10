const fs = require('fs');

let html = fs.readFileSync('english-tutor.html', 'utf8');
html = html.replace(/href=["']\/english-tutor/g, 'href="./english-tutor');
html = html.replace(/src=["']\/english-tutor/g, 'src="./english-tutor');

fs.writeFileSync('english-tutor.html', html, 'utf8');
console.log('✅ Updated relative paths in english-tutor.html successfully!');

