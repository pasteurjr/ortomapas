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
              <option value="twi">Indice Topografico de Umidade (TWI)</option>
              <option value="watershed">Bacia Hidrografica</option>
              <option value="drainage">Rede de Drenagem</option>
            </select>
          </div>
          <div v-if="params.hydro_type === 'drainage'" class="form-group">
            <label>Área contribuinte mínima (m²)</label>
            <input type="number" v-model.number="params.minimum_area_m2" min="1" max="1000000000" step="100" />
            <label>Ordem de Strahler mínima</label>
            <input type="number" v-model.number="params.minimum_strahler_order" min="1" max="12" step="1" />
            <span class="hint">Ordem 1 preserva a rede completa; ordens maiores removem tributários de menor hierarquia.</span>
            <span class="hint">A saída é uma rede potencial D8. Prefira um DTM; a análise usa uma grade generalizada de até 256 pixels por lado.</span>
          </div>
          <div v-if="params.hydro_type === 'watershed'" class="form-group outlet-picker">
            <button type="button" class="btn-pick-outlet" @click="pickOutlet">{{ params.outlet ? 'Alterar exutório no mapa' : 'Escolher exutório no mapa' }}</button>
            <span v-if="params.outlet" class="hint">Ponto selecionado: {{ params.outlet.lat.toFixed(6) }}, {{ params.outlet.lng.toFixed(6) }}</span>
            <span v-else class="hint">Clique no botão e marque no mapa o ponto de saída da bacia.</span>
            <label>Raio para ajustar o ponto ao canal (m)</label>
            <input type="number" v-model.number="params.snap_radius_m" min="0" max="1000" step="1" />
            <span class="hint">Dentro do raio, o algoritmo usa a célula de maior acumulação D8.</span>
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

        <div v-if="queueEligible" class="form-group queue-task-group">
          <label class="checkbox-label">
            <input type="checkbox" v-model="form.queue_task" />
            <span>Enviar para fila de processamento</span>
          </label>
          <span class="hint">{{ queueHelp }}</span>
        </div>
        <div v-else-if="queueUnavailableHint" class="form-group queue-task-group queue-unavailable">
          <span class="hint">{{ queueUnavailableHint }}</span>
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
import { ref, reactive, computed, watch } from 'vue'
import { useProjectStore } from '../stores/projectStore'
import { useMapStore } from '../stores/mapStore'
import { createAnalise } from '../api/client'

const props = defineProps({ visible: Boolean })
const emit = defineEmits(['close', 'created', 'select-outlet', 'outlet-selected'])

const projectStore = useProjectStore()
const mapStore = useMapStore()
const ortomapas = computed(() => projectStore.ortomapas)
const selectedSource = computed(() => ortomapas.value.find(item => String(item.id) === String(form.ortomapa_id)))
const sourceType = computed(() => String(selectedSource.value?.tipo || '').toLowerCase())
const queueOperationCandidate = computed(() => ['classificacao_solo', 'indice_vegetacao', 'terreno', 'hidrologia'].includes(form.tipo_analise))
const queueOperationSupported = computed(() =>
  (form.tipo_analise === 'classificacao_solo' && params.algorithm === 'kmeans') ||
  form.tipo_analise === 'indice_vegetacao' ||
  (form.tipo_analise === 'terreno' && ['slope', 'aspect', 'hillshade', 'contours'].includes(params.terrain_type)) ||
  (form.tipo_analise === 'hidrologia' && ['flow_direction', 'flow_accumulation', 'twi', 'drainage', 'watershed'].includes(params.hydro_type))
)
const sourceSupportsQueueOperation = computed(() => {
  if (['terreno', 'hidrologia'].includes(form.tipo_analise)) return ['dsm', 'dtm'].includes(sourceType.value)
  return ['ortomosaico', 'rgb', 'multispectral'].includes(sourceType.value)
})
const queueEligible = computed(() => queueOperationSupported.value && sourceSupportsQueueOperation.value)
const queueUnavailableHint = computed(() => {
  if (!queueOperationCandidate.value) return ''
  if (form.tipo_analise === 'terreno' && !['slope', 'aspect', 'hillshade', 'contours'].includes(params.terrain_type))
    return 'A fila de terreno cobre declividade, orientacao, hillshade e curvas de nivel.'
  if (form.tipo_analise === 'hidrologia' && !['flow_direction', 'flow_accumulation', 'twi', 'drainage', 'watershed'].includes(params.hydro_type))
    return 'Operação hidrológica indisponível na fila.'
  if (form.tipo_analise === 'classificacao_solo' && params.algorithm !== 'kmeans')
    return 'A fila por agente cobre K-Means. Random Forest e SVM continuam no fluxo de classificacao existente.'
  if (!selectedSource.value) return 'Selecione um raster compatível para habilitar a fila.'
  if (form.tipo_analise === 'terreno' && !sourceSupportsQueueOperation.value)
    return 'A fila de terreno requer um DSM ou DTM; selecione um desses produtos acima.'
  if (form.tipo_analise === 'hidrologia' && !sourceSupportsQueueOperation.value)
    return 'A fila hidrológica requer um DSM ou DTM; selecione um desses produtos acima.'
  if (form.tipo_analise !== 'terreno' && !sourceSupportsQueueOperation.value)
    return 'A fila RGB requer um ortomosaico ou raster multiespectral com pelo menos três bandas.'
  return ''
})
const queueHelp = computed(() => {
  if (form.tipo_analise === 'indice_vegetacao')
    return 'Enfileira VARI, TGI, ExG ou GLI em ortomosaico RGB; calcula o GeoTIFF e as estatisticas em segundo plano.'
  if (form.tipo_analise === 'terreno')
    return 'Enfileira declividade, orientacao, hillshade ou curvas (intervalo em metros) em DSM/DTM; o resultado aparece no mapa.'
  if (form.tipo_analise === 'hidrologia')
    if (params.hydro_type === 'watershed') return 'Delimita a bacia D8 a montante do exutório. A grade é generalizada; confira a resolução informada no resultado.'
    if (params.hydro_type === 'drainage') return 'Extrai a rede potencial D8 usando área contribuinte mínima; o resultado vetorial aparece no mapa.'
    return 'Enfileira direção D8, acumulação de fluxo ou TWI sobre DSM/DTM. O produto será salvo e exibido no mapa.'
  return 'Enfileira a classificacao RGB K-Means (2 a 12 grupos) em raster com CRS projetado, para calcular areas e processar em segundo plano.'
})
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
  minimum_area_m2: 1000,
  minimum_strahler_order: 1,
  outlet: null,
  snap_radius_m: 5,
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
  if (!queueEligible.value) form.queue_task = false
}

function pickOutlet() {
  const source = selectedSource.value
  if (source) {
    const layerId = `orto-${source.id}`
    const activeLayer = mapStore.activeLayers.find((layer) => layer.id === layerId)
    if (!activeLayer) {
      mapStore.addLayer({ id: layerId, name: source.nome, type: 'ortomapa', sourceId: source.id })
    } else {
      activeLayer.visible = true
    }
    mapStore.requestLayerFit(layerId)
  }
  mapStore.setPourPointCallback((lat, lng) => {
    params.outlet = { lat, lng }
    emit('outlet-selected')
  })
  emit('select-outlet')
}

watch(() => params.algorithm, (algorithm) => {
  if (algorithm !== 'kmeans') form.queue_task = false
})

watch(() => params.terrain_type, (terrainType) => {
  if (!['slope', 'aspect', 'hillshade', 'contours'].includes(terrainType)) form.queue_task = false
})

watch(() => params.hydro_type, (hydroType) => {
  if (!['flow_direction', 'flow_accumulation', 'twi', 'drainage', 'watershed'].includes(hydroType)) form.queue_task = false
})

watch(() => form.ortomapa_id, () => {
  if (!queueEligible.value) form.queue_task = false
})

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
      if (params.hydro_type === 'drainage') {
        hp.minimum_area_m2 = params.minimum_area_m2
        hp.minimum_strahler_order = params.minimum_strahler_order
      }
      if (params.hydro_type === 'watershed') {
        hp.outlet = params.outlet
        hp.snap_radius_m = params.snap_radius_m
      }
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
  if (form.queue_task && form.tipo_analise === 'hidrologia' && params.hydro_type === 'watershed' && !params.outlet) {
    error.value = 'Escolha o exutório no mapa antes de enfileirar a delimitação da bacia.'
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
