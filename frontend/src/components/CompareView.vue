<template>
  <div class="compare-view">
    <!-- Controls -->
    <div class="compare-controls">
      <div class="compare-selectors">
        <div class="selector-group">
          <label>Antes</label>
          <Select
            v-model="leftId"
            :options="ortoOptions"
            optionLabel="label"
            optionValue="value"
            placeholder="Selecionar..."
            class="compare-select"
          />
        </div>
        <div class="selector-group">
          <label>Depois</label>
          <Select
            v-model="rightId"
            :options="ortoOptions"
            optionLabel="label"
            optionValue="value"
            placeholder="Selecionar..."
            class="compare-select"
          />
        </div>
      </div>
      <div class="compare-mode-toggle">
        <Button
          :label="swipeMode ? 'Deslizar' : 'Lado a Lado'"
          :icon="swipeMode ? 'pi pi-arrows-h' : 'pi pi-columns'"
          size="small"
          severity="secondary"
          @click="swipeMode = !swipeMode"
        />
        <Button
          label="Fechar"
          icon="pi pi-times"
          size="small"
          severity="danger"
          @click="mapStore.setCompareMode(false)"
        />
      </div>
    </div>

    <!-- Swipe Mode -->
    <div v-if="swipeMode" class="swipe-container" ref="swipeContainer">
      <div class="swipe-map-left" :style="{ clipPath: `inset(0 ${100 - sliderPosition}% 0 0)` }">
        <l-map
          :zoom="mapStore.zoom"
          :center="mapStore.center"
          :useGlobalLeaflet="false"
          :zoomControl="false"
        >
          <l-tile-layer
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            :maxZoom="19"
          />
          <l-tile-layer
            v-if="leftId"
            :url="`/api/ortomapas/${leftId}/tile/{z}/{x}/{y}.png`"
            :maxZoom="22"
          />
        </l-map>
      </div>
      <div class="swipe-map-right" :style="{ clipPath: `inset(0 0 0 ${sliderPosition}%)` }">
        <l-map
          :zoom="mapStore.zoom"
          :center="mapStore.center"
          :useGlobalLeaflet="false"
          :zoomControl="false"
        >
          <l-tile-layer
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            :maxZoom="19"
          />
          <l-tile-layer
            v-if="rightId"
            :url="`/api/ortomapas/${rightId}/tile/{z}/{x}/{y}.png`"
            :maxZoom="22"
          />
        </l-map>
      </div>
      <div
        class="swipe-slider"
        :style="{ left: sliderPosition + '%' }"
        @mousedown="startDrag"
      >
        <div class="slider-handle">
          <i class="pi pi-arrows-h"></i>
        </div>
      </div>
      <div class="swipe-label left-label">Antes</div>
      <div class="swipe-label right-label">Depois</div>
    </div>

    <!-- Side by Side Mode -->
    <div v-else class="side-by-side">
      <div class="side-panel">
        <l-map
          :zoom="mapStore.zoom"
          :center="mapStore.center"
          :useGlobalLeaflet="false"
        >
          <l-tile-layer
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            :maxZoom="19"
          />
          <l-tile-layer
            v-if="leftId"
            :url="`/api/ortomapas/${leftId}/tile/{z}/{x}/{y}.png`"
            :maxZoom="22"
          />
        </l-map>
        <div class="panel-label">Antes</div>
      </div>
      <div class="side-panel">
        <l-map
          :zoom="mapStore.zoom"
          :center="mapStore.center"
          :useGlobalLeaflet="false"
        >
          <l-tile-layer
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            :maxZoom="19"
          />
          <l-tile-layer
            v-if="rightId"
            :url="`/api/ortomapas/${rightId}/tile/{z}/{x}/{y}.png`"
            :maxZoom="22"
          />
        </l-map>
        <div class="panel-label">Depois</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useMapStore } from '../stores/mapStore'
import { useProjectStore } from '../stores/projectStore'
import { LMap, LTileLayer } from '@vue-leaflet/vue-leaflet'
import Select from 'primevue/select'
import Button from 'primevue/button'

const mapStore = useMapStore()
const projectStore = useProjectStore()

const leftId = ref(null)
const rightId = ref(null)
const swipeMode = ref(true)
const sliderPosition = ref(50)
const isDragging = ref(false)
const swipeContainer = ref(null)

const ortoOptions = computed(() =>
  projectStore.ortomapas.map((o) => ({ label: o.nome, value: o.id }))
)

function startDrag(e) {
  isDragging.value = true
  document.addEventListener('mousemove', onDrag)
  document.addEventListener('mouseup', stopDrag)
}

function onDrag(e) {
  if (!isDragging.value || !swipeContainer.value) return
  const rect = swipeContainer.value.getBoundingClientRect()
  const x = e.clientX - rect.left
  const pct = (x / rect.width) * 100
  sliderPosition.value = Math.max(5, Math.min(95, pct))
}

function stopDrag() {
  isDragging.value = false
  document.removeEventListener('mousemove', onDrag)
  document.removeEventListener('mouseup', stopDrag)
}
</script>

<style scoped>
.compare-view {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.compare-controls {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  background: var(--toolbar-bg);
  border-bottom: 1px solid var(--border);
  z-index: 800;
}

.compare-selectors {
  display: flex;
  gap: 12px;
}

.selector-group {
  display: flex;
  align-items: center;
  gap: 6px;
}

.selector-group label {
  font-size: 0.8rem;
  color: var(--text-dim);
  font-weight: 500;
}

.compare-select {
  width: 180px;
}

.compare-mode-toggle {
  display: flex;
  gap: 6px;
}

/* Side by Side */
.side-by-side {
  flex: 1;
  display: flex;
}

.side-panel {
  flex: 1;
  position: relative;
}

.side-panel:first-child {
  border-right: 2px solid var(--accent);
}

.side-panel :deep(.leaflet-container) {
  width: 100%;
  height: 100%;
}

.panel-label {
  position: absolute;
  top: 8px;
  left: 8px;
  z-index: 600;
  background: var(--sidebar-bg);
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--text);
}

/* Swipe Mode */
.swipe-container {
  flex: 1;
  position: relative;
  overflow: hidden;
}

.swipe-map-left,
.swipe-map-right {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
}

.swipe-map-left :deep(.leaflet-container),
.swipe-map-right :deep(.leaflet-container) {
  width: 100%;
  height: 100%;
}

.swipe-slider {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 4px;
  background: var(--accent);
  cursor: col-resize;
  z-index: 700;
  transform: translateX(-50%);
}

.slider-handle {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 36px;
  height: 36px;
  background: var(--accent);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #000;
  font-size: 0.9rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
}

.swipe-label {
  position: absolute;
  top: 8px;
  z-index: 700;
  background: var(--sidebar-bg);
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--text);
}

.left-label {
  left: 8px;
}

.right-label {
  right: 8px;
}
</style>
