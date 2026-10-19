import { cache } from 'react'

export type Property = {
  id: number
  contact_name?: string | null
  contact_phone?: string | null
  contact_role?: string | null
  source: string
  source_url: string
  title: string
  description?: string | null
  address: string
  area_name: string
  district: string
  ward?: string | null
  lat?: number | null
  lng?: number | null
  nearest_school?: string | null
  school_distance_km?: number | null
  nearest_hospital?: string | null
  hospital_distance_km?: number | null
  nearest_road?: string | null
  road_distance_km?: number | null
  road_access_note?: string | null
  road_type?: string | null
  road_width_ft?: number | null
  road_is_pitched?: boolean | null
  road_under_construction?: boolean | null
  enrichment_radius_m?: number | null
  enrichment_status?: string | null
  geocode_status?: string | null
  geocode_precision?: string | null
  geocode_label?: string | null
  price_npr?: number | null
  total_price_npr?: number | null
  price_basis?: string | null
  price_raw?: string | null
  property_type: string
  transaction_type?: string | null
  size?: string | null
  size_sqft?: number | null
  bedrooms?: number | null
  bathrooms?: number | null
  image_url?: string | null
  image_urls?: string[]
  listing_date?: string | null
  scraped_date?: string | null
  content_updated_at?: string | null
  quality_flags?: string[]
  related_properties?: Property[]
  amenities?: { id: number; name: string; kind: string; distance_km: number }[]
}

export type SitemapProperty = { id: number; content_updated_at: string | null; property_type: string; transaction_type: string; district: string }

export type PropertyPage = { total: number; items: Property[]; page: number; page_size: number }

function apiOrigin() {
  return (process.env.LAND_API_URL || process.env.BACKEND_API_URL || 'http://127.0.0.1:8000').replace(/\/$/, '')
}

function serverHeaders(): HeadersInit {
  const headers: Record<string, string> = { accept: 'application/json' }
  const proxySecret = process.env.BACKEND_PROXY_SECRET
  if (proxySecret) headers['X-Land-Proxy-Token'] = proxySecret
  return headers
}

export async function getProperties(params: URLSearchParams): Promise<PropertyPage> {
  const query = new URLSearchParams(params)
  query.set('page_size', query.get('page_size') || '12')
  const response = await fetch(`${apiOrigin()}/api/properties?${query}`, {
    ...(query.get('q') || query.has('saved_ids') ? { cache: 'no-store' as const } : { next: { revalidate: 60, tags: ['properties'] } }),
    headers: serverHeaders(),
    signal: AbortSignal.timeout(20000),
  })
  if (!response.ok) throw new Error(`Property API returned ${response.status}`)
  return response.json()
}

export const getProperty = cache(async (id: string | number): Promise<Property | null> => {
  if (!/^\d+$/.test(String(id))) return null
  const response = await fetch(`${apiOrigin()}/api/properties/${id}`, {
    next: { revalidate: 60, tags: ['properties'] },
    headers: serverHeaders(),
    signal: AbortSignal.timeout(20000),
  })
  if (response.status === 404) return null
  if (!response.ok) throw new Error(`Property API returned ${response.status}`)
  return response.json()
})

export async function getSitemapProperties(): Promise<SitemapProperty[]> {
  const response = await fetch(`${apiOrigin()}/api/sitemap`, {
    next: { revalidate: 300, tags: ['properties'] },
    signal: AbortSignal.timeout(20000),
    headers: serverHeaders(),
  })
  if (!response.ok) throw new Error(`Property API returned ${response.status}`)
  const body = await response.json()
  return body.items
}

export function formatPrice(property: Property) {
  const amount = property.total_price_npr ?? property.price_npr
  if (amount == null) return property.price_raw || 'Price on request'
  const value = amount >= 10_000_000 ? 'NPR ' + (amount / 10_000_000).toLocaleString('en', { maximumFractionDigits: 2 }) + ' crore'
    : amount >= 100_000 ? 'NPR ' + (amount / 100_000).toLocaleString('en', { maximumFractionDigits: 2 }) + ' lakh' : 'NPR ' + amount.toLocaleString('en')
  const basis = !property.total_price_npr ? property.price_basis : ''
  return value + (basis === 'monthly' ? ' / month' : basis?.startsWith('per_') ? ' ' + basis.replaceAll('_', ' ') : '')
}

export function canonicalSiteUrl(path = '/') {
  const base = (process.env.NEXT_PUBLIC_SITE_URL || 'https://land-discover-prototype.vercel.app').replace(/\/$/, '')
  return `${base}${path.startsWith('/') ? path : `/${path}`}`
}
