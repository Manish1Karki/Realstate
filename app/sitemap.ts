import type { MetadataRoute } from 'next'
import { connection } from 'next/server'
import { canonicalSiteUrl, getSitemapProperties } from '@/lib/api'
import { categories, categoryPath, districts } from '@/lib/property-categories'

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  // Only the backend inventory fetch is cached (five minutes), not a second route snapshot.
  await connection()
  const inventory = await getSitemapProperties()
  const pages: MetadataRoute.Sitemap = [{ url: canonicalSiteUrl('/') }, { url: canonicalSiteUrl('/properties') }]
  for (const category of categories) {
    const matching = inventory.filter(item => item.property_type === category.type && item.transaction_type === category.transaction)
    const pageCount = Math.ceil(matching.length / 12)
    for (let page = 1; page <= pageCount; page++) pages.push({ url: canonicalSiteUrl(categoryPath(category) + (page > 1 ? '?page=' + page : '')) })
    for (const district of districts) {
      const districtCount = matching.filter(item => item.district === district).length
      if (districtCount >= 3) for (let page = 1; page <= Math.ceil(districtCount / 12); page++) pages.push({ url: canonicalSiteUrl(categoryPath(category, district) + (page > 1 ? '?page=' + page : '')) })
    }
  }
  for (const item of inventory) pages.push({ url: canonicalSiteUrl('/properties/' + item.id), ...(item.content_updated_at ? { lastModified: item.content_updated_at } : {}) })
  // A cold backend failure throws instead of publishing a misleading partial sitemap.
  // Next's data cache retains a previous successful response when background revalidation fails.
  return pages
}
