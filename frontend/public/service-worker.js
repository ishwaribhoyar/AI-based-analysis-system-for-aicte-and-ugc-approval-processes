// Minimal service worker - doesn't cache aggressively during development
const CACHE_NAME = 'smart-approval-v2';

self.addEventListener('install', (event) => {
  // Skip waiting to immediately activate
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  // Clear old caches
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME) {
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  // Network-first strategy - always try network first
  event.respondWith(
    fetch(event.request)
      .catch(() => {
        // Only fall back to cache if network fails
        return caches.match(event.request);
      })
  );
});
