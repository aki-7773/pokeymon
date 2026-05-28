// Service Worker für Pokémon Website
const CACHE_NAME = 'pokemon-cache-v1';
const OFFLINE_URL = '/offline';

// Zu cachende Assets
const urlsToCache = [
  '/',
  '/static/logo.png',
  '/static/icon-192.png',
  '/static/icon-512.png'
];

// Installation des Service Workers
self.addEventListener('install', event => {
  console.log('[SW] Installing...');
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('[SW] Caching assets...');
        return cache.addAll(urlsToCache);
      })
      .then(() => self.skipWaiting())
  );
});

// Aktivierung des Service Workers
self.addEventListener('activate', event => {
  console.log('[SW] Activating...');
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cache => {
          if (cache !== CACHE_NAME) {
            console.log('[SW] Deleting old cache:', cache);
            return caches.delete(cache);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

// Fetch Event - Netzwerk zuerst, Fallback zu Cache
self.addEventListener('fetch', event => {
  const request = event.request;
  const url = new URL(request.url);
  
  // Nur GET-Anfragen cachen
  if (request.method !== 'GET') {
    event.respondWith(fetch(request));
    return;
  }
  
  // API-Anfragen nicht cachen (immer live)
  if (url.href.includes('pokeapi.co')) {
    event.respondWith(fetch(request));
    return;
  }
  
  // Strategie: Netzwerk zuerst, Fallback zu Cache
  event.respondWith(
    fetch(request)
      .then(response => {
        // Erfolgreiche Antwort in Cache speichern
        const responseClone = response.clone();
        caches.open(CACHE_NAME).then(cache => {
          cache.put(request, responseClone);
        });
        return response;
      })
      .catch(() => {
        // Netzwerk fehlgeschlagen, versuche Cache
        return caches.match(request)
          .then(cachedResponse => {
            if (cachedResponse) {
              return cachedResponse;
            }
            // Wenn nichts im Cache, zeige Offline-Seite für HTML-Anfragen
            if (request.headers.get('Accept').includes('text/html')) {
              return caches.match(OFFLINE_URL);
            }
            return new Response('Offline - No cached data available', {
              status: 503,
              statusText: 'Service Unavailable'
            });
          });
      })
  );
});

// Push Notifications (optional)
self.addEventListener('push', event => {
  const options = {
    body: event.data.text(),
    icon: '/static/icon-192.png',
    badge: '/static/icon-96.png',
    vibrate: [200, 100, 200],
    data: {
      url: '/'
    }
  };
  
  event.waitUntil(
    self.registration.showNotification('Pokémon Database', options)
  );
});

// Notification Click
self.addEventListener('notificationclick', event => {
  event.notification.close();
  event.waitUntil(
    clients.openWindow(event.notification.data.url || '/')
  );
});