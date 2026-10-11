import type { Metadata, Viewport } from 'next'
import Link from 'next/link'
import './globals.css'
import './login/auth.css'
import './market.css'
import { canonicalSiteUrl } from '@/lib/api'
import AccountControl from './account-control'

export const metadata: Metadata = {
  metadataBase: new URL(canonicalSiteUrl()),
  title: { default: 'Land Discover | Property listings in Kathmandu Valley', template: '%s | Land Discover' },
  description: 'Explore property listings across Kathmandu Valley. Compare asking prices, locations, property details, and nearby amenities.',
  applicationName: 'Land Discover',
  openGraph: { type: 'website', siteName: 'Land Discover', locale: 'en_NP' },
  robots: { index: true, follow: true },
}

export const viewport: Viewport = { width: 'device-width', initialScale: 1, themeColor: '#193e32' }

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>
    <a className="skip-link" href="#main">Skip to content</a>
    <header className="site-header">
      <Link className="brand" href="/" aria-label="Land Discover home"><span className="brand-mark">LD</span><span>Land <b>Discover</b></span></Link>
      <nav aria-label="Main navigation"><Link href="/properties">Properties</Link></nav>
      <div className="header-actions"><AccountControl /><Link className="header-cta" href="/properties">Explore listings <span aria-hidden="true">↗</span></Link></div>
    </header>
    {children}
    <footer className="site-footer"><div><Link className="brand footer-brand" href="/"><span className="brand-mark">LD</span><span>Land <b>Discover</b></span></Link><p>Property discovery for Kathmandu Valley.</p></div><nav aria-label="Footer navigation"><Link href="/properties">Browse properties</Link></nav><small>Listing details and availability should be verified with the original source.</small></footer>
  </body></html>
}
