'use client'

import { useEffect, useState, type FormEvent } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { readRememberedSearch } from '@/lib/property-search'

type Props = { initialTransaction: string; initialType: string; initialDistrict?: string; initialQuery?: string; allowResume?: boolean }
export default function BrowseOptions({ initialTransaction, initialType, initialDistrict = '', initialQuery = '', allowResume = true }: Props) {
  const router = useRouter()
  const [transaction, setTransaction] = useState(initialTransaction === 'rent' ? 'rent' : 'sale')
  const [type, setType] = useState(initialType)
  const [district, setDistrict] = useState(initialDistrict)
  const [q, setQ] = useState(initialQuery)
  const [checked,setChecked] = useState(!allowResume)
  useEffect(() => {
    if (allowResume) { const saved=readRememberedSearch(); if(saved) { router.replace(saved); return } }
    setChecked(true)
  },[allowResume,router])
  function search(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!type) return
    const params = new URLSearchParams({ transaction, property_type: type })
    if (district) params.set('district', district)
    if (q.trim()) params.set('q', q.trim())
    router.push(`/properties?${params}`)
  }
  if (!checked) return <main id="main" className="wrap browse-options-page"><p role="status">Returning to your properties...</p></main>
  return <main id="main" className="wrap browse-options-page">
    <nav className="breadcrumbs" aria-label="Breadcrumb"><Link href="/">Home</Link><span>/</span><span>Properties</span></nav>
    <header className="browse-filter-heading"><div><p className="eyebrow">EXPLORE KATHMANDU VALLEY</p><h1>Find a place that fits.</h1><p>Set your filters to explore homes and land for sale or rent.</p></div><Link className="button secondary" href="/properties/new">List a property</Link></header>
    <form className="browse-filter-panel" onSubmit={search} aria-label="Property filters">
      <div className="browse-purpose" role="group" aria-label="Listing purpose">{[{value:'sale',label:'Buy'}, {value:'rent',label:'Rent'}].map(option => <button key={option.value} type="button" aria-pressed={transaction === option.value} onClick={() => setTransaction(option.value)}>{option.label}</button>)}</div>
      <div className="browse-filter-body">
        <fieldset className="browse-types"><legend>Property type</legend><div>{['house','land','apartment'].map(option => <label key={option} className="browse-type-chip"><input type="radio" name="property_type" value={option} checked={type === option} onChange={() => setType(option)} required /><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d={option === 'land' ? 'M3 16l9-11 9 11-9 5-9-5 M8 12l9 6' : option === 'house' ? 'M3 11l9-8 9 8 M5 10v11h14V10 M9 21v-8h6v8' : 'M5 21V3h14v18 M9 7h1 M14 7h1 M9 11h1 M14 11h1 M10 21v-6h4v6'} /></svg><span>{option.charAt(0).toUpperCase() + option.slice(1)}</span></label>)}</div></fieldset>
        <div className="browse-location-fields"><label>District<select value={district} onChange={event => setDistrict(event.target.value)}><option value="">All districts</option><option>Kathmandu</option><option>Lalitpur</option><option>Bhaktapur</option></select></label><label>Neighborhood or keyword<input type="search" value={q} maxLength={200} onChange={event => setQ(event.target.value)} placeholder="e.g. Bhaisepati, garden, family home" /></label></div>
      </div>
      <div className="browse-filter-actions"><div><p>Searching for <strong>{type ? type.charAt(0).toUpperCase() + type.slice(1) : 'a property'}</strong> for <strong>{transaction === 'rent' ? 'rent' : 'sale'}</strong>{district ? ` in ${district}` : ' across Kathmandu Valley'}.</p><button type="button" className="text-button" onClick={() => { setTransaction('sale'); setType(''); setDistrict(''); setQ('') }}>Reset filters</button></div><button className="button primary" type="submit" disabled={!type}>Show properties <span aria-hidden="true">&rarr;</span></button></div>
    </form>
    <p className="browse-filter-note">Choose a property type to start. You can adjust your filters on the results page.</p>
  </main>
}
