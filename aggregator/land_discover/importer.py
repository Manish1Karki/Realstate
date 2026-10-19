"""Bounded imports from user-supplied public property pages."""
import json, os
import re
from urllib.parse import urlparse, urljoin, urldefrag
from bs4 import BeautifulSoup
from .db import connect, now, upsert
from .http import Client, AccessError, validate_public_url
from .locking import single_job
from .scraper import parse_detail, review, apply_public_location
from .sources import SOURCES
from .eligibility import is_recent_listing

def links(html, url, host):
    soup=BeautifulSoup(html,'html.parser')
    found=[]; next_url=None
    for a in soup.select('a[href]'):
        target=urldefrag(urljoin(url,a['href']))[0]
        parsed=urlparse(target)
        if parsed.scheme!='https' or parsed.hostname!=host: continue
        if 'next' in a.get('rel',[]) or a.get_text(' ',strip=True).lower() in ('next','next page'):
            next_url=target
        elif re.search(r'/(?:property|properties|listing|listings|detail|real-estate)/[^/]+',parsed.path,re.I):
            found.append(target)
    return list(dict.fromkeys(found)),next_url

def import_url(url, max_pages=1, max_listings=10):
    url=urldefrag(url.strip())[0]
    validate_public_url(url)
    host=urlparse(url).hostname
    source=next((key for key,config in SOURCES.items() if config['host']==host),host)
    client=Client(delay=3,public_only=True)
    report=dict(pages=0,imported=0,rejected=0,skipped=0,errors=[],property_ids=[])
    with single_job('scraper'):
        with connect() as con:
            run_id=con.execute("INSERT INTO runs(source,started_at,status) VALUES (?,?,'running')",(source,now())).lastrowid
        status='failed'
        try:
            if source in SOURCES: review(source,client)
            visited=set(); seen=set(); page=url
            while page and page not in visited and report['pages']<max_pages and len(seen)<max_listings:
                visited.add(page)
                html=client.page(page,host); report['pages']+=1
                try: item=apply_public_location(parse_detail(html,page,source),html)
                except ValueError: item=None
                if item is not None:
                    if not is_recent_listing(item):
                        report['skipped']+=1
                        report['errors'].append(dict(url=page,message='Listing date unknown, future, or older than six months'))
                        break
                    report['property_ids'].append(upsert(item)); report['imported']+=1
                    break
                candidates,page_next=links(html,page,host)
                if not candidates: raise ValueError('No readable property details or listing links found. This site may require a dedicated adapter or JavaScript rendering.')
                for target in candidates:
                    if target in seen or target in visited: continue
                    if len(seen)>=max_listings: break
                    seen.add(target)
                    try:
                        detail_html=client.page(target,host)
                        item=apply_public_location(parse_detail(detail_html,target,source),detail_html)
                        if not is_recent_listing(item):
                            report['skipped']+=1
                            continue
                        report['property_ids'].append(upsert(item)); report['imported']+=1
                    except AccessError: raise
                    except ValueError as exc:
                        report['rejected']+=1; report['errors'].append(dict(url=target,message=str(exc)))
                page=page_next
            status='complete' if report['imported'] and not report['errors'] else 'partial' if report['imported'] else 'failed'
        except Exception as exc: report['errors'].append(dict(message=str(exc))); status='partial' if report['imported'] else 'failed'
        finally:
            client.close()
            with connect() as con:
                con.execute('UPDATE runs SET finished_at=?,status=?,pages=?,imported=?,rejected=?,errors=? WHERE id=?',(now(),status,report['pages'],report['imported'],report['rejected'],json.dumps(report['errors']),run_id))
    if report['property_ids'] and os.getenv('LAND_AUTO_ENRICH','true').lower()=='true':
        try:
            from .geo import enrich
            radius=int(os.getenv('LAND_AUTO_ENRICH_RADIUS','2000'))
            report['location_enrichment']=enrich(max_listings,radius=radius,property_ids=report['property_ids'])
        except Exception as exc:
            report['location_enrichment']={'errors':[{'message':str(exc)}]}
    if report['property_ids']:
        from .archive import sync_if_enabled
        report['property_archive'] = sync_if_enabled(report['property_ids'], download=True)
    return dict(run_id=run_id,status=status,**report)
