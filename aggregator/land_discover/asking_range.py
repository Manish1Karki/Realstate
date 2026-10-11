"""An auditable comparable asking-price prototype, not a sale valuation model."""
import json
import math
import re
import statistics
from collections import Counter
from datetime import date, timedelta

from .normalize import AANA_SQFT, DIGITS

MIN_COMPARABLES = 5
MAX_AGE_DAYS = 180
ROAD_TOLERANCE_FT = 4


def neighbourhood(value):
    value = re.sub(r'\s+', ' ', str(value or '').strip().casefold())
    return {'banastali': 'banasthali', 'banasthali': 'banasthali'}.get(value, value)


def road_details(note):
    text = str(note or '').translate(DIGITS).casefold()
    widths = re.findall(r'(\d+(?:\.\d+)?)\s*(?:ft\b|feet\b|foot\b|फिट)', text)
    # Ranges and multiple access roads need verification, not a guessed width.
    width = float(widths[0]) if len(widths) == 1 and not re.search(r'\d\s*[-–]\s*\d', text) else None
    surfaces = []
    for surface, words in {
        'asphalt': ('pitched', 'blacktop', 'asphalt'),
        'concrete': ('concrete', 'dhalan', 'ढलान'),
        'gravel': ('gravel', 'gravelled', 'graveled'),
        'earth': ('earthen', 'dirt road', 'unpaved'),
    }.items():
        if any(word in text for word in words): surfaces.append(surface)
    surface = surfaces[0] if len(surfaces) == 1 else None
    inner = bool(re.search(r'\binside\b|\binner\b|\bkittas?\s+(?:inside|in)\b', text))
    direct = bool(re.search(r'\b(?:direct|main[- ]road|highway)\s+frontage\b|\bdirectly adjoining (?:the )?(?:main road|highway)', text))
    frontage = 'inner' if inner and not direct else 'main_road' if direct and not inner else None
    return width, surface, frontage


def unit_price(row, area):
    try:
        price = float(row.get('price_npr') or 0)
        basis = row.get('price_basis')
        if basis == 'per_aana': value = price
        elif basis == 'per_ropani': value = price / 16
        elif basis == 'per_sqft': value = price * AANA_SQFT
        elif basis == 'total': value = float(row.get('total_price_npr') or price) / area
        else: return None
        return value if math.isfinite(value) and value > 0 else None
    except (TypeError, ValueError, ZeroDivisionError): return None


def percentile(values, fraction):
    position = (len(values) - 1) * fraction
    lo, hi = math.floor(position), math.ceil(position)
    return values[lo] + (values[hi] - values[lo]) * (position - lo)


def illustrative_listings(today):
    """Synthetic comparables never written to the property database."""
    rows = []
    for index, (size, width, price) in enumerate(((3.5, 12, 4200000), (4, 14, 4500000), (4.5, 16, 4700000), (5, 16, 4900000), (5.5, 18, 5200000), (6, 20, 5500000))):
        rows.append(dict(id=f'example-{index+1}', source='Illustrative example', source_url='',
                         title=f'Example plot {chr(65+index)}', area_name='Banasthali', district='Kathmandu',
                         property_type='land', transaction_type='sale', is_demo=1,
                         size_sqft=size*AANA_SQFT, price_npr=price, price_basis='per_aana',
                         listing_date=(today-timedelta(days=10+index*9)).isoformat(),
                         road_access_note=f'{width} ft asphalt road; inner residential plot',
                         description='Synthetic residential plot for demonstrating the comparison.', quality_flags=[]))
    return rows


def estimate(rows, subject, today=None):
    today = today or date.today()
    example = subject['mode'] == 'example'
    excluded, matches, seen_urls, seen_fingerprints = Counter(), [], set(), set()
    for raw in rows:
        row = dict(raw)
        reason = None
        if row.get('is_demo') and not example: reason = 'Synthetic property'
        elif row.get('district', '').casefold() != 'kathmandu': reason = 'Outside Kathmandu'
        elif row.get('property_type') != 'land' or row.get('transaction_type') != 'sale': reason = 'Not land for sale'
        elif neighbourhood(row.get('area_name')) != neighbourhood(subject['neighbourhood']): reason = 'Different neighbourhood'
        if reason:
            excluded[reason] += 1
            continue
        flags = row.get('quality_flags') or []
        if isinstance(flags, str):
            try: flags = json.loads(flags)
            except (ValueError, TypeError): flags = ['Unreviewed quality flags']
        text = ' '.join((str(row.get('title') or ''), str(row.get('description') or ''), ' '.join(map(str, flags)))).casefold()
        if re.search(r'\bsold\b|\bsoldout\b|\bexpired\b|\bconflict\w*\b|\bambiguous\b|\bunreviewed\b', text):
            excluded['Availability or data needs review'] += 1
            continue
        if re.search(r'\bcommercial\b|\bgodown\b|\bresort\b|\bagricultur\w*\b', text):
            excluded['Different intended use'] += 1
            continue
        try:
            listed = date.fromisoformat(str(row.get('listing_date') or ''))
            age = (today-listed).days
        except ValueError:
            excluded['Listing date unknown'] += 1
            continue
        if not 0 <= age <= MAX_AGE_DAYS:
            excluded['Old or future listing date'] += 1
            continue
        try: area = float(row.get('size_sqft') or 0) / AANA_SQFT
        except (TypeError, ValueError): area = 0
        if not math.isfinite(area) or area <= 0:
            excluded['Plot size unknown'] += 1
            continue
        if not subject['size_aana']*.5 <= area <= subject['size_aana']*2:
            excluded['Different plot-size band'] += 1
            continue
        price = unit_price(row, area)
        if price is None:
            excluded['Price or price basis unknown'] += 1
            continue
        width, surface, frontage = road_details(row.get('road_access_note'))
        if width is None or surface is None or frontage is None:
            excluded['Road details incomplete'] += 1
            continue
        if abs(width-subject['road_width_ft']) > ROAD_TOLERANCE_FT or surface != subject['road_surface'] or frontage != subject['frontage']:
            excluded['Different road access'] += 1
            continue
        url = str(row.get('source_url') or '').split('#')[0].rstrip('/')
        fingerprint = (neighbourhood(row['area_name']), round(area, 3), round(price), width, surface, frontage)
        if (url and url in seen_urls) or fingerprint in seen_fingerprints:
            excluded['Possible duplicate'] += 1
            continue
        if url: seen_urls.add(url)
        seen_fingerprints.add(fingerprint)
        matches.append(dict(id=row['id'], title=row['title'], source=row['source'], source_url=url,
                            listing_date=listed.isoformat(), size_aana=round(area, 3),
                            per_aana_npr=round(price), road_width_ft=width, road_surface=surface, frontage=frontage))
    matches.sort(key=lambda row: (row['per_aana_npr'], str(row['id'])))
    prices = [row['per_aana_npr'] for row in matches]
    ready = len(matches) >= MIN_COMPARABLES
    result = dict(status='ready' if ready else 'insufficient_data', mode=subject['mode'],
                  as_of=today.isoformat(), subject=subject, comparable_count=len(matches),
                  minimum_comparables=MIN_COMPARABLES, comparables=matches,
                  excluded=[dict(reason=key, count=value) for key, value in sorted(excluded.items())],
                  range=None, evidence='Illustrative only' if example else 'Unverified asking prices',
                  policy=dict(max_age_days=MAX_AGE_DAYS, road_tolerance_ft=ROAD_TOLERANCE_FT,
                              plot_size_min_ratio=.5, plot_size_max_ratio=2),
                  limitations=['These are seller asking prices, not completed-sale values.',
                               'The range is the middle 50% of matched asking rates, not a statistical confidence interval.',
                               'Location and road details have not been independently verified.',
                               'Matching thresholds are provisional prototype rules; duplicate detection is conservative.'])
    if example: result['limitations'].insert(0, 'All example properties and prices are fictional; this is not a Banasthali market estimate.')
    if ready:
        low, high = percentile(prices, .25), percentile(prices, .75)
        result['range'] = dict(low_per_aana_npr=round(low), high_per_aana_npr=round(high),
                              median_per_aana_npr=round(statistics.median(prices)),
                              low_total_npr=round(low*subject['size_aana']), high_total_npr=round(high*subject['size_aana']),
                              observed_min_per_aana_npr=min(prices), observed_max_per_aana_npr=max(prices))
    return result
