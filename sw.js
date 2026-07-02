// Service worker de la Calculadora de Despiece SMC.
// Estrategia: cache-first para los assets propios (funciona sin conexión),
// con fallback a red si algo no está cacheado todavía.
//
// IMPORTANTE al actualizar la app: sube el número de CACHE_VERSION cada vez
// que subas un index.html nuevo al repo. Si no lo subes, los móviles que ya
// tengan la app instalada seguirán viendo la versión vieja cacheada.
const CACHE_VERSION = 'smc-calc-v1';

const ASSETS = [
    './',
    './index.html',
    './manifest.json',
    './tailwind.min.css',
    './icon-192.png',
    './icon-512.png',
    './apple-touch-icon.png'
];

self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_VERSION).then((cache) => cache.addAll(ASSETS))
    );
    self.skipWaiting();
});

self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((keys) =>
            Promise.all(keys.filter((k) => k !== CACHE_VERSION).map((k) => caches.delete(k)))
        )
    );
    self.clients.claim();
});

self.addEventListener('fetch', (event) => {
    if (event.request.method !== 'GET') return;
    event.respondWith(
        caches.match(event.request).then((cached) => {
            if (cached) return cached;
            return fetch(event.request).then((response) => {
                // Cachea también cualquier asset nuevo del mismo origen que se pida
                if (response.ok && event.request.url.startsWith(self.location.origin)) {
                    const clone = response.clone();
                    caches.open(CACHE_VERSION).then((cache) => cache.put(event.request, clone));
                }
                return response;
            }).catch(() => cached);
        })
    );
});
