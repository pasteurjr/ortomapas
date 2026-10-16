<template><section class="copilot"><div class="title"><i class="pi pi-sparkles"></i> Copiloto geoespacial</div><div v-if="mapStore.selectedGeometry" class="selection"><i class="pi pi-map-marker"></i><span>Geometria selecionada</span><button type="button" title="Medir area e perimetro" @click="quick('Calcule a area e o perimetro da geometria desenhada no mapa.')"><i class="pi pi-ruler"></i></button><button type="button" title="Analisar declividade" @click="quick('Calcule a declividade media e maxima dentro da geometria desenhada no mapa.')"><i class="pi pi-chart-line"></i></button><button type="button" title="Calcular volume" @click="quick('Calcule o volume do relevo dentro da geometria desenhada no mapa usando a cota media.')"><i class="pi pi-chart-bar"></i></button></div><div class="messages"><div v-if="!messages.length" class="empty">Pergunte sobre produtos, qualidade, relevo ou análises do projeto.</div><div v-for="(m,i) in messages" :key="i" class="message" :class="m.role"><b>{{m.role==='user'?'Você':'Copiloto'}}</b><p>{{m.text}}</p><small v-if="m.tools?.length">Ferramentas: {{m.tools.join(', ')}}</small><details v-if="m.evidence?.length" class="evidence"><summary>Ver resultados e origem dos cálculos</summary><div v-for="(item,j) in m.evidence" :key="j" class="evidence-item"><b>{{item.tool}}</b><pre>{{formatEvidence(item)}}</pre></div></details></div></div><form @submit.prevent="send"><textarea v-model="prompt" rows="2" placeholder="Ex.: compare DSM e DTM deste projeto..." :disabled="loading"></textarea><button :disabled="loading || !prompt.trim()" title="Enviar"><i :class="loading?'pi pi-spin pi-spinner':'pi pi-send'"></i></button></form></section></template>
<script setup>
import { ref, watch } from 'vue'
import { askCopilot, createCopilotThread, getCopilotThread, addCopilotMessage, getCopilotLayers, saveCopilotLayer } from '../api/client'
import { useProjectStore } from '../stores/projectStore'
import { useMapStore } from '../stores/mapStore'

const projectStore = useProjectStore()
const mapStore = useMapStore()
const prompt = ref('')
const loading = ref(false)
const messages = ref([])
const threadId = ref(null)

async function loadThread() {
  const project = projectStore.activeProject
  if (!project) return
  const key = `ortomapas.thread.${project.id}`
  let id = localStorage.getItem(key)
  try {
    if (id) {
      const history = await getCopilotThread(Number(id))
      threadId.value = Number(id)
      messages.value = (history.data.mensagens || []).filter(m => m.papel !== 'tool').map(m => ({
        role: m.papel,
        text: m.conteudo,
        tools: Array.isArray(m.ferramentas) ? m.ferramentas.map(item => item.tool) : [],
        evidence: Array.isArray(m.ferramentas) ? m.ferramentas : []
      }))
    } else {
      throw new Error('Nova conversa')
    }
  } catch {
    try {
      const { data } = await createCopilotThread({ projeto_id: project.id, titulo: `Copiloto - ${project.nome}` })
      id = data.id
      localStorage.setItem(key, id)
      threadId.value = Number(id)
      messages.value = []
    } catch {
      threadId.value = null
      messages.value = []
    }
  }
  try {
    const saved = await getCopilotLayers(project.id)
    ;(saved.data.camadas || []).forEach(layer => mapStore.addLayer({ id: `saved-${layer.id}`, name: layer.nome, type: 'analysis', geojson: layer.geojson }))
  } catch {}
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
</script><style scoped>.copilot{margin-top:12px;border-top:1px solid var(--border);padding-top:9px}.title{font-size:.8rem;font-weight:600;color:#7fd1b9;text-transform:uppercase}.messages{max-height:230px;overflow:auto;margin:8px 0}.empty{font-size:.75rem;color:var(--text-dim);padding:8px 0}.message{padding:7px;margin:5px 0;border-left:2px solid #40515c;background:#17242c;font-size:.75rem}.message.user{border-color:#56b4d3}.message p{margin:3px 0;white-space:pre-wrap}.message small{color:#7fd1b9}.evidence{margin-top:7px;color:#9cd9d0}.evidence summary{cursor:pointer;font-size:.7rem}.evidence-item{margin-top:5px;padding:5px;background:#101820;border:1px solid var(--border)}.evidence-item pre{white-space:pre-wrap;overflow-wrap:anywhere;font:11px/1.4 monospace;margin:4px 0;color:#d6e3e8}form{display:flex;gap:6px}textarea{flex:1;resize:vertical;background:var(--input-bg,#101820);color:var(--text);border:1px solid var(--border);padding:7px;font:inherit}form button{width:34px;border:1px solid #52616b;background:#17242c;color:#7fd1b9;cursor:pointer}form button:disabled{opacity:.5}
.selection{display:flex;align-items:center;gap:5px;margin-top:7px;padding:5px 6px;border:1px solid #315563;background:#12242b;color:#9cd9d0;font-size:.72rem}.selection span{flex:1}.selection button{width:27px;height:25px;border:1px solid #52616b;background:#17242c;color:#7fd1b9;cursor:pointer}.selection button:hover{background:#21404a}
</style>
