# Estimated asking-price range prototype

The public comparison page is `/asking-price`. It compares land for sale in Kathmandu district. It estimates the distribution of **advertised asking rates**, not completed-sale value, government registration value or future appreciation.

## Two evidence modes

- **Illustrative example:** six fictional Banasthali plots demonstrate a complete result. The input note, result badge, comparable sources and result footnote identify them as fictional. They are generated in memory, never imported into the listing database, and cannot contribute to collected-mode estimates.
- **Collected listings:** reads the configured property database. It withholds the range when fewer than five eligible comparable records remain. It never falls back to fictional examples, other neighbourhoods, government multipliers or a fabricated premium.

## Provisional matching rules

The neighbourhood must match exactly after whitespace/case normalization; Banastali is an explicit alias of Banasthali. The comparison requires a known plot size between half and twice the subject size, a source listing date no more than 180 days old and not in the future, an explicit price basis, road width within four feet, the same recognized surface, and the same inner-plot versus direct main-road frontage.

Explicitly commercial, godown, resort and agricultural marketing is excluded. These exclusions do not establish official residential land-use status. Sold/expired/conflicting records and possible duplicates are excluded. Generic "paved" does not establish asphalt versus concrete. Multiple or ranged road widths and unclear frontage remain unknown. A fresh scrape does not count as owner confirmation or reset the source listing date.

Duplicate detection uses canonical source URLs and a conservative same-neighbourhood/size/price/road fingerprint. This can merge genuinely distinct similar plots and miss duplicates with changed details. The price module does not verify location, legal access, land-use classification, source availability or settlement prices. It should remain a prototype until those inputs and comparison rules have been validated.

## Output

`POST /api/asking-range` accepts:

```json
{
  "mode": "example",
  "neighbourhood": "Banasthali",
  "size_aana": 4,
  "road_width_ft": 16,
  "road_surface": "asphalt",
  "frontage": "inner"
}
```

The response contains the matched records, exclusion counts, method thresholds, evidence label and limitations. At five or more matches, the range is the 25th–75th percentile of normalized asking rates, using linear interpolation. The indicative total scales that rate range by the subject's area. It is not a statistical confidence interval or an adjustment-based appraisal. The median and full observed minimum/maximum are shown separately. Missing evidence returns `insufficient_data` and a null range.

Changing inputs marks the displayed result as outdated until Compare asking prices is selected again. The form supports explicit example/collected selection, incomplete-data states and retryable service errors. The comparable table links back to the app and original sources for collected records. Government and map features are not part of this calculation.

## Local preview

The development-only launcher `.review/preview-asking-price.py` clears cloud database settings, disables collection, and uses `aggregator/data/source-expansion.sqlite3`. The API runs at `http://127.0.0.1:8010`. Run the landing Vite server with `LAND_DEV_API_URL=http://127.0.0.1:8010` on port 5175, then open `http://127.0.0.1:5175/asking-price`.

No source agreements, government rates, listing imports, commits or deployments are changed by running a comparison. For evidence research and further validation requirements, see [KATHMANDU_PRICE_RESEARCH.md](KATHMANDU_PRICE_RESEARCH.md).
