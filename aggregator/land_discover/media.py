"""Extract public property media and descriptive fields from HTML/schema."""
import json
import re
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from .normalize import clean

def collect_gallery(item, html, url):
    """Merge adapter photos with public detail-page galleries, preferring full-size links."""
    from .scraper import ld_items
    soup = BeautifulSoup(html, 'html.parser')
    for node in soup.select('nav, footer, aside, .related-properties, .related-listings, .similar-properties, [class*="related"], [class*="similar"]'):
        node.decompose()
    images = []
    def add(value):
        if isinstance(value, list):
            for entry in value: add(entry)
        elif isinstance(value, dict):
            add(value.get('contentUrl') or value.get('url'))
        elif isinstance(value, str) and value.strip():
            target = urljoin(url, value.strip())
            parsed = urlparse(target)
            target = parsed._replace(fragment='').geturl()
            if parsed.scheme == 'https' and parsed.hostname and not re.search(r'logo|placeholder|og-image|favicon|avatar|\.svg(?:\?|$)', target, re.I) and target not in images:
                images.append(target)
    for script in soup.select('script[type="application/ld+json"]'):
        try: objects = ld_items(json.loads(script.get_text(), strict=False))
        except (ValueError, TypeError): continue
        for obj in objects:
            types = obj.get('@type', [])
            types = [types] if isinstance(types, str) else types
            if set(types) & {'Product','RealEstateListing','House','Apartment','Residence','SingleFamilyResidence'} or ('LocalBusiness' in types and clean(obj.get('name')) == item.get('title')):
                add(obj.get('image'))
    selector = '[itemprop="image"], [class*="gallery"] img, [class*="gallery"] source, [class*="gallery"] a[href], .fotorama img, .fotorama a, [class*="carousel"] img, [class*="swiper"] img, .property-slider img, .property-images img, [data-fancybox][href], [data-lightbox][href]'
    for node in soup.select(selector):
        anchor = node if node.name == 'a' else node.find_parent('a')
        full = node.get('data-full') or node.get('data-large') or node.get('data-zoom-image')
        if anchor and (anchor.has_attr('data-fancybox') or anchor.has_attr('data-lightbox') or re.search(r'\.(?:jpe?g|png|webp|avif)(?:\?|$)', anchor.get('href',''), re.I)):
            full = anchor.get('href') or full
        srcset = node.get('data-srcset') or node.get('srcset')
        if not full and srcset:
            candidates = []
            for entry in srcset.split(','):
                parts = entry.strip().split()
                if parts:
                    try: weight = float(parts[1].rstrip('wx')) if len(parts) > 1 else 1
                    except ValueError: weight = 0
                    candidates.append((weight, parts[0]))
            if candidates: full = max(candidates, key=lambda entry: entry[0])[1]
        add(full or node.get('content') or node.get('data-src') or node.get('data-lazy-src') or node.get('data-original') or node.get('src'))
    # Keep source-specific photos that do not use generic gallery markup.
    add(item.get('image_urls') or [])
    add(item.get('image_url'))
    if not images:
        for meta in soup.select('meta[property="og:image"], meta[name="twitter:image"]'): add(meta.get('content'))
    item.update(image_urls=images[:30], image_url=images[0] if images else None)
    return item

def enrich(item, html, url):
    soup = BeautifulSoup(html, 'html.parser')
    for node in soup.select('nav, footer, aside, [class*="related"], [class*="similar"]'):
        node.decompose()
    from .scraper import fields, ld_items
    labels = fields(soup)
    description = ''
    bedrooms = bathrooms = None
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
            description = description or clean(BeautifulSoup(str(obj.get('description') or ''), 'html.parser').get_text(' ', strip=True))
            bedrooms = bedrooms if bedrooms is not None else count(obj.get('numberOfBedrooms'))
            bathrooms = bathrooms if bathrooms is not None else count(obj.get('numberOfBathroomsTotal'))
    if not description:
        node = soup.select_one('[itemprop="description"], .property-description, .listing-description, meta[name="description"]')
        if node: description = clean(node.get('content') or node.get_text(' ', strip=True))
    if item['source'] == 'hamrobazar':
        from .hamrobazar import visible_description, specifications
        description = visible_description(soup) or description
        labels.update({k.lower(): v for k, v in specifications(soup).items()})
    bedrooms = bedrooms if bedrooms is not None else count(labels.get('bedrooms') or labels.get('bedroom'))
    bathrooms = bathrooms if bathrooms is not None else count(labels.get('bathrooms') or labels.get('bathroom'))
    item.update(description=description[:5000] or None, bedrooms=bedrooms, bathrooms=bathrooms)
    return collect_gallery(item, html, url)
