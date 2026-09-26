import hashlib, json, re
from datetime import date
from urllib.parse import urljoin, urlparse, urldefrag
from bs4 import BeautifulSoup
from .db import ROOT, connect, now, upsert
from .http import Client, AccessError
from .sources import SOURCES
from .normalize import normalize, clean
from .locking import single_job

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

def parse_detail(html,url,source):
    if source=='hamrobazar':
        from .hamrobazar import parse
        return parse(html,url)
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
    # A source must explicitly say sale/rent; an unknown transaction is not a sale.
    main_text=(soup.find('main') or soup).get_text(' ',strip=True)
    title=raw['title'].lower()
    raw['transaction_type']='rent' if re.search(r'\bfor rent\b',title) else 'sale' if re.search(r'\bfor sale\b',title) else 'unknown'
    if raw['transaction_type']=='rent' and not re.search(r'per|/',raw['price_raw'],re.I): raw['price_raw']+=' per month'
    item=normalize(raw)
    # Detect conflicting unit evidence anywhere in detail text; do not treat unit prices as totals.
    if item['price_basis']=='total' and re.search(r'(?:per|/)\s*(?:aana|anna|ana|ropani|sq\.?\s*ft)\b',main_text,re.I):
        item['total_price_npr']=None; item['price_basis']='unknown'; item['quality_flags'].append('Unit-price evidence needs review')
    return item

def discover(html,url,source):
    config=SOURCES[source]; soup=BeautifulSoup(html,'html.parser')
    links=[]; next_url=None
    for a in soup.select('a[href]'):
        target=urldefrag(urljoin(url,a['href']))[0]
        parsed=urlparse(target)
        if parsed.scheme!='https' or parsed.hostname!=config['host']: continue
        if config['detail_path'] and config['detail_path'] in parsed.path: links.append(target)
        rel=a.get('rel',[]); label=clean(a.get('aria-label') or a.get_text()).lower()
        if 'next' in rel or label in ('next','next page','next »','»'): next_url=target
    return list(dict.fromkeys(links)),next_url

def review(source,client):
    config=SOURCES[source]
    if config.get('status')=='public_html':
        from .policy import hamrobazar_terms_digest
        age=(date.today()-date.fromisoformat(config['reviewed_on'])).days
        if not 0<=age<=30:raise AccessError('Public source review expired; review current rules again')
        terms=client.page(config['terms_url'],config['host'])
        if hamrobazar_terms_digest(terms)!=config['terms_sha256']:
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
    if not 1<=max_pages<=10 or not 1<=max_listings<=100: raise ValueError('Use 1–10 pages and 1–100 listings per run')
    with single_job('scraper'):
        return _scrape(source,max_pages,max_listings)

def _scrape(source,max_pages,max_listings):
    c=Client(delay=3); report={'pages':0,'imported':0,'rejected':0,'skipped':0,'errors':[],'property_ids':[],'notes':[]}
    with connect() as con:
        run_id=con.execute("INSERT INTO runs(source,started_at,status) VALUES (?,?,'running')",(source,now())).lastrowid
    status='failed'
    try:
        review(source,c)
        config=SOURCES[source]; url=config['start_url']; visited=set(); seen=set()
        while url and url not in visited and report['pages']<max_pages and len(seen)<max_listings:
            visited.add(url); html=c.page(url,config['host']); report['pages']+=1
            links,next_url=discover(html,url,source)
            if not links: raise ValueError('No detail links found; selectors or JS rendering need re-validation')
            for link in links:
                if link in seen: continue
                if len(seen)>=max_listings: break
                seen.add(link)
                try:
                    property_id=upsert(parse_detail(c.page(link,config['host']),link,source))
                    report['imported']+=1;report['property_ids'].append(property_id)
                except AccessError: raise
                except Exception as e:
                    from .hamrobazar import OutOfScope
                    if isinstance(e,OutOfScope):report['skipped']+=1
                    else:report['rejected']+=1;report['errors'].append({'url':link,'message':str(e)})
            if not next_url:report['notes'].append('No public next-page link present. Collected this HTML page only; no disallowed API pagination attempted.')
            url=next_url
        status='complete' if not report['errors'] else 'partial'
    except Exception as e: report['errors'].append({'message':str(e)})
    finally:
        c.close()
        with connect() as con:
            con.execute('UPDATE runs SET finished_at=?,status=?,pages=?,imported=?,rejected=?,errors=? WHERE id=?',(now(),status,report['pages'],report['imported'],report['rejected'],json.dumps(report['errors']),run_id))
    return dict(run_id=run_id,status=status,**report)
