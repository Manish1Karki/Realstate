import { useEffect, useRef, useState } from 'react'
import { createListingViewer, validListingPoint } from './listingLocation'
import './listingTour.css'
import { nearbyPlaces, placeColors, placeType } from './landmarks'

export default function ListingTour() {
  const params=new URLSearchParams(window.location.search)
  const id=params.get('listing')
  const mapOnly=params.get('mode')==='map'
  const canvas=useRef(null),credits=useRef(null),api=useRef(null),run=useRef(0)
  const [listing,setListing]=useState(null),[ready,setReady]=useState(false),[error,setError]=useState('')
  const [layer,setLayer]=useState('streets'),[view,setView]=useState(2),[playing,setPlaying]=useState(false)
  const [selected,setSelected]=useState(null),[query,setQuery]=useState(''),[category,setCategory]=useState('all')
  const places=nearbyPlaces(listing || {})
  const shown=places.filter(place=>(category==='all' || place.kind===category) && (place.name || placeType(place.kind)).toLowerCase().includes(query.toLowerCase()))
  useEffect(()=>{
    const controller=new AbortController()
    async function load() {
      if(!/^[0-9]+$/.test(id||'')) throw new Error('No valid listing was selected.')
      const response=await fetch('/api/properties/'+id+'?radius_m=2000',{signal:controller.signal,cache:'no-store'})
      if(!response.ok) throw new Error('This listing could not be loaded.')
      const property=await response.json()
      if(!validListingPoint(property)) throw new Error('No source-published map pin is available. No alternative location has been used.')
      setListing(property)
      const result=await createListingViewer({container:canvas.current,credits:credits.current,listing:property,signal:controller.signal,onLayer:setLayer,onPlace:setSelected,initialLayer:mapOnly?'streets':'satellite',orbitEnabled:!mapOnly})
      if(controller.signal.aborted){result.destroy();return}
      if(mapOnly) result.goTo(2,0)
      api.current=result;setReady(true)
      if(!mapOnly) {
        setPlaying(true)
        result.startOrbit(completed=>{if(!controller.signal.aborted){setPlaying(false);if(completed)setView(0)}})
      }
    }
    load().catch(cause=>{if(!controller.signal.aborted)setError(cause.message)})
    return ()=>{run.current++;controller.abort();api.current?.destroy();api.current=null}
  },[id,mapOnly])
  function move(index){run.current++;setPlaying(false);setView(index);api.current?.goTo(index)}
  function play(){
    if(!api.current)return
    if(playing){api.current.cancelOrbit();setPlaying(false);return}
    setPlaying(true)
    api.current.startOrbit(completed=>{setPlaying(false);if(completed)setView(0)})
  }
  async function changeLayer(name){try{await api.current?.setLayer(name);setError('')}catch{setError('That map layer is unavailable. The current location has been kept.')}}
  return <main className="listing-tour" data-ready={ready} data-latitude={listing?.lat} data-longitude={listing?.lng}>
    <div ref={canvas} className="listing-tour-canvas" aria-label="Visual tour of the listing location" />
    <div className="listing-tour-layers" role="group" aria-label="Map layers">{['satellite','streets'].map(name=><button key={name} disabled={!ready} aria-pressed={layer===name} onClick={()=>changeLayer(name)}>{name==='satellite'?'Satellite':'Map'}</button>)}<button disabled={!ready} onClick={()=>move(2)} aria-label="Recenter on property">Recenter</button></div>
    {!mapOnly && <div className="listing-tour-controls" role="group" aria-label="Camera views"><button disabled={!ready} onClick={play}>{playing?'Pause':'Play tour'}</button>{['Property','Neighborhood','Above'].map((name,index)=><button key={name} disabled={!ready} aria-pressed={view===index} onClick={()=>move(index)}>{name}</button>)}</div>}
    {ready && !mapOnly && <aside className="listing-nearby"><details open><summary>Nearby places <span>{places.length}</span></summary><div className="listing-nearby-body"><label>Find a place<input type="search" value={query} onChange={event=>setQuery(event.target.value)} placeholder="School, police station, shop..." /></label><label>Place type<select value={category} onChange={event=>setCategory(event.target.value)}><option value="all">All places</option>{[...new Set(places.map(place=>place.kind))].sort().map(kind=><option key={kind} value={kind}>{placeType(kind)}</option>)}</select></label><p className="listing-nearby-note">Within 2 km of the property. Distances are straight-line.{!listing.facilities_complete && ' Nearby data is incomplete.'}</p><ul>{shown.map(place=><li key={place.id}><button onClick={()=>{run.current++;setPlaying(false);api.current?.viewer.camera.cancelFlight();api.current?.focusPlace(place)}} aria-pressed={selected?.id===place.id}><i style={{background:placeColors[place.kind] || '#45636b'}} /><span>{place.name || placeType(place.kind)}<small>{placeType(place.kind)} ? {Math.round(place.distance_km*1000)} m</small></span></button></li>)}</ul>{!shown.length && <p>No matching mapped places available.</p>}</div></details></aside>}
    {selected && <div className="listing-place-card" role="status"><button aria-label="Dismiss place details" onClick={()=>setSelected(null)}>?</button><strong>{selected.name || placeType(selected.kind)}</strong><p>{placeType(selected.kind)} ? {Math.round(selected.distance_km*1000)} m from property</p></div>}
    <div ref={credits} className="listing-tour-credits" />
    {!ready&&!error&&<div className="listing-tour-loading" role="status">Loading the property location...</div>}
    {error&&<div className="listing-tour-error" role="alert">{error}<button onClick={()=>window.location.reload()}>Retry</button></div>}
  </main>
}
