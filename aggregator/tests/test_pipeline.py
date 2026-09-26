import csv,io,json
import httpx,pytest
from fastapi.testclient import TestClient
from land_discover.normalize import parse_price,parse_size,parse_date,normalize
from land_discover.db import upsert,connect,cached,cache_set
from land_discover.api import app
from land_discover.geo import distance,segment_distance,parse_amenities,geocode
from land_discover.scraper import parse_detail,discover,scrape
from land_discover.http import Client,AccessError

@pytest.mark.parametrize('raw,expected',[('0-4-0-0',1369),('1 ropani 2 aana',6160.5),('1250 sq ft',1250),('४ आना',1369),('0-16-0-0',None),('4 anna',1369),('n/a',None)])
def test_size(raw,expected): assert parse_size(raw)==expected

@pytest.mark.parametrize('raw,size,expected',[('Rs. 1,50,00,000',None,(15000000,'total',15000000)),('NPR २५ लाख per aana',1369,(2500000,'per_aana',10000000)),('1.5 crore',None,(15000000,'total',15000000)),('50,000 per month',None,(50000,'monthly',None)),('25 lakh per aana',None,(2500000,'per_aana',None)),('25-30 lakh',None,(None,'unknown',None)),('Contact for price',None,(None,'unknown',None)),('1 crore 20 lakh',None,(None,'unknown',None)),('Rs. 0',None,(None,'unknown',None))])
def test_price(raw,size,expected): assert parse_price(raw,size)==expected

def test_dates():
    assert parse_date('2083-01-01') is None
    assert parse_date('2 months ago') is None
    assert parse_date('2025-06-30')=='2025-06-30'

def test_valley_validation(raw):
    raw['address']='Lakeside, Pokhara'
    with pytest.raises(ValueError): normalize(raw)

def test_upsert_preserves_first_seen_and_invalidates_geocode(raw):
    item=normalize(raw); id=upsert(item)
    with connect() as con:
        first=con.execute('SELECT first_seen FROM properties WHERE id=?',(id,)).fetchone()[0]
        con.execute("UPDATE properties SET lat=27.7,lng=85.3,geocode_status='matched',enrichment_status='complete' WHERE id=?",(id,))
    assert upsert(item)==id
    item['address']='Lazimpat, Kathmandu';upsert(item)
    with connect() as con:
        row=con.execute('SELECT * FROM properties').fetchone()
        assert row['first_seen']==first and row['lat'] is None and row['geocode_status']=='pending'

def test_semantic_adapter_synthetic_fixture():
    html='''<main><h1>Land for sale in Baneshwor</h1><dl><dt>Location</dt><dd>Baneshwor, Kathmandu</dd><dt>Land area</dt><dd>0-4-0-0</dd><dt>Price</dt><dd>Rs. 25 lakh per aana</dd><dt>Listed on</dt><dd>2026-01-10</dd></dl></main>'''
    item=parse_detail(html,'https://example.org/detail/land/fixture','fixture')
    assert item['total_price_npr']==10000000 and item['property_type']=='land'

def test_structured_data_and_no_location_rejected():
    product={'@type':'Product','name':'Apartment for sale','address':{'streetAddress':'Jhamsikhel','addressLocality':'Lalitpur'},'offers':{'price':18000000,'priceCurrency':'NPR'},'floorSize':{'value':1200,'unitText':'sq ft'}}
    html='<script type="application/ld+json">'+json.dumps(product)+'</script>'
    item=parse_detail(html,'https://example.org/apartment','fixture')
    assert item['district']=='Lalitpur' and item['size_sqft']==1200
    with pytest.raises(ValueError): parse_detail('<h1>Land for sale</h1>','https://example.org/land','fixture')

def test_pagination_and_origin():
    html='<a href="/detail/land/1">One</a><a href="/detail/land/1">Duplicate</a><a href="https://evil.invalid/detail/land/2">Other</a><a rel="next" href="?page=2">Next</a>'
    urls,next_url=discover(html,'https://hamrobazaar.com/category/real-estate','hamrobazar')
    assert urls==['https://hamrobazaar.com/detail/land/1'] and next_url.endswith('?page=2')

def test_nearest_road_is_segment_not_center():
    d,point=segment_distance(27.7,85.3,[{'lat':27.7,'lon':85.29},{'lat':27.7,'lon':85.31}])
    assert d<.001
    rows=parse_amenities([{'type':'way','id':1,'tags':{'highway':'primary','name':'Ring Road'},'geometry':[{'lat':27.7,'lon':85.29},{'lat':27.7,'lon':85.31}]}],27.7,85.3,1000)
    assert rows[0]['distance_km']<.001

def test_amenities_filter_and_dedupe():
    point={'type':'node','id':1,'lat':27.7001,'lon':85.3001,'tags':{'amenity':'school','name':'Fixture school'}}
    far={**point,'id':2,'lat':28.9}
    result=parse_amenities([point,point,far],27.7,85.3,1000)
    assert len(result)==1 and result[0]['kind']=='school'
    assert distance(27.7,85.3,27.7,85.3)==0

def test_geocode_rejects_wrong_district_and_ambiguity(raw):
    class Fake:
        def request(self,*args,**kwargs): raise AssertionError('Should use cache')
    query='geocode:https://nominatim.openstreetmap.org:'+raw['address'].lower()+', nepal'
    hit={'lat':'27.7','lon':'85.3','address':{'county':'Kathmandu'},'addresstype':'suburb','display_name':'Fixture'}
    cache_set(query,[hit,hit])
    assert geocode(normalize(raw),Fake())['geocode_status']=='ambiguous'
    cache_set(query,[{**hit,'address':{'county':'Lalitpur'}}])
    assert geocode(normalize(raw),Fake())['geocode_status']=='not_found'
    cache_set(query,[hit]); assert geocode(normalize(raw),Fake())['lat']==27.7

def test_source_gate_before_network(monkeypatch):
    monkeypatch.setattr(Client,'request',lambda *a,**k:pytest.fail('Unreviewed source made a network request'))
    assert scrape('housingnepal')['status']=='failed'
    assert scrape('nepalpropertybazaar')['status']=='failed'

def test_geocode_nepali_district_and_locality_over_landmark(raw):
    class Fake:
        def request(self,*args,**kwargs): raise AssertionError('Should use cache')
    query='geocode:https://nominatim.openstreetmap.org:'+raw['address'].lower()+', nepal'
    hit={'lat':'27.7','lon':'85.3','address':{'county':'काठमाडौं जिल्ला'},'category':'place','addresstype':'neighbourhood'}
    cache_set(query,[hit,{**hit,'category':'amenity','addresstype':'temple'}])
    result=geocode(normalize(raw),Fake())
    assert result['geocode_status']=='matched' and result['geocode_precision']=='approximate neighbourhood'

def test_robots_denial_and_redirect_checks(monkeypatch):
    c=Client(); calls=[]
    def request(method,url,**kwargs):
        calls.append(url)
        if url.endswith('/robots.txt'): return httpx.Response(200,text='User-agent: *\nDisallow: /api/',request=httpx.Request(method,url))
        return httpx.Response(302,headers={'Location':'https://other.invalid/page'},request=httpx.Request(method,url))
    monkeypatch.setattr(c,'request',request)
    with pytest.raises(AccessError): c.page('https://example.org/api/list','example.org')
    assert len(calls)==1
    with pytest.raises(AccessError): c.page('https://example.org/page','example.org')
    assert not any('other.invalid' in u for u in calls)
    c.close()

def test_api_filters_export_summary_and_dataset_isolation(raw):
    item=normalize(raw); item['area_name']='=FORMULA';id=upsert(item)
    demo={**item,'source_url':'demo://2','is_demo':1,'area_name':'Synthetic'};upsert(demo)
    unknown={**item,'source_url':'https://example.org/3','price_npr':None,'total_price_npr':None};upsert(unknown)
    with TestClient(app) as client:
        assert client.get('/api/health').json()['status']=='ok'
        assert client.get('/api/properties').json()['total']==2
        assert client.get('/api/properties?dataset=demo').json()['total']==1
        assert client.get('/api/properties?min_price=9000000').json()['total']==1
        assert client.get('/api/properties?school_km=1').json()['total']==0
        assert client.get('/api/properties?min_price=10&max_price=1').status_code==422
        assert client.get('/api/properties?area=%27%20OR%201=1--').json()['total']==0
        assert client.get('/api/properties/99999').status_code==404
        assert client.get(f'/api/properties/{id}').json()['amenities']==[]
        stats=client.get('/api/summary').json()
        assert stats['priced_count']==1 and stats['price_by_area'][0]['median_per_aana']==2500000
        assert client.get('/api/map').json()['mapped_total']==0
        response=client.get('/api/export.csv?min_price=1')
        rows=list(csv.DictReader(io.StringIO(response.text.lstrip('\ufeff'))))
        assert len(rows)==1 and rows[0]['area_name']=="'=FORMULA"
        assert client.get('/api/options').json()['areas']==['=FORMULA']
