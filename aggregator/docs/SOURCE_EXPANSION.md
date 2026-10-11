# Local source expansion — 5 October 2026

The original system has two live adapters, Hamrobazar and HUKU. A source needs
working discovery, a detail parser, access checks, and live validation before it
can contribute listings. Hamrobazar's current HTML exposes one page; HUKU is
accessible locally but returns HTTP 403 from the hosted backend.

The following additional sources were checked from the development computer.
No commits, pushes, deployments, or writes to the hosted database were made.

| Source | Local observation | Decision |
|---|---|---|
| [eProperty Nepal](https://epropertynepal.com/) | Public sale/rental indexes, detail pages, property galleries and next-page links | Adapter is now disabled. A later successful review of the published terms found internal-use-only and no-publication/no-distribution restrictions; written permission is required. |
| [Nepal Bhoomi](https://nepalbhoomi.com/) | Public sale/rental indexes, detail galleries, labeled overview and next-page links | Local trial adapter implemented. Privacy policy inspected; no terms link found. Publication/reuse review still needed. Conflicting districts are rejected; missing/word-only prices remain unknown. |
| [Nepal Niwas](https://nepalniwas.com/terms) | Public listings are available, but terms restrict harvesting without authorization and copying content | Permission required; no collection adapter enabled. |
| [MLS Nepal](https://www.mlsnepal.com/terms) | Listings from multiple agencies; terms prohibit scraping without permission | Permission required; no collection adapter enabled. |
| [Merogarh](https://www.merogarh.com/terms/) | Public homepage; terms prohibit scraping | No collection adapter enabled. |
| [99aana](https://99aana.com/terms-conditions/) | Public listings; terms require written consent for automated listing extraction | Permission required; no collection adapter enabled. |
| [Maharjan Real Estate](https://maharjanrealestate.com/terms-conditions/) | Public listings; terms prohibit unauthorized reproduction/distribution | Permission required; no collection adapter enabled. |
| [Basobaas](https://basobaas.com/) | Listing index contains rendered text but no ordinary property-detail anchors; inspected detail had no readable listing body | Requires a supported feed or further public-page rendering investigation. No working adapter claimed. |
| [Kharid Bikri Sewa](https://kharidbikrisewa.com/) | Homepage returned a JavaScript application shell without listing links | Requires a supported feed or public rendering adapter; not enabled. |
| [Sandar](https://sandar.com.np/) | Three public sale listings; sample contains conflicting addresses and mismatched descriptions | Hold for data-quality and reuse review; not enabled. |
| [JaggaMitra](https://www.jaggamitra.com/) | robots URL returned HTML instead of usable rules | Access review incomplete; stopped before fetching listings. |
| [Nepal Homes](https://www.nepalhomes.com/) | robots URL returned HTML instead of usable rules | Access review incomplete; stopped before fetching listings. |
| [HomeLand](https://www.hlreb.com/) | robots URL returned HTML instead of usable rules | Access review incomplete; stopped before fetching listings. |
| [Mero Property](https://www.meroproperty.com/) | robots URL returned HTML instead of usable rules | Access review incomplete; stopped before fetching listings. |
| [Jagga Dalal](https://jaggadalal.com/) | DNS resolution failed locally | Unavailable during this check; no adapter enabled. |

Previously audited Housing Nepal, Gharbazar and Nepal Property Bazaar remain
disabled pending the permissions described in [SOURCES.md](SOURCES.md).

## Historical local validation results

The following figures are from the October 5 local parser trial, before the
eProperty Nepal terms page was successfully reviewed on October 8. They are not
an approved or publishable inventory. Do not display, export, or copy the
eProperty Nepal records into the public database without written permission.

| Source | Saved listing records | Records with photo URLs |
|---|---:|---:|
| Hamrobazar | 7 | 7 |
| HUKU | 18 | 18 |
| Nepal Bhoomi | 13 | 13 |
| Combined historical count, excluding eProperty Nepal | 38 | 38 |

The new adapters were each tested across three public index pages, including
page two, with a cap of 30 attempted detail URLs per source. eProperty Nepal's
batch completed; Nepal Bhoomi's batch was partial because one address named
conflicting districts and two source pages returned HTTP 500. These failures
were recorded, and collection continued. A wanted advert caught during initial
inspection was excluded from the trial database after its filter was corrected.

A subsequent backend startup historically completed a fresh cycle for all four
adapters with a small cap of three URLs each. That experiment was local only.
After the terms review, eProperty Nepal is excluded from future trial runs and
from any published inventory. The other historical observations do not establish
permission or hosted access for any source.

## Run the isolated trial

From `aggregator/`:

```powershell
.\.venv\Scripts\python.exe -m land_discover.source_trial --pages 4 --limit 30
```

This automatically discovers listings from enabled sources. It writes only to
`aggregator/data/source-expansion.sqlite3`, with a report in
`aggregator/data/source-expansion-report.json`. Both files are ignored by Git.
Choose `--sources nepalbhoomi` for a batch using only the remaining local-trial
adapter. Page and listing caps apply per source, not to the entire internet.
Requests observe robots rules and the existing three-second host throttle.

For the existing landing page and aggregator to show this trial database, run:

```powershell
# Terminal 1, from aggregator/: local API and automatic startup collection
.\.venv\Scripts\python.exe -m land_discover.source_trial --serve --pages 2 --limit 3

# Terminal 2, from the repository root
$env:LAND_DEV_API_URL='http://127.0.0.1:8010'
$env:LAND_DEV_AGGREGATOR_URL='http://127.0.0.1:5176'
npm.cmd run dev:landing -- --port 5175 --strictPort

# Terminal 3, from the repository root
$env:LAND_DEV_API_URL='http://127.0.0.1:8010'
npm.cmd --prefix aggregator/frontend run dev -- --base /aggregator/ --port 5176 --strictPort
```

Open `http://127.0.0.1:5175/properties` for property cards and
`http://127.0.0.1:5175/aggregator/` for the dashboard and collection history.
The small server example updates at most three listing URLs per source on each
restart; choose larger bounded limits for subsequent local experiments.

## Scope and limitations

`LAND_LOCAL_SOURCE_TRIAL=true` enables Nepal Bhoomi only with a local database.
Turso, Render, Vercel and hosted proxy settings prevent activation. The default
collector still uses Hamrobazar and HUKU. The trial launcher always selects its
separate database and rejects active cloud environment configuration. The raw
assessment HTML is private, ignored developer evidence under
`.review/source-expansion/`; it is not part of the site or its data API.

The new parsers exclude recommended-property photos, logos, owner contact fields,
wanted adverts and unsupported/out-of-Valley listings. Values not present or
ambiguous on a page remain unknown. Nepal Bhoomi records include a location and
availability review flag because some source fields conflict. Relative dates
are preserved as source text without inventing exact dates.

Repeat imports update the same source URL. A property advertised by two sites
can still produce two source records; cross-source property identity matching
is not implemented. Counts therefore measure source listing records, not
verified unique physical properties.

Before hosting a new source, resolve its publication/reuse conditions, validate
access from the hosted backend and review data quality. A successful local
parser does not establish hosted access or permission to republish photos.
