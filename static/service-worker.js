self.addEventListener('install', function(event) {
    event.waitUntil(
        caches.open('video-app-cache').then(function(cache) {
            return cache.addAll([
                '/',
                '/index.html',
                '/moderator.html',
                '/player.html',
                '/static/css/style.css',
                '/static/js/script.js',
                '/static/uploads/',
                '/manifest.json',
                '/static/icon-192x192.png',
                '/static/icon-512x512.png'
            ]);
        })
    );
});

self.addEventListener('fetch', function(event) {
    event.respondWith(
        caches.match(event.request).then(function(response) {
            return response || fetch(event.request);
        })
    );
});
