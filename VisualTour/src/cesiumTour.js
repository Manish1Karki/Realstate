import * as Cesium from 'cesium'
import 'cesium/Build/Cesium/Widgets/widgets.css'

const ESRI_IMAGERY =
  'https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer'
const KEYLESS_TERRAIN = 'https://terrain.reearth.land/cesium-mesh/ellipsoid'
const OSM_IMAGERY = 'https://tile.openstreetmap.org/'

const toDegreesArray = (coordinates) => coordinates.flatMap(([lon, lat]) => [lon, lat])

export async function createTourViewer({ container, creditContainer, property, onReady, onSourceChange, onPointSelect }) {
  const viewer = new Cesium.Viewer(container, {
    animation: false,
    timeline: false,
    geocoder: false,
    homeButton: false,
    sceneModePicker: false,
    navigationHelpButton: false,
    fullscreenButton: false,
    baseLayerPicker: false,
    selectionIndicator: false,
    infoBox: false,
    baseLayer: false,
    creditContainer,
    requestRenderMode: true,
    maximumRenderTimeChange: Infinity,
    msaaSamples: 4,
  })

  viewer.scene.backgroundColor = Cesium.Color.fromCssColorString('#07110e')
  viewer.scene.globe.baseColor = Cesium.Color.fromCssColorString('#13251f')
  viewer.scene.globe.depthTestAgainstTerrain = true
  viewer.scene.screenSpaceCameraController.minimumZoomDistance = 35
  viewer.scene.screenSpaceCameraController.maximumZoomDistance = 35000
  viewer.scene.screenSpaceCameraController.enableCollisionDetection = true
  viewer.scene.fog.enabled = true
  viewer.scene.fog.density = 0.00012
  viewer.scene.skyAtmosphere.hueShift = -0.05
  viewer.scene.skyAtmosphere.saturationShift = -0.12
  viewer.scene.skyAtmosphere.brightnessShift = -0.08

  let source = 'satellite'
  let currentLayer = null

  async function setMapSource(nextSource) {
    const previousLayer = currentLayer
    let provider

    if (nextSource === 'streets') {
      provider = new Cesium.OpenStreetMapImageryProvider({
        url: OSM_IMAGERY,
        credit: '© OpenStreetMap contributors',
      })
    } else {
      provider = await Cesium.ArcGisMapServerImageryProvider.fromUrl(ESRI_IMAGERY, {
        credit: 'Powered by Esri — Esri, Maxar, Earthstar Geographics, and the GIS User Community',
        enablePickFeatures: false,
      })
    }

    currentLayer = viewer.imageryLayers.addImageryProvider(provider, 0)
    if (previousLayer) viewer.imageryLayers.remove(previousLayer, true)
    source = nextSource
    onSourceChange?.(source)
    viewer.scene.requestRender()
  }

  await setMapSource('satellite')

  try {
    viewer.terrainProvider = await Cesium.CesiumTerrainProvider.fromUrl(KEYLESS_TERRAIN, {
      requestVertexNormals: true,
    })
  } catch {
    viewer.terrainProvider = new Cesium.EllipsoidTerrainProvider()
  }

  const boundaryPositions = Cesium.Cartesian3.fromDegreesArray(toDegreesArray(property.boundary))
  viewer.entities.add({
    id: 'property-fill',
    polygon: {
      hierarchy: boundaryPositions,
      material: Cesium.Color.fromCssColorString('#ff6b35').withAlpha(0.28),
      classificationType: Cesium.ClassificationType.TERRAIN,
    },
  })
  viewer.entities.add({
    id: 'property-outline',
    polyline: {
      positions: boundaryPositions,
      width: 6,
      material: new Cesium.PolylineGlowMaterialProperty({
        glowPower: 0.22,
        color: Cesium.Color.fromCssColorString('#ff7849'),
      }),
      clampToGround: true,
    },
  })
  viewer.entities.add({
    id: 'property-label',
    position: Cesium.Cartesian3.fromDegrees(property.center.longitude, property.center.latitude),
    label: {
      text: 'FOR SALE  ·  6.1 AANA',
      font: '700 14px system-ui',
      fillColor: Cesium.Color.WHITE,
      outlineColor: Cesium.Color.BLACK,
      outlineWidth: 4,
      style: Cesium.LabelStyle.FILL_AND_OUTLINE,
      showBackground: true,
      backgroundColor: Cesium.Color.fromCssColorString('#0c1c17').withAlpha(0.88),
      backgroundPadding: new Cesium.Cartesian2(14, 9),
      pixelOffset: new Cesium.Cartesian2(0, -32),
      heightReference: Cesium.HeightReference.CLAMP_TO_GROUND,
      disableDepthTestDistance: Number.POSITIVE_INFINITY,
    },
    point: {
      pixelSize: 13,
      color: Cesium.Color.fromCssColorString('#ff7849'),
      outlineColor: Cesium.Color.WHITE,
      outlineWidth: 3,
      heightReference: Cesium.HeightReference.CLAMP_TO_GROUND,
      disableDepthTestDistance: Number.POSITIVE_INFINITY,
    },
  })

  viewer.entities.add({
    id: 'access-road-line',
    polyline: {
      positions: Cesium.Cartesian3.fromDegreesArray(toDegreesArray(property.accessRoad)),
      width: 8,
      material: new Cesium.PolylineDashMaterialProperty({
        color: Cesium.Color.fromCssColorString('#ffd36a'),
        dashLength: 18,
      }),
      clampToGround: true,
    },
  })

  for (const point of property.points) {
    viewer.entities.add({
      id: `poi-${point.id}`,
      position: Cesium.Cartesian3.fromDegrees(point.longitude, point.latitude),
      properties: { poiId: point.id },
      point: {
        pixelSize: 12,
        color: Cesium.Color.fromCssColorString(point.tone),
        outlineColor: Cesium.Color.fromCssColorString('#07110e'),
        outlineWidth: 3,
        heightReference: Cesium.HeightReference.CLAMP_TO_GROUND,
        disableDepthTestDistance: Number.POSITIVE_INFINITY,
      },
      label: {
        text: point.label,
        font: '600 13px system-ui',
        fillColor: Cesium.Color.WHITE,
        showBackground: true,
        backgroundColor: Cesium.Color.fromCssColorString('#07110e').withAlpha(0.76),
        backgroundPadding: new Cesium.Cartesian2(10, 7),
        pixelOffset: new Cesium.Cartesian2(0, -25),
        heightReference: Cesium.HeightReference.CLAMP_TO_GROUND,
        disableDepthTestDistance: Number.POSITIVE_INFINITY,
        distanceDisplayCondition: new Cesium.DistanceDisplayCondition(0, 4800),
      },
    })
  }

  const handler = new Cesium.ScreenSpaceEventHandler(viewer.scene.canvas)
  handler.setInputAction((event) => {
    const picked = viewer.scene.pick(event.position)
    const poiId = picked?.id?.properties?.poiId?.getValue?.()
    if (!poiId) return
    const match = property.points.find((point) => point.id === poiId)
    if (match) onPointSelect?.(match)
  }, Cesium.ScreenSpaceEventType.LEFT_CLICK)

  function flyToScene(scene, complete) {
    const longitude = property.center.longitude + (scene.offsetLongitude ?? 0)
    const latitude = property.center.latitude + (scene.offsetLatitude ?? 0)
    const target = Cesium.Cartesian3.fromDegrees(longitude, latitude, property.elevation)
    viewer.camera.flyToBoundingSphere(new Cesium.BoundingSphere(target, 1), {
      offset: new Cesium.HeadingPitchRange(
        Cesium.Math.toRadians(scene.heading),
        Cesium.Math.toRadians(scene.pitch),
        scene.height,
      ),
      duration: scene.duration,
      easingFunction: Cesium.EasingFunction.QUADRATIC_IN_OUT,
      complete,
      cancel: complete,
    })
  }

  function reset() {
    viewer.camera.cancelFlight()
    flyToScene(property.scenes[0])
  }

  onReady?.()
  flyToScene(property.scenes[0])

  return {
    viewer,
    flyToScene,
    setMapSource,
    getMapSource: () => source,
    reset,
    destroy() {
      handler.destroy()
      if (!viewer.isDestroyed()) viewer.destroy()
    },
  }
}
