import hashlib, json, os, re
import httpx
from datetime import date
from urllib.parse import urljoin, urlparse, urldefrag
from bs4 import BeautifulSoup
from .db import ROOT, connect, now, upsert
from .http import Client, AccessError
from .sources import SOURCES
from .normalize import normalize, clean
from .locking import single_job
from .eligibility import is_recent_listing, has_property_information, nepal_today, six_month_cutoff

def fields(soup):
    """Label/value semantics rather than brittle positional class selectors."""
    result={}
    for node in soup.select('li, tr, dt'):
        if node.name=='dt':
            value=node.find_next_sibling('dd')
            if value: result[clean(node.get_text()).lower().rstrip(':')]=clean(value.get_text(' ',strip=True))
        elif node.name=='tr':
            cols=node.find_all(['td','th'],recursive=False)
            if len(cols)==2: result[clean(cols[0].get_text()).lower().rstrip(':')]=clean(cols[1].get_text(' ',strip=True))
        else:
            value=clean(node.get_text(' ',strip=True))
            if ':' in value and len(value)<350:
                k,v=value.split(':',1); result.setdefault(k.lower().strip(),v.strip())
    return result

def ld_items(value):
    if isinstance(value,list):
        for obj in value: yield from ld_items(obj)
    elif isinstance(value,dict):
        yield value
        if '@graph' in value: yield from ld_items(value['@graph'])
        if isinstance(value.get('mainEntity'),(dict,list)): yield from ld_items(value['mainEntity'])
        for key in ('about','itemOffered','containsPlace'):
            if isinstance(value.get(key),(dict,list)): yield from ld_items(value[key])

def parse_detail(html,url,source):
    if SOURCES.get(source, {}).get('adapter') == 'public_sources':
        from .public_sources import parse
        return parse(html, url, source)
    if source in ('epropertynepal','nepalbhoomi'):
        from importlib import import_module
        return import_module('.'+source, __package__).parse(html,url)
    if source=='huku':
        from .huku import parse
        return parse(html,url)
    if source=='hamrobazar':
        from .hamrobazar import parse
        from .media import enrich
        return enrich(parse(html,url),html,url)
    soup=BeautifulSoup(html,'html.parser'); labels=fields(soup)
    h1=soup.find('h1')
    raw=dict(source=source,source_url=url,title=clean(h1.get_text(' ',strip=True)) if h1 else '')
    for script in soup.select('script[type="application/ld+json"]'):
        try: objs=list(ld_items(json.loads(script.get_text())))
        except (ValueError,TypeError): continue
        for obj in objs:
            types=obj.get('@type',[]); types=[types] if isinstance(types,str) else types
            if not set(types)&{'Product','RealEstateListing','House','Apartment','Residence','SingleFamilyResidence','Place'}: continue
            raw['title']=obj.get('name') or raw['title']
            address=obj.get('address')
            if isinstance(address,dict): address=', '.join(str(address[k]) for k in ('streetAddress','addressLocality','addressRegion') if address.get(k))
            if isinstance(address,str): raw['address']=address
            offers=obj.get('offers',{}); offers=offers[0] if isinstance(offers,list) and offers else offers
            if isinstance(offers,dict) and offers.get('priceCurrency')=='NPR' and offers.get('price') is not None:
                raw['price_raw']=str(offers['price'])
                spec=offers.get('priceSpecification',{})
                if isinstance(spec,dict) and spec.get('unitText'): raw['price_raw']+=' per '+str(spec['unitText'])
            raw['listing_date_raw']=obj.get('datePosted') or obj.get('datePublished') or ''
            floor=obj.get('floorSize',{})
            if isinstance(floor,dict) and floor.get('value') and floor.get('unitText'): raw['size']=str(floor['value'])+' '+floor['unitText']
            if 'Apartment' in types: raw['property_type']='apartment'
            elif set(types)&{'House','SingleFamilyResidence'}: raw['property_type']='house'
    for key,aliases in {'address':['location','address'],'size':['land area','land size','size','area'],'price_raw':['price','asking price'],'listing_date_raw':['listed on','posted on','listing date'],'road_access_note':['road description','road access']}.items():
        for alias in aliases:
            if labels.get(alias): raw[key]=labels[alias]; break
    category=labels.get('category') or labels.get('property type') or raw.get('property_type','')
    kind=re.search(r'\b(land|house|apartment)\b',category,re.I)
    if not kind: kind=re.search(r'\b(land|house|apartment)\b',raw['title'],re.I)
    raw['property_type']=kind[1].lower() if kind else ''
    if source=='gharbazar':
        # Observed public page heading and semantic labels; not live-validated.
        price=next((x for x in soup.find_all('h2') if re.match(r'\s*Rs\.',x.get_text())),None)
        if price: raw['price_raw']=price.get_text(' ',strip=True).split('(')[0].strip()
    raw.setdefault('price_raw','')
    if not raw.get('address'):
        from .hamrobazar import extract_address
        description=soup.select_one('meta[name="description"], meta[property="og:description"], [itemprop="description"]')
        text=(description.get('content') or description.get_text(' ',strip=True)) if description else ''
        raw['address'], inferred=extract_address(raw['title'],text)
    # A source must explicitly say sale/rent; an unknown transaction is not a sale.
    main_text=(soup.find('main') or soup).get_text(' ',strip=True)
    title=raw['title'].lower()
    raw['transaction_type']='rent' if re.search(r'\bfor rent\b',title) else 'sale' if re.search(r'\bfor sale\b',title) else 'unknown'
    if raw['transaction_type']=='rent' and not re.search(r'per|/',raw['price_raw'],re.I): raw['price_raw']+=' per month'
    item=normalize(raw)
    # Detect conflicting unit evidence anywhere in detail text; do not treat unit prices as totals.
    if item['price_basis']=='total' and re.search(r'(?:per|/)\s*(?:aana|anna|ana|ropani|sq\.?\s*ft)\b',main_text,re.I):
        item['total_price_npr']=None; item['price_basis']='unknown'; item['quality_flags'].append('Unit-price evidence needs review')
    from .media import enrich
    return enrich(item,html,url)

def apply_public_location(item,html):
    """Keep only coordinates explicitly published in this listing's public page."""
    from .source_location import extract_public_coordinates
    item=dict(item)
    point=extract_public_coordinates(html)
    if point:
        item.update(lat=point[0],lng=point[1],geocode_status='matched',
                    geocode_precision='source map pin (unverified)',
                    geocode_label=item.get('address'),geo_error=None)
    else:
        item.update(lat=None,lng=None,geocode_status='pending',geocode_precision=None,
                    geocode_label=None,geo_error=None,enrichment_status='pending',
                    enrichment_radius_m=None,enriched_date=None,nearest_school=None,
                    school_distance_km=None,nearest_hospital=None,hospital_distance_km=None,
                    nearest_road=None,road_distance_km=None,amenity_count=None,amenity_score=None)
    return item

def discover(html,url,source):
    config=SOURCES[source]; soup=BeautifulSoup(html,'html.parser')
    links=[]; next_url=None
    for a in soup.select('a[href]'):
        target=urldefrag(urljoin(url,a['href']))[0]
        parsed=urlparse(target)
        if parsed.scheme!='https' or parsed.hostname!=config['host']: continue
        if config.get('detail_pattern'):
            if re.fullmatch(config['detail_pattern'],parsed.path):
                if source=='huku' or config.get('status') in ('local_trial','reviewed_public'): target=parsed._replace(path=parsed.path if config.get('canonical_trailing_slash') else parsed.path.rstrip('/'),query='').geturl()
                links.append(target)
        elif config['detail_path'] and config['detail_path'] in parsed.path: links.append(target)
        rel=a.get('rel',[]); label=clean(a.get('aria-label') or a.get_text()).lower()
        if 'next' in rel or label in ('next','next page','older posts','next '+chr(187),chr(187)):
            current_path=urlparse(url).path.rstrip('/')
            if parsed.path.rstrip('/')==current_path or re.fullmatch(re.escape(current_path)+r'/page/\d+/?',parsed.path):
                next_url=target
    return list(dict.fromkeys(links)),next_url

def review(source,client):
    config=SOURCES[source]
    if config.get('status')=='reviewed_public':
        age=(date.today()-date.fromisoformat(config['reviewed_on'])).days
        if not 0<=age<=30: raise AccessError('Source review expired; inspect public pages again')
        if config.get('terms_url'):
            from .policy import public_terms_digest
            if public_terms_digest(client.page(config['terms_url'],config['host'])) != config.get('terms_sha256'):
                raise AccessError('Source policy changed; review required')
        return
    if config.get('status')=='local_trial':
        from .sources import local_trials_enabled
        if not local_trials_enabled():
            raise AccessError('Experimental source disabled. Use the isolated local source trial; hosted collection is not enabled.')
        age=(date.today()-date.fromisoformat(config['reviewed_on'])).days
        if not 0<=age<=30: raise AccessError('Local trial inspection expired; inspect the source again')
        return
    if config.get('status')=='public_html':
        from .policy import hamrobazar_terms_digest, huku_terms_digest
        age=(date.today()-date.fromisoformat(config['reviewed_on'])).days
        if not 0<=age<=30:raise AccessError('Public source review expired; review current rules again')
        try:
            terms=client.page(config['terms_url'],config['host'])
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code==403:
                raise AccessError(f"{config['name']} denied the public terms request (HTTP 403). Collection stopped for this run. Source approval or a supported listing feed is needed for this backend.") from exc
            raise
        digest=huku_terms_digest(terms) if source=='huku' else hamrobazar_terms_digest(terms)
        if digest!=config['terms_sha256']:
            raise AccessError('Published terms changed; review required before collecting more listings')
        return
    if not config['adapter']: raise AccessError(config['reason'])
    file=ROOT/'source_reviews.json'
    reviews=json.loads(file.read_text()) if file.exists() else {}
    approval=reviews.get(source,{})
    if not approval.get('enabled') or not approval.get('live_validated'):
        raise AccessError(config['reason']+' See docs/SOURCES.md.')
    if not approval.get('permission_evidence'): raise AccessError('Source review needs permission/reuse evidence')
    try: age=(date.today()-date.fromisoformat(approval['reviewed_on'])).days
    except (KeyError,ValueError): raise AccessError('Missing source review date')
    if not 0<=age<=30: raise AccessError('Source review expired; review current rules again')
    terms=client.page(config['terms_url'],config['host'])
    digest=hashlib.sha256(terms.encode()).hexdigest()
    if digest!=approval.get('terms_sha256'): raise AccessError('Terms page changed; re-review required')

def scrape(source,max_pages=2,max_listings=20):
    if source not in SOURCES: raise ValueError('Unknown source')
    if not 1<=max_pages<=30 or not 1<=max_listings<=300: raise ValueError('Use 1-30 pages and 1-300 listings per run')
    with single_job('scraper'):
        return _scrape(source,max_pages,max_listings)

def _scrape(source,max_pages,max_listings):
    c=Client(delay=3); report={'pages':0,'imported':0,'rejected':0,'skipped':0,'errors':[],'property_ids':[],'notes':[],'skip_reasons':{},'inspected':0}
    with connect() as con:
        run_id=con.execute("INSERT INTO runs(source,started_at,status) VALUES (?,?,'running')",(source,now())).lastrowid
    status='failed'
    try:
        review(source,c)
        config=SOURCES[source]; pending=list(config.get('start_urls') or [config['start_url']]); visited=set(); seen=set()
        if config.get('status')=='local_trial': report['notes'].append(config['reason'])
        while pending and report['pages']<max_pages and len(seen)<max_listings:
            url=pending.pop(0)
            if url in visited: continue
            visited.add(url); html=c.page(url,config['host']); report['pages']+=1
            links,next_url=discover(html,url,source)
            if not links: raise ValueError('No detail links found; selectors or JS rendering need re-validation')
            for link in links:
                if link in seen: continue
                if len(seen)>=max_listings: break
                seen.add(link); report['inspected']+=1
                try:
                    detail_html=c.page(link,config['host'])
                    item=parse_detail(detail_html,link,source)
                    if not is_recent_listing(item):
                        report['skipped']+=1
                        reason='date_unknown' if not item.get('listing_date') else 'date_future' if item['listing_date']>nepal_today().isoformat() else 'older_than_six_months'
                        report['skip_reasons'][reason]=report['skip_reasons'].get(reason,0)+1
                        continue
                    if not has_property_information(item):
                        report['skipped']+=1
                        report['skip_reasons']['missing_property_information']=report['skip_reasons'].get('missing_property_information',0)+1
                        continue
                    item=apply_public_location(item,detail_html)
                    property_id=upsert(item)
                    report['imported']+=1;report['property_ids'].append(property_id)
                except AccessError: raise
                except Exception as e:
                    from .hamrobazar import OutOfScope
                    if isinstance(e,OutOfScope):report['skipped']+=1
                    else:report['rejected']+=1;report['errors'].append({'url':link,'message':str(e)})
            if not next_url:report['notes'].append('No public next-page link present. Collected this HTML page only; no disallowed API pagination attempted.')
            if next_url and next_url not in visited and next_url not in pending: pending.append(next_url)
        status='complete' if not report['errors'] else 'partial'
    except Exception as e:
        report['errors'].append({'message':str(e)})
        if report['imported']: status='partial'
    finally:
        c.close()
        with connect() as con:
            con.execute('UPDATE runs SET finished_at=?,status=?,pages=?,imported=?,rejected=?,errors=? WHERE id=?',(now(),status,report['pages'],report['imported'],report['rejected'],json.dumps(report['errors']),run_id))
    if report['property_ids'] and os.getenv('LAND_AUTO_GEOCODE','false').lower()=='true':
        try:
            from .geo import geocode_pending
            report['location_geocoding']=geocode_pending(max_listings,property_ids=report['property_ids'])
        except Exception as exc:
            report['location_geocoding']={'errors':[{'message':str(exc)}]}
    if report['property_ids'] and os.getenv('LAND_AUTO_ENRICH','false').lower()=='true':
        try:
            from .geo import enrich
            radius=int(os.getenv('LAND_AUTO_ENRICH_RADIUS','1500'))
            report['location_enrichment']=enrich(max_listings,radius=radius,property_ids=report['property_ids'])
        except Exception as exc:
            report['location_enrichment']={'errors':[{'message':str(exc)}]}
    return dict(run_id=run_id,status=status,**report)
