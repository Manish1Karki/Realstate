# Automatic source collection ? 3 October 2026

The aggregator now runs a background collection cycle on every backend startup.
No user-supplied property links are needed. Enabled sources:

| Source | Discovery | Detail adapter | Collected fields |
|---|---|---|---|
| [Hamrobazar](https://hamrobazaar.com/) | Existing public real-estate category, `/detail/` anchors | Existing Product schema and visible specifications adapter | Public property information, description and photos |
| [HUKU Real Estate](https://www.hukurealestate.com/) | Public homepage `/properties/<numeric-id>` anchors; category URLs excluded | RealEstateListing schema plus visible header, Features and Description | Price/basis, address, type, sale/rent, size, room counts, date, road notes, image URLs and description |

HUKU's [robots.txt](https://www.hukurealestate.com/robots.txt) permits public
pages and disallows `/admins/` and `/api/`. Its published
[terms](https://www.hukurealestate.com/terms-and-services) were reviewed live;
no explicit prohibition of bounded automated public-page access was present.
The stable `.prose` policy content is fingerprinted and rechecked before every
batch. This inspection does not assert a commercial redistribution license.
Live parser checks covered rental 1560, house 1558 and land 1538. A schema
SoldOut value can conflict with the advertised page; the adapter retains a
quality flag for verification instead of inventing an availability state.

Both adapters keep unknown prices/units unknown. Named-source review gates and
robots checks remain in effect. Other sources listed in the historical audit
below remain disabled. Collection status and saved listing counts appear under
Data sources; logs are in `data/automatic-collection.log`.

---

# Source audit — 26 September 2026

A live Hamrobazar batch imported 7 real Kathmandu Valley records on 26 September 2026, skipped 5 unsupported/out-of-area listings and had no parsing failures. The user confirmed there are no source agreements. Hamrobazar is enabled only for bounded local public-HTML collection; no commercial redistribution rights are asserted. Sources with explicit permission restrictions remain disabled.

| Source | Observed rules/structure | Implementation status |
|---|---|---|
| [Hamrobazar](https://hamrobazaar.com/) | `robots.txt` permits public pages and disallows `/api/`, profile/settings/login. Public category contains `/detail/…` anchors; detail pages have Product JSON-LD, visible description/specifications and Posted metadata. | Live adapter enabled. Extracts category, asking amount, public address text, explicit-unit sizes and approximate Posted date. A batch imported 7 records. No current HTML next-page link; API infinite scrolling is not used. |
| [Housing Nepal](https://www.housingnepal.com/terms_and_conditions) | Robots available, but Terms “Restrictions on Use” prohibit automated viewing without consent, data copying without consent, and nonpersonal reuse. | Permission required; no listing selectors fabricated. |
| [Nepal Property Bazaar](https://nepalpropertybazaar.com/terms-and-conditions/) | Robots available; WordPress-style homepage links. Terms clause 3.1 limits reuse to personal noncommercial use and requires prior written permission otherwise. | Permission required for this aggregator's redistribution use. No detail adapter claimed. This is one possible interpretation of “Nepal Property,” not a confirmed exact source. |
| [Gharbazar](https://www.gharbazar.com/) | Robots includes a sitemap and no disallow entries. Listing pages use `/property/details/…`, H1 titles, H2 Rs. prices and labelled fields. Listing footers prohibit copying/reproduction of images and information. Homepage listings are not exposed as ordinary detail anchors in the inspected HTML. | Permission required. Offline semantic parser available; live discovery/pagination must be implemented and validated after consent. Not an enabled alternative to Hamrobazar. |
| GharBeta | No official Nepal property source/domain verified under this exact name. | Needs the user's exact URL. No guessed domain or selectors. |

Hamrobazar's [published terms](https://hamrobazaar.com/terms), fetched and read live, are Seller Program Terms updated August 17, 2026 and refer to broader Platform Terms. No explicit automated public-page access prohibition was found on the reviewed page. Its stable visible policy section is fingerprinted in the source configuration and checked again before collection; a changed policy or expired review stops collection. This narrow public-access review is not an assertion of a license to republish listings, images or descriptions. Review broader use before a commercial launch.

The first inspection attempt was declined, but the user subsequently explicitly requested a real internet scraper, and approved renewed live inspection and a bounded collection run. No restricted-site access or login bypass was used.

The current adapter uses `script[type="application/ld+json"]` for the Product record, a section headed “About this listing” for visible description, the two-column grid in “Specifications,” and `[data-testid="product-meta-chip"]` for Posted metadata. No hidden hydration data or seller profiles are accessed. The current adapters retain public property photos and descriptions; this supersedes the original metadata-only output.

## Enabling a source after permission and validation

1. Resolve the exact source/domain and applicable terms. Obtain written consent where required; retain the evidence locally. No login, CAPTCHA, private endpoint or robots bypass is implemented.
2. Inspect permitted category/detail and pagination pages. Check at least several examples covering land/house/apartment, total/unit prices, missing price/size, dates and out-of-Valley locations. Do not collect seller phone/email information.
3. Save sanitized, minimal HTML fixtures with permission, update the source adapter, and compare normalized values to the visible originals. Current tests are synthetic; they are not this validation step.
4. Implement a missing source adapter/start page only from verified structure. Hamrobazar already has a live-specific adapter. Gharbazar has an offline semantic parser only; the other restricted sources deliberately have `adapter: null`.
5. For an additional permission-required source, copy `source_reviews.example.json` to `source_reviews.json`. Enter the validated source's `enabled`, `live_validated`, `reviewed_on`, `permission_evidence`, and `terms_sha256`. The additional-source hash covers the exact fetched terms HTML; a stable policy-section digest should be added after that source's DOM is verified. Hamrobazar uses its built-in reviewed visible-text fingerprint instead. Do not refresh any hash without reviewing the actual policy change.
6. Run a bounded validation batch, inspect raw/normalized output and quality flags, then run enrichment. Reviews expire after 30 days. Robots are refreshed at least daily and consulted before every page and redirect target.

The inventory is intentionally conservative: registering a source does not mean it works, and a failed run is logged rather than displayed as a successful empty scrape. `audit_sources.py` is a bounded reconnaissance utility; it is not a production scraper. Previously downloaded reconnaissance HTML is excluded from version control.

## Outstanding live acceptance checks

- Hamrobazar category/detail inspection and first-page batch: completed. Full pagination beyond the public HTML page remains unavailable; do not use `/api/` to fill that gap.
- Obtain source permissions before the remaining adapters are built/enabled.
- Nominatim/Overpass first live validation: completed for 7 collected properties using the existing Land Discover site URL as application contact. Four approximate place matches were enriched; 337 property-linked OSM feature rows were stored. Three vague/unresolved addresses remain unmapped. Provider data and approximate locations still need domain review before investment use.
- Configure your own `LAND_CONTACT` in `.env` for subsequent enrichment. Large recurring geocoding needs an appropriate provider; do not scale public Nominatim into a distributed bulk service.
