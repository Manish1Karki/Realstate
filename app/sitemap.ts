import type { MetadataRoute } from 'next'
import { canonicalSiteUrl, getSitemapProperties } from '@/lib/api'

export const revalidate = 1800
export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const pages: MetadataRoute.Sitemap = [
    { url: canonicalSiteUrl('/'), changeFrequency: 'weekly', priority: 1 },
    { url: canonicalSiteUrl('/properties'), changeFrequency: 'hourly', priority: 0.9 },
  ]
  try {
    for (const item of await getSitemapProperties()) pages.push({ url: canonicalSiteUrl(`/properties/${item.id}`), lastModified: item.scraped_date || undefined, changeFrequency: 'daily', priority: 0.7 })
  } catch { /* Keep the stable sitemap available during backend maintenance. */ }
  return pages
}
