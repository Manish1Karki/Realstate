'use client'

import Link from 'next/link'
import { useEffect, useState, type FormEvent } from 'react'

type Mode = 'login' | 'register' | 'forgot' | 'reset'

export default function LoginForm() {
  const [mode, setMode] = useState<Mode>('login')
  const [pending, setPending] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState(false)
  const [resetAvailable, setResetAvailable] = useState<boolean | null>(null)
  const [localResetAvailable, setLocalResetAvailable] = useState<boolean | null>(null)
  const [resetToken, setResetToken] = useState('')

  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const token = params.get('reset_token') || ''
    setResetToken(token)
    if (token) setMode('reset')
    fetch('/api/auth/config')
      .then(response => response.ok ? response.json() : null)
      .then(value => {
        setResetAvailable(Boolean(value?.password_reset_available))
        setLocalResetAvailable(Boolean(value?.local_password_reset_available))
      })
      .catch(() => { setResetAvailable(false); setLocalResetAvailable(false) })
    if (!token) fetch('/api/auth/me').then(response => {
      if (response.ok) {
        const next = params.get('next')
        window.location.assign(next?.startsWith('/') && !next.startsWith('//') && !next.includes('\\') ? next : '/dashboard')
      }
    }).catch(() => {})
  }, [])

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const data = new FormData(event.currentTarget)
    const password = String(data.get('password') || '')
    const localReset = mode === 'forgot' && localResetAvailable === true

    if ((mode === 'register' || mode === 'reset' || localReset) && password !== data.get('confirm_password')) {
      setMessage('The passwords do not match.')
      setError(true)
      return
    }

    const endpoint = mode === 'register' ? 'register'
      : localReset ? 'local-reset-password'
        : mode === 'forgot' ? 'forgot-password'
          : mode === 'reset' ? 'reset-password' : 'login'
    const body = mode === 'reset' ? { token: resetToken, password }
      : localReset ? { email: data.get('email'), password }
        : {
            email: data.get('email'), ...(mode !== 'forgot' ? { password } : {}),
            ...(mode === 'register' ? { display_name: data.get('display_name') } : {}),
            remember: data.get('remember') === 'on',
          }

    setPending(true)
    setMessage('')
    setError(false)
    try {
      const response = await fetch(`/api/auth/${endpoint}`, {
        method: 'POST', credentials: 'include',
        headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
      })
      const value = response.status === 204 ? {} : await response.json()
      if (!response.ok) throw new Error(typeof value.detail === 'string' ? value.detail : 'Unable to complete this request. Please try again.')

      if (mode === 'login' || mode === 'register') {
        const next = new URLSearchParams(window.location.search).get('next')
        window.location.assign(next?.startsWith('/') && !next.startsWith('//') && !next.includes('\\') ? next : '/dashboard')
      } else if (mode === 'reset') {
        window.history.replaceState(null, '', '/login')
        setResetToken('')
        setMode('login')
        setMessage('Password updated. You can now sign in.')
      } else if (localReset) {
        setMode('login')
        setMessage(value.message || 'Password changed. You can now sign in.')
      } else {
        setMessage(value.message || 'If an account exists, you will receive a reset link.')
      }
    } catch (cause) {
      setMessage(cause instanceof Error ? cause.message : 'Unable to reach the account service.')
      setError(true)
    } finally {
      setPending(false)
    }
  }

  const title = mode === 'register' ? 'Create your account'
    : mode === 'forgot' ? 'Reset your password'
      : mode === 'reset' ? 'Choose a new password' : 'Welcome back'
  const checkingRecovery = resetAvailable === null || localResetAvailable === null
  const recoveryAvailable = resetAvailable === true || localResetAvailable === true
  const localReset = mode === 'forgot' && localResetAvailable === true

  return <section className="auth-card">
    <div className="auth-story">
      <p className="eyebrow">LAND DISCOVER</p>
      <h1>Make room for<br /><em>what comes next.</em></h1>
      <p>Save properties and return to your search when you are ready.</p>
    </div>
    <div className="auth-panel">
      <p className="eyebrow">YOUR ACCOUNT</p>
      <h2>{title}</h2>
      <p className="auth-description">
        {mode === 'register' ? 'Create an account to save and list properties.'
          : mode === 'forgot' && localResetAvailable ? 'For local development, enter your account email and choose a new password.'
            : mode === 'forgot' && resetAvailable ? 'Enter your email and we will send a reset link if the account exists.'
              : mode === 'forgot' ? 'Password recovery is temporarily unavailable.'
                : mode === 'reset' ? 'Choose a new password for your account.'
                  : 'Sign in to continue to Land Discover.'}
      </p>
      <form onSubmit={submit} key={mode}>
        {mode === 'forgot' && !recoveryAvailable && <p className="form-message unavailable" role="status">
          {checkingRecovery ? 'Checking password recovery availability…' : 'Password reset email is not configured. Ask the site administrator to configure mail delivery.'}
        </p>}
        {mode === 'register' && <label>Full name<input name="display_name" autoComplete="name" maxLength={120} required disabled={pending} /></label>}
        {mode !== 'reset' && !(mode === 'forgot' && !checkingRecovery && !recoveryAvailable) && <label>Email address<input name="email" type="email" autoComplete="email" maxLength={254} required disabled={pending} /></label>}
        {(mode !== 'forgot' || localReset) && <label>{localReset ? 'New password' : 'Password'}<input name="password" type="password" autoComplete={mode === 'login' ? 'current-password' : 'new-password'} minLength={mode === 'login' ? undefined : 8} maxLength={128} required disabled={pending} /></label>}
        {(mode === 'register' || mode === 'reset' || localReset) && <label>Confirm password<input name="confirm_password" type="password" autoComplete="new-password" minLength={8} maxLength={128} required disabled={pending} /></label>}
        {mode === 'login' && <label className="remember"><input type="checkbox" name="remember" disabled={pending} /> Remember me</label>}
        {message && <p className={error ? 'form-message error' : 'form-message'} role={error ? 'alert' : 'status'}>{message}</p>}
        <button className="button primary auth-submit" disabled={pending || (mode === 'forgot' && !recoveryAvailable)}>
          {pending ? 'Please wait…'
            : mode === 'register' ? 'Create account'
              : mode === 'forgot' && checkingRecovery ? 'Checking availability…'
                : localReset ? 'Change password'
                  : mode === 'forgot' && !recoveryAvailable ? 'Password recovery unavailable'
                    : mode === 'forgot' ? 'Send reset link'
                      : mode === 'reset' ? 'Update password' : 'Sign in'}
        </button>
      </form>
      <div className="auth-links">
        {mode === 'login' && <button onClick={() => { setMode('forgot'); setMessage('') }}>Forgot password?</button>}
        {mode === 'login'
          ? <p>New to Land Discover? <button onClick={() => { setMode('register'); setMessage('') }}>Create an account</button></p>
          : mode !== 'reset' && <p>Already have an account? <button onClick={() => { setMode('login'); setMessage('') }}>Sign in</button></p>}
      </div>
      <Link className="back-link" href="/properties">← Browse properties</Link>
    </div>
  </section>
}
