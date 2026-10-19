'use client'
export default function PropertyError({ reset }: { reset: () => void }) {
  return <main id="main" className="wrap not-found"><h1>Properties are temporarily unavailable</h1><p>The listing service may be waking up. Please try again shortly.</p><button className="button primary" onClick={reset}>Try again</button></main>
}
