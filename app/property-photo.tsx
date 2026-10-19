'use client'
import Image from 'next/image'
import { useState } from 'react'
import { optimizablePhoto } from '@/lib/property-images'

export default function PropertyPhoto({ urls, alt, eager = false, sizes = '(max-width: 640px) 100vw, (max-width: 900px) 50vw, 33vw' }: { urls: string[]; alt: string; eager?: boolean; sizes?: string }) {
  const candidates = [...new Set(urls.filter(url => /^https:\/\//.test(url) && !/\/static\/|og-image|logo|placeholder/i.test(url)))]
  const [direct, setDirect] = useState<string[]>([])
  const [failed, setFailed] = useState<string[]>([])
  const photo = candidates.find(url => !failed.includes(url))
  return photo ? <Image key={photo + (direct.includes(photo) ? '-direct' : '-optimized')} src={photo} alt={alt} fill sizes={sizes} unoptimized={!optimizablePhoto(photo) || direct.includes(photo)} loading={eager ? 'eager' : 'lazy'} fetchPriority={eager ? 'high' : 'auto'} referrerPolicy="no-referrer" onError={() => { if (optimizablePhoto(photo) && !direct.includes(photo)) setDirect(previous => [...previous, photo]); else setFailed(previous => [...previous, photo]) }} /> : <span className="no-photo" role="img" aria-label="Property photo unavailable">Photo unavailable</span>
}
