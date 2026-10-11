import json
import pytest
from land_discover.sources import SOURCES, local_trials_enabled
from land_discover.collector import auto_sources
from land_discover.scraper import parse_detail, discover, scrape, review
from land_discover.http import Client, AccessError
from land_discover.db import connect
from land_discover.hamrobazar import OutOfScope


def eproperty(title='Land For Sale at Changathali, Lalitpur', address='Changathali, Lalitpur', price='Rs 45,00,000/aana'):
    return f'''<div class="row--property-header"><h1><span>{title}</span><span><strong>{price}</strong></span></h1><p class="property-location">{address}</p></div>
    <ul class="property-info"><li>3.94 aana</li><li>5 Bedroom</li><li>3 Bathroom</li></ul>
    <div class="property-description-text">Land with road access. Owner Contact Number: 9812345678</div>
    <div class="property-additional-detail"><li>Posted on: 23 September 2026</li></div>
    <div class="fotorama"><img src="/system/photos/1/land.jpg"><img src="/system/photos/1/land.jpg"></div>
    <aside><h1>House in Pokhara</h1><img src="/system/photos/2/other.jpg"></aside>'''


def bhoomi(address='Ramkot, Kathmandu', price='NPR 25 Lakhs Per Aana', title='Residential Land for Sale'):
    return f'''<div class="property_detail_wrapper"><div class="property_detail_title"><h4 class="property_detail_heading">{title}</h4><p class="property_detail_location">{address}</p></div>
    <h4 class="detail_price">{price}</h4><div class="gallery_showcase"><div class="carousel-main"><img class="thumb" src="/storage/property-galleries/land.jpg"></div>
    <div class="accordion-item"><h2>Overview</h2><ul><li>Area Covered : <span>0-4-1-0</span></li><li>Road Access : <span>13 FT</span></li><li>Posted : <span>6 days ago</span></li></ul></div>
    <aside><img src="/storage/amenities/school.png"><img src="/storage/other-property.jpg">9 Bedroom</aside></div></div>'''


def test_reviewed_sources_enabled_and_restricted_sources_stay_off(monkeypatch):
    monkeypatch.delenv('LAND_LOCAL_SOURCE_TRIAL',raising=False)
    assert auto_sources()==['hamrobazar','huku','nepalbhoomi','gharjagganepal','nepalhomesearch','tradenepal']
    with pytest.raises(AccessError,match='written authorization'): review('epropertynepal',object())
    monkeypatch.setenv('LAND_LOCAL_SOURCE_TRIAL','true')
    assert auto_sources()==['hamrobazar','huku','nepalbhoomi','gharjagganepal','nepalhomesearch','tradenepal']


@pytest.mark.parametrize('setting,value',[('RENDER','true'),('VERCEL','1'),('LAND_REQUIRE_PROXY','true'),('TURSO_DATABASE_URL','libsql://test.turso.io')])
def test_local_opt_in_cannot_enable_cloud_collection(monkeypatch,setting,value):
    monkeypatch.setenv('LAND_LOCAL_SOURCE_TRIAL','true')
    monkeypatch.setenv(setting,value)
    if setting=='TURSO_DATABASE_URL': monkeypatch.setenv('TURSO_AUTH_TOKEN','test-not-a-real-token')
    assert not local_trials_enabled()
    monkeypatch.setitem(SOURCES,'nepalbhoomi',{**SOURCES['nepalbhoomi'],'status':'local_trial'})
    with pytest.raises(AccessError): review('nepalbhoomi',object())


def test_eproperty_preserves_unit_price_and_property_gallery():
    item=parse_detail(eproperty(),'https://epropertynepal.com/properties/1','epropertynepal')
    assert item['price_npr']==4500000 and item['price_basis']=='per_aana'
    assert item['total_price_npr']==17730000 and item['district']=='Lalitpur'
    assert item['listing_date']=='2026-09-23' and item['bedrooms']==5 and item['bathrooms']==3
    assert item['image_urls']==['https://epropertynepal.com/system/photos/1/land.jpg']
    assert '9812345678' not in item['description'] and 'Pokhara' not in item['description']


@pytest.mark.parametrize('price,transaction,basis,amount',[('Rs 2,80,00,000/only','Sale','total',28000000),('Rs 40,000','Rent','monthly',40000),('Price - NA','Sale','unknown',None)])
def test_eproperty_total_monthly_and_missing_price(price,transaction,basis,amount):
    item=parse_detail(eproperty(title=f'House For {transaction} at Kathmandu',address='Kapan, Kathmandu',price=price),'https://epropertynepal.com/properties/1','epropertynepal')
    assert item['price_basis']==basis and item['price_npr']==amount
    assert item['transaction_type']==transaction.lower()


def test_eproperty_skips_wanted_ads():
    with pytest.raises(OutOfScope): parse_detail(eproperty(title='Land required Kathmandu Valley',address='Kathmandu'),'https://epropertynepal.com/properties/1','epropertynepal')


def test_eproperty_skips_outside_valley():
    with pytest.raises(OutOfScope): parse_detail(eproperty(address='Pokhara, Kaski'),'https://epropertynepal.com/properties/1','epropertynepal')


def test_bhoomi_uses_listing_address_and_traditional_area():
    item=parse_detail(bhoomi(),'https://nepalbhoomi.com/properties/land','nepalbhoomi')
    assert item['district']=='Kathmandu' and item['price_basis']=='per_aana'
    assert item['size_sqft']==1454.5625 and item['total_price_npr']==10625000
    from datetime import timedelta
    from land_discover.eligibility import nepal_today
    assert item['listing_date'] == (nepal_today()-timedelta(days=6)).isoformat()
    assert item['image_urls']==['https://nepalbhoomi.com/storage/property-galleries/land.jpg']
    assert item['bedrooms'] is None and item['bathrooms'] is None


def test_bhoomi_does_not_choose_a_district_from_conflicting_address():
    with pytest.raises(ValueError,match='Conflicting advertised districts'):
        parse_detail(bhoomi(address='Thulo Bharyang Kathmandu, Lalitpur'),'https://nepalbhoomi.com/properties/house','nepalbhoomi')


def test_bhoomi_unknown_price_stays_unknown():
    item=parse_detail(bhoomi(price='THIRTY LAKH ONLY Per Aana'),'https://nepalbhoomi.com/properties/land','nepalbhoomi')
    assert item['price_npr'] is None and item['total_price_npr'] is None


def test_trial_discovery_excludes_other_origins_seeds_and_tracking():
    html='''<a href="/properties/buy">Index</a><a href="/properties/land?ref=home">Land</a><a href="/properties/land/">Same</a><a href="https://other.com/properties/land">Other</a>
    <a href="/properties/buy?page=2" rel="next">Next</a><a href="/login" rel="next">Login</a>'''
    assert discover(html,'https://nepalbhoomi.com/properties/buy','nepalbhoomi')==(['https://nepalbhoomi.com/properties/land'],'https://nepalbhoomi.com/properties/buy?page=2')


def test_nepalbhoomi_multiple_indexes_pagination_bounded_and_repeat_updates(monkeypatch):
    monkeypatch.setenv('LAND_LOCAL_SOURCE_TRIAL','true')
    seed=SOURCES['nepalbhoomi']['start_urls'][0]
    rental=SOURCES['nepalbhoomi']['start_urls'][1]
    third='https://nepalbhoomi.com/properties/third-land-listing'
    pages={seed:'<a href="/properties/first-land-listing">Land</a><a href="/properties/buy?page=2" rel="next">Next</a>',
           rental:'<a href="/properties/second-house-listing">House</a>',seed+'?page=2':'<a href="/properties/third-land-listing">Land</a><a href="/properties/third-land-listing?ref=x">Same</a>',
           'https://nepalbhoomi.com/properties/first-land-listing':bhoomi(),
           'https://nepalbhoomi.com/properties/second-house-listing':bhoomi(title='House for Sale'),
           third:bhoomi()}
    requests=[]
    def page(self,url,host): requests.append(url); return pages[url]
    monkeypatch.setattr(Client,'page',page)
    monkeypatch.setattr('land_discover.scraper.review',lambda *args: None)
    first=scrape('nepalbhoomi',max_pages=3,max_listings=3)
    assert first['status']=='complete' and first['pages']==3 and first['imported']==3
    assert requests.count(third)==1
    second=scrape('nepalbhoomi',max_pages=3,max_listings=3)
    assert first['property_ids']==second['property_ids']
    with connect() as con: assert con.execute('SELECT COUNT(*) FROM properties').fetchone()[0]==3
    requests.clear()
    bounded=scrape('nepalbhoomi',max_pages=1,max_listings=1)
    assert bounded['pages']==1 and bounded['imported']==1 and rental not in requests
