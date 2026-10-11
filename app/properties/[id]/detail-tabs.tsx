'use client'

import { useState, type ReactNode, type KeyboardEvent } from 'react'

export default function DetailTabs({ overview, location }: { overview: ReactNode; location: ReactNode }) {
  const [active, setActive] = useState('overview')
  function navigate(event: KeyboardEvent<HTMLButtonElement>) {
    if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return
    event.preventDefault()
    const next = event.key === 'Home' ? 'overview' : event.key === 'End' ? 'location' : active === 'overview' ? 'location' : 'overview'
    setActive(next)
    document.getElementById('detail-tab-' + next)?.focus()
  }
  return <div className="property-tabs">
    <div className="property-tab-list" role="tablist" aria-label="Property information">
      {['overview', 'location'].map(tab => <button key={tab} type="button" role="tab" id={'detail-tab-' + tab} aria-controls={'detail-panel-' + tab} aria-selected={active === tab} tabIndex={active === tab ? 0 : -1} onClick={() => setActive(tab)} onKeyDown={navigate}>{tab === 'overview' ? 'Overview' : 'Location'}</button>)}
    </div>
    <section id="detail-panel-overview" role="tabpanel" aria-labelledby="detail-tab-overview" hidden={active !== 'overview'}>{overview}</section>
    <section id="detail-panel-location" role="tabpanel" aria-labelledby="detail-tab-location" hidden={active !== 'location'}>{location}</section>
  </div>
}
