import PropertyPhoto from '../../property-photo'
import type { Metadata } from 'next'
import Link from 'next/link'
import { notFound } from 'next/navigation'
import { canonicalSiteUrl, formatPrice, getProperty } from '@/lib/api'
import SaveProperty from '../../save-property'
import DetailTabs from './detail-tabs'
import PropertyBack from './property-back'

export const revalidate = 300
type Props = { params: Promise<{ id: string }>; searchParams: Promise<{ returnTo?: string | string[] }> }

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { id } = await params
  const property = await getProperty(id).catch(() => null)
  if (!property) return { title: 'Property not found', robots: { index: false, follow: false } }
  const place = [property.area_name, property.district].filter(Boolean).join(', ')
  const description = `${property.property_type} ${property.transaction_type === 'rent' ? 'for rent' : 'for sale'} in ${place}. ${formatPrice(property)}${property.size ? ` · ${property.size}` : ''}. View listing details and the original source.`
  const image = property.image_url || property.image_urls?.[0]
  return {
    title: `${property.title} in ${place}`,
    description: description.slice(0, 160),
    alternates: { canonical: canonicalSiteUrl(`/properties/${property.id}`) },
    openGraph: { type: 'article', title: `${property.title} in ${place}`, description, ...(image ? { images: [{ url: image, alt: property.title }] } : {}) },
  }
}

export default async function PropertyPage({ params, searchParams }: Props) {
  const { id } = await params
  const property = await getProperty(id).catch(() => null)
  if (!property) notFound()
  const search = await searchParams
  const returnTo = Array.isArray(search.returnTo) ? search.returnTo[0] : search.returnTo
  const photos = [...new Set([property.image_url, ...(property.image_urls || [])].filter((url): url is string => Boolean(url)))]
  const place = [property.area_name, property.district].filter(Boolean).join(', ')
  const hasMapPoint = Number.isFinite(property.lat) && Number.isFinite(property.lng)
    && property.lat! >= 27.5 && property.lat! <= 27.9 && property.lng! >= 85.15 && property.lng! <= 85.6
  const mapLink = hasMapPoint
    ? `https://www.openstreetmap.org/?mlat=${property.lat}&mlon=${property.lng}#map=16/${property.lat}/${property.lng}`
    : ''
  const mapFrame = hasMapPoint
    ? `https://www.openstreetmap.org/export/embed.html?bbox=${(property.lng! - 0.012).toFixed(5)}%2C${(property.lat! - 0.008).toFixed(5)}%2C${(property.lng! + 0.012).toFixed(5)}%2C${(property.lat! + 0.008).toFixed(5)}&layer=mapnik&marker=${property.lat}%2C${property.lng}`
    : ''
  const hasTourPoint = hasMapPoint && String(property.geocode_precision || '').startsWith('source map pin')
  const tourUrl = '/visual-tour/index.html?' + new URLSearchParams({ embed: '1', listing: String(property.id) }).toString()
  const jsonLd = { '@context': 'https://schema.org', '@type': 'WebPage', name: `${property.title} | Land Discover`, description: `${property.property_type} listing in ${place}`, url: canonicalSiteUrl(`/properties/${property.id}`), breadcrumb: { '@type': 'BreadcrumbList', itemListElement: [{ '@type': 'ListItem', position: 1, name: 'Home', item: canonicalSiteUrl('/') }, { '@type': 'ListItem', position: 2, name: 'Properties', item: canonicalSiteUrl('/properties') }, { '@type': 'ListItem', position: 3, name: property.title, item: canonicalSiteUrl(`/properties/${property.id}`) }] } }
  const kind = property.property_type.charAt(0).toUpperCase() + property.property_type.slice(1)
  const purpose = property.transaction_type === 'rent' ? 'For rent' : 'For sale'
  const amount = property.total_price_npr ?? property.price_npr
  const price = formatPrice(property).replace(/^NPR\s*/, '')
  const phone = String(property.contact_phone || '').replace(/[^+0-9]/g, '')
  const enquiryUrl = phone.length >= 7 ? 'tel:' + phone : property.source_url.startsWith('https://') ? property.source_url : null
  const summary = property.description?.replace(/^Views:.*?Table of Contents Toggle\s*/i, '').trim()
  const descriptionStart = summary?.startsWith(property.title) ? summary.slice(property.title.length).trim() : summary
  const displaySummary = descriptionStart?.replace(/^Property Highlights[\s\S]*?(?=\b(?:A|An|This)\s)/, '').trim()
  const listingDate = property.listing_date ? new Date(property.listing_date + 'T00:00:00+05:45').toLocaleDateString('en-NP', { dateStyle: 'medium', timeZone: 'Asia/Kathmandu' }) : ''
  return <main id="main" className="wrap detail-page refined-detail">
    <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd).replace(/</g, '\\\\u003c') }} />
    <PropertyBack returnTo={returnTo} />
    <header className="property-detail-heading"><p className="eyebrow">{kind.toUpperCase()} {purpose.toUpperCase()}</p><h1>{property.title}</h1><div className="property-heading-bottom"><p><DetailIcon kind="pin" />{place}</p><SaveProperty id={property.id} title={property.title} detailed /></div></header>
    <section className="property-visuals" aria-label="Property photo and location or contact details">
      <div className="property-photo-preview"><PropertyPhoto urls={photos} alt={property.title} eager /><span className="property-photo-label">Property exterior</span></div>
      <div className="property-map-preview">{hasMapPoint ? <><div className="property-map-viewport"><iframe title={(hasTourPoint ? 'Visual tour of ' : 'Map showing the published location of ') + property.title} src={hasTourPoint ? tourUrl : mapFrame} loading="eager" referrerPolicy="strict-origin-when-cross-origin" />{!hasTourPoint && <div className="property-map-address" title={property.address || place}>{property.address || place}</div>}</div><div className="property-map-preview-footer"><span>{hasTourPoint ? 'Visual tour' : 'Map preview'}</span><a href={hasTourPoint ? tourUrl : mapLink} target="_blank" rel="noopener noreferrer">{hasTourPoint ? 'Expand visual tour' : 'Open interactive map'} &#8599;</a></div></> : <div className="property-contact-preview"><span className="property-contact-icon"><DetailIcon kind="message" /></span><p className="eyebrow">CONTACT US</p><h2>Contact us for more details</h2><p>Ask about the exact location, property details, and arranging a visit.</p>{enquiryUrl ? <a className="button primary" href={enquiryUrl} {...(phone.length >= 7 ? {} : {target:'_blank',rel:'noopener noreferrer'})}><DetailIcon kind="message" />Contact us</a> : <a className="button primary" href="#property-enquiry">View contact details</a>}</div>}</div>
    </section>
    {photos.length > 1 && <div className="property-extra-photos" aria-label="Additional property photos">{photos.slice(1,5).map((photo,index) => <a key={photo} href={photo} target="_blank" rel="noopener noreferrer"><PropertyPhoto urls={[photo]} alt={property.title + ', photo ' + (index+2)} /></a>)}</div>}
    <div className="property-detail-content">
      <DetailTabs overview={<>
        <h2>About this property</h2>
        <p className="property-overview-copy">{displaySummary ? displaySummary.slice(0,360) + (displaySummary.length>360 ? '...' : '') : kind + ' ' + purpose.toLowerCase() + ' in ' + place + '. Contact the advertiser for available specifications and a viewing.'}</p>
        {summary && summary.length>360 && <details className="property-full-description"><summary>Read full description</summary><p>{summary}</p></details>}
        <dl className="property-summary-facts"><Fact label="Property type" value={kind} /><Fact label="Listing purpose" value={purpose} /><Fact label="Location" value={place} />{property.size && <Fact label="Size" value={property.size} />}{property.bedrooms != null && <Fact label="Bedrooms" value={String(property.bedrooms)} />}{property.bathrooms != null && <Fact label="Bathrooms" value={String(property.bathrooms)} />}</dl>
        {listingDate && <p className="property-posted"><DetailIcon kind="clock" />Listed {listingDate}</p>}
      </>} location={<><h2>Property location</h2><p className="property-overview-copy">{property.address || place}</p>{hasMapPoint ? <a className="text-link" href={mapLink} target="_blank" rel="noopener noreferrer">Explore this location on the map &#8599;</a> : <p className="muted">Map coordinates are not available for this property.</p>}<p className="property-location-note">The map pin comes from the source listing. Confirm the exact property boundary during a visit.</p>{property.road_access_note && <dl className="property-summary-facts"><Fact label="Road access" value={property.road_access_note} /></dl>}{(property.nearest_school || property.nearest_hospital || property.nearest_road) && <ul className="amenity-list">{property.nearest_school && <li><span>{property.nearest_school}</span><span>{distance(property.school_distance_km)}</span></li>}{property.nearest_hospital && <li><span>{property.nearest_hospital}</span><span>{distance(property.hospital_distance_km)}</span></li>}{property.nearest_road && <li><span>{property.nearest_road}</span><span>{distance(property.road_distance_km)}</span></li>}</ul>}</>} />
      <aside id="property-enquiry" className="property-enquiry-aside"><div className="property-enquiry-card"><p className="property-price-label">{property.transaction_type === 'rent' ? property.price_basis === 'monthly' ? 'Asking rent per month' : 'Asking rent' : amount === property.price_npr && !property.total_price_npr && property.price_basis?.startsWith('per_') ? 'Asking price ' + property.price_basis.replace('_', ' ') : 'Asking price'}</p><p className="property-asking-price">{amount != null && <small>NPR</small>}<span>{price}</span></p>{amount != null && <p className="property-numeric-price">NPR {amount.toLocaleString('en-NP')}{property.price_basis === 'monthly' ? ' / month' : ''}</p>}<div className="property-enquiry-section"><h2>Interested in this property?</h2><p>Contact the advertiser for more details or to arrange a viewing.</p>{enquiryUrl ? <a className="button primary" href={enquiryUrl} {...(phone.length >= 7 ? {} : {target:'_blank',rel:'noopener noreferrer'})}><DetailIcon kind="message" />Enquire about this property</a> : <p>Advertiser contact details are unavailable.</p>}<small>Confirm availability and price with the advertiser.</small></div></div><p className="property-viewing-note"><DetailIcon kind="info" /><span>Before making a decision, visit the property and verify its details and documents.</span></p></aside>
    </div>
    <footer className="property-detail-footer"><span>Land Discover</span><span>Property, made straightforward.</span></footer>
  </main>
}

function Fact({ label, value }: { label: string; value: string }) { return <div><dt>{label}</dt><dd>{value}</dd></div> }
function distance(value?: number | null) { return value == null ? 'Unavailable' : value.toFixed(1) + ' km' }
function DetailIcon({ kind }: { kind: 'pin' | 'clock' | 'message' | 'info' }) {
  return <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{kind === 'pin' ? <><path d="M20 10c0 5-8 11-8 11S4 15 4 10a8 8 0 1 1 16 0Z" /><circle cx="12" cy="10" r="2.5" /></> : kind === 'clock' ? <><circle cx="12" cy="12" r="9" /><path d="M12 6v6h5" /></> : kind === 'message' ? <path d="M3 4h18v14H8l-5 3V4Z" /> : <><circle cx="12" cy="12" r="9" /><path d="M12 11v6M12 7h.01" /></>}</svg>
}
