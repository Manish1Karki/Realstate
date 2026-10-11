"""Extract coordinates explicitly published with a property listing page."""
import json
import math
import re
from urllib.parse import parse_qs, unquote, urlparse

VALLEY_BOUNDS = (85.15, 27.50, 85.60, 27.90)
PROPERTY_TYPES = {
    'product', 'realestatelisting', 'house', 'apartment', 'residence',
    'singlefamilyresidence',
}


def _point(latitude, longitude):
    try:
        lat, lng = float(latitude), float(longitude)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(lat) or not math.isfinite(lng):
        return None
    if not VALLEY_BOUNDS[0] <= lng <= VALLEY_BOUNDS[2] or not VALLEY_BOUNDS[1] <= lat <= VALLEY_BOUNDS[3]:
        return None
    return lat, lng


def _geo(value):
    if isinstance(value, dict):
        lat = value.get('latitude', value.get('lat'))
        lng = value.get('longitude', value.get('lon', value.get('lng')))
        return _point(lat, lng) if lat is not None and lng is not None else None
    if isinstance(value, str):
        match = re.fullmatch(r'\s*(-?\d+(?:\.\d+)?)\s*[,;]\s*(-?\d+(?:\.\d+)?)\s*', value)
        if match:
            return _point(match[1], match[2])
    return None


def _json_nodes(value):
    if isinstance(value, list):
        for item in value:
            yield from _json_nodes(item)
    elif isinstance(value, dict):
        yield value
        for key in ('@graph', 'mainEntity', 'itemOffered'):
            if isinstance(value.get(key), (dict, list)):
                yield from _json_nodes(value[key])


def _listing_geo(value):
    types = value.get('@type', [])
    if isinstance(types, str):
        types = [types]
    if not any(str(kind).rstrip('/').rsplit('/', 1)[-1].replace(' ', '').lower() in PROPERTY_TYPES for kind in types):
        return None
    offered = value.get('itemOffered')
    offered = offered if isinstance(offered, list) else [offered]
    candidates = [value.get('geo')]
    location = value.get('location')
    if isinstance(location, dict): candidates.append(location.get('geo'))
    candidates.extend(item.get('geo') for item in offered if isinstance(item, dict))
    for candidate in candidates:
        point = _geo(candidate)
        if point:
            return point
    return None


def _url_points(url):
    text = unquote(url)
    parsed = urlparse(text)
    query = parse_qs(parsed.query)
    points = []
    for key in ('q', 'query', 'll', 'center', 'marker', 'sll'):
        for value in query.get(key, []):
            point = _geo(value)
            if point:
                points.append(point)
    for lat_key, lng_key in (('lat', 'lng'), ('lat', 'lon'), ('mlat', 'mlon')):
        if query.get(lat_key) and query.get(lng_key):
            point = _point(query[lat_key][0], query[lng_key][0])
            if point:
                points.append(point)
    for pattern in (r'@(-?\d+\.\d+),(-?\d+\.\d+)', r'!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)'):
        for match in re.finditer(pattern, text):
            point = _point(match[1], match[2])
            if point:
                points.append(point)
    return points


def extract_public_coordinates(html):
    """Return one unambiguous source map point; ignore unrelated page coordinates."""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, 'html.parser')
    points = []
    for script in soup.select('script[type="application/ld+json"]'):
        try:
            document = json.loads(script.get_text())
        except (TypeError, ValueError):
            continue
        for node in _json_nodes(document):
            point = _listing_geo(node)
            if point:
                points.append(point)

    for meta in soup.select('meta[property="place:location:latitude"], meta[property="place:location:longitude"], meta[name="geo.position"]'):
        if meta.get('name') == 'geo.position':
            point = _geo(meta.get('content', ''))
            if point:
                points.append(point)
    meta = {node.get('property'): node.get('content') for node in soup.select('meta[property]')}
    point = _point(meta.get('place:location:latitude'), meta.get('place:location:longitude'))
    if point:
        points.append(point)

    for node in soup.select('[data-lat][data-lng], [data-latitude][data-longitude]'):
        ancestors = [node, *list(node.parents)[:6]]
        attrs = [' '.join((str(ancestor.get('id', '')), ' '.join(ancestor.get('class', [])),
                           str(ancestor.get('aria-label', '')))).lower() for ancestor in ancestors]
        if any(ancestor.name == 'footer' or 'footer' in text or 'contact' in text for ancestor, text in zip(ancestors, attrs)):
            continue
        context = ' '.join(attrs)
        if 'map' not in context and 'location' not in context:
            continue
        point = _point(node.get('data-lat', node.get('data-latitude')),
                       node.get('data-lng', node.get('data-longitude')))
        if point:
            points.append(point)

    for node in soup.select('iframe[src], a[href]'):
        url = node.get('src') or node.get('href') or ''
        parsed = urlparse(url)
        ancestors = [node, *list(node.parents)[:6]]
        context_parts = []
        excluded = False
        for ancestor in ancestors:
            attrs = ' '.join((str(ancestor.get('title', '')), str(ancestor.get('aria-label', '')),
                              str(ancestor.get('id', '')), ' '.join(ancestor.get('class', [])))).lower()
            context_parts.append(attrs)
            if ancestor.name == 'footer' or 'footer' in attrs or any(word in attrs for word in ('company-location', 'office-location', 'contact')):
                excluded = True
        heading = node.find_previous(lambda tag: tag.name in ('h1', 'h2', 'h3', 'h4'))
        if heading: context_parts.append(heading.get_text(' ', strip=True))
        context_parts.extend((str(node.get('title', '')), str(node.get('aria-label', '')), node.get_text(' ', strip=True)))
        context = ' '.join(context_parts).lower()
        map_url = parsed.hostname and ('map' in parsed.hostname or 'map' in parsed.path.lower())
        property_map_context = any(word in context for word in ('property', 'listing', 'detail', 'media-map', 'map-location'))
        if not excluded and map_url and (property_map_context or 'location' in context or 'map-wrapper' in context):
            points.extend(_url_points(url))

    distinct = list(dict.fromkeys(points))
    return distinct[0] if len(distinct) == 1 else None
