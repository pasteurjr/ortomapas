<template>
  <div class="tools-panel">
    <h3 class="section-title"><i class="pi pi-wrench"></i> Ferramentas de Analise</h3>
    <Tabs :value="activeTab" @update:value="activeTab = $event">
      <TabList>
        <Tab value="vegetacao"><i class="pi pi-sun"></i> Veg</Tab>
        <Tab value="terreno"><i class="pi pi-chart-line"></i> Ter</Tab>
        <Tab value="classificacao"><i class="pi pi-th-large"></i> Cls</Tab>
        <Tab value="hidrologia"><i class="pi pi-slack"></i> Hid</Tab>
        <Tab value="mudancas"><i class="pi pi-arrow-right-arrow-left"></i> Mud</Tab>
        <Tab value="volume"><i class="pi pi-box"></i> Vol</Tab>
        <Tab value="recorte"><i class="pi pi-stop"></i> Rec</Tab>
        <Tab value="exportar"><i class="pi pi-download"></i> Exp</Tab>
      </TabList>

      <TabPanels>
        <!-- Vegetacao -->
        <TabPanel value="vegetacao">
          <div class="tool-form">
            <div class="form-group">
              <label>Ortomapa</label>
              <Select
                v-model="veg.ortomapaId"
                :options="ortoOptions"
                optionLabel="label"
                optionValue="value"
                placeholder="Selecionar..."
                class="w-full"
              />
            </div>
            <div class="form-group">
              <label>Indice de Vegetacao</label>
              <Select
                v-model="veg.index"
                :options="vegIndices"
                optionLabel="label"
                optionValue="value"
                class="w-full"
              />
            </div>
            <Button
              label="Calcular Indice"
              icon="pi pi-play"
              :loading="veg.loading"
              @click="runVegetacao"
              class="w-full"
            />
            <div v-if="veg.result" class="result-stats">
              <h4>Resultado</h4>
              <div class="stat-row"><span>Min:</span> <strong>{{ veg.result.min?.toFixed(3) }}</strong></div>
              <div class="stat-row"><span>Max:</span> <strong>{{ veg.result.max?.toFixed(3) }}</strong></div>
              <div class="stat-row"><span>Media:</span> <strong>{{ veg.result.mean?.toFixed(3) }}</strong></div>
              <div class="stat-row"><span>Desvio:</span> <strong>{{ veg.result.std?.toFixed(3) }}</strong></div>
            </div>
          </div>
        </TabPanel>

        <!-- Terreno -->
        <TabPanel value="terreno">
          <div class="tool-form">
            <div class="form-group">
              <label>Modelo (DSM/DTM)</label>
              <Select
                v-model="terreno.ortomapaId"
                :options="dsmDtmOptions"
                optionLabel="label"
                optionValue="value"
                placeholder="Selecionar..."
                class="w-full"
              />
            </div>
            <div class="form-group">
              <label>Analise</label>
              <Select
                v-model="terreno.tipo"
                :options="terrenoTypes"
                optionLabel="label"
                optionValue="value"
                class="w-full"
              />
            </div>
            <div v-if="terreno.tipo === 'contours'" class="form-group">
              <label>Intervalo (m)</label>
              <InputText v-model.number="terreno.interval" type="number" class="w-full" />
            </div>
            <Button
              label="Gerar Analise"
              icon="pi pi-play"
              :loading="terreno.loading"
              @click="runTerreno"
              class="w-full"
            />
          </div>
        </TabPanel>

        <!-- Classificacao -->
        <TabPanel value="classificacao">
          <div class="tool-form">
            <div class="form-group">
              <label>Ortomapa</label>
              <Select
                v-model="classif.ortomapaId"
                :options="ortoOptions"
                optionLabel="label"
                optionValue="value"
                placeholder="Selecionar..."
                class="w-full"
              />
            </div>
            <div class="form-group">
              <label>Algoritmo</label>
              <Select
                v-model="classif.algorithm"
                :options="classifAlgorithms"
                optionLabel="label"
                optionValue="value"
                class="w-full"
              />
            </div>
            <div class="form-group">
              <label>Num. Classes</label>
              <InputText v-model.number="classif.numClasses" type="number" class="w-full" />
            </div>
            <Button
              v-if="classif.algorithm === 'RF'"
              label="Desenhar Areas de Treino"
              icon="pi pi-pencil"
              severity="secondary"
              @click="startDrawTraining"
              class="w-full mb-2"
            />
            <Button
              label="Classificar"
              icon="pi pi-play"
              :loading="classif.loading"
              @click="runClassificacao"
              class="w-full"
            />
          </div>
        </TabPanel>

        <!-- Hidrologia -->
        <TabPanel value="hidrologia">
          <div class="tool-form">
            <div class="form-group">
              <label>DTM</label>
              <Select
                v-model="hidro.ortomapaId"
                :options="dsmDtmOptions"
                optionLabel="label"
                optionValue="value"
                placeholder="Selecionar..."
                class="w-full"
              />
            </div>
            <div class="form-group">
              <label>Analise</label>
              <Select
                v-model="hidro.tipo"
                :options="hidroTypes"
                optionLabel="label"
                optionValue="value"
                class="w-full"
              />
            </div>
            <div class="form-group">
              <label>Limiar de Acumulacao</label>
              <InputText v-model.number="hidro.threshold" type="number" class="w-full" />
            </div>
            <template v-if="hidro.tipo === 'watershed'">
              <div class="form-group">
                <label>Ponto de Exutorio (Latitude)</label>
                <InputText v-model.number="hidro.pourLat" type="number" step="0.000001" class="w-full" placeholder="Clique no mapa ou digite" />
              </div>
              <div class="form-group">
                <label>Ponto de Exutorio (Longitude)</label>
                <InputText v-model.number="hidro.pourLon" type="number" step="0.000001" class="w-full" placeholder="Clique no mapa ou digite" />
              </div>
              <Button
                label="Capturar do Mapa"
                icon="pi pi-map-marker"
                severity="secondary"
                size="small"
                @click="enablePourPointCapture"
                class="w-full mb-2"
              />
            </template>
            <Button
              label="Executar"
              icon="pi pi-play"
              :loading="hidro.loading"
              @click="runHidrologia"
              class="w-full"
            />
          </div>
        </TabPanel>

        <!-- Mudancas -->
        <TabPanel value="mudancas">
          <div class="tool-form">
            <div class="form-group">
              <label>Ortomapa Antes</label>
              <Select
                v-model="mudanca.antesId"
                :options="ortoOptions"
                optionLabel="label"
                optionValue="value"
                placeholder="Selecionar..."
                class="w-full"
              />
            </div>
            <div class="form-group">
              <label>Ortomapa Depois</label>
              <Select
                v-model="mudanca.depoisId"
                :options="ortoOptions"
                optionLabel="label"
                optionValue="value"
                placeholder="Selecionar..."
                class="w-full"
              />
            </div>
            <div class="form-group">
              <label>Limiar: {{ mudanca.threshold.toFixed(2) }}</label>
              <input
                type="range"
                v-model.number="mudanca.threshold"
                min="0"
                max="1"
                step="0.01"
                class="slider"
              />
            </div>
            <Button
              label="Detectar Mudancas"
              icon="pi pi-play"
              :loading="mudanca.loading"
              @click="runMudancas"
              class="w-full"
            />
          </div>
        </TabPanel>

        <!-- Volume -->
        <TabPanel value="volume">
          <div class="tool-form">
            <div class="form-group">
              <label>DSM</label>
              <Select
                v-model="volume.ortomapaId"
                :options="dsmDtmOptions"
                optionLabel="label"
                optionValue="value"
                placeholder="Selecionar..."
                class="w-full"
              />
            </div>
            <div class="form-group">
              <label>Elevacao de Referencia (m)</label>
              <InputText v-model.number="volume.refElevation" type="number" class="w-full" />
            </div>
            <Button
              label="Calcular Volume"
              icon="pi pi-play"
              :loading="volume.loading"
              @click="runVolume"
              class="w-full"
            />
            <div v-if="volume.result" class="result-stats">
              <h4>Resultado</h4>
              <div class="stat-row"><span>Volume Corte:</span> <strong>{{ volume.result.cut?.toFixed(1) }} m3</strong></div>
              <div class="stat-row"><span>Volume Aterro:</span> <strong>{{ volume.result.fill?.toFixed(1) }} m3</strong></div>
              <div class="stat-row"><span>Volume Liquido:</span> <strong>{{ volume.result.net?.toFixed(1) }} m3</strong></div>
            </div>
          </div>
        </TabPanel>

        <!-- Recorte -->
        <TabPanel value="recorte">
          <div class="tool-form">
            <div class="form-group">
              <label>Ortomapa</label>
              <Select
                v-model="recorte.ortomapaId"
                :options="ortoOptions"
                optionLabel="label"
                optionValue="value"
                placeholder="Selecionar..."
                class="w-full"
              />
            </div>
            <Button
              label="Desenhar Poligono de Recorte"
              icon="pi pi-pencil"
              severity="secondary"
              @click="startDrawClip"
              class="w-full mb-2"
            />
            <Button
              label="Recortar"
              icon="pi pi-play"
              :loading="recorte.loading"
              :disabled="!recorte.polygon"
              @click="runRecorte"
              class="w-full"
            />
          </div>
        </TabPanel>

        <!-- Exportar -->
        <TabPanel value="exportar">
          <div class="tool-form">
            <div class="form-group">
              <label>Camada / Ortomapa</label>
              <Select
                v-model="exportar.layerId"
                :options="allLayerOptions"
                optionLabel="label"
                optionValue="value"
                placeholder="Selecionar..."
                class="w-full"
              />
            </div>
            <div class="form-group">
              <label>Formato</label>
              <Select
                v-model="exportar.format"
                :options="exportFormats"
                optionLabel="label"
                optionValue="value"
                class="w-full"
              />
            </div>
            <div class="form-group">
              <label>CRS</label>
              <Select
                v-model="exportar.crs"
                :options="crsOptions"
                optionLabel="label"
                optionValue="value"
                class="w-full"
              />
            </div>
            <Button
              label="Exportar"
              icon="pi pi-download"
              :loading="exportar.loading"
              @click="runExport"
              class="w-full"
            />
          </div>
        </TabPanel>
      </TabPanels>
    </Tabs>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { useProjectStore } from '../stores/projectStore'
import { useMapStore } from '../stores/mapStore'
import { runTool, exportLayer } from '../api/client'
import Select from 'primevue/select'
import InputText from 'primevue/inputtext'
import Button from 'primevue/button'
import Tabs from 'primevue/tabs'
import TabList from 'primevue/tablist'
import Tab from 'primevue/tab'
import TabPanels from 'primevue/tabpanels'
import TabPanel from 'primevue/tabpanel'

const projectStore = useProjectStore()
const mapStore = useMapStore()
const activeTab = ref('vegetacao')

const ortoOptions = computed(() =>
  projectStore.ortomapas.map((o) => ({ label: o.nome, value: o.id }))
)

const dsmDtmOptions = computed(() =>
  projectStore.ortomapas
    .filter((o) => ['DSM', 'DTM'].includes(o.tipo))
    .map((o) => ({ label: `${o.nome} (${o.tipo})`, value: o.id }))
)

const allLayerOptions = computed(() => [
  ...ortoOptions.value,
  ...mapStore.activeLayers
    .filter((l) => l.type === 'analysis')
    .map((l) => ({ label: l.name, value: l.id })),
])

const vegIndices = [
  { label: 'VARI - Visible Atmospherically Resistant Index', value: 'VARI' },
  { label: 'TGI - Triangular Greenness Index', value: 'TGI' },
  { label: 'ExG - Excess Green', value: 'ExG' },
  { label: 'GLI - Green Leaf Index', value: 'GLI' },
]

const terrenoTypes = [
  { label: 'Declividade (Slope)', value: 'slope' },
  { label: 'Aspecto (Aspect)', value: 'aspect' },
  { label: 'Curvas de Nivel (Contours)', value: 'contours' },
  { label: 'Sombreamento (Hillshade)', value: 'hillshade' },
]

const classifAlgorithms = [
  { label: 'Random Forest (Supervisionado)', value: 'RF' },
  { label: 'K-Means (Nao Supervisionado)', value: 'KMeans' },
]

const hidroTypes = [
  { label: 'Bacias Hidrograficas (Watershed)', value: 'watershed' },
  { label: 'Rede de Drenagem (Streams)', value: 'streams' },
  { label: 'TWI - Indice Topografico', value: 'TWI' },
]

const exportFormats = [
  { label: 'GeoTIFF', value: 'geotiff' },
  { label: 'PNG', value: 'png' },
  { label: 'JPEG', value: 'jpeg' },
  { label: 'KML', value: 'kml' },
  { label: 'GeoJSON', value: 'geojson' },
  { label: 'Shapefile', value: 'shapefile' },
]

const crsOptions = [
  { label: 'EPSG:4326 (WGS 84)', value: 'EPSG:4326' },
  { label: 'EPSG:31983 (SIRGAS 2000 / UTM 23S)', value: 'EPSG:31983' },
  { label: 'EPSG:31984 (SIRGAS 2000 / UTM 24S)', value: 'EPSG:31984' },
  { label: 'EPSG:32723 (WGS 84 / UTM 23S)', value: 'EPSG:32723' },
  { label: 'EPSG:32724 (WGS 84 / UTM 24S)', value: 'EPSG:32724' },
]

// Reactive state for each tool
const veg = reactive({ ortomapaId: null, index: 'VARI', loading: false, result: null })
const terreno = reactive({ ortomapaId: null, tipo: 'slope', interval: 5, loading: false })
const classif = reactive({ ortomapaId: null, algorithm: 'KMeans', numClasses: 5, loading: false })
const hidro = reactive({ ortomapaId: null, tipo: 'watershed', threshold: 500, pourLat: null, pourLon: null, loading: false })
const mudanca = reactive({ antesId: null, depoisId: null, threshold: 0.3, loading: false })
const volume = reactive({ ortomapaId: null, refElevation: 0, loading: false, result: null })
const recorte = reactive({ ortomapaId: null, polygon: null, loading: false })
const exportar = reactive({ layerId: null, format: 'geotiff', crs: 'EPSG:4326', loading: false })

function addResultLayer(name, data) {
  const layerId = `analysis-${Date.now()}`
  mapStore.addLayer({
    id: layerId,
    name,
    type: 'analysis',
    geojson: data.geojson || null,
    sourceId: data.layer_id || null,
  })
  if (data.tile_url) {
    mapStore.addLayer({
      id: `${layerId}-tile`,
      name: `${name} (raster)`,
      type: 'ortomapa',
      sourceId: data.layer_id,
    })
  }
}

async function runVegetacao() {
  if (!veg.ortomapaId) return
  veg.loading = true
  try {
    const res = await runTool('vegetacao', {
      ortomapa_id: veg.ortomapaId,
      indice: veg.index,
    })
    veg.result = res.data.stats || res.data
    addResultLayer(`${veg.index}`, res.data)
    projectStore.fetchAnalises()
  } catch (e) {
    console.error(e)
  } finally {
    veg.loading = false
  }
}

async function runTerreno() {
  if (!terreno.ortomapaId) return
  terreno.loading = true
  try {
    const res = await runTool('terreno', {
      ortomapa_id: terreno.ortomapaId,
      tipo: terreno.tipo,
      intervalo: terreno.interval,
    })
    addResultLayer(terreno.tipo, res.data)
    projectStore.fetchAnalises()
  } catch (e) {
    console.error(e)
  } finally {
    terreno.loading = false
  }
}

async function runClassificacao() {
  if (!classif.ortomapaId) return
  classif.loading = true
  try {
    const res = await runTool('classificacao', {
      ortomapa_id: classif.ortomapaId,
      algoritmo: classif.algorithm,
      num_classes: classif.numClasses,
    })
    addResultLayer('Classificacao', res.data)
    projectStore.fetchAnalises()
  } catch (e) {
    console.error(e)
  } finally {
    classif.loading = false
  }
}

function startDrawTraining() {
  mapStore.setDrawMode('polygon')
}

function enablePourPointCapture() {
  // Set map to capture next click as pour point
  mapStore.setPourPointCallback((lat, lon) => {
    hidro.pourLat = lat
    hidro.pourLon = lon
  })
}

async function runHidrologia() {
  if (!hidro.ortomapaId) return
  hidro.loading = true
  try {
    const params = {
      ortomapa_id: hidro.ortomapaId,
      tipo: hidro.tipo,
      threshold: hidro.threshold,
    }
    if (hidro.tipo === 'watershed' && hidro.pourLat != null && hidro.pourLon != null) {
      params.pour_point = { lat: hidro.pourLat, lon: hidro.pourLon }
    }
    const res = await runTool('hidrologia', params)
    addResultLayer(hidro.tipo, res.data)
    projectStore.fetchAnalises()
  } catch (e) {
    console.error(e)
  } finally {
    hidro.loading = false
  }
}

async function runMudancas() {
  if (!mudanca.antesId || !mudanca.depoisId) return
  mudanca.loading = true
  try {
    const res = await runTool('mudancas', {
      antes_id: mudanca.antesId,
      depois_id: mudanca.depoisId,
      threshold: mudanca.threshold,
    })
    addResultLayer('Deteccao de Mudancas', res.data)
    projectStore.fetchAnalises()
  } catch (e) {
    console.error(e)
  } finally {
    mudanca.loading = false
  }
}

async function runVolume() {
  if (!volume.ortomapaId) return
  volume.loading = true
  try {
    const res = await runTool('volume', {
      ortomapa_id: volume.ortomapaId,
      ref_elevation: volume.refElevation,
    })
    volume.result = res.data
    projectStore.fetchAnalises()
  } catch (e) {
    console.error(e)
  } finally {
    volume.loading = false
  }
}

function startDrawClip() {
  mapStore.setDrawMode('polygon')
}

async function runRecorte() {
  if (!recorte.ortomapaId) return
  recorte.loading = true
  try {
    const res = await runTool('recorte', {
      ortomapa_id: recorte.ortomapaId,
      polygon: recorte.polygon,
    })
    addResultLayer('Recorte', res.data)
    projectStore.fetchAnalises()
  } catch (e) {
    console.error(e)
  } finally {
    recorte.loading = false
  }
}

async function runExport() {
  if (!exportar.layerId) return
  exportar.loading = true
  try {
    const res = await exportLayer({
      layer_id: exportar.layerId,
      format: exportar.format,
      crs: exportar.crs,
    })
    const url = window.URL.createObjectURL(res.data)
    const a = document.createElement('a')
    a.href = url
    a.download = `export_${Date.now()}.${exportar.format === 'geotiff' ? 'tif' : exportar.format}`
    a.click()
    window.URL.revokeObjectURL(url)
  } catch (e) {
    console.error(e)
  } finally {
    exportar.loading = false
  }
}
</script>

<style scoped>
.tools-panel {
  margin-bottom: 8px;
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
  padding: 4px;
  margin-bottom: 6px;
}

.tool-form {
  padding: 8px 4px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.form-group label {
  font-size: 0.8rem;
  font-weight: 500;
  color: var(--text-dim);
}

.w-full {
  width: 100%;
}

.mb-2 {
  margin-bottom: 8px;
}

.slider {
  width: 100%;
  accent-color: var(--accent);
}

.result-stats {
  background: rgba(74, 222, 128, 0.08);
  border: 1px solid rgba(74, 222, 128, 0.2);
  border-radius: 8px;
  padding: 10px;
  margin-top: 4px;
}

.result-stats h4 {
  font-size: 0.8rem;
  color: var(--accent);
  margin-bottom: 6px;
}

.stat-row {
  display: flex;
  justify-content: space-between;
  font-size: 0.78rem;
  padding: 2px 0;
  color: var(--text);
}

.stat-row span {
  color: var(--text-dim);
}
</style>
