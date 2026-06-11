<template>
  <div class="analysis-results">
    <h3 class="section-title">
      <i class="pi pi-chart-bar"></i> Analises
      <Badge :value="projectStore.analises.length" severity="info" />
    </h3>

    <div
      v-for="analise in projectStore.analises"
      :key="analise.id"
      class="result-item"
      :class="{ active: selectedId === analise.id }"
      @click="selectAnalise(analise)"
    >
      <div class="result-icon" :style="{ background: iconBg(analise.tipo_analise) }">
        <i :class="iconClass(analise.tipo_analise)"></i>
      </div>
      <div class="result-info">
        <div class="result-name">{{ analise.nome || analise.tipo_analise }}</div>
        <div class="result-date">{{ formatDate(analise.criado_em) }}</div>
      </div>
      <Badge
        :value="statusLabel(analise.status)"
        :severity="statusSeverity(analise.status)"
      />
    </div>

    <div v-if="projectStore.analises.length === 0" class="empty-state">
      Nenhuma analise realizada
    </div>

    <!-- Statistics Panel -->
    <div v-if="selectedAnalise && selectedAnalise.resultado" class="stats-panel">
      <h4 class="stats-title">Estatisticas</h4>

      <div v-if="selectedAnalise.resultado.classes" class="class-stats">
        <div
          v-for="(cls, idx) in selectedAnalise.resultado.classes"
          :key="idx"
          class="class-row"
        >
          <div class="class-color" :style="{ background: classColors[idx % classColors.length] }"></div>
          <span class="class-name">{{ cls.nome || `Classe ${idx + 1}` }}</span>
          <span class="class-area">{{ formatArea(cls.area) }}</span>
          <span class="class-pct">{{ cls.percentual?.toFixed(1) }}%</span>
        </div>
      </div>

      <!-- Simple bar chart -->
      <div v-if="selectedAnalise.resultado.classes" class="bar-chart">
        <div
          v-for="(cls, idx) in selectedAnalise.resultado.classes"
          :key="idx"
          class="bar-row"
        >
          <div class="bar-label">{{ cls.nome || `C${idx + 1}` }}</div>
          <div class="bar-track">
            <div
              class="bar-fill"
              :style="{
                width: (cls.percentual || 0) + '%',
                background: classColors[idx % classColors.length],
              }"
            ></div>
          </div>
          <div class="bar-value">{{ cls.percentual?.toFixed(1) }}%</div>
        </div>
      </div>

      <div v-if="selectedAnalise.resultado.stats" class="general-stats">
        <div
          v-for="(val, key) in selectedAnalise.resultado.stats"
          :key="key"
          class="stat-row"
        >
          <span>{{ key }}:</span>
          <strong>{{ typeof val === 'number' ? val.toFixed(3) : val }}</strong>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useProjectStore } from '../stores/projectStore'
import { useMapStore } from '../stores/mapStore'
import Badge from 'primevue/badge'

const projectStore = useProjectStore()
const mapStore = useMapStore()

const selectedId = ref(null)

const classColors = ['#22c55e', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16']

const selectedAnalise = computed(() =>
  projectStore.analises.find((a) => a.id === selectedId.value)
)

function selectAnalise(analise) {
  selectedId.value = analise.id

  // Show result on map if available
  if (analise.resultado?.geojson) {
    mapStore.addLayer({
      id: `result-${analise.id}`,
      name: analise.nome || analise.tipo_analise,
      type: 'analysis',
      geojson: analise.resultado.geojson,
    })
  }
  if (analise.resultado?.layer_id) {
    mapStore.addLayer({
      id: `result-tile-${analise.id}`,
      name: `${analise.nome || analise.tipo_analise} (raster)`,
      type: 'ortomapa',
      sourceId: analise.resultado.layer_id,
    })
  }
}

function iconClass(tipo) {
  const map = {
    vegetacao: 'pi pi-sun',
    terreno: 'pi pi-chart-line',
    classificacao: 'pi pi-th-large',
    hidrologia: 'pi pi-slack',
    mudancas: 'pi pi-arrow-right-arrow-left',
    volume: 'pi pi-box',
    recorte: 'pi pi-stop',
  }
  return map[tipo] || 'pi pi-chart-bar'
}

function iconBg(tipo) {
  const map = {
    vegetacao: 'rgba(34,197,94,0.2)',
    terreno: 'rgba(245,158,11,0.2)',
    classificacao: 'rgba(139,92,246,0.2)',
    hidrologia: 'rgba(59,130,246,0.2)',
    mudancas: 'rgba(239,68,68,0.2)',
    volume: 'rgba(236,72,153,0.2)',
    recorte: 'rgba(6,182,212,0.2)',
  }
  return map[tipo] || 'rgba(107,114,128,0.2)'
}

function statusLabel(status) {
  const map = { concluida: 'OK', em_fila: 'Fila', processando: '...', erro: 'Erro' }
  return map[status] || status
}

function statusSeverity(status) {
  const map = { concluida: 'success', em_fila: 'info', processando: 'warn', erro: 'danger' }
  return map[status] || 'secondary'
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function formatArea(area) {
  if (!area) return ''
  if (area > 10000) return `${(area / 10000).toFixed(2)} ha`
  return `${area.toFixed(1)} m2`
}
</script>

<style scoped>
.analysis-results {
  margin-bottom: 8px;
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

.result-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.15s;
  margin-bottom: 2px;
}

.result-item:hover {
  background: var(--sidebar-hover);
}

.result-item.active {
  background: rgba(74, 222, 128, 0.08);
  border-left: 3px solid var(--accent);
}

.result-icon {
  width: 28px;
  height: 28px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.8rem;
  flex-shrink: 0;
}

.result-info {
  flex: 1;
  min-width: 0;
}

.result-name {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.result-date {
  font-size: 0.7rem;
  color: var(--text-dim);
}

.stats-panel {
  margin-top: 8px;
  padding: 10px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--border);
  border-radius: 8px;
}

.stats-title {
  font-size: 0.8rem;
  color: var(--text);
  margin-bottom: 8px;
}

.class-row {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.75rem;
  padding: 3px 0;
}

.class-color {
  width: 10px;
  height: 10px;
  border-radius: 2px;
  flex-shrink: 0;
}

.class-name {
  flex: 1;
  color: var(--text);
}

.class-area {
  color: var(--text-dim);
}

.class-pct {
  color: var(--text);
  font-weight: 600;
  width: 40px;
  text-align: right;
}

.bar-chart {
  margin-top: 10px;
}

.bar-row {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 4px;
}

.bar-label {
  width: 30px;
  font-size: 0.7rem;
  color: var(--text-dim);
  text-align: right;
}

.bar-track {
  flex: 1;
  height: 8px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 4px;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.3s ease;
}

.bar-value {
  width: 36px;
  font-size: 0.7rem;
  color: var(--text);
  text-align: right;
}

.general-stats {
  margin-top: 8px;
}

.stat-row {
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
  padding: 2px 0;
  color: var(--text);
}

.stat-row span {
  color: var(--text-dim);
}

.empty-state {
  text-align: center;
  color: var(--text-dim);
  font-size: 0.85rem;
  padding: 20px 8px;
}
</style>
