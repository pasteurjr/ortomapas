<template>
  <div class="project-list">
    <div class="section-header">
      <h3 class="section-title">
        <i class="pi pi-folder"></i> Projetos
      </h3>
      <Button
        icon="pi pi-plus"
        label="Novo"
        size="small"
        severity="success"
        @click="showNewProject = true"
      />
    </div>

    <div class="filters">
      <InputText
        v-model="filterArea"
        placeholder="Filtrar por area..."
        class="filter-input"
        size="small"
      />
      <Select
        v-model="filterStatus"
        :options="statusOptions"
        optionLabel="label"
        optionValue="value"
        placeholder="Status"
        class="filter-select"
        size="small"
      />
    </div>

    <div v-if="projectStore.loading" class="loading-state">
      <ProgressSpinner style="width: 24px; height: 24px" strokeWidth="4" />
      <span>Carregando...</span>
    </div>

    <div
      v-for="project in filteredProjects"
      :key="project.id"
      class="project-item"
      :class="{ active: projectStore.activeProject?.id === project.id }"
      @click="selectProject(project)"
    >
      <div class="project-icon">
        <i class="pi pi-map"></i>
      </div>
      <div class="project-info">
        <div class="project-name">{{ project.nome }}</div>
        <div class="project-area">{{ project.area_estudo || 'Sem area definida' }}</div>
        <div class="project-meta">
          <span class="meta-item" title="Ortomapas">
            <i class="pi pi-image"></i> {{ project.num_ortomapas || 0 }}
          </span>
          <span class="meta-item" title="Analises">
            <i class="pi pi-chart-bar"></i> {{ project.num_analises || 0 }}
          </span>
        </div>
      </div>
      <Badge
        :value="project.status || 'ativo'"
        :severity="statusSeverity(project.status)"
        class="project-badge"
      />
    </div>

    <div v-if="!projectStore.loading && projectStore.projects.length === 0" class="empty-state">
      Nenhum projeto encontrado
    </div>

    <!-- New Project Dialog -->
    <Dialog
      v-model:visible="showNewProject"
      header="Novo Projeto"
      :modal="true"
      :style="{ width: '450px' }"
    >
      <div class="form-group">
        <label>Nome do Projeto</label>
        <InputText v-model="newProject.nome" placeholder="Nome" class="w-full" />
      </div>
      <div class="form-group">
        <label>Descricao</label>
        <Textarea v-model="newProject.descricao" rows="3" class="w-full" />
      </div>
      <div class="form-group">
        <label>Area de Estudo</label>
        <InputText v-model="newProject.area_estudo" placeholder="Ex: Fazenda Norte" class="w-full" />
      </div>
      <template #footer>
        <Button label="Cancelar" severity="secondary" @click="showNewProject = false" />
        <Button label="Criar" icon="pi pi-check" @click="createProject" />
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useProjectStore } from '../stores/projectStore'
import Button from 'primevue/button'
import Badge from 'primevue/badge'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import Select from 'primevue/select'
import ProgressSpinner from 'primevue/progressspinner'

const projectStore = useProjectStore()
const showNewProject = ref(false)
const newProject = ref({ nome: '', descricao: '', area_estudo: '' })
const filterArea = ref('')
const filterStatus = ref(null)

const statusOptions = [
  { label: 'Todos', value: null },
  { label: 'Ativo', value: 'ativo' },
  { label: 'Planejado', value: 'planejado' },
  { label: 'Em andamento', value: 'em_andamento' },
  { label: 'Concluido', value: 'concluido' },
  { label: 'Arquivado', value: 'arquivado' },
]

const filteredProjects = computed(() => {
  let list = projectStore.projects
  if (filterStatus.value) {
    list = list.filter((p) => p.status === filterStatus.value)
  }
  if (filterArea.value) {
    const q = filterArea.value.toLowerCase()
    list = list.filter(
      (p) =>
        (p.area_estudo || '').toLowerCase().includes(q) ||
        (p.nome || '').toLowerCase().includes(q)
    )
  }
  return list
})

function statusSeverity(status) {
  const map = { ativo: 'success', arquivado: 'warn', concluido: 'info' }
  return map[status] || 'info'
}

function selectProject(project) {
  projectStore.setActiveProject(project)
}

async function createProject() {
  if (!newProject.value.nome) return
  await projectStore.createProject(newProject.value)
  newProject.value = { nome: '', descricao: '', area_estudo: '' }
  showNewProject.value = false
}
</script>

<style scoped>
.project-list {
  margin-bottom: 8px;
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

.filters {
  display: flex;
  gap: 4px;
  padding: 0 4px;
  margin-bottom: 6px;
}

.filter-input {
  flex: 1;
  min-width: 0;
}

.filter-select {
  width: 110px;
}

.loading-state {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  color: var(--text-dim);
  font-size: 0.85rem;
}

.project-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 8px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.15s;
  margin-bottom: 2px;
}

.project-item:hover {
  background: var(--sidebar-hover);
}

.project-item.active {
  background: rgba(74, 222, 128, 0.1);
  border-left: 3px solid var(--accent);
}

.project-icon {
  width: 32px;
  height: 32px;
  border-radius: 6px;
  background: var(--sidebar-hover);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--accent);
  flex-shrink: 0;
}

.project-info {
  flex: 1;
  min-width: 0;
}

.project-name {
  font-weight: 600;
  font-size: 0.85rem;
  color: var(--text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.project-area {
  font-size: 0.75rem;
  color: var(--text-dim);
  margin-top: 2px;
}

.project-meta {
  display: flex;
  gap: 10px;
  margin-top: 4px;
}

.meta-item {
  font-size: 0.7rem;
  color: var(--text-dim);
  display: flex;
  align-items: center;
  gap: 3px;
}

.project-badge {
  flex-shrink: 0;
  font-size: 0.65rem;
}

.form-group {
  margin-bottom: 12px;
}

.form-group label {
  display: block;
  font-size: 0.85rem;
  font-weight: 500;
  margin-bottom: 4px;
  color: var(--text);
}

.w-full {
  width: 100%;
}
</style>
