import type { Metadata } from 'next'
import LoginForm from './login-form'

export const metadata: Metadata = { title: 'Sign in', robots: { index: false, follow: false } }
export default function LoginPage() { return <main id="main" className="auth-wrap"><LoginForm /></main> }
