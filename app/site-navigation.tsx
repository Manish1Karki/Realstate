'use client'

import Link from 'next/link'
import { usePathname, useSearchParams } from 'next/navigation'
import { Suspense, useRef, useState, type KeyboardEvent } from 'react'

const links = [
  { label: 'Home', href: '/', key: 'home' },
  { label: 'Buy', href: '/properties?transaction=sale', key: 'sale' },
  { label: 'Rent', href: '/properties?transaction=rent', key: 'rent' },
  { label: 'How to use', href: '/#how-it-works', key: 'guide' },
  { label: 'Contact us', href: '/contact', key: 'contact' },
]

function NavigationLinks({ pathname, transaction, close }: { pathname: string; transaction?: string | null; close: () => void }) {
  return <>{links.map(link => {
    const current = link.key === 'home' ? pathname === '/'
      : link.key === 'contact' ? pathname === '/contact'
      : ['sale', 'rent'].includes(link.key) && pathname.startsWith('/properties') && pathname !== '/properties/new'
        && (transaction === link.key || pathname.includes(link.key === 'sale' ? '-for-sale' : '-for-rent'))
    return <Link key={link.key} href={link.href} aria-current={current ? 'page' : undefined} onNavigate={close}>{link.label}</Link>
  })}</>
}

function SearchAwareLinks({ pathname, close }: { pathname: string; close: () => void }) {
  const search = useSearchParams()
  return <NavigationLinks pathname={pathname} transaction={search.get('transaction')} close={close} />
}

export default function SiteNavigation() {
  const pathname = usePathname()
  const [open, setOpen] = useState(false)
  const toggle = useRef<HTMLButtonElement>(null)
  function escape(event: KeyboardEvent) {
    if (event.key === 'Escape') { setOpen(false); toggle.current?.focus() }
  }
  return <>
    <button ref={toggle} className="site-navigation-toggle" type="button" aria-expanded={open} aria-controls="site-primary-navigation" onClick={() => setOpen(!open)} onKeyDown={escape}>
      <span>{open ? 'Close' : 'Menu'}</span><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" aria-hidden="true">{open ? <path d="m6 6 12 12M18 6 6 18" /> : <path d="M4 6h16M4 12h16M4 18h16" />}</svg>
    </button>
    <nav id="site-primary-navigation" className={'site-primary-nav' + (open ? ' is-open' : '')} aria-label="Main navigation" onKeyDown={escape}>
      <Suspense fallback={<NavigationLinks pathname={pathname} close={() => setOpen(false)} />}><SearchAwareLinks pathname={pathname} close={() => setOpen(false)} /></Suspense>
    </nav>
  </>
}
