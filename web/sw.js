// Minimal service worker – gör att IT-testare kan "installeras som app".
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', (e) => e.waitUntil(self.clients.claim()));
self.addEventListener('fetch', () => { /* låt nätet sköta allt */ });
