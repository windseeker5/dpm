// Minipass Service Worker - Push Notifications Only
// No caching, no complexity

self.addEventListener('push', (event) => {
  const data = event.data ? event.data.json() : { title: 'Minipass', body: 'New notification' };

  event.waitUntil(
    self.registration.showNotification(data.title, {
      body: data.body,
      icon: '/static/icons/icon-192x192.png',
      badge: '/static/favicon.png',
      tag: data.tag || 'minipass',
      data: { url: data.url || '/' }
    })
  );
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  event.waitUntil(
    clients.openWindow(event.notification.data.url || '/')
  );
});
