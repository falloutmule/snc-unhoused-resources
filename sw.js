'use strict';
const CACHE_PREFIX = 'snc-unhoused-resources-';
const CACHE = CACHE_PREFIX + 'v1-9df71d544d93';
const APP_SHELL = [
  "./",
  "./index.html",
  "./phonebook/",
  "./phonebook/index.html",
  "./recovery/",
  "./recovery/index.html",
  "./phonebook/manifest.webmanifest",
  "./phonebook/icon-192.svg",
  "./phonebook/icon-512.svg",
  "./phonebook/share-qr.svg",
  "./phonebook/resources-01.js",
  "./phonebook/resources-02.js",
  "./phonebook/resources-03.js",
  "./phonebook/resources-04.js",
  "./phonebook/resources-05.js",
  "./phonebook/resources-06.js",
  "./phonebook/resources-07.js",
  "./phonebook/resources-08.js",
  "./phonebook/resources-09.js",
  "./phonebook/resources-10.js",
  "./phonebook/resources-11.js",
  "./phonebook/resources-12.js",
  "./phonebook/app.js"
];
const APP_URLS = new Set(APP_SHELL.map(path => new URL(path, self.location.href).href));

self.addEventListener('install', event => {
  event.waitUntil((async () => {
    const cache = await caches.open(CACHE);
    await cache.addAll([...APP_URLS].map(url => new Request(url, {cache: 'reload'})));
    await self.skipWaiting();
  })());
});

self.addEventListener('activate', event => {
  event.waitUntil((async () => {
    const keys = await caches.keys();
    // CacheStorage is shared with other projects on this origin. Leave them alone.
    await Promise.all(keys.filter(key => key.startsWith(CACHE_PREFIX) && key !== CACHE)
      .map(key => caches.delete(key)));
    await self.clients.claim();
  })());
});

// An install icon is not proof that every resource was saved. Reply only after
// checking the current cache, so pages can show a truthful offline-ready state.
self.addEventListener('message', event => {
  if (event.data?.type !== 'CHECK_OFFLINE_READY' || !event.ports?.[0]) return;
  event.waitUntil((async () => {
    let ready = false;
    try {
      const cache = await caches.open(CACHE);
      const saved = await Promise.all([...APP_URLS].map(url => cache.match(url)));
      ready = saved.every(response => response && response.ok);
    } catch (_) {}
    event.ports[0].postMessage({type: 'OFFLINE_STATUS', cache: CACHE, ready});
  })());
});

self.addEventListener('fetch', event => {
  if (event.request.method !== 'GET') return;
  const url = new URL(event.request.url);
  url.search = '';
  url.hash = '';
  // Only this project's known pages and assets; PDFs and provider sites are not cached.
  if (!APP_URLS.has(url.href)) return;
  const key = url.href;
  event.respondWith((async () => {
    const cache = await caches.open(CACHE);
    const cached = await cache.match(key);
    if (event.request.mode !== 'navigate' && cached) return cached;
    try {
      const response = await fetch(event.request);
      if (response.ok) {
        await cache.put(key, response.clone());
        return response;
      }
      return cached || response;
    } catch (error) {
      if (cached) return cached;
      throw error;
    }
  })());
});
