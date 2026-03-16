// DisasterNet Service Worker v2.5.0
const CACHE_NAME    = 'disasternet-v2.5.0';
const OFFLINE_URL   = '/offline/';

// Assets to pre-cache on install
const PRECACHE_URLS = [
    '/',
    '/disasters/',
    '/heatmap/',
    '/donate/',
    '/static/manifest.json',
    'https://unpkg.com/leaflet/dist/leaflet.css',
    'https://unpkg.com/leaflet/dist/leaflet.js',
    'https://fonts.googleapis.com/css2?family=Oswald:wght@400;600;700&family=Inter:wght@400;500;600&display=swap',
];

// ── INSTALL: pre-cache core assets ────────────────────────────
self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => cache.addAll(PRECACHE_URLS.map(u => new Request(u, { mode: 'no-cors' }))))
            .then(() => self.skipWaiting())
    );
});

// ── ACTIVATE: clean old caches ────────────────────────────────
self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(keys =>
            Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
        ).then(() => self.clients.claim())
    );
});

// ── FETCH: network-first for HTML, cache-first for assets ─────
self.addEventListener('fetch', event => {
    const { request } = event;
    const url = new URL(request.url);

    // Skip non-GET, cross-origin API calls, admin
    if (request.method !== 'GET') return;
    if (url.pathname.startsWith('/admin/'))  return;
    if (url.pathname.startsWith('/api/'))    return;
    if (url.pathname.includes('/get-live-population/')) return;

    // Static assets → cache-first
    if (
        url.pathname.startsWith('/static/') ||
        url.hostname.includes('unpkg.com') ||
        url.hostname.includes('fonts.googleapis.com') ||
        url.hostname.includes('fonts.gstatic.com') ||
        url.hostname.includes('openstreetmap.org') ||
        url.hostname.includes('tile.openstreetmap')
    ) {
        event.respondWith(
            caches.match(request).then(cached => {
                if (cached) return cached;
                return fetch(request).then(response => {
                    if (response && response.status === 200) {
                        const clone = response.clone();
                        caches.open(CACHE_NAME).then(c => c.put(request, clone));
                    }
                    return response;
                });
            })
        );
        return;
    }

    // HTML pages → network-first, fallback to cache
    if (request.headers.get('accept')?.includes('text/html')) {
        event.respondWith(
            fetch(request)
                .then(response => {
                    if (response && response.status === 200) {
                        const clone = response.clone();
                        caches.open(CACHE_NAME).then(c => c.put(request, clone));
                    }
                    return response;
                })
                .catch(() =>
                    caches.match(request).then(cached => cached || caches.match('/'))
                )
        );
        return;
    }
});

// ── BACKGROUND SYNC: queue failed POSTs ───────────────────────
self.addEventListener('sync', event => {
    if (event.tag === 'sync-reports') {
        event.waitUntil(syncQueuedReports());
    }
});

async function syncQueuedReports() {
    // Future: read from IndexedDB queue and replay failed report submissions
    console.log('[SW] Background sync triggered');
}
