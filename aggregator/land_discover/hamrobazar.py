"""Public HTML adapter verified against Hamrobazar's September 2026 pages.

Reads visible listing content and its public Product JSON-LD only. Does not use
hydration internals, private APIs, masked location fields, or seller contacts.
"""
import json
import re
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from .normalize import clean, normalize, parse_size

DISTRICT_ALIASES={'काठमाडौं':'Kathmandu','काठमाडौँ':'Kathmandu','ललितपुर':'Lalitpur','भक्तपुर':'Bhaktapur'}
LOCALITIES={'baneshwor':'Kathmandu','lazimpat':'Kathmandu','budhanilkantha':'Kathmandu','budanilkantha':'Kathmandu','boudha':'Kathmandu','jorpati':'Kathmandu','kalanki':'Kathmandu','kirtipur':'Kathmandu','tokha':'Kathmandu','golfutar':'Kathmandu','bhaisepati':'Lalitpur','imadol':'Lalitpur','jhamsikhel':'Lalitpur','sanepa':'Lalitpur','sunakothi':'Lalitpur','dhapakhel':'Lalitpur','khumaltar':'Lalitpur','tikathali':'Lalitpur','thimi':'Bhaktapur','sallaghari':'Bhaktapur','suryabinayak':'Bhaktapur','dadhikot':'Bhaktapur','balkot':'Bhaktapur'}
UNIT=r'(?:ropani|aana|anna|ana|paisa|daam|dam|sq\.?\s*ft\.?|sqft|square feet|रोपनी|आना|पैसा|दाम)'
SIZE_RE=re.compile(r'\d+(?:\.\d+)?\s*'+UNIT+r'(?:\s*[,;]?\s*\d+(?:\.\d+)?\s*'+UNIT+r')*',re.I)

class OutOfScope(ValueError): pass

def visible_description(soup):
    for heading in soup.find_all(['h2','h3']):
        if clean(heading.get_text())=='About this listing':
            section=heading.find_parent('section')
            p=section.find('p') if section else None
            return p.get_text('\n',strip=True) if p else ''
    return ''

def product_schema(soup):
    for script in soup.select('script[type="application/ld+json"]'):
        try: value=json.loads(script.get_text())
        except ValueError: continue
        if isinstance(value,dict) and value.get('@type')=='Product': return value
    raise ValueError('Hamrobazar Product schema missing; page structure needs review')

def specifications(soup):
    for heading in soup.find_all(['h2','h3']):
        if clean(heading.get_text())=='Specifications':
            section=heading.find_parent('section')
            grid=section.select_one('div.grid') if section else None
            if grid:
                cells=grid.find_all('div',recursive=False)
                return {clean(cells[i].get_text()):clean(cells[i+1].get_text()) for i in range(0,len(cells)-1,2)}
    return {}

def extract_address(title,description):
    text=title+'\n'+description
    for native,english in DISTRICT_ALIASES.items(): text=text.replace(native,english)
    match=re.search(r'(?:\bat\b|\bin\b|location\s*[:–-]|address\s*[:–-])\s*([^\n.!?]{2,100}?\b(?:Kathmandu|Lalitpur|Bhaktapur)\b)',text,re.I)
    if match:
        candidate=clean(match[1]).strip(' ,:-')
        # Avoid treating a title's size/marketing text as a street address.
        if not re.search(r'\b(?:sale|rent|land|house|apartment|aana|ana|price)\b',candidate,re.I):
            return candidate,False
    # Prefer a named locality rather than a whole-district pin.
    for locality,district in LOCALITIES.items():
        if re.search(r'\b'+locality+r'\b',text,re.I): return locality.title()+', '+district,True
    district=re.search(r'\b(Kathmandu|Lalitpur|Bhaktapur)\b',text,re.I)
    if district: return district[1].title(),True
    raise OutOfScope('No public Kathmandu Valley address found; masked addresses are not recovered')

def posted_date(raw,scraped_at):
    value=clean(raw).lower().removeprefix('posted').strip()
    match=re.fullmatch(r'(\d+)\s+(minute|hour|day|week)s?\s+ago',value)
    if not match:return None
    seconds=int(match[1])*{'minute':60,'hour':3600,'day':86400,'week':604800}[match[2]]
    return (scraped_at-timedelta(seconds=seconds)).astimezone(timezone(timedelta(hours=5,minutes=45))).date().isoformat()

def parse(html,url,scraped_at=None):
    soup=BeautifulSoup(html,'html.parser'); obj=product_schema(soup)
    title=clean(obj.get('name')); description=visible_description(soup)
    category=clean(obj.get('category')).lower()
    # Category labels are explicit; exclude rooms, business and wanted ads.
    if 'for sale' in category: transaction='sale'
    elif 'for rent' in category: transaction='rent'
    else: raise OutOfScope('Not a sale or rental listing')
    kind='land' if 'land' in category else 'house' if 'house' in category else 'apartment' if 'apartment' in category else None
    if not kind: raise OutOfScope('Unsupported real-estate category')
    address,inferred=extract_address(title,description)
    specs=specifications(soup)
    sizes=SIZE_RE.findall(title+'\n'+description)
    size=next((clean(s) for s in sizes if parse_size(s)), '')
    if not size:
        four=re.search(r'(?<!\d)\d+\s*-\s*\d+\s*-\s*\d+\s*-\s*\d+(?!\d)',title+'\n'+description)
        size=clean(four[0]) if four else ''
    raw_size=specs.get('Land Size (Aana/Dhur)') or specs.get('House Size (Sq. Ft.)')
    if not size and raw_size:
        # "Aana/Dhur" does not establish a unit. Retain it without conversion.
        size=raw_size if parse_size(raw_size) else raw_size+' (Aana/Dhur unspecified)'
    offers=obj.get('offers',{})
    if offers.get('priceCurrency')!='NPR': raise ValueError('Unsupported listing currency')
    raw_price=str(offers.get('price',''))
    unit=re.search(r'(?:per|/)\s*(aana|anna|ana|ropani|sq\.?\s*ft|sqft)\b',description,re.I)
    if unit:raw_price+=' per '+unit[1]
    elif transaction=='rent' and re.search(r'per\s+month|/\s*month|monthly',description,re.I):raw_price+=' per month'
    posted=next((clean(n.get_text(' ',strip=True)) for n in soup.select('[data-testid="product-meta-chip"]') if clean(n.get_text()).startswith('Posted')), '')
    road=next((clean(line) for line in description.splitlines() if re.search(r'\b(?:road|बाटो)\b',line,re.I) and len(line)<220),'')
    raw=dict(source='hamrobazar',source_url=url,title=title,address=address,area_name=address.split(',')[0],property_type=kind,transaction_type=transaction,price_raw=raw_price,size=size,listing_date_raw=posted,road_access_note=road)
    item=normalize(raw); flags=item['quality_flags']
    if inferred:flags.append('Area/district inferred from public title or description; not a parcel address')
    if raw_size:flags.append('Source size field: '+raw_size+'; explicit units in description take precedence')
    estimate=posted_date(posted,scraped_at or datetime.now(timezone.utc))
    if estimate:
        item['listing_date']=estimate
        flags[:]=[f for f in flags if f!='Listing date unavailable or unparsed']
        flags.append('Listing date approximated from relative Posted label in Nepal time')
    # A bare land amount often represents an unstated unit price. Never assume total.
    if kind=='land' and not unit and not re.search(r'\b(?:total price|total amount|lump sum|all for)\b',description,re.I):
        item['price_basis']='unknown';item['total_price_npr']=None
        flags.append('Land price basis unspecified; raw asking amount retained')
    if transaction=='rent' and item['price_basis']=='total':
        item['price_basis']='unknown';item['total_price_npr']=None;flags.append('Rental period unspecified')
    # Do not retain full descriptions or seller identities/contact details.
    return item
