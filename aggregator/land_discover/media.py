"""Extract public property media and descriptive fields from HTML/schema."""
import json
import re
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from .normalize import clean

def enrich(item, html, url):
    soup = BeautifulSoup(html, 'html.parser')
    from .scraper import fields, ld_items
    labels = fields(soup)
    images = []
    description = ''
    bedrooms = bathrooms = None
    def add(value):
        if isinstance(value, list):
            for entry in value: add(entry)
        elif isinstance(value, dict): add(value.get('contentUrl') or value.get('url'))
        elif isinstance(value, str):
            target = urljoin(url, value.strip())
            if urlparse(target).scheme == 'https' and urlparse(target).hostname and target not in images:
                images.append(target)
    def count(value):
        if isinstance(value, dict): value = value.get('value')
        try:
            number = float(value)
            return int(number) if number.is_integer() and 0 <= number <= 100 else None
        except (TypeError, ValueError): return None
    for script in soup.select('script[type="application/ld+json"]'):
        try: objects = ld_items(json.loads(script.get_text()))
        except (ValueError, TypeError): continue
        for obj in objects:
            types = obj.get('@type', [])
            types = [types] if isinstance(types, str) else types
            if not set(types) & {'Product','RealEstateListing','House','Apartment','Residence','SingleFamilyResidence'}: continue
            add(obj.get('image'))
            description = description or clean(BeautifulSoup(str(obj.get('description') or ''), 'html.parser').get_text(' ', strip=True))
            bedrooms = bedrooms if bedrooms is not None else count(obj.get('numberOfBedrooms'))
            bathrooms = bathrooms if bathrooms is not None else count(obj.get('numberOfBathroomsTotal'))
    for meta in soup.select('meta[property="og:image"], meta[name="twitter:image"]'): add(meta.get('content'))
    for node in soup.select('[itemprop="image"], .property-gallery img, .listing-gallery img, [class*="gallery"] img, .property-slider img'):
        add(node.get('content') or node.get('data-src') or node.get('src'))
    if not description:
        node = soup.select_one('[itemprop="description"], .property-description, .listing-description, meta[name="description"]')
        if node: description = clean(node.get('content') or node.get_text(' ', strip=True))
    if item['source'] == 'hamrobazar':
        from .hamrobazar import visible_description, specifications
        description = visible_description(soup) or description
        labels.update({k.lower(): v for k, v in specifications(soup).items()})
    bedrooms = bedrooms if bedrooms is not None else count(labels.get('bedrooms') or labels.get('bedroom'))
    bathrooms = bathrooms if bathrooms is not None else count(labels.get('bathrooms') or labels.get('bathroom'))
    item.update(image_url=images[0] if images else None, image_urls=images[:30], description=description[:5000] or None, bedrooms=bedrooms, bathrooms=bathrooms)
    return item
