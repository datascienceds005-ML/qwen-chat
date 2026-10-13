/* Cache-first app shell · network-only for the API.
   CACHE version MUST move in lockstep with APP_VERSION (backend/app/__init__.py). */
const VERSION = '0.1.0';
const CACHE = `qwen-chat-${VERSION}`;
const ASSETS = [
  '/', '/index.html', '/style.css', '/app.js', '/manifest.json',
  '/icons/icon-192.png', '/icons/icon-512.png',
];

self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE).then(c =>
      Promise.allSettled(ASSETS.map(a => c.add(a)))
    ).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;                    // never cache inference POSTs
  const p = new URL(e.request.url).pathname;
  if (p.startsWith('/v1/') || p.startsWith('/api/')) return; // network-only
  e.respondWith(
    caches.match(e.request).then(hit => hit || fetch(e.request).then(res => {
      const copy = res.clone();
      caches.open(CACHE).then(c => c.put(e.request, copy));
      return res;
    }).catch(() => p === '/' || !p.includes('.')
        ? caches.match('/index.html') : undefined))
  );
});
