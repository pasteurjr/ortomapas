<template>
  <div v-if="visible" class="modal-overlay" @click.self="$emit('close')">
    <div class="modal">
      <div class="modal-header">
        <h3><i class="pi pi-download"></i> Exportar Dados</h3>
        <button class="close-btn" @click="$emit('close')"><i class="pi pi-times"></i></button>
      </div>

      <div class="modal-body">
        <div class="form-group">
          <label>Camada / Ortomapa</label>
          <select v-model="selectedSource">
            <option :value="null" disabled>Selecione...</option>
            <optgroup label="Ortomapas">
              <option v-for="o in ortomapas" :key="'orto-' + o.id" :value="{ type: 'ortomapa', id: o.id, path: o.caminho_arquivo, name: o.nome }">
                {{ o.nome }}
              </option>
            </optgroup>
            <optgroup v-if="analysisLayers.length > 0" label="Resultados de Analise">
              <option v-for="l in analysisLayers" :key="'layer-' + l.id" :value="{ type: 'analysis', id: l.id, sourceId: l.sourceId, name: l.name }">
                {{ l.name }}
              </option>
            </optgroup>
          </select>
        </div>

        <div class="form-group">
          <label>Formato de saida</label>
          <select v-model="format">
            <option value="GTiff">GeoTIFF (.tif)</option>
            <option value="PNG">PNG (.png)</option>
            <option value="JPEG">JPEG (.jpg)</option>
            <option value="KML">KML (.kml)</option>
            <option value="GeoJSON">GeoJSON (.geojson)</option>
          </select>
        </div>

        <div class="form-group">
          <label>Sistema de Coordenadas (CRS)</label>
          <select v-model="targetCrs">
            <option value="EPSG:4326">EPSG:4326 - WGS 84 (Geograficas)</option>
            <option value="EPSG:31983">EPSG:31983 - SIRGAS 2000 / UTM 23S</option>
            <option value="EPSG:31984">EPSG:31984 - SIRGAS 2000 / UTM 24S</option>
            <option value="EPSG:32723">EPSG:32723 - WGS 84 / UTM 23S</option>
            <option value="EPSG:32724">EPSG:32724 - WGS 84 / UTM 24S</option>
          </select>
        </div>

        <div class="form-group">
          <label>Resolucao (opcional, metros)</label>
          <input type="number" v-model.number="resolution" step="0.01" min="0.01" placeholder="Manter original" />
          <span class="hint">Deixe vazio para manter a resolucao original</span>
        </div>

        <div v-if="format === 'PNG' || format === 'JPEG'" class="form-group">
          <label>Qualidade ({{ quality }}%)</label>
          <input type="range" v-model.number="quality" min="10" max="100" step="5" class="slider" />
        </div>

        <div v-if="error" class="error-message">
          <i class="pi pi-exclamation-triangle"></i> {{ error }}
        </div>

        <div v-if="downloadReady" class="success-message">
          <i class="pi pi-check-circle"></i> Exportacao concluida com sucesso!
        </div>
      </div>

      <div class="modal-footer">
        <button class="btn-cancel" @click="$emit('close')">Cancelar</button>
        <button class="btn-export" @click="doExport" :disabled="!selectedSource || loading">
          <i :class="loading ? 'pi pi-spin pi-spinner' : 'pi pi-download'"></i>
          {{ loading ? 'Exportando...' : 'Exportar' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useProjectStore } from '../stores/projectStore'
import { useMapStore } from '../stores/mapStore'
import { runTool, exportLayer } from '../api/client'

const props = defineProps({ visible: Boolean })
const emit = defineEmits(['close'])

const projectStore = useProjectStore()
const mapStore = useMapStore()

const ortomapas = computed(() => projectStore.ortomapas)
const analysisLayers = computed(() =>
  mapStore.activeLayers.filter((l) => l.type === 'analysis')
)

const selectedSource = ref(null)
const format = ref('GTiff')
const targetCrs = ref('EPSG:4326')
const resolution = ref(null)
const quality = ref(90)
const loading = ref(false)
const error = ref(null)
const downloadReady = ref(false)

async function doExport() {
  if (!selectedSource.value) return
  loading.value = true
  error.value = null
  downloadReady.value = false

  try {
    const params = {
      format: format.value,
      crs: targetCrs.value,
    }

    if (selectedSource.value.type === 'ortomapa') {
      params.input_path = selectedSource.value.path
      params.ortomapa_id = selectedSource.value.id
    } else {
      params.layer_id = selectedSource.value.sourceId || selectedSource.value.id
    }

    if (resolution.value && resolution.value > 0) {
      params.resolution = resolution.value
    }

    if ((format.value === 'PNG' || format.value === 'JPEG') && quality.value < 100) {
      params.quality = quality.value
    }

    const res = await exportLayer(params)

    // Handle blob download
    const blob = res.data || res
    const url = window.URL.createObjectURL(blob instanceof Blob ? blob : new Blob([blob]))
    const link = document.createElement('a')
    link.href = url

    const extensions = { GTiff: 'tif', PNG: 'png', JPEG: 'jpg', KML: 'kml', GeoJSON: 'geojson' }
    const ext = extensions[format.value] || 'dat'
    const safeName = (selectedSource.value.name || 'export').replace(/[^a-zA-Z0-9_-]/g, '_')
    link.download = `${safeName}_${Date.now()}.${ext}`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)

    downloadReady.value = true
  } catch (e) {
    // If blob export fails, try with URL approach
    if (e.response?.data?.output_path) {
      window.open(`/data/${e.response.data.output_path}`, '_blank')
      downloadReady.value = true
    } else {
      error.value = e.response?.data?.detail || e.message || 'Erro ao exportar'
    }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.65);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(2px);
}

.modal {
  background: #1e1e2e;
  border-radius: 12px;
  width: 440px;
  max-width: 92vw;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
  border: 1px solid #313244;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px 12px;
  border-bottom: 1px solid #313244;
}

.modal-header h3 {
  margin: 0;
  color: #cdd6f4;
  font-size: 1rem;
  display: flex;
  align-items: center;
  gap: 8px;
}

.close-btn {
  background: none;
  border: none;
  color: #6c7086;
  cursor: pointer;
  font-size: 1rem;
  padding: 4px;
  border-radius: 4px;
  transition: all 0.15s;
}

.close-btn:hover {
  color: #cdd6f4;
  background: #313244;
}

.modal-body {
  padding: 16px 20px;
  overflow-y: auto;
  flex: 1;
}

.form-group {
  margin-bottom: 14px;
}

.form-group label {
  display: block;
  font-size: 0.78rem;
  font-weight: 500;
  color: #a6adc8;
  margin-bottom: 5px;
}

.form-group select,
.form-group input[type="number"] {
  width: 100%;
  padding: 8px 10px;
  background: #181825;
  border: 1px solid #313244;
  border-radius: 6px;
  color: #cdd6f4;
  font-size: 0.82rem;
  box-sizing: border-box;
  transition: border-color 0.15s;
}

.form-group select:focus,
.form-group input:focus {
  outline: none;
  border-color: #89b4fa;
}

.slider {
  width: 100%;
  accent-color: #89b4fa;
}

.hint {
  display: block;
  font-size: 0.7rem;
  color: #585b70;
  margin-top: 3px;
  font-style: italic;
}

.error-message {
  padding: 8px 12px;
  background: rgba(243, 139, 168, 0.1);
  border: 1px solid rgba(243, 139, 168, 0.3);
  border-radius: 6px;
  color: #f38ba8;
  font-size: 0.8rem;
  display: flex;
  align-items: center;
  gap: 6px;
}

.success-message {
  padding: 8px 12px;
  background: rgba(166, 227, 161, 0.1);
  border: 1px solid rgba(166, 227, 161, 0.3);
  border-radius: 6px;
  color: #a6e3a1;
  font-size: 0.8rem;
  display: flex;
  align-items: center;
  gap: 6px;
}

.modal-footer {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
  padding: 12px 20px 16px;
  border-top: 1px solid #313244;
}

.btn-cancel {
  padding: 8px 18px;
  background: #313244;
  border: 1px solid #45475a;
  border-radius: 6px;
  color: #cdd6f4;
  cursor: pointer;
  font-size: 0.82rem;
  transition: all 0.15s;
}

.btn-cancel:hover {
  background: #45475a;
}

.btn-export {
  padding: 8px 20px;
  background: #a6e3a1;
  border: none;
  border-radius: 6px;
  color: #1e1e2e;
  cursor: pointer;
  font-weight: 600;
  font-size: 0.82rem;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.15s;
}

.btn-export:hover:not(:disabled) {
  background: #94e2d5;
}

.btn-export:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
