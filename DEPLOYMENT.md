# Land Discover prototype on Vercel

The prototype publishes the three required parts under one Vercel website:

| Route | Feature |
|---|---|
| `/` | Landing page |
| `/aggregator/` | Aggregator dashboard, collected properties, source status |
| `/login` | Registration, login, account sessions |
| `/properties` and `/properties/:id` | Public marketplace and property details |

`VisualTour/` is excluded from the deployment upload and build. Property details
include two sections: property information and a map placeholder. The live map
will be added later.

Vercel serves the compiled website and a small same-origin API proxy. The existing
FastAPI backend runs on Render's Free plan with a remote Turso libSQL database
on Turso's Free plan. This preserves
accounts, sessions, and scraped listings across deployments and runs the existing
background scraper on every backend restart. This setup deploys the user-facing
system on Vercel; the backend and storage are separate services.

The prototype is live at **https://land-discover-prototype.vercel.app**. Its backend
is `https://land-discover-api.onrender.com`, and persistent storage is the Turso
libSQL database `land-discover-prototype`. All three services use free plans.
Production secrets are configured in the providers, not in this repository.

Hosted checks passed for registration, sessions, logout, login, page refreshes,
frontend assets, property details, and exclusion of `/VisualTour/`. The first
startup collected five Hamrobazar listings with photos. HUKU currently returns
HTTP 403 to the hosted collector; the Data sources screen records that error.
The steps below document how to recreate the deployment.

## 1. Publish application code

Commit application code, `package.json`, `package-lock.json`, `vercel.json`,
`render.yaml`, and this guide. Do not commit `.env`, accounts, local database
files, or secrets. `aggregator/data/` and local configuration remain excluded.

## 2. Create the free persistent database and backend

Sign in to [Turso](https://turso.tech/) and use the **Free** plan. Create a
**libSQL** database for this prototype (the backend uses the `libsql` driver,
not Turso's newer database engine). Record its database URL and create a database
authentication token. Keep the token in backend environment variables only.
The application queries the cloud database directly; it does not depend on a
local replica or an ephemeral SQLite file for hosted data.
[Python SDK documentation](https://docs.turso.tech/sdk/python/quickstart)

In Render, create a Blueprint from the repository's root `render.yaml`.
The Blueprint selects a **Free web service with no paid disk**. Set
`TURSO_DATABASE_URL` and `TURSO_AUTH_TOKEN` using the database you just created.
`LAND_REQUIRE_PERSISTENT_DB=true` prevents startup if these are missing, so the
hosted app cannot silently store accounts in an ephemeral file.

The Blueprint specifies:

- Root directory: `aggregator`
- Python: `3.12.14`
- Build: `pip install -r requirements.txt`
- Start: `uvicorn land_discover.api:app --host 0.0.0.0 --port $PORT`
- Health check: `/api/health`
- Database: the remote Turso libSQL database
- Automatic scraping: one public HTML page and up to 20 listings per enabled source
- Secure session cookies and authenticated proxy access

Choose free workspace/service/database plans, avoid paid trials or upgrades, and
do not add payment methods for this prototype. Render's free service sleeps after
15 idle minutes and can take about a minute to wake. Vercel's proxy allows up to
110 seconds for a backend response (120-second function duration); keep Fluid
Compute enabled. This may make the first login or listings request slow.
Free usage limits still apply; services may suspend when limits are reached.
[Render free-service limits](https://render.com/docs/free),
[Turso pricing](https://turso.tech/pricing?frequency=monthly),
[Vercel function duration](https://vercel.com/docs/functions/configuring-functions/duration)

Render prompts for `LAND_AUTH_ORIGINS` and `LAND_PUBLIC_URL`. Set them to the
Vercel website's exact HTTPS origin, without a trailing slash, once its project
URL is known. Update these values after adding a custom domain. Trusted proxy
requests also support the same project's preview deployments.

Render generates `LAND_PROXY_SECRET` and `LAND_IMPORT_TOKEN`. The first is shared
with Vercel's server-side proxy; the second protects the developer-only manual
import endpoint. Normal users need neither secret, and both stay out of frontend
JavaScript. Direct API access is refused except for the health check.

Confirm `https://YOUR-BACKEND.onrender.com/api/health` returns `{"status":"ok"}`.

## 3. Create the Vercel project

Import the same repository into Vercel using the **repository root (`.`)**.
Do not select `LandingPage` as the project root for this combined prototype.

- Framework preset: Other
- Node.js: 24.x
- Install command: `npm run install:apps`
- Build command: `npm run build`
- Output directory: `dist`

`vercel.json` includes these build settings and routes. The root build compiles
the landing/login/marketplace app to `dist/`, then the aggregator to
`dist/aggregator/`. Each app has its own asset paths.

Add these **server-side** Vercel environment variables:

| Variable | Value |
|---|---|
| `BACKEND_API_URL` | Your Render backend HTTPS origin, such as `https://YOUR-BACKEND.onrender.com` |
| `BACKEND_PROXY_SECRET` | The exact value of Render's `LAND_PROXY_SECRET` |

Set them for Production and, if desired, Preview. Do not use `VITE_` prefixes
for either value. Leave `VITE_AUTH_API_URL`, `VITE_PROPERTY_API_URL`, and
`VITE_GOOGLE_AUTH_URL` unset; leave `VITE_DASHBOARD_URL` unset or `/properties`.
The browser calls `/api` on its own website origin. The proxy forwards API
responses and session cookies; users stay on the Vercel website.

Deploy, then set Render's public URL/origin variables to the resulting Vercel
origin. [Vercel rewrite documentation](https://vercel.com/docs/routing/rewrites)

## 4. Verify the hosted prototype

1. Open `/`, `/aggregator/`, and `/login`, including direct page refreshes.
2. Create a test account, confirm its name appears in the marketplace header,
   sign out, then sign in again.
3. Check the aggregator's Data sources page for Hamrobazar and HUKU collection.
4. Open a property and check its image, description, price, and source.
5. Redeploy the backend, then confirm the test account and existing listings
   still exist. A backend restart starts another bounded collection cycle.
6. Confirm the visual-tour project is not served.

New hosting starts with an empty database. The scraper supplies new listings,
and testers create new accounts. To carry over local records, transfer a
reviewed database migration explicitly into Turso; never commit or
publish the account database as a website asset.

Password reset is hidden until backend mail delivery is configured (Render's
free service blocks common SMTP ports). Google
OAuth is not part of the email/password prototype. Source reviews still expire
after 30 days; a changed or expired policy review appears as a collection error
until that source is reviewed again.

## Keep updating while testing

The current Vercel deployment was published through the CLI. Its GitHub
integration is not connected, so pushing to GitHub alone does not publish website
changes. From the repository root, deploy an update with:

```powershell
npm.cmd run deploy:prototype
```

The script prepares a clean upload containing application sources and project
link metadata, then runs the Vercel production deployment. It excludes local
databases, environment files, dependencies, caches, and VisualTour. This also
avoids a Windows permission error when the CLI scans the local Python cache.
Use `npm.cmd run deploy:prototype -- --prepare-only` to inspect the upload without
publishing it. On another
machine, first sign in to the Vercel CLI and link the existing
`land-discover-prototype` project in the `manish-33ce` team.

For backend changes, push the commit to GitHub and select **Manual Deploy →
Deploy latest commit** in the Render service dashboard. Keep the existing
database environment variables. Turso keeps records during backend redeployments
and idle shutdowns. Preview deployments are not configured in this prototype;
before using them, configure their server-side proxy variables and use a separate
testing backend/database when real users join. Keep database tokens and proxy
secrets out of frontend code and the repository.

## Local development and checks

Start the backend using `aggregator/start.ps1`. In separate terminals at the
repository root, run `npm run dev:landing` and `npm run dev:aggregator`.
Open `http://127.0.0.1:5173/`; its aggregator link goes through the local Vite
proxy to port 5174. Keep `LAND_REQUIRE_PROXY=false` locally.

Before committing:

```powershell
npm.cmd run build
npm.cmd run test:hosting
```

Run backend tests from `aggregator/` with
`.\.venv\Scripts\python.exe -m pytest -q`. Production routing/proxy behavior
is covered by Node tests, and hosted backend authentication/administrator
restrictions are covered by backend tests. Cloud deployment acceptance still
requires the live checks above after accounts and environment variables are set.
