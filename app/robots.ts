import type { MetadataRoute } from 'next'
import { canonicalSiteUrl } from '@/lib/api'

export default function robots(): MetadataRoute.Robots {
  return { rules: { userAgent: '*', allow: '/', disallow: ['/api/', '/aggregator/'] }, sitemap: canonicalSiteUrl('/sitemap.xml') }
}
