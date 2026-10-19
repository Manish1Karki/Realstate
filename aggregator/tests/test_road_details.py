import pytest
from land_discover.road import extract
from land_discover.scraper import parse_detail
from land_discover.db import upsert, connect
from land_discover.api import decode
from land_discover.geo import parse_amenities, enrich


@pytest.mark.parametrize('note,surface,pitched', [
    ('20 feet blacktopped road', 'asphalt', True),
    ('16 ft gravel road', 'gravel', False),
    ('Concrete road', 'concrete', True),
    ('Paved road', None, True),
    ('Road will be pitched', None, None),
    ('Not pitched road', None, False),
    ('Asphalt and gravel road', None, None),
    ('Road access available', None, None),
])
def test_surface_evidence(note, surface, pitched):
    item = extract({'road_access_note': note}, {})
    assert item['road_type'] == surface
    assert item['road_is_pitched'] is pitched


def test_construction_is_for_road():
    item = extract({'description': 'House under construction with 20 ft pitched road.'}, {})
    assert item['road_under_construction'] is None
    assert extract({'description': 'Access road is under construction.'}, {})['road_under_construction'] is True
    assert extract({'road_access_note': 'Road not under construction'}, {})['road_under_construction'] is False
    assert extract({}, {'road status': 'Completed'})['road_under_construction'] is False


def test_width_and_nearby_are_not_guessed():
    assert extract({'road_access_note': '16-20 ft road'}, {})['road_width_ft'] is None
    assert extract({'description': 'Located 200 feet from a pitched road.'}, {})['road_type'] is None


def test_scraper_storage_and_api(raw):
    html = '''<main><h1>Land for sale</h1><dl>
    <dt>Location</dt><dd>Baneshwor, Kathmandu</dd>
    <dt>Road Size (ft)</dt><dd>20</dd><dt>Road Type</dt><dd>Blacktopped</dd>
    <dt>Road Status</dt><dd>Under construction</dd></dl></main>'''
    item = parse_detail(html, raw['source_url'], 'fixture')
    identifier = upsert(item)
    with connect() as con:
        result = decode(con.execute('SELECT * FROM properties WHERE id=?', (identifier,)).fetchone())
    assert result['address'] == 'Baneshwor, Kathmandu'
    assert result['road_width_ft'] == 20
    assert result['road_type'] == 'asphalt'
    assert result['road_is_pitched'] is True
    assert result['road_under_construction'] is True


def test_facilities_inside_one_kilometre_only():
    elements = [dict(type='node', id=i, lat=27.7+offset, lon=85.3, tags=tags)
                for i, (offset, tags) in enumerate([
                    (0.001, {'amenity':'pharmacy'}),
                    (0.002, {'shop':'supermarket'}),
                    (0.003, {'leisure':'park'}),
                    (0.01, {'amenity':'school'}),
                ])]
    result = parse_amenities(elements, 27.7, 85.3, 1000)
    assert {row['kind'] for row in result} == {'pharmacy','market','park'}
    assert all(row['distance_km'] <= 1 for row in result)
