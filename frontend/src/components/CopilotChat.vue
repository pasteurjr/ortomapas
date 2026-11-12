<template>
  <section class="copilot">
    <div class="title"><i class="pi pi-sparkles"></i> Copiloto geoespacial</div>
    <div class="threads">
      <select v-model="threadId" aria-label="Conversas do projeto" :disabled="loading || !threadReady || !threads.length" @change="openThread">
        <option v-if="!threads.length" :value="null">Nenhuma conversa</option>
        <option v-for="thread in threads" :key="thread.id" :value="thread.id">{{thread.titulo || 'Conversa sem título'}}</option>
      </select>
      <button type="button" title="Nova conversa" aria-label="Nova conversa" :disabled="loading || !threadReady || !projectStore.activeProject" @click="newThread()"><i class="pi pi-plus"></i></button>
      <button type="button" title="Resumir conversa" aria-label="Resumir conversa" :disabled="loading || !threadReady || summaryLoading || !threadId || !messages.length" @click="summarizeThread"><i :class="summaryLoading ? 'pi pi-spin pi-spinner' : 'pi pi-file-edit'"></i></button>
    </div>
    <label v-if="projectStore.activeProject" class="analysis-surface">
      <span>Superfície para medidas do relevo</span>
      <select v-model="analysisProductId" aria-label="DSM ou DTM para análise" :disabled="analysisProductsLoading">
        <option value="">{{ analysisProducts.length > 1 ? 'Selecione um DSM/DTM' : 'Selecione DSM/DTM (opcional)' }}</option>
        <option v-for="product in analysisProducts" :key="product.id" :value="String(product.id)">{{ product.tipo.toUpperCase() }} · proc. #{{ product.processamento_id }} · produto #{{ product.id }}</option>
      </select>
      <small v-if="analysisProducts.length > 1 && !analysisProductId">Escolha o processamento antes de pedir declividade, aspecto, perfil ou volume.</small>
      <small v-else-if="analysisProductId">A medida do relevo usará somente a superfície selecionada.</small>
      <small v-else-if="!analysisProductsLoading && !analysisProducts.length">Este projeto não tem DSM/DTM concluído disponível.</small>
    </label>
    <details v-if="threadSummary" class="summary-panel"><summary>Resumo salvo desta conversa</summary><p>{{ threadSummary }}</p><small v-if="summaryUsage">{{ summaryUsageText(summaryUsage) }}</small></details>
    <p v-if="summaryError" class="memory-error" role="alert">{{ summaryError }}</p>
    <details class="memory-panel" @toggle="loadMemories">
      <summary>Memórias pessoais ({{ memories.length }})</summary>
      <p class="memory-note">Anotações suas, usadas como contexto nas conversas deste projeto. Não são dados medidos do mapa.</p>
      <form class="memory-form" @submit.prevent="saveMemory">
        <input v-model="memoryKey" aria-label="Chave da memória" placeholder="ex.: unidades_area" maxlength="80" :disabled="memorySaving">
        <textarea v-model="memoryValue" aria-label="Conteúdo da memória" placeholder="ex.: prefiro resultados em hectares" rows="2" maxlength="4096" :disabled="memorySaving"></textarea>
        <button type="submit" title="Salvar memória" aria-label="Salvar memória" :disabled="memorySaving || !memoryKey.trim() || !memoryValue.trim()"><i class="pi pi-save"></i></button>
      </form>
      <p v-if="memoryError" class="memory-error">{{ memoryError }}</p>
      <div v-for="memory in memories" :key="memory.id" class="memory-item">
        <span><b>{{ memory.chave }}</b><small>{{ memoryText(memory.valor) }}</small></span>
        <button type="button" title="Excluir memória" :aria-label="`Excluir memória ${memory.chave}`" @click="removeMemory(memory.id)"><i class="pi pi-trash"></i></button>
      </div>
    </details>
    <div v-if="mapStore.selectedGeometry" class="selection">
      <i class="pi pi-map-marker"></i><span>Geometria selecionada</span>
      <button type="button" title="Medir area e perimetro" @click="quick('Calcule a area e o perimetro da geometria desenhada no mapa.')"><i class="pi pi-ruler"></i></button>
      <button type="button" title="Analisar declividade" @click="quick('Calcule a declividade media e maxima dentro da geometria desenhada no mapa.')"><i class="pi pi-chart-line"></i></button>
      <button type="button" title="Calcular volume" @click="quick('Calcule o volume do relevo dentro da geometria desenhada no mapa usando a cota media.')"><i class="pi pi-chart-bar"></i></button>
    </div>
    <div class="messages">
      <div v-if="!threadReady" class="empty" role="status">Preparando a conversa do projeto...</div>
      <div v-else-if="!messages.length" class="empty">Pergunte sobre produtos, qualidade, relevo ou análises do projeto.</div>
      <div v-for="(m,i) in messages" :key="i" class="message" :class="m.role">
        <b>{{m.role==='user'?'Você':'Copiloto'}}</b><div class="message-content" v-html="formatAnswer(m.text)"></div><small v-if="m.tools?.length">Ferramentas: {{m.tools.join(', ')}}</small>
        <details v-if="m.evidence?.length" class="evidence"><summary>Ver resultados e origem dos cálculos</summary><div v-for="(item,j) in m.evidence" :key="j" class="evidence-item"><b>{{item.tool}}</b><pre>{{formatEvidence(item)}}</pre><div v-if="spatialGeometry(item)" class="layer-action"><span v-if="isLayerSaved(item)" role="status">Camada salva no projeto</span><span v-else-if="item.saveError" class="layer-error" role="alert">{{ item.saveError }}</span><button v-if="!isLayerSaved(item)" type="button" :disabled="item.savingLayer" @click="saveSpatialResult(item)"><i :class="item.savingLayer ? 'pi pi-spin pi-spinner' : 'pi pi-save'"></i>{{ item.savingLayer ? 'Salvando...' : 'Salvar camada no projeto' }}</button></div></div></details>
      </div>
    </div>
    <form @submit.prevent="send"><textarea v-model="prompt" rows="2" placeholder="Ex.: compare DSM e DTM deste projeto..." :disabled="loading || !threadReady"></textarea><button :disabled="loading || !threadReady || !threadId || !prompt.trim()" title="Enviar" aria-label="Enviar"><i :class="loading?'pi pi-spin pi-spinner':'pi pi-send'"></i></button></form>
  </section>
</template>
<script setup>
import { ref, watch } from 'vue'
import { askCopilot, createCopilotThread, getCopilotThread, listCopilotThreads, addCopilotMessage, summarizeCopilotThread, getCopilotLayers, saveCopilotLayer, listCopilotMemories, saveCopilotMemory, deleteCopilotMemory, getOdmProducts } from '../api/client'
import { useProjectStore } from '../stores/projectStore'
import { useMapStore } from '../stores/mapStore'

const projectStore = useProjectStore()
const mapStore = useMapStore()
const prompt = ref('')
const loading = ref(false)
const threadReady = ref(false)
const messages = ref([])
const threadId = ref(null)
const threadSummary = ref('')
const summaryUsage = ref(null)
const summaryLoading = ref(false)
const summaryError = ref('')
const threads = ref([])
const memories = ref([])
const savedLayers = ref([])
const memoryKey = ref('')
const memoryValue = ref('')
const memorySaving = ref(false)
const memoryError = ref('')
const analysisProducts = ref([])
const analysisProductId = ref('')
const analysisProductsLoading = ref(false)
let analysisProductsRequest = 0
let threadLoadRequest = 0

async function loadThread() {
  const request = ++threadLoadRequest
  const project = projectStore.activeProject
  threadReady.value = false
  if (!project) { threads.value = []; threadId.value = null; messages.value = []; memories.value = []; threadSummary.value = ''; summaryUsage.value = null; threadReady.value = true; return }
  const key = `ortomapas.thread.${project.id}`
  try {
    const { data } = await listCopilotThreads(project.id)
    if (request !== threadLoadRequest) return
    threads.value = data.conversas || []
  } catch {
    if (request !== threadLoadRequest) return
    threads.value = []
  }
  const savedId = Number(localStorage.getItem(key))
  const selected = threads.value.find(thread => Number(thread.id) === savedId) || threads.value[0]
  try {
    if (selected) await selectThread(selected.id, request)
    else await newThread(request)
    if (request !== threadLoadRequest) return
  } finally {
    if (request === threadLoadRequest) threadReady.value = true
  }
  try {
    const saved = await getCopilotLayers(project.id)
    if (request !== threadLoadRequest) return
    savedLayers.value = saved.data.camadas || []
    savedLayers.value.forEach(layer => mapStore.addLayer({ id: `saved-${layer.id}`, name: layer.nome, type: 'analysis', geojson: layer.geojson }))
  } catch {}
  if (request === threadLoadRequest) await loadMemories()
}

async function loadMemories(event) {
  if (event && !event.target.open) return
  const projectId = projectStore.activeProject?.id
  if (!projectId) return
  try {
    const { data } = await listCopilotMemories(projectId)
    memories.value = data.memorias || []
    memoryError.value = ''
  } catch (error) {
    memoryError.value = error.response?.data?.detail || 'Falha ao carregar memórias.'
  }
}

async function saveMemory() {
  const projectId = projectStore.activeProject?.id
  if (!projectId || memorySaving.value) return
  memorySaving.value = true
  memoryError.value = ''
  try {
    await saveCopilotMemory({ projeto_id: projectId, chave: memoryKey.value, valor: memoryValue.value.trim() })
    memoryKey.value = ''
    memoryValue.value = ''
    await loadMemories()
  } catch (error) {
    memoryError.value = error.response?.data?.detail || 'Falha ao salvar memória.'
  } finally {
    memorySaving.value = false
  }
}

async function removeMemory(id) {
  try {
    await deleteCopilotMemory(id)
    memories.value = memories.value.filter(memory => memory.id !== id)
    memoryError.value = ''
  } catch (error) {
    memoryError.value = error.response?.data?.detail || 'Falha ao excluir memória.'
  }
}

function memoryText(value) {
  return typeof value === 'string' ? value : JSON.stringify(value)
}

function summaryUsageText(usage) {
  const input = Number(usage.input_tokens ?? usage.usage?.input_tokens ?? 0)
  const output = Number(usage.output_tokens ?? usage.usage?.output_tokens ?? 0)
  const cost = usage.estimated_cost_usd
  const model = usage.model || 'Provedor de IA'
  const tokens = new Intl.NumberFormat('pt-BR').format(input + output)
  return `${model} · ${tokens} tokens${Number.isFinite(Number(cost)) ? ` · US$ ${Number(cost).toFixed(6)} estimados` : ''}`
}

function formatAnswer(value) {
  const escapeHtml = (text) => String(text).replace(/[&<>"']/g, (char) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  })[char])
  const inline = (text) => escapeHtml(text)
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
  const output = []
  let inList = false
  for (const line of String(value || '').replace(/\r/g, '').split('\n')) {
    const item = line.match(/^\s*-\s+(.+)$/)
    if (item) {
      if (!inList) output.push('<ul>')
      inList = true
      output.push(`<li>${inline(item[1])}</li>`)
    } else {
      if (inList) output.push('</ul>')
      inList = false
      if (line.trim()) output.push(`<p>${inline(line)}</p>`)
    }
  }
  if (inList) output.push('</ul>')
  return output.join('')
}

async function selectThread(id, request = null) {
  const currentRequest = request ?? ++threadLoadRequest
  const ownsReadyState = request === null
  if (ownsReadyState) threadReady.value = false
  const selectedId = Number(id)
  threadId.value = selectedId
  messages.value = []
  threadSummary.value = ''
  summaryUsage.value = null
  summaryError.value = ''
  try {
    const { data } = await getCopilotThread(selectedId)
    if (currentRequest !== threadLoadRequest) return
    threadSummary.value = data.resumo || ''
    summaryUsage.value = data.resumo_telemetria || null
    messages.value = (data.mensagens || []).filter(m => m.papel !== 'tool').map(m => ({
      role: m.papel,
      text: m.conteudo,
      tools: Array.isArray(m.ferramentas) ? m.ferramentas.map(item => item.tool) : [],
      evidence: Array.isArray(m.ferramentas) ? m.ferramentas : []
    }))
    if (projectStore.activeProject) localStorage.setItem(`ortomapas.thread.${projectStore.activeProject.id}`, selectedId)
  } catch {
    if (currentRequest !== threadLoadRequest) return
    messages.value = []
  } finally {
    if (ownsReadyState && currentRequest === threadLoadRequest) threadReady.value = true
  }
}

async function summarizeThread() {
  if (!threadId.value || !messages.value.length || summaryLoading.value) return
  summaryLoading.value = true
  summaryError.value = ''
  try {
    const { data } = await summarizeCopilotThread(threadId.value)
    threadSummary.value = data.resumo || ''
    summaryUsage.value = data.telemetria?.usage_summary || data.telemetria || null
    const index = threads.value.findIndex(thread => Number(thread.id) === Number(threadId.value))
    if (index >= 0) threads.value[index].resumo = threadSummary.value
  } catch (error) {
    summaryError.value = error.response?.data?.detail || 'Falha ao resumir a conversa.'
  } finally {
    summaryLoading.value = false
  }
}

async function openThread() {
  if (threadId.value) await selectThread(threadId.value)
}

async function newThread(request = null) {
  const ownsReadyState = request === null
  const currentRequest = request ?? ++threadLoadRequest
  let readyGeneration = currentRequest
  if (ownsReadyState) threadReady.value = false
  const project = projectStore.activeProject
  if (!project) return
  const projectId = Number(project.id)
  try {
    const { data } = await createCopilotThread({ projeto_id: project.id, titulo: `Conversa ${new Date().toLocaleString('pt-BR')}` })
    if (Number(projectStore.activeProject?.id) !== projectId) return
    // A deliberate user request wins over any project-detail refresh that
    // finished while the thread was being created.
    if (!ownsReadyState && currentRequest !== threadLoadRequest) return
    const selectionRequest = ownsReadyState ? ++threadLoadRequest : currentRequest
    readyGeneration = selectionRequest
    threads.value = [data, ...threads.value]
    await selectThread(data.id, selectionRequest)
  } catch {
    if (currentRequest === threadLoadRequest) {
      threadId.value = null
      messages.value = []
    }
  } finally {
    if (ownsReadyState && readyGeneration === threadLoadRequest) threadReady.value = true
  }
}

// Project IDs arrive as strings from the summary list and numbers from the
// detail endpoint. Normalize them so the detail refresh does not reload the
// thread while a user is creating or sending a conversation.
watch(() => (projectStore.activeProject?.id == null ? null : Number(projectStore.activeProject.id)), loadThread, { immediate: true })

watch(() => projectStore.activeProject?.id, async (projectId) => {
  const request = ++analysisProductsRequest
  analysisProducts.value = []
  analysisProductId.value = ''
  if (!projectId) return
  analysisProductsLoading.value = true
  try {
    const { data } = await getOdmProducts(projectId)
    if (request !== analysisProductsRequest) return
    analysisProducts.value = (data.produtos || []).filter(product =>
      ['dsm', 'dtm'].includes(String(product.tipo).toLowerCase()) && product.status === 'disponivel' && product.processamento_status === 'concluido'
    )
    if (analysisProducts.value.length === 1) analysisProductId.value = String(analysisProducts.value[0].id)
  } catch {
    if (request === analysisProductsRequest) analysisProducts.value = []
  } finally {
    if (request === analysisProductsRequest) analysisProductsLoading.value = false
  }
}, { immediate: true })

async function publishSpatialResults(results) {
  const previews = new Map()
  for (const item of results || []) {
    const geometry = spatialGeometry(item)
    if (!geometry) continue
    if (isLayerSaved(item)) continue
    const geometryKey = JSON.stringify(geometry)
    if (previews.has(geometryKey)) {
      item.previewLayerId = previews.get(geometryKey)
      continue
    }
    const name = item.tool === 'buffer_geometria' ? 'Buffer gerado' : item.tool === 'intersectar_geometrias' ? 'Intersecao calculada' : 'Resultado espacial'
    const geojson = { type: 'Feature', properties: { tool: item.tool }, geometry }
    const id = `copilot-${item.tool}-${Date.now()}-${Math.random().toString(16).slice(2)}`
    item.previewLayerId = id
    previews.set(geometryKey, id)
    mapStore.addLayer({ id, name, type: 'analysis', geojson })
  }
}

function spatialGeometry(item) {
  const geometry = item?.result?.dados?.geometry
  return geometry?.type && Array.isArray(geometry.coordinates) ? geometry : null
}

function isLayerSaved(item) {
  const geometry = spatialGeometry(item)
  return !!geometry && savedLayers.value.some(layer => JSON.stringify(layer.geojson?.geometry || layer.geojson) === JSON.stringify(geometry))
}

async function saveSpatialResult(item) {
  const geometry = spatialGeometry(item)
  const projectId = projectStore.activeProject?.id
  if (!geometry || !projectId || item.savingLayer || isLayerSaved(item)) return
  item.savingLayer = true
  item.saveError = ''
  try {
    const name = item.tool === 'buffer_geometria' ? 'Buffer gerado' : item.tool === 'intersectar_geometrias' ? 'Intersecao calculada' : 'Resultado espacial'
    const geojson = { type: 'Feature', properties: { tool: item.tool }, geometry }
    const { data } = await saveCopilotLayer({ projeto_id: projectId, nome: name, ferramenta: item.tool, geojson, parametros: item.result?.dados || {} })
    const layer = { id: data.id, nome: name, ferramenta: item.tool, geojson }
    savedLayers.value = [layer, ...savedLayers.value]
    if (item.previewLayerId) mapStore.removeLayer(item.previewLayerId)
    mapStore.addLayer({ id: `saved-${data.id}`, name, type: 'analysis', geojson })
  } catch (error) {
    item.saveError = error.response?.data?.detail || 'Falha ao salvar a camada. A prévia continua disponível no mapa.'
  } finally {
    item.savingLayer = false
  }
}

function formatEvidence(item) {
  return JSON.stringify({ resultado: item.result?.dados || item.result || null, origem: item.result?.origem || null, erro: item.error || null }, null, 2)
}

async function send() {
  const text = prompt.value.trim()
  if (!text || !threadReady.value || !threadId.value) return
  messages.value.push({ role: 'user', text })
  prompt.value = ''
  loading.value = true
  try {
    if (threadId.value) await addCopilotMessage(threadId.value, { papel: 'user', conteudo: text })
    const context = { projeto_id: projectStore.activeProject?.id, geometria: mapStore.selectedGeometry, bbox: mapStore.clipBbox, produto_analise_id: analysisProductId.value ? Number(analysisProductId.value) : null }
    const { data } = await askCopilot(text, context, threadId.value)
    const evidence = data.ferramentas_executadas || []
    await publishSpatialResults(evidence)
    const answer = data.resposta?.answer || 'Analise concluida.'
    messages.value.push({ role: 'assistant', text: answer, tools: evidence.map(item => item.tool), evidence })
    if (threadId.value) await addCopilotMessage(threadId.value, { papel: 'assistant', conteudo: answer, ferramentas: evidence })
  } catch (error) {
    const answer = error.response?.data?.detail || 'Nao foi possivel consultar o copiloto.'
    messages.value.push({ role: 'assistant', text: answer })
    if (threadId.value) await addCopilotMessage(threadId.value, { papel: 'assistant', conteudo: answer })
  } finally {
    loading.value = false
  }
}

function quick(text) {
  if (loading.value) return
  prompt.value = text
  send()
}
</script><style scoped>.copilot{margin-top:12px;border-top:1px solid var(--border);padding-top:9px}.title{font-size:.8rem;font-weight:600;color:#7fd1b9;text-transform:uppercase}.threads{display:flex;gap:5px;margin-top:7px}.threads select{flex:1;min-width:0;background:var(--input-bg,#101820);color:var(--text);border:1px solid var(--border);padding:5px;font:inherit;font-size:.72rem}.threads button{width:30px;border:1px solid #52616b;background:#17242c;color:#7fd1b9;cursor:pointer}.threads button:disabled{opacity:.5}.messages{max-height:360px;overflow:auto;margin:8px 0}.empty{font-size:.75rem;color:var(--text-dim);padding:8px 0}.message{padding:7px;margin:5px 0;border-left:2px solid #40515c;background:#17242c;font-size:.75rem}.message.user{border-color:#56b4d3}.message-content p{margin:3px 0;white-space:pre-wrap}.message-content ul{margin:3px 0;padding-left:18px}.message-content code{font:11px/1.4 monospace;color:#b3d7ff}.message small{color:#7fd1b9}.evidence{margin-top:7px;color:#9cd9d0}.evidence summary{cursor:pointer;font-size:.7rem}.evidence-item{margin-top:5px;padding:5px;background:#101820;border:1px solid var(--border)}.evidence-item pre{white-space:pre-wrap;overflow-wrap:anywhere;font:11px/1.4 monospace;margin:4px 0;color:#d6e3e8}form{display:flex;gap:6px}textarea{flex:1;resize:vertical;background:var(--input-bg,#101820);color:var(--text);border:1px solid var(--border);padding:7px;font:inherit}form button{width:34px;border:1px solid #52616b;background:#17242c;color:#7fd1b9;cursor:pointer}form button:disabled{opacity:.5}
.selection{display:flex;align-items:center;gap:5px;margin-top:7px;padding:5px 6px;border:1px solid #315563;background:#12242b;color:#9cd9d0;font-size:.72rem}.selection span{flex:1}.selection button{width:27px;height:25px;border:1px solid #52616b;background:#17242c;color:#7fd1b9;cursor:pointer}.selection button:hover{background:#21404a}
.memory-panel{margin-top:7px;border:1px solid var(--border);padding:6px;font-size:.72rem}.memory-panel>summary{cursor:pointer;color:#9cd9d0}.memory-note{margin:6px 0;color:var(--text-dim);font-size:.68rem}.memory-form{display:grid;grid-template-columns:1fr auto;gap:5px;margin:6px 0}.memory-form input,.memory-form textarea{grid-column:1;background:var(--input-bg,#101820);color:var(--text);border:1px solid var(--border);padding:6px;font:inherit;min-width:0}.memory-form textarea{resize:vertical}.memory-form button{grid-column:2;grid-row:1 / span 2;width:32px;border:1px solid #52616b;background:#17242c;color:#7fd1b9;cursor:pointer}.memory-form button:disabled{opacity:.5}.memory-item{display:flex;align-items:center;gap:6px;border-top:1px solid var(--border);padding:5px 0}.memory-item span{display:grid;gap:2px;min-width:0;overflow-wrap:anywhere}.memory-item small{color:var(--text-dim)}.memory-item button{flex:none;width:28px;height:27px;border:1px solid var(--border);background:transparent;color:#e18c78;cursor:pointer}.memory-error{color:#ff9f90;font-size:.7rem}
.analysis-surface{display:grid;gap:4px;margin-top:7px;padding:6px;border:1px solid #315563;background:#12242b;color:#9cd9d0;font-size:.72rem}.analysis-surface select{width:100%;background:var(--input-bg,#101820);color:var(--text);border:1px solid var(--border);padding:5px;font:inherit}.analysis-surface small{color:var(--text-dim);font-size:.67rem}
.layer-action{display:flex;align-items:center;justify-content:space-between;gap:8px;margin-top:6px;font-size:.68rem;color:#9cd9d0}.layer-action button{display:inline-flex;align-items:center;gap:6px;border:1px solid #52616b;background:#17242c;color:#d6e3e8;padding:5px 8px;font:inherit;cursor:pointer}.layer-action button:disabled{opacity:.6;cursor:wait}.layer-error{color:#ff9f90}
.summary-panel{margin-top:7px;border:1px solid #315563;background:#12242b;padding:6px;font-size:.72rem}.summary-panel>summary{cursor:pointer;color:#9cd9d0}.summary-panel p{margin:6px 0;white-space:pre-wrap;line-height:1.4}.summary-panel small{display:block;border-top:1px solid var(--border);padding-top:5px;color:var(--text-dim);font-size:.65rem}.threads button[title="Resumir conversa"]{color:#c7b7ff}
</style>
