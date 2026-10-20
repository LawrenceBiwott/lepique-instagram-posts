// Lepique Fashions Service Worker — v1.0
// Cache-first for images, network-first for HTML

const CACHE = 'lepique-v1';
const STATIC = [
  '/',
  '/catalogue.html',
  '/wide-leg-jeans-nairobi.html',
  '/skinny-jeans-nairobi.html',
  '/flare-jeans-nairobi.html',
  '/high-waist-jeans-nairobi.html',
  '/mom-jeans-nairobi.html',
  '/denim-jackets-nairobi.html',
  '/leather-jackets-nairobi.html',
  '/ladies-croptops-nairobi.html',
  '/new-arrivals-nairobi.html',
  '/lepique-ai.js',
  '/site.webmanifest',
];

self.addEventListener('install', e => {
  self.skipWaiting();
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(STATIC).catch(() => {})));
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);
  if (e.request.method !== 'GET') return;
  if (url.hostname !== self.location.hostname) return;

  // Images: cache-first (long TTL)
  if (/\.(jpe?g|png|webp|avif|gif|svg)$/i.test(url.pathname)) {
    e.respondWith(
      caches.match(e.request).then(cached => {
        if (cached) return cached;
        return fetch(e.request).then(resp => {
          const clone = resp.clone();
          caches.open(CACHE).then(c => c.put(e.request, clone));
          return resp;
        }).catch(() => new Response('', {status: 404}));
      })
    );
    return;
  }

  // HTML: network-first, fall back to cache
  if (/\.html$|^\/$/.test(url.pathname)) {
    e.respondWith(
      fetch(e.request)
        .then(resp => {
          const clone = resp.clone();
          caches.open(CACHE).then(c => c.put(e.request, clone));
          return resp;
        })
        .catch(() => caches.match(e.request))
    );
    return;
  }

  // JS/CSS: stale-while-revalidate
  e.respondWith(
    caches.match(e.request).then(cached => {
      const fetchPromise = fetch(e.request).then(resp => {
        caches.open(CACHE).then(c => c.put(e.request, resp.clone()));
        return resp;
      });
      return cached || fetchPromise;
    })
  );
});
