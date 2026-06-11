<template>
  <div v-if="visible" class="modal-overlay" @click.self="$emit('close')">
    <div class="modal">
      <div class="modal-header">
        <h3><i class="pi pi-chart-bar"></i> Nova Analise</h3>
        <button class="close-btn" @click="$emit('close')"><i class="pi pi-times"></i></button>
      </div>

      <div class="modal-body">
        <div class="form-group">
          <label>Ortomapa</label>
          <select v-model="form.ortomapa_id">
            <option :value="null" disabled>Selecione um ortomapa...</option>
            <option v-for="o in ortomapas" :key="o.id" :value="o.id">
              {{ o.nome }} {{ o.tipo ? `(${o.tipo})` : '' }}
            </option>
          </select>
        </div>

        <div class="form-group">
          <label>Nome da Analise</label>
          <input v-model="form.nome" placeholder="Ex: NDVI Fazenda Norte - Mar 2026" />
        </div>

        <div class="form-group">
          <label>Tipo de Analise</label>
          <select v-model="form.tipo_analise" @change="onTipoChange">
            <option value="indice_vegetacao">Indice de Vegetacao</option>
            <option value="classificacao_solo">Classificacao de Solo</option>
            <option value="terreno">Analise de Terreno</option>
            <option value="hidrologia">Analise Hidrologica</option>
            <option value="deteccao_mudancas">Deteccao de Mudancas</option>
            <option value="calculo_volume">Calculo de Volume</option>
            <option value="segmentacao">Segmentacao</option>
            <option value="ndvi_rgb">NDVI RGB Estimado</option>
          </select>
        </div>

        <!-- Parametros: Indice de Vegetacao -->
        <template v-if="form.tipo_analise === 'indice_vegetacao'">
          <div class="form-group">
            <label>Indice</label>
            <select v-model="params.index_name">
              <option value="VARI">VARI - Visible Atmospherically Resistant Index</option>
              <option value="TGI">TGI - Triangular Greenness Index</option>
              <option value="ExG">ExG - Excess Green</option>
              <option value="GLI">GLI - Green Leaf Index</option>
            </select>
          </div>
          <div class="form-group">
            <label>Limiar de vegetacao (opcional)</label>
            <input type="number" v-model.number="params.threshold" step="0.01" min="-1" max="1" placeholder="0.1" />
            <span class="hint">Valores acima deste limiar serao classificados como vegetacao</span>
          </div>
        </template>

        <!-- Parametros: Classificacao de Solo -->
        <template v-if="form.tipo_analise === 'classificacao_solo'">
          <div class="form-group">
            <label>Algoritmo</label>
            <select v-model="params.algorithm">
              <option value="kmeans">K-Means (nao-supervisionado)</option>
              <option value="random_forest">Random Forest (supervisionado)</option>
              <option value="svm">SVM - Support Vector Machine</option>
            </select>
          </div>
          <div class="form-group">
            <label>Numero de classes</label>
            <input type="number" v-model.number="params.n_classes" min="2" max="20" />
          </div>
          <div v-if="params.algorithm === 'random_forest' || params.algorithm === 'svm'" class="form-group">
            <label>Amostras de treino (GeoJSON, opcional)</label>
            <textarea v-model="params.training_geojson" rows="3" placeholder='{"type":"FeatureCollection",...}'></textarea>
          </div>
        </template>

        <!-- Parametros: Terreno -->
        <template v-if="form.tipo_analise === 'terreno'">
          <div class="form-group">
            <label>Tipo</label>
            <select v-model="params.terrain_type">
              <option value="slope">Declividade (Slope)</option>
              <option value="aspect">Orientacao (Aspect)</option>
              <option value="hillshade">Sombreamento (Hillshade)</option>
              <option value="contours">Curvas de Nivel</option>
            </select>
          </div>
          <div v-if="params.terrain_type === 'contours'" class="form-group">
            <label>Intervalo de curvas (m)</label>
            <input type="number" v-model.number="params.interval" step="0.5" min="0.5" />
          </div>
          <div v-if="params.terrain_type === 'hillshade'" class="form-group">
            <label>Azimute solar (graus)</label>
            <input type="number" v-model.number="params.azimuth" min="0" max="360" step="1" />
          </div>
          <div v-if="params.terrain_type === 'hillshade'" class="form-group">
            <label>Elevacao solar (graus)</label>
            <input type="number" v-model.number="params.altitude" min="0" max="90" step="1" />
          </div>
        </template>

        <!-- Parametros: Hidrologia -->
        <template v-if="form.tipo_analise === 'hidrologia'">
          <div class="form-group">
            <label>Tipo</label>
            <select v-model="params.hydro_type">
              <option value="flow_direction">Direcao de Fluxo</option>
              <option value="flow_accumulation">Acumulacao de Fluxo</option>
              <option value="watershed">Bacia Hidrografica</option>
              <option value="drainage">Rede de Drenagem</option>
            </select>
          </div>
          <div v-if="params.hydro_type === 'drainage'" class="form-group">
            <label>Limiar de acumulacao</label>
            <input type="number" v-model.number="params.accumulation_threshold" min="10" step="10" />
          </div>
        </template>

        <!-- Parametros: Deteccao de Mudancas -->
        <template v-if="form.tipo_analise === 'deteccao_mudancas'">
          <div class="form-group">
            <label>Ortomapa de referencia (antes)</label>
            <select v-model="params.reference_id">
              <option :value="null" disabled>Selecione...</option>
              <option v-for="o in ortomapas" :key="o.id" :value="o.id">{{ o.nome }}</option>
            </select>
          </div>
          <div class="form-group">
            <label>Metodo</label>
            <select v-model="params.change_method">
              <option value="difference">Diferenca Simples</option>
              <option value="ratio">Razao de Bandas</option>
              <option value="ndvi_diff">Diferenca de NDVI</option>
            </select>
          </div>
          <div class="form-group">
            <label>Limiar: {{ (params.change_threshold || 0.15).toFixed(2) }}</label>
            <input type="range" v-model.number="params.change_threshold" min="0.01" max="1" step="0.01" class="slider" />
          </div>
        </template>

        <!-- Parametros: Calculo de Volume -->
        <template v-if="form.tipo_analise === 'calculo_volume'">
          <div class="form-group">
            <label>Elevacao de referencia (m)</label>
            <input type="number" v-model.number="params.reference_elevation" step="0.1" />
          </div>
          <div class="form-group">
            <label>Tipo de calculo</label>
            <select v-model="params.volume_type">
              <option value="cut">Corte (acima da referencia)</option>
              <option value="fill">Aterro (abaixo da referencia)</option>
              <option value="both">Corte e aterro</option>
            </select>
          </div>
        </template>

        <!-- Parametros: Segmentacao -->
        <template v-if="form.tipo_analise === 'segmentacao'">
          <div class="form-group">
            <label>Tamanho minimo do segmento (pixels)</label>
            <input type="number" v-model.number="params.min_segment_size" min="10" step="10" />
          </div>
          <div class="form-group">
            <label>Compacidade</label>
            <input type="number" v-model.number="params.compactness" step="0.1" min="0" max="1" />
            <span class="hint">0 = mais irregular, 1 = mais compacto</span>
          </div>
        </template>

        <!-- Parametros: NDVI RGB -->
        <template v-if="form.tipo_analise === 'ndvi_rgb'">
          <div class="form-group">
            <label>Metodo de estimativa</label>
            <select v-model="params.ndvi_method">
              <option value="excess_green">Excess Green (ExG)</option>
              <option value="vari">VARI</option>
              <option value="tgi">TGI</option>
            </select>
          </div>
        </template>

        <div class="form-group queue-task-group">
          <label class="checkbox-label">
            <input type="checkbox" v-model="form.queue_task" />
            <span>Executar via Agente de IA</span>
          </label>
          <span class="hint">Quando ativado, a analise sera enfileirada para processamento automatico por agente de IA</span>
        </div>

        <div v-if="error" class="error-message">
          <i class="pi pi-exclamation-triangle"></i> {{ error }}
        </div>
      </div>

      <div class="modal-footer">
        <button class="btn-cancel" @click="$emit('close')">Cancelar</button>
        <button class="btn-submit" @click="submit" :disabled="loading || !form.ortomapa_id || !form.nome">
          <i :class="loading ? 'pi pi-spin pi-spinner' : 'pi pi-play'"></i>
          {{ loading ? 'Criando...' : 'Criar e Executar' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { useProjectStore } from '../stores/projectStore'
import { createAnalise } from '../api/client'

const props = defineProps({ visible: Boolean })
const emit = defineEmits(['close', 'created'])

const projectStore = useProjectStore()
const ortomapas = computed(() => projectStore.ortomapas)
const loading = ref(false)
const error = ref(null)

const form = reactive({
  ortomapa_id: null,
  tipo_analise: 'indice_vegetacao',
  nome: '',
  queue_task: false,
})

const params = reactive({
  // Vegetacao
  index_name: 'VARI',
  threshold: 0.1,
  // Classificacao
  algorithm: 'kmeans',
  n_classes: 5,
  training_geojson: '',
  // Terreno
  terrain_type: 'slope',
  interval: 5,
  azimuth: 315,
  altitude: 45,
  // Hidrologia
  hydro_type: 'flow_direction',
  accumulation_threshold: 100,
  // Mudancas
  reference_id: null,
  change_method: 'difference',
  change_threshold: 0.15,
  // Volume
  reference_elevation: 0,
  volume_type: 'both',
  // Segmentacao
  min_segment_size: 50,
  compactness: 0.5,
  // NDVI RGB
  ndvi_method: 'excess_green',
})

function onTipoChange() {
  error.value = null
}

function getRelevantParams() {
  const tipo = form.tipo_analise
  switch (tipo) {
    case 'indice_vegetacao':
      return { index_name: params.index_name, threshold: params.threshold }
    case 'classificacao_solo': {
      const cp = { algorithm: params.algorithm, n_classes: params.n_classes }
      if (params.training_geojson) cp.training_geojson = params.training_geojson
      return cp
    }
    case 'terreno': {
      const tp = { terrain_type: params.terrain_type }
      if (params.terrain_type === 'contours') tp.interval = params.interval
      if (params.terrain_type === 'hillshade') {
        tp.azimuth = params.azimuth
        tp.altitude = params.altitude
      }
      return tp
    }
    case 'hidrologia': {
      const hp = { hydro_type: params.hydro_type }
      if (params.hydro_type === 'drainage') hp.accumulation_threshold = params.accumulation_threshold
      return hp
    }
    case 'deteccao_mudancas':
      return {
        reference_id: params.reference_id,
        change_method: params.change_method,
        change_threshold: params.change_threshold,
      }
    case 'calculo_volume':
      return {
        reference_elevation: params.reference_elevation,
        volume_type: params.volume_type,
      }
    case 'segmentacao':
      return {
        min_segment_size: params.min_segment_size,
        compactness: params.compactness,
      }
    case 'ndvi_rgb':
      return { ndvi_method: params.ndvi_method }
    default:
      return {}
  }
}

async function submit() {
  if (!form.ortomapa_id || !form.nome) {
    error.value = 'Preencha o ortomapa e o nome da analise.'
    return
  }
  loading.value = true
  error.value = null
  try {
    const data = {
      ortomapa_id: form.ortomapa_id,
      projeto_id: projectStore.activeProject?.id,
      tipo_analise: form.tipo_analise,
      nome: form.nome,
      parametros: JSON.stringify(getRelevantParams()),
      queue_task: form.queue_task,
    }
    const res = await createAnalise(data)
    await projectStore.fetchAnalises()
    emit('created', res.data)
    emit('close')
    // Reset form
    form.ortomapa_id = null
    form.nome = ''
    form.tipo_analise = 'indice_vegetacao'
    form.queue_task = false
  } catch (e) {
    error.value = e.response?.data?.detail || e.message || 'Erro ao criar analise'
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
  width: 480px;
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
.form-group input[type="text"],
.form-group input[type="number"],
.form-group input:not([type]),
.form-group textarea {
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
.form-group input:focus,
.form-group textarea:focus {
  outline: none;
  border-color: #89b4fa;
}

.form-group textarea {
  resize: vertical;
  font-family: monospace;
  font-size: 0.72rem;
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

.queue-task-group {
  padding: 10px;
  background: rgba(137, 180, 250, 0.05);
  border: 1px solid rgba(137, 180, 250, 0.15);
  border-radius: 6px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-size: 0.82rem;
  color: #cdd6f4;
}

.checkbox-label input[type="checkbox"] {
  accent-color: #89b4fa;
  width: 16px;
  height: 16px;
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

.btn-submit {
  padding: 8px 20px;
  background: #89b4fa;
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

.btn-submit:hover:not(:disabled) {
  background: #74c7ec;
}

.btn-submit:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
