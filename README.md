# Land Discover

Land Discover is moving to a production-oriented stack for its public real estate marketplace. The public site is now a Next.js App Router application with TypeScript. Property search and detail pages render listing content on the server and generate page metadata, canonical URLs, robots rules, and a listing sitemap. The existing FastAPI collection and account API remains the source of listing data. Collection runs only in the backend; the research dashboard is not served by the public site.

Current storage is still SQLite locally and Turso libSQL on the hosted prototype. PostgreSQL/PostGIS and a dedicated queue/worker are a later backend migration; they have not been switched on by this front-end SEO migration. Collection remains source-specific and permission-aware. VisualTour is not part of the public deployment.

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

Collection defaults to six index pages and up to 80 inspected detail URLs per source per cycle (maximum configurable limits: 30 pages/300 URLs). Reports distinguish inspected, imported/updated, rejected and date/information skips. External listings are stored as an information cache with source URLs and original listing dates. Optional external geocoding/enrichment is disabled locally so it does not delay collection; source-published map pins are retained.
