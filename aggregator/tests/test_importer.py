import json
import socket
import pytest
from fastapi.testclient import TestClient
from land_discover.api import app
from land_discover.http import AccessError, validate_public_url
from land_discover.scraper import parse_detail
from land_discover.importer import links

def fixture_html():
    obj={'@type':'House','name':'House for sale','address':'Imadol, Lalitpur','offers':{'price':25000000,'priceCurrency':'NPR'},'image':['/house.jpg',{'url':'https://cdn.example.org/second.jpg'},'javascript:alert(1)'],'description':'A spacious family house.','numberOfBedrooms':4,'numberOfBathroomsTotal':2}
    return '<script type="application/ld+json">'+json.dumps(obj)+'</script>'

def test_property_media_and_rooms():
    item=parse_detail(fixture_html(),'https://example.org/property/1','example.org')
    assert item['image_urls']==['https://example.org/house.jpg','https://cdn.example.org/second.jpg']
    assert item['bedrooms']==4 and item['bathrooms']==2
    assert item['description']=='A spacious family house.'

def test_import_round_trip_and_deduplication(monkeypatch):
    monkeypatch.setattr('land_discover.importer.validate_public_url',lambda url: None)
    monkeypatch.setattr('land_discover.importer.Client.page',lambda self,url,host: fixture_html())
    with TestClient(app) as client:
        response=client.post('/api/import',json={'url':'https://example.org/property/1'})
        assert response.status_code==200
        report=response.json()
        assert report['imported']==1 and report['status']=='complete'
        detail=client.get('/api/properties/'+str(report['property_ids'][0])).json()
        assert len(detail['image_urls'])==2 and detail['bedrooms']==4
        again=client.post('/api/import',json={'url':'https://example.org/property/1'}).json()
        assert again['property_ids']==report['property_ids']

def test_generic_discovery_bounds_origin():
    html='<a href="/property/1">House</a><a href="/property/1">Duplicate</a><a href="https://other.org/property/2">Other</a><a rel="next" href="?page=2">Next</a>'
    candidates,next_url=links(html,'https://example.org/properties','example.org')
    assert candidates==['https://example.org/property/1']
    assert next_url=='https://example.org/properties?page=2'

@pytest.mark.parametrize('url',['http://example.org','https://user:pass@example.org','https://example.org:8080'])
def test_invalid_urls(url):
    with pytest.raises(AccessError): validate_public_url(url)

def test_private_network_refused(monkeypatch):
    monkeypatch.setattr(socket,'getaddrinfo',lambda *a,**kw: [(socket.AF_INET,socket.SOCK_STREAM,6,'',('127.0.0.1',443))])
    with pytest.raises(AccessError): validate_public_url('https://internal.example.org')
