self.addEventListener("install", function (event) {
    event.waitUntil(
      caches.open("mulla-cache-v1").then(function (cache) {
        return cache.addAll([
          "/", // cache only the homepage
        ]);
      })
    );
  });
  
  self.addEventListener("fetch", function (event) {
    if (event.request.mode === "navigate" || event.request.url.endsWith(".html")) {
      // For navigations, prefer network
      event.respondWith(
        fetch(event.request).catch(() =>
          caches.match("/")
        )
      );
    } else {
      // For static files (like icons), use cache first
      event.respondWith(
        caches.match(event.request).then((response) =>
          response || fetch(event.request)
        )
      );
    }
  });
  