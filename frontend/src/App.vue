<template>
  <div class="app-layout">
    <!-- Top Toolbar -->
    <header class="toolbar">
      <div class="toolbar-left">
        <i class="pi pi-map" style="font-size: 1.4rem; color: #4ade80"></i>
        <span class="app-title">Sistema de Ortomapas</span>
      </div>
      <div class="toolbar-center">
        <Select
          v-model="selectedProjectId"
          :options="projectOptions"
          optionLabel="label"
          optionValue="value"
          placeholder="Selecionar projeto..."
          class="project-selector"
          @change="onProjectChange"
        />
        <InputText
          v-model="searchQuery"
          placeholder="Buscar..."
          class="search-input"
        />
      </div>
      <div class="toolbar-right">
        <Button
          icon="pi pi-bell"
          severity="secondary"
          text
          rounded
          :badge="pendingCount > 0 ? String(pendingCount) : undefined"
          badgeSeverity="warn"
        />
        <Button icon="pi pi-cog" severity="secondary" text rounded />
      </div>
    </header>

    <!-- Main Content -->
    <div class="main-content">
      <!-- Left Sidebar -->
      <aside class="sidebar-left" :class="{ collapsed: leftCollapsed }">
        <div class="sidebar-toggle" @click="leftCollapsed = !leftCollapsed">
          <i :class="leftCollapsed ? 'pi pi-angle-right' : 'pi pi-angle-left'"></i>
        </div>
        <div v-if="!leftCollapsed" class="sidebar-content">
          <ProjectList />
          <div class="sidebar-section">
            <h3 class="section-title">
              <i class="pi pi-image"></i> Ortomapas
              <Badge :value="projectStore.ortomapas.length" severity="info" />
            </h3>
            <OrtomapCard
              v-for="orto in projectStore.ortomapas"
              :key="orto.id"
              :ortomapa="orto"
            />
            <div v-if="projectStore.ortomapas.length === 0" class="empty-state">
              Nenhum ortomapa carregado
            </div>
          </div>
          <VoosList />
          <AnalysisResults />
        </div>
      </aside>

      <!-- Map Area -->
      <main class="map-area">
        <CompareView v-if="mapStore.compareMode" />
        <MapViewer v-else />
        <MeasureTools v-if="mapStore.measureMode" />
      </main>

      <!-- Right Sidebar -->
      <aside class="sidebar-right" :class="{ collapsed: rightCollapsed }">
        <div class="sidebar-toggle" @click="rightCollapsed = !rightCollapsed">
          <i :class="rightCollapsed ? 'pi pi-angle-left' : 'pi pi-angle-right'"></i>
        </div>
        <div v-if="!rightCollapsed" class="sidebar-content">
          <ToolsPanel />
          <DrawTools />
        </div>
      </aside>
    </div>

    <!-- Bottom Status Bar -->
    <footer class="status-bar">
      <div class="status-left">
        <AgentStatus />
      </div>
      <div class="status-right">
        <span class="coords">
          Lat: {{ mapStore.cursorCoords.lat.toFixed(6) }},
          Lng: {{ mapStore.cursorCoords.lng.toFixed(6) }}
        </span>
        <span class="zoom-level">Zoom: {{ mapStore.zoom }}</span>
      </div>
    </footer>

    <!-- Modals -->
    <AnalysisForm
      v-if="showAnalysisForm"
      :visible="showAnalysisForm"
      @close="showAnalysisForm = false"
    />
    <ExportDialog
      v-if="showExportDialog"
      :visible="showExportDialog"
      @close="showExportDialog = false"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, provide } from 'vue'
import { useProjectStore } from './stores/projectStore'
import { useMapStore } from './stores/mapStore'
import Select from 'primevue/select'
import InputText from 'primevue/inputtext'
import Button from 'primevue/button'
import Badge from 'primevue/badge'
import ProjectList from './components/ProjectList.vue'
import OrtomapCard from './components/OrtomapCard.vue'
import MapViewer from './components/MapViewer.vue'
import ToolsPanel from './components/ToolsPanel.vue'
import AnalysisResults from './components/AnalysisResults.vue'
import VoosList from './components/VoosList.vue'
import DrawTools from './components/DrawTools.vue'
import MeasureTools from './components/MeasureTools.vue'
import CompareView from './components/CompareView.vue'
import AgentStatus from './components/AgentStatus.vue'
import AnalysisForm from './components/AnalysisForm.vue'
import ExportDialog from './components/ExportDialog.vue'

const projectStore = useProjectStore()
const mapStore = useMapStore()

const leftCollapsed = ref(false)
const rightCollapsed = ref(false)
const searchQuery = ref('')
const selectedProjectId = ref(null)
const showAnalysisForm = ref(false)
const showExportDialog = ref(false)

const projectOptions = computed(() =>
  projectStore.projects.map((p) => ({ label: p.nome, value: p.id }))
)

const pendingCount = computed(() => projectStore.pendingAnalises.length)

function onProjectChange(event) {
  const project = projectStore.projects.find((p) => p.id === event.value)
  if (project) {
    projectStore.setActiveProject(project)
  }
}

provide('showAnalysisForm', showAnalysisForm)
provide('showExportDialog', showExportDialog)

onMounted(() => {
  projectStore.fetchProjects()
})
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

:root {
  --sidebar-bg: #1e1e2e;
  --sidebar-text: #cdd6f4;
  --sidebar-hover: #313244;
  --toolbar-bg: #181825;
  --toolbar-border: #313244;
  --accent: #4ade80;
  --accent-dim: #22c55e;
  --danger: #f38ba8;
  --warning: #fab387;
  --info: #89b4fa;
  --surface: #11111b;
  --text: #cdd6f4;
  --text-dim: #6c7086;
  --border: #45475a;
}

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  background: var(--surface);
  color: var(--text);
  overflow: hidden;
}

.app-layout {
  display: flex;
  flex-direction: column;
  height: 100vh;
  width: 100vw;
}

/* Toolbar */
.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 48px;
  padding: 0 16px;
  background: var(--toolbar-bg);
  border-bottom: 1px solid var(--toolbar-border);
  z-index: 1000;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.app-title {
  font-size: 1.1rem;
  font-weight: 700;
  color: #fff;
  letter-spacing: -0.02em;
}

.toolbar-center {
  display: flex;
  align-items: center;
  gap: 12px;
}

.project-selector {
  width: 260px;
}

.search-input {
  width: 200px;
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 4px;
}

/* Main Content */
.main-content {
  display: flex;
  flex: 1;
  overflow: hidden;
}

/* Sidebars */
.sidebar-left,
.sidebar-right {
  background: var(--sidebar-bg);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  position: relative;
  transition: width 0.2s ease;
  overflow: hidden;
}

.sidebar-left {
  width: 280px;
  border-right: 1px solid var(--border);
}

.sidebar-right {
  width: 320px;
  border-left: 1px solid var(--border);
  border-right: none;
}

.sidebar-left.collapsed {
  width: 32px;
}

.sidebar-right.collapsed {
  width: 32px;
}

.sidebar-toggle {
  position: absolute;
  top: 8px;
  right: 4px;
  z-index: 10;
  cursor: pointer;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  color: var(--text-dim);
  transition: color 0.15s;
}

.sidebar-toggle:hover {
  color: var(--text);
}

.sidebar-content {
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  overflow-x: hidden;
  height: 100%;
  padding: 8px;
  gap: 8px;
}

.sidebar-section {
  margin-bottom: 4px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.8rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-dim);
  padding: 8px 4px;
  border-bottom: 1px solid var(--border);
  margin-bottom: 6px;
}

.empty-state {
  text-align: center;
  color: var(--text-dim);
  font-size: 0.85rem;
  padding: 20px 8px;
}

/* Map Area */
.map-area {
  flex: 1;
  position: relative;
  overflow: hidden;
}

/* Status Bar */
.status-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 28px;
  padding: 0 12px;
  background: var(--toolbar-bg);
  border-top: 1px solid var(--toolbar-border);
  font-size: 0.75rem;
  color: var(--text-dim);
  z-index: 1000;
}

.status-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.status-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.coords {
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  font-size: 0.7rem;
}

.zoom-level {
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  font-size: 0.7rem;
}

/* Scrollbar */
::-webkit-scrollbar {
  width: 6px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: var(--border);
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: var(--text-dim);
}
</style>
