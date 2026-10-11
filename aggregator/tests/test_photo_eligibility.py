from fastapi.testclient import TestClient
from land_discover.api import app
from land_discover.db import upsert
from land_discover.normalize import normalize
from land_discover.eligibility import nepal_today


def test_public_properties_require_real_photo(raw):
    base = {**normalize(raw), 'listing_date': nepal_today().isoformat()}
    ids = []
    for index, (primary, gallery) in enumerate([
        (None, []), ('https://example.org/uploads/static/og-image.jpg', []),
        ('https://example.org/house.jpg', []), (None, ['https://example.org/land.jpg'])
    ]):
        ids.append(upsert({**base, 'title': 'Property '+str(index),
                           'source_url': 'https://example.org/'+str(index),
                           'image_url': primary, 'image_urls': gallery}))
    with TestClient(app) as client:
        result = client.get('/api/properties').json()
        assert result['total'] == 2
        assert {p['id'] for p in result['items']} == set(ids[2:])
        assert client.get('/api/properties/'+str(ids[0])).status_code == 404
        assert client.get('/api/summary').json()['total'] == 2
        assert {p['id'] for p in client.get('/api/sitemap').json()['items']} == set(ids[2:])
