// Service Worker for Article Intelligence Hub PWA
const CACHE_NAME = 'article-hub-v1';
const OFFLINE_URL = '/offline.html';

// Files to cache for offline use
const urlsToCache = [
  '/',
  '/manifest.json',
  '/offline.html',
  'https://static.line-scdn.net/liff/edge/2/sdk.js'
];

// Install event - cache resources
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('Opened cache');
        return cache.addAll(urlsToCache.map(url => {
          return new Request(url, { mode: 'no-cors' });
        }));
      })
      .then(() => self.skipWaiting())
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== CACHE_NAME) {
            console.log('Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

// Fetch event - serve from cache or network
self.addEventListener('fetch', event => {
  // Skip cross-origin requests
  if (!event.request.url.startsWith(self.location.origin) && 
      !event.request.url.includes('line-scdn.net')) {
    return;
  }

  // Handle API requests differently (network first)
  if (event.request.url.includes('/api/')) {
    event.respondWith(
      fetch(event.request)
        .then(response => {
          // Clone the response before caching
          const responseToCache = response.clone();
          
          caches.open(CACHE_NAME).then(cache => {
            cache.put(event.request, responseToCache);
          });
          
          return response;
        })
        .catch(() => {
          // Try to return cached API response if network fails
          return caches.match(event.request);
        })
    );
    return;
  }

  // For non-API requests, use cache-first strategy
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        if (response) {
          // Return cached version
          return response;
        }

        // Clone the request
        const fetchRequest = event.request.clone();

        return fetch(fetchRequest).then(response => {
          // Check if valid response
          if (!response || response.status !== 200 || response.type !== 'basic') {
            return response;
          }

          // Clone the response
          const responseToCache = response.clone();

          caches.open(CACHE_NAME).then(cache => {
            cache.put(event.request, responseToCache);
          });

          return response;
        });
      })
      .catch(() => {
        // Return offline page for navigation requests
        if (event.request.mode === 'navigate') {
          return caches.match(OFFLINE_URL);
        }
      })
  );
});

// Background sync for offline article additions
self.addEventListener('sync', event => {
  if (event.tag === 'sync-articles') {
    event.waitUntil(syncArticles());
  }
});

async function syncArticles() {
  try {
    // Get pending articles from IndexedDB
    const pending = await getPendingArticles();
    
    for (const article of pending) {
      try {
        const response = await fetch('/api/articles', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(article)
        });
        
        if (response.ok) {
          await removePendingArticle(article.id);
        }
      } catch (error) {
        console.error('Failed to sync article:', error);
      }
    }
  } catch (error) {
    console.error('Sync failed:', error);
  }
}

// Push notification handling
self.addEventListener('push', event => {
  const options = {
    body: event.data ? event.data.text() : 'New article update!',
    icon: '/icon-192x192.png',
    badge: '/icon-72x72.png',
    vibrate: [100, 50, 100],
    data: {
      dateOfArrival: Date.now(),
      primaryKey: 1
    },
    actions: [
      {
        action: 'explore',
        title: 'Open Article Hub',
        icon: '/icon-72x72.png'
      },
      {
        action: 'close',
        title: 'Close',
        icon: '/icon-72x72.png'
      }
    ]
  };

  event.waitUntil(
    self.registration.showNotification('Article Intelligence Hub', options)
  );
});

// Notification click handling
self.addEventListener('notificationclick', event => {
  event.notification.close();

  if (event.action === 'explore') {
    event.waitUntil(
      clients.openWindow('/')
    );
  }
});

// IndexedDB functions for offline storage
function openDB() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('ArticleHubDB', 1);
    
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);
    
    request.onupgradeneeded = event => {
      const db = event.target.result;
      if (!db.objectStoreNames.contains('pending_articles')) {
        db.createObjectStore('pending_articles', { keyPath: 'id', autoIncrement: true });
      }
    };
  });
}

async function getPendingArticles() {
  const db = await openDB();
  const transaction = db.transaction(['pending_articles'], 'readonly');
  const store = transaction.objectStore('pending_articles');
  
  return new Promise((resolve, reject) => {
    const request = store.getAll();
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

async function removePendingArticle(id) {
  const db = await openDB();
  const transaction = db.transaction(['pending_articles'], 'readwrite');
  const store = transaction.objectStore('pending_articles');
  
  return new Promise((resolve, reject) => {
    const request = store.delete(id);
    request.onsuccess = () => resolve();
    request.onerror = () => reject(request.error);
  });
}

// Listen for skip waiting message
self.addEventListener('message', event => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});