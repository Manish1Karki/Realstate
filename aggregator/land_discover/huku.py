"""Adapter for HUKU's public server-rendered detail pages."""
import json
import re
from urllib.parse import urlparse
from datetime import datetime
from bs4 import BeautifulSoup
from .normalize import clean, normalize, DISTRICTS
from .hamrobazar import OutOfScope, extract_address

def parse(html,url):
    parsed=urlparse(url)
    url=parsed._replace(path=parsed.path.rstrip('/'),query='',fragment='').geturl()
    from .scraper import ld_items
    from .media import enrich
    soup=BeautifulSoup(html,'html.parser')
    main=soup.find('main'); h1=soup.find('h1')
    if not main or not h1: raise ValueError('HUKU property detail structure missing')
    title=clean(h1.get_text(' ',strip=True))
    # Only inspect the property header, never similar property cards.
    header=main.find('section')
    header_text=header.get_text(' ',strip=True) if header else ''
    kind=re.search(r'\b(House|Land|Apartment|Flat)\s+For\s+(Sale|Rent)\b',header_text,re.I)
    if not kind: raise OutOfScope('Unsupported HUKU property category')
    property_type='apartment' if kind[1].lower()=='flat' else kind[1].lower()
    transaction=kind[2].lower()
    labels={}
    heading=next((h for h in main.find_all('h2') if clean(h.get_text())=='Features'),None)
    if heading:
        for span in heading.parent.select('span'):
            label=clean(span.get_text()).rstrip(':').strip().lower()
            value=span.find_next_sibling('span')
            if value: labels[label]=clean(value.get_text(' ',strip=True))
    desc_heading=next((h for h in main.find_all('h2') if clean(h.get_text())=='Description'),None)
    desc_node=desc_heading.find_next_sibling('p') if desc_heading else None
    description=desc_node.get_text('\n',strip=True) if desc_node else ''
    obj={}
    for script in soup.select('script[type="application/ld+json"]'):
        try: objects=ld_items(json.loads(script.get_text()))
        except (TypeError,ValueError): continue
        for candidate in objects:
            if candidate.get('@type')=='RealEstateListing': obj=candidate
    address=obj.get('address',{})
    if isinstance(address,dict): address=', '.join(dict.fromkeys(str(address[k]) for k in ('streetAddress','addressLocality','addressRegion') if address.get(k)))
    # Prefer explicitly labelled location, then a locality in the title.
    # Nearby schools/roads in descriptions are not the property's address.
    explicit=re.search(r'\bLocation\s*:\s*([^\n]+)',description,re.I)
    title_area=re.search(r'\b(?:sale|rent)\s+(?:in|at)\s+([^|]+)',title,re.I)
    district=next((d for d in DISTRICTS if d.lower() in str(address).lower()),None)
    inferred=False
    if explicit and any(d.lower() in explicit[1].lower() for d in DISTRICTS):
        address=clean(explicit[1])
    elif title_area and district:
        address=clean(title_area[1]).strip(' ,')
        if district.lower() not in address.lower(): address+=', '+district
        inferred=True
    elif not address:
        address,inferred=extract_address(title,'')
    offer=obj.get('offer') or obj.get('offers') or {}
    if offer and offer.get('priceCurrency')!='NPR': raise ValueError('Unsupported HUKU currency')
    price_node=next((p for p in header.find_all('p') if re.match(r'\s*Rs\.',p.get_text())),None) if header else None
    price=clean(price_node.get_text(' ',strip=True)).replace('/-','') if price_node else str(offer.get('price',''))
    if transaction=='rent' and not re.search(r'per\s+month|/\s*month',price,re.I): price+=' per month'
    date_raw=obj.get('datePosted','')
    try: date_raw=datetime.strptime(date_raw[:15],'%a %b %d %Y').date().isoformat()
    except (ValueError,TypeError): pass
    road=', '.join(filter(None,[labels.get('road size (ft)'),labels.get('road type')]))
    item=normalize(dict(source='huku',source_url=url,title=title,address=address,property_type=property_type,transaction_type=transaction,price_raw=price,size=labels.get('size/area',''),listing_date_raw=date_raw,road_access_note=road))
    item=enrich(item,html,url)
    if inferred: item['quality_flags'].append('Locality taken from public title; not a verified parcel address')
    item['description']=description[:5000] or item['description']
    for key in ('bedrooms','bathrooms'):
        value=labels.get(key,'')
        item[key]=int(value) if re.fullmatch(r'\d{1,2}',value) else None
    # SoldOut appears in schema even on advertised rentals; retain the
    # conflict as a review flag rather than silently deciding availability.
    if offer.get('availability','').endswith('SoldOut'):
        item['quality_flags'].append('Source schema says SoldOut; verify availability on original listing')
    return item
