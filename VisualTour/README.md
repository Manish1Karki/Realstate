# Land Discover Visual Tour

Standalone aerial property-tour prototype. It does not modify or depend on the existing `LandingPage` or `aggregator` applications.

## Run locally

```powershell
npm install
npm run dev
```

## Production build

```powershell
npm run build
npm run preview
```

## Replace the demonstration property

Edit `src/property.js`. Boundary coordinates must use `[longitude, latitude]` order, and a polygon must repeat its first point as its last point.

The current coordinates, price, dimensions, travel times, and nearby locations are demonstration data. Do not present them as a real listing without verification.

## Map services

- Satellite imagery: Esri World Imagery
- Terrain: Re:Earth / Mapterhorn quantized mesh, with a flat-globe fallback
- Street map: OpenStreetMap

Provider attribution is displayed inside the interface and must remain visible. Public tile services are suitable for a low-traffic prototype; review provider terms and authenticated production options before a commercial launch.

## Listing-linked tour

The detail-page map embeds /visual-tour/index.html?embed=1&listing=ID.
The viewer fetches that listing through the public API; query strings cannot
replace its stored coordinates. Only source-published pins are accepted.
All camera views target that same pin. The standalone demo requires an explicit demo=1 URL parameter. Missing listing IDs show an error and never fall back to demo coordinates.

Terrain height is sampled at maximum available detail for the marker and camera.
It is shown as an estimate above the WGS84 ellipsoid, not surveyed altitude or
height above sea level. If terrain fails, elevation is shown as unavailable and
flat-map geometry is used. Demo locations and altitude never substitute.

Boundaries require explicit GeoJSON Polygon data with matching source provenance,
a closed ring containing the pin, and reasonable local dimensions.
Current scraped records have no plot boundary data, so no boundary is drawn.
Exact plot limits require cadastral/owner survey data.

The repository build generates public/visual-tour/ before Next.js.
