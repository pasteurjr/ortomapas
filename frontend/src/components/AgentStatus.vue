<template>
  <div class="agent-status">
    <div class="agent-status-bar">
      <!-- Active tasks -->
      <div v-if="activeTasks.length > 0" class="tasks-list">
        <div
          v-for="task in activeTasks"
          :key="task.id"
          class="task-item"
          :class="task.status"
        >
          <i
            :class="statusIcon(task.status)"
            :style="{ color: statusColor(task.status) }"
            class="task-icon"
          ></i>
          <span class="task-agent">{{ task.agente || 'Agente' }}</span>
          <span class="task-type">{{ taskLabel(task) }}</span>
          <span class="task-time" v-if="task.criado_em">{{ elapsed(task.criado_em) }}</span>
        </div>
      </div>

      <!-- No tasks -->
      <div v-else class="no-tasks">
        <i class="pi pi-check-circle" style="color: #a6e3a1"></i>
        <span>Nenhuma tarefa em execucao</span>
      </div>

      <!-- Action buttons -->
      <button class="status-btn" @click="openAnalysisForm" title="Nova Analise">
        <i class="pi pi-plus"></i>
      </button>
      <button class="status-btn" @click="refreshTasks" title="Atualizar">
        <i :class="refreshing ? 'pi pi-spin pi-spinner' : 'pi pi-refresh'"></i>
      </button>
    </div>

    <!-- Expanded task detail panel -->
    <div v-if="showDetail && allTasks.length > 0" class="tasks-detail">
      <div class="detail-header">
        <h4><i class="pi pi-server"></i> Tarefas do Agente</h4>
        <button class="close-btn" @click="showDetail = false"><i class="pi pi-times"></i></button>
      </div>
      <div class="detail-list">
        <div
          v-for="task in allTasks"
          :key="task.id"
          class="detail-item"
          :class="task.status"
        >
          <div class="detail-icon">
            <i
              :class="statusIcon(task.status)"
              :style="{ color: statusColor(task.status) }"
            ></i>
          </div>
          <div class="detail-info">
            <div class="detail-name">{{ task.nome || task.tipo_analise || 'Tarefa' }}</div>
            <div class="detail-meta">
              <span class="detail-agent">{{ task.agente || 'auto' }}</span>
              <span class="detail-status-label">{{ statusLabel(task.status) }}</span>
              <span class="detail-elapsed" v-if="task.criado_em">{{ elapsed(task.criado_em) }}</span>
            </div>
            <div v-if="task.status === 'erro' && task.erro" class="detail-error">
              {{ task.erro }}
            </div>
          </div>
          <div class="detail-badge" :class="task.status">
            {{ statusLabel(task.status) }}
          </div>
        </div>
      </div>
    </div>

    <!-- Toggle detail -->
    <button
      v-if="allTasks.length > 0"
      class="toggle-detail"
      @click="showDetail = !showDetail"
    >
      {{ showDetail ? 'Ocultar detalhes' : `Ver ${allTasks.length} tarefa(s)` }}
      <i :class="showDetail ? 'pi pi-chevron-up' : 'pi pi-chevron-down'"></i>
    </button>
  </div>
</template>

<script setup>
import { ref, computed, inject, onMounted, onUnmounted } from 'vue'
import { useProjectStore } from '../stores/projectStore'

const projectStore = useProjectStore()
const showAnalysisForm = inject('showAnalysisForm', ref(false))
const showDetail = ref(false)
const refreshing = ref(false)

const activeTasks = computed(() =>
  projectStore.analises.filter((a) =>
    ['em_fila', 'processando'].includes(a.status)
  )
)

const allTasks = computed(() =>
  [...projectStore.analises]
    .sort((a, b) => {
      const order = { processando: 0, em_fila: 1, concluida: 2, erro: 3 }
      return (order[a.status] ?? 4) - (order[b.status] ?? 4)
    })
    .slice(0, 20)
)

function statusIcon(status) {
  const map = {
    em_fila: 'pi pi-clock',
    processando: 'pi pi-spin pi-spinner',
    concluida: 'pi pi-check-circle',
    erro: 'pi pi-exclamation-triangle',
  }
  return map[status] || 'pi pi-circle'
}

function statusColor(status) {
  const map = {
    em_fila: '#89b4fa',
    processando: '#f9e2af',
    concluida: '#a6e3a1',
    erro: '#f38ba8',
  }
  return map[status] || '#6c7086'
}

function statusLabel(status) {
  const map = {
    em_fila: 'Na fila',
    processando: 'Processando',
    concluida: 'Concluida',
    erro: 'Erro',
  }
  return map[status] || status
}

function taskLabel(task) {
  return task.nome || task.tipo_analise || task.tipo_tarefa || 'Tarefa'
}

function elapsed(dateStr) {
  if (!dateStr) return ''
  const diff = Date.now() - new Date(dateStr).getTime()
  const secs = Math.floor(diff / 1000)
  if (secs < 60) return `${secs}s`
  const mins = Math.floor(secs / 60)
  if (mins < 60) return `${mins}m ${secs % 60}s`
  const hours = Math.floor(mins / 60)
  return `${hours}h ${mins % 60}m`
}

function openAnalysisForm() {
  if (showAnalysisForm) showAnalysisForm.value = true
}

async function refreshTasks() {
  refreshing.value = true
  try {
    await projectStore.fetchAnalises()
    await projectStore.pollAgentTasks()
  } finally {
    refreshing.value = false
  }
}

let pollTimer = null

onMounted(() => {
  projectStore.pollAgentTasks()
  pollTimer = setInterval(() => {
    projectStore.pollAgentTasks()
  }, 5000)
})

onUnmounted(() => {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
})
</script>

<style scoped>
.agent-status {
  position: relative;
}

.agent-status-bar {
  display: flex;
  align-items: center;
  gap: 8px;
}

.tasks-list {
  display: flex;
  gap: 12px;
  overflow-x: auto;
  max-width: 400px;
}

.task-item {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 0.72rem;
  white-space: nowrap;
  padding: 3px 8px;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.03);
}

.task-item.processando {
  background: rgba(249, 226, 175, 0.08);
}

.task-item.em_fila {
  background: rgba(137, 180, 250, 0.08);
}

.task-icon {
  font-size: 0.75rem;
}

.task-agent {
  font-weight: 600;
  color: #cdd6f4;
}

.task-type {
  color: #a6adc8;
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
}

.task-time {
  color: #6c7086;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.68rem;
}

.no-tasks {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 0.72rem;
  color: #a6adc8;
}

.status-btn {
  background: none;
  border: 1px solid #313244;
  color: #a6adc8;
  cursor: pointer;
  width: 28px;
  height: 28px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.72rem;
  transition: all 0.15s;
  flex-shrink: 0;
}

.status-btn:hover {
  background: #313244;
  color: #cdd6f4;
}

.toggle-detail {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 4px;
  background: none;
  border: none;
  color: #89b4fa;
  font-size: 0.68rem;
  cursor: pointer;
  padding: 2px 0;
}

.toggle-detail:hover {
  color: #74c7ec;
}

.tasks-detail {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  min-width: 380px;
  background: #1e1e2e;
  border: 1px solid #313244;
  border-radius: 10px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
  z-index: 900;
  margin-top: 6px;
  overflow: hidden;
}

.detail-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  border-bottom: 1px solid #313244;
}

.detail-header h4 {
  margin: 0;
  font-size: 0.82rem;
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
  padding: 2px;
}

.close-btn:hover {
  color: #cdd6f4;
}

.detail-list {
  max-height: 300px;
  overflow-y: auto;
  padding: 6px;
}

.detail-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 8px 10px;
  border-radius: 6px;
  margin-bottom: 3px;
  transition: background 0.15s;
}

.detail-item:hover {
  background: rgba(255, 255, 255, 0.03);
}

.detail-icon {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: 0.85rem;
}

.detail-info {
  flex: 1;
  min-width: 0;
}

.detail-name {
  font-size: 0.8rem;
  font-weight: 600;
  color: #cdd6f4;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.detail-meta {
  display: flex;
  gap: 8px;
  margin-top: 2px;
  font-size: 0.7rem;
}

.detail-agent {
  color: #89b4fa;
}

.detail-status-label {
  color: #a6adc8;
}

.detail-elapsed {
  color: #6c7086;
  font-family: 'JetBrains Mono', monospace;
}

.detail-error {
  margin-top: 4px;
  font-size: 0.7rem;
  color: #f38ba8;
  background: rgba(243, 139, 168, 0.08);
  padding: 4px 8px;
  border-radius: 4px;
}

.detail-badge {
  font-size: 0.65rem;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 10px;
  flex-shrink: 0;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.detail-badge.em_fila {
  background: rgba(137, 180, 250, 0.15);
  color: #89b4fa;
}

.detail-badge.processando {
  background: rgba(249, 226, 175, 0.15);
  color: #f9e2af;
}

.detail-badge.concluida {
  background: rgba(166, 227, 161, 0.15);
  color: #a6e3a1;
}

.detail-badge.erro {
  background: rgba(243, 139, 168, 0.15);
  color: #f38ba8;
}
</style>
