<template>
  <section class="copilot">
    <div class="title"><i class="pi pi-sparkles"></i> Copiloto geoespacial</div>
    <div class="threads">
      <select v-model="threadId" aria-label="Conversas do projeto" :disabled="loading || !threads.length" @change="openThread">
        <option v-if="!threads.length" :value="null">Nenhuma conversa</option>
        <option v-for="thread in threads" :key="thread.id" :value="thread.id">{{thread.titulo || 'Conversa sem título'}}</option>
      </select>
      <button type="button" title="Nova conversa" aria-label="Nova conversa" :disabled="loading || !projectStore.activeProject" @click="newThread"><i class="pi pi-plus"></i></button>
    </div>
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
      <div v-if="!messages.length" class="empty">Pergunte sobre produtos, qualidade, relevo ou análises do projeto.</div>
      <div v-for="(m,i) in messages" :key="i" class="message" :class="m.role">
        <b>{{m.role==='user'?'Você':'Copiloto'}}</b><p>{{m.text}}</p><small v-if="m.tools?.length">Ferramentas: {{m.tools.join(', ')}}</small>
        <details v-if="m.evidence?.length" class="evidence"><summary>Ver resultados e origem dos cálculos</summary><div v-for="(item,j) in m.evidence" :key="j" class="evidence-item"><b>{{item.tool}}</b><pre>{{formatEvidence(item)}}</pre></div></details>
      </div>
    </div>
    <form @submit.prevent="send"><textarea v-model="prompt" rows="2" placeholder="Ex.: compare DSM e DTM deste projeto..." :disabled="loading"></textarea><button :disabled="loading || !prompt.trim()" title="Enviar" aria-label="Enviar"><i :class="loading?'pi pi-spin pi-spinner':'pi pi-send'"></i></button></form>
  </section>
</template>
<script setup>
import { ref, watch } from 'vue'
import { askCopilot, createCopilotThread, getCopilotThread, listCopilotThreads, addCopilotMessage, getCopilotLayers, saveCopilotLayer, listCopilotMemories, saveCopilotMemory, deleteCopilotMemory } from '../api/client'
import { useProjectStore } from '../stores/projectStore'
import { useMapStore } from '../stores/mapStore'

const projectStore = useProjectStore()
const mapStore = useMapStore()
const prompt = ref('')
const loading = ref(false)
const messages = ref([])
const threadId = ref(null)
const threads = ref([])
const memories = ref([])
const memoryKey = ref('')
const memoryValue = ref('')
const memorySaving = ref(false)
const memoryError = ref('')

async function loadThread() {
  const project = projectStore.activeProject
  if (!project) { threads.value = []; threadId.value = null; messages.value = []; memories.value = []; return }
  const key = `ortomapas.thread.${project.id}`
  try {
    const { data } = await listCopilotThreads(project.id)
    threads.value = data.conversas || []
  } catch {
    threads.value = []
  }
  const savedId = Number(localStorage.getItem(key))
  const selected = threads.value.find(thread => Number(thread.id) === savedId) || threads.value[0]
  if (selected) await selectThread(selected.id)
  else await newThread()
  try {
    const saved = await getCopilotLayers(project.id)
    ;(saved.data.camadas || []).forEach(layer => mapStore.addLayer({ id: `saved-${layer.id}`, name: layer.nome, type: 'analysis', geojson: layer.geojson }))
  } catch {}
  await loadMemories()
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

async function selectThread(id) {
  const selectedId = Number(id)
  threadId.value = selectedId
  try {
    const { data } = await getCopilotThread(selectedId)
    messages.value = (data.mensagens || []).filter(m => m.papel !== 'tool').map(m => ({
      role: m.papel,
      text: m.conteudo,
      tools: Array.isArray(m.ferramentas) ? m.ferramentas.map(item => item.tool) : [],
      evidence: Array.isArray(m.ferramentas) ? m.ferramentas : []
    }))
    if (projectStore.activeProject) localStorage.setItem(`ortomapas.thread.${projectStore.activeProject.id}`, selectedId)
  } catch {
    messages.value = []
  }
}

async function openThread() {
  if (threadId.value) await selectThread(threadId.value)
}

async function newThread() {
  const project = projectStore.activeProject
  if (!project) return
  try {
    const { data } = await createCopilotThread({ projeto_id: project.id, titulo: `Conversa ${new Date().toLocaleString('pt-BR')}` })
    threads.value = [data, ...threads.value]
    await selectThread(data.id)
  } catch {
    threadId.value = null
    messages.value = []
  }
}

watch(() => projectStore.activeProject, loadThread, { immediate: true })

async function publishSpatialResults(results) {
  for (const item of results || []) {
    const geometry = item?.result?.dados?.geometry
    if (!geometry) continue
    const name = item.tool === 'buffer_geometria' ? 'Buffer gerado' : item.tool === 'intersectar_geometrias' ? 'Intersecao calculada' : 'Resultado espacial'
    const geojson = { type: 'Feature', properties: { tool: item.tool }, geometry }
    const id = `copilot-${item.tool}-${Date.now()}-${Math.random().toString(16).slice(2)}`
    mapStore.addLayer({ id, name, type: 'analysis', geojson })
    try { await saveCopilotLayer({ projeto_id: projectStore.activeProject?.id, nome: name, ferramenta: item.tool, geojson, parametros: item.result?.dados || {} }) } catch {}
  }
}

function formatEvidence(item) {
  return JSON.stringify({ resultado: item.result?.dados || item.result || null, origem: item.result?.origem || null, erro: item.error || null }, null, 2)
}

async function send() {
  const text = prompt.value.trim()
  if (!text) return
  messages.value.push({ role: 'user', text })
  prompt.value = ''
  loading.value = true
  try {
    if (threadId.value) await addCopilotMessage(threadId.value, { papel: 'user', conteudo: text })
    const { data } = await askCopilot(text, { projeto_id: projectStore.activeProject?.id, geometria: mapStore.selectedGeometry, bbox: mapStore.clipBbox }, threadId.value)
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
</script><style scoped>.copilot{margin-top:12px;border-top:1px solid var(--border);padding-top:9px}.title{font-size:.8rem;font-weight:600;color:#7fd1b9;text-transform:uppercase}.threads{display:flex;gap:5px;margin-top:7px}.threads select{flex:1;min-width:0;background:var(--input-bg,#101820);color:var(--text);border:1px solid var(--border);padding:5px;font:inherit;font-size:.72rem}.threads button{width:30px;border:1px solid #52616b;background:#17242c;color:#7fd1b9;cursor:pointer}.threads button:disabled{opacity:.5}.messages{max-height:230px;overflow:auto;margin:8px 0}.empty{font-size:.75rem;color:var(--text-dim);padding:8px 0}.message{padding:7px;margin:5px 0;border-left:2px solid #40515c;background:#17242c;font-size:.75rem}.message.user{border-color:#56b4d3}.message p{margin:3px 0;white-space:pre-wrap}.message small{color:#7fd1b9}.evidence{margin-top:7px;color:#9cd9d0}.evidence summary{cursor:pointer;font-size:.7rem}.evidence-item{margin-top:5px;padding:5px;background:#101820;border:1px solid var(--border)}.evidence-item pre{white-space:pre-wrap;overflow-wrap:anywhere;font:11px/1.4 monospace;margin:4px 0;color:#d6e3e8}form{display:flex;gap:6px}textarea{flex:1;resize:vertical;background:var(--input-bg,#101820);color:var(--text);border:1px solid var(--border);padding:7px;font:inherit}form button{width:34px;border:1px solid #52616b;background:#17242c;color:#7fd1b9;cursor:pointer}form button:disabled{opacity:.5}
.selection{display:flex;align-items:center;gap:5px;margin-top:7px;padding:5px 6px;border:1px solid #315563;background:#12242b;color:#9cd9d0;font-size:.72rem}.selection span{flex:1}.selection button{width:27px;height:25px;border:1px solid #52616b;background:#17242c;color:#7fd1b9;cursor:pointer}.selection button:hover{background:#21404a}
.memory-panel{margin-top:7px;border:1px solid var(--border);padding:6px;font-size:.72rem}.memory-panel>summary{cursor:pointer;color:#9cd9d0}.memory-note{margin:6px 0;color:var(--text-dim);font-size:.68rem}.memory-form{display:grid;grid-template-columns:1fr auto;gap:5px;margin:6px 0}.memory-form input,.memory-form textarea{grid-column:1;background:var(--input-bg,#101820);color:var(--text);border:1px solid var(--border);padding:6px;font:inherit;min-width:0}.memory-form textarea{resize:vertical}.memory-form button{grid-column:2;grid-row:1 / span 2;width:32px;border:1px solid #52616b;background:#17242c;color:#7fd1b9;cursor:pointer}.memory-form button:disabled{opacity:.5}.memory-item{display:flex;align-items:center;gap:6px;border-top:1px solid var(--border);padding:5px 0}.memory-item span{display:grid;gap:2px;min-width:0;overflow-wrap:anywhere}.memory-item small{color:var(--text-dim)}.memory-item button{flex:none;width:28px;height:27px;border:1px solid var(--border);background:transparent;color:#e18c78;cursor:pointer}.memory-error{color:#ff9f90;font-size:.7rem}
</style>
