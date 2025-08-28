/**
 * Service Worker for Financial Agent PWA
 * 提供离线功能和缓存管理
 */

const CACHE_NAME = "financial-agent-v1";
const urlsToCache = [
  "/",
  "/static/css/material.css",
  "/static/js/material-app.js",
  "https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap",
  "https://fonts.googleapis.com/icon?family=Material+Icons",
  "https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined",
  "https://cdn.jsdelivr.net/npm/chart.js",
];

// Install event
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log("Opened cache");
      return cache.addAll(urlsToCache);
    })
  );
});

// Fetch event
self.addEventListener("fetch", (event) => {
  event.respondWith(
    caches.match(event.request).then((response) => {
      // Return cached version or fetch from network
      return response || fetch(event.request);
    })
  );
});

// Activate event
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME) {
            console.log("Deleting old cache:", cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});
