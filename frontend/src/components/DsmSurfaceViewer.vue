<template>
  <div class="surface-view">
    <header><strong>{{ product.tipo === 'dtm' ? 'Terreno DTM 3D' : 'Superficie DSM 3D' }}</strong><div>
      <button title="Alternar wireframe" :aria-pressed="wireframe" @click="wireframe = !wireframe; updateMaterial()"><i class="pi pi-th-large"></i></button>
      <button title="Enquadrar" @click="fit"><i class="pi pi-expand"></i></button>
      <button title="Fechar" @click="$emit('close')"><i class="pi pi-times"></i></button>
    </div></header>
    <div ref="host" class="host"><div v-if="loading" class="overlay">Carregando DSM...</div><div v-else-if="error" class="overlay error" role="alert">{{ error }}</div></div>
    <footer><span class="legend"><i style="background:hsl(245,65%,50%)"></i>{{ min.toFixed(1) }} m <i style="background:hsl(122,65%,50%)"></i>{{ ((min + max) / 2).toFixed(1) }} m <i style="background:hsl(0,65%,50%)"></i>{{ max.toFixed(1) }} m</span><span>Escala XYZ 1:1 · {{ metricCrs }} · {{ triangles }} triangulos</span></footer>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'
import { getSurfaceGrid } from '../api/client'
import { terrainGeometry } from '../utils/terrainGeometry'

const props = defineProps({ product: { type: Object, required: true } })
defineEmits(['close'])
const host = ref(null), loading = ref(true), error = ref(''), wireframe = ref(false)
const min = ref(0), max = ref(0), metricCrs = ref(''), triangles = ref(0)
let renderer, scene, camera, controls, mesh, frame, observer, disposed = false
function fit() {
  if (!mesh) return
  const box = new THREE.Box3().setFromObject(mesh), s = box.getBoundingSphere(new THREE.Sphere())
  const direction = new THREE.Vector3(.65, .7, 1).normalize()
  const right = new THREE.Vector3().crossVectors(camera.up, direction).normalize()
  const up = new THREE.Vector3().crossVectors(direction, right).normalize()
  const tanV = Math.tan(camera.fov * Math.PI / 360), tanH = tanV * camera.aspect
  let d = 0
  for (const x of [box.min.x, box.max.x]) for (const y of [box.min.y, box.max.y]) for (const z of [box.min.z, box.max.z]) {
    const corner = new THREE.Vector3(x, y, z).sub(s.center)
    d = Math.max(d, corner.dot(direction) + Math.max(Math.abs(corner.dot(right)) / tanH, Math.abs(corner.dot(up)) / tanV))
  }
  d *= 1.12
  camera.near = Math.max(.01, s.radius / 1000); camera.far = d * 10; camera.updateProjectionMatrix()
  camera.position.copy(s.center).add(direction.multiplyScalar(d))
  controls.target.copy(s.center); controls.update()
}
function updateMaterial() { if (mesh) mesh.material.wireframe = wireframe.value }
async function load() {
  try {
    const { data } = await getSurfaceGrid(props.product.id)
    if (disposed) return
    const geometry = terrainGeometry(data)
    min.value = data.min; max.value = data.max; metricCrs.value = data.metric_crs; triangles.value = geometry.index.count / 3
    mesh = new THREE.Mesh(geometry, new THREE.MeshLambertMaterial({ vertexColors: true, side: THREE.DoubleSide }))
    scene.add(mesh); fit()
  } catch (e) { error.value = e.response?.data?.detail || e.message || 'Falha ao carregar superficie' }
  finally { loading.value = false }
}
onMounted(() => {
  scene = new THREE.Scene(); scene.background = new THREE.Color('#101820')
  camera = new THREE.PerspectiveCamera(55, 1, .1, 10000)
  renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true })
  host.value.appendChild(renderer.domElement); controls = new OrbitControls(camera, renderer.domElement)
  scene.add(new THREE.HemisphereLight(0xffffff, 0x667788, 2))
  const sun = new THREE.DirectionalLight(0xffffff, 2); sun.position.set(200, 300, 100); scene.add(sun)
  observer = new ResizeObserver(() => {
    const w = host.value.clientWidth, h = host.value.clientHeight
    camera.aspect = w / Math.max(h, 1); camera.updateProjectionMatrix(); renderer.setSize(w, h, false); fit()
  }); observer.observe(host.value)
  const animate = () => { controls.update(); renderer.render(scene, camera); frame = requestAnimationFrame(animate) }
  animate(); load()
})
onUnmounted(() => {
  disposed = true; cancelAnimationFrame(frame); observer?.disconnect(); controls?.dispose()
  renderer?.dispose(); mesh?.geometry.dispose(); mesh?.material.dispose()
})
</script>

<style scoped>
.surface-view{position:fixed;inset:4vh 4vw;background:#101820;color:#e8f0f2;z-index:2100;display:flex;flex-direction:column;border:1px solid #40515c}
header{display:flex;justify-content:space-between;align-items:center;padding:12px 16px;background:#17242c}
button{background:transparent;border:1px solid #52616b;color:#dce7eb;width:34px;height:32px;margin-left:5px;cursor:pointer}
button[aria-pressed=true]{background:#276653}.host{position:relative;flex:1;min-height:0}.host :deep(canvas){display:block;width:100%;height:100%}
.overlay{position:absolute;inset:0;display:grid;place-items:center;background:#101820aa}.error{color:#ffb4a9}
footer{display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px;padding:8px 16px;color:#b4c7cd;background:#17242c;font-size:.78rem}
.legend{display:flex;align-items:center;gap:8px}.legend i{width:10px;height:10px;display:inline-block}
</style>
