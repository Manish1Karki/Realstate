"""Bounded public-photo availability checks. Transient outages do not unpublish listings."""
import json
import re
from datetime import datetime, timedelta, timezone
from .db import connect, now
from .http import Client

def photo_candidates(item):
    values = item.get('image_urls') or []
    if isinstance(values, str):
        try: values = json.loads(values)
        except (ValueError,TypeError): values = []
    return list(dict.fromkeys(url for url in [item.get('image_url'), *values] if isinstance(url,str)
        and url.startswith('https://') and not re.search(r'/static/|og-image|logo|placeholder',url,re.I)))

def check_photo(url, client):
    """True for image responses, False for confirmed missing/non-images, None for transient/policy failures."""
    from urllib.parse import urljoin
    try:
        for _ in range(4):
            delay = client.robots(url)
            response = client.request('HEAD', url, delay=delay)
            if response.is_redirect:
                url = urljoin(url,response.headers['location'])
                continue
            if response.status_code in (404,410): return False
            if response.status_code != 200: return None
            mime = response.headers.get('content-type','').split(';')[0].lower()
            return mime.startswith('image/') and mime != 'image/svg+xml' and response.headers.get('content-length') != '0'
    except Exception: return None
    return None

def validate_pending(limit=40):
    cutoff = (datetime.now(timezone.utc)-timedelta(hours=6)).isoformat()
    with connect() as con:
        rows = [dict(row) for row in con.execute("SELECT * FROM properties WHERE is_demo=0 AND (photo_checked_at IS NULL OR photo_checked_at<?) ORDER BY photo_checked_at IS NOT NULL,photo_checked_at,id LIMIT ?",(cutoff,limit))]
    report = dict(checked=0,available=0,unavailable=0,deferred=0)
    client = Client(delay=1,public_only=True)
    remaining=120
    try:
        for item in rows:
            if remaining <= 0: break
            candidates = photo_candidates(item)
            checked = []
            for url in candidates[:20]:
                if remaining <= 0: break
                remaining-=1
                checked.append((url,check_photo(url,client)))
                if checked[-1][1] is True: break
            good = next((url for url,valid in checked if valid is True),None)
            confirmed = not candidates or (len(checked)==len(candidates) and all(valid is False for _,valid in checked))
            failures = 0 if good else (item.get('photo_failures') or 0)+1 if confirmed else item.get('photo_failures') or 0
            status = 'available' if good else ('invalid' if failures>=2 else item.get('photo_status') or 'unknown') if confirmed else item.get('photo_status') or 'unknown'
            with connect() as con:
                con.execute('UPDATE properties SET photo_status=?,photo_checked_at=?,photo_failures=? WHERE id=?',(status,now(),failures,item['id']))
                if status == 'available' and item.get('photo_status') == 'invalid':
                    con.execute('UPDATE properties SET content_updated_at=? WHERE id=?',(now(),item['id']))
                if good and good != item.get('image_url'):
                    con.execute('UPDATE properties SET image_url=?,content_updated_at=? WHERE id=?',(good,now(),item['id']))
            report['checked']+=1
            report['available' if good else 'unavailable' if status=='invalid' else 'deferred']+=1
    finally: client.close()
    return report

if __name__ == '__main__':
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--limit',type=int,default=40)
    print(json.dumps(validate_pending(max(1,min(parser.parse_args().limit,100)))))
