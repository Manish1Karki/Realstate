# Land Discover — Kathmandu Valley data aggregator

Python 3.12+, FastAPI, SQLite, BeautifulSoup, React, Vite and Leaflet. This app is independent of the marketing landing page in the parent folder.

## Current delivery status

- Working dashboard: interactive OSM map, price/proximity marker colours, amenity heatmap, area/ward/type/price/proximity filters, paginated table, property detail dialog with mini-map, land-price comparison chart, CSV export and source status view.
- Working offline-tested pipeline: conservative price/size/date normalization, idempotent SQLite upserts, bounded pagination, robots checks, rate limiting, retries, source policy review gates, Nominatim geocoding/cache, Overpass enrichment/cache and run logs.
- **Working live Hamrobazar scraper.** A live run on 26 September 2026 imported 7 Valley listings, skipped 5 unsupported/out-of-area listings and reported no parsing failures. The CSV is `data/hamrobazar-listings.csv`; the same records are stored in SQLite and appear under Collected data. Other candidate sources remain disabled because of explicit reuse restrictions or unverified domains.
- 40 synthetic examples can be explicitly seeded for UI testing. They are isolated from collected data in every list, map, summary and export query.
- Live location validation: 4 of the 7 collected properties matched approximate OSM locations and were enriched within 1,500 m, producing 337 property-linked facility/road rows. These are not 337 unique facilities across the valley. Three addresses remain unresolved or too vague; no coordinates were fabricated.
- No AI valuation model, forecast model, water reliability inference, authentication or automatic collection scheduler is included.

## Quick start on Windows

From this `aggregator` directory:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
Copy-Item .env.example .env
cd frontend
npm ci
npm run build
cd ..
.\.venv\Scripts\python.exe -m land_discover.cli init
# Optional: create the clearly labelled demo dataset.
.\.venv\Scripts\python.exe -m land_discover.cli demo
.\.venv\Scripts\python.exe -m uvicorn land_discover.api:app --host 127.0.0.1 --port 8000
```

Open **http://127.0.0.1:8000**. API docs: **http://127.0.0.1:8000/docs**. Ctrl+C stops the server. After setup, `./start.ps1` is a convenience launcher. Do not recreate an existing working virtual environment just to launch it.

### Download real listings now

From `aggregator/`, after installing dependencies:

```powershell
.\.venv\Scripts\python.exe -X utf8 -m land_discover.cli scrape hamrobazar --pages 1 --limit 20 --csv data/hamrobazar-listings.csv
```

Or run `./scrape.ps1 -Limit 20`. This makes real HTTPS requests, validates current robots rules and the reviewed terms text, extracts public property fields, upserts SQLite records, and writes the current batch to CSV. The dashboard does not need to be running. To export every previously collected record, use `python -m land_discover.cli export data/all-listings.csv` with your virtual-environment Python.

On macOS/Linux, use `python3 -m venv .venv` and `.venv/bin/python` in place of the Windows Python path. Dependency versions are locked in `requirements-lock.txt`; the frontend has `package-lock.json`.

For UI development, start FastAPI as above and run `npm run dev` in `frontend/`. Vite proxies `/api` to port 8000. After production frontend changes, rebuild, then refresh the page. If the first build occurred after starting FastAPI, restart FastAPI so it mounts the frontend assets.

## Collecting permitted data

Read [source review](docs/SOURCES.md). Hamrobazar is enabled for bounded local public-HTML collection following live inspection. Sources with explicit permission requirements remain disabled. This is not a commercial redistribution license; the user has no source agreements. Source policy review is not a substitute for consent where required.

```powershell
.\.venv\Scripts\python.exe -m land_discover.cli sources
# Enabled public-HTML adapter:
.\.venv\Scripts\python.exe -m land_discover.cli scrape hamrobazar --pages 2 --limit 20
```

The crawler follows observed next-page links, deduplicates links/pages, limits each run, rejects cross-origin redirects, and checks robots at each URL. It does not synthesize page parameters, access disallowed APIs, bypass login/challenges, or silently switch to browser rendering. Hamrobazar's category/detail pages provide server-rendered HTML and Product JSON-LD; BeautifulSoup reads these directly. **The current category exposes 12 listing links and no ordinary next-page link.** The live run therefore processes that page, even if a larger limit is supplied, and reports this limitation. Disallowed API pagination is not attempted. Generic next-link pagination is covered by tests; full Hamrobazar infinite scrolling is not implemented.

Alternatively, import an authorized CSV. This does not download or scrape source pages:

```powershell
.\.venv\Scripts\python.exe -m land_discover.cli import-csv your-authorized-listings.csv --source partner-feed
```

CSV columns:

```csv
source_url,title,address,area_name,property_type,transaction_type,price_raw,size,listing_date_raw,road_access_note
```

Use a unique HTTPS `source_url`, an address including Kathmandu/Lalitpur/Bhaktapur, `land|house|apartment`, and `sale|rent|unknown`. `price_raw` examples: `25000000`, `2.5 crore`, `25 lakh per aana`; `size` examples: `0-4-0-0`, `4 aana`, `1250 sq ft`. Quote CSV values containing commas. Invalid rows are reported individually. A nonzero exit status signals errors/partial import. The imported data must be licensed for your intended use; the importer does not grant rights to third-party content.

## Location enrichment

In `.env`, set `LAND_CONTACT` to your real project URL or contact email. Endpoints are configurable. No API key is required.

```powershell
.\.venv\Scripts\python.exe -m land_discover.cli enrich --limit 10 --radius 1500
```

Radius is configurable from 250 to 2,000 metres. Results are persisted per property. The dashboard's radius control selects already-recorded enrichment; it does not initiate external requests. To recompute, run the CLI with a different radius. Use `--retry` to retry not-found/ambiguous geocodes after improving an address or changing your provider. Never manufacture parcel coordinates from an area centroid.

Geocoding uses an application-identifying User-Agent, one serial batch process per database, a persistent host clock, at least 1.1 seconds between requests, and 90-day response caching (including empty results). Only bounded Valley matches agreeing with the expected district are accepted; multiple matches remain unresolved. Matched coordinates are labelled approximate, not verified parcel boundaries. Bulk/recurring public Nominatim jobs are discouraged; use a suitable hosted or self-hosted service when scaling. Run on one machine, not distributed workers.

Overpass requests are at least 5 seconds apart and cached for 30 days. Schools/colleges, hospitals/clinics/doctors, major road ways, bus stops/platforms/stations, banks and marketplaces are recorded. Facility distances are straight-line distances; road distances use the nearest point on a mapped polyline. Missing amenities do not mean amenities are absent. No water-supply reliability is inferred.

## Data and calculations

- SQLite path defaults to `data/properties.sqlite3`, configurable with `LAND_DB`.
- Raw asking price, price basis, total price and original size are separate fields. A per-aana price is multiplied by the parsed land size only when both are known; a quality flag records the calculation.
- 1 ropani = 16 aana; 1 aana = 342.25 sq ft; 1 paisa = 1/4 aana; 1 daam = 1/4 paisa. Unsupported units remain unparsed.
- Hamrobazar's minute/hour/day/week relative Posted labels are converted to approximate dates in Nepal time, flagged as approximate, and preserved in `listing_date_raw`. Other unrecognized/Bikram Sambat dates remain raw; no guessed calendar conversion. Scraped date and first seen are separate from listing date.
- Hamrobazar masks some address fields. The adapter uses only the public title and visible description, never hidden application data to recover masked details. A named-locality fallback is marked inferred. District-only addresses are retained but not mapped or enriched.
- A bare Hamrobazar land amount is preserved as `price_npr` but its basis/total remain unknown unless the description states a unit or total. The ambiguous source label “Land Size (Aana/Dhur)” is not converted without explicit units. Seller contact information and full descriptions are not stored in the property database or CSV.
- Listings are deduplicated by source URL, not across sites. Changing an address invalidates prior geocoding/enrichment. Re-collection does not prove availability; verify the original source and listing date before relying on any record.
- Median asking-price card excludes rentals and unknown totals. Area chart compares **land sale asking price per aana** only. It shows sample counts and makes no market-value prediction.
- Proximity score: `50 * max(0, 1 - school_distance/radius) + 50 * max(0, 1 - hospital_distance/radius)`. Unenriched properties have no score. Comparisons require the same radius.
- Heatmap uses unique facility identifiers across the filtered properties, excluding road segments. It is sampled OSM coverage around those properties, not a complete valley census. Duplicate real-world facilities represented by different OSM objects may remain.
- Public geocoding results can return Nepali district names; both Nepali and English district names are recognized. A unique place feature is preferred over a same-named road or temple, and the location remains explicitly approximate.
- Table: 25 rows/page. Map: maximum 3,000 filtered pins (explicit truncation notice); heatmap: up to 10,000 facility points. CSV exports all filtered records with spreadsheet formula escaping.

## Verify

```powershell
.\.venv\Scripts\python.exe -m pytest -q
cd frontend
npm run build
```

Tests use temporary databases, synthetic HTML and mocked geocoding/HTTP responses. They cover units, ambiguous values, field extraction, pagination discovery, source gates, robots/redirect denial, cache use, district/ambiguity checks, road geometry, filters, unknown values, demo isolation and CSV safety. Separate live validation collected 7 actual properties; the fixture tests alone are not claimed as live proof.

## Project layout

```text
land_discover/
  api.py          Read-only API and built frontend serving
  cli.py          Init, seed, scrape, import and enrich commands
  db.py           SQLite schema, transactions, cache and upserts
  normalize.py    Conservative price/size/date normalization
  scraper.py      Semantic/JSON-LD adapters and bounded crawl engine
  hamrobazar.py   Live-validated public Hamrobazar HTML adapter
  policy.py       Stable reviewed policy text fingerprint
  export.py       Standalone filtered CSV writer
  sources.py      Audited source inventory and blockers
  http.py         Rate limiting, retries and robots enforcement
  geo.py          Nominatim/Overpass and distance calculations
  demo.py         Explicit synthetic sample dataset
  locking.py      Process locks for serialized batches
frontend/src/     React dashboard and styles
tests/            Offline pipeline/API tests
docs/SOURCES.md   Source review evidence and next steps
```

This is a local single-operator app. It binds to loopback; collection is CLI-only. Hosting requires a Python runtime and persistent SQLite storage, which the existing static marketing site does not provide. Add authentication and operational hardening before exposing the API beyond a trusted environment. This app has not been deployed over the existing landing page.

Map tiles and data: [OpenStreetMap contributors, ODbL](https://www.openstreetmap.org/copyright). Follow the [Nominatim policy](https://operations.osmfoundation.org/policies/nominatim/), [OSM tile policy](https://operations.osmfoundation.org/policies/tiles/), and [Overpass public-instance guidance](https://dev.overpass-api.de/overpass-doc/en/preface/commons.html). Leaflet tiles are fetched only for the visible view; there is no tile prefetching/offline download.
