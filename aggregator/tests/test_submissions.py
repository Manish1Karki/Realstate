from fastapi.testclient import TestClient
from land_discover.api import app
from land_discover.db import init_db, connect


def submission(**changes):
    return dict(title='Family home in Bhaisepati', address='Ward 25, Bhaisepati',
                area_name='Bhaisepati', district='Lalitpur', property_type='house',
                transaction_type='sale', total_price_npr=25000000, size='4 aana',
                description='A bright family home with a private garden.',
                bedrooms=3, bathrooms=2, contact_name='Test Owner',
                contact_phone='9800000000', **changes)


def test_submission_persists_and_is_public():
    with TestClient(app) as client:
        response = client.post('/api/properties', json=submission())
        assert response.status_code == 201
        record = response.json()
        assert record['source'] == 'community' and record['is_demo'] == 0
        assert record['description'].startswith('A bright family')
        assert record['lat'] is None and record['lng'] is None
        assert record['size_sqft'] == 1369
        assert client.get(f"/api/properties/{record['id']}").json()['contact_phone'] == '9800000000'
        assert client.get('/api/properties').json()['total'] == 1
        assert client.get('/api/properties?dataset=demo').json()['total'] == 0
        assert client.get('/api/properties?q=bhaisepati').json()['total'] == 1
        assert client.get('/api/properties?q=missing').json()['total'] == 0
        assert client.get('/api/properties', params={'saved_ids': record['id']}).json()['total'] == 1
        assert client.get('/api/properties?saved_ids=0').json()['total'] == 0
        assert client.get('/api/properties?q=%27%20OR%201%3D1--').json()['total'] == 0


def test_rental_price_is_not_treated_as_sale_total():
    data = submission()
    data.update(transaction_type='rent', total_price_npr=50000)
    with TestClient(app) as client:
        record = client.post('/api/properties', json=data).json()
        assert record['price_npr'] == 50000 and record['price_basis'] == 'monthly'
        assert record['total_price_npr'] is None
        assert client.get('/api/summary').json()['priced_count'] == 0


def test_invalid_submission_does_not_create_record():
    with TestClient(app) as client:
        for changes in [{'total_price_npr': -1}, {'title': '   '}, {'image_url': 'javascript:alert(1)'}, {'image_url': 'http://example.com/photo.jpg'}, {'bedrooms': -1}, {'contact_phone': 'not-a-number'}]:
            data = submission()
            data.update(changes)
            assert client.post('/api/properties', json=data).status_code == 422
        assert client.get('/api/properties').json()['total'] == 0


def test_schema_migration_is_repeatable():
    init_db()
    init_db()
    with connect() as con:
        assert 'description' in {row['name'] for row in con.execute('PRAGMA table_info(properties)')}
