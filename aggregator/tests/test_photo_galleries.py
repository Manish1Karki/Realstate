import json
from land_discover.media import collect_gallery
from land_discover.scraper import parse_detail
from land_discover.db import connect, upsert
from land_discover.api import decode


def test_full_size_lazy_gallery_and_exclusions():
    html = '''<div class="property-gallery">
      <a href="/front.jpg"><img src="/front-thumb.jpg"></a>
      <img data-src="/side.jpg" src="/placeholder.jpg">
      <img srcset="/rear-small.jpg 300w, /rear.jpg 1600w">
      <a data-fancybox href="/interior.jpg"><img src="/interior-thumb.jpg"></a>
      <img data-original="/side.jpg#duplicate">
      <img src="/logo.png">
    </div><aside><div class="gallery"><img src="/other-house.jpg"></div></aside>
    <div class="related-properties"><div class="gallery"><img src="/related.jpg"></div></div>'''
    item = collect_gallery({'title':'House'}, html, 'https://example.org/listing/1')
    assert item['image_urls'] == ['https://example.org/front.jpg','https://example.org/side.jpg',
                                 'https://example.org/rear.jpg','https://example.org/interior.jpg']


def test_schema_and_gallery_merge_without_single_metadata_limit():
    data = {'@type':'RealEstateListing','image':['https://example.org/front.jpg', {'contentUrl':'https://example.org/side.jpg'}]}
    html = '<script type="application/ld+json">'+json.dumps(data)+'</script><div class="gallery"><img src="/rear.jpg"></div>'
    result = collect_gallery({'image_urls':['https://example.org/legacy.jpg']}, html, 'https://example.org/1')
    assert len(result['image_urls']) == 4


def test_all_photos_survive_scraper_database_api(raw):
    html = '''<h1>House for sale</h1><dl><dt>Location</dt><dd>Baneshwor, Kathmandu</dd></dl>
    <div class="property-gallery"><a href="/front.jpg"><img src="/front-thumb.jpg"></a><img data-src="/side.jpg"><img src="/inside.jpg"></div>'''
    item = parse_detail(html, raw['source_url'], 'fixture')
    identifier = upsert(item)
    with connect() as con:
        result = decode(con.execute('SELECT * FROM properties WHERE id=?',(identifier,)).fetchone())
    assert len(result['image_urls']) == 3
    assert 'https://example.org/front-thumb.jpg' not in result['image_urls']
    assert result['image_url'] in result['image_urls']


def test_single_photo_source_is_not_duplicated():
    result = collect_gallery({}, '<div class="gallery"><img src="/one.jpg"><img src="/one.jpg"></div>', 'https://example.org/1')
    assert result['image_urls'] == ['https://example.org/one.jpg']
