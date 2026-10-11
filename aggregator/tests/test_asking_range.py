from copy import deepcopy
from datetime import date

import pytest
from fastapi.testclient import TestClient
from land_discover.api import app
from land_discover.asking_range import estimate, illustrative_listings, road_details
from land_discover.db import connect
from land_discover.normalize import AANA_SQFT

TODAY = date(2026, 10, 6)
SUBJECT = dict(mode='example', neighbourhood='Banasthali', size_aana=4,
               road_width_ft=16, road_surface='asphalt', frontage='inner')


def test_example_range_and_subject_total():
    result = estimate(illustrative_listings(TODAY), SUBJECT, TODAY)
    assert result['comparable_count'] == 6
    assert result['range']['low_per_aana_npr'] == 4550000
    assert result['range']['high_per_aana_npr'] == 5125000
    assert result['range']['median_per_aana_npr'] == 4800000
    assert result['range']['low_total_npr'] == 18200000
    assert result['range']['high_total_npr'] == 20500000
    assert result['range']['observed_min_per_aana_npr'] == 4200000
    assert 'fictional' in result['limitations'][0]


def test_four_matches_withhold_range_even_with_known_prices():
    result = estimate(illustrative_listings(TODAY)[:4], SUBJECT, TODAY)
    assert result['status'] == 'insufficient_data'
    assert result['range'] is None
    assert result['comparable_count'] == 4


def test_collected_mode_cannot_use_examples():
    result = estimate(illustrative_listings(TODAY), {**SUBJECT, 'mode': 'collected'}, TODAY)
    assert result['comparable_count'] == 0
    assert result['range'] is None


@pytest.mark.parametrize('change,reason', [
    ({'district': 'Lalitpur'}, 'Outside Kathmandu'),
    ({'property_type': 'house'}, 'Not land for sale'),
    ({'transaction_type': 'rent'}, 'Not land for sale'),
    ({'area_name': 'Baluwatar'}, 'Different neighbourhood'),
    ({'listing_date': None}, 'Listing date unknown'),
    ({'listing_date': '2025-01-01'}, 'Old or future listing date'),
    ({'listing_date': '2026-10-07'}, 'Old or future listing date'),
    ({'size_sqft': None}, 'Plot size unknown'),
    ({'size_sqft': 20*AANA_SQFT}, 'Different plot-size band'),
    ({'price_basis': 'unknown'}, 'Price or price basis unknown'),
    ({'price_npr': float('inf')}, 'Price or price basis unknown'),
    ({'road_access_note': '16 ft paved road, inner plot'}, 'Road details incomplete'),
    ({'road_access_note': '16 ft asphalt road'}, 'Road details incomplete'),
    ({'road_access_note': '16 ft concrete road; inner plot'}, 'Different road access'),
    ({'road_access_note': '30 ft asphalt road; inner plot'}, 'Different road access'),
    ({'description': 'Sold property'}, 'Availability or data needs review'),
    ({'quality_flags': '["SoldOut conflicts with page"]'}, 'Availability or data needs review'),
    ({'description': 'Commercial godown land'}, 'Different intended use'),
])
def test_incompatible_or_unreliable_record_is_excluded(change, reason):
    row = {**illustrative_listings(TODAY)[0], **change}
    result = estimate([row], SUBJECT, TODAY)
    assert result['comparable_count'] == 0
    assert result['excluded'] == [dict(reason=reason, count=1)]


def test_same_property_from_different_sources_is_not_counted_twice():
    rows = illustrative_listings(TODAY)
    copy = deepcopy(rows[0])
    copy.update(id='duplicate', source='Another source', source_url='https://example.com/copy')
    result = estimate(rows + [copy], SUBJECT, TODAY)
    assert result['comparable_count'] == 6
    assert {'reason': 'Possible duplicate', 'count': 1} in result['excluded']


@pytest.mark.parametrize('basis,price,total', [
    ('total', 14700000, 14700000), ('per_ropani', 67200000, None),
    ('per_sqft', 4200000/AANA_SQFT, None),
])
def test_supported_price_bases_normalize_to_aana(basis, price, total):
    row = {**illustrative_listings(TODAY)[0], 'price_basis': basis, 'price_npr': price, 'total_price_npr': total}
    result = estimate([row], SUBJECT, TODAY)
    assert result['comparables'][0]['per_aana_npr'] == 4200000


def test_alias_matches_but_does_not_expand_to_nearby_neighbourhood():
    rows = illustrative_listings(TODAY)
    result = estimate(rows, {**SUBJECT, 'neighbourhood': ' Banastali '}, TODAY)
    assert result['status'] == 'ready'
    assert estimate(rows, {**SUBJECT, 'neighbourhood': 'Banasthali Kharibot'}, TODAY)['range'] is None


def test_unknown_road_ranges_and_multiple_roads_are_not_guessed():
    assert road_details('12-16 ft asphalt road, inner plot')[0] is None
    assert road_details('16 ft asphalt and 12 ft concrete road, inner plot')[:2] == (None, None)
    assert road_details('१६ फिट ढलान बाटो; inner plot') == (16, 'concrete', 'inner')


def test_api_example_does_not_insert_properties():
    client = TestClient(app)
    with connect() as con: before = con.execute('SELECT COUNT(*) FROM properties').fetchone()[0]
    response = client.post('/api/asking-range', json=SUBJECT)
    assert response.status_code == 200
    assert response.json()['mode'] == 'example'
    assert response.json()['status'] == 'ready'
    with connect() as con: assert con.execute('SELECT COUNT(*) FROM properties').fetchone()[0] == before
    collected = client.post('/api/asking-range', json={**SUBJECT, 'mode': 'collected'}).json()
    assert collected['status'] == 'insufficient_data'
    assert collected['range'] is None


def test_api_rejects_invalid_subject():
    client = TestClient(app)
    for changed in ({'size_aana': 0}, {'road_width_ft': -1}, {'mode': 'sale'}, {'road_surface': 'unknown'}, {'neighbourhood': ' '}):
        assert client.post('/api/asking-range', json={**SUBJECT, **changed}).status_code == 422
