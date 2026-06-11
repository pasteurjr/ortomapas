<template>
  <div class="layer-panel">
    <div class="panel-header">
      <h3><i class="pi pi-layers"></i> Camadas</h3>
      <span class="layer-count" v-if="layers.length > 0">{{ layers.length }}</span>
    </div>

    <div v-if="layers.length === 0" class="empty-state">
      <i class="pi pi-info-circle"></i>
      <span>Nenhuma camada ativa</span>
    </div>

    <div class="layers-list" ref="layersList">
      <div
        v-for="(layer, index) in layers"
        :key="layer.id"
        class="layer-item"
        :class="{ hidden: !layer.visible }"
        draggable="true"
        @dragstart="onDragStart(index, $event)"
        @dragover.prevent="onDragOver(index, $event)"
        @drop="onDrop(index)"
        @dragend="onDragEnd"
      >
        <div class="layer-drag-handle" title="Arrastar para reordenar">
          <i class="pi pi-bars"></i>
        </div>

        <button
          class="icon-btn visibility-btn"
          @click="toggleVisibility(layer)"
          :title="layer.visible ? 'Ocultar camada' : 'Mostrar camada'"
        >
          <i :class="layer.visible ? 'pi pi-eye' : 'pi pi-eye-slash'"></i>
        </button>

        <div class="layer-info" @click="toggleExpanded(layer.id)">
          <div class="layer-type-icon">
            <i :class="layerTypeIcon(layer.type)"></i>
          </div>
          <div class="layer-details">
            <span class="layer-name" :class="{ dimmed: !layer.visible }">{{ layer.name }}</span>
            <span class="layer-type-label">{{ layerTypeLabel(layer.type) }}</span>
          </div>
        </div>

        <div class="layer-actions">
          <button class="icon-btn" @click="zoomToLayer(layer)" title="Zoom para camada">
            <i class="pi pi-search"></i>
          </button>
          <button class="icon-btn remove-btn" @click="removeLayer(layer)" title="Remover camada">
            <i class="pi pi-times"></i>
          </button>
        </div>

        <!-- Expanded controls -->
        <div class="layer-expanded" v-if="expandedLayer === layer.id">
          <div class="opacity-control">
            <label>Opacidade: {{ Math.round(layer.opacity * 100) }}%</label>
            <input
              type="range"
              min="0"
              max="100"
              :value="Math.round(layer.opacity * 100)"
              @input="setOpacity(layer, parseInt($event.target.value) / 100)"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- Quick actions -->
    <div v-if="layers.length > 1" class="panel-actions">
      <button class="panel-action-btn" @click="showAllLayers" title="Mostrar todas">
        <i class="pi pi-eye"></i> Todas
      </button>
      <button class="panel-action-btn" @click="hideAllLayers" title="Ocultar todas">
        <i class="pi pi-eye-slash"></i> Nenhuma
      </button>
      <button class="panel-action-btn danger" @click="removeAllLayers" title="Remover todas">
        <i class="pi pi-trash"></i> Limpar
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useMapStore } from '../stores/mapStore'

const mapStore = useMapStore()

const emit = defineEmits(['zoom-to', 'toggle-layer', 'remove-layer'])

const layers = computed(() => mapStore.activeLayers)
const expandedLayer = ref(null)
const dragIndex = ref(null)
const dragOverIndex = ref(null)

function layerTypeIcon(type) {
  const map = {
    ortomapa: 'pi pi-image',
    analysis: 'pi pi-chart-bar',
    annotation: 'pi pi-pencil',
    basemap: 'pi pi-map',
  }
  return map[type] || 'pi pi-circle'
}

function layerTypeLabel(type) {
  const map = {
    ortomapa: 'Ortomapa',
    analysis: 'Analise',
    annotation: 'Anotacao',
    basemap: 'Base',
  }
  return map[type] || type
}

function toggleVisibility(layer) {
  mapStore.toggleLayer(layer.id)
  emit('toggle-layer', layer)
}

function toggleExpanded(layerId) {
  expandedLayer.value = expandedLayer.value === layerId ? null : layerId
}

function setOpacity(layer, opacity) {
  mapStore.setLayerOpacity(layer.id, opacity)
}

function zoomToLayer(layer) {
  emit('zoom-to', layer)
}

function removeLayer(layer) {
  mapStore.removeLayer(layer.id)
  emit('remove-layer', layer)
  if (expandedLayer.value === layer.id) {
    expandedLayer.value = null
  }
}

function showAllLayers() {
  layers.value.forEach((l) => {
    if (!l.visible) mapStore.toggleLayer(l.id)
  })
}

function hideAllLayers() {
  layers.value.forEach((l) => {
    if (l.visible) mapStore.toggleLayer(l.id)
  })
}

function removeAllLayers() {
  mapStore.clearAllLayers()
  expandedLayer.value = null
}

// Drag and drop reorder
function onDragStart(index, event) {
  dragIndex.value = index
  event.dataTransfer.effectAllowed = 'move'
  event.dataTransfer.setData('text/plain', index.toString())
}

function onDragOver(index, event) {
  dragOverIndex.value = index
  event.dataTransfer.dropEffect = 'move'
}

function onDrop(targetIndex) {
  if (dragIndex.value === null || dragIndex.value === targetIndex) return
  const item = mapStore.activeLayers.splice(dragIndex.value, 1)[0]
  mapStore.activeLayers.splice(targetIndex, 0, item)
  dragIndex.value = null
  dragOverIndex.value = null
}

function onDragEnd() {
  dragIndex.value = null
  dragOverIndex.value = null
}
</script>

<style scoped>
.layer-panel {
  padding: 4px 0;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 8px 6px;
}

.panel-header h3 {
  margin: 0;
  font-size: 0.8rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #a6adc8;
  display: flex;
  align-items: center;
  gap: 6px;
}

.layer-count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 20px;
  height: 20px;
  padding: 0 5px;
  border-radius: 10px;
  background: #89b4fa;
  color: #1e1e2e;
  font-size: 0.65rem;
  font-weight: 700;
}

.empty-state {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 16px 12px;
  color: #585b70;
  font-size: 0.78rem;
  justify-content: center;
}

.layers-list {
  padding: 0 4px;
}

.layer-item {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px;
  padding: 6px 6px;
  border-radius: 6px;
  margin-bottom: 2px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid transparent;
  transition: all 0.15s;
  cursor: default;
}

.layer-item:hover {
  background: #313244;
  border-color: #45475a;
}

.layer-item.hidden {
  opacity: 0.6;
}

.layer-drag-handle {
  cursor: grab;
  color: #45475a;
  font-size: 0.7rem;
  padding: 2px;
  flex-shrink: 0;
}

.layer-drag-handle:active {
  cursor: grabbing;
}

.layer-item:hover .layer-drag-handle {
  color: #6c7086;
}

.icon-btn {
  background: none;
  border: none;
  cursor: pointer;
  color: #6c7086;
  font-size: 0.78rem;
  padding: 3px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s;
  flex-shrink: 0;
}

.icon-btn:hover {
  color: #cdd6f4;
  background: rgba(255, 255, 255, 0.05);
}

.visibility-btn {
  color: #89b4fa;
}

.layer-item.hidden .visibility-btn {
  color: #45475a;
}

.remove-btn:hover {
  color: #f38ba8;
}

.layer-info {
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
}

.layer-type-icon {
  width: 22px;
  height: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  background: rgba(137, 180, 250, 0.1);
  color: #89b4fa;
  font-size: 0.68rem;
  flex-shrink: 0;
}

.layer-details {
  flex: 1;
  min-width: 0;
}

.layer-name {
  display: block;
  font-size: 0.78rem;
  font-weight: 500;
  color: #cdd6f4;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.layer-name.dimmed {
  color: #585b70;
}

.layer-type-label {
  display: block;
  font-size: 0.65rem;
  color: #585b70;
}

.layer-actions {
  display: flex;
  gap: 2px;
  flex-shrink: 0;
}

.layer-expanded {
  width: 100%;
  padding: 6px 4px 2px 30px;
}

.opacity-control {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.opacity-control label {
  font-size: 0.7rem;
  color: #a6adc8;
}

.opacity-control input[type="range"] {
  width: 100%;
  height: 4px;
  accent-color: #89b4fa;
  cursor: pointer;
}

.panel-actions {
  display: flex;
  gap: 4px;
  padding: 8px 8px 4px;
  border-top: 1px solid #313244;
  margin-top: 4px;
}

.panel-action-btn {
  flex: 1;
  padding: 4px 6px;
  border: 1px solid #313244;
  border-radius: 4px;
  background: transparent;
  color: #a6adc8;
  font-size: 0.68rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 3px;
  transition: all 0.15s;
}

.panel-action-btn:hover {
  background: #313244;
  color: #cdd6f4;
}

.panel-action-btn.danger:hover {
  border-color: #f38ba8;
  color: #f38ba8;
}
</style>
