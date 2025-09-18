// Define un nombre para nuestra caché
const CACHE_NAME = 'silvatest-v1';
// Lista de archivos que queremos cachear al instalar el Service Worker.
// El más importante es nuestra página offline.
const urlsToCache = [
  '/offline'
];

// Evento 'install': Se dispara cuando el Service Worker se instala.
self.addEventListener('install', event => {
  // Espera hasta que la promesa se resuelva
  event.waitUntil(
    // Abre la caché con el nombre que definimos
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('Cache abierta');
        // Añade todos los archivos de nuestra lista a la caché
        return cache.addAll(urlsToCache);
      })
  );
});

// Evento 'fetch': Se dispara cada vez que la página pide un recurso (una página, una imagen, etc.)
self.addEventListener('fetch', event => {
  event.respondWith(
    // Intenta obtener el recurso de la red primero
    fetch(event.request)
      .catch(() => {
        // Si falla (porque no hay conexión), devuelve la página offline desde la caché
        return caches.match('/offline');
      })
  );
});