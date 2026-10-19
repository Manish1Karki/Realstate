import json
import pytest
import httpx
from land_discover import archive
from land_discover.db import upsert
from land_discover.normalize import normalize


def record(raw):
    return {**normalize(raw),'contact_phone':'9800000000','contact_role':'owner',
            'image_url':'https://example.org/front.jpg',
            'image_urls':['https://example.org/front.jpg','https://example.org/side.jpg']}


def folder(identifier):
    entry = json.loads((archive.archive_root()/'by-id'/f'property-{identifier:06d}.json').read_text())
    return archive.archive_root()/entry['folder']


def test_property_id_links_location_contact_and_photos(raw):
    identifier = upsert(record(raw))
    report = archive.sync_properties()
    target = folder(identifier)
    assert report['properties'] == 1 and report['pending_photos'] == 2
    assert target.parent.name.startswith('Baneshwor-')
    assert target.parent.parent.name.startswith('Kathmandu-')
    assert json.loads((target/'property.json').read_text())['id'] == identifier
    for filename in ('contact.json','location.json','facilities.json','photos/manifest.json'):
        assert json.loads((target/filename).read_text())['property_id'] == identifier
    contact = json.loads((target/'contact.json').read_text())
    assert contact['phone'] == '9800000000' and contact['role'] == 'owner'


def test_rescrape_keeps_id_and_moves_folder_with_downloaded_photos(raw,monkeypatch):
    item = record(raw)
    identifier = upsert(item)
    def download(url, directory, client):
        filename = 'front.jpg' if 'front' in url else 'side.jpg'
        (directory/filename).write_bytes(b'photo')
        return filename
    monkeypatch.setattr(archive,'download_photo',download)
    archive.sync_properties(download=True)
    previous = folder(identifier)
    assert upsert({**item,'address':'Imadol, Lalitpur','area_name':'Imadol','district':'Lalitpur'}) == identifier
    report = archive.sync_properties(download=True)
    target = folder(identifier)
    assert not previous.exists() and target != previous
    assert (target/'photos/front.jpg').read_bytes() == b'photo'
    assert report['downloaded'] == 0


def test_download_failure_keeps_metadata_and_batch_progress(raw,monkeypatch):
    upsert(record(raw))
    monkeypatch.setattr(archive,'download_photo',lambda *args: (_ for _ in ()).throw(ValueError('Unavailable photo')))
    first = archive.sync_properties(download=True,max_downloads=1)
    assert first['properties'] == 1 and first['photo_errors'] == 1 and first['pending_photos'] == 2
    second = archive.sync_properties(download=True,max_downloads=1)
    # Failed photo is cooled down, so the next photo gets its own attempt.
    assert second['photo_errors'] == 1


def test_archive_excludes_demo_and_rejects_escaping_index(raw):
    identifier = upsert(record(raw))
    upsert({**record(raw),'source_url':'demo://1','is_demo':1})
    assert archive.sync_properties()['properties'] == 1
    index = archive.archive_root()/'by-id'/f'property-{identifier:06d}.json'
    archive.atomic_json(index, {'folder':'../../outside'})
    assert archive.sync_properties()['errors']
    with pytest.raises(ValueError): archive.within(archive.archive_root(),archive.archive_root()/'..'/'outside')


def test_upsert_updates_archive_when_enabled(raw,monkeypatch):
    monkeypatch.setenv('LAND_ARCHIVE_ENABLED','true')
    identifier = upsert(record(raw))
    assert (folder(identifier)/'property.json').is_file()
    upsert({**record(raw),'contact_phone':'9800000001'})
    assert json.loads((folder(identifier)/'contact.json').read_text())['phone'] == '9800000001'


def test_streaming_photo_redirect_and_size_limit(tmp_path,monkeypatch):
    visited = []
    monkeypatch.setattr(archive,'validate_public_url',lambda url: visited.append(url))
    monkeypatch.setattr(archive,'throttle',lambda *args: None)
    class Fake:
        delay = 0
        def robots(self,url): return 0
    def response(request):
        if request.url.path == '/redirect': return httpx.Response(302,headers={'location':'https://cdn.example.org/photo.jpg'})
        return httpx.Response(200,content=b'photo',headers={'content-type':'image/jpeg'})
    client = Fake()
    with httpx.Client(transport=httpx.MockTransport(response)) as client.client:
        filename = archive.download_photo('https://example.org/redirect',tmp_path,client)
        assert (tmp_path/filename).read_bytes() == b'photo'
        assert visited == ['https://example.org/redirect','https://cdn.example.org/photo.jpg']
        monkeypatch.setattr(archive,'MAX_PHOTO_BYTES',2)
        with pytest.raises(ValueError,match='archive limit'):
            archive.download_photo('https://example.org/large.jpg',tmp_path,client)
    assert not list(tmp_path.glob('.download-*'))


def test_nonimage_response_never_becomes_photo(tmp_path,monkeypatch):
    directory = tmp_path/'downloads'
    directory.mkdir()
    monkeypatch.setattr(archive,'validate_public_url',lambda url: None)
    monkeypatch.setattr(archive,'throttle',lambda *args: None)
    class Fake:
        delay = 0
        def robots(self,url): return 0
    client = Fake()
    with httpx.Client(transport=httpx.MockTransport(lambda request:httpx.Response(200,content=b'HTML',headers={'content-type':'text/html'}))) as client.client:
        with pytest.raises(ValueError,match='raster image'):
            archive.download_photo('https://example.org/fake.jpg',directory,client)
    assert not list(directory.iterdir())
