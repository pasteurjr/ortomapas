<template>
  <section v-if="projectStore.activeProject" class="odm-tasks">
    <div class="section-title"><i class="pi pi-cog"></i> Processamentos ODM <Badge :value="tasks.length" severity="info" /></div>
    <div v-if="!tasks.length" class="empty-state">Nenhum processamento</div>
    <div v-for="task in tasks" :key="task.id" class="task-row">
      <div class="task-main"><strong>{{ task.etapa || task.status }}</strong><small>{{ task.odm_task_id.slice(0, 8) }}</small></div>
      <ProgressBar :value="Number(task.progresso || 0)" :showValue="true" />
    </div>
  </section>
</template>
<script setup>
import { ref, watch, onUnmounted } from 'vue'
import { useProjectStore } from '../stores/projectStore'
import { getOdmProcessamentos } from '../api/client'
import Badge from 'primevue/badge'; import ProgressBar from 'primevue/progressbar'
const projectStore = useProjectStore(); const tasks = ref([]); let timer
async function refresh() { if (!projectStore.activeProject) return; try { const { data } = await getOdmProcessamentos(projectStore.activeProject.id); tasks.value = data.processamentos || [] } catch {} }
watch(() => projectStore.activeProject, () => { refresh(); clearInterval(timer); timer = setInterval(refresh, 5000) }, { immediate: true })
onUnmounted(() => clearInterval(timer))
</script>
<style scoped>
.odm-tasks { margin-top:10px; border-top:1px solid var(--border); padding-top:8px; }.section-title { display:flex; align-items:center; gap:6px; font-size:.8rem; font-weight:600; color:var(--text-dim); text-transform:uppercase; }.task-row { padding:8px 2px; border-bottom:1px solid var(--border); }.task-main { display:flex; justify-content:space-between; font-size:.78rem; } small,.empty-state { color:var(--text-dim); }.task-row :deep(.p-progressbar) { margin-top:5px; height:14px; }.empty-state { padding:8px 0; font-size:.78rem; }
</style>
