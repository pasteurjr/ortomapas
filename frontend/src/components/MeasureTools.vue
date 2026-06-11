<template>
  <div class="measure-overlay" v-if="mapStore.measureMode">
    <div class="measure-panel">
      <div class="measure-header">
        <h4>
          <i :class="mapStore.measureMode === 'distance' ? 'pi pi-arrows-h' : 'pi pi-stop'"></i>
          {{ mapStore.measureMode === 'distance' ? 'Medir Distancia' : 'Medir Area' }}
        </h4>
        <button class="close-btn" @click="closeMeasure">
          <i class="pi pi-times"></i>
        </button>
      </div>

      <div class="measure-modes">
        <button
          class="mode-btn"
          :class="{ active: mapStore.measureMode === 'distance' }"
          @click="mapStore.setMeasureMode('distance')"
        >
          <i class="pi pi-arrows-h"></i> Distancia
        </button>
        <button
          class="mode-btn"
          :class="{ active: mapStore.measureMode === 'area' }"
          @click="mapStore.setMeasureMode('area')"
        >
          <i class="pi pi-stop"></i> Area
        </button>
      </div>

      <!-- Distance result -->
      <div class="measure-result" v-if="mapStore.measureMode === 'distance'">
        <div class="result-label">Distancia Total</div>
        <div class="result-value">{{ formattedDistance }}</div>
        <div class="result-detail" v-if="segments.length > 0">
          <div v-for="(seg, idx) in segments" :key="idx" class="segment">
            Segmento {{ idx + 1 }}: {{ formatDist(seg) }}
          </div>
        </div>
        <div class="result-detail" v-if="points.length > 0">
          {{ points.length }} ponto(s) marcado(s)
        </div>
      </div>

      <!-- Area result -->
      <div class="measure-result" v-if="mapStore.measureMode === 'area'">
        <div class="result-label">Area</div>
        <div class="result-value">{{ formattedArea }}</div>
        <div class="result-detail">Perimetro: {{ formattedPerimeter }}</div>
        <div class="result-detail" v-if="points.length > 0">
          {{ points.length }} vertice(s)
        </div>
      </div>

      <div class="measure-hint">
        Clique no mapa para adicionar pontos.
        <span v-if="mapStore.measureMode === 'area'">Minimo 3 pontos para calcular area.</span>
      </div>

      <div class="measure-actions">
        <button class="action-btn undo" @click="undoLastPoint" :disabled="points.length === 0">
          <i class="pi pi-undo"></i> Desfazer
        </button>
        <button class="action-btn clear" @click="clearMeasurements">
          <i class="pi pi-eraser"></i> Limpar
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useMapStore } from '../stores/mapStore'

const props = defineProps({
  mapMeasurePoints: {
    type: Array,
    default: () => [],
  },
})

const emit = defineEmits(['clear-points', 'undo-point'])

const mapStore = useMapStore()

// Use the map's measure points passed from the parent (MapViewer)
const points = computed(() => props.mapMeasurePoints)

const segments = computed(() => {
  const pts = points.value
  const segs = []
  for (let i = 1; i < pts.length; i++) {
    segs.push(haversineDistance(pts[i - 1], pts[i]))
  }
  return segs
})

const totalDistance = computed(() => segments.value.reduce((a, b) => a + b, 0))

const formattedDistance = computed(() => formatDist(totalDistance.value))

const formattedArea = computed(() => {
  const pts = points.value
  if (pts.length < 3) return '0 m\u00B2'
  const area = polygonArea(pts)
  if (area > 10000) return `${(area / 10000).toFixed(4)} ha`
  return `${area.toFixed(2)} m\u00B2`
})

const formattedPerimeter = computed(() => {
  const pts = points.value
  if (pts.length < 2) return '0 m'
  let perim = 0
  for (let i = 1; i < pts.length; i++) {
    perim += haversineDistance(pts[i - 1], pts[i])
  }
  if (pts.length > 2) {
    perim += haversineDistance(pts[pts.length - 1], pts[0])
  }
  return formatDist(perim)
})

function formatDist(meters) {
  if (meters >= 1000) return `${(meters / 1000).toFixed(3)} km`
  return `${meters.toFixed(2)} m`
}

function haversineDistance(p1, p2) {
  const R = 6371000
  const toRad = (d) => (d * Math.PI) / 180
  const dLat = toRad(p2[0] - p1[0])
  const dLng = toRad(p2[1] - p1[1])
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(toRad(p1[0])) * Math.cos(toRad(p2[0])) * Math.sin(dLng / 2) ** 2
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
}

function polygonArea(pts) {
  const toMeters = (lat, lng, refLat, refLng) => {
    const R = 6371000
    const toRad = (d) => (d * Math.PI) / 180
    const x = (lng - refLng) * toRad(1) * R * Math.cos(toRad(refLat))
    const y = (lat - refLat) * toRad(1) * R
    return [x, y]
  }
  const refLat = pts[0][0]
  const refLng = pts[0][1]
  const projected = pts.map((p) => toMeters(p[0], p[1], refLat, refLng))
  let area = 0
  for (let i = 0; i < projected.length; i++) {
    const j = (i + 1) % projected.length
    area += projected[i][0] * projected[j][1]
    area -= projected[j][0] * projected[i][1]
  }
  return Math.abs(area) / 2
}

function closeMeasure() {
  mapStore.setMeasureMode(null)
  emit('clear-points')
}

function clearMeasurements() {
  emit('clear-points')
}

function undoLastPoint() {
  emit('undo-point')
}

// Clear points when measure mode changes
watch(
  () => mapStore.measureMode,
  (newMode, oldMode) => {
    if (newMode && oldMode && newMode !== oldMode) {
      emit('clear-points')
    }
  }
)
</script>

<style scoped>
.measure-overlay {
  position: absolute;
  top: 12px;
  left: 12px;
  z-index: 800;
}

.measure-panel {
  background: #1e1e2e;
  border: 1px solid #313244;
  border-radius: 10px;
  padding: 12px;
  width: 260px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4);
}

.measure-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}

.measure-header h4 {
  margin: 0;
  font-size: 0.85rem;
  color: #cdd6f4;
  display: flex;
  align-items: center;
  gap: 6px;
}

.close-btn {
  background: none;
  border: none;
  color: #6c7086;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  transition: all 0.15s;
}

.close-btn:hover {
  color: #cdd6f4;
  background: #313244;
}

.measure-modes {
  display: flex;
  gap: 4px;
  margin-bottom: 10px;
}

.mode-btn {
  flex: 1;
  padding: 6px;
  border: 1px solid #313244;
  border-radius: 6px;
  background: transparent;
  color: #a6adc8;
  font-size: 0.75rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  transition: all 0.15s;
}

.mode-btn:hover {
  background: #313244;
}

.mode-btn.active {
  background: #89b4fa;
  color: #1e1e2e;
  border-color: #89b4fa;
  font-weight: 600;
}

.measure-result {
  background: rgba(245, 158, 11, 0.08);
  border: 1px solid rgba(245, 158, 11, 0.2);
  border-radius: 8px;
  padding: 10px;
  margin-bottom: 10px;
}

.result-label {
  font-size: 0.7rem;
  color: #a6adc8;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 2px;
}

.result-value {
  font-size: 1.2rem;
  font-weight: 700;
  color: #f59e0b;
  font-family: 'JetBrains Mono', monospace;
}

.result-detail {
  font-size: 0.72rem;
  color: #a6adc8;
  margin-top: 4px;
}

.segment {
  padding: 1px 0;
}

.measure-hint {
  font-size: 0.72rem;
  color: #585b70;
  margin-bottom: 10px;
  font-style: italic;
  line-height: 1.4;
}

.measure-actions {
  display: flex;
  gap: 6px;
}

.action-btn {
  flex: 1;
  padding: 6px;
  border: 1px solid #313244;
  border-radius: 6px;
  background: transparent;
  color: #a6adc8;
  font-size: 0.75rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  transition: all 0.15s;
}

.action-btn:hover:not(:disabled) {
  background: #313244;
  color: #cdd6f4;
}

.action-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.action-btn.clear:hover:not(:disabled) {
  border-color: #f38ba8;
  color: #f38ba8;
}
</style>
