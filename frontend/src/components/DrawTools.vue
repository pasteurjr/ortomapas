<template>
  <div class="draw-tools">
    <h3 class="section-title"><i class="pi pi-pencil"></i> Anotacoes</h3>

    <div class="draw-buttons">
      <Button
        icon="pi pi-map-marker"
        :severity="mapStore.drawMode === 'point' ? 'success' : 'secondary'"
        size="small"
        @click="setMode('point')"
        title="Ponto"
        v-tooltip.bottom="'Ponto'"
      />
      <Button
        icon="pi pi-minus"
        :severity="mapStore.drawMode === 'line' ? 'success' : 'secondary'"
        size="small"
        @click="setMode('line')"
        title="Linha"
        v-tooltip.bottom="'Linha'"
      />
      <Button
        icon="pi pi-stop"
        :severity="mapStore.drawMode === 'polygon' ? 'success' : 'secondary'"
        size="small"
        @click="setMode('polygon')"
        title="Poligono"
        v-tooltip.bottom="'Poligono'"
      />
      <Button
        icon="pi pi-clone"
        :severity="mapStore.drawMode === 'rectangle' ? 'success' : 'secondary'"
        size="small"
        @click="setMode('rectangle')"
        title="Retangulo"
        v-tooltip.bottom="'Retangulo'"
      />
      <Button
        icon="pi pi-times"
        severity="danger"
        size="small"
        @click="cancelDraw"
        title="Cancelar"
        :disabled="!mapStore.drawMode"
      />
    </div>

    <!-- Annotation Form (shown after drawing) -->
    <div v-if="showForm" class="annotation-form">
      <h4>Nova Anotacao</h4>
      <div class="form-group">
        <label>Categoria</label>
        <Select
          v-model="form.categoria"
          :options="categorias"
          optionLabel="label"
          optionValue="value"
          class="w-full"
        />
      </div>
      <div class="form-group">
        <label>Rotulo</label>
        <InputText v-model="form.rotulo" class="w-full" placeholder="Nome da anotacao" />
      </div>
      <div class="form-group">
        <label>Descricao</label>
        <Textarea v-model="form.descricao" rows="2" class="w-full" />
      </div>
      <div class="form-actions">
        <Button label="Cancelar" severity="secondary" size="small" @click="cancelAnnotation" />
        <Button label="Salvar" icon="pi pi-check" size="small" @click="saveAnnotation" />
      </div>
    </div>

    <!-- Existing Annotations -->
    <div class="annotations-list" v-if="projectStore.anotacoes.length > 0">
      <h4 class="list-title">Anotacoes Existentes ({{ projectStore.anotacoes.length }})</h4>
      <div
        v-for="anotacao in projectStore.anotacoes"
        :key="anotacao.id"
        class="annotation-item"
      >
        <div class="annotation-color" :style="{ background: catColor(anotacao.categoria) }"></div>
        <div class="annotation-info">
          <span class="annotation-label">{{ anotacao.rotulo || 'Sem rotulo' }}</span>
          <span class="annotation-cat">{{ anotacao.categoria }}</span>
        </div>
        <Button
          icon="pi pi-trash"
          severity="danger"
          text
          size="small"
          @click="deleteAnnotation(anotacao)"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useMapStore } from '../stores/mapStore'
import { useProjectStore } from '../stores/projectStore'
import { createAnotacao, deleteAnotacao as apiDeleteAnotacao } from '../api/client'
import Select from 'primevue/select'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import Button from 'primevue/button'

const mapStore = useMapStore()
const projectStore = useProjectStore()

const showForm = ref(false)
const drawnGeometry = ref(null)

const form = reactive({
  categoria: 'vegetacao',
  rotulo: '',
  descricao: '',
})

const categorias = [
  { label: 'Vegetacao', value: 'vegetacao' },
  { label: 'Construcao', value: 'construcao' },
  { label: 'Agua', value: 'agua' },
  { label: 'Solo Exposto', value: 'solo' },
  { label: 'Erosao', value: 'erosao' },
  { label: 'Infraestrutura', value: 'infraestrutura' },
]

const catColors = {
  vegetacao: '#22c55e',
  construcao: '#ef4444',
  agua: '#3b82f6',
  solo: '#a16207',
  erosao: '#f97316',
  infraestrutura: '#8b5cf6',
}

function catColor(cat) {
  return catColors[cat] || '#6b7280'
}

function setMode(mode) {
  if (mapStore.drawMode === mode) {
    mapStore.setDrawMode(null)
  } else {
    mapStore.setDrawMode(mode)
  }
}

function cancelDraw() {
  mapStore.setDrawMode(null)
  showForm.value = false
  drawnGeometry.value = null
}

// Called when a geometry is drawn on the map (from MapViewer events)
function onDrawComplete(geometry) {
  drawnGeometry.value = geometry
  showForm.value = true
  mapStore.setDrawMode(null)
}

function cancelAnnotation() {
  showForm.value = false
  drawnGeometry.value = null
  form.categoria = 'vegetacao'
  form.rotulo = ''
  form.descricao = ''
}

async function saveAnnotation() {
  if (!drawnGeometry.value || !projectStore.activeProject) return
  // Use first available ortomapa from the active project
  const ortomapa = projectStore.ortomapas[0]
  if (!ortomapa) {
    console.error('Nenhum ortomapa disponivel para vincular a anotacao')
    return
  }
  try {
    await createAnotacao({
      ortomapa_id: ortomapa.id,
      categoria: form.categoria,
      rotulo: form.rotulo,
      descricao: form.descricao,
      geometria_wkt: drawnGeometry.value,
    })
    await projectStore.fetchAnotacoes()
    cancelAnnotation()
  } catch (e) {
    console.error(e)
  }
}

async function deleteAnnotation(anotacao) {
  try {
    await apiDeleteAnotacao(anotacao.id)
    await projectStore.fetchAnotacoes()
  } catch (e) {
    console.error(e)
  }
}

defineExpose({ onDrawComplete })
</script>

<style scoped>
.draw-tools {
  margin-top: 8px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.8rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-dim);
  padding: 8px 4px;
  border-bottom: 1px solid var(--border);
  margin-bottom: 8px;
}

.draw-buttons {
  display: flex;
  gap: 4px;
  padding: 0 4px;
  margin-bottom: 8px;
}

.annotation-form {
  padding: 10px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--border);
  border-radius: 8px;
  margin: 8px 4px;
}

.annotation-form h4 {
  font-size: 0.85rem;
  margin-bottom: 8px;
  color: var(--text);
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: 8px;
}

.form-group label {
  font-size: 0.78rem;
  color: var(--text-dim);
}

.w-full {
  width: 100%;
}

.form-actions {
  display: flex;
  gap: 6px;
  justify-content: flex-end;
}

.list-title {
  font-size: 0.78rem;
  color: var(--text-dim);
  padding: 4px;
  margin-top: 8px;
  margin-bottom: 4px;
}

.annotation-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  border-radius: 4px;
  transition: background 0.15s;
}

.annotation-item:hover {
  background: var(--sidebar-hover);
}

.annotation-color {
  width: 8px;
  height: 8px;
  border-radius: 2px;
  flex-shrink: 0;
}

.annotation-info {
  flex: 1;
  min-width: 0;
}

.annotation-label {
  display: block;
  font-size: 0.8rem;
  color: var(--text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.annotation-cat {
  font-size: 0.7rem;
  color: var(--text-dim);
}

.annotations-list {
  max-height: 200px;
  overflow-y: auto;
}
</style>
