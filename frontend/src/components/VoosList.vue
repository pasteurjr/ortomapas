<template>
  <div class="voos-list">
    <div class="section-header">
      <h3 class="section-title">
        <i class="pi pi-send"></i> Voos
        <Badge :value="voos.length" severity="info" />
      </h3>
      <Button
        icon="pi pi-plus"
        label="Novo"
        size="small"
        severity="success"
        @click="showNewVoo = true"
        :disabled="!projectStore.activeProject"
      />
    </div>

    <div v-if="loading" class="loading-state">
      <ProgressSpinner style="width: 20px; height: 20px" strokeWidth="4" />
      <span>Carregando...</span>
    </div>

    <div v-if="!loading && voos.length === 0" class="empty-state">
      Nenhum voo registrado
    </div>

    <div
      v-for="voo in voos"
      :key="voo.id"
      class="voo-item"
    >
      <div class="voo-icon">
        <i class="pi pi-send"></i>
      </div>
      <div class="voo-info">
        <div class="voo-date">{{ voo.data_voo || 'Sem data' }}</div>
        <div class="voo-meta">
          <span v-if="voo.drone" class="meta-item" :title="'Drone: ' + voo.drone">
            <i class="pi pi-video"></i> {{ voo.drone }}
          </span>
          <span v-if="voo.altitude_voo" class="meta-item" :title="'Altitude: ' + voo.altitude_voo + 'm'">
            <i class="pi pi-arrow-up"></i> {{ voo.altitude_voo }}m
          </span>
          <span v-if="voo.num_fotos" class="meta-item">
            <i class="pi pi-camera"></i> {{ voo.num_fotos }}
          </span>
        </div>
      </div>
      <Button
        icon="pi pi-trash"
        severity="danger"
        text
        size="small"
        @click="removeVoo(voo)"
      />
    </div>

    <!-- New Voo Dialog -->
    <Dialog
      v-model:visible="showNewVoo"
      header="Novo Voo"
      :modal="true"
      :style="{ width: '420px' }"
    >
      <div class="form-group">
        <label>Data do Voo</label>
        <InputText v-model="newVoo.data_voo" type="date" class="w-full" />
      </div>
      <div class="form-group">
        <label>Drone</label>
        <InputText v-model="newVoo.drone" placeholder="Ex: DJI Mini 3" class="w-full" />
      </div>
      <div class="form-group">
        <label>Altitude de voo (m)</label>
        <InputText v-model.number="newVoo.altitude_voo" type="number" placeholder="120" class="w-full" />
      </div>
      <div class="form-group">
        <label>Numero de fotos</label>
        <InputText v-model.number="newVoo.num_fotos" type="number" class="w-full" />
      </div>
      <div class="form-group">
        <label>Area coberta (ha)</label>
        <InputText v-model.number="newVoo.area_coberta_ha" type="number" step="0.1" class="w-full" />
      </div>
      <div class="form-group">
        <label>GSD (cm/px)</label>
        <InputText v-model.number="newVoo.gsd_cm" type="number" step="0.01" class="w-full" />
      </div>
      <div class="form-group">
        <label>Observacoes</label>
        <Textarea v-model="newVoo.observacoes" rows="2" class="w-full" />
      </div>
      <template #footer>
        <Button label="Cancelar" severity="secondary" @click="showNewVoo = false" />
        <Button label="Criar" icon="pi pi-check" @click="addVoo" />
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useProjectStore } from '../stores/projectStore'
import { getVoos, createVoo, deleteVoo } from '../api/client'
import Button from 'primevue/button'
import Badge from 'primevue/badge'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import ProgressSpinner from 'primevue/progressspinner'

const projectStore = useProjectStore()
const voos = ref([])
const loading = ref(false)
const showNewVoo = ref(false)
const newVoo = ref({
  data_voo: '',
  drone: '',
  altitude_voo: null,
  num_fotos: null,
  area_coberta_ha: null,
  gsd_cm: null,
  observacoes: '',
})

async function fetchVoos() {
  if (!projectStore.activeProject) {
    voos.value = []
    return
  }
  loading.value = true
  try {
    const res = await getVoos(projectStore.activeProject.id)
    voos.value = res.data.voos || res.data || []
  } catch (e) {
    console.error('Erro ao carregar voos:', e)
  } finally {
    loading.value = false
  }
}

async function addVoo() {
  if (!projectStore.activeProject) return
  try {
    await createVoo({
      projeto_id: projectStore.activeProject.id,
      ...newVoo.value,
    })
    newVoo.value = { data_voo: '', drone: '', altitude_voo: null, num_fotos: null, area_coberta_ha: null, gsd_cm: null, observacoes: '' }
    showNewVoo.value = false
    await fetchVoos()
  } catch (e) {
    console.error('Erro ao criar voo:', e)
  }
}

async function removeVoo(voo) {
  try {
    await deleteVoo(voo.id)
    await fetchVoos()
  } catch (e) {
    console.error('Erro ao deletar voo:', e)
  }
}

watch(() => projectStore.activeProject, fetchVoos, { immediate: true })
</script>

<style scoped>
.voos-list {
  margin-top: 8px;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 4px;
  margin-bottom: 6px;
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
  margin: 0;
}

.loading-state {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  color: var(--text-dim);
  font-size: 0.85rem;
}

.empty-state {
  text-align: center;
  padding: 12px;
  color: var(--text-dim);
  font-size: 0.8rem;
}

.voo-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px;
  border-radius: 6px;
  transition: background 0.15s;
  margin-bottom: 2px;
}

.voo-item:hover {
  background: var(--sidebar-hover);
}

.voo-icon {
  width: 28px;
  height: 28px;
  border-radius: 6px;
  background: var(--sidebar-hover);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #89b4fa;
  flex-shrink: 0;
  font-size: 0.8rem;
}

.voo-info {
  flex: 1;
  min-width: 0;
}

.voo-date {
  font-weight: 600;
  font-size: 0.82rem;
  color: var(--text);
}

.voo-meta {
  display: flex;
  gap: 8px;
  margin-top: 2px;
}

.meta-item {
  font-size: 0.7rem;
  color: var(--text-dim);
  display: flex;
  align-items: center;
  gap: 3px;
}

.form-group {
  margin-bottom: 10px;
}

.form-group label {
  display: block;
  font-size: 0.82rem;
  font-weight: 500;
  margin-bottom: 4px;
  color: var(--text);
}

.w-full {
  width: 100%;
}
</style>
