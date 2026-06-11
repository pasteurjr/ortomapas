<template>
  <div class="map-container" ref="mapContainer">
    <l-map
      ref="leafletMap"
      v-model:zoom="currentZoom"
      v-model:center="currentCenter"
      :useGlobalLeaflet="false"
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
      <l-tile-layer
        v-for="layer in visibleOrtoLayers"
        :key="'orto-' + layer.id"
        :url="`/api/ortomapas/${layer.sourceId}/tile/{z}/{x}/{y}.png`"
        :opacity="layer.opacity"
        :maxZoom="22"
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
        <span class="layer-name">{{ layer.name }}</span>
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
import { ref, computed, watch, onMounted } from 'vue'
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

// Watch for project change to zoom to bbox
watch(
  () => projectStore.activeProject,
  (project) => {
    if (project?.bbox) {
      const bbox = project.bbox
      currentCenter.value = [
        (bbox[1] + bbox[3]) / 2,
        (bbox[0] + bbox[2]) / 2,
      ]
      currentZoom.value = 14
    }
  }
)

// Expose measure points for MeasureTools
defineExpose({ measurePoints })

onMounted(() => {
  // Fix Leaflet icon issue
  setTimeout(() => {
    if (leafletMap.value?.leafletObject) {
      leafletMap.value.leafletObject.invalidateSize()
    }
  }, 200)
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
