// sw.js (Versión Mínima para Diagnóstico)

self.addEventListener('install', event => {
  console.log('Service Worker Mínimo: Instalado');
  // Forzamos al nuevo Service Worker a activarse inmediatamente.
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  console.log('Service Worker Mínimo: Activado');
});

// Lo más importante: un evento 'fetch', aunque no haga nada.
// Esto es un requisito para que la PWA sea instalable.
self.addEventListener('fetch', event => {
  // No hacemos nada con la petición, solo la dejamos pasar.
  return; 
});