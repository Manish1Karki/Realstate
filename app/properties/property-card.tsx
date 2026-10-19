import { readableTitle } from '@/lib/property-content'
import Link from 'next/link'
import { formatPrice, type Property } from '@/lib/api'
import PropertyPhoto from '../property-photo'
import SaveProperty from '../save-property'

export default function PropertyCard({ property, returnTo }: { property: Property; returnTo: string }) {
  return <article className="property-card"><Link className="card-image" href={'/properties/' + property.id + '?returnTo=' + encodeURIComponent(returnTo)} aria-label={`View ${property.title}`}>
      <PropertyPhoto urls={[property.image_url || '', ...(property.image_urls || [])].filter(Boolean)} alt={property.property_type + ' in ' + property.area_name + ', ' + property.district} />
      <span className="status-pill">{property.transaction_type === 'rent' ? 'FOR RENT' : property.transaction_type === 'sale' ? 'FOR SALE' : 'PROPERTY'}</span>
    </Link><div className="card-content"><div className="card-topline"><p className="card-location">{property.area_name}, {property.district}</p><SaveProperty id={property.id} title={property.title} /></div><h3><Link href={'/properties/' + property.id + '?returnTo=' + encodeURIComponent(returnTo)}>{readableTitle(property.title)}</Link></h3><p className="card-price">{formatPrice(property)}</p><div className="card-facts"><span>{property.property_type}</span><span>{property.size || 'Size not provided'}</span>{property.bedrooms != null && <span>{property.bedrooms} beds</span>}</div><p className="card-nearby">School {distance(property.school_distance_km)} · Hospital {distance(property.hospital_distance_km)} · Road {distance(property.road_distance_km)}</p></div></article>
}
function distance(value?: number | null) { return value == null ? 'Unavailable' : value.toFixed(1) + ' km' }
