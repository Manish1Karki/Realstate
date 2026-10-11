from fastapi.testclient import TestClient
from land_discover.api import app
from land_discover.db import init_db, connect
from land_discover.auth import COOKIE, digest


def sign_in(client):
    response = client.post("/api/auth/register", json={"email": "owner@example.org", "password": "a secure test password", "display_name": "Test Owner"})
    assert response.status_code == 201


def submission(**changes):
    data = dict(title='Family home in Bhaisepati', address='Ward 25, Bhaisepati',
                area_name='Bhaisepati', district='Lalitpur', property_type='house',
                transaction_type='sale', total_price_npr=25000000, size='4 aana',
                description='A bright family home with a private garden.',
                bedrooms=3, bathrooms=2, contact_name='Test Owner',
                contact_phone='9800000000', image_url='https://example.org/house.jpg')
    data.update(changes)
    return data


def test_authenticated_submission_is_visible_without_coordinates():
    with TestClient(app) as client:
        sign_in(client)
        response = client.post('/api/properties', json=submission())
        assert response.status_code == 201
        record = response.json()
        assert record['source'] == 'community' and record['is_demo'] == 0
        assert record['description'].startswith('A bright family')
        assert record['lat'] is None and record['lng'] is None
        assert record['size_sqft'] == 1369
        assert client.get(f"/api/properties/{record['id']}").status_code == 200
        assert client.get('/api/properties').json()['total'] == 1
        with connect() as con:
            assert con.execute('SELECT COUNT(*) FROM properties').fetchone()[0] == 1



def test_rental_price_is_not_treated_as_sale_total():
    data = submission()
    data.update(transaction_type='rent', total_price_npr=50000)
    with TestClient(app) as client:
        sign_in(client)
        record = client.post('/api/properties', json=data).json()
        assert record['price_npr'] == 50000 and record['price_basis'] == 'monthly'
        assert record['total_price_npr'] is None
        assert client.get('/api/summary').json()['priced_count'] == 0


def test_invalid_submission_does_not_create_record():
    with TestClient(app) as client:
        sign_in(client)
        for changes in [{'image_url': ''}, {'image_url': 'https://example.org/static/logo.png'}, {'total_price_npr': -1}, {'title': '   '}, {'image_url': 'javascript:alert(1)'}, {'image_url': 'http://example.com/photo.jpg'}, {'bedrooms': -1}, {'contact_phone': 'not-a-number'}]:
            data = submission()
            data.update(changes)
            assert client.post('/api/properties', json=data).status_code == 422
        assert client.get('/api/properties').json()['total'] == 0


def test_schema_migration_is_repeatable():
    init_db()
    init_db()
    with connect() as con:
        assert 'description' in {row['name'] for row in con.execute('PRAGMA table_info(properties)')}


def test_submission_requires_valid_session():
    with TestClient(app) as client:
        assert client.post('/api/properties', json=submission()).status_code == 401
        client.cookies.set(COOKIE, 'forged-session')
        assert client.post('/api/properties', json=submission()).status_code == 401
        client.cookies.clear()
        sign_in(client)
        token = client.cookies.get(COOKIE)
        with connect() as con:
            con.execute('UPDATE user_sessions SET expires_at=0 WHERE token_hash=?', (digest(token),))
        assert client.post('/api/properties', json=submission()).status_code == 401
        with connect() as con:
            assert con.execute('SELECT COUNT(*) FROM properties').fetchone()[0] == 0


def test_logout_and_cross_origin_submission_are_rejected():
    with TestClient(app) as client:
        sign_in(client)
        assert client.post('/api/properties', json=submission(), headers={'Origin': 'https://evil.example.org'}).status_code == 403
        token = client.cookies.get(COOKIE)
        assert client.post('/api/auth/logout').status_code == 204
        client.cookies.set(COOKIE, token)
        assert client.post('/api/properties', json=submission()).status_code == 401
        with connect() as con:
            assert con.execute('SELECT COUNT(*) FROM properties').fetchone()[0] == 0
