export const sourceNames = { huku: 'HUKU Real Estate', hamrobazar: 'Hamrobazar', nepalbhoomi: 'Nepal Bhoomi', nepalhomesearch: 'Nepal Home Search', gharjagganepal: 'Ghar Jagga Nepal', tradenepal: 'Trade Nepal', community: 'Property advertiser' }

export function clean(value, length = 180) {
  return typeof value === 'string' ? value.replace(/<[^>]*>/g, ' ').replace(/[\w.+-]+@[\w.-]+\.[a-z]{2,}/gi, '[email removed]').replace(/\+?\d[\d ()-]{7,}\d/g, '[number removed]').replace(/\s+/g, ' ').trim().slice(0, length) : null
}
const number = value => typeof value === 'number' && Number.isFinite(value) && value >= 0 ? value : null
const boolean = value => typeof value === 'boolean' ? value : null
export const distance = km => km == null ? 'distance not available' : km < 1 ? `${Math.round(km * 1000)} m` : `${km.toFixed(2)} km`

export function advertisedPrice(p) {
  const amount = number(p.total_price_npr) ?? number(p.price_npr)
  if (amount == null) return clean(p.price_raw) || 'Not provided'
  const basis = p.total_price_npr != null ? 'total' : p.price_basis
  const suffix = basis === 'monthly' ? ' per month' : basis?.startsWith('per_') ? ` ${basis.replaceAll('_', ' ')}` : ''
  return `NPR ${amount.toLocaleString('en-US')}${suffix}`
}

// Explicit fields only: no names, phone numbers, addresses, coordinates, descriptions,
// photos, session cookies or full source records are sent to the model.
export function propertyFacts(p) {
  return {
    property_id: p.id, property_type: clean(p.property_type, 30), purpose: clean(p.transaction_type, 30),
    area: clean(p.area_name), district: clean(p.district), size: clean(p.size, 80),
    bedrooms: number(p.bedrooms), bathrooms: number(p.bathrooms),
    advertised_price: advertisedPrice(p), purchase_price_npr: number(p.total_price_npr),
    price_basis: clean(p.price_basis, 40),
    road_access: clean(p.road_access_note, 300), road_width_ft: number(p.road_width_ft),
    road_surface: clean(p.road_type, 40), road_is_pitched: boolean(p.road_is_pitched),
    access_road_under_construction: boolean(p.road_under_construction),
    facilities_radius_m: number(p.enrichment_radius_m), facilities_status: clean(p.enrichment_status, 40),
    nearby_places: (Array.isArray(p.amenities) ? p.amenities : []).filter(a => a.kind !== 'road' && number(a.distance_km) != null)
      .slice(0, 70).map(a => ({ name: clean(a.name), kind: clean(a.kind, 40), distance_km: number(a.distance_km) })),
    map_precision: clean(p.geocode_precision, 100), listing_date: clean(p.listing_date, 30),
    source: sourceNames[p.source] || 'Property advertiser',
  }
}

export function propertyView(p) {
  return { id: p.id, title: clean(p.title, 220) || 'Property details', type: p.property_type,
    location: [clean(p.area_name), clean(p.district)].filter(Boolean).join(', '),
    price: advertisedPrice(p), size: clean(p.size, 80) || 'Not provided', source: sourceNames[p.source] || 'Property advertiser',
    page_url: `http://localhost:3000/properties/${p.id}`, facts: propertyFacts(p) }
}

export function missingFacts(f) {
  return [f.advertised_price === 'Not provided' && 'Price', !f.size && 'Size',
    !f.road_access && f.road_width_ft == null && 'Road access', !f.road_surface && 'Road surface',
    f.access_road_under_construction == null && 'Access road construction status',
    !f.nearby_places.length && 'Nearby places', !f.map_precision?.startsWith('source map pin') && 'Source-published map pin'].filter(Boolean)
}
