/* Service worker de MédiGuide web : fonctionnement hors connexion.
   - Interface (fichiers de l'application) : cache d'abord, mis à jour en arrière-plan.
   - Données (meds.json, actualités, cas) : réseau d'abord, cache si hors connexion. */
const VERSION = "mediguide-web-2";
const INTERFACE = ["./", "index.html", "style.css", "app.js", "manifest.webmanifest", "icone-192.png", "icone-512.png", "croissance_oms.json", "croissance_fenton.json"];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(VERSION).then((c) => c.addAll(INTERFACE)).then(() => self.skipWaiting()));
});
self.addEventListener("activate", (e) => {
  e.waitUntil(caches.keys().then((ks) => Promise.all(ks.filter((k) => k !== VERSION && k !== "mediguide-donnees").map((k) => caches.delete(k))))
    .then(() => self.clients.claim()));
});
self.addEventListener("fetch", (e) => {
  const url = new URL(e.request.url);
  if (e.request.method !== "GET") return;
  if (url.hostname === "raw.githubusercontent.com") {
    e.respondWith(fetch(e.request).then((r) => {
      if (r.ok) { const copie = r.clone(); caches.open("mediguide-donnees").then((c) => c.put(url.origin + url.pathname, copie)); }
      return r;
    }).catch(() => caches.match(url.origin + url.pathname, { cacheName: "mediguide-donnees" })));
    return;
  }
  if (url.origin === self.location.origin) {
    e.respondWith(caches.match(e.request, { ignoreSearch: true }).then((c) => {
      const reseau = fetch(e.request).then((r) => { if (r.ok) { const copie = r.clone(); caches.open(VERSION).then((ca) => ca.put(e.request, copie)); } return r; }).catch(() => c);
      return c || reseau;
    }));
  }
});
