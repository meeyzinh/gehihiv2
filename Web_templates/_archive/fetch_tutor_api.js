const { chromium } = require('playwright');
const fs = require('fs');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  
  await page.goto('https://memory.gmbot.name.vn/');
  await page.waitForTimeout(1000);
  
  // Get captcha SVG
  const svgText = await page.evaluate(() => {
    const el = document.getElementById('captchaSvg') || document.querySelector('svg');
    return el ? el.innerHTML : '';
  });
  
  const textMatches = svgText.match(/<text[^>]*>([^<]+)<\/text>/g) || [];
  const captchaCode = textMatches.map(m => m.replace(/<[^>]+>/g, '').trim()).join('');
  console.log('Captcha Code:', captchaCode);
  
  await page.fill('#username', '330730');
  await page.fill('#password', '123456');
  await page.fill('#captcha', captchaCode);
  await page.click('button[type="submit"]');
  await page.waitForTimeout(2000);
  
  const token = await page.evaluate(() => localStorage.getItem('token'));
  console.log('Token:', token ? token.substring(0, 20) + '...' : 'null');
  
  if (token) {
    const data = await page.evaluate(async (tok) => {
      const r1 = await fetch('/api/english-tutor/templates?mode=lesson', {
        headers: { 'Authorization': 'Bearer ' + tok }
      }).then(r => r.json()).catch(e => ({ error: e.message }));
      
      const r2 = await fetch('/api/english-tutor/templates?mode=roleplay', {
        headers: { 'Authorization': 'Bearer ' + tok }
      }).then(r => r.json()).catch(e => ({ error: e.message }));

      const r3 = await fetch('/api/english-tutor/recommendation?deviceId=330730', {
        headers: { 'Authorization': 'Bearer ' + tok }
      }).then(r => r.json()).catch(e => ({ error: e.message }));

      const r4 = await fetch('/api/english-tutor/active-lesson?deviceId=330730', {
        headers: { 'Authorization': 'Bearer ' + tok }
      }).then(r => r.json()).catch(e => ({ error: e.message }));

      const r5 = await fetch('/api/english-tutor/parent-report?deviceId=330730', {
        headers: { 'Authorization': 'Bearer ' + tok }
      }).then(r => r.json()).catch(e => ({ error: e.message }));

      return { lesson: r1, roleplay: r2, recommendation: r3, activeLesson: r4, parentReport: r5 };
    }, token);

    fs.writeFileSync('english_tutor_api_data.json', JSON.stringify(data, null, 2), 'utf8');
    console.log('Saved english_tutor_api_data.json!');
    console.log('Lessons count:', data.lesson?.templates?.length);
    console.log('Roleplay count:', data.roleplay?.templates?.length);
  }
  
  await browser.close();
})();

