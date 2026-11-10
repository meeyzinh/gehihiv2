const fs = require('fs');

const html = fs.readFileSync('memory_page.html', 'utf8');

// 1. Extract CSS
const styleMatch = html.match(/<style[^>]*>([\s\S]*?)<\/style>/i);
const css = styleMatch ? styleMatch[1] : '';

// 2. Extract Colors
const hexColors = [...new Set(css.match(/#[0-9a-fA-F]{3,8}\b/g) || [])];
const rgbColors = [...new Set(css.match(/rgba?\([^)]+\)/g) || [])];

// 3. Extract Font families and typography
const fontFamilies = [...new Set(css.match(/font-family:[^;]+;/gi) || [])];
const fontSizes = [...new Set(css.match(/font-size:[^;]+;/gi) || [])];
const lineHeights = [...new Set(css.match(/line-height:[^;]+;/gi) || [])];

// 4. Extract visual effects
const borderRadii = [...new Set(css.match(/border-radius:[^;]+;/gi) || [])];
const boxShadows = [...new Set(css.match(/box-shadow:[^;]+;/gi) || [])];
const backgrounds = [...new Set(css.match(/background(?:-color)?:[^;]+;/gi) || [])];

console.log('=== COLORS ===');
console.log('HEX:', hexColors);
console.log('RGB:', rgbColors.slice(0, 10));

console.log('\n=== TYPOGRAPHY ===');
console.log('Font Families:', fontFamilies);
console.log('Font Sizes:', fontSizes.slice(0, 15));
console.log('Line Heights:', lineHeights);

console.log('\n=== VISUAL EFFECTS ===');
console.log('Border Radius:', borderRadii);
console.log('Box Shadows:', boxShadows);

// 5. Structure of sections
const sections = [...html.matchAll(/id="([^"]+)"[^>]*class="[^"]*card[^"]*"/gi)].map(m => m[1]);
console.log('\n=== CARDS FOUND ===');
console.log(sections);

