// Family PT Coach — tiny web server for Render.
// Serves the app from ./public behind one family passcode (FAMILY_CODE).
// All workout data stays on each phone; the server stores nothing.
'use strict';
const http = require('http');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const PORT = process.env.PORT || 3000;
const CODE = (process.env.FAMILY_CODE || '').trim();
const SECRET = process.env.COOKIE_SECRET || crypto.randomBytes(32).toString('hex');
const PUBLIC = path.join(__dirname, 'public');
const COOKIE = 'ptc_auth';
const YEAR = 365 * 24 * 3600;

// Files anyone may load without the passcode (needed to install the app icon and show the login page).
const OPEN = new Set(['/sw.js', '/manifest.webmanifest', '/icon-192.png', '/icon-512.png', '/icon-maskable-512.png', '/apple-touch-icon.png', '/healthz', '/login']);

const TYPES = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.png': 'image/png', '.mp4': 'video/mp4', '.webmanifest': 'application/manifest+json', '.json': 'application/json' };

// A token is tied to the current code, so changing FAMILY_CODE signs everyone out.
const token = () => crypto.createHmac('sha256', SECRET).update('ptc:' + CODE).digest('base64url');
const safeEq = (a, b) => { const x = Buffer.from(String(a)), y = Buffer.from(String(b)); return x.length === y.length && crypto.timingSafeEqual(x, y); };
function cookies(req) { const out = {}; (req.headers.cookie || '').split(';').forEach(p => { const i = p.indexOf('='); if (i > 0) out[p.slice(0, i).trim()] = decodeURIComponent(p.slice(i + 1).trim()); }); return out; }
const authed = req => !!CODE && safeEq(cookies(req)[COOKIE] || '', token());

// Simple brute-force guard: 10 wrong tries per address per 15 minutes.
const tries = new Map();
function tooMany(ip) { const now = Date.now(), t = (tries.get(ip) || []).filter(x => now - x < 15 * 60e3); tries.set(ip, t); return t.length >= 10; }
function miss(ip) { const t = tries.get(ip) || []; t.push(Date.now()); tries.set(ip, t); }
setInterval(() => { const now = Date.now(); for (const [k, v] of tries) if (!v.some(x => now - x < 15 * 60e3)) tries.delete(k); }, 10 * 60e3).unref();

const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
function loginPage(msg) {
  return `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>Family PT Coach</title><meta name="theme-color" content="#0a6a86"><link rel="manifest" href="/manifest.webmanifest"><link rel="apple-touch-icon" href="/apple-touch-icon.png">
<style>:root{--bg:#eef3f5;--s:#fff;--ink:#13222a;--mut:#56676f;--line:#d4dfe4;--acc:#0a6a86;--bad:#b3261e;color-scheme:light}
@media (prefers-color-scheme:dark){:root{--bg:#0d161b;--s:#152129;--ink:#e4edf0;--mut:#93a6ae;--line:#26363f;--acc:#53b6d2;--bad:#f08a80;color-scheme:dark}}
*{box-sizing:border-box}body{margin:0;min-height:100vh;display:grid;place-items:center;background:var(--bg);color:var(--ink);font:16px/1.45 system-ui,sans-serif;padding:24px max(16px,env(safe-area-inset-left))}
form{width:100%;max-width:340px;background:var(--s);border:1px solid var(--line);border-radius:16px;padding:24px;display:flex;flex-direction:column;gap:14px}
h1{margin:0;font-size:24px}p{margin:0;color:var(--mut)}input{font:inherit;color:inherit;font-size:22px;letter-spacing:.15em;text-align:center;padding:12px;border:1px solid var(--line);border-radius:10px;background:var(--bg);width:100%}
button{font:inherit;font-weight:700;font-size:18px;padding:14px;border:0;border-radius:10px;background:var(--acc);color:#fff;cursor:pointer}.err{color:var(--bad);font-weight:700}</style></head>
<body><form method="post" action="/login"><h1>Family PT Coach</h1><p>Enter the family passcode. You only need to do this once on each phone.</p>
${msg ? `<p class="err">${esc(msg)}</p>` : ''}<input name="code" type="password" inputmode="numeric" autocomplete="current-password" autofocus aria-label="Family passcode" required>
<button type="submit">Open</button></form></body></html>`;
}

function send(res, status, body, headers = {}) { res.writeHead(status, { 'Cache-Control': 'no-store', ...headers }); res.end(body); }

function serveFile(req, res, rel) {
  const file = path.join(PUBLIC, rel);
  if (!file.startsWith(PUBLIC + path.sep)) return send(res, 404, 'Not found');
  fs.stat(file, (err, st) => {
    if (err || !st.isFile()) return send(res, 404, 'Not found');
    const ext = path.extname(file);
    const headers = {
      'Content-Type': TYPES[ext] || 'application/octet-stream',
      'Cache-Control': ext === '.html' || rel === 'sw.js' ? 'no-cache' : 'public, max-age=86400',
      'Accept-Ranges': 'bytes',
      'X-Content-Type-Options': 'nosniff',
    };
    // iPhones need byte-range support to play video.
    const m = /^bytes=(\d*)-(\d*)$/.exec(req.headers.range || '');
    if (m && (m[1] || m[2])) {
      let start = m[1] ? +m[1] : Math.max(0, st.size - +m[2]);
      let end = m[1] && m[2] ? Math.min(+m[2], st.size - 1) : st.size - 1;
      if (start > end || start >= st.size) return send(res, 416, '', { 'Content-Range': `bytes */${st.size}` });
      res.writeHead(206, { ...headers, 'Content-Range': `bytes ${start}-${end}/${st.size}`, 'Content-Length': end - start + 1 });
      if (req.method === 'HEAD') return res.end();
      return fs.createReadStream(file, { start, end }).pipe(res);
    }
    res.writeHead(200, { ...headers, 'Content-Length': st.size });
    if (req.method === 'HEAD') return res.end();
    fs.createReadStream(file).pipe(res);
  });
}

const server = http.createServer((req, res) => {
  let url;
  try { url = new URL(req.url, 'http://x'); } catch { return send(res, 400, 'Bad request'); }
  const p = decodeURIComponent(url.pathname);
  const ip = (req.headers['x-forwarded-for'] || req.socket.remoteAddress || '').split(',')[0].trim();

  if (p === '/healthz') return send(res, 200, 'ok', { 'Content-Type': 'text/plain' });

  if (p === '/login') {
    if (!CODE) return send(res, 503, loginPage('The app isn’t set up yet: add FAMILY_CODE in Render → Environment.'), { 'Content-Type': 'text/html; charset=utf-8' });
    if (req.method === 'GET') return authed(req) ? send(res, 303, '', { Location: '/' }) : send(res, 200, loginPage(''), { 'Content-Type': 'text/html; charset=utf-8' });
    if (req.method !== 'POST') return send(res, 405, 'Method not allowed');
    let body = '';
    req.on('data', c => { body += c; if (body.length > 4096) req.destroy(); });
    req.on('end', () => {
      if (tooMany(ip)) return send(res, 429, loginPage('Too many wrong tries. Wait 15 minutes and try again.'), { 'Content-Type': 'text/html; charset=utf-8' });
      const code = (new URLSearchParams(body).get('code') || '').trim();
      if (!safeEq(code, CODE)) { miss(ip); return send(res, 401, loginPage('That passcode isn’t right. Try again.'), { 'Content-Type': 'text/html; charset=utf-8' }); }
      send(res, 303, '', { Location: '/', 'Set-Cookie': `${COOKIE}=${token()}; Max-Age=${YEAR}; Path=/; HttpOnly; Secure; SameSite=Lax` });
    });
    return;
  }

  if (req.method !== 'GET' && req.method !== 'HEAD') return send(res, 405, 'Method not allowed');
  if (!OPEN.has(p) && !authed(req)) {
    if (p === '/' || p === '/index.html') return send(res, 303, '', { Location: '/login' });
    return send(res, 401, 'Sign in first');
  }
  serveFile(req, res, p === '/' ? 'index.html' : p.replace(/^\/+/, ''));
});

server.listen(PORT, () => console.log(`Family PT Coach on :${PORT}${CODE ? '' : ' (FAMILY_CODE not set — app is locked)'}`));
