import type { Metadata } from 'next'
import DashboardClient from './dashboard-client'

export const metadata: Metadata = { title: 'My account', robots: { index: false, follow: false } }

export default function DashboardPage() {
  return <main id="main" className="dashboard-wrap"><DashboardClient /></main>
}
