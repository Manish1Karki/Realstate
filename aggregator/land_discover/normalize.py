"""Conservative normalization: unknown prices/units/dates stay unknown."""
import re
from datetime import date

DIGITS = str.maketrans('०१२३४५६७८९','0123456789')
DISTRICTS = ('Kathmandu','Lalitpur','Bhaktapur')
AANA_SQFT = 342.25

def clean(value):
    return re.sub(r'\s+',' ',str(value or '').translate(DIGITS)).strip()

def parse_size(raw):
    value = clean(raw).lower().replace(',','')
    if 'unspecified' in value:return None
    value=value.replace('रोपनी','ropani').replace('आना','aana').replace('पैसा','paisa').replace('दाम','daam')
    value=re.sub(r'\bdam\b','daam',value)
    value=value.replace('sqrft','sqft')
    # Traditional ropani-aana-paisa-daam is accepted only as four components.
    match = re.search(r'(?<!\d)(\d+)\s*-\s*(\d+)\s*-\s*(\d+)\s*-\s*(\d+)(?!\d)',value)
    if match:
        r,a,p,d = map(int,match.groups())
        if a>=16 or p>=4 or d>=4: return None
        return round((r*16+a+p/4+d/16)*AANA_SQFT,4)
    units = {'ropani':16*AANA_SQFT,'aana':AANA_SQFT,'anna':AANA_SQFT,'ana':AANA_SQFT,'paisa':AANA_SQFT/4,'daam':AANA_SQFT/16,'sq ft':1,'sqft':1,'sq. ft':1,'square feet':1,'sq m':10.7639104167,'sqm':10.7639104167}
    pattern = r'(\d+(?:\.\d+)?)\s*('+'|'.join(re.escape(u) for u in sorted(units,key=len,reverse=True))+r')\b'
    parts = re.findall(pattern,value)
    if not parts: return None
    return round(sum(float(n)*units[u] for n,u in parts),4) or None

def parse_price(raw, size_sqft=None):
    value = clean(raw).lower().replace(',','')
    basis='total'
    if re.search(r'(?:per|/)\s*(?:aana|anna|ana)\b',value): basis='per_aana'
    elif re.search(r'(?:per|/)\s*ropani\b',value): basis='per_ropani'
    elif re.search(r'(?:per|/)\s*(?:sq\.?\s*ft|sqft|square feet)',value): basis='per_sqft'
    elif re.search(r'(?:per|/)\s*(?:month|mo)\b',value): basis='monthly'
    elif re.search(r'\bper\b|/',value): basis='unknown'
    if re.search(r'\b(call|contact|negotiable only|not disclosed|on request)\b',value) or not re.search(r'\d',value):
        return None,'unknown',None
    # Ranges and mixed crore/lakh expressions need explicit review, never first-number parsing.
    if re.search(r'\d\s*(?:-|–|to)\s*\d',value): return None,'unknown',None
    tokens=re.findall(r'(\d+(?:\.\d+)?)\s*(crores?|cr\b|lakhs?|lacs?|million|thousand|करोड|लाख)?',value)
    if len(tokens)!=1: return None,'unknown',None
    n,unit=tokens[0]
    multiplier = 10_000_000 if unit.startswith(('cr','करोड')) else 100_000 if unit.startswith(('la','लाख')) else 1_000_000 if unit=='million' else 1000 if unit=='thousand' else 1
    price=float(n)*multiplier
    if price<=0: return None,'unknown',None
    total=price if basis=='total' else None
    if size_sqft and basis in ('per_aana','per_ropani','per_sqft'):
        total=price*size_sqft/({'per_aana':AANA_SQFT,'per_ropani':16*AANA_SQFT,'per_sqft':1}[basis])
    return round(price,2),basis,round(total,2) if total is not None else None

def parse_date(raw):
    raw=clean(raw)
    # Do not guess relative timestamps or Bikram Sambat calendar dates.
    match=re.search(r'\b(20\d{2}-\d{2}-\d{2})\b',raw)
    if not match: return None
    try:
        d=date.fromisoformat(match[1])
        return d.isoformat() if d<=date.today() else None
    except ValueError: return None

def normalize(raw):
    title=clean(raw.get('title')); address=clean(raw.get('address'))
    district=next((d for d in DISTRICTS if d.lower() in address.lower()),None)
    if not title or not address or not district: raise ValueError('Missing title/address or outside Kathmandu Valley')
    kind=clean(raw.get('property_type')).lower()
    if kind not in ('land','house','apartment'): raise ValueError('Unsupported or unknown property type')
    size=clean(raw.get('size')); sqft=parse_size(size)
    price,basis,total=parse_price(raw.get('price_raw'),sqft)
    flags=[]
    if price is None: flags.append('Price needs review')
    if sqft is None: flags.append('Size unparsed')
    listed=parse_date(raw.get('listing_date_raw'))
    if not listed: flags.append('Listing date unavailable or unparsed')
    if basis not in ('total','monthly') and total is not None: flags.append('Total calculated from unit price and size')
    parts=[p.strip() for p in address.split(',') if p.strip()]
    area=clean(raw.get('area_name')) or parts[0]
    ward=re.search(r'\bward\s*[-:#]?\s*(\d{1,2})\b',address,re.I)
    return dict(source=raw['source'],source_url=raw['source_url'],title=title,address=address,area_name=area,district=district,ward=ward[1] if ward else None,price_npr=price,price_basis=basis,price_raw=clean(raw.get('price_raw')),total_price_npr=total,property_type=kind,transaction_type=raw.get('transaction_type','unknown'),size=size,size_sqft=sqft,listing_date=listed,listing_date_raw=clean(raw.get('listing_date_raw')),road_access_note=clean(raw.get('road_access_note')) or None,quality_flags=flags)
