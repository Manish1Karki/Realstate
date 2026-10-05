import { useEffect, useState } from 'react'
import './AccountMenu.css'

const API_URL = import.meta.env.VITE_AUTH_API_URL?.replace(/\/$/, '') || '/api/auth'

export default function AccountMenu({ signInClass = '' }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const [pending, setPending] = useState(false)
  const [error, setError] = useState('')
  useEffect(() => {
    const controller = new AbortController()
    fetch(`${API_URL}/me`, { credentials: 'include', signal: controller.signal })
      .then(async response => { if (response.ok) setUser((await response.json()).user) })
      .catch(() => {})
      .finally(() => { if (!controller.signal.aborted) setLoading(false) })
    return () => controller.abort()
  }, [])
  async function signOut() {
    setPending(true); setError('')
    try {
      const response = await fetch(`${API_URL}/logout`, { method: 'POST', credentials: 'include' })
      if (!response.ok) throw new Error('Unable to sign out. Please try again.')
      setUser(null)
    } catch (cause) { setError(cause.message) }
    finally { setPending(false) }
  }
  if (loading) return <span className="account-loading" aria-label="Checking account">Checking account...</span>
  if (!user) return <a className={signInClass} href="/login">Sign in</a>
  return <div className="account-menu">
    <span title={user.email}>{user.display_name || user.email}</span>
    <button type="button" disabled={pending} onClick={signOut}>{pending ? 'Signing out...' : 'Sign out'}</button>
    {error && <span className="account-error" role="alert">{error}</span>}
  </div>
}
