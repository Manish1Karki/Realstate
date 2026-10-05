import json
import pytest
from fastapi.testclient import TestClient
from land_discover.api import app
from land_discover import collector
from land_discover.db import connect, upsert
from land_discover.scraper import discover, parse_detail
from land_discover.policy import huku_terms_digest

def huku_html(transaction='Rent',kind='House',price='110000',size='5 aana'):
    obj={'@type':'RealEstateListing','name':f'{kind} for {transaction.lower()} in Dhumbarahi','address':{'addressLocality':'Kathmandu','addressRegion':'Kathmandu'},'offer':{'priceCurrency':'NPR','price':int(price)},'image':['https://images.example.org/house.webp'],'datePosted':'Thu Oct 01 2026 04:41:29 GMT+0000 (Coordinated Universal Time)'}
    return '<script type="application/ld+json">'+json.dumps(obj)+'</script>'+f'''<main>
      <section><h1>{obj['name']}</h1><span>{kind} For {transaction}</span><p>Rs. {price} {'Per Month' if transaction=='Rent' else 'Per Aana' if kind=='Land' else ''}</p></section>
      <div><h2>Features</h2><div><span>Size/Area : </span><span>{size}</span></div><div><span>Bedrooms : </span><span>8</span></div><div><span>Bathrooms : </span><span>3</span></div></div>
      <div><h2>Description</h2><p>House in Dhumbarahi, Kathmandu with a garden.</p></div>
      <aside><h2>Similar Properties</h2><p>Land in Pokhara Rs. 999</p></aside>
    </main>'''

@pytest.mark.parametrize('transaction,kind,price,basis,total', [('Rent','House','110000','monthly',None),('Sale','House','60000000','total',60000000),('Sale','Land','9000000','per_aana',45000000)])
def test_huku_sale_rental_and_land(transaction,kind,price,basis,total):
    item=parse_detail(huku_html(transaction,kind,price),'https://www.hukurealestate.com/properties/1','huku')
    assert item['price_basis']==basis and item['total_price_npr']==total
    assert item['district']=='Kathmandu' and item['bedrooms']==8 and item['bathrooms']==3
    assert item['listing_date']=='2026-10-01' and len(item['image_urls'])==1
    assert 'Pokhara' not in item['description']

def test_huku_discovery_excludes_categories():
    html='<a href="/properties/1">House</a><a href="/properties/1/">Same House</a><a href="/properties/1?ref=home">Tracking link</a><a href="/properties/house-for-sale">Category</a><a href="https://other.org/properties/2">Other</a>'
    assert discover(html,'https://www.hukurealestate.com/','huku')[0]==['https://www.hukurealestate.com/properties/1']

def test_title_location_takes_precedence_over_nearby_landmarks():
    html=huku_html('Sale','Land','9000000').replace('Land for sale in Dhumbarahi','Land for sale in Kuleshwor | 6 aana').replace('House in Dhumbarahi, Kathmandu with a garden.','Near Kalanki junction, Kathmandu.')
    item=parse_detail(html,'https://www.hukurealestate.com/properties/1','huku')
    assert item['address']=='Kuleshwor, Kathmandu'

def test_source_failure_does_not_stop_next_source(monkeypatch):
    calls=[]
    def fake(source,pages,limit):
        calls.append((source,pages,limit))
        if source=='hamrobazar': raise RuntimeError('Source temporarily unavailable')
        return {'status':'complete','imported':2,'errors':[]}
    monkeypatch.setattr(collector,'scrape',fake)
    result=collector.collect_all()
    assert [x[0] for x in calls]==['hamrobazar','huku']
    assert result['status']=='partial'
    assert collector.collection_status()['cycle']['status']=='partial'
    assert collector.collection_status()['cycle']['current_source'] is None

def test_repeat_cycles_update_properties(monkeypatch):
    def fake(source,pages,limit):
        item=parse_detail(huku_html(),'https://www.hukurealestate.com/properties/1','huku')
        return {'status':'complete','imported':1,'property_ids':[upsert(item)],'errors':[]}
    monkeypatch.setattr(collector,'scrape',fake)
    monkeypatch.setattr(collector,'auto_sources',lambda:['huku'])
    first=collector.collect_all(); second=collector.collect_all()
    assert first['reports'][0]['property_ids']==second['reports'][0]['property_ids']
    with connect() as con:
        assert con.execute('SELECT COUNT(*) FROM properties').fetchone()[0]==1
        assert con.execute('SELECT COUNT(*) FROM collection_cycles').fetchone()[0]==2

def test_startup_and_shutdown_manage_worker(monkeypatch):
    calls=[]
    worker=object()
    monkeypatch.setattr(collector,'start_worker',lambda: calls.append('start') or worker)
    monkeypatch.setattr(collector,'stop_worker',lambda p: calls.append(('stop',p)))
    with TestClient(app) as client:
        assert calls==['start']
        assert client.get('/api/health').json()['status']=='ok'
        assert client.get('/api/sources').json()['collection']['sources']==['hamrobazar','huku']
    assert calls==['start',('stop',worker)]

def test_disabled_startup_does_not_spawn():
    assert collector.start_worker() is None

def test_limits_are_bounded(monkeypatch):
    monkeypatch.setenv('LAND_AUTO_SCRAPE_LIMIT','999999')
    assert collector.limit('LAND_AUTO_SCRAPE_LIMIT',20,100)==100
    monkeypatch.setenv('LAND_AUTO_SCRAPE_LIMIT','invalid')
    assert collector.limit('LAND_AUTO_SCRAPE_LIMIT',20,100)==20

def test_terms_digest_ignores_navigation():
    content='<div class="prose"><h2>User-Generated Content</h2><p>Public policy.</p></div>'
    assert huku_terms_digest('<nav>First</nav>'+content)==huku_terms_digest('<nav>Second</nav>'+content)
    with pytest.raises(ValueError): huku_terms_digest('<h1>Unexpected page</h1>')
