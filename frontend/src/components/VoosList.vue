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
        :disabled="!projectStore.canEdit"
      />
    </div>

    <input ref="photoInput" type="file" accept=".jpg,.jpeg,.tif,.tiff" multiple hidden @change="uploadPhotos" />

    <p v-if="feedback" class="upload-feedback" :class="feedbackType" role="status">{{ feedback }}</p>

    <Dialog v-model:visible="showOdmDialog" header="Processar fotos no ODM" :modal="true" :style="{ width: '420px' }">
      <p class="dialog-help">{{ selectedFiles.length }} foto(s), {{ selectedFilesSizeMb }} MB, para o voo {{ selectedVoo?.id }}.</p>
      <p class="dialog-note">Padrão: resolução original e reconstrução completa, com DSM, DTM e nuvem LAZ. A opção rápida reduz o tempo e pode diminuir a densidade da nuvem.</p>
      <p v-if="selectedFiles.length < 3" class="validation-warning" role="alert">Selecione ao menos 3 imagens para a fotogrametria.</p>
      <div class="form-group"><label>Redimensionar para (px, 0 = original)</label><InputText v-model.number="odmResize" type="number" min="0" class="w-full" /></div>
      <div class="form-group"><label><input v-model="odmFast" type="checkbox" /> Gerar ortofoto rápida</label></div>
      <div class="form-group"><label><input v-model="odmDsm" type="checkbox" /> Gerar DSM (superfície)</label></div>
      <div class="form-group"><label><input v-model="odmDtm" type="checkbox" /> Gerar DTM (terreno)</label></div>
      <div class="form-group"><label><input v-model="odmPointCloud" type="checkbox" /> Gerar nuvem de pontos LAZ</label></div>
      <div class="form-group"><label><input v-model="odmSkip3d" type="checkbox" /> Não gerar modelo 3D texturizado</label></div>
      <template #footer><Button label="Cancelar" severity="secondary" @click="showOdmDialog = false" /><Button label="Iniciar processamento" icon="pi pi-play" :loading="odmLoading" @click="submitOdm" /></template>
    </Dialog>

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
          <span v-if="voo.app_voo" class="meta-item" :title="'Aplicativo: ' + voo.app_voo">
            <i class="pi pi-send"></i> {{ voo.app_voo }}
          </span>
          <span v-if="voo.altitude_voo_m" class="meta-item" :title="'Altitude: ' + voo.altitude_voo_m + 'm'">
            <i class="pi pi-arrow-up"></i> {{ voo.altitude_voo_m }}m
          </span>
          <span v-if="voo.num_fotos" class="meta-item">
            <i class="pi pi-camera"></i> {{ voo.num_fotos }}
          </span>
        </div>
      </div>
      <Button
        icon="pi pi-upload"
        label="Fotos"
        severity="info"
        text
        size="small"
        title="Enviar fotos deste voo para o ODM"
        :disabled="!projectStore.canEdit"
        @click="choosePhotos(voo)"
      />
      <Button
        icon="pi pi-trash"
        severity="danger"
        text
        size="small"
        @click="removeVoo(voo)"
        :disabled="!projectStore.canEdit"
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
        <label>Aplicativo de voo</label>
        <InputText v-model="newVoo.app_voo" placeholder="Ex: DJI Fly" class="w-full" />
      </div>
      <div class="form-group">
        <label>Altitude de voo (m)</label>
        <InputText v-model.number="newVoo.altitude_voo_m" type="number" placeholder="120" class="w-full" />
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
import { getVoos, createVoo, deleteVoo, createOdmTask } from '../api/client'
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
const photoInput = ref(null)
const selectedVoo = ref(null)
const selectedFiles = ref([])
const showOdmDialog = ref(false)
const odmLoading = ref(false)
const feedback = ref('')
const feedbackType = ref('success')
const odmResize = ref(0)
const odmFast = ref(false)
const odmSkip3d = ref(false)
const odmDsm = ref(true)
const odmDtm = ref(true)
const odmPointCloud = ref(true)
const selectedFilesSizeMb = ref('0.0')
const newVoo = ref({
  data_voo: '',
  app_voo: '',
  altitude_voo_m: null,
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
    newVoo.value = { data_voo: '', app_voo: '', altitude_voo_m: null, num_fotos: null, area_coberta_ha: null, gsd_cm: null, observacoes: '' }
    showNewVoo.value = false
    feedbackType.value = 'success'
    feedback.value = 'Voo cadastrado no projeto.'
    await fetchVoos()
  } catch (e) {
    feedbackType.value = 'error'
    feedback.value = e.response?.data?.detail || 'Falha ao cadastrar voo.'
  }
}

async function removeVoo(voo) {
  try {
    await deleteVoo(voo.id)
    await fetchVoos()
  } catch (e) {
    feedbackType.value = 'error'
    feedback.value = e.response?.data?.detail || 'Falha ao remover voo.'
  }
}

function choosePhotos(voo) {
  selectedVoo.value = voo
  photoInput.value?.click()
}

async function uploadPhotos(event) {
  const files = Array.from(event.target.files || [])
  if (!files.length || !selectedVoo.value || !projectStore.activeProject) return
  selectedFiles.value = files
  selectedFilesSizeMb.value = (files.reduce((sum, file) => sum + file.size, 0) / 1024 / 1024).toFixed(1)
  feedback.value = ''
  showOdmDialog.value = true
  event.target.value = ''
}

async function submitOdm() {
  if (!selectedFiles.value.length || !selectedVoo.value || !projectStore.activeProject) return
  if (selectedFiles.value.length < 3) return
  const form = new FormData()
  selectedFiles.value.forEach((file) => form.append('images', file))
  form.append('projeto_id', projectStore.activeProject.id)
  form.append('voo_id', selectedVoo.value.id)
  form.append('name', `${projectStore.activeProject.nome} - Voo ${selectedVoo.value.id}`)
  const options = []
  if (odmResize.value) options.push({ name: 'resize-to', value: Number(odmResize.value) })
  if (odmFast.value) options.push({ name: 'fast-orthophoto', value: true })
  if (odmSkip3d.value) options.push({ name: 'skip-3dmodel', value: true })
  if (odmDsm.value) options.push({ name: 'dsm', value: true })
  if (odmDtm.value) options.push({ name: 'dtm', value: true })
  if (odmPointCloud.value) options.push({ name: 'pc-las', value: true })
  form.append('options', JSON.stringify(options))
  odmLoading.value = true
  try {
    const { data } = await createOdmTask(form)
    showOdmDialog.value = false
    feedbackType.value = 'success'
    feedback.value = `Processamento iniciado no NodeODM (${data.task.uuid}). ${data.images_count} fotos vinculadas ao voo ${selectedVoo.value.id}.`
  } catch (e) {
    feedbackType.value = 'error'
    feedback.value = e.response?.data?.detail || 'Falha ao iniciar processamento ODM.'
  } finally {
    odmLoading.value = false
  }
}

watch(() => projectStore.activeProject, fetchVoos, { immediate: true })
</script>

<style scoped>
.voos-list {
  margin-top: 8px;
}

.upload-feedback,.validation-warning { margin: 8px 0; padding: 8px 10px; border-left: 3px solid #16a34a; background: color-mix(in srgb, #16a34a 10%, transparent); font-size: .8rem; overflow-wrap: anywhere; }
.dialog-note { margin: 8px 0; color: var(--text-dim); font-size: .78rem; line-height: 1.45; }
.upload-feedback.error,.validation-warning { border-left-color: #dc2626; background: color-mix(in srgb, #dc2626 10%, transparent); }

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
