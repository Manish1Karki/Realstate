# Land Discover

Land Discover is moving to a production-oriented stack for its public real estate marketplace. The public site is now a Next.js App Router application with TypeScript. Property search and detail pages render listing content on the server and generate page metadata, canonical URLs, robots rules, and a listing sitemap. The existing FastAPI collection and account API remains the source of listing data. Collection runs only in the backend; the research dashboard is not served by the public site.

Current storage is still SQLite locally and Turso libSQL on the hosted prototype. PostgreSQL/PostGIS and a dedicated queue/worker are a later backend migration. Collection remains source-specific and permission-aware. The public deployment includes the property visual tour and the AI assistant beneath each property's photos and map. Property valuation remains a separate local demo and is not published.

For local development, run the FastAPI service and Next.js in separate terminals:

```powershell
cd aggregator
.\.venv\Scripts\python.exe -m uvicorn land_discover.api:app --host 127.0.0.1 --port 8000
```

```powershell
npm.cmd run dev:web
```

Open `http://localhost:3000`. Next.js proxies `/api` to the local backend. The public site has no research dashboard route. The main site uses server-rendered listing pages. Account registration and sign-in are available at `/login`.

The aggregator automatically collects public property listings from Hamrobazar, HUKU Real Estate, Nepal Bhoomi, Ghar Jagga Nepal, Nepal Home Search, and Trade Nepal Real Estate on backend startup and every six hours, including available photos, property details, and map coordinates published on listing pages. Collection, search, exports, details, and sitemaps include listings posted within the past six calendar months, based on the original listing date in Nepal time. Unknown, future, and older listing dates are excluded. Listings require useful property information. Map pins and facility enrichment are optional for browsing; map results require coordinates. Backend operators can monitor collection with `/api/sources` (administrator token required when configured); no listing URLs need to be entered. It does not include an AI valuation or forecasting model. Source access limits and live validation evidence are documented in [`aggregator/docs/SOURCES.md`](aggregator/docs/SOURCES.md).

Databases, scraped CSV exports, credentials, installed dependencies, and generated dashboard builds are excluded from Git. A fresh clone starts without collected listings; follow the aggregator instructions to collect them locally.


## User accounts and authentication

Open `http://localhost:3000/login`, choose **Create an account**, and enter your
name, email and a password of at least eight characters. Registration signs you
in and opens your account dashboard at `/dashboard`. The header links your account
name to the dashboard and provides **Sign out**.
Existing users can sign in with email and password. **Remember me** persists the
cookie and server session for 30 days; otherwise the browser uses a session cookie
with a 12-hour server expiry. Logging out revokes the current session immediately.

Local users are stored in `aggregator/data/properties.sqlite3` (or `LAND_DB`) in the
`users` table: email, display name, salted scrypt password hash, creation time and
last login time. `user_sessions` stores hashes of random session tokens and their
expiry, never plaintext passwords or raw session tokens. Existing property data
is preserved. Hosted accounts and sessions use the remote Turso database instead
of a local file. Accounts and sessions persist across backend restarts.

Authentication endpoints are `POST /api/auth/register`, `/login`, `/logout`,
`POST /api/auth/forgot-password`, `/reset-password`, `/change-password`,
`/request-email-change`, `/confirm-email`, `GET /api/auth/me`, and
`GET /api/auth/config`. `GET` and `PATCH /me` require a valid session. Dashboard
settings support a display name, primary and alternate phone numbers, a verified
email change, and password changes. Changing a password revokes other sessions.
All account responses exclude password hashes. Origin checks and
persistent rate limits protect authentication requests. Cookies are HttpOnly
and SameSite=Lax. Password hashing uses the
[OWASP scrypt parameters](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html).

The frontend uses `/api/auth` by default, so no separate authentication service
or frontend environment setting is needed locally. For a hosted deployment,
serve frontend and `/api` under the same origin, configure `LAND_AUTH_ORIGINS`
with the exact HTTPS origin, and set `LAND_AUTH_SECURE_COOKIE=true`.

Password reset is implemented with single-use 15-minute tokens and revokes all
sessions. A signed-in password change ends other sessions while keeping the
current one active. To enable recovery and email verification, set
`LAND_SMTP_HOST`, `LAND_SMTP_PORT` (STARTTLS, default 587), `LAND_SMTP_USER`,
`LAND_SMTP_PASSWORD`, `LAND_MAIL_FROM`, and `LAND_PUBLIC_URL` in the backend `.env`.
Until mail delivery is configured, password recovery and email verification show
that email delivery is unavailable. The Next.js site currently supports
email/password authentication; Google sign-in is not configured.

For temporary local development only, `LAND_LOCAL_PASSWORD_RESET=true` enables
reset by account email without sending mail. The backend only accepts this mode
for loopback requests using local SQLite with the proxy disabled. Keep it false
in hosted environments; use the verified email reset flow there.

Property submission requires a valid signed-in session. Guests visiting `/properties/new` are redirected to login and returned to the form after sign-in or registration. The backend rejects unauthenticated, expired, or revoked sessions on `POST /api/properties`; browsing listings remains public.

Collection defaults to six index pages and up to 80 inspected detail URLs per source per cycle (maximum configurable limits: 30 pages/300 URLs). Reports distinguish inspected, imported/updated, rejected and date/information skips. External listings are stored as an information cache with source URLs and original listing dates. Approximate address geocoding remains optional. Automatic nearby-facility enrichment is enabled for source-published map pins within a 2,000 metre radius (straight-line distance), using cached OpenStreetMap data. Listings without a source pin retain their address but cannot provide reliable property-centred facility distances.

## Scraped location, road access, and nearby facilities

Property photo collection merges source-specific photos, listing schema image arrays, and public gallery/carousel images, including lazy-loaded images and full-size lightbox links. Up to 30 distinct photo URLs are stored in `image_urls`; `image_url` is the cover photo. Related listings, logos, and placeholders are excluded. A source with only one published photo retains one photo; additional perspectives are never fabricated. Existing listings receive expanded galleries on re-collection.

Each source detail adapter captures the published address and map coordinates when available. Road evidence is retained in `road_access_note`, with structured `road_type` (asphalt, concrete, gravel, earth, or pavers), `road_width_ft`, `road_is_pitched`, and `road_under_construction`. The last field describes the access road, not the building. Boolean fields are `true`, `false`, or `null` in the API; missing or conflicting evidence remains unknown. Pitched means paved: asphalt, concrete, or pavers. Future paving promises do not establish the present surface. These are source-reported claims, not an independent inspection.

Automatic enrichment defaults to `LAND_AUTO_ENRICH=true` and `LAND_AUTO_ENRICH_RADIUS=2000`. The detail API returns mapped schools/colleges/universities, healthcare facilities, pharmacies, banks/ATMs, markets/shops/department stores, transport stops, parks/playgrounds, police and fire stations within 2 km of the source pin, with names and straight-line distances. OpenStreetMap coverage may be incomplete. A nearby mapped road does not establish legal or physical access, pavement, or current construction status. Failed facility lookups remain marked as errors; an empty successful result means no matching mapped facilities were returned.

Existing listings gain road fields on re-collection. To refresh nearby facilities for existing source pins, run `.venv/Scripts/python.exe -m land_discover.cli enrich --radius 1000 --limit 100 --retry` from the `aggregator` directory.

The property detail API accepts `?radius_m=1000` or `?radius_m=2000` to view nearby facilities at either radius. `facilities_radius_m` identifies the requested radius; `facilities_complete` is false when enrichment failed, is pending, or covers a smaller radius. Mapped residential buildings are not included as facilities.

Public listing phone numbers are stored in `contact_phone`, with `contact_role` set to owner, agent, seller, or unknown only according to the page label. Masked numbers, reveal controls, hidden data, related listings and site-wide office contacts are excluded. Missing numbers remain null and contacts are refreshed on re-collection. Published contact claims do not verify ownership. Source-advertised prices remain in `price_raw`; normalized prices and totals derived from explicit unit prices remain labelled. No price is generated when a source omits it; synthetic demo records are separate from the public dataset.

## Property folders and primary IDs

The database `properties.id` is the primary key for each property. Re-scraping the same source listing updates that ID. The local archive mirrors non-demo records under `aggregator/data/property-archive/`, organized by district, locality, and `property-000084` (example ID). Folder names include a short hash to avoid collisions between sanitized location names.

Each property folder contains:

- `property.json`: the complete property record, database ID, source URL, road details and photo URLs.
- `location.json`: address, district, locality, ward, coordinates and precision.
- `contact.json`: publicly published number, contact role, and an explicit unverified-ownership flag.
- `facilities.json`: facilities, distances, enrichment radius and status.
- `photos/manifest.json`: source URLs, downloaded file names, pending/error status and timestamps.
- `photos/photo-<hash>.jpg` (or other supported raster extension): downloaded originals, up to 30 photos per property, with a 10 MiB limit per file.

Every companion JSON file references the same `property_id`; `by-id/property-000084.json` points to its location folder. If a property's location changes, its folder and existing photos move while the primary ID stays the same. Downloads reuse existing files and report failures without discarding property metadata. Failed URLs are retried after six hours, while other pending photos can proceed in subsequent batches. This archive is local, excluded from Git, and outside the public web assets.

Metadata is refreshed after property upserts, geocoding, and facility enrichment. Scraping/import and automatic collection also download photos in bounded batches. Settings: `LAND_ARCHIVE_ENABLED=true`, optional `LAND_ARCHIVE_DIR`, and `LAND_ARCHIVE_PHOTO_BATCH=40`. Hosted deployments need a persistent disk or an external archive location for durable files; the Turso database remains the source of truth.

To backfill or refresh the archive from the `aggregator` directory:

```powershell
.\.venv\Scripts\python.exe -m land_discover.cli archive
.\.venv\Scripts\python.exe -m land_discover.cli archive --photos --max-downloads 40
```

Repeat photo batches to download remaining photos. A pending or error photo entry is a source reference, not a claim that the file was downloaded. Cross-source advertisements retain separate IDs because matching them to the same physical property requires verification.
