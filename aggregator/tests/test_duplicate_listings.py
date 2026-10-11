from fastapi.testclient import TestClient
from land_discover.api import app
from land_discover.db import upsert
from land_discover.normalize import normalize
from land_discover.eligibility import nepal_today


def test_duplicate_source_aliases_collapse_before_pagination(raw):
    item = {**normalize(raw), 'image_url': 'https://example.org/house.jpg', 'listing_date': nepal_today().isoformat()}
    first = upsert({**item, 'source_url': 'https://example.org/first'})
    upsert({**item, 'source_url': 'https://example.org/alias'})
    distinct = upsert({**item, 'source_url': 'https://example.org/different', 'price_npr': 123456})
    with TestClient(app) as client:
        result = client.get('/api/properties', params={'page_size': 1}).json()
        assert result['total'] == 2
        second = client.get('/api/properties', params={'page_size': 1, 'page': 2}).json()
        assert {result['items'][0]['id'], second['items'][0]['id']} == {first, distinct}
