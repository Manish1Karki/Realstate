import type { ReactNode } from 'react'
import type { Property } from '@/lib/api'

function distance(km?: number | null) {
  if (km == null || !Number.isFinite(km)) return 'Distance unavailable'
  return km < 1 ? `${Math.round(km * 1000)} m` : `${km.toFixed(2)} km`
}

function Icon({ kind }: { kind: string }) {
  const paths: Record<string, ReactNode> = {
    house: <><path d="m3 10 9-7 9 7v11H3V10Z" /><path d="M9 21v-8h6v8" /></>,
    land: <path d="m4 5 7-2 9 3-2 15-8-3-8 3L4 5ZM11 3l-1 15M4 12l15 2" />,
    bed: <path d="M2 20V9h20v11M2 16h20M5 9V4h14v5M12 4v5" />,
    bath: <path d="M3 11h18v4a6 6 0 0 1-6 6H9a6 6 0 0 1-6-6v-4ZM6 11V5a3 3 0 0 1 6 0M7 21v1m10-1v1M10 5h4" />,
    school: <path d="m2 9 10-5 10 5-10 5-10-5ZM6 11v6l6 3 6-3v-6M22 9v7" />,
    hospital: <><rect x="3" y="3" width="18" height="18" rx="1" /><path d="M12 7v10M7 12h10" /></>,
    road: <path d="m7 3-4 18M17 3l4 18M12 3v3m0 4v4m0 4v3" />,
    bank: <path d="m2 7 10-5 10 5H2ZM3 21h18M5 10v8m7-8v8m7-8v8" />,
    atm: <><rect x="2" y="4" width="20" height="16" rx="1" /><path d="m5 15 2-6 2 6m-3-2h2m2-4h4m-2 0v6m4 0V9l2 3 2-3v6" /></>,
    market: <><path d="M2 3h2l3 13h12l3-10H5" /><circle cx="8" cy="21" r="1" /><circle cx="18" cy="21" r="1" /></>,
    phone: <path d="m7 3 3 5-3 2a15 15 0 0 0 7 7l2-3 5 3-1 4C10 22 2 14 3 4l4-1Z" />,
    info: <><circle cx="12" cy="12" r="9" /><path d="M12 11v6M12 7h.01" /></>,
    arrow: <path d="m9 5 7 7-7 7" />,
    pin: <><path d="M20 10c0 5-8 11-8 11S4 15 4 10a8 8 0 1 1 16 0Z" /><circle cx="12" cy="10" r="2.5" /></>,
  }
  const alias = ['college', 'university', 'kindergarten'].includes(kind) ? 'school'
    : ['clinic', 'pharmacy'].includes(kind) ? 'hospital' : kind === 'department_store' ? 'market' : kind
  return <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{paths[alias] || paths.pin}</svg>
}

export default function PropertyInformation({ property }: { property: Property }) {
  const kind = property.property_type.charAt(0).toUpperCase() + property.property_type.slice(1)
  const place = [property.area_name, property.district].filter(Boolean).join(', ')
  const facts = [
    { label: 'Property type', value: kind, icon: 'house' },
    { label: ['land', 'house'].includes(property.property_type) ? 'Land area' : 'Floor area', value: property.size || 'Not provided', icon: 'land' },
    ...(property.bedrooms != null ? [{ label: 'Bedrooms', value: String(property.bedrooms), icon: 'bed' }] : []),
    ...(property.bathrooms != null ? [{ label: 'Bathrooms', value: String(property.bathrooms), icon: 'bath' }] : []),
  ]
  const roadType = property.road_type ? property.road_type.charAt(0).toUpperCase() + property.road_type.slice(1) : ''
  const roadAccess = [property.road_width_ft ? `${property.road_width_ft} ft` : '', property.road_access_note].filter(Boolean).join('; ')
  const facilities = (property.amenities || []).filter(item => item.kind !== 'road').sort((a, b) => a.distance_km - b.distance_km)
  const radius = property.enrichment_radius_m ? property.enrichment_radius_m / 1000 : null
  const listingDate = property.listing_date ? new Date(property.listing_date + 'T00:00:00+05:45').toLocaleDateString('en-GB', { dateStyle: 'medium', timeZone: 'Asia/Kathmandu' }) : ''
  const phone = (property.contact_phone || '').replace(/[^+0-9]/g, '')
  const hasPhone = phone.replace(/\D/g, '').length >= 7
  const contactLabel = property.contact_role === 'owner' ? 'Property owner' : property.contact_role === 'agent' ? 'Listing agent' : 'Advertiser'

  function facilityRow(item: NonNullable<Property['amenities']>[number]) {
    return <li key={item.id}><span className="information-facility-icon"><Icon kind={item.kind} /></span><div><strong>{item.name}</strong><span>{item.kind === 'atm' ? 'ATM' : item.kind.replaceAll('_', ' ')}</span></div><span className="information-distance">{distance(item.distance_km)}</span></li>
  }

  return <section className="property-information" aria-labelledby="information-heading">
    <p className="information-breadcrumb">Property details <span aria-hidden="true">/</span> {property.area_name || property.district}</p>
    <header className="information-heading"><div><h2 id="information-heading">About this property</h2><p className="information-place"><Icon kind="pin" />{place || property.address}</p></div><span className="information-purpose">{property.transaction_type === 'rent' ? 'For rent' : 'For sale'}</span></header>
    <dl className="information-facts">{facts.map(fact => <div key={fact.label}><Icon kind={fact.icon} /><div><dt>{fact.label}</dt><dd>{fact.value}</dd></div></div>)}</dl>
    <div className="information-columns">
      <div className="information-main">
        {(roadAccess || roadType || property.road_under_construction != null) && <section className="information-access" aria-labelledby="insights-heading"><h3 id="insights-heading">Access &amp; surroundings</h3><div className="information-insights">
          {roadAccess && <article><Icon kind="road" /><div><h4>Road access</h4><p>{roadAccess}</p><span>As reported in the listing</span></div></article>}
          {(roadType || property.road_under_construction != null) && <article><Icon kind="road" /><div><h4>Road surface</h4>{roadType && <p>{roadType}</p>}{property.road_under_construction != null && <span>{property.road_under_construction ? 'Access road under construction' : 'Access road not under construction'}</span>}</div></article>}
        </div></section>}
        <section className="information-facility-section" aria-labelledby="facilities-heading"><h3 id="facilities-heading">Nearby facilities</h3>
          {facilities.length ? <><p className="information-facility-count">{facilities.length} mapped places{radius ? ` within ${radius} km` : ''}</p><ul className="information-facilities">{facilities.slice(0, 5).map(facilityRow)}</ul>
          {facilities.length > 5 && <details className="information-more"><summary><span>View all {facilities.length} facilities</span><Icon kind="arrow" /></summary><ul className="information-facilities">{facilities.slice(5).map(facilityRow)}</ul></details>}
          <p className="information-note">Straight-line distances. Mapped coverage may be incomplete.</p></> : <p className="information-empty">Nearby facility information is not available for this listing yet.</p>}
        </section>
      </div>
      <aside className="information-aside" aria-label="Property contact"><div className="information-contact"><h3>Contact advertiser</h3><span className="information-contact-role">{contactLabel}</span>
        {property.contact_name && <p className="information-contact-name">{property.contact_name}</p>}
        {hasPhone ? <><a className="information-phone" href={'tel:' + phone}>{property.contact_phone}</a><a className="information-call" href={'tel:' + phone}><Icon kind="phone" />Call advertiser</a><p className="information-contact-note">Ask about availability or arrange a viewing.</p></> : <p className="information-no-phone">Contact number is not available yet.</p>}
        {listingDate && <footer id="property-source-details" className="information-source"><span>Listed {listingDate}</span></footer>}
      </div><p className="information-verification"><Icon kind="info" />Confirm property details with the advertiser.</p></aside>
    </div>
  </section>
}
