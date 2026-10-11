"""Public HTML adapter, available only in the opt-in local source trial."""
import re
from datetime import datetime
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from .normalize import clean, normalize, DISTRICTS
from .hamrobazar import OutOfScope


def parse(html, url):
    soup = BeautifulSoup(html, 'html.parser')
    header = soup.select_one('.row--property-header')
    if not header or not header.select_one('h1 > span'):
        raise ValueError('eProperty Nepal detail header missing; revalidation required')
    title = clean(header.select_one('h1 > span').get_text(' ', strip=True))
    if re.search(r'\b(?:wanted|required|looking for)\b', title, re.I):
        raise OutOfScope('Property request, not an available listing')
    address_node = header.select_one('.property-location')
    address = clean(address_node.get_text(' ', strip=True)) if address_node else ''
    if not any(d.lower() in address.lower() for d in DISTRICTS):
        raise OutOfScope('Outside Kathmandu Valley')
    # Use the advertised title, not recommended listings elsewhere on the page.
    kind = re.search(r'\b(house|land|apartment|flat)\b', title, re.I)
    if not kind:
        raise OutOfScope('Unsupported property type')
    transaction = 'rent' if re.search(r'\bfor\s+rent\b', title, re.I) else 'sale' if re.search(r'\bfor\s+sale\b', title, re.I) else 'unknown'
    price_node = header.select_one('h1 strong')
    price = clean(price_node.get_text(' ', strip=True)) if price_node else ''
    price = re.sub(r'/\s*only\b', '', price, flags=re.I)
    if transaction == 'rent' and not re.search(r'per|/', price, re.I):
        price += ' per month'
    size = ''
    rooms = {'bedrooms': None, 'bathrooms': None}
    for li in soup.select('ul.property-info > li'):
        value = clean(li.get_text(' ', strip=True))
        if re.fullmatch(r'[\d.,]+\s+(?:aana|ropani|sq\.?\s*ft|sqft)', value, re.I):
            size = value
        for field, word in [('bedrooms', 'bedroom'), ('bathrooms', 'bathroom')]:
            match = re.fullmatch(r'(\d+)\s+' + word + 's?', value, re.I)
            if match: rooms[field] = int(match[1])
    description_node = soup.select_one('.property-description-text')
    description = clean(description_node.get_text(' ', strip=True)) if description_node else ''
    # Keep property prose while excluding owner contact details.
    description = re.split(r'\b(?:owner\s+contact|contact\s+(?:number|person)|phone|mobile)\b', description, flags=re.I)[0]
    description = re.sub(r'\b(?:\+977[-\s]*)?9[678]\d{8}\b', '[contact omitted]', description)
    description = re.sub(r'^Description\s*', '', description).strip()
    road = re.search(r'Road Access\s*:\s*([^.!]+(?:\([^)]*\))?)', description, re.I)
    date_node = next((li for li in soup.select('.property-additional-detail li') if clean(li.get_text()).lower().startswith('posted on:')), None)
    posted = clean(date_node.get_text()).split(':', 1)[1].strip() if date_node else ''
    try: posted = datetime.strptime(posted, '%d %B %Y').date().isoformat()
    except ValueError: pass
    item = normalize(dict(source='epropertynepal', source_url=url, title=title, address=address,
                          property_type='apartment' if kind[1].lower() == 'flat' else kind[1].lower(),
                          transaction_type=transaction, price_raw=price, size=size,
                          listing_date_raw=posted, road_access_note=road[1] if road else ''))
    images = list(dict.fromkeys(urljoin(url, img['src']) for img in soup.select('.fotorama img[src]') if img['src'].startswith('/system/photos/')))
    item.update(description=description[:5000] or None, image_url=images[0] if images else None, image_urls=images[:30], **rooms)
    return item
