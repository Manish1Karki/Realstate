"""Location-organized local archive keyed by the existing database property ID."""
import hashlib
import json
import os
import re
import shutil
import tempfile
import httpx
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse

from .db import connect, db_path, now
from .http import Client, AccessError, throttle, validate_public_url
from .locking import single_job
from .photos import photo_candidates

MAX_PHOTO_BYTES = 10 * 1024 * 1024
PHOTO_TYPES = {'image/jpeg':'.jpg', 'image/png':'.png', 'image/webp':'.webp',
               'image/gif':'.gif', 'image/avif':'.avif'}


def enabled():
    return os.getenv('LAND_ARCHIVE_ENABLED', 'true').lower() not in ('false','0','no','off')


def archive_root():
    return Path(os.getenv('LAND_ARCHIVE_DIR') or db_path().parent / 'property-archive').resolve()


def segment(value):
    text = re.sub(r'[^\w-]+', '-', str(value or '').strip(), flags=re.UNICODE).strip('-_')[:70]
    if not text: text = 'Unknown'
    if text.upper() in {'CON','PRN','AUX','NUL',*(f'COM{i}' for i in range(1,10)),*(f'LPT{i}' for i in range(1,10))}:
        text = '_' + text
    # Hash prevents distinct source localities with identical sanitized names from merging.
    return text + '-' + hashlib.sha256(str(value or '').encode()).hexdigest()[:6]


def within(root, path):
    resolved = path.resolve()
    if resolved == root or not resolved.is_relative_to(root):
        raise ValueError('Archive path must stay inside the property archive')
    return resolved


def atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.write-', suffix='.tmp', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as output:
            json.dump(value, output, indent=2, ensure_ascii=False)
            output.write('\n')
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary): os.unlink(temporary)


def read_json(path, default):
    try: return json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError): return default


def download_photo(url, target_dir, client):
    """Bounded streaming download with public-network and robots checks on every redirect."""
    original = url
    for _ in range(5):
        if urlparse(url).scheme != 'https': raise AccessError('Photo must use HTTPS')
        validate_public_url(url)
        delay = client.robots(url)
        throttle(urlparse(url).netloc, max(client.delay, delay))
        with client.client.stream('GET', url) as response:
            if response.is_redirect:
                url = urljoin(url, response.headers['location'])
                continue
            response.raise_for_status()
            mime = response.headers.get('content-type','').split(';')[0].strip().lower()
            if mime not in PHOTO_TYPES: raise ValueError('Photo response is not a supported raster image')
            if int(response.headers.get('content-length') or 0) > MAX_PHOTO_BYTES:
                raise ValueError('Photo exceeds 10 MiB archive limit')
            filename = 'photo-' + hashlib.sha256(original.encode()).hexdigest()[:24] + PHOTO_TYPES[mime]
            fd, temporary = tempfile.mkstemp(prefix='.download-', dir=target_dir)
            try:
                size = 0
                with os.fdopen(fd, 'wb') as output:
                    for chunk in response.iter_bytes():
                        size += len(chunk)
                        if size > MAX_PHOTO_BYTES: raise ValueError('Photo exceeds 10 MiB archive limit')
                        output.write(chunk)
                if not size: raise ValueError('Empty photo response')
                os.replace(temporary, target_dir / filename)
            finally:
                if os.path.exists(temporary): os.unlink(temporary)
            return filename
    raise AccessError('Too many photo redirects')


def sync_properties(property_ids=None, download=False, max_downloads=40):
    """Write all metadata first, then attempt a bounded number of missing photos."""
    root = archive_root()
    report = {'root':str(root), 'properties':0, 'downloaded':0, 'pending_photos':0, 'photo_errors':0, 'errors':[]}
    ids = None if property_ids is None else list(dict.fromkeys(int(value) for value in property_ids))
    if ids == []: return report
    with single_job('property_archive'):
        with connect() as con:
            query = 'SELECT * FROM properties WHERE is_demo=0'
            if ids is not None: query += ' AND id IN (' + ','.join('?' for _ in ids) + ')'
            rows = [dict(row) for row in con.execute(query + ' ORDER BY id', ids or [])]
            facilities = {}
            for item in rows:
                facilities[item['id']] = [dict(row) for row in con.execute('SELECT * FROM amenities WHERE property_id=? ORDER BY distance_km',(item['id'],))]
        jobs = []
        for item in rows:
            identifier = f"property-{item['id']:06d}"
            try:
                folder = within(root, root / segment(item['district']) / segment(item['area_name']) / identifier)
                index = within(root, root / 'by-id' / (identifier + '.json'))
                previous = read_json(index, {})
                if previous.get('folder'):
                    old = within(root, root / previous['folder'])
                    if old.name != identifier: raise ValueError('Archive index does not match property ID')
                    if old != folder and old.exists():
                        # Both absolute paths are verified inside root before the recursive move.
                        if folder.exists(): raise ValueError('Destination archive folder already exists')
                        folder.parent.mkdir(parents=True, exist_ok=True)
                        shutil.move(str(old), str(folder))
                folder.mkdir(parents=True, exist_ok=True)
                photo_dir = within(root, folder / 'photos')
                photo_dir.mkdir(exist_ok=True)
                for key in ('quality_flags','image_urls'):
                    if isinstance(item.get(key), str): item[key] = json.loads(item[key] or '[]')
                for key in ('road_is_pitched','road_under_construction'):
                    if item.get(key) is not None: item[key] = bool(item[key])
                common = {'property_id':item['id'], 'archive_id':identifier, 'source_url':item['source_url']}
                atomic_json(within(root, folder / 'property.json'), {**item, 'archive_id':identifier})
                location_keys = ('address','area_name','district','ward','lat','lng','geocode_status','geocode_precision')
                atomic_json(within(root, folder / 'location.json'), {**common, **{key:item.get(key) for key in location_keys}})
                atomic_json(within(root, folder / 'contact.json'), {**common, 'name':item.get('contact_name'),
                            'phone':item.get('contact_phone'), 'role':item.get('contact_role') or 'unknown', 'ownership_verified':False})
                atomic_json(within(root, folder / 'facilities.json'), {**common, 'radius_m':item.get('enrichment_radius_m'),
                            'status':item.get('enrichment_status'), 'items':facilities[item['id']]})
                manifest_path = within(root, photo_dir / 'manifest.json')
                previous_photos = {entry['source_url']:entry for entry in read_json(manifest_path, {}).get('photos',[])}
                entries = []
                for url in photo_candidates(item)[:30]:
                    entry = previous_photos.get(url, {'source_url':url,'status':'pending','file':None})
                    if entry.get('file'):
                        photo = within(root, photo_dir / entry['file'])
                        if photo.parent != photo_dir or not photo.is_file(): entry = {'source_url':url,'status':'pending','file':None}
                    entries.append(entry)
                manifest = {**common, 'photos':entries}
                atomic_json(manifest_path, manifest)
                atomic_json(index, {**common, 'folder':folder.relative_to(root).as_posix()})
                jobs.append((photo_dir, manifest_path, manifest))
                report['properties'] += 1
            except Exception as exc: report['errors'].append({'property_id':item['id'], 'message':str(exc)})
        client = Client(delay=1, public_only=True) if download else None
        attempts = 0
        unavailable_hosts = set()
        try:
            for photo_dir, path, manifest in jobs:
                for entry in manifest['photos']:
                    if entry['status'] == 'downloaded' and entry.get('file'): continue
                    retry_due = True
                    if entry.get('attempted_at'):
                        try: retry_due = datetime.fromisoformat(entry['attempted_at']) < datetime.now(timezone.utc)-timedelta(hours=6)
                        except ValueError: pass
                    host = urlparse(entry['source_url']).netloc
                    if client and attempts < max_downloads and retry_due and host not in unavailable_hosts:
                        attempts += 1
                        try:
                            entry['file'] = download_photo(entry['source_url'], photo_dir, client)
                            entry.update(status='downloaded', downloaded_at=now())
                            entry.pop('error', None)
                            report['downloaded'] += 1
                        except Exception as exc:
                            entry.update(status='error', error=str(exc), attempted_at=now())
                            report['photo_errors'] += 1
                            if isinstance(exc, (AccessError, httpx.TransportError)):
                                unavailable_hosts.add(host)
                    elif client and host in unavailable_hosts:
                        entry.update(status='error', error='Photo host unavailable; retry in a later batch', attempted_at=now())
                    if entry['status'] != 'downloaded': report['pending_photos'] += 1
                atomic_json(path, manifest)
        finally:
            if client: client.close()
    return report


def sync_if_enabled(property_ids=None, download=False):
    if not enabled(): return {'disabled':True}
    try:
        return sync_properties(property_ids, download=download,
                               max_downloads=max(0,min(200,int(os.getenv('LAND_ARCHIVE_PHOTO_BATCH','40')))))
    except Exception as exc:
        return {'errors':[{'message':str(exc)}]}
