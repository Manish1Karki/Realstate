'use client'
import { useEffect } from 'react'
import { SEARCH_COOKIE, resultsPath } from '@/lib/property-search'
export default function RememberSearch({ path }: { path: string }) {
  useEffect(() => { const safe=resultsPath(path); if(safe) document.cookie=SEARCH_COOKIE+'='+encodeURIComponent(safe)+'; Path=/; SameSite=Lax' },[path])
  return null
}
