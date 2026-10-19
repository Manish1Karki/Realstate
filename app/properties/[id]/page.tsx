import PropertyInformation from './property-information'
import { listingSchema } from '@/lib/structured-data'
import PropertyLocation from './property-location'
import { propertyTitle, propertyDescription, propertySummary, readableTitle, sourceNames, jsonLdText } from '@/lib/property-content'
import { categoryForProperty, categoryPath } from '@/lib/property-categories'
import PropertyCard from '../property-card'
import CategoryPage, { categoryMetadata } from '../category-page'
import { categoryFor, pageNumber } from '@/lib/property-categories'
import PropertyGallery from './property-gallery'
import type { Metadata } from 'next'
import Link from 'next/link'
import { notFound, permanentRedirect } from 'next/navigation'
import { canonicalSiteUrl, getProperty } from '@/lib/api'
import SaveProperty from '../../save-property'
import DetailTabs from './detail-tabs'
import PropertyBack from './property-back'
import PropertyAssistant from './property-assistant'

export const revalidate = 300
type Props = { params: Promise<{ id: string }>; searchParams: Promise<{ returnTo?: string | string[]; page?: string }> }

export async function generateMetadata({ params, searchParams }: Props): Promise<Metadata> {
  const { id } = await params
  const category = categoryFor(id)
  if (category) {
    const search = await searchParams
    const page = pageNumber(search.page)
    return categoryMetadata(category, undefined, page)
  }
  const property = await getProperty(id)
  if (!property) return { title: 'Property not found', robots: { index: false, follow: false } }
  const place = [property.area_name, property.district].filter(Boolean).join(', ')
  const description = propertySummary(property)

  const image = property.image_url || property.image_urls?.[0]
  return {
    title: propertyTitle(property),
    description: description.slice(0, 160),
    twitter: { card: 'summary_large_image', title: propertyTitle(property), description: description.slice(0,160), ...(image ? { images: [image] } : {}) },
    alternates: { canonical: canonicalSiteUrl(`/properties/${property.id}`) },
    openGraph: { type: 'article', url: canonicalSiteUrl('/properties/' + property.id), title: propertyTitle(property), description, ...(image ? { images: [{ url: image, alt: property.title }] } : {}) },
  }
}

export default async function PropertyPage({ params, searchParams }: Props) {
  const { id } = await params
  const category = categoryFor(id)
  if (category) {
    const search = await searchParams
    const page = pageNumber(search.page)
    return <CategoryPage category={category} page={page} />
  }
  const property = await getProperty(id)
  if (!property) notFound()
  if (String(property.id) !== id) permanentRedirect('/properties/' + property.id)
  const search = await searchParams
  const returnTo = Array.isArray(search.returnTo) ? search.returnTo[0] : search.returnTo
  const photos = [...new Set([property.image_url, ...(property.image_urls || [])].filter((url): url is string => Boolean(url)))]
  const place = [property.area_name, property.district].filter(Boolean).join(', ')
  const hasMapPoint = Number.isFinite(property.lat) && Number.isFinite(property.lng)
    && property.lat! >= 27.5 && property.lat! <= 27.9 && property.lng! >= 85.15 && property.lng! <= 85.6
  const hasTourPoint = hasMapPoint && String(property.geocode_precision || '').startsWith('source map pin')
  const tourUrl = '/visual-tour/index.html?' + new URLSearchParams({ embed: '1', listing: String(property.id) }).toString()
  const jsonLd = listingSchema(property)
  const kind = property.property_type.charAt(0).toUpperCase() + property.property_type.slice(1)
  const purpose = property.transaction_type === 'rent' ? 'For rent' : 'For sale'
  const whatsappPhone = '9779803529868'
  const whatsappUrl = whatsappPhone ? 'https://wa.me/' + whatsappPhone + '?text=' + encodeURIComponent('Hi, I am interested in ' + readableTitle(property.title) + '. ' + canonicalSiteUrl('/properties/' + property.id)) : ''
  const matchingCategory = categoryForProperty(property)
  const related = property.related_properties || []
  const title = readableTitle(property.title)
  return <main id="main" className="wrap detail-page refined-detail">
    <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLdText(jsonLd) }} />
    <PropertyBack returnTo={returnTo} />
    <header className="property-detail-heading"><p className="eyebrow">{kind.toUpperCase()} {purpose.toUpperCase()}</p><h1>{title}</h1><div className="property-heading-bottom"><p><DetailIcon kind="pin" />{place}</p><SaveProperty id={property.id} title={property.title} detailed /></div></header>
    <div className="property-detail-content">
      <DetailTabs overview={<>
        <section className="property-visuals information-visuals" aria-label="Property photos and map">
          <PropertyGallery photos={photos} title={property.title} />
          <div className="property-map-preview"><PropertyLocation title={property.title} tourUrl={tourUrl} canTour={hasTourPoint} whatsappUrl={whatsappUrl} /></div>
        </section>
        <PropertyAssistant propertyId={property.id} title={title} />
        <PropertyInformation property={property} />
      </>} location={<><h2>Property location</h2><p className="property-overview-copy">{property.address || place}</p>{hasTourPoint ? <p className="muted">Explore the property map beside the photos in the Information tab.</p> : <p className="muted">A source-published map location is not available for this property.</p>}<p className="property-location-note">{hasTourPoint ? 'The map pin was published with the source listing. Confirm the exact property boundary during a visit.' : 'This map may show an approximate location. Confirm the exact address and property boundary with the advertiser.'}</p>{property.road_access_note && <dl className="property-summary-facts"><Fact label="Road access" value={property.road_access_note} /></dl>}{(property.nearest_school || property.nearest_hospital || property.nearest_road) && <ul className="amenity-list">{property.nearest_school && <li><span>{property.nearest_school}</span><span>{distance(property.school_distance_km)}</span></li>}{property.nearest_hospital && <li><span>{property.nearest_hospital}</span><span>{distance(property.hospital_distance_km)}</span></li>}{property.nearest_road && <li><span>{property.nearest_road}</span><span>{distance(property.road_distance_km)}</span></li>}</ul>}</>} />
    </div>
    {matchingCategory && <section className="browse-category-links"><h2>Explore similar properties</h2><Link href={categoryPath(matchingCategory)}>{matchingCategory.label} in Kathmandu Valley</Link></section>}
    {related.length > 0 && <section><h2>More properties in {property.district}</h2><div className="property-grid">{related.map(item => <PropertyCard key={item.id} property={item} returnTo={'/properties?' + new URLSearchParams({ transaction: item.transaction_type || 'sale', property_type: item.property_type, district: item.district }).toString()} />)}</div></section>}
    <footer className="property-detail-footer"><span>Land Discover</span><span>Property, made straightforward.</span></footer>
  </main>
}

function Fact({ label, value }: { label: string; value: string }) { return <div><dt>{label}</dt><dd>{value}</dd></div> }
function distance(value?: number | null) { return value == null ? 'Unavailable' : value.toFixed(1) + ' km' }
function DetailIcon({ kind }: { kind: 'pin' | 'clock' | 'message' | 'info' }) {
  return <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{kind === 'pin' ? <><path d="M20 10c0 5-8 11-8 11S4 15 4 10a8 8 0 1 1 16 0Z" /><circle cx="12" cy="10" r="2.5" /></> : kind === 'clock' ? <><circle cx="12" cy="12" r="9" /><path d="M12 6v6h5" /></> : kind === 'message' ? <path d="M3 4h18v14H8l-5 3V4Z" /> : <><circle cx="12" cy="12" r="9" /><path d="M12 11v6M12 7h.01" /></>}</svg>
}
