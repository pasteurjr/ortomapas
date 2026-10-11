<template>
  <div class="map-container" :class="{ 'profile-open': mapStore.profileOpen }" ref="mapContainer">
    <l-map
      ref="leafletMap"
      :key="projectStore.activeProject?.id || 'sem-projeto'"
      v-model:zoom="currentZoom"
      v-model:center="currentCenter"
      :useGlobalLeaflet="true"
      @ready="onMapReady"
      @mousemove="onMouseMove"
      @click="onMapClick"
      @update:zoom="onZoomUpdate"
    >
      <!-- Base Layers -->
      <l-tile-layer
        v-if="mapStore.basemap === 'osm'"
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution="&copy; OpenStreetMap contributors"
        :maxZoom="19"
        layerType="base"
      />
      <l-tile-layer
        v-if="mapStore.basemap === 'satellite'"
        url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
        attribution="&copy; Esri"
        :maxZoom="19"
        layerType="base"
      />

      <!-- Ortomapa Tile Layers -->
      <OrtomapaTiles
        v-for="layer in visibleOrtoLayers"
        :key="'orto-' + layer.id"
        :sourceId="layer.sourceId"
        :opacity="layer.opacity"
      />

      <!-- Analysis Result Layers (GeoJSON) -->
      <l-geo-json
        v-for="layer in visibleAnalysisLayers"
        :key="'analysis-' + layer.id"
        :geojson="layer.geojson"
        :optionsStyle="getAnalysisStyle(layer)"
      />

      <!-- Anotacoes GeoJSON -->
      <l-geo-json
        v-if="anotacoesGeoJSON && anotacoesGeoJSON.features.length > 0"
        :geojson="anotacoesGeoJSON"
        :optionsStyle="anotacaoStyle"
        :onEachFeature="onEachAnotacao"
      />

      <!-- Measurement overlay -->
      <l-polyline
        v-if="measurePoints.length > 1 && mapStore.measureMode === 'distance'"
        :latLngs="measurePoints"
        :color="'#f59e0b'"
        :weight="3"
        :dashArray="'8,6'"
      />
      <l-polygon
        v-if="measurePoints.length > 2 && mapStore.measureMode === 'area'"
        :latLngs="measurePoints"
        :color="'#f59e0b'"
        :fillColor="'#f59e0b'"
        :fillOpacity="0.2"
        :weight="2"
      />
      <l-circle-marker
        v-for="(pt, idx) in measurePoints"
        :key="'measure-' + idx"
        :latLng="pt"
        :radius="4"
        :color="'#f59e0b'"
        :fillColor="'#fff'"
        :fillOpacity="1"
      />

      <l-control-scale position="bottomleft" :imperial="false" />
    </l-map>
    <ElevationProfile v-if="mapStore.profileOpen" />

    <!-- Basemap Switcher -->
    <div class="basemap-switcher">
      <button
        :class="{ active: mapStore.basemap === 'osm' }"
        @click="mapStore.basemap = 'osm'"
        title="OpenStreetMap"
      >
        <i class="pi pi-map"></i>
      </button>
      <button
        :class="{ active: mapStore.basemap === 'satellite' }"
        @click="mapStore.basemap = 'satellite'"
        title="Satellite"
      >
        <i class="pi pi-globe"></i>
      </button>
    </div>

    <!-- Layer opacity quick controls -->
    <div class="layer-controls" v-if="mapStore.visibleLayers.length > 0">
      <div
        v-for="layer in mapStore.visibleLayers"
        :key="layer.id"
        class="layer-control-item"
      >
        <div class="layer-control-header"><span class="layer-name">{{ layer.name }}</span><button v-if="layer.type === 'analysis'" type="button" title="Baixar GeoJSON" @click="exportLayer(layer, 'geojson')"><i class="pi pi-download"></i></button><button v-if="layer.type === 'analysis'" type="button" title="Baixar KML" @click="exportLayer(layer, 'kml')"><i class="pi pi-map-marker"></i></button><button type="button" title="Remover camada" @click="mapStore.removeLayer(layer.id)"><i class="pi pi-times"></i></button></div>
        <input
          type="range"
          min="0"
          max="1"
          step="0.05"
          :value="layer.opacity"
          @input="mapStore.setLayerOpacity(layer.id, parseFloat($event.target.value))"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import L from 'leaflet'
import OrtomapaTiles from './OrtomapaTiles.vue'
import ElevationProfile from './ElevationProfile.vue'
import 'leaflet-draw'
import 'leaflet-draw/dist/leaflet.draw.css'
// Leaflet Draw and Vue layers must share one Leaflet instance and renderer types.
window.L = L
import { useMapStore } from '../stores/mapStore'
import { useProjectStore } from '../stores/projectStore'
import {
  LMap,
  LTileLayer,
  LGeoJson,
  LPolyline,
  LPolygon,
  LCircleMarker,
  LControlScale,
} from '@vue-leaflet/vue-leaflet'

const mapStore = useMapStore()
const projectStore = useProjectStore()
const leafletMap = ref(null)
const mapContainer = ref(null)

const currentZoom = ref(mapStore.zoom)
const currentCenter = ref(mapStore.center)
const measurePoints = ref([])
let resizeObserver
let resizeFrame

const visibleOrtoLayers = computed(() =>
  mapStore.activeLayers.filter((l) => l.type === 'ortomapa' && l.visible)
)

const visibleAnalysisLayers = computed(() =>
  mapStore.activeLayers.filter(
    (l) => l.type === 'analysis' && l.visible && l.geojson
  )
)

const anotacoesGeoJSON = computed(() => {
  const features = projectStore.anotacoes
    .filter((a) => a.geometria)
    .map((a) => ({
      type: 'Feature',
      properties: {
        id: a.id,
        categoria: a.categoria,
        rotulo: a.rotulo,
        descricao: a.descricao,
      },
      geometry: a.geometria,
    }))
  return { type: 'FeatureCollection', features }
})

const categoriaColors = {
  vegetacao: '#22c55e',
  construcao: '#ef4444',
  agua: '#3b82f6',
  solo: '#a16207',
  erosao: '#f97316',
  infraestrutura: '#8b5cf6',
  default: '#6b7280',
}

function anotacaoStyle(feature) {
  const cat = feature.properties?.categoria || 'default'
  const color = categoriaColors[cat] || categoriaColors.default
  return {
    color,
    weight: 2,
    fillColor: color,
    fillOpacity: 0.25,
  }
}

function onEachAnotacao(feature, layer) {
  if (feature.properties) {
    const { rotulo, categoria, descricao } = feature.properties
    const popup = `
      <div style="min-width:150px">
        <strong>${rotulo || 'Sem rotulo'}</strong><br/>
        <em>${categoria || ''}</em><br/>
        ${descricao || ''}
      </div>
    `
    layer.bindPopup(popup)
  }
}

function getAnalysisStyle(layer) {
  return function (feature) {
    const classValue = feature.properties?.class || feature.properties?.value || 0
    const colors = ['#22c55e', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899']
    return {
      color: colors[classValue % colors.length],
      weight: 1,
      fillColor: colors[classValue % colors.length],
      fillOpacity: 0.5,
    }
  }
}

function onMouseMove(event) {
  if (event.latlng) {
    mapStore.setCursorCoords(event.latlng.lat, event.latlng.lng)
  }
}

function onMapClick(event) {
  if (event.latlng) {
    // Handle pour point capture for hydrology
    mapStore.handleMapClick(event.latlng.lat, event.latlng.lng)
  }
  if (mapStore.measureMode && event.latlng) {
    measurePoints.value.push([event.latlng.lat, event.latlng.lng])
  }
}

function onZoomUpdate(zoom) {
  mapStore.zoom = zoom
}

function escapeXml(value) { return String(value).replace(/[<>&'\"]/g, (char) => ({ '<': '&lt;', '>': '&gt;', '&': '&amp;', "'": '&apos;', '"': '&quot;' }[char])) }
function geometryToKml(geometry) {
  const coords = (points) => points.map(([x, y]) => `${x},${y},0`).join(' ')
  const make = (geom) => {
    if (!geom) return ''
    if (geom.type === 'Point') return `<Point><coordinates>${coords([geom.coordinates])}</coordinates></Point>`
    if (geom.type === 'LineString') return `<LineString><coordinates>${coords(geom.coordinates)}</coordinates></LineString>`
    if (geom.type === 'Polygon') return `<Polygon><outerBoundaryIs><LinearRing><coordinates>${coords(geom.coordinates[0])}</coordinates></LinearRing></outerBoundaryIs></Polygon>`
    if (geom.type === 'MultiPolygon') return geom.coordinates.map((polygon) => make({ type: 'Polygon', coordinates: polygon })).join('')
    if (geom.type === 'MultiLineString') return geom.coordinates.map((line) => make({ type: 'LineString', coordinates: line })).join('')
    if (geom.type === 'MultiPoint') return geom.coordinates.map((point) => make({ type: 'Point', coordinates: point })).join('')
    return ''
  }
  return make(geometry)
}
function exportLayer(layer, format) {
  const geojson = layer.geojson?.type === 'Feature' ? layer.geojson : { type: 'Feature', properties: {}, geometry: layer.geojson }
  let content = JSON.stringify(geojson, null, 2); let mime = 'application/geo+json'; let extension = 'geojson'
  if (format === 'kml') { content = `<?xml version="1.0" encoding="UTF-8"?><kml xmlns="http://www.opengis.net/kml/2.2"><Document><name>${escapeXml(layer.name)}</name><Placemark><name>${escapeXml(layer.name)}</name>${geometryToKml(geojson.geometry)}</Placemark></Document></kml>`; mime = 'application/vnd.google-earth.kml+xml'; extension = 'kml' }
  const url = URL.createObjectURL(new Blob([content], { type: mime })); const link = document.createElement('a'); link.href = url; link.download = `${(layer.name || 'analise').replace(/[^a-z0-9_-]+/gi, '_')}.${extension}`; link.click(); URL.revokeObjectURL(url)
}

function resourceBounds(resource) {
  if (!resource) return null
  const bbox = resource.bbox || [resource.bbox_oeste, resource.bbox_sul, resource.bbox_leste, resource.bbox_norte]
  if (bbox.length !== 4 || bbox.some((v) => v == null || !Number.isFinite(Number(v)))) return null
  const [west, south, east, north] = bbox.map(Number)
  if (west >= east || south >= north) return null
  return [[south, west], [north, east]]
}

function fitResource(resource) {
  const map = leafletMap.value?.leafletObject
  const bounds = resourceBounds(resource)
  if (!map || !bounds) return
  map.invalidateSize()
  map.fitBounds(bounds, { padding: [40, 40], maxZoom: 20, animate: false })
  mapStore.setView([map.getCenter().lat, map.getCenter().lng], map.getZoom())
}

function onMapReady() {
  const newest = visibleOrtoLayers.value.at(-1)
  const resource = projectStore.ortomapas.find((o) => o.id === newest?.sourceId)
  fitResource(resource || projectStore.activeProject)
  const map = leafletMap.value?.leafletObject
  if (map) setupDrawing(map)
}

let drawHandler, stopDrawingWatch
function setupDrawing(map) {
  stopDrawingWatch?.()
  try { drawHandler?.disable() } catch { /* Previous keyed Leaflet map may already be removed. */ }
  drawHandler = null
  const drawn = new L.FeatureGroup().addTo(map)
  map.on(L.Draw.Event.DRAWVERTEX, event => { if(mapStore.drawMode==='profile') mapStore.profileVertexCount=event.layers.getLayers().length })
  map.on(L.Draw.Event.CREATED, (event) => {
    const mode = mapStore.drawMode
    drawn.clearLayers(); drawn.addLayer(event.layer)
    const geo = event.layer.toGeoJSON().geometry
    if (mode === 'profile') mapStore.profileLine = geo
    else {
      mapStore.setSelectedGeometry(geo)
      if (event.layer.getBounds) {
        const b = event.layer.getBounds()
        mapStore.setClipBbox({ xmin:b.getWest(),ymin:b.getSouth(),xmax:b.getEast(),ymax:b.getNorth() })
      }
    }
    mapStore.setDrawMode(null)
  })
  stopDrawingWatch = watch(() => mapStore.drawMode, mode => {
    drawHandler?.disable()
    mapStore.profileVertexCount=0; mapStore.finishProfile=null
    if (mode === 'profile') drawHandler = new L.Draw.Polyline(map,{shapeOptions:{color:'#eab308',weight:3}})
    else if (mode === 'clip') drawHandler = new L.Draw.Rectangle(map,{shapeOptions:{color:'#f59e0b'}})
    else drawHandler = null
    drawHandler?.enable()
    if(mode==='profile') mapStore.finishProfile=()=>drawHandler?.completeShape()
  },{immediate:true})
}

watch(() => projectStore.activeProject, (project) => fitResource(project), { flush: 'post' })
watch(() => mapStore.profileOpen, () => leafletMap.value?.leafletObject?.invalidateSize({animate:false}), {flush:'post'})
watch(() => projectStore.ortomapas, (products) => {
  if (visibleOrtoLayers.value.length || resourceBounds(projectStore.activeProject)) return
  const own = products.filter((p) => p.projeto_id === projectStore.activeProject?.id)
  fitResource(own.find((p) => p.tipo === 'ortomosaico') || own[0])
}, { flush: 'post' })
watch(
  () => visibleOrtoLayers.value.map((layer) => layer.sourceId).join('|'),
  () => {
    const newest = visibleOrtoLayers.value.at(-1)
    fitResource(projectStore.ortomapas.find((o) => o.id === newest?.sourceId))
  },
  { flush: 'post' }
)

// Enquadra automaticamente a camada espacial mais recente retornada pelo Copiloto.
watch(
  () => mapStore.activeLayers.map((layer) => layer.id).join('|'),
  () => {
    const map = leafletMap.value?.leafletObject
    const latest = [...mapStore.activeLayers].reverse().find((layer) => layer.type === 'analysis' && layer.geojson)
    if (!map || !latest) return
    const bounds = L.geoJSON(latest.geojson).getBounds()
    if (bounds.isValid()) setTimeout(() => map.fitBounds(bounds, { padding: [28, 28], maxZoom: 18 }), 0)
  }
)

// Expose measure points for MeasureTools
defineExpose({ measurePoints })

onMounted(() => {
  resizeObserver = new ResizeObserver(() => {
    cancelAnimationFrame(resizeFrame)
    resizeFrame = requestAnimationFrame(() => leafletMap.value?.leafletObject?.invalidateSize({ animate: false }))
  })
  resizeObserver.observe(mapContainer.value)
  // Fix Leaflet icon issue
  setTimeout(() => {
    if (leafletMap.value?.leafletObject) {
      leafletMap.value.leafletObject.invalidateSize()
    }
  }, 200)
})

onUnmounted(() => {
  stopDrawingWatch?.(); drawHandler?.disable()
  resizeObserver?.disconnect()
  cancelAnimationFrame(resizeFrame)
})
</script>

<style scoped>
.map-container {
  width: 100%;
  height: 100%;
  position: relative;
}

.map-container :deep(.leaflet-container) {
  width: 100%;
  height: 100%;
  background: #1a1a2e;
}
.map-container.profile-open :deep(.leaflet-container){height:calc(100% - 280px) !important}

.basemap-switcher {
  position: absolute;
  top: 12px;
  right: 12px;
  z-index: 800;
  display: flex;
  gap: 2px;
  background: var(--sidebar-bg);
  border-radius: 8px;
  padding: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.4);
}

.basemap-switcher button {
  width: 36px;
  height: 36px;
  border: none;
  background: transparent;
  color: var(--text-dim);
  cursor: pointer;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s;
}

.basemap-switcher button:hover {
  background: var(--sidebar-hover);
  color: var(--text);
}

.basemap-switcher button.active {
  background: var(--accent);
  color: #000;
}

.layer-controls {
  position: absolute;
  top: 60px;
  right: 12px;
  z-index: 800;
  background: var(--sidebar-bg);
  border-radius: 8px;
  padding: 8px 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.4);
  max-width: 220px;
}

.layer-control-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
  margin-bottom: 6px;
}

.layer-control-header { display: flex; align-items: center; gap: 5px; }
.layer-control-header .layer-name { flex: 1; }
.layer-control-header button { width: 20px; height: 20px; border: 0; background: transparent; color: var(--text-dim); cursor: pointer; padding: 0; }
.layer-control-header button:hover { color: #ef8f8f; }

.layer-control-item:last-child {
  margin-bottom: 0;
}

.layer-name {
  font-size: 0.7rem;
  color: var(--text-dim);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.layer-control-item input[type='range'] {
  width: 100%;
  height: 4px;
  accent-color: var(--accent);
}
</style>
