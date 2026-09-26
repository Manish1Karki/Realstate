import json
from datetime import datetime,timezone
import pytest
from land_discover.hamrobazar import parse,OutOfScope
from land_discover.policy import hamrobazar_terms_digest
from land_discover.scraper import scrape
from land_discover.export import export_properties
from land_discover.db import upsert,connect
from land_discover.normalize import normalize

def fixture(description='Land for sale at Example Tole, Lalitpur. 4 aana. 16 ft road.',category='For Sale - Land',title='Example land'):
    # Synthetic values in the DOM structure actually observed on public pages.
    obj={'@type':'Product','name':title,'category':category,'offers':{'price':3000000,'priceCurrency':'NPR'}}
    return '<script type="application/ld+json">'+json.dumps(obj)+'</script>'+f'<section><h2>About this listing</h2><p>{description}</p></section><section><h2>Specifications</h2><div class="grid"><div>Land Size (Aana/Dhur)</div><div>4</div></div></section><span data-testid="product-meta-chip">Posted 2 days ago</span>'

def test_live_structure_and_unspecified_price():
    row=parse(fixture(),'https://hamrobazaar.com/detail/for-sale-land/fixture',datetime(2026,9,26,tzinfo=timezone.utc))
    assert row['address']=='Example Tole, Lalitpur'
    assert row['price_npr']==3000000 and row['total_price_npr'] is None
    assert row['price_basis']=='unknown' and row['size_sqft']==1369
    assert row['listing_date']=='2026-09-24'

def test_unit_price_calculation():
    row=parse(fixture('Land for sale at Example Tole, Lalitpur. 4 aana, price per aana negotiable.'),'https://hamrobazaar.com/detail/fixture')
    assert row['total_price_npr']==12000000

def test_masked_location_not_recovered():
    html=fixture('A plot in Itahari.','For Sale - Land')+'<script>hiddenAddress="Lalitpur"</script><div>Similar Products: Kathmandu land</div>'
    with pytest.raises(OutOfScope):parse(html,'https://hamrobazaar.com/detail/fixture')

def test_date_and_size_unknown_preserved():
    row=parse(fixture('Land for sale in Kathmandu.'),'https://hamrobazaar.com/detail/fixture')
    assert row['size_sqft'] is None and 'unspecified' in row['size']
    assert row['address']=='Kathmandu'

def test_source_policy_digest_ignores_navigation():
    a='<nav>One</nav><h1>Terms</h1><p>Updated at: September 2026</p><p>Example policy</p><div>You\'ve reached the end of the page</div>'
    assert hamrobazar_terms_digest(a)==hamrobazar_terms_digest(a.replace('One','Two'))
    assert hamrobazar_terms_digest(a)!=hamrobazar_terms_digest(a.replace('Example policy','Changed policy'))

def test_crawl_end_to_end_with_mocked_network(monkeypatch,tmp_path):
    import land_discover.scraper as crawler
    index='<a href="/detail/for-sale-land/fixture">Land</a><a href="/detail/for-sale-land/fixture">Duplicate</a><a rel="next" href="?page=2">Next</a>'
    next_page='<a href="/detail/for-sale-land/second">Second</a>'
    monkeypatch.setattr(crawler,'review',lambda *args:None)
    calls=[]
    def page(self,url,host):
        calls.append(url)
        if '/detail/' in url:return fixture()
        return next_page if 'page=2' in url else index
    monkeypatch.setattr(crawler.Client,'page',page)
    report=scrape('hamrobazar',2,10)
    assert report['imported']==2 and report['pages']==2 and len(calls)==4
    exported=export_properties(tmp_path/'out.csv','hamrobazar',report['property_ids'])
    assert exported['rows']==2
