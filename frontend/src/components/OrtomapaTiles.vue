<template>
  <l-tile-layer v-if="url" :url="url" :opacity="opacity" :maxZoom="22" />
</template>

<script setup>
import { ref, watch, onUnmounted } from 'vue'
import { LTileLayer } from '@vue-leaflet/vue-leaflet'
import api from '../api/client'

const props = defineProps({ sourceId: { type: Number, required: true }, opacity: { type: Number, default: 1 } })
const url = ref('')
let timer
let generation = 0
async function refresh() {
  const request = ++generation
  clearTimeout(timer)
  try {
    const { data } = await api.get(`/ortomapas/${props.sourceId}/tile-access`)
    if (request !== generation) return
    url.value = data.url
    timer = setTimeout(refresh, (data.expires_in - 30) * 1000)
  } catch {
    if (request === generation) url.value = ''
  }
}
watch(() => props.sourceId, () => { url.value = ''; refresh() }, { immediate: true })
onUnmounted(() => { generation++; clearTimeout(timer) })
</script>
