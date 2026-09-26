# Land Discover

This repository contains two independent applications:

- [`LandingPage/`](LandingPage/): the existing marketing landing page.
- [`aggregator/`](aggregator/README.md): the Kathmandu Valley property scraper, FastAPI backend, SQLite storage, React dashboard, and tests.

See each application's README for setup and launch instructions. The aggregator runs independently and does not modify the landing page.

The aggregator collects public Hamrobazar listing fields, supports location enrichment with OpenStreetMap services, and separates real collected listings from optional synthetic demo data. It does not include an AI valuation or forecasting model. Source access limits and live validation evidence are documented in [`aggregator/docs/SOURCES.md`](aggregator/docs/SOURCES.md).

Databases, scraped CSV exports, credentials, installed dependencies, and generated dashboard builds are excluded from Git. A fresh clone starts without collected listings; follow the aggregator instructions to collect them locally.
