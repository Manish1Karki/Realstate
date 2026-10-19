import pytest
from fastapi.testclient import TestClient
from land_discover.api import app
from land_discover.db import upsert,connect
from land_discover.normalize import normalize
from land_discover import photos

def item(raw, **changes):
    return {**normalize(raw), 'image_url':'https://example.org/house.jpg', **changes}

def test_lastmod_changes_only_when_public_facts_change(raw,monkeypatch):
    from land_discover import db
    monkeypatch.setattr(db,'now',lambda:'2026-10-12T00:00:00+00:00')
    identity=upsert(item(raw))
    monkeypatch.setattr(db,'now',lambda:'2026-10-12T01:00:00+00:00')
    upsert(item(raw,scraped_date='2026-10-12T01:00:00+00:00'))
    with connect() as con:
        assert con.execute('SELECT content_updated_at FROM properties WHERE id=?',(identity,)).fetchone()[0]=='2026-10-12T00:00:00+00:00'
        con.execute('UPDATE properties SET content_updated_at=NULL WHERE id=?',(identity,))
    upsert(item(raw))
    with connect() as con: assert con.execute('SELECT content_updated_at FROM properties WHERE id=?',(identity,)).fetchone()[0] is None
    upsert(item(raw,price_npr=42))
    with connect() as con: assert con.execute('SELECT content_updated_at FROM properties WHERE id=?',(identity,)).fetchone()[0]=='2026-10-12T01:00:00+00:00'

def test_sitemap_listing_and_detail_use_same_eligible_representatives(raw):
    bad=upsert(item(raw,source_url='https://example.org/first',photo_status='invalid'))
    good=upsert(item(raw,source_url='https://example.org/second'))
    alias=upsert(item(raw,source_url='https://example.org/alias'))
    with TestClient(app) as client:
        listings=client.get('/api/properties').json()
        sitemap=client.get('/api/sitemap').json()
        assert {p['id'] for p in listings['items']}=={p['id'] for p in sitemap['items']}=={good}
        assert client.get('/api/properties/'+str(alias)).status_code==404
        assert client.get('/api/properties/'+str(bad)).status_code==404
        assert all('content_updated_at' in p and 'scraped_date' not in p for p in sitemap['items'])

def test_photo_failures_require_confirmation_and_transient_errors_do_not_hide(raw,monkeypatch):
    identity=upsert(item(raw))
    monkeypatch.setattr(photos,'check_photo',lambda *args:None)
    photos.validate_pending()
    with connect() as con:
        assert con.execute('SELECT photo_failures FROM properties WHERE id=?',(identity,)).fetchone()[0]==0
        con.execute('UPDATE properties SET photo_checked_at=NULL')
    monkeypatch.setattr(photos,'check_photo',lambda *args:False)
    photos.validate_pending()
    with connect() as con:
        assert con.execute('SELECT photo_status FROM properties WHERE id=?',(identity,)).fetchone()[0]=='unknown'
        con.execute('UPDATE properties SET photo_checked_at=NULL')
    photos.validate_pending()
    with TestClient(app) as client: assert client.get('/api/properties').json()['total']==0
    with connect() as con: con.execute('UPDATE properties SET photo_checked_at=NULL')
    monkeypatch.setattr(photos,'check_photo',lambda *args:True)
    photos.validate_pending()
    with TestClient(app) as client: assert client.get('/api/properties').json()['total']==1

def test_valid_gallery_fallback_is_not_reset_by_identical_scrape(raw,monkeypatch):
    identity=upsert(item(raw,image_url='https://example.org/broken.jpg',image_urls=['https://example.org/broken.jpg','https://example.org/good.jpg']))
    monkeypatch.setattr(photos,'check_photo',lambda url,*args:url.endswith('good.jpg'))
    photos.validate_pending()
    with connect() as con: before=dict(con.execute('SELECT * FROM properties WHERE id=?',(identity,)).fetchone())
    upsert(item(raw,image_url='https://example.org/broken.jpg',image_urls=['https://example.org/broken.jpg','https://example.org/good.jpg']))
    with connect() as con: after=dict(con.execute('SELECT * FROM properties WHERE id=?',(identity,)).fetchone())
    assert after['image_url']==before['image_url']=='https://example.org/good.jpg'
    assert after['content_updated_at']==before['content_updated_at']

def test_conflicting_districts_are_rejected(raw):
    with pytest.raises(ValueError,match='Conflicting'): normalize({**raw,'address':'Kathmandu, Lalitpur'})

def test_distinct_property_facts_are_not_collapsed(raw):
    upsert(item(raw,source_url='https://example.org/one',bedrooms=2))
    upsert(item(raw,source_url='https://example.org/two',bedrooms=3))
    with TestClient(app) as client: assert client.get('/api/properties').json()['total']==2

def test_trailing_slash_identity_updates_existing_property(raw):
    first=upsert(item(raw,source_url='https://example.org/property/house'))
    second=upsert(item(raw,source_url='https://example.org/property/house/',bedrooms=3))
    assert first==second
    with connect() as con: assert con.execute('SELECT COUNT(*) FROM properties').fetchone()[0]==1

def test_legacy_aliases_resolve_to_current_canonical_record(raw):
    old=upsert(item(raw,source_url='https://example.org/property/house'))
    with connect() as con:
        record=dict(con.execute('SELECT * FROM properties WHERE id=?',(old,)).fetchone())
        record['id']=old+1;record['source_url']+='/' ;record['bedrooms']=3
        con.execute('INSERT INTO properties ('+','.join(record)+') VALUES ('+','.join('?' for _ in record)+')',list(record.values()))
    with TestClient(app) as client:
        assert client.get('/api/properties').json()['total']==1
        assert client.get('/api/properties/'+str(old)).json()['id']==old+1
        assert client.get('/api/sitemap').json()['items'][0]['id']==old+1
