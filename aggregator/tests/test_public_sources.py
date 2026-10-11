import json
from datetime import date, datetime, timezone
import pytest
from land_discover.scraper import parse_detail, discover
from land_discover.normalize import parse_date
from land_discover.eligibility import has_property_information, is_recent_listing
from land_discover.hamrobazar import posted_date
from land_discover.sources import SOURCES
from land_discover.policy import public_terms_digest


def document(obj, extra=''):
    return '<h1>House for Sale in Kalanki</h1><script type="application/ld+json">'+json.dumps(obj)+'</script>'+extra


def test_timestamp_dates_are_not_discarded():
    assert parse_date('2026-07-02T13:46:50+00:00') == '2026-07-02'
    assert parse_date('2026-99-01T10:00:00Z') is None


def test_trade_schema_uses_original_date_and_does_not_guess_bedrooms():
    obj={'@type':'RealEstateListing','name':'House for Sale in Kalanki',
         'address':{'streetAddress':'Kalanki','addressLocality':'Kathmandu'},
         'offers':{'price':26000000,'priceCurrency':'NPR'},'datePosted':'2026-07-02T00:00:00Z',
         'dateModified':'2026-10-10','description':'Residential house with garden and road access.',
         'numberOfRooms':5}
    item=parse_detail(document(obj),'https://realestatebrokernepal.com/property/test','tradenepal')
    assert item['listing_date']=='2026-07-02'
    assert item['bedrooms'] is None
    assert has_property_information(item)
    obj.pop('datePosted')
    assert parse_detail(document(obj),'https://realestatebrokernepal.com/property/test','tradenepal')['listing_date'] is None


def test_home_search_preserves_per_aana_price():
    obj={'@type':'RealEstateListing','name':'House for Sale in Kalanki'}
    extra='<p class="rh_page__property_address">Kalanki, Kathmandu</p><div class="rh_page__property_price">For Sale Rs25 Lakh /Aana</div><div class="prop_lot_size">Lot Size 4 Aana</div><meta property="article:published_time" content="2026-07-02T10:00:00Z">'
    extra+='<div class="prop_bedrooms">Bedrooms 3</div><div class="rh_property__meta road">Road 13 ft</div>'
    item=parse_detail(document(obj,extra),'https://nepalhomesearch.com/property/test/','nepalhomesearch')
    assert item['bedrooms']==3
    assert item['road_access_note']=='13 ft'
    assert item['price_basis']=='per_aana'
    assert item['total_price_npr']==10000000
    assert item['listing_date']=='2026-07-02'


def test_geodirectory_uses_page_date_not_photo_or_modified_date():
    url='https://gharjagganepal.com/properties/kathmandu/municipality/test/'
    obj={'@graph':[{'@type':'WebPage','url':url,'datePublished':'2026-07-02','dateModified':'2026-10-10'},
                   {'@type':'ImageObject','datePublished':'2026-10-10'}]}
    extra='<div class="geodir-field-address">Kalanki Kathmandu</div><div class="geodir-field-price">Rs25000000</div>'
    item=parse_detail(document(obj,extra),url,'gharjagganepal')
    assert item['listing_date']=='2026-07-02'


def test_map_is_not_required_and_empty_properties_are_excluded():
    item={'title':'House for sale','address':'Kalanki, Kathmandu','property_type':'house','transaction_type':'sale','size':'4 aana','lat':None,'lng':None,'listing_date':'2026-07-02'}
    assert has_property_information(item)
    assert is_recent_listing(item,date(2026,10,10))
    item['size']=''
    assert not has_property_information(item)


def test_relative_month_dates_use_calendar_arithmetic():
    assert posted_date('9 months ago',datetime(2026,10,10,tzinfo=timezone.utc))=='2026-01-10'
    assert posted_date('6 months ago',datetime(2026,8,31,tzinfo=timezone.utc))=='2026-02-28'


def test_discovery_uses_canonical_urls_and_older_posts_pagination():
    html='<a href="/properties/kathmandu/city/home/?ref=ad">House</a><a href="/properties/kathmandu/city/home/">Same</a><a href="/properties/page/2/">Older posts</a><a href="https://other.org/properties/kathmandu/city/home/">Other</a>'
    links,next_url=discover(html,'https://gharjagganepal.com/properties/','gharjagganepal')
    assert links==['https://gharjagganepal.com/properties/kathmandu/city/home/']
    assert next_url=='https://gharjagganepal.com/properties/page/2/'


def test_public_policy_digest_detects_content_changes():
    assert public_terms_digest('<main>Terms permit public access</main>') != public_terms_digest('<main>No scraping</main>')
    assert public_terms_digest('<header>Dynamic</header><main>Terms</main>') == public_terms_digest('<header>Other</header><main>Terms</main>')
