<template>
  <section class="diff-view" aria-label="Diferenca DSM DTM">
    <header><strong>DSM − DTM · Altura relativa</strong><button title="Fechar diferenca" @click="$emit('close')"><i class="pi pi-times"></i></button></header>
    <div class="canvas-wrap"><canvas v-show="!error && !loading" ref="canvas" :style="{aspectRatio: `${stats.width}/${stats.height}`}" aria-label="Raster da diferenca de elevacao"></canvas><div v-if="loading" class="state" role="status">Alinhando grades...</div><div v-else-if="error" class="state error" role="alert">{{ error }}</div></div>
    <footer v-if="!loading && !error"><div class="legend"><span>{{ (-span).toFixed(1) }} m</span><i></i><span>{{ span.toFixed(1) }} m</span></div><span>Min {{ stats.min.toFixed(2) }} · Media {{ stats.mean.toFixed(2) }} · Max {{ stats.max.toFixed(2) }} m</span><span>{{ stats.crs }} · {{ stats.valid_pixels }} pixels validos · DTM alinhado ao DSM</span></footer>
  </section>
</template>
<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { getElevationDifference } from '../api/client'
const props=defineProps({processingId:{type:Number,required:true}})
defineEmits(['close'])
const canvas=ref(null),loading=ref(true),error=ref(''),stats=ref({min:0,max:0,mean:0,width:1,height:1})
const span=computed(()=>Math.max(Math.abs(stats.value.min),Math.abs(stats.value.max),1))
let disposed=false
onUnmounted(()=>{disposed=true})
onMounted(async()=>{
  try {
    const {data}=await getElevationDifference(props.processingId,128)
    if(disposed) return
    stats.value=data
    const c=canvas.value,ctx=c.getContext('2d');c.width=data.width;c.height=data.height
    const pixels=ctx.createImageData(c.width,c.height)
    data.differences.forEach((row,y)=>row.forEach((v,x)=>{
      if(v===null) return
      const t=Math.min(1,Math.abs(v)/span.value), base=v<0?[40,110,220]:[225,65,50],i=(y*c.width+x)*4
      base.forEach((channel,j)=>{pixels.data[i+j]=Math.round(240+(channel-240)*t)})
      pixels.data[i+3]=255
    }))
    ctx.putImageData(pixels,0,0)
  } catch(e) { if(!disposed) error.value=e.response?.data?.detail || 'Falha ao comparar superficies' }
  finally { if(!disposed) loading.value=false }
})
</script>
<style scoped>
.diff-view{position:fixed;inset:4vh 4vw;background:#101820;color:#e8f0f2;z-index:2200;display:flex;flex-direction:column;border:1px solid #40515c}header{display:flex;align-items:center;justify-content:space-between;padding:12px 16px;background:#17242c}button{width:34px;height:32px;border:1px solid #536773;background:transparent;color:#e8f0f2}.canvas-wrap{position:relative;flex:1;min-height:0;display:grid;place-items:center;padding:16px}.canvas-wrap canvas{width:min(100%,900px);height:auto;max-width:100%;max-height:100%;image-rendering:pixelated;object-fit:contain;background:#23313b}.state{position:absolute;inset:0;display:grid;place-items:center}.error{color:#ffb4a9}footer{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;padding:10px 16px;background:#17242c;font-size:.75rem}.legend{display:flex;gap:8px;align-items:center}.legend i{width:180px;height:12px;background:linear-gradient(90deg,rgb(40,110,220),rgb(240,240,240),rgb(225,65,50))}
</style>
