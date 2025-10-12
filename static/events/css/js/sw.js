const CACHE_NAME = 'eventhub-v1.2.0';
const urlsToCache = [
    '/',
    '/static/events/css/style.css',
    '/static/events/css/themes.css',
    '/static/events/js/theme_manager.js',
    '/static/events/js/main.js',
    '/static/images/logo.png'
];

self.addEventListener('install', function(event) {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(function(cache) {
                return cache.addAll(urlsToCache);
            })
    );
});

self.addEventListener('fetch', function(event) {
    event.respondWith(
        caches.match(event.request)
            .then(function(response) {
                if (response) {
                    return response;
                }
                return fetch(event.request);
            }
        )
    );
});

// Push notifications
self.addEventListener('push', function(event) {
    if (!event.data) return;

    const data = event.data.json();
    const options = {
        body: data.body,
        icon: '/static/images/logo-192.png',
        badge: '/static/images/badge-72.png',
        image: data.image,
        data: data.url,
        actions: [
            {
                action: 'open',
                title: 'Open Event'
            },
            {
                action: 'dismiss',
                title: 'Dismiss'
            }
        ],
        tag: data.tag || 'eventhub-notification',
        requireInteraction: true
    };

    event.waitUntil(
        self.registration.showNotification(data.title, options)
    );
});

self.addEventListener('notificationclick', function(event) {
    event.notification.close();

    if (event.action === 'open') {
        const url = event.notification.data || '/';
        event.waitUntil(
            clients.matchAll({type: 'window'}).then(windowClients => {
                for (let client of windowClients) {
                    if (client.url === url && 'focus' in client) {
                        return client.focus();
                    }
                }
                if (clients.openWindow) {
                    return clients.openWindow(url);
                }
            })
        );
    }
});

// Background sync для оффлайн функциональности
self.addEventListener('sync', function(event) {
    if (event.tag === 'background-sync') {
        event.waitUntil(doBackgroundSync());
    }
});

async function doBackgroundSync() {
    // Синхронизация данных при появлении соединения
    const requests = await getPendingRequests();
    for (let request of requests) {
        try {
            await fetch(request.url, request.options);
            await deletePendingRequest(request.id);
        } catch (error) {
            console.log('Background sync failed:', error);
        }
    }
}