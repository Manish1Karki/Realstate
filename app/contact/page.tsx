import type { Metadata } from 'next'
import Link from 'next/link'

export const metadata: Metadata = {
  title: 'Contact',
  description: 'Contact property advertisers for listing details and viewings.',
}

export default function ContactPage() {
  return <main id="main" className="wrap contact-page">
    <p className="eyebrow">GET IN TOUCH</p>
    <h1>Contact</h1>
    <section className="detail-panel">
      <h2>Speak with a property advertiser</h2>
      <p className="property-description">For property details, availability, or arranging a viewing, open the property listing and use its published contact number.</p>
      <Link className="button primary" href="/properties">Browse properties</Link>
    </section>
  </main>
}
