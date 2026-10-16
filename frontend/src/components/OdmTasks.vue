<template>
  <section v-if="projectStore.activeProject" class="odm-tasks">
    <div class="section-title"><i class="pi pi-cog"></i> Processamentos ODM <Badge :value="tasks.length" severity="info" /></div>
    <p v-if="error" class="odm-error" role="alert">{{ error }}</p>
    <div v-if="!tasks.length" class="empty-state">Nenhum processamento</div>
    <div v-for="task in tasks" :key="task.id" class="task-row">
      <div class="task-main"><strong>{{ statusLabel(task.status) }}</strong><small>{{ task.odm_task_id.slice(0, 8) }} · {{ task.etapa || 'Aguardando etapa' }}</small></div>
      <ProgressBar :value="Number(task.progresso || 0)" :showValue="true" />
      <div class="task-actions">
        <Button v-if="task.status === 'concluido' && orthoFor(task)" label="Abrir ortofoto" icon="pi pi-image" size="small" severity="success" @click="openOrthomosaic(task)" />
        <Button v-if="task.status === 'concluido' && pointCloudFor(task)" label="Abrir 3D" icon="pi pi-box" size="small" severity="info" @click="selectedProduct = pointCloudFor(task)" />
        <Button v-if="task.status === 'concluido' && surfaceFor(task)" :label="surfaceFor(task).tipo.toUpperCase() + ' 3D'" icon="pi pi-chart-line" size="small" severity="warn" @click="selectedSurface = surfaceFor(task)" />
        <Button v-if="task.status === 'concluido' && terrainFor(task)" label="DTM 3D" icon="pi pi-chart-line" size="small" severity="info" @click="selectedSurface = terrainFor(task)" />
        <Button v-if="task.status === 'concluido' && hasComparison(task)" label="Diferença" icon="pi pi-sliders-h" size="small" severity="secondary" @click="comparisonTask = task.id" />
        <Button v-if="task.status === 'concluido' && reportFor(task)" icon="pi pi-file-pdf" size="small" severity="secondary" title="Baixar relatório ODM" @click="downloadReport(reportFor(task))" />
        <Button v-if="task.status === 'concluido'" icon="pi pi-check-circle" size="small" severity="help" title="Avaliar qualidade" @click="evaluate(task)" />
        <Button v-if="task.status === 'concluido'" label="Importar produtos" icon="pi pi-download" size="small" severity="success" :disabled="!projectStore.canEdit" :loading="importing === task.id" @click="importProducts(task)" />
      </div>
      <small v-if="task.status === 'erro' && task.erro" class="task-error">{{ task.erro }}</small>
      <div v-if="quality[task.id]" class="quality-row"><strong>Qualidade: {{ quality[task.id].score }}%</strong><span>{{ quality[task.id].nivel }}</span><small>{{ quality[task.id].recomendacoes?.[0] }}</small></div>
    </div>
    <PointCloudViewer v-if="selectedProduct" :product="selectedProduct" @close="selectedProduct = null" />
    <DsmSurfaceViewer v-if="selectedSurface" :product="selectedSurface" @close="selectedSurface = null" />
    <ElevationDifference v-if="comparisonTask" :processing-id="comparisonTask" @close="comparisonTask = null" />
  </section>
</template>
<script setup>
import { ref, watch, onUnmounted } from 'vue'
import { useProjectStore } from '../stores/projectStore'
import { useMapStore } from '../stores/mapStore'
import { getOdmProcessamentos, getOdmProducts, importOdmProducts, downloadOdmProduct, getOdmQuality } from '../api/client'
import PointCloudViewer from './PointCloudViewer.vue'
import DsmSurfaceViewer from './DsmSurfaceViewer.vue'
import ElevationDifference from './ElevationDifference.vue'
import Badge from 'primevue/badge'; import ProgressBar from 'primevue/progressbar'
import Button from 'primevue/button'
const projectStore = useProjectStore(); const mapStore = useMapStore(); const tasks = ref([]); const products = ref([]); const quality = ref({}); const importing = ref(null); const selectedProduct = ref(null); const selectedSurface = ref(null); const comparisonTask = ref(null); const error = ref(''); let timer
async function refresh() { if (!projectStore.activeProject) return; try { const [jobs, assets] = await Promise.all([getOdmProcessamentos(projectStore.activeProject.id), getOdmProducts(projectStore.activeProject.id)]); tasks.value = jobs.data.processamentos || []; products.value = assets.data.produtos || []; error.value = '' } catch (e) { error.value = e.response?.data?.detail || 'Falha ao atualizar tarefas ODM.' } }
watch(() => projectStore.activeProject, () => { refresh(); clearInterval(timer); timer = setInterval(refresh, 5000) }, { immediate: true })
onUnmounted(() => clearInterval(timer))
async function importProducts(task) { importing.value = task.id; error.value = ''; try { await importOdmProducts(task.id); await projectStore.fetchOrtomapas(); await refresh() } catch (e) { error.value = e.response?.data?.detail || 'Falha ao importar produtos ODM.' } finally { importing.value = null } }
function orthoFor(task) { return products.value.find((p) => p.processamento_id === task.id && p.tipo === 'ortomosaico') }
async function openOrthomosaic(task) {
  await projectStore.fetchOrtomapas()
  const product = orthoFor(task)
  const ortho = projectStore.ortomapas.find((item) => item.id === product?.ortomapa_id)
  if (!ortho) { error.value = 'Ortomosaico importado, mas nao localizado no catalogo do projeto.'; return }
  if (ortho.centro_lat != null && ortho.centro_lon != null && Number.isFinite(Number(ortho.centro_lat)) && Number.isFinite(Number(ortho.centro_lon))) {
    mapStore.setView([Number(ortho.centro_lat), Number(ortho.centro_lon)], 17)
  }
  mapStore.addLayer({ id: `orto-${ortho.id}`, name: ortho.nome, type: 'ortomapa', sourceId: ortho.id })
}
function statusLabel(status) { return ({ pendente: 'Na fila', processando: 'Processando', concluido: 'Concluído', erro: 'Falhou', cancelado: 'Cancelado' })[status] || status }
function pointCloudFor(task) { return products.value.find((p) => p.processamento_id === task.id && p.tipo === 'nuvem_pontos') }
function terrainFor(task) { return products.value.find((p) => p.processamento_id === task.id && p.tipo === 'dtm') }
function surfaceFor(task) {
  // Prefer the DSM when both elevation products are available; DTM remains a
  // fallback for processing runs that did not generate a DSM.
  return products.value.find((p) => p.processamento_id === task.id && p.tipo === 'dsm')
    || products.value.find((p) => p.processamento_id === task.id && p.tipo === 'dtm')
}
function hasComparison(task) { return products.value.some((p) => p.processamento_id === task.id && p.tipo === 'dsm') && products.value.some((p) => p.processamento_id === task.id && p.tipo === 'dtm') }
function reportFor(task) { return products.value.find((p) => p.processamento_id === task.id && p.tipo === 'relatorio') }
async function downloadReport(product) { const { data } = await downloadOdmProduct(product.id); const url = URL.createObjectURL(data); const link = document.createElement('a'); link.href = url; link.download = product.caminho?.split('/').pop() || 'relatorio-odm.pdf'; link.click(); URL.revokeObjectURL(url) }
async function evaluate(task) { const { data } = await getOdmQuality(task.id); quality.value = { ...quality.value, [task.id]: data } }
</script>
<style scoped>
.odm-tasks { margin-top:10px; border-top:1px solid var(--border); padding-top:8px; }.section-title { display:flex; align-items:center; gap:6px; font-size:.8rem; font-weight:600; color:var(--text-dim); text-transform:uppercase; }.task-row { padding:8px 2px; border-bottom:1px solid var(--border); }.task-main { display:flex; justify-content:space-between; font-size:.78rem; } small,.empty-state { color:var(--text-dim); }.task-row :deep(.p-progressbar) { margin-top:5px; height:14px; }.task-actions { display:flex; gap:6px; margin-top:6px; }.empty-state { padding:8px 0; font-size:.78rem; }
.quality-row{display:flex;justify-content:space-between;margin-top:5px;font-size:.72rem;color:#7fd1b9}.quality-row span{text-transform:uppercase;color:var(--text-dim)}
.task-actions{flex-wrap:wrap}.quality-row{flex-wrap:wrap;gap:5px}
.odm-error,.task-error{display:block;color:#b91c1c;font-size:.76rem;margin:6px 0;overflow-wrap:anywhere}
</style>
