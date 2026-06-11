<template>
  <div class="ortomapa-card" @click="$emit('select', ortomapa)">
    <div class="card-thumbnail">
      <img
        v-if="ortomapa.thumbnail"
        :src="`/api/ortomapas/${ortomapa.id}/thumbnail`"
        alt="thumbnail"
      />
      <div v-else class="no-thumb">
        <i class="pi pi-image"></i>
      </div>
    </div>
    <div class="card-body">
      <div class="card-title">{{ ortomapa.nome }}</div>
      <div class="card-meta">
        <Badge :value="ortomapa.tipo || 'RGB'" :severity="tipoBadge(ortomapa.tipo)" />
        <span v-if="ortomapa.resolucao" class="resolution">{{ ortomapa.resolucao }}cm/px</span>
      </div>
      <div class="card-date" v-if="ortomapa.data_voo">
        <i class="pi pi-calendar"></i> {{ formatDate(ortomapa.data_voo) }}
      </div>
    </div>
    <div class="card-actions">
      <button
        class="action-btn"
        :class="{ active: isVisible }"
        @click.stop="toggleVisibility"
        title="Visibilidade"
      >
        <i :class="isVisible ? 'pi pi-eye' : 'pi pi-eye-slash'"></i>
      </button>
      <button class="action-btn" @click.stop="analyzeOrtomapa" title="Analisar">
        <i class="pi pi-chart-bar"></i>
      </button>
      <button class="action-btn" @click.stop="$emit('export', ortomapa)" title="Exportar">
        <i class="pi pi-download"></i>
      </button>
      <button class="action-btn danger" @click.stop="$emit('delete', ortomapa)" title="Excluir">
        <i class="pi pi-trash"></i>
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed, inject } from 'vue'
import { useMapStore } from '../stores/mapStore'
import Badge from 'primevue/badge'

const props = defineProps({
  ortomapa: { type: Object, required: true },
})

defineEmits(['select', 'export', 'delete'])

const mapStore = useMapStore()
const showAnalysisForm = inject('showAnalysisForm')

const isVisible = computed(() => mapStore.isLayerVisible(`orto-${props.ortomapa.id}`))

function toggleVisibility() {
  const layerId = `orto-${props.ortomapa.id}`
  if (mapStore.activeLayers.find((l) => l.id === layerId)) {
    mapStore.toggleLayer(layerId)
  } else {
    mapStore.addLayer({
      id: layerId,
      name: props.ortomapa.nome,
      type: 'ortomapa',
      sourceId: props.ortomapa.id,
    })
  }
}

function analyzeOrtomapa() {
  if (showAnalysisForm) showAnalysisForm.value = true
}

function tipoBadge(tipo) {
  const map = { RGB: 'info', NDVI: 'success', DSM: 'warn', DTM: 'warn', multispectral: 'secondary' }
  return map[tipo] || 'info'
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return d.toLocaleDateString('pt-BR')
}
</script>

<style scoped>
.ortomapa-card {
  display: flex;
  gap: 8px;
  padding: 8px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.15s;
  border: 1px solid transparent;
}

.ortomapa-card:hover {
  background: var(--sidebar-hover);
  border-color: var(--border);
}

.card-thumbnail {
  width: 48px;
  height: 48px;
  border-radius: 6px;
  overflow: hidden;
  flex-shrink: 0;
  background: var(--sidebar-hover);
}

.card-thumbnail img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.no-thumb {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-dim);
}

.card-body {
  flex: 1;
  min-width: 0;
}

.card-title {
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.card-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 3px;
}

.resolution {
  font-size: 0.7rem;
  color: var(--text-dim);
}

.card-date {
  font-size: 0.7rem;
  color: var(--text-dim);
  margin-top: 2px;
  display: flex;
  align-items: center;
  gap: 4px;
}

.card-actions {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex-shrink: 0;
}

.action-btn {
  width: 24px;
  height: 24px;
  border: none;
  background: transparent;
  color: var(--text-dim);
  cursor: pointer;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  transition: all 0.15s;
}

.action-btn:hover {
  background: var(--sidebar-hover);
  color: var(--text);
}

.action-btn.active {
  color: var(--accent);
}

.action-btn.danger:hover {
  color: var(--danger);
}
</style>
