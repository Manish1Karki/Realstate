import AccountMenu from './AccountMenu'
import { useEffect, useRef, useState } from 'react'
import './PropertyDashboard.css'

const API = (import.meta.env.VITE_PROPERTY_API_URL || '').replace(/\/$/, '')
const money = property => {
  const n = property.total_price_npr ?? property.price_npr
  if (n == null) return 'Price on request'
  const value = n >= 1e7 ? `${(n / 1e7).toLocaleString('en', { maximumFractionDigits: 2 })} Cr` : n >= 1e5 ? `${(n / 1e5).toLocaleString('en', { maximumFractionDigits: 2 })} lakh` : n.toLocaleString('en')
  return `NPR ${value}`
}
async function request(path, options = {}) {
  const response = await fetch(`${API}/api${path}`, options)
  if (!response.ok) throw new Error(response.status === 404 ? 'This property could not be found.' : response.status === 422 ? 'Please check your property details and try again.' : 'The property service is unavailable. Please try again.')
  return response.json()
}
function Symbol({ kind = 'home', size = 20 }) {
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{kind === 'pin' ? <><path d="M20 10c0 5-8 11-8 11S4 15 4 10a8 8 0 1 1 16 0Z" /><circle cx="12" cy="10" r="2.5" /></> : kind === 'search' ? <><circle cx="10.5" cy="10.5" r="6.5" /><path d="m16 16 5 5" /></> : kind === 'heart' ? <path d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.7l-1.1-1.1a5.5 5.5 0 0 0-7.8 7.8L12 21l8.8-8.6a5.5 5.5 0 0 0 0-7.8Z" /> : kind === 'grid' ? <><rect x="3" y="3" width="7" height="7" rx="1" /><rect x="14" y="3" width="7" height="7" rx="1" /><rect x="3" y="14" width="7" height="7" rx="1" /><rect x="14" y="14" width="7" height="7" rx="1" /></> : <><path d="m3 10 9-7 9 7M5 9v12h14V9M9 21v-8h6v8" /></>}</svg>
}
function Photo({ property, large = false }) {
  const [failed, setFailed] = useState(false)
  return <div className={`market-photo ${large ? 'market-photo-large' : ''} ${property.property_type}`}>{property.image_url && !failed ? <img src={property.image_url} alt={property.title} onError={() => setFailed(true)} /> : <div className="market-no-photo"><Symbol size={large ? 60 : 42} /><span>Property photo not provided</span></div>}<span className="market-photo-badge">{property.transaction_type === 'rent' ? 'FOR RENT' : property.transaction_type === 'sale' ? 'FOR SALE' : 'PROPERTY'}</span></div>
}
function AddProperty({ onClose, onAdded }) {
  const dialog = useRef(null)
  const [pending, setPending] = useState(false)
  const [error, setError] = useState('')
  const [type, setType] = useState('house')
  useEffect(() => {
    const element = dialog.current
    element.showModal()
    return () => element.close()
  }, [])
  async function submit(event) {
    event.preventDefault()
    const data = Object.fromEntries(new FormData(event.currentTarget))
    data.total_price_npr = Number(data.total_price_npr)
    data.bedrooms = type === 'land' || data.bedrooms === '' ? null : Number(data.bedrooms)
    data.bathrooms = type === 'land' || data.bathrooms === '' ? null : Number(data.bathrooms)
    setPending(true)
    setError('')
    try {
      const property = await request('/properties', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) })
      onAdded(property)
    } catch (cause) {
      setError(cause instanceof TypeError ? 'Unable to connect to the property service. Please try again.' : cause.message)
    } finally { setPending(false) }
  }
  return <dialog ref={dialog} className="market-dialog" onCancel={event => { if (pending) event.preventDefault(); else onClose() }} onClick={event => { if (event.target === dialog.current && !pending) onClose() }}>
    <div className="market-dialog-heading"><div><p className="market-eyebrow">NEW LISTING</p><h2>Share your property</h2></div><button className="market-icon-button" aria-label="Close form" onClick={onClose} disabled={pending}>×</button></div>
    <p className="market-muted">A new home. A fresh start. Let someone discover yours.</p>
    <form onSubmit={submit} className="market-add-form"><fieldset disabled={pending}>
      <label className="full">Property name<input name="title" placeholder="e.g. Family home in Bhaisepati" minLength="3" maxLength="140" required /></label>
      <label>Property type<select name="property_type" value={type} onChange={event => setType(event.target.value)}><option value="house">House</option><option value="apartment">Apartment</option><option value="land">Land</option></select></label>
      <label>Listing type<select name="transaction_type"><option value="sale">For sale</option><option value="rent">For rent · monthly price</option></select></label>
      <label>Neighborhood<input name="area_name" placeholder="e.g. Bhaisepati" minLength="2" maxLength="100" required /></label>
      <label>District<select name="district"><option>Kathmandu</option><option>Lalitpur</option><option>Bhaktapur</option></select></label>
      <label className="full">Street / address<input name="address" placeholder="Street, ward, neighborhood" minLength="3" maxLength="250" required /></label>
      <label>Asking price (NPR)<input type="number" name="total_price_npr" placeholder="e.g. 25000000" min="1" max="1000000000000" step="any" required /></label>
      <label>Property size<input name="size" placeholder="e.g. 4 aana or 1200 sq ft" maxLength="80" required /></label>
      {type !== 'land' && <><label>Bedrooms<input name="bedrooms" type="number" min="0" max="100" placeholder="e.g. 3" /></label><label>Bathrooms<input name="bathrooms" type="number" min="0" max="100" placeholder="e.g. 2" /></label></>}
      <label className="full">About this property<textarea name="description" rows="3" placeholder="What makes this place special?" minLength="10" maxLength="5000" required /></label>
      <label className="full">Road access <span>(optional)</span><input name="road_access_note" placeholder="e.g. 16 ft road, east facing" maxLength="300" /></label>
      <label>Contact name<input name="contact_name" minLength="2" maxLength="100" autoComplete="name" required /></label>
      <label>Contact phone<input name="contact_phone" type="tel" minLength="7" maxLength="30" pattern="\+?[0-9 ()\-]+" autoComplete="tel" required /></label>
      <label className="full">Property photo URL <span>(optional)</span><input name="image_url" type="url" placeholder="https://…" pattern="https://.*" maxLength="2000" /></label>
    </fieldset><p className="market-form-note">Your listing and contact details will be publicly visible.</p>{error && <p className="market-error" role="alert">{error}</p>}<div className="market-form-actions"><button type="button" className="market-secondary" onClick={onClose} disabled={pending}>Cancel</button><button className="market-primary" disabled={pending}>{pending ? 'Publishing…' : 'Publish property'} <span aria-hidden="true">↗</span></button></div></form>
  </dialog>
}

function PropertyDetails({ id, saved, toggleSaved }) {
  const [result, setResult] = useState({ property: null, error: '' })
  useEffect(() => {
    const controller = new AbortController()
    request(`/properties/${id}`, { signal: controller.signal }).then(property => setResult({ property, error: '' })).catch(error => { if (error.name !== 'AbortError') setResult({ property: null, error: error instanceof TypeError ? 'Unable to load this property. Please check the property service.' : error.message }) })
    return () => controller.abort()
  }, [id])
  const { property, error } = result
  return <><div className="market-detail-toolbar"><a href="/properties">← Back to properties</a>{property && <button className={`market-secondary ${saved.includes(property.id) ? 'is-saved' : ''}`} onClick={() => toggleSaved(property.id)}><Symbol kind="heart" size={16} />{saved.includes(property.id) ? 'Saved' : 'Save property'}</button>}</div>{error ? <div className="market-empty" role="alert"><h2>Property unavailable</h2><p>{error}</p></div> : !property ? <div className="market-empty" role="status">Loading property…</div> : <div className="market-detail-grid">
    <section className="market-property-info" aria-label="Property information"><Photo property={property} large /><div className="market-info-copy"><div className="market-card-location"><Symbol kind="pin" size={14} />{property.area_name}, {property.district}</div><div className="market-detail-title"><h1>{property.title}</h1><div><strong>{money(property)}</strong><small>{property.transaction_type === 'rent' ? 'per month' : property.price_basis?.startsWith('per_') ? property.price_basis.replaceAll('_', ' ') : property.total_price_npr == null && property.price_npr != null ? 'Price basis not disclosed' : 'asking price'}</small></div></div>
    <dl className="market-detail-facts"><div><dt>Property type</dt><dd>{property.property_type}</dd></div><div><dt>Size</dt><dd>{property.size || 'Not provided'}</dd></div>{property.bedrooms != null && <div><dt>Bedrooms</dt><dd>{property.bedrooms}</dd></div>}{property.bathrooms != null && <div><dt>Bathrooms</dt><dd>{property.bathrooms}</dd></div>}</dl>
    <h2>About this property</h2><p className="market-description">{property.description || 'A full description is not available for this listing. Visit the original listing for further details.'}</p>
    <h2>Property information</h2><dl className="market-information"><div><dt>Address</dt><dd>{property.address}</dd></div><div><dt>Road access</dt><dd>{property.road_access_note || 'Not provided'}</dd></div><div><dt>Listed</dt><dd>{property.listing_date || property.listing_date_raw || 'Not provided'}</dd></div><div><dt>Source</dt><dd>{property.source === 'community' ? 'Owner-submitted listing' : property.source}</dd></div></dl>
    {property.is_demo === 1 && <p className="market-form-note">Sample property. This is a synthetic example.</p>}
    {property.contact_name && <div className="market-contact"><span className="market-contact-avatar">{property.contact_name.slice(0, 1).toUpperCase()}</span><div><strong>{property.contact_name}</strong><p>Listing contact</p></div><a className="market-primary" href={`tel:${property.contact_phone.replace(/[^+0-9]/g, '')}`}>Call owner ↗</a><span className="market-contact-phone">{property.contact_phone}</span></div>}
    {/^https:\/\//.test(property.source_url) && <a className="market-primary" href={property.source_url} target="_blank" rel="noreferrer">View original listing ↗</a>}
    <p className="market-detail-note">Listing details and availability should be confirmed with the owner or original source.</p></div></section>
    <section className="market-location-panel" aria-labelledby="property-map-heading">
      <div className="market-location-heading"><p className="market-eyebrow">PROPERTY LOCATION</p><h2 id="property-map-heading">Map</h2><p>{property.area_name}, {property.district}</p></div>
      <div className="market-map-placeholder"><div className="market-map-icon"><Symbol kind="pin" size={32} /></div><h3>Map coming soon</h3><p>The property location map will be available here.</p><span>MAP PLACEHOLDER</span></div>
    </section>
  </div>}</>
}

export default function PropertyDashboard() {
  const id = window.location.pathname.split('/')[2]
  const [items, setItems] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [status, setStatus] = useState('loading')
  const [error, setError] = useState('')
  const [reload, setReload] = useState(0)
  const [showAdd, setShowAdd] = useState(false)
  const [query, setQuery] = useState('')
  const [type, setType] = useState('')
  const [district, setDistrict] = useState('')
  const [transaction, setTransaction] = useState('')
  const [sort, setSort] = useState('newest')
  const [onlySaved, setOnlySaved] = useState(() => new URLSearchParams(window.location.search).get('saved') === '1')
  const [feedback, setFeedback] = useState('')
  const [saved, setSaved] = useState(() => { try { const value = JSON.parse(localStorage.getItem('land-discover-saved') || '[]'); return Array.isArray(value) ? value.filter(Number.isInteger) : [] } catch { return [] } })
  useEffect(() => {
    if (id) return
    const controller = new AbortController()
    const params = new URLSearchParams({ page, page_size: 12, sort, district, property_type: type, transaction, q: query })
    if (onlySaved) (saved.length ? saved : [0]).forEach(value => params.append('saved_ids', value))
    request(`/properties?${params}`, { signal: controller.signal }).then(data => { setItems(data.items); setTotal(data.total); setStatus('ready') }).catch(cause => { if (cause.name !== 'AbortError') { setError(cause instanceof TypeError ? 'Unable to connect to the property service. Start the backend and try again.' : cause.message); setStatus('error') } })
    return () => controller.abort()
  }, [id, page, sort, district, type, transaction, query, onlySaved, saved, reload])
  function filter(setter, value) { setter(value); setPage(1); setStatus('loading') }
  function toggleSaved(propertyId) {
    const next = saved.includes(propertyId) ? saved.filter(value => value !== propertyId) : [...saved, propertyId]
    setSaved(next)
    try { localStorage.setItem('land-discover-saved', JSON.stringify(next)) } catch { setFeedback('Saved for this visit. Browser storage is unavailable.') }
  }
  const visible = items.filter(property => (!onlySaved || saved.includes(property.id)) && `${property.title} ${property.area_name} ${property.address} ${property.district}`.toLowerCase().includes(query.trim().toLowerCase()))
  return <div className="market-shell">
    <header className="market-header"><a className="market-brand" href="/"><span><Symbol size={18} /></span><div>Land Discover<small>Find your place. Make it yours.</small></div></a><div className="market-header-actions"><AccountMenu signInClass="market-signin" /><button className="market-primary" onClick={() => setShowAdd(true)}>＋ <span>List a property</span></button></div></header>
    <div className="market-body"><nav className="market-sidebar" aria-label="Marketplace navigation"><a className={!id && !onlySaved ? 'active' : ''} href="/properties" aria-label="Browse properties" title="Browse properties"><Symbol /></a><button className={onlySaved ? 'active' : ''} aria-label="Show saved properties" title="Saved properties" onClick={() => { if (id) window.location.assign('/properties?saved=1'); else { setOnlySaved(value => !value); setPage(1); setStatus('loading') } }}><Symbol kind="heart" /></button><a href="/" aria-label="About Land Discover" title="About Land Discover"><Symbol kind="grid" /></a><span className="market-sidebar-bottom">LD</span></nav>
    <main className={`market-main ${id ? 'market-main-details' : ''}`}>
      {id ? <PropertyDetails id={id} saved={saved} toggleSaved={toggleSaved} /> : <>
        <section className="market-intro"><div><p className="market-eyebrow">PROPERTY MARKETPLACE</p><h1>A better way to find<br />your next <em>home.</em></h1></div><p>Discover a place that feels like you.<br />Explore properties across Kathmandu Valley.</p></section>
        <section className="market-search" aria-label="Filter properties"><label className="market-search-input"><Symbol kind="search" size={18} /><input aria-label="Search properties" placeholder="Search by neighborhood or property" value={query} onChange={event => filter(setQuery, event.target.value)} /></label><select aria-label="Property type" value={type} onChange={event => filter(setType, event.target.value)}><option value="">All types</option><option value="house">House</option><option value="apartment">Apartment</option><option value="land">Land</option></select><select aria-label="District" value={district} onChange={event => filter(setDistrict, event.target.value)}><option value="">All districts</option><option>Kathmandu</option><option>Lalitpur</option><option>Bhaktapur</option></select><select aria-label="Listing type" value={transaction} onChange={event => filter(setTransaction, event.target.value)}><option value="">Sale & rent</option><option value="sale">For sale</option><option value="rent">For rent</option></select></section>
        {feedback && <p className="market-success" role="status">{feedback}</p>}
        <section className="market-listings"><div className="market-listings-heading"><div><h2>{onlySaved ? 'Saved properties' : 'Available properties'}</h2><p>{total} {total === 1 ? 'listing' : 'listings'} · Find a place for your next chapter.</p></div><select aria-label="Sort properties" value={sort} onChange={event => filter(setSort, event.target.value)}><option value="newest">Newest first</option><option value="price_asc">Price: low to high</option><option value="price_desc">Price: high to low</option></select></div>
        {status === 'loading' ? <div className="market-empty" role="status">Finding your next place…</div> : status === 'error' ? <div className="market-empty"><h2>We couldn’t load the listings</h2><p role="alert">{error}</p><button className="market-primary" onClick={() => { setStatus('loading'); setReload(value => value + 1) }}>Try again</button></div> : !visible.length ? <div className="market-empty"><Symbol size={40} /><h2>{total ? 'No matching properties' : 'A new neighborhood starts with you.'}</h2><p>{total ? 'Try another search, change the filters, or browse another page.' : 'Be the first to share a property for others to discover.'}</p><button className="market-primary" onClick={() => setShowAdd(true)}>List a property ↗</button></div> : <div className="market-card-grid">{visible.map(property => <article className="market-listing-card" key={property.id}><a href={`/properties/${property.id}`} aria-label={`View ${property.title}`}><Photo property={property} /></a><button className={`market-save ${saved.includes(property.id) ? 'is-saved' : ''}`} aria-label={`${saved.includes(property.id) ? 'Unsave' : 'Save'} ${property.title}`} aria-pressed={saved.includes(property.id)} onClick={() => toggleSaved(property.id)}><Symbol kind="heart" size={16} /></button><a className="market-card-copy" href={`/properties/${property.id}`}><div className="market-card-location"><Symbol kind="pin" size={13} />{property.area_name}, {property.district}</div><h3>{property.title}</h3><div className="market-card-price"><strong>{money(property)}</strong><span>{property.transaction_type === 'rent' ? '/ month' : property.price_basis?.startsWith('per_') ? property.price_basis.replaceAll('_', ' ') : 'asking price'}</span></div><div className="market-card-facts"><span>{property.property_type}</span><span>{property.size || 'Size not provided'}</span>{property.bedrooms != null && <span>{property.bedrooms} beds</span>}</div></a></article>)}</div>}
        {total > 12 && <div className="market-pagination"><button className="market-secondary" disabled={page === 1 || status === 'loading'} onClick={() => { setPage(value => value - 1); setStatus('loading') }}>← Previous</button><span>Page {page} of {Math.ceil(total / 12)}</span><button className="market-secondary" disabled={page * 12 >= total || status === 'loading'} onClick={() => { setPage(value => value + 1); setStatus('loading') }}>Next →</button></div>}
        </section><div className="market-bottom-note"><span><Symbol size={16} /> A place to belong.</span><p>Explore freely. Find something that feels like home.</p></div>
      </>}
    </main></div>{showAdd && <AddProperty onClose={() => setShowAdd(false)} onAdded={property => { window.location.assign(`/properties/${property.id}`) }} />}
  </div>
}
