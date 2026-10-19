import RememberSearch from './remember-search'
import { jsonLdText } from '@/lib/property-content'
import { cache } from 'react'
import type { Metadata } from 'next'
import Link from 'next/link'
import { notFound } from 'next/navigation'
import { canonicalSiteUrl, getProperties, getSitemapProperties } from '@/lib/api'
import { type Category, categoryPath, districts } from '@/lib/property-categories'
import PropertyCard from './property-card'
import BrowseLinks from './browse-links'

const categoryResult = cache((type: string, transaction: string, district: string, page: number) => getProperties(new URLSearchParams({ transaction, property_type: type, district, page_size: '12', page: String(page) })))

export async function categoryMetadata(category: Category, district?: string, page = 1): Promise<Metadata> {
  const result = await categoryResult(category.type, category.transaction, district || '', page)
  const title = category.label + ' in ' + (district || 'Kathmandu Valley')
  return { title, description: category.introduction.replaceAll('Kathmandu Valley', district || 'Kathmandu Valley'),
    alternates: { canonical: canonicalSiteUrl(categoryPath(category, district) + (page > 1 ? '?page=' + page : '')) },
    robots: { index: result.total >= (district ? 3 : 1), follow: true },
    openGraph: { images: [{ url: canonicalSiteUrl('/social-image'), width: 1200, height: 630 }], title, description: category.introduction, url: canonicalSiteUrl(categoryPath(category, district)) } }
}

export default async function CategoryPage({ category, district, page = 1 }: { category: Category; district?: string; page?: number }) {
  const result = await categoryResult(category.type, category.transaction, district || '', page)
  if (district && result.total < 3) notFound()
  const pages = Math.max(1, Math.ceil(result.total / 12))
  if (page > pages) notFound()
  const path = categoryPath(category, district)
  const returnTo = '/properties?' + new URLSearchParams({ transaction: category.transaction, property_type: category.type, district: district || '' }).toString()
  const inventory = district ? [] : await getSitemapProperties().catch(() => [])
  const districtResults = districts.map(name => ({ name, result: { total: inventory.filter(item => item.district === name && item.property_type === category.type && item.transaction_type === category.transaction).length } }))

  const neighborhoods = [...new Set(result.items.map(item => item.area_name).filter(Boolean))].slice(0,6)
  const schema = { '@context':'https://schema.org','@type':'CollectionPage',url:canonicalSiteUrl(path + (page > 1 ? '?page=' + page : '')),name:category.label + ' in ' + (district || 'Kathmandu Valley'),
    mainEntity:{'@type':'ItemList',itemListElement:result.items.map((item,index)=>({'@type':'ListItem',position:(page-1)*12+index+1,url:canonicalSiteUrl('/properties/'+item.id),name:item.title}))},
    breadcrumb:{'@type':'BreadcrumbList',itemListElement:[{'@type':'ListItem',position:1,name:'Home',item:canonicalSiteUrl('/')},{'@type':'ListItem',position:2,name:'Properties',item:canonicalSiteUrl('/properties')},{'@type':'ListItem',position:3,name:category.label,item:canonicalSiteUrl(categoryPath(category))},...(district ? [{'@type':'ListItem',position:4,name:district,item:canonicalSiteUrl(path)}] : [])]} }
  return <main id="main" className="wrap listing-page"><RememberSearch path={returnTo} /><script type="application/ld+json" dangerouslySetInnerHTML={{__html:jsonLdText(schema)}} /><nav className="breadcrumbs" aria-label="Breadcrumb"><Link href="/">Home</Link><span>/</span><Link href="/properties">Properties</Link>{district && <><span>/</span><Link href={categoryPath(category)}>{category.label}</Link></>}</nav>
    <header className="page-heading"><div><p className="eyebrow">KATHMANDU VALLEY PROPERTY LISTINGS</p><h1>{category.label} in {district || 'Kathmandu Valley'}</h1><p>{category.introduction.replaceAll('Kathmandu Valley', district || 'Kathmandu Valley')}</p></div></header>
    {district && neighborhoods.length > 0 && <section className="district-context"><h2>Locations in these {district} listings</h2><p>The properties shown on this page include published locations in {neighborhoods.join(', ')}. Open a listing to compare its reported size, asking price, photos, and available address details.</p></section>}
    <p>{result.total} recent {result.total === 1 ? 'listing' : 'listings'} with property photos.</p>
    <Link className="button secondary" href={returnTo}>Refine these listings</Link>
    {result.items.length ? <div className="property-grid category-results">{result.items.map(property => <PropertyCard key={property.id} property={property} returnTo={returnTo} />)}</div> : <div className="empty-state"><h2>No recent properties in this category</h2><p>Try another category or check back for new listings.</p></div>}
    {pages > 1 && <nav className="pagination" aria-label="Category pages">{page > 1 && <Link href={path + (page > 2 ? '?page=' + (page - 1) : '')}>Previous</Link>}<span>Page {page} of {pages}</span>{page < pages && <Link href={path + '?page=' + (page + 1)}>Next</Link>}</nav>}
    {districtResults.some(item => item.result.total >= 3) && <section className="browse-category-links"><h2>Browse this category by district</h2>{districtResults.filter(item => item.result.total >= 3).map(item => <Link key={item.name} href={categoryPath(category, item.name)}>{category.label} in {item.name} ({item.result.total})</Link>)}</section>}
    <BrowseLinks /><p className="disclaimer">Listings are supplied by owners or collected from public sources. Confirm availability, prices, property boundaries, and documents with the advertiser.</p>
  </main>
}
