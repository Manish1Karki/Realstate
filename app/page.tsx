import Link from 'next/link'

export default function HomePage() {
  return <main id="main">
    <section className="hero wrap">
      <div className="hero-copy"><p className="eyebrow"><span /> Property intelligence for Nepal</p>
        <h1>Find your place.<br /><em>Know your market.</em></h1>
        <p className="hero-lede">Explore property listings across Kathmandu Valley, compare asking prices, and understand the neighborhood before you make your next move.</p>
        <div className="hero-actions"><Link className="button primary" href="/properties">Browse properties <span aria-hidden="true">→</span></Link><a className="text-link" href="#how-it-works">How it works</a></div>
        <p className="trust-note">Local listings. Clear details. A more informed search.</p>
      </div>
      <div className="hero-art" aria-label="Illustration of a Kathmandu Valley neighborhood"><div className="sun" /><div className="ridge ridge-back" /><div className="ridge ridge-front" /><div className="neighborhood"><span>Baluwatar</span><span>Lazimpat</span><span>Maharajgunj</span></div><div className="art-card"><span className="eyebrow">PROPERTY DISCOVERY</span><strong>See the details<br />behind every place.</strong><Link href="/properties">Explore the marketplace <span aria-hidden="true">↗</span></Link></div></div>
    </section>
    <section className="proof-strip"><span>PROPERTY LISTINGS</span><i>✦</i><span>LOCATION CONTEXT</span><i>✦</i><span>ASKING-PRICE DETAILS</span><i>✦</i><span>KATHMANDU VALLEY</span></section>
    <section className="section wrap" id="how-it-works"><div className="section-heading"><p className="eyebrow">A clearer way to explore</p><h2>Start with the listing.<br /><em>Understand the place.</em></h2><p>Browse available properties, open a detail page, and review the asking price, size, address, source, and other available information in one place.</p></div>
      <div className="feature-grid"><article><span>01</span><h3>Search the market</h3><p>Explore homes and land, then narrow the results by property type, district, and price.</p></article><article><span>02</span><h3>Review the details</h3><p>Each listing links back to its source so you can confirm availability and ask follow-up questions.</p></article><article><span>03</span><h3>Compare locations</h3><p>Use available neighborhood and amenity information to guide your next steps.</p></article></div>
    </section>
    <section className="closing wrap"><div><p className="eyebrow">Your next move starts here</p><h2>Discover a place<br /><em>that feels right.</em></h2></div><Link className="button cream" href="/properties">Explore Kathmandu Valley listings <span aria-hidden="true">→</span></Link></section>
  </main>
}
