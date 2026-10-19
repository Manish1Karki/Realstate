'use client'

import Link from 'next/link'
import { useEffect, useState, type FormEvent } from 'react'

type User = {
  id: number
  email: string
  display_name: string
  phone_number: string
  alternate_phone: string
  created_at: string
  last_login_at: string | null
}

async function responseMessage(response: Response) {
  const value = response.status === 204 ? {} : await response.json().catch(() => ({}))
  if (!response.ok) throw new Error(typeof value.detail === 'string' ? value.detail : 'Unable to save your changes. Please try again.')
  return value
}

export default function DashboardClient() {
  const [user, setUser] = useState<User | null>(null)
  const [ready, setReady] = useState(false)
  const [emailVerified, setEmailVerified] = useState(false)
  const [profileMessage, setProfileMessage] = useState('')
  const [profileError, setProfileError] = useState(false)
  const [securityMessage, setSecurityMessage] = useState('')
  const [securityError, setSecurityError] = useState(false)
  const [emailMessage, setEmailMessage] = useState('')
  const [emailError, setEmailError] = useState(false)
  const [pending, setPending] = useState('')

  useEffect(() => {
    let active = true
    async function load() {
      const params = new URLSearchParams(window.location.search)
      const verificationToken = params.get('verify_email')
      if (verificationToken) {
        try {
          const value = await responseMessage(await fetch('/api/auth/confirm-email', {
            method: 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ token: verificationToken }),
          }))
          if (active) {
            setEmailMessage(value.message || 'Email address updated.')
            setEmailError(false)
            setEmailVerified(true)
            if (value.user) setUser(value.user)
          }
        } catch (cause) {
          if (active) { setEmailMessage(cause instanceof Error ? cause.message : 'Email verification failed.'); setEmailError(true) }
        }
        window.history.replaceState(null, '', '/dashboard')
      }
      try {
        const response = await fetch('/api/auth/me', { credentials: 'include', cache: 'no-store', signal: AbortSignal.timeout(8000) })
        if (response.status === 401 && !verificationToken) {
          window.location.assign('/login?next=%2Fdashboard')
          return
        }
        if (response.ok) {
          const value = await response.json()
          if (!value.user && !verificationToken) { window.location.assign('/login?next=%2Fdashboard'); return }
          if (active) setUser(value.user)
        } else if (response.status !== 401 && active) {
          setProfileMessage('The account service is unavailable. Please try again.')
          setProfileError(true)
        }
      } catch {
        if (active) { setProfileMessage('The account service is unavailable. Please try again.'); setProfileError(true) }
      } finally {
        if (active) setReady(true)
      }
    }
    void load()
    return () => { active = false }
  }, [])

  async function saveProfile(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const data = new FormData(event.currentTarget)
    setPending('profile'); setProfileMessage(''); setProfileError(false)
    try {
      const value = await responseMessage(await fetch('/api/auth/me', {
        method: 'PATCH', credentials: 'include', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ display_name: data.get('display_name'), phone_number: data.get('phone_number'), alternate_phone: data.get('alternate_phone') }),
      }))
      setUser(value.user); setProfileMessage(value.message || 'Profile updated.')
    } catch (cause) { setProfileMessage(cause instanceof Error ? cause.message : 'Unable to update your profile.'); setProfileError(true) }
    finally { setPending('') }
  }

  async function changePassword(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const form = event.currentTarget
    const data = new FormData(form)
    if (data.get('new_password') !== data.get('confirm_password')) {
      setSecurityMessage('The new passwords do not match.'); setSecurityError(true); return
    }
    setPending('password'); setSecurityMessage(''); setSecurityError(false)
    try {
      const value = await responseMessage(await fetch('/api/auth/change-password', {
        method: 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ current_password: data.get('current_password'), new_password: data.get('new_password') }),
      }))
      form.reset(); setSecurityMessage(value.message || 'Password changed.')
    } catch (cause) { setSecurityMessage(cause instanceof Error ? cause.message : 'Unable to change your password.'); setSecurityError(true) }
    finally { setPending('') }
  }

  async function requestEmailChange(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const form = event.currentTarget
    const data = new FormData(form)
    setPending('email'); setEmailMessage(''); setEmailError(false)
    try {
      const value = await responseMessage(await fetch('/api/auth/request-email-change', {
        method: 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: data.get('email'), current_password: data.get('current_password') }),
      }))
      form.reset(); setEmailMessage(value.message || 'Check your new email for a verification link.')
    } catch (cause) { setEmailMessage(cause instanceof Error ? cause.message : 'Unable to request an email change.'); setEmailError(true) }
    finally { setPending('') }
  }

  async function signOut() {
    await fetch('/api/auth/logout', { method: 'POST', credentials: 'include' }).catch(() => {})
    window.location.assign('/')
  }

  if (!ready) return <div className="dashboard-loading" role="status">Loading your account…</div>
  if (!user) return <section className="dashboard-card dashboard-signed-out"><p className="eyebrow">{emailVerified ? 'EMAIL VERIFIED' : 'YOUR ACCOUNT'}</p><h1>{emailVerified ? 'Your account email is updated.' : 'Sign in to manage your account.'}</h1><p>{emailVerified ? 'Sign in with your new email address to manage your profile.' : profileMessage || emailMessage || 'Sign in to access your profile and security settings.'}</p>{emailMessage && <p className={emailError ? 'form-message error' : 'form-message'} role={emailError ? 'alert' : 'status'}>{emailMessage}</p>}<Link className="button primary" href="/login">Go to sign in</Link></section>

  return <>
    <div className="dashboard-heading"><div><p className="eyebrow">YOUR LAND DISCOVER ACCOUNT</p><h1>Welcome{user.display_name ? `, ${user.display_name.split(' ')[0]}` : ' back'}.</h1><p>Manage your personal information, contact details, and sign-in security.</p></div><button className="button secondary" onClick={signOut}>Sign out</button></div>
    <div className="dashboard-grid">
      <section className="dashboard-card dashboard-overview"><p className="eyebrow">ACCOUNT OVERVIEW</p><h2>{user.display_name || 'Your profile'}</h2><p>{user.email}</p><span className="account-status"><i /> Account active</span></section>
      <section className="dashboard-card dashboard-section"><div className="dashboard-section-heading"><div><p className="eyebrow">PERSONAL DETAILS</p><h2>Profile information</h2></div></div>
        <form className="settings-form" onSubmit={saveProfile}>
          <label>Full name<input name="display_name" autoComplete="name" maxLength={120} defaultValue={user.display_name} required disabled={pending === 'profile'} /></label>
          <div className="settings-fields"><label>Primary phone<input name="phone_number" type="tel" autoComplete="tel" maxLength={32} defaultValue={user.phone_number} placeholder="+977 98…" disabled={pending === 'profile'} /></label><label>Alternate phone<input name="alternate_phone" type="tel" autoComplete="tel" maxLength={32} defaultValue={user.alternate_phone} placeholder="Optional" disabled={pending === 'profile'} /></label></div>
          {profileMessage && <p className={profileError ? 'form-message error' : 'form-message'} role={profileError ? 'alert' : 'status'}>{profileMessage}</p>}
          <button className="button primary" disabled={pending === 'profile'}>{pending === 'profile' ? 'Saving…' : 'Save profile'}</button>
        </form>
      </section>
      <section className="dashboard-card dashboard-section"><div className="dashboard-section-heading"><div><p className="eyebrow">EMAIL ADDRESS</p><h2>Change account email</h2></div></div><p className="settings-help">Current email: <strong>{user.email}</strong>. We’ll send a confirmation link to the new address before changing your account.</p>
        <form className="settings-form" onSubmit={requestEmailChange}>
          <label>New email address<input name="email" type="email" autoComplete="email" maxLength={254} required disabled={pending === 'email'} /></label>
          <label>Current password<input name="current_password" type="password" autoComplete="current-password" maxLength={128} required disabled={pending === 'email'} /></label>
          {emailMessage && <p className={emailError ? 'form-message error' : 'form-message'} role={emailError ? 'alert' : 'status'}>{emailMessage}</p>}
          <button className="button primary" disabled={pending === 'email'}>{pending === 'email' ? 'Sending…' : 'Send verification link'}</button>
        </form>
      </section>
      <section className="dashboard-card dashboard-section"><div className="dashboard-section-heading"><div><p className="eyebrow">SIGN-IN SECURITY</p><h2>Change password</h2></div></div><p className="settings-help">Use at least eight characters. Other active sessions will be signed out.</p>
        <form className="settings-form" onSubmit={changePassword}>
          <label>Current password<input name="current_password" type="password" autoComplete="current-password" maxLength={128} required disabled={pending === 'password'} /></label>
          <label>New password<input name="new_password" type="password" autoComplete="new-password" minLength={8} maxLength={128} required disabled={pending === 'password'} /></label>
          <label>Confirm new password<input name="confirm_password" type="password" autoComplete="new-password" minLength={8} maxLength={128} required disabled={pending === 'password'} /></label>
          {securityMessage && <p className={securityError ? 'form-message error' : 'form-message'} role={securityError ? 'alert' : 'status'}>{securityMessage}</p>}
          <button className="button primary" disabled={pending === 'password'}>{pending === 'password' ? 'Updating…' : 'Update password'}</button>
          <Link className="dashboard-reset-link" href="/login">Forgot your current password?</Link>
        </form>
      </section>
    </div>
  </>
}
