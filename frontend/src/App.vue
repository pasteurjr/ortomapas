<template>
  <div v-if="authChecking" class="auth-checking" role="status">Verificando sessão…</div>
  <LoginView v-else-if="!authenticated" :notice="sessionExpired ? 'Sua sessão expirou. Entre novamente para continuar.' : ''" @authenticated="onAuthenticated" />
  <div v-else class="app-layout">
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
          icon="pi pi-send"
          label="Planejar missao"
          severity="success"
          size="small"
          :disabled="!projectStore.activeProject"
          title="Abrir planejador de missao de captura"
          @click="showMissionPlanner = true"
        />
        <Button
          icon="pi pi-bell"
          severity="secondary"
          text
          rounded
          :badge="pendingCount > 0 ? String(pendingCount) : undefined"
          badgeSeverity="warn"
          :aria-label="`Notificações: ${pendingCount} análises em andamento`"
          :aria-expanded="showNotifications"
          aria-controls="notifications-panel"
          @click="showNotifications = !showNotifications"
        />
        <section v-if="showNotifications" id="notifications-panel" class="notification-popover" role="dialog" aria-label="Notificações de análise" @keydown.esc="showNotifications = false">
          <div class="notification-header"><strong>Análises em andamento</strong><button type="button" aria-label="Fechar notificações" @click="showNotifications = false"><i class="pi pi-times"></i></button></div>
          <p v-if="!pendingCount" class="notification-empty">Nenhuma análise na fila ou em processamento neste projeto.</p>
          <button v-for="analysis in projectStore.pendingAnalises" :key="analysis.id" type="button" class="notification-item" @click="openPendingAnalysis(analysis)">
            <i :class="analysis.status === 'processando' ? 'pi pi-spin pi-spinner' : 'pi pi-clock'"></i>
            <span><strong>{{ analysis.nome || analysis.tipo_analise || 'Análise' }}</strong><small>{{ analysis.status === 'processando' ? 'Processando' : 'Na fila' }}<template v-if="analysis.criado_em"> · {{ formatNotificationDate(analysis.criado_em) }}</template> · abrir resultados</small></span>
          </button>
        </section>
      </div>
    </header>

    <!-- Main Content -->
    <div class="main-content">
      <!-- Left Sidebar -->
      <aside class="sidebar-left" :class="{ collapsed: leftCollapsed }">
        <button class="sidebar-toggle" :title="leftCollapsed ? 'Expandir navegacao' : 'Recolher navegacao'" :aria-expanded="!leftCollapsed" @click="leftCollapsed = !leftCollapsed">
          <i :class="leftCollapsed ? 'pi pi-angle-right' : 'pi pi-angle-left'"></i>
        </button>
        <nav class="workspace-sidebar-nav" aria-label="Navegacao principal">
          <button v-for="item in workspaceItems" :key="item.id" type="button" class="workspace-nav-item" :class="{ active: activeWorkspace === item.id }" :title="leftCollapsed ? item.label : undefined" @click="selectWorkspace(item.id)">
            <i :class="item.icon"></i><span v-if="!leftCollapsed">{{ item.label }}</span>
          </button>
          <div v-if="!leftCollapsed" class="workspace-subnav">
            <button v-for="sub in (workspaceSubitems[activeWorkspace] || [])" :key="sub.label" type="button" :aria-current="activeSubitem === sub.label ? 'location' : undefined" :disabled="sub.disabled?.()" @click="activateSubitem(sub)"><i :class="sub.icon"></i>{{ sub.label }}</button>
          </div>
        </nav>
        <div v-if="!leftCollapsed" class="sidebar-content">
          <template v-if="activeWorkspace === 'dados'">
            <div id="workspace-projects">
            <ProjectList
              :search-results="globalSearchResults"
              :global-search-query="searchQuery"
              :global-search-loading="globalSearchLoading"
              :global-search-error="globalSearchError"
            />
            </div>
            <div id="workspace-layers">
            <LayerPanel />
            </div>
            <div class="sidebar-section">
            <h3 class="section-title">
              <i class="pi pi-image"></i> Ortomapas
              <Badge :value="projectStore.ortomapas.length" severity="info" />
            </h3>
            <div id="workspace-import"><GeoTiffUpload /></div>
            <div id="workspace-orthomaps">
            <OrtomapCard
              v-for="orto in projectStore.ortomapas"
              :key="orto.id"
              :ortomapa="orto"
              :can-delete="projectStore.canEdit"
              @export="openOrtomapaExport"
              @delete="openOrtomapaDelete"
            />
            <div v-if="projectStore.ortomapas.length === 0" class="empty-state">
              Nenhum ortomapa carregado
            </div>
            <p v-if="deleteOrtomapaNotice" class="delete-ortomapa-notice" role="status">{{ deleteOrtomapaNotice }}</p>
            </div>
            </div>
          </template>
          <template v-else-if="activeWorkspace === 'odm'">
            <div id="workspace-flights">
            <VoosList />
            </div>
            <div id="workspace-odm-tasks">
            <OdmTasks />
            </div>
          </template>
          <template v-else-if="activeWorkspace === 'analises'">
            <div id="workspace-analysis-layers">
            <LayerPanel />
            </div>
            <div id="workspace-analysis-tools"><ToolsPanel ref="toolsPanelRef" /></div>
            <div id="workspace-analysis-results"><AnalysisResults @select-analysis="onSelectAnalysis" /></div>
          </template>
          <template v-else-if="activeWorkspace === 'copiloto'">
            <CopilotChat />
          </template>
          <template v-else>
            <ProjectList />
            <div class="workspace-empty"><i class="pi pi-send"></i><strong>Missões de captura</strong><span>Use o botão Planejar missão para criar, validar e exportar uma rota.</span><Button icon="pi pi-plus" label="Nova missão" size="small" severity="success" :disabled="!projectStore.activeProject" @click="showMissionPlanner = true" /></div>
          </template>
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
        <button class="sidebar-toggle" :title="rightCollapsed ? 'Expandir propriedades' : 'Recolher propriedades'" :aria-expanded="!rightCollapsed" @click="rightCollapsed = !rightCollapsed">
          <i :class="rightCollapsed ? 'pi pi-angle-left' : 'pi pi-angle-right'"></i>
        </button>
        <div v-if="!rightCollapsed" class="sidebar-content">
          <DrawTools v-if="activeWorkspace === 'dados' || activeWorkspace === 'analises'" />
          <div v-if="activeWorkspace === 'odm'" class="workspace-help"><i class="pi pi-cog"></i><div class="workspace-help-copy"><strong>Pipeline ODM</strong><span>Envie fotos, acompanhe o processamento, importe produtos e abra as visualizações 3D.</span></div></div>
          <div v-if="activeWorkspace === 'missoes'" class="workspace-help"><i class="pi pi-send"></i><div class="workspace-help-copy"><strong>Planejamento de voo</strong><span>Crie AOI, exclusões, takeoff, waypoints, grid e exportação para o aplicativo de voo.</span></div></div>
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
      :visible="showAnalysisForm"
      @close="showAnalysisForm = false"
      @select-outlet="showAnalysisForm = false"
      @outlet-selected="showAnalysisForm = true"
    />
    <ExportDialog
      v-if="showExportDialog"
      :visible="showExportDialog"
      :initial-ortomapa-id="exportOrtomapaId"
      @close="showExportDialog = false"
    />
    <Dialog v-model:visible="showDeleteOrtomapaDialog" modal header="Remover ortomapa do catálogo" :closable="!deletingOrtomapa" :closeOnEscape="!deletingOrtomapa" :style="{ width: 'min(92vw, 30rem)' }" aria-label="Confirmar remoção de ortomapa">
      <p v-if="ortomapaToDelete" class="delete-ortomapa-copy">Remover <strong>{{ ortomapaToDelete.nome }}</strong> do catálogo deste projeto?</p>
      <p class="delete-ortomapa-note">O registro será removido do catálogo; o arquivo raster será mantido. Se houver análises, anotações, comparações ou tarefas de agente vinculadas, a remoção será bloqueada para preservar esse histórico.</p>
      <p v-if="deleteOrtomapaError" class="delete-ortomapa-error" role="alert">{{ deleteOrtomapaError }}</p>
      <template #footer>
        <Button label="Cancelar" severity="secondary" outlined :disabled="deletingOrtomapa" @click="closeDeleteOrtomapa" />
        <Button label="Remover do catálogo" severity="danger" :loading="deletingOrtomapa" @click="confirmDeleteOrtomapa" />
      </template>
    </Dialog>
    <MissionPlanner v-if="showMissionPlanner" @close="showMissionPlanner = false" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, provide, watch, nextTick } from 'vue'
import { useProjectStore } from './stores/projectStore'
import { useMapStore } from './stores/mapStore'
import Select from 'primevue/select'
import InputText from 'primevue/inputtext'
import Button from 'primevue/button'
import Badge from 'primevue/badge'
import Dialog from 'primevue/dialog'
import ProjectList from './components/ProjectList.vue'
import OrtomapCard from './components/OrtomapCard.vue'
import MapViewer from './components/MapViewer.vue'
import ToolsPanel from './components/ToolsPanel.vue'
import AnalysisResults from './components/AnalysisResults.vue'
import VoosList from './components/VoosList.vue'
import DrawTools from './components/DrawTools.vue'
import CopilotChat from './components/CopilotChat.vue'
import MeasureTools from './components/MeasureTools.vue'
import CompareView from './components/CompareView.vue'
import AgentStatus from './components/AgentStatus.vue'
import AnalysisForm from './components/AnalysisForm.vue'
import ExportDialog from './components/ExportDialog.vue'
import LoginView from './components/LoginView.vue'
import OdmTasks from './components/OdmTasks.vue'
import MissionPlanner from './components/MissionPlanner.vue'
import LayerPanel from './components/LayerPanel.vue'
import GeoTiffUpload from './components/GeoTiffUpload.vue'
import { getCurrentUser, searchProjects, deleteOrtomapa } from './api/client'

const projectStore = useProjectStore()
const mapStore = useMapStore()

const leftCollapsed = ref(false)
const toolsPanelRef = ref(null)
const compactViewport = window.matchMedia('(max-width: 1100px)')
const rightCollapsed = ref(compactViewport.matches)
function onCompactViewport(event) { rightCollapsed.value=event.matches }
const searchQuery = ref('')
const globalSearchResults = ref(null)
const globalSearchLoading = ref(false)
const globalSearchError = ref(false)
let searchTimer
let searchGeneration = 0
watch(searchQuery, (value) => {
  const generation = ++searchGeneration
  clearTimeout(searchTimer)
  const query = value.trim()
  if (!query) {
    globalSearchResults.value = null
    globalSearchLoading.value = false
    globalSearchError.value = false
    return
  }
  globalSearchResults.value = []
  globalSearchLoading.value = true
  globalSearchError.value = false
  searchTimer = setTimeout(async () => {
    try {
      const response = await searchProjects(query)
      if (generation === searchGeneration) globalSearchResults.value = response.data.projetos || []
    } catch {
      if (generation === searchGeneration) {
        globalSearchResults.value = []
        globalSearchError.value = true
      }
    } finally {
      if (generation === searchGeneration) globalSearchLoading.value = false
    }
  }, 250)
})
const selectedProjectId = ref(null)
watch(() => projectStore.activeProject?.id, (id) => { selectedProjectId.value = id ?? null }, { immediate: true })
const showAnalysisForm = ref(false)
const showExportDialog = ref(false)
const exportOrtomapaId = ref(null)
const showMissionPlanner = ref(false)
const showNotifications = ref(false)
const showDeleteOrtomapaDialog = ref(false)
const ortomapaToDelete = ref(null)
const deletingOrtomapa = ref(false)
const deleteOrtomapaError = ref('')
const deleteOrtomapaNotice = ref('')
const activeSubitem = ref('')
const authenticated = ref(false)
const sessionExpired = ref(false)
const authChecking = ref(Boolean(localStorage.getItem('ortomapas_token')))
const activeWorkspace = ref('dados')
const workspaceItems = [
  { id: 'dados', label: 'Dados e mapa', icon: 'pi pi-map' },
  { id: 'odm', label: 'Voos e ODM', icon: 'pi pi-cog' },
  { id: 'analises', label: 'Análises', icon: 'pi pi-chart-bar' },
  { id: 'missoes', label: 'Missões', icon: 'pi pi-send' },
  { id: 'copiloto', label: 'Copiloto', icon: 'pi pi-sparkles' },
]
const workspaceSubitems = {
  dados: [
    { label: 'Projetos', icon: 'pi pi-folder', target: 'workspace-projects' },
    { label: 'Camadas e ortomapas', icon: 'pi pi-images', target: 'workspace-layers' },
    { label: 'Perfil altimétrico', icon: 'pi pi-chart-line', action: () => { mapStore.profileOpen = true } },
    { label: 'Importar dados', icon: 'pi pi-upload', target: 'workspace-import' },
  ],
  odm: [
    { label: 'Voos e fotos', icon: 'pi pi-camera', target: 'workspace-flights' },
    { label: 'Fila e produtos ODM', icon: 'pi pi-clock', target: 'workspace-odm-tasks' },
  ],
  analises: [
    { label: 'Ferramentas espaciais', icon: 'pi pi-sliders-h', target: 'workspace-analysis-tools' },
    { label: 'Resultados', icon: 'pi pi-chart-line', target: 'workspace-analysis-results' },
  ],
  missoes: [{ label: 'Planejador de captura', icon: 'pi pi-send', action: () => { showMissionPlanner.value = true } }],
  copiloto: [
    { label: 'Conversas do projeto', icon: 'pi pi-comments', target: 'copilot-threads' },
    { label: 'Histórico e ferramentas', icon: 'pi pi-wrench', target: 'copilot-messages' },
  ],
}

function onAuthenticated() { authenticated.value = true; sessionExpired.value = false; authChecking.value = false; projectStore.fetchProjects() }

function onUnauthenticated() {
  sessionExpired.value = true
  authenticated.value = false
  authChecking.value = false
  projectStore.projects = []
  projectStore.setActiveProject(null)
}

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

function selectWorkspace(id) {
  activeWorkspace.value = id
  activeSubitem.value = ''
  showNotifications.value = false
  if(id==='copiloto') rightCollapsed.value=true
}

function activateSubitem(sub) {
  activeSubitem.value = sub.label
  if (sub.action) sub.action()
  if (sub.target) document.getElementById(sub.target)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

function formatNotificationDate(value) {
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? '' : new Intl.DateTimeFormat('pt-BR', { dateStyle: 'short', timeStyle: 'short' }).format(date)
}

async function openPendingAnalysis(analysis) {
  showNotifications.value = false
  activeWorkspace.value = 'analises'
  await nextTick()
  document.querySelector(`[data-analysis-id="${analysis.id}"]`)?.scrollIntoView({ behavior: 'smooth', block: 'center' })
}

async function onSelectAnalysis(analysis) {
  activeWorkspace.value = 'analises'
  await nextTick()
  toolsPanelRef.value?.selectForAnalysis(analysis)
}

function openOrtomapaExport(ortomapa) {
  exportOrtomapaId.value = ortomapa?.id ?? null
  showExportDialog.value = true
}

function openOrtomapaDelete(ortomapa) {
  if (!ortomapa || !projectStore.canEdit) return
  deleteOrtomapaNotice.value = ''
  ortomapaToDelete.value = ortomapa
  deleteOrtomapaError.value = ''
  showDeleteOrtomapaDialog.value = true
}

function closeDeleteOrtomapa() {
  if (deletingOrtomapa.value) return
  showDeleteOrtomapaDialog.value = false
  ortomapaToDelete.value = null
  deleteOrtomapaError.value = ''
}

async function confirmDeleteOrtomapa() {
  if (!ortomapaToDelete.value || deletingOrtomapa.value || !projectStore.canEdit) return
  const id = ortomapaToDelete.value.id
  deletingOrtomapa.value = true
  deleteOrtomapaError.value = ''
  try {
    await deleteOrtomapa(id)
    projectStore.ortomapas = projectStore.ortomapas.filter((item) => item.id !== id)
    mapStore.removeLayer(`orto-${id}`)
    deleteOrtomapaNotice.value = `${ortomapaToDelete.value.nome} removido do catálogo; o arquivo raster foi mantido.`
    showDeleteOrtomapaDialog.value = false
    ortomapaToDelete.value = null
  } catch (error) {
    deleteOrtomapaError.value = error.response?.data?.detail || 'Não foi possível remover o ortomapa. O item continua no catálogo.'
  } finally {
    deletingOrtomapa.value = false
  }
}

provide('showAnalysisForm', showAnalysisForm)
provide('showExportDialog', showExportDialog)

onMounted(() => {
  compactViewport.addEventListener('change',onCompactViewport)
  window.addEventListener('ortomapas:unauthorized', onUnauthenticated)
  if (authChecking.value) {
    getCurrentUser()
      .then(() => { if (localStorage.getItem('ortomapas_token')) { authenticated.value = true; projectStore.fetchProjects() } })
      .catch(() => { sessionExpired.value = true; authenticated.value = false; localStorage.removeItem('ortomapas_token') })
      .finally(() => { authChecking.value = false })
  }
})
onUnmounted(()=>{
  clearTimeout(searchTimer)
  compactViewport.removeEventListener('change',onCompactViewport)
  window.removeEventListener('ortomapas:unauthorized', onUnauthenticated)
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

html, body, #app { width: 100%; height: 100%; overflow: clip; }

.app-layout {
  display: flex;
  flex-direction: column;
  height: 100vh;
  width: 100vw;
  overflow: hidden;
}

/* Toolbar */
.toolbar {
  position: relative;
  display: flex;
  flex: 0 0 48px;
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
  position: relative;
  display: flex;
  align-items: center;
  gap: 4px;
}

.notification-popover {
  position: absolute;
  top: calc(100% + 8px);
  right: 38px;
  width: min(360px, 90vw);
  max-height: min(60vh, 420px);
  overflow: auto;
  padding: 10px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--toolbar-bg);
  box-shadow: 0 12px 32px #0008;
  z-index: 1100;
}
.notification-header { display:flex; align-items:center; justify-content:space-between; padding:3px 4px 9px; color:var(--text); font-size:.85rem; }
.notification-header button { border:0; background:transparent; color:var(--text-dim); cursor:pointer; padding:4px; }
.notification-empty { padding:12px 5px; color:var(--text-dim); font-size:.8rem; }
.notification-item { width:100%; display:flex; align-items:center; gap:10px; padding:9px 6px; border:0; border-top:1px solid var(--border); background:transparent; color:var(--text); text-align:left; cursor:pointer; }
.notification-item:hover, .notification-item:focus-visible { background:var(--sidebar-hover); outline:0; }
.notification-item > i { color:var(--warning); }
.notification-item span { display:grid; gap:3px; }
.notification-item strong { font-size:.8rem; }
.notification-item small { color:var(--text-dim); font-size:.72rem; }

/* Main Content */
.main-content {
  display: flex;
  flex: 1;
  min-height: 0;
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

.sidebar-left, .sidebar-right { flex-shrink: 0; min-height: 0; }

.sidebar-left {
  width: 292px;
  border-right: 1px solid var(--border);
}

.sidebar-right {
  width: 320px;
  border-left: 1px solid var(--border);
  border-right: none;
}

.sidebar-left.collapsed {
  width: 56px;
}

.sidebar-right.collapsed {
  width: 32px;
}

.sidebar-toggle {
  border:0;
  background:transparent;
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
  flex: 1;
  min-height: 0;
  padding: 8px;
  gap: 8px;
}

.sidebar-content > * { flex-shrink: 0; }
.workspace-help { display:flex; align-items:flex-start; gap:10px; padding:12px; border:1px solid var(--border); border-radius:4px; color:var(--text-dim); }
.workspace-help > i { flex:none; margin-top:2px; color:var(--accent); }
.workspace-help-copy { min-width:0; display:grid; gap:6px; }
.workspace-help-copy strong { color:var(--text); font-size:.82rem; }
.workspace-help-copy span { font-size:.75rem; line-height:1.45; overflow-wrap:anywhere; }

.workspace-sidebar-nav {
  flex: 0 0 auto;
  padding: 10px 8px 6px;
  border-bottom: 1px solid var(--border);
}

.workspace-nav-item {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 10px;
  min-height: 36px;
  padding: 8px 10px;
  border: 0;
  border-radius: 6px;
  background: transparent;
  color: var(--text-dim);
  cursor: pointer;
  text-align: left;
  font-size: .82rem;
}

.workspace-nav-item:hover { background: var(--sidebar-hover); color: var(--text); }
.workspace-nav-item.active { background: #243b35; color: #86efac; box-shadow: inset 3px 0 0 var(--accent); }
.sidebar-left.collapsed .workspace-nav-item { justify-content: center; padding-inline: 0; }
.sidebar-left.collapsed .workspace-nav-item.active { box-shadow: inset 3px 0 0 var(--accent); }
.workspace-subnav { margin: 2px 0 4px 28px; display: grid; gap: 2px; }
.workspace-subnav button { display: flex; align-items: center; gap: 8px; padding: 6px 8px; border: 0; background: transparent; color: var(--text-dim); font-size: .74rem; text-align: left; cursor: pointer; border-radius: 4px; }
.workspace-subnav button:hover { background: var(--sidebar-hover); color: var(--text); }
.workspace-subnav button[aria-current="location"] { color:#86efac; background:#243b35; }
.workspace-subnav button:disabled { opacity:.45; cursor:not-allowed; }
.delete-ortomapa-copy { margin: 0 0 10px; line-height: 1.5; }
.delete-ortomapa-note { color: var(--text-dim, #94a3b8); font-size: .9rem; line-height: 1.5; }
.delete-ortomapa-error { margin-top: 12px; color: #f87171; font-size: .9rem; }
.delete-ortomapa-notice { margin: 8px; color: #86efac; font-size: .75rem; line-height: 1.4; }

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
  flex: 0 0 36px;
  height: 36px;
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

/* Dialogs must remain opaque over the map; transparent panels make form data
   unreadable and look like a rendering failure in screenshots. */
.p-dialog {
  background: #17242c !important;
  background-color: #17242c !important;
  opacity: 1 !important;
  isolation: isolate;
  color: #e8f0f2 !important;
  border: 1px solid #52616b !important;
  box-shadow: 0 18px 48px #000b !important;
}
.p-dialog .p-dialog-header,
.p-dialog .p-dialog-content,
.p-dialog .p-dialog-footer {
  background: #17242c !important;
  color: #e8f0f2 !important;
}
.p-dialog .p-dialog-content label { color: #c9d6dc; }
.auth-checking { min-height: 100vh; display: grid; place-items: center; color: #d6e3e8; background: #0f1720; font: 1rem sans-serif; }
</style>
