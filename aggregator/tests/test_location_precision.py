import json
from land_discover.source_location import extract_public_coordinates


def test_original_pin_precision_is_preserved():
    lat=27.653996123456
    lng=85.303110345678
    html='<script type="application/ld+json">'+json.dumps({
        '@type':'RealEstateListing','geo':{'@type':'GeoCoordinates','latitude':lat,'longitude':lng}
    })+'</script>'
    assert extract_public_coordinates(html)==(lat,lng)


def test_conflicting_pins_do_not_choose_an_arbitrary_location():
    html=''.join('<script type="application/ld+json">'+json.dumps({
        '@type':'RealEstateListing','geo':{'latitude':lat,'longitude':lng}
    })+'</script>' for lat,lng in [(27.653996,85.3031103),(27.7,85.35)])
    assert extract_public_coordinates(html) is None


def test_missing_pin_never_uses_demo_coordinates():
    assert extract_public_coordinates('<h1>House in Bhaisepati</h1>') is None
