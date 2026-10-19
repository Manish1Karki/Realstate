import { websiteSchema } from '@/lib/structured-data'
import { jsonLdText } from '@/lib/property-content'
import type { Metadata } from 'next'
import { canonicalSiteUrl } from '@/lib/api'
import BrowseLinks from './properties/browse-links'

export const metadata: Metadata = { alternates: { canonical: canonicalSiteUrl('/') }, openGraph: { type: 'website', title: 'Land Discover | Property listings in Kathmandu Valley', url: canonicalSiteUrl('/'), images: [{ url: canonicalSiteUrl('/social-image'), width: 1200, height: 630, alt: 'Land Discover property listings in Kathmandu Valley' }] } }
import Link from 'next/link'

export default function HomePage() {
  return <main id="main"><script type="application/ld+json" dangerouslySetInnerHTML={{ __html:jsonLdText(websiteSchema()) }} />
    <section className="hero wrap">
      <div className="hero-copy"><p className="eyebrow"><span /> Houses, land, and flats in Nepal</p>
        <h1>Find a house,<br /><em>land, or flat.</em></h1>
        <p className="hero-lede">Find houses, land, and flats for sale or rent in Kathmandu Valley. See photos, prices, and nearby places before you choose.</p>
        <div className="hero-actions"><Link className="button primary" href="/properties">Find a place <span aria-hidden="true">→</span></Link><a className="text-link" href="#how-it-works">How to use this site</a></div>
        <p className="trust-note">Local homes and land. Photos and details in one place.</p>
      </div>
      <div className="hero-art" aria-label="Illustration of a Kathmandu Valley neighborhood"><div className="sun" /><div className="ridge ridge-back" /><div className="ridge ridge-front" /><div className="neighborhood"><span>Baluwatar</span><span>Lazimpat</span><span>Maharajgunj</span></div><div className="art-card"><span className="eyebrow">FIND YOUR PLACE</span><strong>See photos and details.</strong><Link href="/properties">See houses, land, and flats <span aria-hidden="true">↗</span></Link></div></div>
    </section>
    <section className="proof-strip"><span>HOUSES, LAND, AND FLATS</span><i>✦</i><span>NEARBY PLACES</span><i>✦</i><span>PRICES</span><i>✦</i><span>KATHMANDU VALLEY</span></section>
    <section className="section wrap" id="how-it-works"><div className="section-heading"><p className="eyebrow">Easy steps to find a place</p><h2>See a place you like?<br /><em>Learn more about it.</em></h2><p>Click a house, land, or flat to see its photos, price, size, and address, if shown.</p></div>
      <div className="feature-grid"><article><span>01</span><h3>Find a place</h3><p>Choose a house, land, or flat. Then choose a district to see places there.</p></article><article><span>02</span><h3>Read the details</h3><p>Use the link to the original website. Ask the person who posted it if the place is still for sale or rent.</p></article><article><span>03</span><h3>Check nearby places</h3><p>Check the map for nearby schools, hospitals, shops, and roads, where shown.</p></article></div>
    </section>
    <div className="wrap"><BrowseLinks simpleEnglish /></div>
    <section className="closing wrap"><div><p className="eyebrow">Ready to find a place?</p><h2>Find the right place<br /><em>for you.</em></h2></div><Link className="button cream" href="/properties">Find a place in Kathmandu Valley <span aria-hidden="true">→</span></Link></section>
  </main>
}
