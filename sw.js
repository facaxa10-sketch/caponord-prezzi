/* ===========================================================================
   Capo Nord 2026 · service worker
   - app e icone: sempre disponibili offline
   - librerie esterne (mappe, globo, font): messe in cache alla prima visita
   - tessere delle mappe: quelle già viste restano leggibili senza rete
   =========================================================================== */
const VERSION    = "v27";
const CACHE_APP  = "caponord-app-"   + VERSION;
const CACHE_LIB  = "caponord-lib-"   + VERSION;
const CACHE_TILE = "caponord-tiles-" + VERSION;
const TILE_MAX   = 400;

const SHELL = [
  "./", "./index.html", "./manifest.webmanifest",
  "./icon-192.png", "./icon-512.png", "./apple-touch-icon.png"
];

const LIBS = [
  "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js",
  "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css",
  "https://cdnjs.cloudflare.com/ajax/libs/d3/7.8.5/d3.min.js",
  "https://cdnjs.cloudflare.com/ajax/libs/topojson/3.0.2/topojson.min.js",
  "https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json"
];

const isTile = url =>
  /tile\.openstreetmap\.org|basemaps\.cartocdn\.com|tile\.opentopomap\.org|\.tile\./.test(url.hostname + url.pathname);
const isLib = url =>
  /cdnjs\.cloudflare\.com|cdn\.jsdelivr\.net|fonts\.googleapis\.com|fonts\.gstatic\.com|unpkg\.com/.test(url.hostname);

self.addEventListener("install", e => {
  e.waitUntil((async () => {
    const app = await caches.open(CACHE_APP);
    await app.addAll(SHELL);
    const lib = await caches.open(CACHE_LIB);
    await Promise.allSettled(LIBS.map(u => lib.add(new Request(u, { mode: "cors" }))));
    self.skipWaiting();
  })());
});

self.addEventListener("activate", e => {
  e.waitUntil((async () => {
    const keep = [CACHE_APP, CACHE_LIB, CACHE_TILE];
    const keys = await caches.keys();
    await Promise.all(keys.filter(k => !keep.includes(k)).map(k => caches.delete(k)));
    await self.clients.claim();
  })());
});

async function trimTiles() {
  const c = await caches.open(CACHE_TILE);
  const keys = await c.keys();
  if (keys.length > TILE_MAX) {
    for (const k of keys.slice(0, keys.length - TILE_MAX)) await c.delete(k);
  }
}

self.addEventListener("fetch", e => {
  const req = e.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);

  /* 1. tessere delle mappe: rete, ma quelle già viste restano offline */
  if (isTile(url)) {
    e.respondWith((async () => {
      const c = await caches.open(CACHE_TILE);
      try {
        const r = await fetch(req);
        if (r && (r.ok || r.type === "opaque")) { c.put(req, r.clone()); trimTiles(); }
        return r;
      } catch (err) {
        const hit = await c.match(req);
        if (hit) return hit;
        throw err;
      }
    })());
    return;
  }

  /* 2. librerie e font: prima la cache, poi la rete */
  if (isLib(url)) {
    e.respondWith((async () => {
      const c = await caches.open(CACHE_LIB);
      const hit = await c.match(req);
      if (hit) return hit;
      const r = await fetch(req);
      if (r && (r.ok || r.type === "opaque")) c.put(req, r.clone());
      return r;
    })());
    return;
  }

  /* 3. Drive, prezzi, meteo, aurore: sempre dati vivi dalla rete */
  if (url.origin !== location.origin) return;

  /* 4. il sito: rete con copia di sicurezza in cache */
  e.respondWith((async () => {
    const c = await caches.open(CACHE_APP);
    try {
      const r = await fetch(req);
      if (r && r.ok) c.put(req, r.clone());
      return r;
    } catch (err) {
      const hit = await c.match(req);
      return hit || c.match("./index.html");
    }
  })());
});
