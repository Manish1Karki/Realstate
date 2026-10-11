import Link from 'next/link'

export default function NotFound() {
  return <main id="main" className="wrap not-found"><p className="eyebrow">404 · NOT FOUND</p><h1>This listing is no longer available.</h1><p>It may have been removed from the original source or the address may be incorrect.</p><Link className="button primary" href="/properties">Browse current listings</Link></main>
}
