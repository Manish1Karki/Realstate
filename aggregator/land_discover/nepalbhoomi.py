"""Nepal Bhoomi's public detail markup; reviewed public HTML."""
import re
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from .normalize import clean, normalize, DISTRICTS
from .hamrobazar import OutOfScope, posted_date


def parse(html, url):
    soup = BeautifulSoup(html, 'html.parser')
    header = soup.select_one('.property_detail_title')
    if not header or not header.select_one('.property_detail_heading'):
        raise ValueError('Nepal Bhoomi detail header missing; revalidation required')
    title = clean(header.select_one('.property_detail_heading').get_text(' ', strip=True))
    location = header.select_one('.property_detail_location')
    address = clean(location.get_text(' ', strip=True)) if location else ''
    districts = [d for d in DISTRICTS if re.search(r'\b'+d+r'\b', address, re.I)]
    if not districts: raise OutOfScope('Missing public Valley address')
    if len(districts) > 1: raise ValueError('Conflicting advertised districts; address needs review')
    if re.search(r'\b(?:commercial|business|office)\b', title, re.I):
        raise OutOfScope('Unsupported commercial or studio listing')
    kind = re.search(r'\b(house|banglow|bungalow|bunglow|land|apartment|flat)\b', title, re.I)
    if not kind: raise OutOfScope('Unknown property type')
    kind = kind[1].lower()
    kind = 'house' if kind in ('banglow','bungalow','bunglow') else 'apartment' if kind == 'flat' else kind
    transaction = 'rent' if re.search(r'\brent\b', title, re.I) else 'sale' if re.search(r'\b(?:sale|sail|sell)\b', title, re.I) else 'unknown'
    price_node = soup.select_one('.detail_price')
    price = clean(price_node.get_text(' ', strip=True)) if price_node else ''
    if transaction == 'rent' and not re.search(r'per|/', price, re.I): price += ' per month'
    heading = next((h for h in soup.select('h2') if clean(h.get_text()).lower() == 'overview'), None)
    overview = heading.find_parent(class_='accordion-item') if heading else None
    if not overview: raise ValueError('Nepal Bhoomi Overview missing; revalidation required')
    labels = {}
    for li in overview.select('li'):
        text = clean(li.get_text(' ', strip=True))
        if ':' in text:
            key, value = text.split(':',1); labels[key.lower().strip()] = value.strip()
    item = normalize(dict(source='nepalbhoomi', source_url=url, title=title, address=address,
                          property_type=kind, transaction_type=transaction, price_raw=price,
                          size=labels.get('area covered',''), listing_date_raw=labels.get('posted',''),
                          road_access_note=labels.get('road access','')))
    if not item['listing_date']:
        estimate = posted_date(labels.get('posted', ''), datetime.now(timezone.utc))
        if estimate and not re.fullmatch(r'(?:[6-9]|\d{2,})\s+months?\s+ago', labels.get('posted','').strip(), re.I):
            item['listing_date'] = estimate
            item['quality_flags'].remove('Listing date unavailable or unparsed')
            item['quality_flags'].append('Listing date approximated from relative Posted label in Nepal time')
    images=[]
    for image in soup.select('.gallery_showcase img.thumb[src]'):
        target=urljoin(url,image['src'])
        if urlparse(target).scheme=='https' and urlparse(target).hostname=='nepalbhoomi.com' and '/storage/' in urlparse(target).path and target not in images:
            images.append(target)
    # Only explicit room totals near the property header; do not add up floor rows.
    text = ' '.join(clean(node.get_text(' ', strip=True)) for node in soup.select('.property_detail_title'))
    def room(word):
        match=re.search(r'\b(\d+)\s+'+word+r's?\b',text,re.I)
        return int(match[1]) if match else None
    description_heading=next((h for h in soup.select('#propertyAccordion h2') if clean(h.get_text()).lower()=='description'),None)
    description_block=description_heading.find_parent(class_='accordion-item').select_one('.accordion-body') if description_heading else None
    description=clean(description_block.get_text(' ',strip=True)) if description_block else ''
    description=re.split(r'\b(?:owner\s+contact|contact\s+(?:number|person)|phone|mobile)\b',description,flags=re.I)[0].strip()
    item.update(description=description[:5000] or None, image_url=images[0] if images else None, image_urls=images[:30],
                bedrooms=room('bedroom'), bathrooms=room('bathroom'))
    item['quality_flags'].append('Source-published listing: location and availability need verification')
    return item
