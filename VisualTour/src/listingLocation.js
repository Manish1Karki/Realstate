import * as Cesium from 'cesium'
import 'cesium/Build/Cesium/Widgets/widgets.css'

const TERRAIN = 'https://terrain.reearth.land/cesium-mesh/ellipsoid'
const IMAGERY = 'https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer'

export function validListingPoint(listing) {
  return Number.isFinite(listing?.lat) && Number.isFinite(listing?.lng)
    && listing.lat >= 27.5 && listing.lat <= 27.9 && listing.lng >= 85.15 && listing.lng <= 85.6
    && String(listing.geocode_precision || '').startsWith('source map pin')
}

export function validBoundary(value, lat, lng) {
  // Only accept an explicit source polygon containing the listing pin.
  if (value?.type !== 'Polygon' || value.coordinates?.length !== 1) return null
  const ring = value.coordinates[0]
  if (!Array.isArray(ring) || ring.length < 4 || ring.length > 200) return null
  if (ring.some(p => !Array.isArray(p) || p.length !== 2 || !p.every(Number.isFinite)
    || Math.abs(p[0]-lng) > 0.01 || Math.abs(p[1]-lat) > 0.01)) return null
  if (ring[0][0] !== ring.at(-1)[0] || ring[0][1] !== ring.at(-1)[1]) return null
  let inside = false
  for (let i=0,j=ring.length-1;i<ring.length;j=i++) {
    const [xi,yi]=ring[i], [xj,yj]=ring[j]
    if (((yi>lat)!==(yj>lat)) && (lng<(xj-xi)*(lat-yi)/(yj-yi)+xi)) inside=!inside
  }
  return inside ? ring : null
}

function deadline(promise, milliseconds) {
  let timer
  return Promise.race([promise, new Promise((_, reject) => { timer=setTimeout(()=>reject(new Error('Map data timed out')),milliseconds) })]).finally(()=>clearTimeout(timer))
}

export async function createListingViewer({ container, credits, listing, signal, onLayer }) {
  if (!validListingPoint(listing)) throw new Error('This listing has no source-published map pin. No substitute location has been used.')
  const viewer = new Cesium.Viewer(container, {
    animation:false, timeline:false, geocoder:false, homeButton:false, sceneModePicker:false,
    navigationHelpButton:false, fullscreenButton:false, baseLayerPicker:false, selectionIndicator:false,
    infoBox:false, baseLayer:false, creditContainer:credits, requestRenderMode:true,
    maximumRenderTimeChange:Infinity, msaaSamples:1,
  })
  const destroy=()=>{if (!viewer.isDestroyed()) viewer.destroy()}
  signal?.addEventListener('abort',destroy,{once:true})
  function check() { if(signal?.aborted || viewer.isDestroyed()) throw new Error('Tour closed') }
  try {
    viewer.scene.globe.depthTestAgainstTerrain=true
    viewer.scene.globe.baseColor=Cesium.Color.fromCssColorString('#dce5d5')
    viewer.scene.screenSpaceCameraController.minimumZoomDistance=30
    viewer.scene.screenSpaceCameraController.maximumZoomDistance=25000
    let elevation=null, terrainAvailable=false
    try {
      const terrain=await deadline(Cesium.CesiumTerrainProvider.fromUrl(TERRAIN),15000)
      check()
      const point=Cesium.Cartographic.fromDegrees(listing.lng,listing.lat)
      const [sample]=await deadline(Cesium.sampleTerrainMostDetailed(terrain,[point],true),20000)
      check()
      if (!Number.isFinite(sample.height)) throw new Error('Elevation unavailable')
      elevation=sample.height
      viewer.terrainProvider=terrain
      terrainAvailable=true
    } catch(error) { check(); viewer.terrainProvider=new Cesium.EllipsoidTerrainProvider() }

    // These coordinates are never replaced by demo values or camera offsets.
    const target=Cesium.Cartesian3.fromDegrees(listing.lng,listing.lat,elevation ?? 0)
    const pin=viewer.entities.add({
      id:'listing-'+listing.id,
      position:target,
      point:{pixelSize:12,color:Cesium.Color.fromCssColorString('#c44a29'),outlineColor:Cesium.Color.WHITE,outlineWidth:3,disableDepthTestDistance:Infinity},
      label:{text:'Property location',font:'13px sans-serif',showBackground:true,
        backgroundColor:Cesium.Color.fromCssColorString('#193e32').withAlpha(.9),
        fillColor:Cesium.Color.WHITE,pixelOffset:new Cesium.Cartesian2(0,-24),
        disableDepthTestDistance:Infinity},
    })
    const ring=listing.boundary_source_url === listing.source_url ? validBoundary(listing.boundary_geojson,listing.lat,listing.lng) : null
    if(ring) {
      const positions=Cesium.Cartesian3.fromDegreesArray(ring.flat())
      viewer.entities.add({id:'source-boundary',polygon:{hierarchy:positions,material:Cesium.Color.ORANGE.withAlpha(.15),classificationType:Cesium.ClassificationType.TERRAIN},
        polyline:{positions,width:3,material:Cesium.Color.ORANGE,clampToGround:true}})
    }
    let imagery=null
    async function setLayer(name) {
      check()
      const provider=name==='satellite'
        ? await deadline(Cesium.ArcGisMapServerImageryProvider.fromUrl(IMAGERY,{enablePickFeatures:false}),15000)
        : new Cesium.OpenStreetMapImageryProvider({url:'https://tile.openstreetmap.org/'})
      check()
      const next=viewer.imageryLayers.addImageryProvider(provider)
      if(imagery) viewer.imageryLayers.remove(imagery,true)
      imagery=next
      onLayer?.(name)
      viewer.scene.requestRender()
    }
    const views=[
      {name:'Property',range:450,pitch:-65,heading:0},
      {name:'Neighborhood',range:1800,pitch:-65,heading:0},
      {name:'Above',range:600,pitch:-90,heading:0},
    ]
    function goTo(index,duration=1.8,complete) {
      check()
      const view=views[index]
      viewer.camera.cancelFlight()
      viewer.camera.flyToBoundingSphere(new Cesium.BoundingSphere(target,1),{
        offset:new Cesium.HeadingPitchRange(Cesium.Math.toRadians(view.heading),Cesium.Math.toRadians(view.pitch),view.range),
        duration,complete,cancel:complete,
      })
    }
    // Opening and recentering are immediate and always use the exact pin.
    goTo(0,0)
    try { await setLayer('satellite') } catch(error) { check(); await setLayer('streets') }
    check()
    return {viewer,pin,target,elevation,terrainAvailable,boundary:ring,views,setLayer,goTo,
      destroy(){signal?.removeEventListener('abort',destroy);destroy()}}
  } catch(error) { signal?.removeEventListener('abort',destroy);destroy();throw error }
}
