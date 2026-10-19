import json
import pytest
from fastapi.testclient import TestClient
from land_discover.contacts import extract_contact
from land_discover.api import app
from land_discover.db import connect, upsert
from land_discover.normalize import normalize
from land_discover.geo import parse_amenities
from land_discover.scraper import parse_detail


def test_public_owner_phone_excludes_office_and_hidden():
    html = '''<footer><p>Owner contact: 9800000001</p></footer>
    <main><p hidden>Owner contact: 9800000002</p>
    <p>Owner contact: +977 9800000003</p></main>'''
    result = extract_contact({}, html)
    assert result['contact_phone'] == '+9779800000003'
    assert result['contact_role'] == 'owner'


def test_agent_is_not_claimed_to_be_owner():
    html = '<main><div class="agent-contact"><a href="tel:9800000004">9800000004</a></div></main>'
    result = extract_contact({}, html)
    assert result['contact_phone'] == '9800000004'
    assert result['contact_role'] == 'agent'


def test_realhomes_agent_sidebar_outside_main():
    html = '''<header><a href="tel:9800000001">9800000001</a></header>
    <main><h1>House for sale</h1></main><aside class="rh_sidebar">
    <section class="rh_property_agent"><p class="contact mobile"><a href="tel:+9779800000002">+9779800000002</a></p></section>
    </aside>'''
    result = extract_contact({}, html)
    assert result['contact_phone'] == '+9779800000002'
    assert result['contact_role'] == 'agent'


def test_visible_listing_phone_without_custom_css_class():
    html = '<main><div><h3>Contact owner</h3><a href="tel:9800000003">9800000003</a></div></main>'
    result = extract_contact({},html)
    assert result['contact_phone'] == '9800000003'
    assert result['contact_role'] == 'owner'


def test_partially_masked_phone_is_not_saved():
    assert extract_contact({},'<main><p>Owner contact: 9800000***</p></main>')['contact_phone'] is None


@pytest.mark.parametrize('html', [
    '<p>Owner contact: 98XXXXXXXX</p>',
    '<div class="owner-contact"><a href="tel:9800000000">98********</a></div>',
    '<div style="display: none">Owner contact: 9800000000</div>',
    '<div class="related-properties"><p>Owner contact: 9800000000</p></div>',
])
def test_masked_hidden_and_unrelated_contacts_are_unknown(html):
    assert extract_contact({}, html)['contact_phone'] is None


def test_scraped_contact_and_source_price(raw):
    html = '''<main><h1>House for sale</h1><dl><dt>Location</dt><dd>Baneshwor, Kathmandu</dd>
    <dt>Price</dt><dd>25 lakh</dd><dt>Owner Phone</dt><dd>9800000005</dd></dl></main>'''
    result = parse_detail(html, raw['source_url'], 'fixture')
    assert result['contact_phone'] == '9800000005'
    assert result['contact_role'] == 'owner'
    assert result['price_raw'] == '25 lakh'
    assert result['price_npr'] == 2500000
    assert normalize({**raw, 'price_raw':''})['price_npr'] is None
    identifier = upsert(result)
    with connect() as con:
        saved = con.execute('SELECT contact_phone,contact_role FROM properties WHERE id=?',(identifier,)).fetchone()
    assert saved['contact_phone'] == '9800000005' and saved['contact_role'] == 'owner'


def test_missing_source_price_is_not_required_or_invented(raw):
    data = {'@type':'RealEstateListing','name':'House for sale in Kathmandu',
            'address':'Baneshwor, Kathmandu', 'offers':{},
            'description':'Residential house with garden and direct road access.'}
    html = '<h1>House for sale in Kathmandu</h1><script type="application/ld+json">'+json.dumps(data)+'</script>'
    result = parse_detail(html, raw['source_url'], 'tradenepal')
    assert result['price_npr'] is None and result['total_price_npr'] is None


def test_one_or_two_km_facilities_and_coverage(raw):
    identifier = upsert({**normalize(raw), 'image_url':'https://example.org/photo.jpg',
                         'enrichment_status':'complete','enrichment_radius_m':2000})
    with connect() as con:
        for index, distance in enumerate((0.5, 1.5, 2.1)):
            con.execute('INSERT INTO amenities(property_id,osm_id,name,kind,lat,lng,distance_km) VALUES(?,?,?,?,?,?,?)',
                        (identifier, f'node/{index}', 'Hospital', 'hospital', 27.7, 85.3, distance))
    with TestClient(app) as client:
        one = client.get(f'/api/properties/{identifier}?radius_m=1000').json()
        two = client.get(f'/api/properties/{identifier}?radius_m=2000').json()
        assert len(one['amenities']) == 1 and len(two['amenities']) == 2
        assert two['facilities_complete'] is True
        assert client.get(f'/api/properties/{identifier}?radius_m=3000').status_code == 422
        with connect() as con:
            con.execute('UPDATE properties SET enrichment_radius_m=1000 WHERE id=?',(identifier,))
        assert client.get(f'/api/properties/{identifier}?radius_m=2000').json()['facilities_complete'] is False


def test_department_stores_exclude_residential_buildings():
    elements = [dict(type='node',id=i,lat=27.7001,lon=85.3,tags=tags) for i,tags in enumerate([
        {'shop':'department_store'}, {'building':'house'}, {'building':'apartments'},
        {'building':'apartments','amenity':'hospital'},
    ])]
    assert [item['kind'] for item in parse_amenities(elements,27.7,85.3,2000)] == ['department_store','hospital']
