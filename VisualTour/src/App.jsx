import { useEffect, useRef, useState } from 'react'
import { createTourViewer } from './cesiumTour.js'
import { property } from './property.js'

const Icon = ({ children, size = 18 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{children}</svg>
)
const Pin = () => <Icon><path d="M20 10c0 5-8 11-8 11S4 15 4 10a8 8 0 1 1 16 0Z" /><circle cx="12" cy="10" r="2.4" /></Icon>
const Play = () => <Icon><path d="m8 5 11 7-11 7V5Z" /></Icon>
const Pause = () => <Icon><path d="M9 5v14M15 5v14" /></Icon>
const Layers = () => <Icon><path d="m12 3 9 5-9 5-9-5 9-5Z" /><path d="m3 13 9 5 9-5" /></Icon>
const Close = () => <Icon><path d="m6 6 12 12M18 6 6 18" /></Icon>

function App() {
  const mapElement = useRef(null)
  const creditElement = useRef(null)
  const tourApi = useRef(null)
  const runId = useRef(0)
  const mounted = useRef(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [activeScene, setActiveScene] = useState(0)
  const [playing, setPlaying] = useState(false)
  const [mapSource, setMapSource] = useState('satellite')
  const [selectedPoint, setSelectedPoint] = useState(null)
  const [detailsOpen, setDetailsOpen] = useState(true)

  useEffect(() => {
    let disposed = false
    mounted.current = true

    createTourViewer({
      container: mapElement.current,
      creditContainer: creditElement.current,
      property,
      onReady: () => !disposed && setLoading(false),
      onSourceChange: (source) => !disposed && setMapSource(source),
      onPointSelect: (point) => !disposed && setSelectedPoint(point),
    })
      .then((api) => {
        if (disposed) api.destroy()
        else tourApi.current = api
      })
      .catch(() => {
        if (!disposed) {
          setLoading(false)
          setError('The interactive terrain could not be loaded. Check the connection and try again.')
        }
      })

    return () => {
      disposed = true
      mounted.current = false
      runId.current += 1
      tourApi.current?.destroy()
      tourApi.current = null
    }
  }, [])

  function goToScene(index) {
    if (!tourApi.current) return
    runId.current += 1
    setPlaying(false)
    setActiveScene(index)
    setSelectedPoint(null)
    tourApi.current.flyToScene(property.scenes[index])
  }

  async function playTour() {
    if (!tourApi.current) return
    const currentRun = ++runId.current
    setPlaying(true)
    setSelectedPoint(null)

    for (let index = 0; index < property.scenes.length; index += 1) {
      if (runId.current !== currentRun || !mounted.current) return
      setActiveScene(index)
      await new Promise((resolve) => tourApi.current?.flyToScene(property.scenes[index], resolve))
      if (runId.current !== currentRun) return
      await new Promise((resolve) => window.setTimeout(resolve, index === property.scenes.length - 1 ? 600 : 1300))
    }

    if (runId.current === currentRun && mounted.current) setPlaying(false)
  }

  function stopTour() {
    runId.current += 1
    tourApi.current?.viewer.camera.cancelFlight()
    setPlaying(false)
  }

  async function changeMapSource(source) {
    if (!tourApi.current || source === mapSource) return
    try {
      await tourApi.current.setMapSource(source)
    } catch {
      setError('That map layer is temporarily unavailable. The current view has been kept.')
    }
  }

  return (
    <main className="tour-shell">
      <div ref={mapElement} className="map-canvas" aria-label="Interactive 3D map showing the property and its surroundings" />
      <div className="map-shade" aria-hidden="true" />

      <header className="topbar">
        <a className="brand" href="#tour" aria-label="Land Discover visual tour">
          <span className="brand-mark"><Pin /></span>
          <span>LAND<strong>DISCOVER</strong></span>
        </a>
        <div className="tour-status"><span className="status-dot" /> LIVE PROPERTY VIEW <small>· DEMO DATA</small></div>
        <button className="contact-button" type="button">Schedule a visit <span>↗</span></button>
      </header>

      <section className={`property-panel ${detailsOpen ? '' : 'is-collapsed'}`} aria-label="Property overview">
        <button className="panel-toggle" type="button" onClick={() => setDetailsOpen((open) => !open)} aria-label={detailsOpen ? 'Hide property details' : 'Show property details'}>
          {detailsOpen ? <Close /> : <Pin />}
        </button>
        <div className="property-content">
          <p className="eyebrow">{property.eyebrow}</p>
          <h1>{property.title}</h1>
          <p className="location"><Pin /> {property.address}</p>
          <div className="property-price"><span>ASKING PRICE</span><strong>{property.price}</strong></div>
          <dl className="facts">
            <div><dt>Plot area</dt><dd>{property.area}</dd></div>
            <div><dt>Road</dt><dd>{property.road}</dd></div>
            <div><dt>Orientation</dt><dd>{property.facing}</dd></div>
          </dl>
          <div className="boundary-note"><span>i</span><p><strong>Approximate boundary</strong>Verify dimensions and corners against the official survey before purchase.</p></div>
        </div>
      </section>

      <div className="map-tools" aria-label="Map style">
        <span><Layers /> MAP</span>
        <button className={mapSource === 'satellite' ? 'active' : ''} type="button" onClick={() => changeMapSource('satellite')}>Satellite</button>
        <button className={mapSource === 'streets' ? 'active' : ''} type="button" onClick={() => changeMapSource('streets')}>Streets</button>
      </div>

      {selectedPoint && (
        <aside className="poi-card">
          <button type="button" onClick={() => setSelectedPoint(null)} aria-label="Close point information"><Close /></button>
          <span>NEARBY CONTEXT</span>
          <strong>{selectedPoint.label}</strong>
          <p>{selectedPoint.detail}</p>
        </aside>
      )}

      <section className="tour-controls" id="tour" aria-label="Guided property tour">
        <button className={`play-button ${playing ? 'playing' : ''}`} type="button" onClick={playing ? stopTour : playTour} disabled={loading || Boolean(error)}>
          {playing ? <Pause /> : <Play />}
          <span>{playing ? 'Pause tour' : 'Play tour'}</span>
        </button>
        <div className="scene-track">
          {property.scenes.map((scene, index) => (
            <button className={activeScene === index ? 'active' : ''} type="button" key={scene.id} onClick={() => goToScene(index)} disabled={loading || Boolean(error)}>
              <span>{scene.number}</span>
              <span><strong>{scene.name}</strong><small>{scene.description}</small></span>
            </button>
          ))}
        </div>
      </section>

      <div ref={creditElement} className="map-credits" aria-label="Map data attribution" />

      {loading && (
        <div className="loading-screen" role="status">
          <div className="loading-orbit"><span /><i /></div>
          <p>Preparing the land view</p>
          <small>Loading terrain and satellite context…</small>
        </div>
      )}

      {error && (
        <div className="error-banner" role="alert">
          <strong>Map unavailable</strong>
          <span>{error}</span>
          <button type="button" onClick={() => window.location.reload()}>Try again</button>
        </div>
      )}
    </main>
  )
}

export default App
