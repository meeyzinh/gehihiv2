const https = require('https');
const fs = require('fs');

function request(url, options = {}, body = null) {
  return new Promise((resolve, reject) => {
    const req = https.request(url, options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          resolve({ status: res.statusCode, headers: res.headers, data: JSON.parse(data) });
        } catch (e) {
          resolve({ status: res.statusCode, headers: res.headers, data });
        }
      });
    });
    req.on('error', reject);
    if (body) req.write(typeof body === 'string' ? body : JSON.stringify(body));
    req.end();
  });
}

async function main() {
  console.log('1. Getting captcha...');
  const captchaRes = await request('https://memory.gmbot.name.vn/api/captcha?t=' + Date.now());
  const captchaId = captchaRes.data.captchaId;
  const svg = captchaRes.data.svg;
  
  const matches = svg.match(/<text[^>]*>([^<]+)<\/text>/g) || [];
  const captchaCode = matches.map(m => m.replace(/<[^>]+>/g, '').trim()).join('');
  console.log('Captcha ID:', captchaId, 'Code:', captchaCode);
  
  console.log('2. Logging in...');
  const loginRes = await request('https://memory.gmbot.name.vn/api/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' }
  }, {
    username: '330730',
    password: '123456',
    captchaId,
    captchaCode
  });
  
  const token = loginRes.data.token;
  console.log('Login result status:', loginRes.status, 'Token exists:', !!token);
  
  if (!token) {
    console.error('Login failed:', loginRes.data);
    return;
  }
  
  const authHeaders = {
    'Authorization': 'Bearer ' + token,
    'Content-Type': 'application/json'
  };
  
  console.log('3. Fetching lessons & roleplay templates...');
  const [lessonsRes, roleplayRes] = await Promise.all([
    request('https://memory.gmbot.name.vn/api/english-tutor/templates?mode=lesson', { headers: authHeaders }),
    request('https://memory.gmbot.name.vn/api/english-tutor/templates?mode=roleplay', { headers: authHeaders })
  ]);
  
  const lessons = lessonsRes.data.templates || [];
  const roleplay = roleplayRes.data.templates || [];
  
  console.log(`Fetched ${lessons.length} lesson templates and ${roleplay.length} roleplay templates.`);
  
  fs.writeFileSync('all_english_templates.json', JSON.stringify({
    lessons,
    roleplay
  }, null, 2), 'utf8');
  
  console.log('Saved all_english_templates.json successfully!');
}

main().catch(console.error);

