'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useEffect, useState } from 'react'

type User = { display_name: string; email: string }
export default function AccountControl() {
  const pathname = usePathname()
  const [user, setUser] = useState<User | null>(null)
  const [ready, setReady] = useState(false)
  useEffect(() => { fetch('/api/auth/me', { credentials: 'include', cache: 'no-store', signal: AbortSignal.timeout(8000) }).then(response => response.ok ? response.json() : null).then(value => setUser(value?.user || null)).catch(() => {}).finally(() => setReady(true)) }, [])
  async function signOut() {
    await fetch('/api/auth/logout', { method: 'POST', credentials: 'include' }).catch(() => {})
    setUser(null)
    window.location.assign('/')
  }
  if (!ready || !user) return <Link className="sign-in" href="/login">{pathname === '/' ? 'Log in' : 'Sign in'}</Link>
  if (pathname === '/properties/new') return <details className="listing-account-menu"><summary>{user.display_name || user.email}<svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.4" aria-hidden="true"><path d="m3 6 5 5 5-5" /></svg></summary><div><Link href="/dashboard">My account</Link><button type="button" onClick={signOut}>Sign out</button></div></details>
  return <div className="account-control"><Link className="sign-in" href="/dashboard" title={user.email}>{user.display_name || user.email}</Link><button className="sign-in" onClick={signOut}>Sign out</button></div>
}
