"""Public property facts from validated Nepal HTML pages."""
import json
import re
from bs4 import BeautifulSoup
from .normalize import clean, normalize, parse_size
from .hamrobazar import OutOfScope, SIZE_RE, extract_address


def schema_objects(soup):
    from .scraper import ld_items
    for script in soup.select('script[type="application/ld+json"]'):
        try: yield from ld_items(json.loads(script.get_text(), strict=False))
        except (ValueError, TypeError): continue


def parse(html, url, source):
    soup = BeautifulSoup(html, 'html.parser')
    heading = soup.find('h1')
    if not heading: raise ValueError('Property title missing; review source markup')
    title = clean(heading.get_text(' ', strip=True))
    objects = list(schema_objects(soup))
    listing = next((obj for obj in objects if obj.get('@type') == 'RealEstateListing'), {})
    business = next((obj for obj in objects if obj.get('@type') == 'LocalBusiness' and obj.get('name') == title), {})
    data = listing or business
    address = data.get('address', {})
    if isinstance(address, dict):
        address = ', '.join(dict.fromkeys(str(address[k]) for k in ('streetAddress','addressLocality','addressRegion') if address.get(k)))
    description = clean(BeautifulSoup(str(data.get('description') or ''), 'html.parser').get_text(' ', strip=True))
    node = soup.select_one('.geodir-field-post_content, .rh_content, .property-description')
    detail_text = clean(node.get_text(' ', strip=True)) if node else description
    date_raw = data.get('datePosted') or data.get('datePublished') or ''
    images = data.get('image') or []
    if source == 'gharjagganepal':
        page = next((o for o in objects if o.get('@type') == 'WebPage' and o.get('url', '').rstrip('/') == url.rstrip('/')), {})
        date_raw = page.get('datePublished', '')
        node = soup.select_one('.geodir-field-address')
        address = clean(node.get_text(' ', strip=True)).strip(' ,') if node else address
        kind_text = title + ' ' + clean(soup.get_text(' ', strip=True)).split('Description')[0]
        node = soup.select_one('.geodir-field-price')
        price = clean(node.get_text(' ', strip=True)) if node else ''
        transaction_text = kind_text
    elif source == 'nepalhomesearch':
        if not listing: raise ValueError('RealEstateListing schema missing')
        node = soup.select_one('.rh_page__property_address')
        address = clean(node.get_text(' ', strip=True)) if node else address
        node = soup.select_one('.rh_page__property_price')
        price = clean(node.get_text(' ', strip=True)) if node else ''
        transaction_text = title + ' ' + price
        price = re.sub(r'For (?:Sale|Rent)', '', price, flags=re.I).strip()
        if not date_raw:
            node = soup.select_one('meta[property="article:published_time"]')
            date_raw = node.get('content', '') if node else ''
        kind_text = title
    else:
        if not listing: raise ValueError('RealEstateListing schema missing')
        offers = listing.get('offers', {})
        if offers.get('price') not in (None, '') and offers.get('priceCurrency') != 'NPR': raise ValueError('Unsupported currency')
        price = str(offers.get('price') or '')
        kind_text = title
        transaction_text = title + ' ' + str(offers.get('businessFunction', ''))
    kind = re.search(r'\b(house|bungalow|land|plot|apartment|flat)\b', kind_text, re.I)
    if not kind: raise OutOfScope('Unsupported property category')
    kind = kind[1].lower()
    kind = 'house' if kind == 'bungalow' else 'land' if kind == 'plot' else 'apartment' if kind == 'flat' else kind
    transaction = 'rent' if re.search(r'\brent\b|#Lease', transaction_text, re.I) else 'sale' if re.search(r'\bsale\b|\bsell\b|#Sell', transaction_text, re.I) else 'unknown'
    if transaction == 'unknown': raise OutOfScope('No explicit sale or rent information')
    if not address or not re.search(r'Kathmandu|Lalitpur|Bhaktapur', address, re.I):
        address, _ = extract_address(title, str(address) + ' ' + detail_text)
    size = ''
    if source == 'nepalhomesearch':
        node = soup.select_one('.prop_lot_size, .prop_size')
        size = re.sub(r'^(?:Lot Size|Area|Built Up)', '', clean(node.get_text(' ', strip=True)), flags=re.I).strip() if node else ''
    if not size:
        size = next((clean(value) for value in SIZE_RE.findall(detail_text) if parse_size(value)), '')
    if transaction == 'rent' and not re.search(r'per|/', price, re.I): price += ' per month'
    item = normalize(dict(source=source, source_url=url, title=title, address=address,
                          property_type=kind, transaction_type=transaction, size=size,
                          price_raw=price, listing_date_raw=date_raw))
    description = re.split(r'Owner Contact|Email:|Contact:|Phone:|Mobile:', detail_text, flags=re.I)[0].strip()
    description = re.sub(r'\b[\w.+-]+@[\w.-]+\.\w+\b', '', description)
    photos = []
    if not isinstance(images, list): images = [images]
    for image in images:
        target = (image.get('url') or image.get('contentUrl')) if isinstance(image, dict) else image
        if isinstance(target, str) and target.startswith('https://') and not re.search(r'/static/|og-image|logo|placeholder', target, re.I) and target not in photos: photos.append(target)
    if not photos:
        node = soup.select_one('meta[property="og:image"]')
        if node and str(node.get('content', '')).startswith('https://') and not re.search(r'/static/|og-image|logo|placeholder', node['content'], re.I): photos.append(node['content'])
    item.update(description=description[:1500] or None, image_urls=photos[:20],
                image_url=photos[0] if photos else None, bedrooms=None, bathrooms=None)
    if source == 'nepalhomesearch':
        for field, selector in [('bedrooms','.prop_bedrooms'),('bathrooms','.prop_bathrooms')]:
            node=soup.select_one(selector)
            match=re.search(r'\b(\d+)\b',node.get_text(' ',strip=True)) if node else None
            if match and 0<=int(match[1])<=100: item[field]=int(match[1])
        road=soup.select_one('.rh_property__meta.road')
        if road: item['road_access_note']=re.sub(r'^Road\s*','',clean(road.get_text(' ',strip=True)))
    for field, key in [('bedrooms','numberOfBedrooms'),('bathrooms','numberOfBathroomsTotal')]:
        value = data.get(key)
        if isinstance(value, (int,float)) and 0 < value <= 100 and int(value) == value: item[field] = int(value)
    return item
