const CACHE_NAME = 'silvatest-v2'; // Importante: Cambia la versión para forzar la actualización
const STATIC_ASSETS = [
  '/offline',
  '/static/logo.png',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css',
  'https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css',
  'https://fonts.googleapis.com/css2?family=Lato:wght@400;700&display=swap'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      console.log('Cache abierta y assets estáticos guardados');
      return cache.addAll(STATIC_ASSETS);
    })
  );
  self.skipWaiting();
});

// Limpia cachés antiguas
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== CACHE_NAME) {
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});

self.addEventListener('fetch', event => {
  // Estrategia: Cache first para los assets estáticos
  if (STATIC_ASSETS.includes(new URL(event.request.url).pathname)) {
    event.respondWith(caches.match(event.request));
    return;
  }

  // Estrategia: Network first para el resto (contenido dinámico)
  event.respondWith(
    fetch(event.request).catch(() => {
      return caches.match('/offline');
    })
  );
});