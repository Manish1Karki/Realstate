import type { Metadata, Viewport } from 'next'
import Link from 'next/link'
import './globals.css'
import './login/auth.css'
import './market.css'
import './palette.css'
import './property-information.css'
import { canonicalSiteUrl } from '@/lib/api'
import AccountControl from './account-control'
import WhatsAppButton from './whatsapp-button'
import HomepageText from './homepage-text'
import SiteNavigation from './site-navigation'

export const metadata: Metadata = {
  metadataBase: new URL(canonicalSiteUrl()),
  title: { default: 'Land Discover | Property listings in Kathmandu Valley', template: '%s | Land Discover' },
  description: 'Explore property listings across Kathmandu Valley. Compare asking prices, locations, property details, and nearby amenities.',
  applicationName: 'Land Discover',
  openGraph: { type: 'website', siteName: 'Land Discover', locale: 'en_NP', images: [{ url: canonicalSiteUrl('/social-image'), width: 1200, height: 630, alt: 'Land Discover property listings in Kathmandu Valley' }] },
  twitter: { card: 'summary_large_image', images: [canonicalSiteUrl('/social-image')] },
  icons: { icon: '/favicon.ico', apple: '/apple-icon.png' },
  robots: { index: true, follow: true },
}

export const viewport: Viewport = { width: 'device-width', initialScale: 1, themeColor: '#363c46' }

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en" data-scroll-behavior="smooth"><body>
    <a className="skip-link" href="#main"><HomepageText home="Go to the main page content" standard="Skip to content" /></a>
    <header className="site-header">
      <Link className="brand" href="/" aria-label="Land Discover home"><span className="brand-mark" aria-hidden="true">LD</span><span>Land <b>Discover</b></span></Link>
      <SiteNavigation />
      <div className="header-actions"><AccountControl /><Link className="header-cta" href="/properties/new">Add a property <span aria-hidden="true">↗</span></Link></div>
    </header>
    {children}
    <footer className="site-footer"><div><Link className="brand footer-brand" href="/"><span className="brand-mark" aria-hidden="true">LD</span><span>Land <b>Discover</b></span></Link><p><HomepageText home="Find houses, land, and flats in Kathmandu Valley." standard="Property discovery for Kathmandu Valley." /></p></div><nav aria-label="Footer navigation"><Link href="/properties"><HomepageText home="Find a place" standard="Browse properties" /></Link></nav><small><HomepageText home="Before you decide, ask the person who posted it to check the price, details, and whether the place is still for sale or rent." standard="Listing details and availability should be verified with the original source." /></small></footer>
    <WhatsAppButton href="https://wa.me/9779803529868" />
  </body></html>
}
