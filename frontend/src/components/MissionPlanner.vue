<template>
  <section class="mission-planner" aria-label="Planejador de missao de captura">
    <header class="planner-header">
      <div class="planner-title">
        <button class="icon-button" type="button" title="Fechar planejador" aria-label="Fechar planejador" @click="$emit('close')">
          <i class="pi pi-arrow-left"></i>
        </button>
        <div>
          <span class="eyebrow">Planejamento de voo</span>
          <h1>Missao de captura</h1>
        </div>
      </div>
      <div class="planner-actions">
        <span class="save-state" :class="{ saved: saved }">
          <i :class="saved ? 'pi pi-check-circle' : 'pi pi-circle'"></i>
          {{ saved ? 'Salva' : 'Rascunho' }}
        </span>
        <button class="primary-button" type="button" :disabled="saving || !canSave" @click="saveMission">
          <i :class="saving ? 'pi pi-spin pi-spinner' : 'pi pi-save'"></i>
          {{ saving ? 'Salvando' : 'Salvar missao' }}
        </button>
      </div>
    </header>

    <div class="planner-body">
      <main class="planner-map-wrap">
        <div ref="mapElement" class="planner-map"></div>
        <div class="map-toolbar" role="toolbar" aria-label="Ferramentas do mapa">
          <button class="tool-button" :class="{ active: activeTool === 'aoi' }" type="button" title="Desenhar area de interesse" aria-label="Desenhar area de interesse" @click="activate('aoi')">
            <i class="pi pi-stop"></i><span>AOI</span>
          </button>
          <button class="tool-button" :class="{ active: activeTool === 'exclusion' }" type="button" title="Desenhar zona de exclusao" aria-label="Desenhar zona de exclusao" @click="activate('exclusion')">
            <i class="pi pi-ban"></i><span>Exclusao</span>
          </button>
          <button class="tool-button" :class="{ active: activeTool === 'takeoff' }" type="button" title="Marcar ponto de decolagem" aria-label="Marcar ponto de decolagem" @click="activate('takeoff')">
            <i class="pi pi-home"></i><span>Takeoff</span>
          </button>
          <button class="tool-button" :class="{ active: activeTool === 'waypoint' }" type="button" title="Adicionar waypoint" aria-label="Adicionar waypoint" @click="activate('waypoint')">
            <i class="pi pi-map-marker"></i><span>Waypoint</span>
          </button>
          <button class="tool-button" :class="{ active: selectedWaypointId }" type="button" title="Selecionar waypoint" aria-label="Selecionar waypoint" @click="activate('select')">
            <i class="pi pi-crosshairs"></i><span>Selecionar</span>
          </button>
          <button class="tool-button" type="button" title="Importar GeoJSON" aria-label="Importar GeoJSON" @click="fileInput?.click()">
            <i class="pi pi-upload"></i><span>Importar</span>
          </button>
          <input ref="fileInput" class="visually-hidden" type="file" accept=".json,.geojson,application/geo+json,application/json" @change="importGeoJson" />
          <button class="tool-button" type="button" title="Gerar grid fotogrametrica" aria-label="Gerar grid fotogrametrica" :disabled="!missionId || generatingGrid" @click="generateGrid">
            <i :class="generatingGrid ? 'pi pi-spin pi-spinner' : 'pi pi-th-large'"></i><span>Gerar grid</span>
          </button>
          <button class="tool-button" type="button" title="Limpar desenho" aria-label="Limpar desenho" @click="clearMap">
            <i class="pi pi-trash"></i><span>Limpar</span>
          </button>
          <button class="tool-button" :class="{ active: simulationRunning }" type="button" :title="simulationRunning ? 'Pausar simulacao' : 'Simular rota'" :aria-label="simulationRunning ? 'Pausar simulacao' : 'Simular rota'" :disabled="!waypoints.length" @click="toggleSimulation">
            <i :class="simulationRunning ? 'pi pi-pause' : 'pi pi-play'"></i><span>{{ simulationRunning ? 'Pausar' : 'Simular' }}</span>
          </button>
          <button class="tool-button" type="button" title="Validar seguranca e compatibilidade" aria-label="Validar missao" :disabled="!missionId || validating" @click="validateMission">
            <i :class="validating ? 'pi pi-spin pi-spinner' : 'pi pi-shield'"></i><span>Validar</span>
          </button>
          <button class="tool-button" type="button" title="Baixar KML da rota" aria-label="Exportar KML" :disabled="!missionId || exporting" @click="exportMission">
            <i :class="exporting ? 'pi pi-spin pi-spinner' : 'pi pi-download'"></i><span>Exportar</span>
          </button>
          <button class="tool-button" type="button" title="Baixar CSV para Litchi Mission Hub" aria-label="Exportar Litchi" :disabled="!missionId || exporting" @click="exportMission('litchi_csv')">
            <i class="pi pi-send"></i><span>Litchi CSV</span>
          </button>
        </div>
        <div class="map-legend">
          <span><i class="legend-swatch aoi"></i>AOI</span>
          <span><i class="legend-swatch exclusion"></i>Exclusao</span>
          <span><i class="legend-swatch route"></i>Rota</span>
        </div>
        <div v-if="notice" class="map-notice" :class="noticeType" role="status">
          <i :class="noticeType === 'error' ? 'pi pi-exclamation-triangle' : 'pi pi-info-circle'"></i>
          {{ notice }}
        </div>
      </main>

      <aside class="planner-panel">
        <div class="panel-section">
          <div class="section-heading"><span>Identificacao</span><span class="step">1/3</span></div>
          <label for="mission-name">Nome da missao</label>
          <input id="mission-name" v-model.trim="missionName" class="text-input" placeholder="Ex.: Fazenda Norte - Grid 50m" />
          <p class="project-context"><i class="pi pi-folder"></i>{{ projectStore.activeProject?.nome || 'Selecione um projeto' }}</p>
        </div>

        <div class="panel-section">
          <div class="section-heading"><span>Captura</span><span class="step">2/3</span></div>
          <div class="field-grid">
            <label>Drone<select v-model="capture.drone"><option>DJI Mini 3</option><option>DJI Mini 3 Pro</option><option>Outro</option></select></label>
            <label>Formato<select v-model="capture.format"><option>JPEG</option><option>JPEG + RAW</option></select></label>
            <label>GSD (cm/px)<input v-model.number="capture.gsd" type="number" min="0.1" step="0.1" /></label>
            <label>Altitude (m)<input v-model.number="capture.altitude" type="number" min="1" step="1" /></label>
            <label>Overlap frontal (%)<input v-model.number="capture.frontOverlap" type="number" min="0" max="95" step="1" /></label>
            <label>Overlap lateral (%)<input v-model.number="capture.sideOverlap" type="number" min="0" max="95" step="1" /></label>
            <label>Velocidade (m/s)<input v-model.number="capture.speed" type="number" min="0.5" step="0.5" /></label>
            <label>Gimbal (graus)<input v-model.number="capture.gimbal" type="number" min="-90" max="30" step="1" /></label>
          </div>
          <div class="capture-note"><i class="pi pi-lightbulb"></i>Preset nadir. Salve a missao e gere a cobertura para calcular linhas, fotos e distancia.</div>
          <div class="grid-options">
            <label>Orientacao (graus)<input v-model.number="gridOptions.orientacao_graus" type="number" min="-180" max="180" step="1" /></label>
            <label>Espacamento linhas (m)<input v-model.number="gridOptions.espacamento_linhas_m" type="number" min="1" step="1" /></label>
            <label>Espacamento fotos (m)<input v-model.number="gridOptions.espacamento_fotos_m" type="number" min="1" step="1" /></label>
            <label class="check-field"><input v-model="gridOptions.double_grid" type="checkbox" /> Double-grid</label>
          </div>
          <div v-if="gridStats" class="grid-summary" aria-label="Resumo do grid">
            <span><strong>{{ gridStats.lines }}</strong> linhas</span>
            <span><strong>{{ gridStats.waypoints }}</strong> fotos</span>
            <span><strong>{{ gridStats.distanceLabel }}</strong> distancia</span>
          </div>
        </div>

        <div class="panel-section">
          <div class="section-heading"><span>Elementos da missao</span><span class="step">3/3</span></div>
          <div class="metric-grid">
            <div><strong>{{ aoi ? '1' : '0' }}</strong><span>AOI</span></div>
            <div><strong>{{ exclusions.length }}</strong><span>Exclusoes</span></div>
            <div><strong>{{ waypoints.length }}</strong><span>Waypoints</span></div>
            <div><strong>{{ takeoff ? 'OK' : '--' }}</strong><span>Takeoff</span></div>
          </div>
          <div class="coordinate-card" v-if="takeoff"><span>Decolagem</span><code>{{ takeoff.lat.toFixed(6) }}, {{ takeoff.lng.toFixed(6) }}</code></div>
          <div class="coordinate-card empty" v-else><i class="pi pi-home"></i><span>Marque o ponto de decolagem no mapa</span></div>
          <div class="waypoint-list" v-if="waypoints.length">
            <div v-for="(point, index) in waypoints" :key="point.id" class="waypoint-row" :class="{ selected: selectedWaypointId === point.id }" tabindex="0" @click="selectWaypoint(point.id)" @keydown.enter="selectWaypoint(point.id)">
              <span class="waypoint-number">{{ index + 1 }}</span>
              <code>{{ point.lat.toFixed(5) }}, {{ point.lng.toFixed(5) }}</code>
              <button type="button" title="Remover waypoint" aria-label="Remover waypoint" @click="removeWaypoint(point.id)"><i class="pi pi-times"></i></button>
            </div>
          </div>
          <div v-if="selectedWaypoint" class="waypoint-editor" aria-label="Editor do waypoint selecionado">
            <div class="selected-heading"><span>Waypoint {{ selectedWaypointIndex + 1 }}</span><span class="selected-badge">Selecionado</span></div>
            <div class="field-grid compact-grid">
              <label>Altitude (m)<input v-model.number="selectedWaypoint.altitude_m" type="number" min="1" step="1" @change="markDirty" /></label>
              <label>Velocidade (m/s)<input v-model.number="selectedWaypoint.velocidade_ms" type="number" min="0.5" step="0.5" @change="markDirty" /></label>
              <label>Gimbal (graus)<input v-model.number="selectedWaypoint.gimbal_graus" type="number" min="-90" max="30" step="1" @change="markDirty" /></label>
              <label>Rumo (graus)<input v-model.number="selectedWaypoint.rumo_graus" type="number" min="-180" max="180" step="1" @change="markDirty" /></label>
            </div>
            <div class="waypoint-actions">
              <button type="button" @click="insertWaypoint('before')"><i class="pi pi-plus"></i> Antes</button>
              <button type="button" @click="insertWaypoint('after')"><i class="pi pi-plus"></i> Depois</button>
              <button type="button" @click="duplicateWaypoint"><i class="pi pi-copy"></i> Duplicar</button>
              <button type="button" class="danger-action" @click="removeWaypoint(selectedWaypoint.id)"><i class="pi pi-trash"></i> Excluir</button>
            </div>
          </div>
          <div v-if="simulationIndex >= 0" class="simulation-status" role="status">Simulando ponto {{ simulationIndex + 1 }} de {{ waypoints.length }}</div>
          <div v-if="validationReport" class="validation-report" aria-label="Resultado da validacao">
            <div class="validation-summary" :class="`status-${validationReport.status}`"><i :class="validationReport.status === 'aprovado' ? 'pi pi-check-circle' : validationReport.status === 'aviso' ? 'pi pi-exclamation-triangle' : 'pi pi-ban'"></i><strong>{{ validationReport.status }}</strong><span>{{ validationReport.blocked }} bloqueio(s), {{ validationReport.warnings }} aviso(s)</span></div>
            <div v-for="rule in validationReport.rules" :key="rule.regra" class="validation-rule" :class="`rule-${rule.status}`"><i :class="rule.status === 'aprovado' ? 'pi pi-check' : rule.status === 'aviso' ? 'pi pi-exclamation-triangle' : 'pi pi-times'"></i><span><strong>{{ rule.regra }}</strong>{{ rule.mensagem }}</span></div>
          </div>
        </div>

        <div class="panel-footer">
          <div class="validation-line" :class="canSave ? 'ok' : 'warn'"><i :class="canSave ? 'pi pi-check-circle' : 'pi pi-exclamation-circle'"></i>{{ validationMessage }}</div>
          <span class="crs-label">CRS de exportacao: EPSG:4326</span>
        </div>
      </aside>
    </div>
  </section>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import L from 'leaflet'
import 'leaflet-draw'
import 'leaflet-draw/dist/leaflet.draw.css'
import { useProjectStore } from '../stores/projectStore'
import { createCaptureMission, exportCaptureMission, generateCaptureGrid, getCaptureMission, updateCaptureWaypoints, validateCaptureMission } from '../api/client'

defineEmits(['close'])
const projectStore = useProjectStore()
const mapElement = ref(null)
const fileInput = ref(null)
const map = ref(null)
const drawn = ref(null)
const aoi = ref(null)
const exclusions = ref([])
const takeoff = ref(null)
const waypoints = ref([])
const missionName = ref('')
const missionId = ref(null)
const activeTool = ref(null)
const saving = ref(false)
const generatingGrid = ref(false)
const saved = ref(false)
const notice = ref('')
const noticeType = ref('info')
const capture = reactive({ drone: 'DJI Mini 3', format: 'JPEG', gsd: 1.5, altitude: 50, frontOverlap: 80, sideOverlap: 70, speed: 4, gimbal: -90 })
const gridOptions = reactive({ orientacao_graus: 0, double_grid: false, espacamento_linhas_m: 80, espacamento_fotos_m: 80 })
const gridStats = ref(null)
const selectedWaypointId = ref(null)
const simulationRunning = ref(false)
const simulationIndex = ref(-1)
const waypointDirty = ref(false)
const validating = ref(false)
const exporting = ref(false)
const validationReport = ref(null)
let waypointLine = null
let simulationMarker = null
let simulationTimer = null
let polygonPoints = []
let polygonPreview = null
let polygonVertices = []

const canSave = computed(() => Boolean(projectStore.activeProject?.id && missionName.value && aoi.value && takeoff.value))
const validationMessage = computed(() => {
  if (!projectStore.activeProject?.id) return 'Selecione um projeto para continuar'
  if (!missionName.value) return 'Informe o nome da missao'
  if (!aoi.value) return 'Desenhe a area de interesse'
  if (!takeoff.value) return 'Marque o ponto de decolagem'
  return 'Pronto para salvar o rascunho'
})
const selectedWaypointIndex = computed(() => waypoints.value.findIndex((point) => point.id === selectedWaypointId.value))
const selectedWaypoint = computed(() => selectedWaypointIndex.value >= 0 ? waypoints.value[selectedWaypointIndex.value] : null)

function showNotice(message, type = 'info') {
  notice.value = message; noticeType.value = type
  window.clearTimeout(showNotice.timer)
  showNotice.timer = window.setTimeout(() => { notice.value = '' }, 3500)
}

function styleFor(type) {
  if (type === 'aoi') return { color: '#22d3ee', fillColor: '#0891b2', fillOpacity: 0.16, weight: 3 }
  if (type === 'exclusion') return { color: '#fb7185', fillColor: '#be123c', fillOpacity: 0.28, weight: 2, dashArray: '6 5' }
  return { color: '#4ade80', weight: 3, dashArray: '8 5' }
}

function activate(tool) {
  activeTool.value = activeTool.value === tool ? null : tool
  if (activeTool.value === 'aoi' || activeTool.value === 'exclusion') {
    polygonPoints = []
    polygonPreview = null
    polygonVertices = []
    showNotice('Clique no mapa para adicionar vertices; clique no primeiro para fechar')
  } else if (activeTool.value === 'takeoff' || activeTool.value === 'waypoint') {
    showNotice(activeTool.value === 'takeoff' ? 'Clique no mapa para marcar a decolagem' : 'Clique no mapa para adicionar waypoints')
  }
}

function addTakeoff(latlng) {
  takeoff.value = { lat: latlng.lat, lng: latlng.lng }
  if (drawn.value?.takeoff) map.value.removeLayer(drawn.value.takeoff)
  drawn.value.takeoff = L.marker(latlng, { title: 'Ponto de decolagem' }).addTo(map.value).bindTooltip('Takeoff', { permanent: true, direction: 'top', className: 'takeoff-label' })
  activeTool.value = null
}

function waypointIcon(index, selected = false) {
  return L.divIcon({ className: `waypoint-marker${selected ? ' selected' : ''}`, html: `<span>${index + 1}</span>`, iconSize: [28, 28], iconAnchor: [14, 14] })
}

function addWaypoint(latlng, values = {}) {
  const id = values.id || `wp-${Date.now()}-${waypoints.value.length}`
  const item = { id, lat: latlng.lat, lng: latlng.lng, altitude_m: values.altitude_m || capture.altitude, velocidade_ms: values.velocidade_ms || capture.speed, gimbal_graus: values.gimbal_graus ?? capture.gimbal, rumo_graus: values.rumo_graus ?? null }
  waypoints.value.push(item)
  const marker = L.marker(latlng, { title: `Waypoint ${waypoints.value.length}`, draggable: true, icon: waypointIcon(waypoints.value.length - 1) }).addTo(map.value)
  marker.on('click', () => selectWaypoint(id))
  marker.on('dragend', (event) => {
    const point = waypoints.value.find((entry) => entry.id === id)
    if (!point) return
    const position = event.target.getLatLng()
    point.lat = position.lat; point.lng = position.lng; waypointDirty.value = true; updateWaypointLine(); selectWaypoint(id)
  })
  drawn.value.waypoints[id] = marker
  updateWaypointLine(); return id
}

function updateWaypointLine() {
  if (waypointLine) map.value.removeLayer(waypointLine)
  if (waypoints.value.length > 1) waypointLine = L.polyline(waypoints.value.map((p) => [p.lat, p.lng]), styleFor('route')).addTo(map.value)
}

function removeWaypoint(id) {
  const marker = drawn.value?.waypoints[id]
  if (marker) map.value.removeLayer(marker)
  delete drawn.value.waypoints[id]
  waypoints.value = waypoints.value.filter((point) => point.id !== id)
  waypoints.value.forEach((point, index) => { const m = drawn.value.waypoints[point.id]; if (m) { m.setIcon(waypointIcon(index, point.id === selectedWaypointId.value)); m.options.title = `Waypoint ${index + 1}` } })
  if (selectedWaypointId.value === id) selectedWaypointId.value = waypoints.value[Math.max(0, waypoints.value.length - 1)]?.id || null
  waypointDirty.value = true; updateWaypointLine()
}

function selectWaypoint(id) {
  selectedWaypointId.value = id
  waypoints.value.forEach((point, index) => drawn.value?.waypoints[point.id]?.setIcon(waypointIcon(index, point.id === id)))
  const marker = drawn.value?.waypoints[id]
  if (marker) map.value.panTo(marker.getLatLng(), { animate: true, duration: 0.2 })
}

function markDirty() { waypointDirty.value = true }

function insertWaypoint(position) {
  if (!selectedWaypoint.value) return
  const index = selectedWaypointIndex.value
  const neighborIndex = position === 'before' ? Math.max(0, index - 1) : Math.min(waypoints.value.length - 1, index + 1)
  const neighbor = waypoints.value[neighborIndex]
  const latlng = { lat: (selectedWaypoint.value.lat + neighbor.lat) / 2, lng: (selectedWaypoint.value.lng + neighbor.lng) / 2 }
  const newId = addWaypoint(latlng, { altitude_m: selectedWaypoint.value.altitude_m, velocidade_ms: selectedWaypoint.value.velocidade_ms, gimbal_graus: selectedWaypoint.value.gimbal_graus, rumo_graus: selectedWaypoint.value.rumo_graus })
  const item = waypoints.value.pop()
  waypoints.value.splice(position === 'before' ? index : index + 1, 0, item)
  redrawWaypointMarkers(); selectWaypoint(newId); waypointDirty.value = true; updateWaypointLine()
}

function duplicateWaypoint() { insertWaypoint('after') }

function redrawWaypointMarkers() {
  waypoints.value.forEach((point, index) => { const marker = drawn.value?.waypoints[point.id]; if (marker) marker.setIcon(waypointIcon(index, point.id === selectedWaypointId.value)) })
}

function onMapClick(event) {
  if (activeTool.value === 'aoi' || activeTool.value === 'exclusion') {
    if (polygonPoints.length >= 3) {
      const first = map.value.latLngToContainerPoint(polygonPoints[0])
      const current = map.value.latLngToContainerPoint(event.latlng)
      if (first.distanceTo(current) <= 22) {
        finishPolygon()
        return
      }
    }
    polygonPoints.push(event.latlng)
    polygonVertices.push(L.circleMarker(event.latlng, { radius: 5, color: '#f8fafc', weight: 2, fillColor: '#0891b2', fillOpacity: 1 }).addTo(map.value))
    if (polygonPreview) map.value.removeLayer(polygonPreview)
    polygonPreview = L.polyline(polygonPoints, { color: activeTool.value === 'aoi' ? '#22d3ee' : '#fb7185', weight: 2, dashArray: '5 4' }).addTo(map.value)
    return
  }
  if (activeTool.value === 'takeoff') addTakeoff(event.latlng)
  if (activeTool.value === 'waypoint') addWaypoint(event.latlng)
}

function finishPolygon() {
  const type = activeTool.value
  if (polygonPoints.length < 3) return
  polygonVertices.forEach((marker) => map.value.removeLayer(marker))
  if (polygonPreview) map.value.removeLayer(polygonPreview)
  const layer = L.polygon(polygonPoints, styleFor(type)).addTo(map.value)
  makeOverlayPassive(layer)
  if (type === 'aoi') {
    if (drawn.value.aoi) map.value.removeLayer(drawn.value.aoi)
    drawn.value.aoi = layer
    aoi.value = layer.toGeoJSON().geometry
  } else {
    drawn.value.exclusions.push(layer)
    exclusions.value.push(layer.toGeoJSON().geometry)
  }
  polygonPoints = []; polygonPreview = null; polygonVertices = []
  activeTool.value = null
  showNotice(type === 'aoi' ? 'Area de interesse definida' : 'Zona de exclusao adicionada')
}

function makeOverlayPassive(layer) {
  // As geometrias servem como referência visual; não podem bloquear o
  // desenho de uma exclusão ou a marcação de pontos sobre a AOI.
  layer.options.interactive = false
  if (layer._path) layer._path.style.pointerEvents = 'none'
}

function onDrawCreated(event) {
  // Mantido para compatibilidade com a API do Leaflet Draw; o editor usa o
  // fluxo explícito de cliques acima para permitir alternância de ferramentas.
  if (event.layer) map.value.removeLayer(event.layer)
}

function clearMap() {
  Object.values(drawn.value?.waypoints || {}).forEach((layer) => map.value.removeLayer(layer))
  if (drawn.value?.aoi) map.value.removeLayer(drawn.value.aoi)
  drawn.value?.exclusions?.forEach((layer) => map.value.removeLayer(layer))
  if (drawn.value?.takeoff) map.value.removeLayer(drawn.value.takeoff)
  if (waypointLine) map.value.removeLayer(waypointLine)
  stopSimulation(); aoi.value = null; exclusions.value = []; takeoff.value = null; waypoints.value = []; waypointLine = null; selectedWaypointId.value = null; gridStats.value = null
  drawn.value = { waypoints: {}, exclusions: [] }; activeTool.value = null; saved.value = false; missionId.value = null
}

function normalizeGeoJson(input) {
  if (input.type === 'FeatureCollection') return input.features.find((f) => ['Polygon', 'MultiPolygon'].includes(f.geometry?.type))?.geometry
  if (input.type === 'Feature') return input.geometry
  return input
}

function importGeoJson(event) {
  const file = event.target.files?.[0]
  if (!file) return
  const reader = new FileReader()
  reader.onload = () => {
    try {
      const geometry = normalizeGeoJson(JSON.parse(reader.result))
      if (!geometry || !['Polygon', 'MultiPolygon'].includes(geometry.type)) throw new Error('O arquivo precisa conter Polygon ou MultiPolygon')
      if (drawn.value.aoi) map.value.removeLayer(drawn.value.aoi)
      drawn.value.aoi = L.geoJSON(geometry, { style: styleFor('aoi') }).addTo(map.value)
      aoi.value = geometry
      map.value.fitBounds(drawn.value.aoi.getBounds(), { padding: [28, 28] })
      showNotice('AOI importada do GeoJSON')
    } catch (error) { showNotice(error.message || 'Nao foi possivel importar o GeoJSON', 'error') }
    event.target.value = ''
  }
  reader.readAsText(file)
}

async function saveMission() {
  if (!canSave.value) return
  saving.value = true
  try {
    const payload = {
      nome: missionName.value,
      drone_perfil: { modelo: capture.drone, controle: 'DJI RC-N1' },
      camera_perfil: { formato: capture.format },
      crs: 'EPSG:4326',
      takeoff: { lat: takeoff.value.lat, lon: takeoff.value.lng },
      capture: { gsd_cm_px: capture.gsd, front_overlap: capture.frontOverlap / 100, side_overlap: capture.sideOverlap / 100, altitude_m: capture.altitude, altitude_referencia: 'AGL', velocidade_ms: capture.speed, gimbal_graus: capture.gimbal },
      aoi: { type: aoi.value.type, coordinates: aoi.value.coordinates },
      zonas_exclusao: exclusions.value,
      canonical: { waypoints: waypoints.value.map(({ lat, lng }) => ({ lat, lon: lng })) },
    }
    if (missionId.value) {
      await updateCaptureWaypoints(missionId.value, waypoints.value)
      waypointDirty.value = false; saved.value = true; showNotice('Edicoes da missao salvas')
    } else {
      const response = await createCaptureMission(projectStore.activeProject.id, payload)
      missionId.value = response.data.id; saved.value = true; showNotice('Missao salva no projeto')
    }
  } catch (error) { showNotice(error.response?.data?.detail || 'Nao foi possivel salvar a missao', 'error')
  } finally { saving.value = false }
}

function clearGeneratedWaypoints() {
  Object.values(drawn.value?.waypoints || {}).forEach((layer) => map.value.removeLayer(layer))
  drawn.value.waypoints = {}
  waypoints.value = []
  selectedWaypointId.value = null
  if (waypointLine) { map.value.removeLayer(waypointLine); waypointLine = null }
}

async function generateGrid() {
  if (!missionId.value) { showNotice('Salve a missao antes de gerar o grid', 'error'); return }
  generatingGrid.value = true
  try {
    const response = await generateCaptureGrid(missionId.value, gridOptions)
    const missionResponse = await getCaptureMission(missionId.value)
    const mission = missionResponse.data
    clearGeneratedWaypoints()
    ;(mission.waypoints || []).forEach((point) => addWaypoint({ lat: Number(point.latitude), lng: Number(point.longitude) }, { altitude_m: point.altitude_m, velocidade_ms: point.velocidade_ms, gimbal_graus: point.gimbal_graus, rumo_graus: point.rumo_graus }))
    selectedWaypointId.value = waypoints.value[0]?.id || null
    redrawWaypointMarkers()
    gridStats.value = {
      ...response.data.grid,
      waypoints: response.data.waypoints,
      distanceLabel: `${(response.data.distancia_m / 1000).toFixed(2)} km`,
    }
    saved.value = true
    waypointDirty.value = false
    showNotice(`Grid gerado: ${response.data.waypoints} pontos em ${response.data.blocos} bloco(s)`)
  } catch (error) {
    showNotice(error.response?.data?.detail || 'Nao foi possivel gerar o grid', 'error')
  } finally { generatingGrid.value = false }
}

function startSimulation() {
  if (!waypoints.value.length) return
  stopSimulation(false); simulationRunning.value = true; simulationIndex.value = simulationIndex.value >= 0 ? simulationIndex.value : 0
  if (simulationMarker) map.value.removeLayer(simulationMarker)
  simulationMarker = L.circleMarker([waypoints.value[simulationIndex.value].lat, waypoints.value[simulationIndex.value].lng], { radius: 9, color: '#facc15', fillColor: '#facc15', fillOpacity: .95, weight: 3 }).addTo(map.value)
  simulationTimer = window.setInterval(() => {
    simulationIndex.value += 1
    if (simulationIndex.value >= waypoints.value.length) { stopSimulation(false); return }
    const point = waypoints.value[simulationIndex.value]
    simulationMarker.setLatLng([point.lat, point.lng]); selectWaypoint(point.id)
  }, 450)
}

function stopSimulation(reset = true) {
  simulationRunning.value = false
  if (simulationTimer) { window.clearInterval(simulationTimer); simulationTimer = null }
  if (simulationMarker) { map.value?.removeLayer(simulationMarker); simulationMarker = null }
  if (reset) simulationIndex.value = -1
}

function toggleSimulation() { simulationRunning.value ? stopSimulation(false) : startSimulation() }

async function validateMission() {
  if (!missionId.value) { showNotice('Salve a missao antes de validar', 'error'); return }
  validating.value = true
  try {
    const response = await validateCaptureMission(missionId.value)
    validationReport.value = response.data
    showNotice(`Validacao: ${response.data.status}`)
  } catch (error) { showNotice(error.response?.data?.detail || 'Nao foi possivel validar a missao', 'error')
  } finally { validating.value = false }
}

async function exportMission(formato = 'kml') {
  if (!missionId.value || exporting.value) return
  exporting.value = true
  try {
    const response = await exportCaptureMission(missionId.value, formato)
    const blobUrl = URL.createObjectURL(response.data)
    const link = document.createElement('a')
    const extension = formato === 'litchi_csv' ? 'csv' : 'kml'
    link.href = blobUrl; link.download = `${missionName.value || 'missao'}.${extension}`; link.click()
    URL.revokeObjectURL(blobUrl)
    showNotice(formato === 'litchi_csv' ? 'CSV Litchi exportado para o Mission Hub' : 'KML exportado para o aplicativo de mapas')
  } catch (error) {
    showNotice(error?.response?.data?.detail || 'Falha ao exportar KML', 'error')
  } finally { exporting.value = false }
}

onMounted(() => {
  map.value = L.map(mapElement.value, { zoomControl: true }).setView([-15.78, -47.93], 13)
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { attribution: '&copy; OpenStreetMap contributors', maxZoom: 19 }).addTo(map.value)
  drawn.value = { waypoints: {}, exclusions: [] }
  map.value.on('click', onMapClick)
  map.value.on(L.Draw.Event.CREATED, onDrawCreated)
  window.setTimeout(() => map.value?.invalidateSize(), 100)
})

onBeforeUnmount(() => { stopSimulation(); if (map.value) map.value.remove() })
</script>

<style scoped>
.mission-planner { position: fixed; inset: 0; z-index: 1200; display: flex; flex-direction: column; background: #0b1120; color: #e2e8f0; }
.planner-header { height: 64px; display: flex; align-items: center; justify-content: space-between; gap: 16px; padding: 0 20px; background: #111827; border-bottom: 1px solid #334155; }
.planner-title, .planner-actions, .section-heading, .save-state, .project-context, .capture-note, .validation-line { display: flex; align-items: center; }
.planner-title { gap: 12px; }.planner-title h1 { margin: 1px 0 0; font-size: 1.05rem; font-weight: 650; }.eyebrow { color: #94a3b8; font-size: .7rem; text-transform: uppercase; letter-spacing: .08em; }
.planner-actions { gap: 14px; }.icon-button, .tool-button, .waypoint-row button { border: 0; cursor: pointer; color: #cbd5e1; background: transparent; }.icon-button { width: 34px; height: 34px; border-radius: 7px; font-size: 1rem; }.icon-button:hover { background: #1e293b; color: #fff; }
.primary-button { border: 0; border-radius: 6px; padding: 9px 13px; background: #22c55e; color: #052e16; font-weight: 700; cursor: pointer; }.primary-button:disabled { opacity: .45; cursor: not-allowed; }.save-state { gap: 6px; color: #fbbf24; font-size: .78rem; }.save-state.saved { color: #4ade80; }
.planner-body { display: flex; flex: 1; min-height: 0; }.planner-map-wrap { position: relative; flex: 1; min-width: 0; }.planner-map { position: absolute; inset: 0; background: #162032; }.planner-panel { width: 360px; overflow-y: auto; background: #111827; border-left: 1px solid #334155; }
.map-toolbar { position: absolute; z-index: 700; left: 16px; top: 16px; display: flex; gap: 4px; padding: 6px; border: 1px solid #334155; border-radius: 8px; background: rgba(15, 23, 42, .95); box-shadow: 0 8px 22px rgba(15, 23, 42, .28); }.tool-button { display: flex; align-items: center; gap: 5px; padding: 8px 9px; border-radius: 5px; font-size: .72rem; }.tool-button:hover, .tool-button.active { background: #164e63; color: #67e8f9; }.tool-button i { font-size: .85rem; }
.map-legend { position: absolute; z-index: 700; left: 16px; bottom: 20px; display: flex; gap: 10px; padding: 7px 9px; border-radius: 6px; background: rgba(15, 23, 42, .9); color: #cbd5e1; font-size: .72rem; }.map-legend span { display: flex; align-items: center; gap: 4px; }.legend-swatch { width: 9px; height: 9px; border-radius: 2px; display: inline-block; }.legend-swatch.aoi { background: #22d3ee; }.legend-swatch.exclusion { background: #fb7185; }.legend-swatch.route { background: #4ade80; }.map-notice { position: absolute; z-index: 800; top: 76px; left: 50%; transform: translateX(-50%); padding: 9px 13px; border-radius: 6px; background: #0f172a; border: 1px solid #334155; color: #bae6fd; font-size: .78rem; box-shadow: 0 8px 20px rgba(0,0,0,.25); }.map-notice.error { border-color: #fb7185; color: #fecdd3; }
.panel-section { padding: 16px; border-bottom: 1px solid #1f2937; }.section-heading { justify-content: space-between; margin-bottom: 12px; color: #f8fafc; font-size: .78rem; font-weight: 700; text-transform: uppercase; letter-spacing: .07em; }.step { color: #64748b; font-size: .68rem; }label { display: flex; flex-direction: column; gap: 5px; color: #94a3b8; font-size: .72rem; }.text-input, select, input[type=number] { width: 100%; min-height: 34px; border: 1px solid #334155; border-radius: 5px; padding: 7px 8px; background: #0f172a; color: #e2e8f0; font-size: .78rem; }.text-input:focus, select:focus, input:focus { outline: 2px solid #22d3ee; outline-offset: 1px; }.project-context { gap: 6px; margin-top: 9px; color: #67e8f9; font-size: .74rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }.field-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }.capture-note { gap: 7px; margin-top: 12px; color: #94a3b8; font-size: .7rem; line-height: 1.35; }.capture-note i { color: #fbbf24; }
.metric-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 6px; }.metric-grid div { padding: 8px 4px; border: 1px solid #263449; border-radius: 5px; text-align: center; }.metric-grid strong { display: block; color: #67e8f9; font-size: .95rem; }.metric-grid span { display: block; margin-top: 2px; color: #94a3b8; font-size: .62rem; }.coordinate-card { display: flex; flex-direction: column; gap: 4px; margin-top: 12px; padding: 9px; border-radius: 5px; background: #0f172a; color: #94a3b8; font-size: .7rem; }.coordinate-card code, .waypoint-row code { color: #bae6fd; font-size: .7rem; }.coordinate-card.empty { flex-direction: row; align-items: center; color: #64748b; }.coordinate-card.empty i { color: #fbbf24; }.waypoint-list { display: flex; flex-direction: column; gap: 4px; margin-top: 10px; max-height: 150px; overflow: auto; }.waypoint-row { display: flex; align-items: center; gap: 7px; padding: 5px 7px; border-radius: 4px; background: #0f172a; }.waypoint-number { display: grid; place-items: center; width: 19px; height: 19px; border-radius: 50%; background: #22c55e; color: #052e16; font-size: .65rem; font-weight: 700; }.waypoint-row code { flex: 1; }.waypoint-row button:hover { color: #fb7185; }.panel-footer { padding: 14px 16px 18px; }.validation-line { gap: 7px; font-size: .73rem; line-height: 1.35; }.validation-line.ok { color: #86efac; }.validation-line.warn { color: #fbbf24; }.crs-label { display: block; margin-top: 9px; color: #64748b; font-size: .68rem; }.visually-hidden { position: absolute; width: 1px; height: 1px; opacity: 0; pointer-events: none; }
.tool-button:disabled { opacity: .4; cursor: not-allowed; }.grid-options { display: grid; grid-template-columns: 1fr 1fr; align-items: end; gap: 10px; margin-top: 12px; }.check-field { flex-direction: row; align-items: center; min-height: 34px; color: #cbd5e1; }.check-field input { accent-color: #22c55e; }.grid-summary { display: grid; grid-template-columns: repeat(3, 1fr); gap: 5px; margin-top: 10px; color: #94a3b8; font-size: .65rem; text-align: center; }.grid-summary span { padding: 6px 3px; border: 1px solid #263449; border-radius: 4px; }.grid-summary strong { display: block; color: #86efac; font-size: .78rem; }.waypoint-editor { margin-top: 12px; padding: 10px; border: 1px solid #155e75; border-radius: 6px; background: #0b2233; }.selected-heading { display: flex; justify-content: space-between; align-items: center; color: #e0f2fe; font-size: .75rem; font-weight: 700; }.selected-badge { color: #67e8f9; font-size: .62rem; text-transform: uppercase; }.compact-grid { margin-top: 9px; gap: 7px; }.waypoint-actions { display: grid; grid-template-columns: 1fr 1fr; gap: 5px; margin-top: 9px; }.waypoint-actions button { border: 1px solid #334155; border-radius: 4px; padding: 6px 4px; background: #111827; color: #cbd5e1; font-size: .66rem; cursor: pointer; }.waypoint-actions button:hover { border-color: #22d3ee; color: #67e8f9; }.waypoint-actions .danger-action:hover { border-color: #fb7185; color: #fda4af; }.simulation-status { margin-top: 9px; color: #fde68a; font-size: .7rem; }
.validation-report { margin-top: 12px; padding-top: 10px; border-top: 1px solid #263449; }.validation-summary { display: flex; align-items: center; gap: 6px; font-size: .72rem; }.validation-summary span { margin-left: auto; color: #94a3b8; font-size: .62rem; }.status-aprovado { color: #86efac; }.status-aviso { color: #fbbf24; }.status-bloqueado { color: #fb7185; }.validation-rule { display: flex; gap: 6px; margin-top: 6px; color: #cbd5e1; font-size: .64rem; line-height: 1.25; }.validation-rule i { margin-top: 1px; }.validation-rule span { display: flex; flex-direction: column; gap: 2px; }.validation-rule strong { color: #94a3b8; font-size: .61rem; text-transform: uppercase; }.rule-aprovado { color: #86efac; }.rule-aviso { color: #fbbf24; }.rule-bloqueado { color: #fb7185; }
:deep(.waypoint-marker) { display: grid; place-items: center; border: 2px solid #052e16; border-radius: 50%; background: #4ade80; color: #052e16; font-size: 11px; font-weight: 800; }.waypoint-marker.selected { background: #facc15; border-color: #713f12; transform: scale(1.22); z-index: 1000 !important; }.waypoint-row.selected { background: #164e63; outline: 1px solid #22d3ee; }.takeoff-label { border: 0; background: #0f172a; color: #fbbf24; box-shadow: none; font-weight: 700; }.takeoff-label::before { display: none; }
@media (max-width: 900px) { .planner-panel { width: 320px; }.tool-button span { display: none; }.tool-button { width: 34px; justify-content: center; } }
@media (max-width: 680px) { .planner-header { height: 58px; padding: 0 10px; }.planner-actions .save-state { display: none; }.planner-body { flex-direction: column; }.planner-map-wrap { min-height: 48vh; flex: 0 0 48vh; }.planner-panel { width: 100%; flex: 1; }.map-toolbar { left: 8px; top: 8px; }.map-legend { left: 8px; bottom: 8px; } }
</style>
