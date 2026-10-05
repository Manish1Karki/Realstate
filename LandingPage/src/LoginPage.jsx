import { useEffect, useState } from 'react'
import './LoginPage.css'

const API_URL = import.meta.env.VITE_AUTH_API_URL?.replace(/\/$/, '') || '/api/auth'
const GOOGLE_URL = import.meta.env.VITE_GOOGLE_AUTH_URL
const DASHBOARD_URL = import.meta.env.VITE_DASHBOARD_URL || '/properties'

function HomeIcon() {
  return <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="m3 10 9-7 9 7M5 9v12h14V9M9 21v-8h6v8" /></svg>
}

export default function LoginPage() {
  const resetToken = new URLSearchParams(window.location.search).get('reset_token')
  const [mode, setMode] = useState(resetToken ? 'password-reset' : 'login')
  const [pending, setPending] = useState(false)
  const [notice, setNotice] = useState(null)
  const [resetAvailable, setResetAvailable] = useState(false)
  const isLogin = mode === 'login'
  const isReset = mode === 'reset'
  const isPasswordReset = mode === 'password-reset'
  const isRegister = mode === 'register'

  useEffect(() => {
    const controller = new AbortController()
    fetch(`${API_URL}/config`, { signal: controller.signal }).then(r => r.ok ? r.json() : null).then(value => { if (value) setResetAvailable(value.password_reset_available) }).catch(() => {})
    if (!resetToken) fetch(`${API_URL}/me`, { credentials: 'include', signal: controller.signal }).then(r => { if (r.ok) window.location.assign(DASHBOARD_URL) }).catch(() => {})
    return () => controller.abort()
  }, [resetToken])

  function changeMode(next) { setMode(next); setNotice(null) }
  async function submit(event) {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    if ((isRegister || isPasswordReset) && form.get('password') !== form.get('confirm_password')) {
      setNotice({ error: true, text: 'The passwords do not match.' }); return
    }
    setPending(true); setNotice(null)
    const endpoint = isPasswordReset ? 'reset-password' : isReset ? 'forgot-password' : isLogin ? 'login' : 'register'
    const body = isPasswordReset ? { token: resetToken, password: form.get('password') } : {
      email: form.get('email'), ...(!isReset && { password: form.get('password') }),
      ...(isRegister && { display_name: form.get('display_name') }), remember: form.get('remember') === 'on',
    }
    try {
      const response = await fetch(`${API_URL}/${endpoint}`, { method: 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
      const value = await response.json()
      if (!response.ok) throw new Error(typeof value.detail === 'string' ? value.detail : Array.isArray(value.detail) ? value.detail.map(e => e.msg).join('. ') : 'Unable to complete your request. Please try again.')
      if (isReset) setNotice({ text: value.message })
      else if (isPasswordReset) { window.history.replaceState(null, '', '/login'); setMode('login'); setNotice({ text: value.message }) }
      else window.location.assign(DASHBOARD_URL)
    } catch (error) { setNotice({ error: true, text: error instanceof TypeError ? 'Unable to reach the sign-in service. Please try again later.' : error.message }) }
    finally { setPending(false) }
  }

  return <main className="auth-page">
    <div className="auth-card">
      <aside className="auth-story" aria-label="A place to belong">
        <a className="auth-brand" href="/" aria-label="Land Discover home"><span><HomeIcon /></span>Land Discover</a>
        <div className="auth-story-copy"><span className="auth-pill">A PLACE TO BELONG</span><blockquote>A space that truly feels like yours.</blockquote><div className="auth-community"><div className="auth-avatars" aria-hidden="true"><span>AM</span><span>JL</span><span>SK</span></div><p>Your next chapter starts here.</p></div></div>
      </aside>
      <section className="auth-panel" aria-labelledby="auth-title">
        <div className="auth-form-wrap">
          <p className="auth-eyebrow">{isReset || isPasswordReset ? 'WELCOME BACK' : isLogin ? 'WELCOME HOME' : 'MAKE YOURSELF AT HOME'}</p>
          <h1 id="auth-title">{isPasswordReset ? 'Choose a new password' : isReset ? 'Forgot your password?' : isLogin ? 'Sign in to continue' : 'Find your place.'}</h1>
          <p className="auth-description">{isReset ? 'Enter your email to receive a reset link.' : isPasswordReset ? 'Use at least 8 characters for your new password.' : isLogin ? 'Sign in to your Land Discover account.' : 'Create your Land Discover account.'}</p>
          <form onSubmit={submit} className="auth-form" key={mode}>
            {isRegister && <><label htmlFor="auth-name">Full name</label><input id="auth-name" name="display_name" autoComplete="name" maxLength={120} placeholder="Your name" required disabled={pending} /></>}
            {!isPasswordReset && <><label htmlFor="auth-email">Email address</label><input id="auth-email" name="email" type="email" autoComplete="email" maxLength={254} placeholder="you@example.com" required disabled={pending} /></>}
            {!isReset && <><label htmlFor="auth-password">Password</label><input id="auth-password" name="password" type="password" autoComplete={isLogin ? 'current-password' : 'new-password'} minLength={isLogin ? undefined : 8} maxLength={128} placeholder={isLogin ? 'Your password' : 'At least 8 characters'} required disabled={pending} /></>}
            {(isRegister || isPasswordReset) && <><label htmlFor="auth-confirm">Confirm password</label><input id="auth-confirm" name="confirm_password" type="password" autoComplete="new-password" minLength={8} maxLength={128} required disabled={pending} /></>}
            {isLogin && <div className="auth-options"><label className="auth-remember"><input type="checkbox" name="remember" disabled={pending} />Remember me</label>{resetAvailable && <button type="button" onClick={() => changeMode('reset')} disabled={pending}>Forgot password?</button>}</div>}
            {notice && <p className={`auth-notice ${notice.error ? 'auth-error' : ''}`} role={notice.error ? 'alert' : 'status'}>{notice.text}</p>}
            <button className="auth-submit" type="submit" disabled={pending}>{pending ? 'Please wait...' : isPasswordReset ? 'Update password' : isReset ? 'Send reset link' : isLogin ? 'Sign in' : 'Create account'}<span aria-hidden="true">?</span></button>
          </form>
          {GOOGLE_URL && !isReset && !isPasswordReset && <button className="auth-google" type="button" disabled={pending} onClick={() => window.location.assign(GOOGLE_URL)}>Continue with Google</button>}
          <p className="auth-switch">{isLogin ? 'New to Land Discover? ' : 'Already have an account? '}<button type="button" disabled={pending} onClick={() => { if (isPasswordReset) window.history.replaceState(null, '', '/login'); changeMode(isLogin ? 'register' : 'login') }}>{isLogin ? 'Create an account' : 'Sign in'}</button></p>
          <p className="auth-footnote">A little closer to a place you can call your own.</p>
        </div>
      </section>
    </div>
  </main>
}
