// Offline support: the page itself is fetched fresh when there's signal and
// falls back to the saved copy when there isn't; demo videos and icons are cached.
const CACHE = 'ptc-v3';
const SHELL = ['/', '/manifest.webmanifest', '/icon-192.png', '/icon-512.png', '/apple-touch-icon.png',
  '/demos/glute-bridge.mp4', '/demos/clamshell.mp4', '/demos/heel-slide.mp4', '/demos/calf-stretch.mp4',
  '/demos/prone-press-up.mp4', '/demos/pelvic-tilt.mp4', '/demos/nerve-glide.mp4', '/demos/dead-bug.mp4', '/demos/bird-dog.mp4', '/demos/side-plank-knees.mp4',
  '/demos/cat-cow.mp4', '/demos/childs-pose.mp4', '/demos/figure-four.mp4', '/demos/hip-flexor-stretch.mp4', '/demos/hamstring-strap.mp4',
  '/demos/prone-y.mp4', '/demos/prone-t.mp4', '/demos/prone-i.mp4'];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => Promise.all(SHELL.map(u =>
    fetch(u, { credentials: 'same-origin' }).then(r => { if (r.ok && !r.redirected) return c.put(u, r); }).catch(() => {})
  ))).then(() => self.skipWaiting()));
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});
self.addEventListener('fetch', e => {
  const req = e.request, url = new URL(req.url);
  if (req.method !== 'GET' || url.origin !== location.origin) return;
  if (url.pathname.startsWith('/login') || url.pathname === '/healthz') return;
  if (req.mode === 'navigate' || url.pathname === '/') {
    e.respondWith(fetch(req).then(r => {
      if (r.ok && !r.redirected && url.pathname === '/') { const copy = r.clone(); caches.open(CACHE).then(c => c.put('/', copy)); }
      return r;
    }).catch(() => caches.match('/').then(r => r || Response.error())));
    return;
  }
  if (req.headers.has('range')) return; // let the browser stream video ranges from the network
  e.respondWith(caches.match(url.pathname).then(hit => hit || fetch(req).then(r => {
    if (r.ok && r.status === 200 && !r.redirected && /\.(mp4|png|webmanifest)$/.test(url.pathname)) {
      const copy = r.clone(); caches.open(CACHE).then(c => c.put(url.pathname, copy));
    }
    return r;
  })));
});
