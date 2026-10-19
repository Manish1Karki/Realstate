import PropertyCard from './property-card'
import SortChoice from './sort-choice'
import BrowseLinks from './browse-links'
import type { Metadata } from 'next'
import Link from 'next/link'
import { canonicalSiteUrl, formatPrice, getProperties, type Property } from '@/lib/api'
import BrowseOptions from './browse-options'
import RememberSearch from './remember-search'

type Search = Record<string, string | string[] | undefined>
export async function generateMetadata({ searchParams }: { searchParams: Promise<Search> }): Promise<Metadata> {
  const search = await searchParams
  const isFiltered = ['q', 'district', 'property_type', 'transaction', 'sort', 'page'].some(key => Boolean(first(search[key])))
  return {
    title: 'Properties for sale and rent in Kathmandu Valley',
    description: 'Browse property listings across Kathmandu, Lalitpur, and Bhaktapur. Compare homes, apartments, and land with clear listing details.',
    alternates: { canonical: canonicalSiteUrl('/properties') },
    robots: isFiltered ? { index: false, follow: true } : { index: true, follow: true },
  }
}

export default async function PropertiesPage({ searchParams }: { searchParams: Promise<Search> }) {
  const search = await searchParams
  const q = first(search.q).slice(0, 200)
  const districtValue = first(search.district), district = ['Kathmandu', 'Lalitpur', 'Bhaktapur'].includes(districtValue) ? districtValue : ''
  const typeValue = first(search.property_type), type = ['house', 'apartment', 'land'].includes(typeValue) ? typeValue : ''
  const transactionValue = first(search.transaction), transaction = ['sale', 'rent', 'unknown'].includes(transactionValue) ? transactionValue : ''
  const sortValue = first(search.sort), sort = ['newest', 'price_asc', 'price_desc'].includes(sortValue) ? sortValue : 'newest'
  const page = Math.min(100000, Math.max(1, Math.floor(Number(first(search.page)) || 1)))
  const editing = first(search.edit) === '1'
  if (editing || !['rent','sale'].includes(transaction) || !type) {
    return <BrowseOptions key={JSON.stringify([transaction, type, district, q])} initialTransaction={transaction} initialType={type} initialDistrict={district} initialQuery={q}><BrowseLinks /></BrowseOptions>
  }
  const currentPath = pageHref(page,q,district,type,transaction,sort)
  const params = new URLSearchParams({ page: String(page), page_size: '12', q, district, property_type: type, transaction, sort })
  let result
  try { result = await getProperties(params) } catch { result = { total: 0, items: [], page, page_size: 12, unavailable: true } }
  const pages = Math.max(1, Math.ceil(result.total / result.page_size))
  return <main id="main" className="wrap listing-page"><RememberSearch path={currentPath} />
    <nav className="breadcrumbs" aria-label="Breadcrumb"><Link href="/">Home</Link><span aria-hidden="true">/</span><span>Properties</span></nav>
    <header className="page-heading"><div><p className="eyebrow">KATHMANDU VALLEY MARKETPLACE</p><h1>Find your next <em>place.</em></h1><p className="listing-intro">Browse matching properties across Kathmandu Valley.</p></div><div className="page-heading-actions"><Link className="text-link" href={currentPath + '&edit=1'}>Change search choices</Link><Link className="button secondary" href="/properties/new">List a property</Link></div></header>
    <form className="filter-bar" action="/properties" method="get"><input type="hidden" name="sort" value={sort} />
      <label className="search-field"><span className="filter-label">Search properties</span><input name="q" type="search" placeholder="Search neighborhood or listing" defaultValue={q} /></label>
      <label><span className="filter-label">Property type</span><select name="property_type" defaultValue={type}><option value="house">House</option><option value="apartment">Apartment</option><option value="land">Land</option></select></label>
      <label><span className="filter-label">District</span><select name="district" defaultValue={district}><option value="">All districts</option><option value="Kathmandu">Kathmandu</option><option value="Lalitpur">Lalitpur</option><option value="Bhaktapur">Bhaktapur</option></select></label>
      <label><span className="filter-label">Listing type</span><select name="transaction" defaultValue={transaction}><option value="sale">For sale</option><option value="rent">For rent</option></select></label>
      <button className="button primary" type="submit">Search</button>
    </form>
    <section aria-labelledby="listing-heading"><div className="listing-toolbar"><div><h2 id="listing-heading">{type === 'land' ? 'Land' : type === 'apartment' ? 'Apartments' : 'Houses'} for {transaction === 'rent' ? 'rent' : 'sale'}</h2><p>{result.total.toLocaleString()} {result.total === 1 ? 'listing' : 'listings'}</p></div><form action="/properties" method="get"><input type="hidden" name="q" value={q} /><input type="hidden" name="district" value={district} /><input type="hidden" name="property_type" value={type} /><input type="hidden" name="transaction" value={transaction} /><label><span className="filter-label">Sort listings</span><SortChoice key={sort} sort={sort} /></label><button className="text-button" type="submit">Sort</button></form></div>
      {'unavailable' in result ? <div className="empty-state"><h2>Listings are temporarily unavailable</h2><p>Please try again in a moment.</p></div> : result.items.length ? <div className="property-grid">{result.items.map(property => <PropertyCard key={property.id} property={property} returnTo={currentPath} />)}</div> : <div className="empty-state"><h2>No recent listings found</h2><p>Listings posted within the past six months appear here, including properties without a map pin.</p><Link className="button secondary" href={`/properties?transaction=${transaction}&property_type=${type}`}>Clear search filters</Link></div>}
    </section>
    {pages > 1 && <nav className="pagination" aria-label="Property listing pages">{page > 1 && <Link href={pageHref(page - 1, q, district, type, transaction, sort)}>← Previous</Link>}<span>Page {page} of {pages}</span>{page < pages && <Link href={pageHref(page + 1, q, district, type, transaction, sort)}>Next →</Link>}</nav>}
    <p className="disclaimer">Listing information can change. Confirm price, availability, and property details with the original source before making decisions.</p>
  </main>
}

function first(value: string | string[] | undefined) { return Array.isArray(value) ? value[0] || '' : value || '' }
function pageHref(page: number, q: string, district: string, type: string, transaction: string, sort: string) { const p = new URLSearchParams({ page: String(page), q, district, property_type: type, transaction, sort }); return `/properties?${p}` }
