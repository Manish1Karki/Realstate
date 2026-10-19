import * as Cesium from 'cesium'
import { nearbyPlaces, placeColors, placeType } from './landmarks'
import 'cesium/Build/Cesium/Widgets/widgets.css'

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

export async function createListingViewer({ container, credits, listing, signal, onLayer, onPlace, initialLayer='satellite', orbitEnabled=true }) {
  if (!validListingPoint(listing)) throw new Error('This listing has no source-published map pin. No substitute location has been used.')
  const radiusKm=5
  const latDelta=radiusKm/111.32
  const lngDelta=radiusKm/(111.32*Math.cos(Cesium.Math.toRadians(listing.lat)))
  const localArea=Cesium.Rectangle.fromDegrees(listing.lng-lngDelta,listing.lat-latDelta,listing.lng+lngDelta,listing.lat+latDelta)
  const viewer = new Cesium.Viewer(container, {
    sceneMode:orbitEnabled?Cesium.SceneMode.SCENE3D:Cesium.SceneMode.SCENE2D, mapMode2D:Cesium.MapMode2D.ROTATE, animation:false, timeline:false, geocoder:false, homeButton:false, sceneModePicker:false,
    navigationHelpButton:false, fullscreenButton:false, baseLayerPicker:false, selectionIndicator:false,
    infoBox:false, baseLayer:false, creditContainer:credits, requestRenderMode:true,
    maximumRenderTimeChange:Infinity, msaaSamples:1, skyBox:false, skyAtmosphere:false,
  })
  // Render at up to two physical pixels per CSS pixel, without multiplying DPR twice.
  viewer.useBrowserRecommendedResolution=true
  viewer.resolutionScale=Math.min(2,Math.max(1,window.devicePixelRatio || 1))
  viewer.scene.globe.maximumScreenSpaceError=1
  // Limit camera movement, not rendered coverage: clipping the globe leaves black
  // bands when the viewport extends beyond the local rectangle.
  viewer.scene.backgroundColor=Cesium.Color.fromCssColorString('#e0eee9')
  viewer.scene.globe.tileCacheSize=128
  viewer.scene.screenSpaceCameraController.enableRotate=orbitEnabled
  viewer.scene.screenSpaceCameraController.enableTilt=false
  viewer.scene.postProcessStages.fxaa.enabled=false
  let orbitFrame=0,orbitFinished=null
  function cancelOrbit() {
    if(!orbitFinished)return
    cancelAnimationFrame(orbitFrame)
    const finished=orbitFinished;orbitFinished=null
    if(!viewer.isDestroyed())viewer.camera.lookAtTransform(Cesium.Matrix4.IDENTITY)
    finished(false)
  }
  const destroy=()=>{cancelOrbit();if (!viewer.isDestroyed()) viewer.destroy()}
  signal?.addEventListener('abort',destroy,{once:true})
  function check() { if(signal?.aborted || viewer.isDestroyed()) throw new Error('Tour closed') }
  try {
    viewer.scene.globe.depthTestAgainstTerrain=true
    viewer.scene.globe.baseColor=Cesium.Color.fromCssColorString('#dce5d5')
    viewer.scene.globe.enableLighting=false
    viewer.scene.globe.showGroundAtmosphere=false
    viewer.scene.globe.tileLoadProgressEvent.addEventListener(()=>viewer.scene.requestRender())
    viewer.scene.screenSpaceCameraController.minimumZoomDistance=30
    viewer.scene.screenSpaceCameraController.maximumZoomDistance=6000
    const elevation=null, terrainAvailable=false
    viewer.terrainProvider=new Cesium.EllipsoidTerrainProvider()
    let correcting=false
    viewer.camera.moveEnd.addEventListener(()=>{
      if(correcting || viewer.isDestroyed())return
      const center=viewer.camera.positionCartographic
      const lat=Cesium.Math.clamp(center.latitude,localArea.south,localArea.north)
      const lng=Cesium.Math.clamp(center.longitude,localArea.west,localArea.east)
      const height=Cesium.Math.clamp(center.height,100,6000)
      if(lat!==center.latitude || lng!==center.longitude || height!==center.height){
        correcting=true
        viewer.camera.setView({destination:Cesium.Cartesian3.fromRadians(lng,lat,height)})
        correcting=false
      }
    })

    // These coordinates are never replaced by demo values or camera offsets.
    const target=Cesium.Cartesian3.fromDegrees(listing.lng,listing.lat,elevation ?? 0)
    const pin=viewer.entities.add({
      id:'listing-'+listing.id,
      position:target,
      point:{pixelSize:12,color:Cesium.Color.fromCssColorString('#c44a29'),outlineColor:Cesium.Color.WHITE,outlineWidth:3,disableDepthTestDistance:Infinity},
      label:{text:'Property location',font:'bold 14px sans-serif',showBackground:false,style:Cesium.LabelStyle.FILL_AND_OUTLINE,outlineColor:Cesium.Color.fromCssColorString('#193e32'),outlineWidth:3,
        fillColor:Cesium.Color.WHITE,pixelOffset:new Cesium.Cartesian2(0,-24),
        disableDepthTestDistance:Infinity},
    })
    const places=nearbyPlaces(listing)
    const placeEntities=new Map()
    places.forEach((place,index)=>{
      const entity=viewer.entities.add({
        id:'landmark-'+place.id,
        position:Cesium.Cartesian3.fromDegrees(place.lng,place.lat),
        point:{pixelSize:9,color:Cesium.Color.fromCssColorString(placeColors[place.kind] || '#45636b'),outlineColor:Cesium.Color.WHITE,outlineWidth:2,heightReference:Cesium.HeightReference.CLAMP_TO_GROUND,disableDepthTestDistance:Infinity},
        label:{text:place.name || placeType(place.kind),show:false,font:'13px sans-serif',fillColor:Cesium.Color.WHITE,outlineColor:Cesium.Color.fromCssColorString('#193e32'),outlineWidth:2,style:Cesium.LabelStyle.FILL_AND_OUTLINE,showBackground:false,pixelOffset:new Cesium.Cartesian2(12,-12),horizontalOrigin:Cesium.HorizontalOrigin.LEFT,heightReference:Cesium.HeightReference.CLAMP_TO_GROUND,disableDepthTestDistance:Infinity},
      })
      placeEntities.set(String(place.id),entity)
    })
    let selectedId=null,hoveredId=null
    function choosePlace(place) { selectedId=place ? String(place.id) : null; onPlace?.(place || null); viewer.scene.requestRender() }
    // Show only names that fit, preserving space around the property marker.
    viewer.scene.postRender.addEventListener(()=>{
      const time=viewer.clock.currentTime
      const origin=Cesium.SceneTransforms.worldToWindowCoordinates(viewer.scene,target)
      const boxes=origin ? [{x:origin.x-90,y:origin.y-50,w:180,h:65}] : []
      const overlaps=box=>boxes.some(other=>box.x<other.x+other.w && box.x+box.w>other.x && box.y<other.y+other.h && box.y+box.h>other.y)
      let count=0
      const ordered=[...places].sort((a,b)=>Number(String(b.id)===selectedId || String(b.id)===hoveredId)-Number(String(a.id)===selectedId || String(a.id)===hoveredId))
      for(const place of ordered){
        const entity=placeEntities.get(String(place.id))
        const point=Cesium.SceneTransforms.worldToWindowCoordinates(viewer.scene,entity.position.getValue(time))
        const priority=String(place.id)===selectedId || String(place.id)===hoveredId
        const named=place.name && !/^unnamed/i.test(place.name)
        const box=point ? {x:point.x+12,y:point.y-25,w:Math.min(300,(place.name || '').length*7)+16,h:30} : null
        const visible=Boolean(box && box.x>=0 && box.y>=0 && box.x+box.w<viewer.canvas.clientWidth && box.y+box.h<viewer.canvas.clientHeight && (priority || (named && count<6 && !overlaps(box))))
        if(visible){boxes.push(box);count++}
        if(entity.label.show.getValue(time)!==visible)entity.label.show=visible
      }
    })
    viewer.screenSpaceEventHandler.setInputAction(event=>{
      const picked=viewer.scene.pick(event.endPosition)
      const place=places.find(place=>picked?.id===placeEntities.get(String(place.id)))
      const next=place ? String(place.id) : null
      if(next!==hoveredId){hoveredId=next;viewer.scene.requestRender()}
    },Cesium.ScreenSpaceEventType.MOUSE_MOVE)
    viewer.screenSpaceEventHandler.setInputAction(event=>{
      const picked=viewer.scene.pick(event.position)
      const place=places.find(place=>picked?.id===placeEntities.get(String(place.id)))
      choosePlace(place)
    },Cesium.ScreenSpaceEventType.LEFT_CLICK)
    function focusPlace(place) {
      check()
      cancelOrbit()
      const entity=placeEntities.get(String(place.id))
      if(!entity)return
      choosePlace(place)
      viewer.camera.flyToBoundingSphere(new Cesium.BoundingSphere(Cesium.Cartesian3.fromDegrees(place.lng,place.lat,elevation ?? 0),1),{offset:new Cesium.HeadingPitchRange(0,-Math.PI/2,700),duration:window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 0 : 1})
    }
    const ring=listing.boundary_source_url === listing.source_url ? validBoundary(listing.boundary_geojson,listing.lat,listing.lng) : null
    if(ring) {
      const positions=Cesium.Cartesian3.fromDegreesArray(ring.flat())
      viewer.entities.add({id:'source-boundary',polygon:{hierarchy:positions,material:Cesium.Color.ORANGE.withAlpha(.15),classificationType:Cesium.ClassificationType.TERRAIN},
        polyline:{positions,width:3,material:Cesium.Color.ORANGE,clampToGround:true}})
    }
    // Keep a complete street-map layer under satellite tiles while they load.
    viewer.imageryLayers.addImageryProvider(new Cesium.OpenStreetMapImageryProvider({url:'https://tile.openstreetmap.org/'}))
    let imagery=null
    async function setLayer(name) {
      check()
      const provider=name==='satellite'
        ? await deadline(Cesium.ArcGisMapServerImageryProvider.fromUrl(IMAGERY,{enablePickFeatures:false}),15000)
        : new Cesium.OpenStreetMapImageryProvider({url:'https://tile.openstreetmap.org/'})
      check()
      const next=viewer.imageryLayers.add(new Cesium.ImageryLayer(provider))
      if(imagery) viewer.imageryLayers.remove(imagery,true)
      imagery=next
      onLayer?.(name)
      viewer.scene.requestRender()
    }
    const views=[
      {name:'Property',range:500,pitch:-90,heading:0},
      {name:'Neighborhood',range:2400,pitch:-90,heading:0},
      {name:'Above',range:1600,pitch:-90,heading:0},
    ]
    function goTo(index,duration=1.8,complete) {
      check()
      cancelOrbit()
      const view=views[index]
      viewer.camera.cancelFlight()
      viewer.camera.flyToBoundingSphere(new Cesium.BoundingSphere(target,1),{
        offset:new Cesium.HeadingPitchRange(Cesium.Math.toRadians(view.heading),Cesium.Math.toRadians(view.pitch),view.range),
        duration,complete,cancel:complete,
      })
    }
    function startOrbit(onFinish=()=>{}) {
      check();cancelOrbit();viewer.camera.cancelFlight()
      if(!orbitEnabled || window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
        goTo(0,0);onFinish(true);return
      }
      orbitFinished=onFinish
      const started=performance.now()
      function frame(time) {
        if(!orbitFinished || signal?.aborted || viewer.isDestroyed())return
        const progress=Math.min(1,(time-started)/4000)
        const eased=progress*progress*(3-2*progress)
        // A short, gentle arc with modest zoom avoids a full spinning descent.
        const range=1000+(700-1000)*eased
        const heading=Cesium.Math.toRadians(-10+20*eased)
        const pitch=Cesium.Math.toRadians(-65)
        viewer.camera.lookAt(target,new Cesium.HeadingPitchRange(heading,pitch,range))
        viewer.scene.requestRender()
        if(progress<1)orbitFrame=requestAnimationFrame(frame)
        else {
          const finished=orbitFinished;orbitFinished=null
          viewer.camera.lookAtTransform(Cesium.Matrix4.IDENTITY)
          finished(true)
        }
      }
      orbitFrame=requestAnimationFrame(frame)
    }
    for(const type of [Cesium.ScreenSpaceEventType.LEFT_DOWN,Cesium.ScreenSpaceEventType.WHEEL,Cesium.ScreenSpaceEventType.PINCH_START]) {
      viewer.screenSpaceEventHandler.setInputAction(cancelOrbit,type)
    }
    // Start in the same pose as the gentle introduction, without a camera snap.
    if(orbitEnabled && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      viewer.camera.lookAt(target,new Cesium.HeadingPitchRange(Cesium.Math.toRadians(-10),Cesium.Math.toRadians(-65),1000))
      viewer.camera.lookAtTransform(Cesium.Matrix4.IDENTITY)
    } else goTo(orbitEnabled?0:2,0)
    try { await setLayer(initialLayer) }
    catch(error) {
      check()
      if(initialLayer==='streets') throw error
      await setLayer('streets')
    }
    check()
    return {viewer,pin,target,elevation,terrainAvailable,boundary:ring,views,setLayer,goTo,focusPlace,startOrbit,cancelOrbit,
      destroy(){signal?.removeEventListener('abort',destroy);destroy()}}
  } catch(error) { signal?.removeEventListener('abort',destroy);destroy();throw error }
}
