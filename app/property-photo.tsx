'use client'

import { useState } from 'react'

export default function PropertyPhoto({ urls, alt, eager = false }: { urls: string[]; alt: string; eager?: boolean }) {
  const candidates = [...new Set(urls.filter(url => !/\/static\/|og-image|logo|placeholder/i.test(url)))]
  const [failed, setFailed] = useState<string[]>([])
  const photo = candidates.find(url => !failed.includes(url))
  return photo ? <img src={photo} alt={alt} loading={eager ? 'eager' : 'lazy'} fetchPriority={eager ? 'high' : 'auto'} referrerPolicy="no-referrer" onError={() => setFailed(previous => [...previous, photo])} /> : <span className="no-photo" role="img" aria-label="Property photo unavailable">Photo unavailable</span>
}
