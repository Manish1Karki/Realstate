# Kathmandu property price research

Research date: 6 October 2026. Scope: Kathmandu **district**, with municipalities and neighbourhoods kept separate; Lalitpur and Bhaktapur are excluded. This is a feasibility study and a small advertised-price sample, not a valuation of a particular parcel. No application changes, listing imports, commits or deployments were made for this research.

## What the system can establish

Government minimum registration values and public seller asking prices can be collected and compared, provided the exact location, access and property type are known. Actual completed-sale prices require another evidence source. Public advertisements alone do not establish what buyers paid.

Keep these measures separate:

| Measure | Meaning | Proposed treatment |
|---|---|---|
| Government minimum | Annual minimum valuation used for registration | Office-specific, fiscal-year-specific rule lookup, with source page and matching conditions |
| Asking price | Seller's advertised amount | Normalize price basis and compare similar properties; label as advertised |
| Declared transaction value (Thaili) | Amount declared at the Land Revenue Office for taxation | Preserve as a declared amount, not independently verified consideration |
| Verified completed-sale consideration | Evidence of the amount actually agreed/paid | Separate dataset; record verification method and date |

NRB explicitly defines Thaili as a tax-declared value. Its April 2026 report uses administrative transaction data. The newer September 2026 publication gives aggregate transaction activity; neither of the reviewed publications supplies a public list of verified closing prices for individual Banasthali parcels. I did not find an open, parcel-level Kathmandu dataset that resolves that gap. Sources: [NRB report, PDF page 4, footnote 1](https://www.nrb.org.np/contents/uploads/2026/04/A-Report-on-the-Status-of-Real-Estate-Market-in-Nepal.pdf#page=4), [latest reviewed quarterly report](https://www.nrb.org.np/contents/uploads/2026/09/Real-Estate-Report-2082-83Q4.pdf), [publication date and spreadsheet link](https://www.nrb.org.np/red/page/2/).

## Government rates checked against the original PDFs

These are **selected table rates**, in NPR lakh per aana, for FY 2083/84. They are not a complete office-wide rulebook or the final applied valuation of a specific property.

| Office / specified location | Table rate | Reference |
|---|---:|---|
| Kalanki: land directly adjoining Ring Road, Balkhu–Banasthali | 49.35 | PDF page 2, first table |
| Kalanki: Chamati housing area's paved roads, width over 8 m up to 11 m / over 4 m up to 8 m / up to 4 m | 23 / 21 / 17 | PDF page 3, ward 15, row 12 |
| Dillibazar: Banasthali–Balaju–Gongabu–Maharajgunj–Dhumbarahi–Dhobikhola specified Ring Road frontage | 40.65 | PDF page 3, row 3 |
| Dillibazar: specified New Road/Indrachowk frontage | 76.20 | PDF page 10, row 60 |
| Dillibazar: Putalisadak–Bagbazar–Ratnapark main-road frontage | 56.00 | PDF page 11, row 71 |

Primary sources: [Kalanki 2083/84 PDF](https://kalanki.dolma.gov.np/uploads/document/178412427808384%20%E0%A4%AE%E0%A5%81%E0%A4%B2%E0%A5%8D%E0%A4%AF%E0%A4%BE%E0%A4%95%E0%A4%A8.pdf), [Dillibazar 2083/84 PDF](https://dillibazar.dolma.gov.np/uploads/document/1785309496IMG_0014.pdf). Both were downloaded from links on their official office pages and visually checked; their scanned/OCR text cannot be trusted for automatic numeric extraction.

Kalanki decision 16 adds 10% for qualifying officially classified residential/commercial land. Other clauses govern frontage and previous valuations. An exact parcel lookup therefore needs the applicable clauses and local recommendation, not just a neighbourhood name. Source: [Kalanki PDF, pages 10–11](https://kalanki.dolma.gov.np/uploads/document/178412427808384%20%E0%A4%AE%E0%A5%81%E0%A4%B2%E0%A5%8D%E0%A4%AF%E0%A4%BE%E0%A4%95%E0%A4%A8.pdf#page=10).

### Conflicting reporting resolved for the selected Ring Road row

[Fiscal Nepal](https://www.fiscalnepal.com/2026/07/22/27080/govt-sets-new-land-valuation-in-kathmandu-prices-range-from-rs-143000-to-rs-7-62-million-per-aana/) reported 49.35 lakh, while [Khabarhub](https://english.khabarhub.com/2026/21/559628/) reported 43.50 lakh for Balkhu–Banasthali. The original Kalanki table reads **49.35 lakh**. The lesson is to digitize the official table and its conditions, rather than importing rates from news summaries.

Government reference retrievals:

- [Kalanki official current-document page](https://kalanki.dolma.gov.np/office/kalanki/content/%E0%A4%A8%E0%A5%8D%E0%A4%AF%E0%A5%81%E0%A4%A8%E0%A4%A4%E0%A4%AE-%E0%A4%AE%E0%A5%81%E0%A4%B2%E0%A5%8D%E0%A4%AF%E0%A4%BE%E0%A4%95%E0%A4%A8-083-84-1784124198). PDF SHA-256: `F26F93C3CE9D2608BF4001AB8216DDF0C28AD9369CAB25531995D6C057BF5035`.
- [Dillibazar official current-document page](https://dillibazar.dolma.gov.np/office/dillibazar/content/s-1784262219). PDF SHA-256: `5087913FCB5D2BECE992239F58B1EDCCB921AE1C70B5FAAD1EE36EBF9B71603D`.

These two documents do not cover every Kathmandu parcel. A district-wide feature needs the current schedules and jurisdiction mapping for all relevant offices, including Chabahil, Tokha and Manmaiju, with amendments checked before release.

## Advertised land prices found

This is a purposive sample of ten advertisements from two publishers, chosen to inspect variation and field quality. It is not a representative survey, an area average or a confirmed-sales dataset. Road and location descriptions are advertiser claims. Availability was not independently confirmed. Dates below are the dates displayed by the source, not proof of owner confirmation; older advertisements are context rather than current comparable evidence.

All prices below are **NPR lakh per aana**. Land sizes retain source notation where needed; R-A-P-D means ropani–aana–paisa–dam.

| Location | Asking rate | Advertised plot/access | Source update | Source |
|---|---:|---|---|---|
| Banasthali, toward Chamati | 80 | 17 aana; 20 ft pitched road; about 400 m inside Ring Road; commercial/godown marketing | 10 Aug 2026 | [GJB 3703](https://gharjaggabazar.com/property/details/banasthali/9325/1/) |
| Baniyatar Dhaneshwor | 38 | 0-5-1-0; 16 ft concrete/dhalan road; elevated plot | 17 Aug 2026 | [GJB 2890](https://gharjaggabazar.com/property/details/land-on-sale-at-baniyatar-dhaneshwor/7472/1/) |
| Baniyatar Dhaneshwor | 43 | 0-4-2-0; 12 ft road, surface unstated; 30 ft frontage; about 3.5 km from Gangabu Ring Road | 22 Jul 2026 | [GJB 3665](https://gharjaggabazar.com/property/details/baniyatar-dhaneshwor/9239/1/) |
| Baluwatar | 70 | 0-6-3-2; 10 ft road, surface unstated; residential marketing | 20 Sep 2026 | [GJB 3714](https://gharjaggabazar.com/property/details/land-on-sale-at-baluwatar/9354/1/) |
| Thankot Nagdhunga | 18 | Two plots, 0-4-0-0 and 0-4-1-3; 16–18 ft road, surface unstated; about 150 m from check post | 31 Jul 2026 on detail page | [GJB 3739](https://gharjaggabazar.com/property/details/land-on-sale-at-thankot-nagdhunga/9412/1/) |
| Kapan Height | 38 | 0-6-1-0; 14 ft pitched road; colony access | 23 May 2026 | [GJB 3573](https://gharjaggabazar.com/property/details/land-on-sale-at-kapan-height/9021/1/) |
| Kattike Bhanjyang, Shankharapur | 15 | 3-14-1-0; main-road access, width/surface unstated; large resort-oriented plot, whole-plot purchase condition | 23 May 2026 | [GJB 3699](https://gharjaggabazar.com/property/details/kattike-bhanjyang/9320/1/) |
| Pepsicola | 65 | Description: 9 aana; 20 ft paved road; structured area field is inconsistent | 12 Mar 2026 | [Basobaas 16249](https://basobaas.com/property/land-on-sale-at-pepsicola-kathmandu-16249) |
| Gothatar | 47 | 4 aana 2 paisa; 13 ft paved road | 11 Mar 2026 | [Basobaas 16245](https://basobaas.com/property/land-on-sale-at-gothatar-kathmandu-16245) |
| Kirtipur, semi-commercial | 53 | 5 aana 1 paisa; 20 ft paved road; exact micro-location missing | 19 Mar 2026 | [Basobaas 16269](https://basobaas.com/property/semi-commercial-land-on-sale-at-kirtipur-kathmandu-16269) |

Interpretation: these examples demonstrate substantial advertised variation within Kathmandu. They do not establish neighbourhood price bands. The two Baniyatar plots show that a wider advertised road need not mean a higher asking rate. Other differences are uncontrolled. Banasthali's commercial plot is also a different product from a small residential plot. No causal road premium or government-to-market multiplier can be calculated from this sample.

## Houses need their own comparison

Two Kapan examples demonstrate why house prices should stay separate from bare-land rates:

| Advertised property | Total asking price | Details | Source date |
|---|---:|---|---|
| Kapan Akashedhara house | NPR 1.75 crore | 2.5 storeys; 0-2-2-1 land; 1,465 sq ft built area; 12 ft pitched road; bike parking only; construction 2073/74 BS | 29 Aug 2026; [detail page](https://gharjaggabazar.com/property/details/house-on-sale-at-kapan-akashedhara/9410/2/) |
| Kapan Lasuntar house | NPR 3.30 crore | Advertised new, 2.5 storeys; 0-3-2-2 land; 2,164 sq ft built area; 13 ft access; about 200 m inside main road | 6 Sep 2026; [publisher's Kapan results](https://gharjaggabazar.com/search/?location=kapan), detail fetch failed |

These are asking amounts for land plus buildings, not construction-cost estimates or completed sales. A future house estimate should account for land, built area, age, condition, approvals, parking and verified rental income. Dividing total house price by land area produces a combined-property ratio, not a bare-land value.

## Data problems that the prototype must handle

- **Sold does not reveal the settlement price.** [Gharbazar's Balaju–Banasthali–Kharibot advertisement](https://www.gharbazar.com/property/details/land-at-balaju-banasthali-kharibot-9564) displays Sold and a 52.5 lakh/aana advertisement. It is excluded from current comparisons and cannot establish a sale at that amount.
- **Refreshing a page is not refreshing the offer.** Baniyatar GJB 2890 first appeared in 2022 despite its 2026 update. Thankot's index and detail page show different update dates. Keep first-posted, last-source-update, last-observed and last-owner-confirmed separately. Sources: their individual pages linked above and [Thankot index date](https://gharjaggabazar.com/property/details/land-on-sale-at-kapan-height/9021/1/).
- **Structured fields can contain unit errors.** Pepsicola's description says 9 aana while the structured square-foot field says 9. Its EMI calculator also treats the per-aana number as a total. Use explicit price basis and cross-check fields; quarantine contradictions instead of silently trusting the calculator. [Pepsicola source](https://basobaas.com/property/land-on-sale-at-pepsicola-kathmandu-16249).
- **District names in titles are not dependable.** A [Basobaas Tikathali title says Kathmandu](https://basobaas.com/property/land-on-sale-at-tikathali-kathmandu-16247), but the description identifies Lalitpur. It was excluded. Confirm administrative geography before selecting comparables.
- **Large plots have different purchase conditions.** Kattike's price requires buying the whole plot; it should not price a four-aana residential parcel.
- **One property can appear on multiple sites.** Deduplicate by location, size, photos where authorized, description and advertiser evidence. Count independent properties, not copied advertisements.

## Proposed fields and comparison method — not implemented

| Group | Fields to record | Why |
|---|---|---|
| Location | District, municipality, current ward, former ward/VDC, neighbourhood, landmark, coordinates and precision | Separate similar names and identify the correct government jurisdiction/rule |
| Road | Width and unit, paved/concrete/gravel/earth/footpath/unknown, direct frontage or inner parcel, main-road distance, narrowest approach, legal/public/private/shared access | Describe usable access; width in a photograph is not proof of a legal road |
| Land | Area and unit, frontage, shape, slope, drainage/flood exposure, utilities, verified land-use classification, encumbrances where documented | Establish buildability and appropriate comparison group |
| Building | Property type, built area, age, floors, condition, parking, approvals, occupancy and rental evidence | Separate land, houses, flats and commercial buildings |
| Evidence | Source URL/ID, raw price basis, dates, availability, field conflicts, duplicate group, verification level | Make estimates reproducible and avoid inventing missing information |
| Government lookup | Office, FY, route/segment, schedule row/page, base rate, clause adjustments, evidence of rule match | Distinguish a table entry from an applied parcel valuation |

The model should use **micro-locations**, rather than assigning one number to Banasthali or all of Kathmandu. Proposed descriptive groups are central commercial corridors, established residential neighbourhoods, developing suburban areas and peripheral locations. These are research labels for comparison; they must not be confused with official land-use classifications or inferred solely from a municipality name.

Start with a manually reviewed pilot in Banasthali–Balaju–Chamati, then one residential and one peripheral cluster. Match property type, micro-location, road/frontage, plot-size range and recency. Show a median and spread only after obtaining enough independent comparable records; otherwise show individual examples and "insufficient comparable data". A tentative minimum of five well-matched properties is a pilot operating rule to validate, not a statistical guarantee. Avoid pooling peripheral resort land with central residential plots.

Do not hard-code rules such as "market value = government value × 2", "20-foot road adds 30%", or a uniform negotiation discount. Calibrate any future adjustments against documented comparable evidence. This research sample is too small and biased to train a reliable price-prediction model.

The property screen could eventually show:

1. **Government minimum:** matched fiscal year/rule, with base versus applicable adjustments and a source.
2. **Comparable asking prices:** date range, independent property count, road/location match and observed spread.
3. **Verified completed sales:** show only when supported by evidence; otherwise "not available".

## Feasibility and remaining work before implementation

| Capability | Assessment |
|---|---|
| Annual government reference table | Feasible with manual review of scans, fiscal-year versioning and office coverage; selected rows verified here |
| Automatic asking-price monitoring | Feasible for accessible, permitted sources; extraction must retain dates, units, unknowns and contradictions |
| Kathmandu-wide market valuation | Not established by this sample; needs broader, independently verified comparables |
| Automatic actual-sale-price discovery | No adequate open dataset found in this research; explore an authorized administrative feed and consenting broker/owner evidence |
| Reliable house valuation | Requires building data and a separate comparison model |

Before building: finish official office coverage and amendment checks; obtain exact access/location fields; broaden and verify comparables; test deduplication and date/unit conflicts; validate the proposed display with local property professionals. Agree on how actual sale evidence will be obtained and verified. Research access to public advertisements does not by itself authorize bulk republication; supported feeds and source agreements remain preferable for expansion. The existing source-access findings are in [SOURCE_EXPANSION.md](SOURCE_EXPANSION.md) and [SOURCES.md](SOURCES.md).

The practical first product is an auditable Kathmandu government-rate reference plus a comparison of similar advertised properties. Verified settlement-price estimates should follow once the missing transaction evidence exists.
