'use client'

import { useEffect, useState } from 'react'

export default function SaveProperty({ id, title, detailed = false }: { id: number; title: string; detailed?: boolean }) {
  const [saved, setSaved] = useState(false)
  useEffect(() => {
    try { const ids = JSON.parse(localStorage.getItem('land-discover-saved') || '[]'); setSaved(Array.isArray(ids) && ids.includes(id)) } catch { }
  }, [id])
  function toggle() {
    let ids: number[] = []
    try { const value = JSON.parse(localStorage.getItem('land-discover-saved') || '[]'); if (Array.isArray(value)) ids = value.filter(Number.isInteger) } catch { }
    const next = ids.includes(id) ? ids.filter(value => value !== id) : [...ids, id]
    try { localStorage.setItem('land-discover-saved', JSON.stringify(next)); setSaved(next.includes(id)) } catch { setSaved(false) }
  }
  return <button className={`save-property${saved ? ' is-saved' : ''}`} type="button" onClick={toggle} aria-pressed={saved} aria-label={`${saved ? 'Remove' : 'Save'} ${title}`}><svg width="19" height="19" viewBox="0 0 24 24" fill={saved ? 'currentColor' : 'none'} stroke="currentColor" strokeWidth="1.5" aria-hidden="true"><path d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.7l-1.1-1.1a5.5 5.5 0 0 0-7.8 7.8L12 21l8.8-8.6a5.5 5.5 0 0 0 0-7.8Z" /></svg><span>{saved ? 'Saved' : detailed ? 'Save property' : 'Save'}</span></button>
}
