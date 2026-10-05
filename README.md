# Land Discover

The prototype combines the landing page, aggregator and login in one Vercel website. See [DEPLOYMENT.md](DEPLOYMENT.md) for the free Vercel + Render + Turso setup with persistent data. VisualTour is excluded from this deployment.

This repository contains the website and its property data service:

- [`LandingPage/`](LandingPage/): marketing, login UI, public property marketplace at `/properties`, and property detail pages at `/properties/:id`.
- [`aggregator/`](aggregator/README.md): the Kathmandu Valley property scraper, FastAPI backend, SQLite storage, React dashboard, and tests.

The public marketplace uses the aggregator API and SQLite database. Visitors can browse, search, filter, save properties in their browser, and publish owner-submitted listings. Detail pages have two sections: property photos and information, and a map placeholder for a future location map. Visual tours are outside the hosted prototype. Browsing and owner submissions remain public. The built-in account service supports registration, email/password login, persistent sessions, remember me, and logout. The landing page and marketplace headers display the signed-in user.

For local development, run these commands in two terminals from the repository root:

```powershell
cd aggregator
.\.venv\Scripts\python.exe -m uvicorn land_discover.api:app --host 127.0.0.1 --port 8000
```

```powershell
cd LandingPage
npm.cmd run dev -- --host 127.0.0.1
```

Open `http://127.0.0.1:5173/properties`. Vite proxies `/api` to the backend. Owner submissions persist in the same database as collected listings and are marked as unverified. The submission form accepts an optional HTTPS photo URL; existing listings without a photo display a placeholder. Production hosting needs a persistent backend and a reverse proxy for `/api`, plus an SPA fallback for `/login` and `/properties/*`. This implementation is running locally and has not been deployed to the internet.

The aggregator automatically collects public property listings from Hamrobazar and HUKU Real Estate on every backend startup, including available photos and property details. It updates existing listings by source URL, supports location enrichment with OpenStreetMap services, and separates real collected listings from optional synthetic demo data. Open `http://127.0.0.1:8000` and select Data sources to monitor automatic collection; no listing URLs need to be entered. It does not include an AI valuation or forecasting model. Source access limits and live validation evidence are documented in [`aggregator/docs/SOURCES.md`](aggregator/docs/SOURCES.md).

Databases, scraped CSV exports, credentials, installed dependencies, and generated dashboard builds are excluded from Git. A fresh clone starts without collected listings; follow the aggregator instructions to collect them locally.


## User accounts and authentication

Open `http://127.0.0.1:5173/login`, choose **Create an account**, and enter your
name, email and a password of at least eight characters. Registration signs you
in and opens the marketplace. The header shows your account name and **Sign out**.
Existing users can sign in with email and password. **Remember me** persists the
cookie and server session for 30 days; otherwise the browser uses a session cookie
with a 12-hour server expiry. Logging out revokes the current session immediately.

Users are stored in `aggregator/data/properties.sqlite3` (or `LAND_DB`) in the
`users` table: email, display name, salted scrypt password hash, creation time and
last login time. `user_sessions` stores hashes of random session tokens and their
expiry, never plaintext passwords or raw session tokens. Existing property data
is preserved. Accounts and sessions persist across backend restarts.

Authentication endpoints are `POST /api/auth/register`, `/login`, `/logout`,
`GET /api/auth/me`, and `GET /api/auth/config`. The `/me` endpoint requires a
valid session. All account responses exclude password hashes. Origin checks and
persistent rate limits protect authentication requests. Cookies are HttpOnly
and SameSite=Lax. Password hashing uses the
[OWASP scrypt parameters](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html).

The frontend uses `/api/auth` by default, so no separate authentication service
or frontend environment setting is needed locally. For a hosted deployment,
serve frontend and `/api` under the same origin, configure `LAND_AUTH_ORIGINS`
with the exact HTTPS origin, and set `LAND_AUTH_SECURE_COOKIE=true`.

Password reset is implemented with single-use 15-minute tokens, and changing a
password revokes all existing sessions. To enable its email flow, set
`LAND_SMTP_HOST`, `LAND_SMTP_PORT` (STARTTLS, default 587), `LAND_SMTP_USER`,
`LAND_SMTP_PASSWORD`, `LAND_MAIL_FROM`, and `LAND_PUBLIC_URL` in the backend `.env`.
Until mail delivery is configured, the reset option stays hidden. Google login
stays hidden unless an external `VITE_GOOGLE_AUTH_URL` is configured; this change
implements email/password authentication.
