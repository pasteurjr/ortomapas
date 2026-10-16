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
                :options="rgbOptions"
                optionLabel="label"
                optionValue="value"
                placeholder="Selecionar..."
                :disabled="veg.loading"
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
                :disabled="veg.loading"
                class="w-full"
              />
            </div>
            <div class="terrain-aoi">
              <label><input type="checkbox" v-model="useVegAoi" :disabled="veg.loading" /> Limitar a area</label>
              <div v-if="useVegAoi" class="aoi-actions">
                <button type="button" title="Desenhar area do indice" :disabled="veg.loading" @click="mapStore.setDrawMode(mapStore.drawMode === 'analysis-aoi' ? null : 'analysis-aoi')"><i class="pi pi-pencil"></i></button>
                <span>{{ mapStore.drawMode === 'analysis-aoi' ? 'Desenhando' : mapStore.analysisAoi ? 'Area selecionada' : 'Sem area' }}</span>
                <button type="button" title="Limpar area do indice" :disabled="veg.loading || !mapStore.analysisAoi" @click="mapStore.analysisAoi = null; mapStore.setDrawMode(null)"><i class="pi pi-trash"></i></button>
              </div>
            </div>
            <Button
              label="Calcular Indice"
              icon="pi pi-play"
              :loading="veg.loading"
              :disabled="!projectStore.canEdit || !veg.ortomapaId || (useVegAoi && (!mapStore.analysisAoi || mapStore.drawMode === 'analysis-aoi'))"
              @click="runVegetacao"
              class="w-full"
            />
            <div v-if="veg.error" class="terrain-error" role="alert">{{ veg.error }}</div>
            <div v-if="veg.result" class="result-stats">
              <h4>Resultado</h4>
              <div class="stat-row"><span>Min:</span> <strong>{{ veg.result.statistics.band_1.min.toFixed(3) }}</strong></div>
              <div class="stat-row"><span>Max:</span> <strong>{{ veg.result.statistics.band_1.max.toFixed(3) }}</strong></div>
              <div class="stat-row"><span>Media:</span> <strong>{{ veg.result.statistics.band_1.mean.toFixed(3) }}</strong></div>
              <div class="stat-row"><span>Pixels validos:</span> <strong>{{ veg.result.statistics.band_1.valid_pixels.toLocaleString('pt-BR') }}</strong></div>
              <small>Indice visivel RGB; nao utiliza banda NIR.</small>
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
                :disabled="terreno.loading"
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
                :disabled="terreno.loading"
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
            <div class="terrain-aoi">
              <label><input type="checkbox" v-model="useTerrainAoi" :disabled="terreno.loading" /> Limitar a area</label>
              <div v-if="useTerrainAoi" class="aoi-actions">
                <button type="button" title="Desenhar area de analise" :disabled="terreno.loading" @click="mapStore.setDrawMode(mapStore.drawMode === 'analysis-aoi' ? null : 'analysis-aoi')"><i class="pi pi-pencil"></i></button>
                <span>{{ mapStore.drawMode === 'analysis-aoi' ? 'Desenhando' : mapStore.analysisAoi ? 'Area selecionada' : 'Sem area' }}</span>
                <button type="button" title="Limpar area de analise" :disabled="terreno.loading || !mapStore.analysisAoi" @click="mapStore.analysisAoi = null"><i class="pi pi-trash"></i></button>
              </div>
            </div>
            <Button
              label="Gerar Analise"
              icon="pi pi-play"
              :loading="terreno.loading"
              :disabled="!projectStore.canEdit || !terreno.ortomapaId || (useTerrainAoi && (!mapStore.analysisAoi || mapStore.drawMode === 'analysis-aoi'))"
              @click="runTerreno"
              class="w-full"
            />
            <div v-if="terreno.error" class="terrain-error" role="alert">{{ terreno.error }}</div>
            <div v-if="terreno.result && terreno.tipo === 'contours'" class="result-stats terrain-result">
              <div class="stat-row"><span>Curvas:</span><strong>{{ terreno.result.statistics.feature_count }}</strong></div>
              <div class="stat-row"><span>Cotas (m):</span><strong>{{ terreno.result.statistics.min_elevation_m }} - {{ terreno.result.statistics.max_elevation_m }}</strong></div>
              <div class="stat-row"><span>Intervalo (m):</span><strong>{{ terreno.result.statistics.interval_m }}</strong></div>
            </div>
            <div v-if="terreno.result && terreno.tipo !== 'contours'" class="result-stats terrain-result">
              <div class="stat-row"><span>Min:</span><strong>{{ terreno.result.statistics?.band_1?.min?.toFixed(2) ?? 'Sem dados' }}</strong></div>
              <div class="stat-row"><span>Max:</span><strong>{{ terreno.result.statistics?.band_1?.max?.toFixed(2) ?? 'Sem dados' }}</strong></div>
              <div class="stat-row"><span>Media aritmetica:</span><strong>{{ terreno.result.statistics?.band_1?.mean?.toFixed(2) ?? 'Sem dados' }}</strong></div>
              <small>{{ terreno.tipo === 'hillshade' ? 'Intensidade 0-255' : 'Graus' }}. {{ terreno.result.analise ? 'Resultado salvo e publicado' : 'Raster gerado' }}.</small>
            </div>
          </div>
        </TabPanel>

        <!-- Classificacao -->
        <TabPanel value="classificacao">
          <div class="tool-form">
            <div class="form-group">
              <label>Ortomapa</label>
              <Select
                v-model="classif.ortomapaId"
                :options="rgbOptions"
                optionLabel="label"
                optionValue="value"
                placeholder="Selecionar..."
                :disabled="classif.loading"
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
                :disabled="classif.loading"
                class="w-full"
              />
            </div>
            <div class="form-group">
              <label>Numero de grupos espectrais</label>
              <InputText v-model.number="classif.numClasses" type="number" min="2" max="12" :disabled="classif.loading" class="w-full" />
            </div>
            <div class="terrain-aoi">
              <label><input type="checkbox" v-model="useClassAoi" :disabled="classif.loading" /> Limitar a area</label>
              <div v-if="useClassAoi" class="aoi-actions">
                <button type="button" title="Desenhar area da classificacao" :disabled="classif.loading" @click="mapStore.setDrawMode(mapStore.drawMode === 'analysis-aoi' ? null : 'analysis-aoi')"><i class="pi pi-pencil"></i></button>
                <span>{{ mapStore.drawMode === 'analysis-aoi' ? 'Desenhando' : mapStore.analysisAoi ? 'Area selecionada' : 'Sem area' }}</span>
                <button type="button" title="Limpar area da classificacao" :disabled="classif.loading || !mapStore.analysisAoi" @click="mapStore.analysisAoi = null; mapStore.setDrawMode(null)"><i class="pi pi-trash"></i></button>
              </div>
            </div>
            <Button
              label="Gerar Grupos"
              icon="pi pi-play"
              :loading="classif.loading"
              :disabled="!projectStore.canEdit || !classif.ortomapaId || classif.numClasses < 2 || classif.numClasses > 12 || (useClassAoi && (!mapStore.analysisAoi || mapStore.drawMode === 'analysis-aoi'))"
              @click="runClassificacao"
              class="w-full"
            />
            <div v-if="classif.error" class="terrain-error" role="alert">{{ classif.error }}</div>
            <div v-if="classif.result" class="result-stats class-result">
              <h4>Grupos espectrais</h4>
              <div v-for="cluster in classif.result.clusters" :key="cluster.cluster" class="cluster-row">
                <span class="cluster-color" :style="{ background: classif.result.analise.resultado.style.colors[cluster.cluster - 1] }"></span>
                <span>Grupo {{ cluster.cluster }}</span><strong>{{ cluster.percent.toFixed(2) }}%</strong>
              </div>
              <small>KMeans RGB sem rotulos semanticos.</small>
            </div>
          </div>
        </TabPanel>

        <!-- Hidrologia -->
        <TabPanel value="hidrologia">
          <div class="tool-form">
            <div class="form-group">
              <label>Modelo de terreno (DTM recomendado)</label>
              <Select
                v-model="hidro.ortomapaId"
                :options="dsmDtmOptions"
                optionLabel="label"
                optionValue="value"
                placeholder="Selecionar..."
                :disabled="hidro.loading"
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
                :disabled="hidro.loading"
                class="w-full"
              />
            </div>
            <div v-if="hidro.tipo === 'streams'" class="form-group">
              <label>Area contribuinte minima (m2)</label>
              <InputText v-model.number="hidro.minimumArea" type="number" min="0.01" step="1" :disabled="hidro.loading" class="w-full" />
            </div>
            <template v-if="hidro.tipo === 'watershed'">
              <div class="form-group">
                <label>Ponto de Exutorio (Latitude)</label>
                <InputText v-model.number="hidro.pourLat" type="number" step="0.000001" :disabled="hidro.loading" class="w-full" placeholder="Clique no mapa ou digite" />
              </div>
              <div class="form-group">
                <label>Ponto de Exutorio (Longitude)</label>
                <InputText v-model.number="hidro.pourLon" type="number" step="0.000001" :disabled="hidro.loading" class="w-full" placeholder="Clique no mapa ou digite" />
              </div>
              <div class="form-group">
                <label>Raio de ajuste ao canal (m)</label>
                <InputText v-model.number="hidro.snapRadius" type="number" min="0" max="1000" step="1" :disabled="hidro.loading" class="w-full" />
              </div>
              <Button
                label="Capturar do Mapa"
                icon="pi pi-map-marker"
                severity="secondary"
                size="small"
                :disabled="hidro.loading"
                @click="enablePourPointCapture"
                class="w-full mb-2"
              />
            </template>
            <Button
              label="Executar"
              icon="pi pi-play"
              :loading="hidro.loading"
              :disabled="!projectStore.canEdit || !hidro.ortomapaId || (hidro.tipo === 'streams' && !(hidro.minimumArea > 0)) || (hidro.tipo === 'watershed' && (hidro.pourLat == null || hidro.pourLon == null))"
              @click="runHidrologia"
              class="w-full"
            />
            <div v-if="hidro.error" class="terrain-error" role="alert">{{ hidro.error }}</div>
            <div v-if="hidro.result && hidro.tipo === 'watershed'" class="result-stats">
              <div class="stat-row"><span>Area contribuinte:</span><strong>{{ hidro.result.area_m2.toLocaleString('pt-BR', { maximumFractionDigits: 1 }) }} m2</strong></div>
              <div class="stat-row"><span>Celulas:</span><strong>{{ hidro.result.watershed_cells.toLocaleString('pt-BR') }}</strong></div>
              <div class="stat-row"><span>Ajuste do exutorio:</span><strong>{{ hidro.result.snapped_outlet.distance_m.toFixed(2) }} m</strong></div>
            </div>
            <div v-if="hidro.result && hidro.tipo === 'streams'" class="result-stats">
              <div class="stat-row"><span>Segmentos:</span><strong>{{ hidro.result.feature_count }}</strong></div>
              <div class="stat-row"><span>Comprimento:</span><strong>{{ hidro.result.total_length_m.toFixed(1) }} m</strong></div>
              <div class="stat-row"><span>Limiar:</span><strong>{{ hidro.result.minimum_area_m2.toFixed(1) }} m2</strong></div>
            </div>
            <div v-if="hidro.result && hidro.tipo === 'twi'" class="result-stats">
              <div class="stat-row"><span>Min:</span><strong>{{ hidro.result.statistics.band_1.min.toFixed(2) }}</strong></div>
              <div class="stat-row"><span>Max:</span><strong>{{ hidro.result.statistics.band_1.max.toFixed(2) }}</strong></div>
              <div class="stat-row"><span>Media:</span><strong>{{ hidro.result.statistics.band_1.mean.toFixed(2) }}</strong></div>
            </div>
            <small v-if="hidro.ortomapaId && selectedHydrologySource?.tipo?.toLowerCase() === 'dsm'">DSM inclui vegetacao e edificacoes; use DTM para inferencia hidrologica do terreno.</small>
          </div>
        </TabPanel>

        <!-- Mudancas -->
        <TabPanel value="mudancas">
          <div class="tool-form">
            <div class="form-group">
              <label>Modelo anterior</label>
              <Select
                v-model="mudanca.antesId"
                :options="dsmDtmOptions"
                optionLabel="label"
                optionValue="value"
                placeholder="DSM/DTM de referencia..."
                :disabled="mudanca.loading"
                class="w-full"
              />
            </div>
            <div class="form-group">
              <label>Modelo posterior</label>
              <Select
                v-model="mudanca.depoisId"
                :options="dsmDtmOptions"
                optionLabel="label"
                optionValue="value"
                placeholder="DSM/DTM posterior..."
                :disabled="mudanca.loading"
                class="w-full"
              />
            </div>
            <div class="form-group">
              <label>Limiar estavel: +/- {{ mudanca.threshold.toFixed(2) }} m</label>
              <input
                type="range"
                v-model.number="mudanca.threshold"
                min="0"
                max="5"
                step="0.01"
                :disabled="mudanca.loading"
                class="slider"
              />
            </div>
            <div class="terrain-aoi">
              <label><input type="checkbox" v-model="useChangeAoi" :disabled="mudanca.loading" /> Limitar a area</label>
              <div v-if="useChangeAoi" class="aoi-actions">
                <button type="button" title="Desenhar area de comparacao" :disabled="mudanca.loading" @click="mapStore.setDrawMode(mapStore.drawMode === 'analysis-aoi' ? null : 'analysis-aoi')"><i class="pi pi-pencil"></i></button>
                <span>{{ mapStore.drawMode === 'analysis-aoi' ? 'Desenhando' : mapStore.analysisAoi ? 'Area selecionada' : 'Sem area' }}</span>
                <button type="button" title="Limpar area de comparacao" :disabled="mudanca.loading || !mapStore.analysisAoi" @click="mapStore.analysisAoi = null; mapStore.setDrawMode(null)"><i class="pi pi-trash"></i></button>
              </div>
            </div>
            <Button
              label="Comparar Elevacoes"
              icon="pi pi-play"
              :loading="mudanca.loading"
              :disabled="!projectStore.canEdit || !mudanca.antesId || !mudanca.depoisId || mudanca.antesId === mudanca.depoisId || (useChangeAoi && (!mapStore.analysisAoi || mapStore.drawMode === 'analysis-aoi'))"
              @click="runMudancas"
              class="w-full"
            />
            <div v-if="mudanca.error" class="terrain-error" role="alert">{{ mudanca.error }}</div>
            <div v-if="mudanca.result" class="result-stats volume-result change-result">
              <h4>Depois - antes</h4>
              <div class="stat-row"><span>Remocao (m3):</span><strong>{{ mudanca.result.cut_volume_m3.toFixed(2) }}</strong></div>
              <div class="stat-row"><span>Deposicao (m3):</span><strong>{{ mudanca.result.fill_volume_m3.toFixed(2) }}</strong></div>
              <div class="stat-row"><span>Saldo deposicao - remocao:</span><strong>{{ mudanca.result.net_volume_m3.toFixed(2) }} m3</strong></div>
              <div class="stat-row"><span>Area alterada:</span><strong>{{ (mudanca.result.cut_area_m2 + mudanca.result.fill_area_m2).toFixed(2) }} m2</strong></div>
              <div class="stat-row"><span>Pixels alterados:</span><strong>{{ mudanca.result.changed_percent.toFixed(2) }}%</strong></div>
            </div>
          </div>
        </TabPanel>

        <!-- Volume -->
        <TabPanel value="volume">
          <div class="tool-form">
            <div class="form-group">
              <label>Modelo (DSM/DTM)</label>
              <Select
                v-model="volume.ortomapaId"
                :disabled="volume.loading"
                :options="dsmDtmOptions"
                optionLabel="label"
                optionValue="value"
                placeholder="Selecionar..."
                class="w-full"
              />
            </div>
            <div class="form-group">
              <label>Elevacao de Referencia (m)</label>
              <InputText v-model.number="volume.refElevation" type="number" :disabled="volume.loading" class="w-full" />
            </div>
            <div class="terrain-aoi">
              <label><input type="checkbox" v-model="useVolumeAoi" :disabled="volume.loading" /> Limitar a area</label>
              <div v-if="useVolumeAoi" class="aoi-actions">
                <button type="button" title="Desenhar area de volume" :disabled="volume.loading" @click="mapStore.setDrawMode(mapStore.drawMode === 'analysis-aoi' ? null : 'analysis-aoi')"><i class="pi pi-pencil"></i></button>
                <span>{{ mapStore.analysisAoi ? 'Area selecionada' : 'Nenhuma area selecionada' }}</span>
                <button type="button" title="Limpar area de volume" :disabled="volume.loading" @click="mapStore.analysisAoi = null; mapStore.setDrawMode(null)"><i class="pi pi-trash"></i></button>
              </div>
            </div>
            <Button
              label="Calcular Volume"
              icon="pi pi-play"
              :loading="volume.loading"
              :disabled="!projectStore.canEdit || !volume.ortomapaId || !Number.isFinite(volume.refElevation) || (useVolumeAoi && (!mapStore.analysisAoi || mapStore.drawMode === 'analysis-aoi'))"
              @click="runVolume"
              class="w-full"
            />
            <div v-if="volume.error" class="terrain-error" role="alert">{{ volume.error }}</div>
            <div v-if="volume.result" class="result-stats volume-result">
              <h4>Resultado</h4>
              <div class="stat-row"><span>Corte (m3):</span> <strong>{{ volume.result.volume_above_m3.toFixed(2) }}</strong></div>
              <div class="stat-row"><span>Aterro (m3):</span> <strong>{{ volume.result.volume_below_m3.toFixed(2) }}</strong></div>
              <div class="stat-row"><span>Saldo corte - aterro:</span> <strong>{{ volume.result.net_volume_m3.toFixed(2) }} m3</strong></div>
              <div class="stat-row"><span>Area valida (m2):</span> <strong>{{ volume.result.valid_area_m2.toFixed(2) }}</strong></div>
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
            <div class="aoi-actions">
              <span>{{ mapStore.analysisAoi ? 'Area selecionada' : 'Nenhuma area selecionada' }}</span>
              <button type="button" title="Limpar area" :disabled="!mapStore.analysisAoi" @click="mapStore.analysisAoi = null"><i class="pi pi-trash"></i></button>
            </div>
            <Button v-if="mapStore.drawMode === 'analysis-aoi'" label="Concluir poligono" icon="pi pi-check" severity="secondary" class="w-full mb-2" @click="mapStore.finishAnalysisAoi?.()" />
            <Button
              label="Recortar"
              icon="pi pi-play"
              :loading="recorte.loading"
              :disabled="!projectStore.canEdit || !recorte.ortomapaId || !mapStore.analysisAoi || mapStore.drawMode === 'analysis-aoi'"
              @click="runRecorte"
              class="w-full"
            />
            <div v-if="recorte.error" class="error-message">{{ recorte.error }}</div>
            <div v-if="recorte.result" class="result-panel">
              <h4>Recorte criado</h4>
              <div class="stat-row"><span>Pixels validos:</span><strong>{{ recorte.result.statistics.valid_pixels }}</strong></div>
              <div class="stat-row"><span>Dimensoes:</span><strong>{{ recorte.result.statistics.width }} x {{ recorte.result.statistics.height }}</strong></div>
            </div>
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
                :options="availableExportFormats"
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
                :disabled="['geojson', 'kml'].includes(exportar.format)"
                class="w-full"
              />
            </div>
            <Button
              label="Exportar"
              icon="pi pi-download"
              :loading="exportar.loading"
              :disabled="!exportar.layerId"
              @click="runExport"
              class="w-full"
            />
            <div v-if="exportar.error" class="error-message">{{ exportar.error }}</div>
            <small v-if="['png', 'jpeg'].includes(exportar.format)">PNG/JPEG sao imagens sem georreferenciamento. Para GIS, use GeoTIFF.</small>
          </div>
        </TabPanel>
      </TabPanels>
    </Tabs>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { useProjectStore } from '../stores/projectStore'
import { useMapStore } from '../stores/mapStore'
import { analysisRasterLayer, analysisVectorLayer } from '../utils/analysisProducts'
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
const useTerrainAoi = ref(false)
watch(() => projectStore.activeProject?.id, () => { useTerrainAoi.value = false; terreno.result = null })
const activeTab = ref('vegetacao')

const ortoOptions = computed(() =>
  projectStore.ortomapas.map((o) => ({ label: o.nome, value: o.id }))
)

const rgbOptions = computed(() =>
  projectStore.ortomapas
    .filter((o) => ['ortomosaico', 'rgb', 'multispectral'].includes(String(o.tipo).toLowerCase()))
    .map((o) => ({ label: `${o.nome} (${o.tipo})`, value: o.id }))
)

const dsmDtmOptions = computed(() =>
  projectStore.ortomapas
    .filter((o) => ['dsm', 'dtm', 'DSM', 'DTM'].includes(o.tipo))
    .map((o) => ({ label: `${o.nome} (${o.tipo})`, value: o.id }))
)

const allLayerOptions = computed(() => [
  ...projectStore.ortomapas.map((o) => ({ label: o.nome, value: `ortomapa-${o.id}`, path: o.caminho_arquivo })),
  ...projectStore.analises.filter((a) => a.resultado_path).map((a) => ({
    label: a.nome, value: `analise-${a.id}`, path: a.resultado_path,
  })),
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
  { label: 'K-Means RGB (Nao Supervisionado)', value: 'kmeans' },
]

const hidroTypes = [
  { label: 'Bacias Hidrograficas (Watershed)', value: 'watershed' },
  { label: 'Rede de Drenagem (Streams)', value: 'streams' },
  { label: 'TWI - Indice Topografico', value: 'twi' },
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
const useVegAoi = ref(false)
const veg = reactive({ ortomapaId: null, index: 'VARI', loading: false, result: null, error: '' })
watch(() => [veg.ortomapaId, veg.index, useVegAoi.value, JSON.stringify(mapStore.analysisAoi)], () => { veg.result = null; veg.error = '' })
const terreno = reactive({ ortomapaId: null, tipo: 'slope', interval: 5, loading: false, result: null, error: '' })
watch(() => [terreno.tipo, terreno.ortomapaId, terreno.interval, useTerrainAoi.value, JSON.stringify(mapStore.analysisAoi)], () => { terreno.result = null; terreno.error = '' })
const useClassAoi = ref(false)
const classif = reactive({ ortomapaId: null, algorithm: 'kmeans', numClasses: 5, loading: false, result: null, error: '' })
watch(() => [classif.ortomapaId, classif.algorithm, classif.numClasses, useClassAoi.value, JSON.stringify(mapStore.analysisAoi)], () => { classif.result = null; classif.error = '' })
const hidro = reactive({ ortomapaId: null, tipo: 'watershed', minimumArea: 50, snapRadius: 5, pourLat: null, pourLon: null, loading: false, result: null, error: '' })
const selectedHydrologySource = computed(() => projectStore.ortomapas.find(item => item.id === hidro.ortomapaId))
watch(() => [hidro.ortomapaId, hidro.tipo, hidro.minimumArea, hidro.snapRadius, hidro.pourLat, hidro.pourLon], () => { hidro.result = null; hidro.error = '' })
const useChangeAoi = ref(false)
const mudanca = reactive({ antesId: null, depoisId: null, threshold: 0.1, loading: false, result: null, error: '' })
watch(() => [mudanca.antesId, mudanca.depoisId, mudanca.threshold, useChangeAoi.value, JSON.stringify(mapStore.analysisAoi)], () => { mudanca.result = null; mudanca.error = '' })
const useVolumeAoi = ref(false)
const volume = reactive({ ortomapaId: null, refElevation: null, loading: false, result: null, error: '' })
watch(() => [volume.ortomapaId, volume.refElevation, useVolumeAoi.value, JSON.stringify(mapStore.analysisAoi)], () => { volume.result = null; volume.error = '' })
watch(() => projectStore.activeProject?.id, () => {
  useVolumeAoi.value = false; volume.result = null; volume.error = ''
  useChangeAoi.value = false; mudanca.result = null; mudanca.error = ''
  useVegAoi.value = false; veg.result = null; veg.error = ''
  useClassAoi.value = false; classif.result = null; classif.error = ''
  hidro.result = null; hidro.error = ''; hidro.pourLat = null; hidro.pourLon = null; mapStore.hydrologyOutlet = null
})
const recorte = reactive({ ortomapaId: null, loading: false, result: null, error: '' })
const exportar = reactive({ layerId: null, format: 'geotiff', crs: 'EPSG:4326', loading: false, error: '' })
const selectedExportSource = computed(() => allLayerOptions.value.find((item) => item.value === exportar.layerId))
const exportIsVector = computed(() => /\.(geojson|json|gpkg|shp|kml)$/i.test(selectedExportSource.value?.path || ''))
const availableExportFormats = computed(() => exportFormats.filter((item) =>
  exportIsVector.value ? ['geojson', 'kml', 'shapefile'].includes(item.value) : ['geotiff', 'png', 'jpeg'].includes(item.value)))
watch(exportIsVector, () => { exportar.format = exportIsVector.value ? 'geojson' : 'geotiff' })
watch(() => exportar.format, (format) => { if (['geojson', 'kml'].includes(format)) exportar.crs = 'EPSG:4326' })
watch(() => projectStore.activeProject?.id, () => {
  recorte.result = null; recorte.error = ''; recorte.ortomapaId = null
  exportar.layerId = null; exportar.error = ''
})

function ortoPath(id) {
  return projectStore.ortomapas.find((item) => item.id === id)?.caminho_arquivo || ''
}

watch(() => projectStore.ortomapas, (items) => {
  if (!items?.length) {
    veg.ortomapaId = null
    classif.ortomapaId = null
    terreno.ortomapaId = null
    return
  }
  const rgb = items.find((item) => ['ortomosaico', 'rgb', 'multispectral'].includes(item.tipo?.toLowerCase()))
  const elevation = items.find((item) => ['dsm', 'dtm', 'DSM', 'DTM'].includes(item.tipo))
  if (!items.some(item => item.id === veg.ortomapaId && ['ortomosaico', 'rgb', 'multispectral'].includes(item.tipo?.toLowerCase()))) veg.ortomapaId = rgb?.id || null
  if (!items.some(item => item.id === classif.ortomapaId && ['ortomosaico', 'rgb', 'multispectral'].includes(item.tipo?.toLowerCase()))) classif.ortomapaId = rgb?.id || null
  if (!items.some(item => item.id === mudanca.antesId)) mudanca.antesId = elevation?.id || null
  if (!items.some(item => item.id === mudanca.depoisId)) {
    const before = items.find(item => item.id === mudanca.antesId)
    mudanca.depoisId = items.find(item => item.id !== mudanca.antesId && item.tipo?.toLowerCase() === before?.tipo?.toLowerCase())?.id || null
  }
  if (!items.some(item => item.id === terreno.ortomapaId)) terreno.ortomapaId = elevation?.id || null
  if (!items.some(item => item.id === hidro.ortomapaId && ['dsm', 'dtm'].includes(item.tipo?.toLowerCase()))) {
    hidro.ortomapaId = items.find(item => item.tipo?.toLowerCase() === 'dtm')?.id || elevation?.id || null
  }
  if (!volume.ortomapaId && elevation) volume.ortomapaId = elevation.id
  if (!recorte.ortomapaId && rgb) recorte.ortomapaId = rgb.id
}, { immediate: true })

function addResultLayer(name, data) {
  if (data.analise) {
    const layer = analysisVectorLayer(data.analise) || analysisRasterLayer(data.analise)
    if (layer) mapStore.addLayer(layer)
    return
  }
  if (!data.geojson && !data.tile_url) return
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
  veg.result = null
  veg.error = ''
  try {
    const res = await runTool('vegetation', {
      input_path: ortoPath(veg.ortomapaId),
      ortomapa_id: veg.ortomapaId,
      projeto_id: projectStore.activeProject.id,
      aoi: useVegAoi.value ? mapStore.analysisAoi : null,
      output_name: `vegetacao_${veg.index.toLowerCase()}_${Date.now()}`,
      index_name: veg.index,
    })
    veg.result = res.data
    addResultLayer(`${veg.index}`, res.data)
    await projectStore.fetchAnalises()
  } catch (e) {
    veg.error = e.response?.data?.detail || 'Nao foi possivel calcular o indice RGB'
  } finally {
    veg.loading = false
  }
}

async function runTerreno() {
  if (!terreno.ortomapaId) return
  const projectId = projectStore.activeProject?.id
  terreno.loading = true
  terreno.result = null
  terreno.error = ''
  try {
    const terrainEndpoint = { slope: 'slope', aspect: 'aspect', contours: 'contours', hillshade: 'hillshade' }[terreno.tipo] || 'slope'
    const res = await runTool(terrainEndpoint, {
      input_path: ortoPath(terreno.ortomapaId),
      ortomapa_id: terreno.ortomapaId,
      projeto_id: projectId,
      aoi: useTerrainAoi.value ? mapStore.analysisAoi : null,
      output_name: `terreno_${terreno.tipo}_${Date.now()}`,
      interval: terreno.interval,
    })
    if (projectStore.activeProject?.id !== projectId) return
    terreno.result = res.data
    addResultLayer(terreno.tipo, res.data)
    projectStore.fetchAnalises()
  } catch (e) {
    if (projectStore.activeProject?.id === projectId) terreno.error = e.response?.data?.detail || 'Falha ao calcular terreno'
  } finally {
    terreno.loading = false
  }
}

async function runClassificacao() {
  if (!classif.ortomapaId) return
  classif.loading = true
  classif.result = null
  classif.error = ''
  try {
    const res = await runTool('classify', {
      ortomapa_path: ortoPath(classif.ortomapaId),
      ortomapa_id: classif.ortomapaId,
      projeto_id: projectStore.activeProject.id,
      algorithm: classif.algorithm,
      n_clusters: classif.numClasses,
      aoi: useClassAoi.value ? mapStore.analysisAoi : null,
      output_name: `classificacao_kmeans_${Date.now()}`,
    })
    classif.result = res.data
    addResultLayer('Grupos espectrais KMeans', res.data)
    await projectStore.fetchAnalises()
  } catch (e) {
    classif.error = e.response?.data?.detail || 'Nao foi possivel gerar os grupos espectrais'
  } finally {
    classif.loading = false
  }
}

function enablePourPointCapture() {
  mapStore.setPourPointCallback((lat, lon) => {
    hidro.pourLat = lat
    hidro.pourLon = lon
  })
}

async function runHidrologia() {
  if (!hidro.ortomapaId) return
  hidro.loading = true
  hidro.result = null
  hidro.error = ''
  try {
    const common = {
      dtm_path: ortoPath(hidro.ortomapaId), ortomapa_id: hidro.ortomapaId,
      projeto_id: projectStore.activeProject.id, output_name: `hidrologia_${hidro.tipo}_${Date.now()}`,
    }
    const params = hidro.tipo === 'watershed'
      ? { ...common, pour_point: { lat: hidro.pourLat, lon: hidro.pourLon }, snap_radius_m: hidro.snapRadius }
      : hidro.tipo === 'streams'
        ? { ...common, minimum_area_m2: hidro.minimumArea }
        : common
    const endpoint = { watershed: 'hydrology/watershed', streams: 'hydrology/streams', twi: 'hydrology/twi' }[hidro.tipo]
    const res = await runTool(endpoint, params)
    hidro.result = res.data
    addResultLayer(hidro.tipo, res.data)
    await projectStore.fetchAnalises()
  } catch (e) {
    hidro.error = e.response?.data?.detail || 'Nao foi possivel executar a analise hidrologica'
  } finally {
    hidro.loading = false
  }
}

async function runMudancas() {
  if (!mudanca.antesId || !mudanca.depoisId) return
  mudanca.loading = true
  mudanca.result = null
  mudanca.error = ''
  try {
    const res = await runTool('volume/difference', {
      ortomapa_antes_id: mudanca.antesId,
      ortomapa_depois_id: mudanca.depoisId,
      projeto_id: projectStore.activeProject.id,
      dsm1_path: ortoPath(mudanca.antesId),
      dsm2_path: ortoPath(mudanca.depoisId),
      threshold: mudanca.threshold,
      aoi: useChangeAoi.value ? mapStore.analysisAoi : null,
      output_name: `mudanca_elevacao_${Date.now()}`,
    })
    mudanca.result = res.data
    addResultLayer('Mudanca de elevacao', res.data)
    await projectStore.fetchAnalises()
  } catch (e) {
    mudanca.error = e.response?.data?.detail || 'Nao foi possivel comparar os modelos'
  } finally {
    mudanca.loading = false
  }
}

async function runVolume() {
  if (!volume.ortomapaId) return
  volume.loading = true
  volume.error = ''
  volume.result = null
  try {
    const res = await runTool('volume', {
      ortomapa_id: volume.ortomapaId,
      projeto_id: projectStore.activeProject.id,
      dsm_path: ortoPath(volume.ortomapaId),
      reference_elevation: volume.refElevation,
      aoi: useVolumeAoi.value ? mapStore.analysisAoi : null,
      output_name: `volume_${Date.now()}`,
    })
    volume.result = res.data
    addResultLayer('Corte/aterro por cota', res.data)
    await projectStore.fetchAnalises()
  } catch (e) {
    volume.error = e.response?.data?.detail || 'Nao foi possivel calcular o volume'
  } finally {
    volume.loading = false
  }
}

function startDrawClip() {
  mapStore.setDrawMode('analysis-aoi')
}

async function runRecorte() {
  if (!recorte.ortomapaId) return
  recorte.loading = true
  recorte.error = ''
  recorte.result = null
  try {
    const res = await runTool('recorte', {
      ortomapa_id: recorte.ortomapaId,
      projeto_id: projectStore.activeProject.id,
      input_path: ortoPath(recorte.ortomapaId),
      aoi: mapStore.analysisAoi,
      output_name: `recorte_${Date.now()}`,
    })
    addResultLayer('Recorte', res.data)
    recorte.result = res.data
    await projectStore.fetchAnalises()
  } catch (e) {
    recorte.error = e.response?.data?.detail || 'Falha ao recortar o raster'
  } finally {
    recorte.loading = false
  }
}

async function runExport() {
  if (!selectedExportSource.value) return
  exportar.loading = true
  exportar.error = ''
  try {
    const res = await exportLayer({
      input_path: selectedExportSource.value.path,
      format: exportar.format,
      crs: exportar.crs,
    })
    const url = window.URL.createObjectURL(res.data)
    const a = document.createElement('a')
    a.href = url
    const extension = { geotiff: 'tif', jpeg: 'jpg', shapefile: 'zip' }[exportar.format] || exportar.format
    a.download = `export_${Date.now()}.${extension}`
    document.body.appendChild(a)
    a.click()
    a.remove()
    setTimeout(() => window.URL.revokeObjectURL(url), 1000)
  } catch (e) {
    if (e.response?.data instanceof Blob) {
      const body = await e.response.data.text()
      try { exportar.error = JSON.parse(body).detail || body } catch { exportar.error = body }
    } else exportar.error = e.response?.data?.detail || 'Falha na exportacao'
  } finally {
    exportar.loading = false
  }
}
</script>

<style scoped>
.tools-panel {
  margin-bottom: 8px;
}
.terrain-aoi label { display: flex; align-items: center; gap: 8px; font-size: .8rem; }
.aoi-actions { display: flex; align-items: center; gap: 8px; margin-top: 6px; font-size: .78rem; }
.aoi-actions button { width: 30px; height: 30px; border: 1px solid #aab6b2; background: white; cursor: pointer; }

.section-title {
  contain: paint;
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

.terrain-error {
  color: #b42318;
  overflow-wrap: anywhere;
  font-size: 0.8rem;
}

.terrain-result strong, .volume-result strong {
  color: #173b29;
}

.class-result h4 { margin: 0 0 6px; font-size: .82rem; }
.cluster-row { display: grid; grid-template-columns: 14px 1fr auto; align-items: center; gap: 7px; padding: 3px 0; font-size: .78rem; }
.cluster-color { width: 12px; height: 12px; border: 1px solid rgba(0, 0, 0, .22); }
.class-result small { display: block; margin-top: 6px; }

.volume-result .stat-row { flex-wrap: wrap; gap: 4px; }

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
  color: #173b29;
}

.stat-row span {
  color: #52645c;
}
</style>
