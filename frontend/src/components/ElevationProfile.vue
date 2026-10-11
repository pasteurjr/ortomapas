<template>
  <section class="elevation-profile" aria-label="Perfil altimetrico">
    <header>
      <strong>Perfil altimetrico</strong>
      <select v-model="productId" aria-label="Produto de elevacao" @change="calculate"><option :value="null" disabled>Selecionar DSM / DTM</option><option v-for="p in products" :key="p.id" :value="p.id">{{ p.tipo.toUpperCase() }} · {{ p.id }} · {{ p.odm_task_id.slice(0,8) }}</option></select>
      <button title="Desenhar linha de perfil" :aria-pressed="map.drawMode === 'profile'" :disabled="!productId" @click="map.setDrawMode(map.drawMode === 'profile' ? null : 'profile')"><i class="pi pi-pencil"></i></button>
      <button v-if="map.drawMode === 'profile'" title="Concluir linha de perfil" :disabled="map.profileVertexCount < 2" @click="map.finishProfile?.()"><i class="pi pi-check"></i></button>
      <button v-if="map.drawMode === 'profile'" title="Cancelar linha de perfil" @click="map.setDrawMode(null)"><i class="pi pi-undo"></i></button>
      <button title="Exportar perfil CSV" :disabled="!result || loading" @click="exportCsv"><i class="pi pi-download"></i></button>
      <button title="Fechar perfil" @click="map.profileOpen = false"><i class="pi pi-times"></i></button>
    </header>
    <div v-if="error" class="profile-state error" role="alert">{{ error }}</div>
    <div v-else-if="loading" class="profile-state" role="status">Calculando perfil...</div>
    <div v-else-if="!result" class="profile-state">{{ products.length ? 'Nenhuma linha selecionada' : 'Nenhum DSM / DTM disponivel' }}</div>
    <template v-else>
      <svg class="profile-chart" viewBox="0 0 900 180" role="img" aria-label="Grafico de elevacao por distancia em metros" @mousemove="inspect" @mouseleave="selected = null">
        <line x1="70" y1="140" x2="880" y2="140" stroke="#6b7a88"/><line x1="70" y1="15" x2="70" y2="140" stroke="#6b7a88"/>
        <g v-for="t in [0,.5,1]" :key="t"><line x1="70" :y1="15+125*t" x2="880" :y2="15+125*t" stroke="#38434e"/><text x="62" :y="20+125*t" text-anchor="end">{{ (maximum-(maximum-minimum)*t).toFixed(1) }}</text><text :x="70+810*t" y="158" text-anchor="middle">{{ (result.comprimento_m*t).toFixed(1) }}</text></g>
        <path :d="plot" stroke="#35c5a7" stroke-width="2" fill="none"/>
        <text x="460" y="176" text-anchor="middle">Distancia (m)</text><text x="12" y="85" transform="rotate(-90 12 85)" text-anchor="middle">Elevacao (m)</text>
        <line v-if="selected !== null" :x1="70+810*selected/(result.pontos-1)" :x2="70+810*selected/(result.pontos-1)" y1="15" y2="140" stroke="#ffd85c"/>
      </svg>
      <footer><span>{{ result.comprimento_m.toFixed(2) }} m · {{ result.pontos }} amostras · {{ result.crs_calculo }}</span><span v-if="selected !== null">{{ result.distancias_m[selected].toFixed(2) }} m / {{ result.elevacoes[selected] === null ? 'Sem dados' : result.elevacoes[selected].toFixed(2)+' m' }}</span><span v-else>Cotas {{ minimum.toFixed(2) }} – {{ maximum.toFixed(2) }} m</span></footer>
    </template>
  </section>
</template>

<script setup>
import { ref, computed, watch, onUnmounted } from 'vue'
import { useMapStore } from '../stores/mapStore'
import { useProjectStore } from '../stores/projectStore'
import api, { getOdmProducts } from '../api/client'
const map = useMapStore(), project = useProjectStore()
const products = ref([]), productId = ref(null), result = ref(null), loading = ref(false), error = ref(''), selected = ref(null)
let version = 0, productVersion = 0
const minimum = computed(() => Math.min(...(result.value?.elevacoes || []).filter(v => v !== null)))
const maximum = computed(() => Math.max(...(result.value?.elevacoes || []).filter(v => v !== null)))
const plot = computed(() => { let move = true; return (result.value?.elevacoes || []).map((v,i) => { if (v === null) { move=true; return '' }; const command=move?'M':'L'; move=false; return `${command}${70+810*i/(result.value.pontos-1)},${140-125*(v-minimum.value)/Math.max(maximum.value-minimum.value,1e-9)}` }).join(' ') })
async function calculate() {
  const request = ++version; result.value=null; error.value=''; selected.value=null
  if (!productId.value || !map.profileLine) { loading.value=false; return }
  loading.value=true
  try { const { data } = await api.post('/agents/tools/execute',{name:'perfil_altimetrico',arguments:{produto_id:productId.value,geometry:map.profileLine,crs:'EPSG:4326',samples:200}}); if(request===version) result.value=data.dados }
  catch(e) { if(request===version) error.value=e.response?.data?.detail || 'Falha ao calcular perfil' }
  finally { if(request===version) loading.value=false }
}
watch(() => project.activeProject?.id, async id => {
  const request=++productVersion; products.value=[]; productId.value=null; result.value=null; ++version
  if(!id) return
  try { const {data}=await getOdmProducts(id); if(request !== productVersion) return; products.value=data.produtos.filter(p=>['dsm','dtm'].includes(p.tipo)); productId.value=products.value[0]?.id || null; calculate() }
  catch(e) { if(request===productVersion) error.value=e.response?.data?.detail || 'Falha ao listar produtos' }
},{immediate:true})
watch(() => map.profileLine,calculate)
function inspect(event) { const box=event.currentTarget.getBoundingClientRect(); selected.value=Math.max(0,Math.min(result.value.pontos-1,Math.round(((event.clientX-box.left)/box.width*900-70)/810*(result.value.pontos-1)))) }
function exportCsv() { const r=result.value; const rows=['distancia_m,elevacao_m,longitude,latitude']; r.distancias_m.forEach((d,i)=>rows.push([d,r.elevacoes[i] ?? '',...r.coordinates_wgs84[i]].join(','))); const url=URL.createObjectURL(new Blob([rows.join('\n')],{type:'text/csv'})); const a=document.createElement('a'); a.href=url;a.download=`perfil_${productId.value}.csv`;a.click();URL.revokeObjectURL(url) }
onUnmounted(()=>{ ++version; ++productVersion; if(map.drawMode==='profile') map.setDrawMode(null) })
</script>

<style scoped>
.elevation-profile{position:absolute;bottom:0;left:0;right:0;height:280px;z-index:850;background:#1b242d;color:#e4ecf1;border-top:1px solid #536471;display:flex;flex-direction:column;padding:8px 12px;gap:6px}header{display:flex;align-items:center;gap:8px;flex-wrap:wrap}strong{font-size:.85rem}select{margin-left:auto;max-width:50%;background:#111a22;color:#e4ecf1;border:1px solid #536471;padding:6px}button{width:32px;height:32px;flex:none;background:transparent;border:1px solid #536471;color:#e4ecf1;cursor:pointer}button:disabled{opacity:.4;cursor:default}button[aria-pressed=true]{background:#276653}.profile-chart{width:100%;height:180px;min-height:0;flex:1}.profile-chart text{font-size:12px;fill:#bccbd5}footer{display:flex;justify-content:space-between;flex-wrap:wrap;gap:6px;font-size:.75rem;color:#bccbd5}.profile-state{flex:1;display:grid;place-items:center;font-size:.85rem}.error{color:#ffb4a9}
</style>
