const fs = require('fs');
const html = fs.readFileSync('english-tutor.html', 'utf8');

console.log('File size:', html.length);
const titleMatch = html.match(/<title>([^<]+)<\/title>/i);
console.log('Title:', titleMatch ? titleMatch[1] : 'No title');

// Check external dependencies
const scripts = [...html.matchAll(/<script[^>]*src=["']([^"']+)["']/gi)].map(m => m[1]);
console.log('External scripts:', scripts);
const links = [...html.matchAll(/<link[^>]*href=["']([^"']+)["']/gi)].map(m => m[1]);
console.log('External links:', links);

