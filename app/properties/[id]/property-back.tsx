'use client'
import Link from 'next/link'
import { useEffect, useState } from 'react'
import { readRememberedSearch, resultsPath } from '@/lib/property-search'
export default function PropertyBack({ returnTo }: { returnTo?: string }) {
  const [href,setHref]=useState(resultsPath(returnTo)||'/properties')
  useEffect(()=>{setHref(resultsPath(returnTo)||readRememberedSearch()||'/properties')},[returnTo])
  return <Link className="property-back" href={href}><span aria-hidden="true">&larr;</span>Back to properties</Link>
}
