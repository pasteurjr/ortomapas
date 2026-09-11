<template>
  <section v-if="projectStore.activeProject" class="odm-tasks">
    <div class="section-title"><i class="pi pi-cog"></i> Processamentos ODM <Badge :value="tasks.length" severity="info" /></div>
    <div v-if="!tasks.length" class="empty-state">Nenhum processamento</div>
    <div v-for="task in tasks" :key="task.id" class="task-row">
      <div class="task-main"><strong>{{ task.etapa || task.status }}</strong><small>{{ task.odm_task_id.slice(0, 8) }}</small></div>
      <ProgressBar :value="Number(task.progresso || 0)" :showValue="true" />
      <div class="task-actions">
        <Button v-if="task.status === 'concluido' && pointCloudFor(task)" label="Abrir 3D" icon="pi pi-box" size="small" severity="info" @click="selectedProduct = pointCloudFor(task)" />
        <Button v-if="task.status === 'concluido' && surfaceFor(task)" :label="surfaceFor(task).tipo.toUpperCase() + ' 3D'" icon="pi pi-chart-line" size="small" severity="warn" @click="selectedSurface = surfaceFor(task)" />
        <Button v-if="task.status === 'concluido'" label="Importar produtos" icon="pi pi-download" size="small" severity="success" :loading="importing === task.id" @click="importProducts(task)" />
      </div>
    </div>
    <PointCloudViewer v-if="selectedProduct" :product="selectedProduct" @close="selectedProduct = null" />
    <DsmSurfaceViewer v-if="selectedSurface" :product="selectedSurface" @close="selectedSurface = null" />
  </section>
</template>
<script setup>
import { ref, watch, onUnmounted } from 'vue'
import { useProjectStore } from '../stores/projectStore'
import { getOdmProcessamentos, getOdmProducts, importOdmProducts } from '../api/client'
import PointCloudViewer from './PointCloudViewer.vue'
import DsmSurfaceViewer from './DsmSurfaceViewer.vue'
import Badge from 'primevue/badge'; import ProgressBar from 'primevue/progressbar'
const projectStore = useProjectStore(); const tasks = ref([]); const products = ref([]); const importing = ref(null); const selectedProduct = ref(null); const selectedSurface = ref(null); let timer
async function refresh() { if (!projectStore.activeProject) return; try { const [jobs, assets] = await Promise.all([getOdmProcessamentos(projectStore.activeProject.id), getOdmProducts(projectStore.activeProject.id)]); tasks.value = jobs.data.processamentos || []; products.value = assets.data.produtos || [] } catch {} }
watch(() => projectStore.activeProject, () => { refresh(); clearInterval(timer); timer = setInterval(refresh, 5000) }, { immediate: true })
onUnmounted(() => clearInterval(timer))
async function importProducts(task) { importing.value = task.id; try { await importOdmProducts(task.id); await refresh() } finally { importing.value = null } }
function pointCloudFor(task) { return products.value.find((p) => p.processamento_id === task.id && p.tipo === 'nuvem_pontos') }
function surfaceFor(task) { return products.value.find((p) => p.processamento_id === task.id && ['dsm', 'dtm'].includes(p.tipo)) }
</script>
<style scoped>
.odm-tasks { margin-top:10px; border-top:1px solid var(--border); padding-top:8px; }.section-title { display:flex; align-items:center; gap:6px; font-size:.8rem; font-weight:600; color:var(--text-dim); text-transform:uppercase; }.task-row { padding:8px 2px; border-bottom:1px solid var(--border); }.task-main { display:flex; justify-content:space-between; font-size:.78rem; } small,.empty-state { color:var(--text-dim); }.task-row :deep(.p-progressbar) { margin-top:5px; height:14px; }.task-actions { display:flex; gap:6px; margin-top:6px; }.empty-state { padding:8px 0; font-size:.78rem; }
</style>
