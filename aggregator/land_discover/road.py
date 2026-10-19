"""Source-reported access roads; nearby mapped roads never establish access."""
import re
from .normalize import clean


def extract(item, labels):
    labels = {clean(k).lower().rstrip(':'): clean(v) for k, v in labels.items()}
    notes = [item.get('road_access_note') or '']
    for key in ('road access', 'road description', 'road type', 'road surface', 'road size (ft)', 'road width', 'road width (ft)', 'road status', 'road construction'):
        if labels.get(key):
            value = labels[key]
            if key in ('road size (ft)', 'road width (ft)'): value += ' ft'
            notes.append(value)
    # Only road clauses from the property's description, never page navigation or related listings.
    for clause in re.split(r'[.!?;\n]+(?=\s|$)', item.get('description') or ''):
        if re.search(r'\b(?:road|blacktop|blacktopped|pitched)\b|बाटो|सडक', clause, re.I):
            if not re.search(r'\b(?:nearby|away|distance|from|proposed|planned|will be|to be)\b', clause, re.I):
                notes.append(clean(clause))
    note = '; '.join(dict.fromkeys(value for value in notes if value))[:1500] or None
    text = (note or '').lower()
    # Future/negative descriptions cannot be used as evidence of the current surface.
    surface_text = re.sub(r'[^;]*(?:\bnot\b|\bnon[- ]|\bwill\b|\bplanned\b|\bproposed\b|\bto be\b)[^;]*', '', text)
    surfaces = {
        'asphalt': r'\b(?:asphalt|black\s*top(?:ped)?|pitch(?:ed)?)\b|कालोपत्रे',
        'concrete': r'\b(?:concrete|cemented)\b|ढलान',
        'gravel': r'\b(?:gravel(?:led)?|graveled)\b|ग्राभेल',
        'earth': r'\b(?:earthen|earth|dirt|unpaved|unpitched)\b|कच्ची',
        'pavers': r'\b(?:pavers?|cobblestone)\b',
    }
    found = [kind for kind, pattern in surfaces.items() if re.search(pattern, surface_text)]
    surface = found[0] if len(found) == 1 else None
    paved = True if surface in ('asphalt', 'concrete', 'pavers') else False if surface in ('gravel', 'earth') else None
    if surface is None and not found and re.search(r'\bpaved\b', surface_text): paved = True
    if re.search(r'\b(?:not pitched|not paved|not blacktopped|non[- ]pitched)\b', text):
        paved = False if surface is None else None
    widths = re.findall(r'(?<![\d.])(\d+(?:\.\d+)?)\s*(?:ft\b|feet\b|foot\b|फिट)', text)
    ranged = re.search(r'\d\s*(?:-|–|to)\s*\d', text)
    width = float(widths[0]) if len(set(widths)) == 1 and not ranged else None
    construction = None
    status = labels.get('road status') or labels.get('road construction') or ''
    construction_text = re.sub(r'\b(?:house|building|apartment|hospital|school)\s+(?:is\s+)?(?:not\s+)?under construction\b', '', text)
    if re.search(r'\b(?:under construction|being (?:built|constructed)|construction ongoing)\b|निर्माणाधीन', construction_text):
        construction = True
    if re.search(r'\b(?:not under construction|construction completed|construction complete)\b', construction_text) or status.lower() in ('completed', 'complete', 'no'):
        construction = False
    item.update(road_access_note=note, road_type=surface, road_width_ft=width,
                road_is_pitched=paved, road_under_construction=construction)
    return item
