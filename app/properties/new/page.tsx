import type { Metadata } from 'next'
import Link from 'next/link'
import NewListingForm from './new-listing-form'
import { cookies } from 'next/headers'
import { redirect } from 'next/navigation'

export const metadata: Metadata = { title: 'List your property', robots: { index: false, follow: false } }
export default async function NewListingPage() {
  const session = (await cookies()).get('land_discover_session')
  const login = '/login?next=%2Fproperties%2Fnew'
  if (!session) redirect(login)
  const headers: Record<string, string> = { Cookie: `land_discover_session=${session.value}` }
  if (process.env.BACKEND_PROXY_SECRET) headers['X-Land-Proxy-Token'] = process.env.BACKEND_PROXY_SECRET
  const origin = (process.env.LAND_API_URL || process.env.BACKEND_API_URL || 'http://127.0.0.1:8000').replace(/\/$/, '')
  const response = await fetch(`${origin}/api/auth/me`, { headers, cache: 'no-store' })
  if (response.status === 401) redirect(login)
  if (!response.ok) throw new Error('Unable to verify your session. Please try again.')
  const { user } = await response.json()
  return <main id="main" className="wrap submit-page">
    <nav className="breadcrumbs" aria-label="Breadcrumb"><Link href="/properties">Properties</Link><span>/</span><span>List a property</span></nav>
    <header className="listing-page-heading"><h1>List your property</h1><p>A few details to help the right people find your place.</p></header>
    <NewListingForm displayName={user.display_name || user.email} />
    <footer className="listing-page-footer"><span>Land Discover</span><span>Property, made straightforward.</span></footer>
  </main>
}
