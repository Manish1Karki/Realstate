import { useEffect, useRef, useState } from 'react'
import { createListingViewer, validListingPoint } from './listingLocation'
import './listingTour.css'

export default function ListingTour() {
  const params=new URLSearchParams(window.location.search)
  const id=params.get('listing')
  const canvas=useRef(null),credits=useRef(null),api=useRef(null),run=useRef(0)
  const [listing,setListing]=useState(null),[ready,setReady]=useState(false),[error,setError]=useState('')
  const [layer,setLayer]=useState('satellite'),[view,setView]=useState(0),[playing,setPlaying]=useState(false)
  const [elevation,setElevation]=useState(null),[hasBoundary,setHasBoundary]=useState(false)
  useEffect(()=>{
    const controller=new AbortController()
    async function load() {
      if(!/^[0-9]+$/.test(id||'')) throw new Error('No valid listing was selected.')
      const response=await fetch('/api/properties/'+id,{signal:controller.signal,cache:'no-store'})
      if(!response.ok) throw new Error('This listing could not be loaded.')
      const property=await response.json()
      if(!validListingPoint(property)) throw new Error('No source-published map pin is available. No alternative location has been used.')
      setListing(property)
      const result=await createListingViewer({container:canvas.current,credits:credits.current,listing:property,signal:controller.signal,onLayer:setLayer})
      if(controller.signal.aborted){result.destroy();return}
      api.current=result;setElevation(result.elevation);setHasBoundary(Boolean(result.boundary));setReady(true)
    }
    load().catch(cause=>{if(!controller.signal.aborted)setError(cause.message)})
    return ()=>{run.current++;controller.abort();api.current?.destroy();api.current=null}
  },[id])
  function move(index){run.current++;setPlaying(false);setView(index);api.current?.goTo(index)}
  async function play(){
    if(!api.current)return
    if(playing){run.current++;api.current.viewer.camera.cancelFlight();setPlaying(false);return}
    const token=++run.current;setPlaying(true)
    for(const index of [1,2,0]){
      if(run.current!==token||!api.current)return
      setView(index)
      await new Promise(resolve=>api.current.goTo(index,2.2,resolve))
    }
    if(run.current===token)setPlaying(false)
  }
  async function changeLayer(name){try{await api.current?.setLayer(name);setError('')}catch{setError('That map layer is unavailable. The current location has been kept.')}}
  return <main className="listing-tour" data-ready={ready} data-latitude={listing?.lat} data-longitude={listing?.lng} data-elevation={elevation ?? ''} data-boundary={hasBoundary}>
    <div ref={canvas} className="listing-tour-canvas" aria-label="Visual tour of the listing location" />
    <div className="listing-tour-layers" role="group" aria-label="Map layers">{['satellite','streets'].map(name=><button key={name} disabled={!ready} aria-pressed={layer===name} onClick={()=>changeLayer(name)}>{name==='satellite'?'Satellite':'Streets'}</button>)}<button disabled={!ready} onClick={()=>move(0)} aria-label="Recenter on property">Recenter</button></div>
    <div className="listing-tour-controls" role="group" aria-label="Camera views"><button disabled={!ready} onClick={play}>{playing?'Pause':'Play tour'}</button>{['Property','Neighborhood','Above'].map((name,index)=><button key={name} disabled={!ready} aria-pressed={view===index} onClick={()=>move(index)}>{name}</button>)}</div>
    <div ref={credits} className="listing-tour-credits" />
    {!ready&&!error&&<div className="listing-tour-loading" role="status">Loading the property location...</div>}
    {error&&<div className="listing-tour-error" role="alert">{error}<button onClick={()=>window.location.reload()}>Retry</button></div>}
    {ready&&<details className="listing-tour-accuracy"><summary>Location details</summary><div><p>Latitude: {listing.lat}</p><p>Longitude: {listing.lng}</p><p>{elevation==null?'Elevation unavailable; flat map.':'Terrain elevation (estimate): '+elevation.toFixed(1)+' m above WGS84 ellipsoid.'}</p><p>{hasBoundary?'Boundary supplied by the listing source; not independently surveyed.':'No surveyed plot boundary provided.'}</p></div></details>}
  </main>
}
