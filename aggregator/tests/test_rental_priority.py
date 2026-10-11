import pytest
from fastapi.testclient import TestClient
from land_discover.api import app
from land_discover.db import upsert, connect
from land_discover.normalize import normalize
from land_discover.eligibility import nepal_today


@pytest.mark.parametrize('sort',['newest','price_asc','price_desc'])
@pytest.mark.parametrize('transaction',['rent','sale'])
def test_all_mapped_properties_rank_before_unmapped_before_pagination(raw,sort,transaction):
    base={**normalize(raw), 'image_url': 'https://example.org/house.jpg'}
    ids={}
    for name,lat,lng,listing_transaction,stamp in [
        ('mapped',27.65,85.30,transaction,'2026-01-01T00:00:00Z'),
        ('unmapped',None,None,transaction,'2026-10-11T00:00:00Z'),
        ('partial',27.65,None,transaction,'2026-10-11T00:00:00Z'),
        ('invalid',0,0,transaction,'2026-10-11T00:00:00Z'),
        ('other',27.65,85.30,'sale' if transaction=='rent' else 'rent','2026-10-11T00:00:00Z')]:
        ids[name]=upsert({**base,'source_url':'https://example.org/'+name,'lat':lat,'lng':lng,
                         'transaction_type':listing_transaction,'listing_date':nepal_today().isoformat()})
        with connect() as con:
            con.execute('UPDATE properties SET scraped_date=? WHERE id=?',(stamp,ids[name]))
    with TestClient(app) as client:
        response=client.get('/api/properties',params={'transaction':transaction,'page_size':1,'sort':sort}).json()
        assert response['total']==4
        assert response['items'][0]['id']==ids['mapped']
        second=client.get('/api/properties',params={'transaction':transaction,'page_size':1,'page':2,'sort':sort}).json()
        assert second['items'][0]['id']!=ids['mapped']
        all_rows=client.get('/api/properties',params={'sort':sort}).json()
        assert {row['id'] for row in all_rows['items'][:2]}=={ids['mapped'],ids['other']}
        assert client.get('/api/properties',params={'transaction':'sale' if transaction=='rent' else 'rent','sort':sort}).json()['items'][0]['id']==ids['other']
