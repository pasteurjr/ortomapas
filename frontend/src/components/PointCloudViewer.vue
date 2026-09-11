<template>
  <div class="viewer-shell" ref="shell">
    <header class="viewer-header">
      <div><strong>{{ product?.tipo === 'nuvem_pontos' ? 'Nuvem de pontos 3D' : 'Visualizador 3D' }}</strong><small>{{ product?.formato }} · {{ formatNumber(meta.total) }} pontos</small></div>
      <div class="viewer-actions">
        <button class="icon-button" title="Enquadrar nuvem" @click="fitView"><i class="pi pi-expand"></i></button>
        <button class="icon-button" title="Tela cheia" @click="fullscreen"><i class="pi pi-window-maximize"></i></button>
        <button class="icon-button" title="Fechar" @click="$emit('close')"><i class="pi pi-times"></i></button>
      </div>
    </header>
    <div class="viewer-body">
      <div ref="canvasHost" class="canvas-host"></div>
      <div v-if="loading" class="overlay"><i class="pi pi-spin pi-spinner"></i> Carregando amostra...</div>
      <div v-if="error" class="overlay error">{{ error }}</div>
      <aside class="tools-panel">
        <label>Tamanho dos pontos <output>{{ pointSize.toFixed(1) }}</output></label>
        <input v-model.number="pointSize" type="range" min="0.5" max="8" step="0.5" @input="updateMaterial" />
        <label>Coloração</label>
        <select v-model="colorMode" @change="updateColors"><option value="elevation">Elevação</option><option value="intensity">Intensidade</option></select>
        <label class="check"><input v-model="showGrid" type="checkbox" @change="renderScene" /> Grade</label>
        <label class="check"><input v-model="showAxes" type="checkbox" @change="renderScene" /> Eixos</label>
        <button class="measure-button" :class="{ active: measuring }" @click="toggleMeasure"><i class="pi pi-arrows-h"></i> {{ measuring ? 'Clique em dois pontos' : 'Medir distância' }}</button>
        <button v-if="measureDistance !== null" class="clear-button" @click="clearMeasure"><i class="pi pi-eraser"></i> Limpar medição</button>
        <div v-if="measureDistance !== null" class="measure-result"><span>Distância</span><b>{{ measureDistance.toFixed(2) }} m</b></div>
        <div class="stats"><span>Amostra</span><b>{{ formatNumber(meta.sampled) }}</b><span>Elevação</span><b>{{ elevationRange }}</b></div>
      </aside>
    </div>
    <footer>Arraste para orbitar · Shift + arraste para deslocar · roda para zoom</footer>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'
import { getPointCloud } from '../api/client'

const props = defineProps({ product: { type: Object, required: true } })
defineEmits(['close'])
const canvasHost = ref(null); const shell = ref(null); const loading = ref(false); const error = ref('')
const pointSize = ref(2); const colorMode = ref('elevation'); const showGrid = ref(true); const showAxes = ref(true)
const measuring = ref(false); const measureDistance = ref(null); let measurePoints = []; let measureLine; let measureMarkers = []
const meta = ref({ total: 0, sampled: 0, minZ: 0, maxZ: 0 }); let renderer; let scene; let camera; let controls; let points; let grid; let axes; let frame; let raycaster; let pointer
const elevationRange = computed(() => `${meta.value.minZ.toFixed(1)} – ${meta.value.maxZ.toFixed(1)} m`)
const formatNumber = (n) => Number(n || 0).toLocaleString('pt-BR')

function initScene () {
  scene = new THREE.Scene(); scene.background = new THREE.Color('#101820')
  camera = new THREE.PerspectiveCamera(55, 1, 0.1, 100000); camera.position.set(0, -1.6, 1.2)
  renderer = new THREE.WebGLRenderer({ antialias: true }); renderer.setPixelRatio(Math.min(devicePixelRatio, 2)); canvasHost.value.appendChild(renderer.domElement)
  controls = new OrbitControls(camera, renderer.domElement); controls.enableDamping = true; controls.target.set(0, 0, 0)
  raycaster = new THREE.Raycaster(); pointer = new THREE.Vector2(); renderer.domElement.addEventListener('pointerdown', pickPoint)
  grid = new THREE.GridHelper(10, 20, '#52616b', '#263640'); grid.rotation.x = 0; scene.add(grid)
  axes = new THREE.AxesHelper(5); scene.add(axes)
  resize(); window.addEventListener('resize', resize); frame = requestAnimationFrame(animate)
}
function resize () { if (!renderer || !canvasHost.value) return; const w = canvasHost.value.clientWidth; const h = canvasHost.value.clientHeight; camera.aspect = w / Math.max(h, 1); camera.updateProjectionMatrix(); renderer.setSize(w, h, false) }
function animate () { controls?.update(); renderer?.render(scene, camera); frame = requestAnimationFrame(animate) }
function renderScene () { if (grid) grid.visible = showGrid.value; if (axes) axes.visible = showAxes.value }
function updateMaterial () { if (points) points.material.size = pointSize.value }
function updateColors () { if (!points) return; const mode = colorMode.value; const values = points.userData[mode] || points.userData.elevation; const colors = new Float32Array(values.length * 3); const min = Math.min(...values); const max = Math.max(...values); values.forEach((v, i) => { const t = (v - min) / Math.max(max - min, 1e-9); const c = new THREE.Color(); c.setHSL((mode === 'intensity' ? 0.65 - t * 0.65 : 0.68 - t * 0.68), 0.85, 0.54); colors[i * 3] = c.r; colors[i * 3 + 1] = c.g; colors[i * 3 + 2] = c.b }); points.geometry.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3)); points.geometry.attributes.color.needsUpdate = true }
function fitView () { if (!points) return; const sphere = new THREE.Box3().setFromObject(points).getBoundingSphere(new THREE.Sphere()); const distance = sphere.radius / Math.sin(camera.fov * Math.PI / 360); camera.position.copy(sphere.center).add(new THREE.Vector3(distance * .8, -distance * .8, distance * .55)); controls.target.copy(sphere.center); camera.near = Math.max(sphere.radius / 1000, .01); camera.far = sphere.radius * 20; camera.updateProjectionMatrix(); controls.update() }
function fullscreen () { shell.value?.requestFullscreen?.() }
function toggleMeasure () { measuring.value = !measuring.value; if (!measuring.value) clearMeasure() }
function clearMeasure () { measurePoints = []; measureDistance.value = null; if (measureLine) { measureLine.geometry.dispose(); measureLine.material.dispose(); scene.remove(measureLine); measureLine = null }; measureMarkers.forEach((m) => { m.geometry.dispose(); m.material.dispose(); scene.remove(m) }); measureMarkers = [] }
function pickPoint (event) {
  if (!measuring.value || !points) return
  const rect = renderer.domElement.getBoundingClientRect(); pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1; pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1; raycaster.params.Points.threshold = Math.max(pointSize.value / 80, .04); raycaster.setFromCamera(pointer, camera)
  const hit = raycaster.intersectObject(points)[0]; if (!hit) return
  measurePoints.push(hit.point.clone()); const marker = new THREE.Mesh(new THREE.SphereGeometry(.08, 12, 8), new THREE.MeshBasicMaterial({ color: '#ffcf56' })); marker.position.copy(hit.point); scene.add(marker); measureMarkers.push(marker)
  if (measurePoints.length === 2) { const geometry = new THREE.BufferGeometry().setFromPoints(measurePoints); measureLine = new THREE.Line(geometry, new THREE.LineBasicMaterial({ color: '#ffcf56' })); scene.add(measureLine); measureDistance.value = measurePoints[0].distanceTo(measurePoints[1]); measuring.value = false }
}
async function loadCloud () {
  loading.value = true; error.value = ''
  try {
    const { data } = await getPointCloud(props.product.id, 120000); const { x, y, z, intensity } = data.points; const cx = (Math.min(...x) + Math.max(...x)) / 2; const cy = (Math.min(...y) + Math.max(...y)) / 2; const cz = (Math.min(...z) + Math.max(...z)) / 2
    const maxExtent = Math.max(Math.max(...x) - Math.min(...x), Math.max(...y) - Math.min(...y), Math.max(...z) - Math.min(...z), 1); const scale = 10 / maxExtent; const pos = new Float32Array(x.length * 3); x.forEach((v, i) => { pos[i * 3] = (v - cx) * scale; pos[i * 3 + 1] = (z[i] - cz) * scale; pos[i * 3 + 2] = (v = y[i] - cy) * scale })
    points?.geometry.dispose(); points?.material.dispose(); const geometry = new THREE.BufferGeometry(); geometry.setAttribute('position', new THREE.BufferAttribute(pos, 3)); points = new THREE.Points(geometry, new THREE.PointsMaterial({ size: pointSize.value / 100, vertexColors: true, sizeAttenuation: true })); points.userData.elevation = z; points.userData.intensity = intensity.length ? intensity : z; scene.add(points); meta.value = { total: data.total, sampled: data.sampled, minZ: Math.min(...z), maxZ: Math.max(...z) }; updateColors(); fitView()
  } catch (e) { error.value = e.response?.data?.detail || 'Nao foi possivel carregar a nuvem de pontos.' } finally { loading.value = false }
}
onMounted(() => { initScene(); loadCloud() }); watch(() => props.product?.id, loadCloud); onUnmounted(() => { cancelAnimationFrame(frame); window.removeEventListener('resize', resize); renderer?.domElement.removeEventListener('pointerdown', pickPoint); clearMeasure(); renderer?.dispose(); points?.geometry.dispose(); points?.material.dispose() })
</script>

<style scoped>
.viewer-shell{position:fixed;inset:4vh 4vw;background:#101820;color:#e8f0f2;z-index:2000;display:flex;flex-direction:column;border:1px solid #40515c;box-shadow:0 20px 80px #000b;font-size:.82rem}.viewer-header{display:flex;justify-content:space-between;align-items:center;padding:12px 16px;background:#17242c;border-bottom:1px solid #40515c}.viewer-header strong{display:block;font-size:1rem}.viewer-header small{color:#9db0ba}.viewer-actions{display:flex;gap:6px}.icon-button{background:transparent;border:1px solid #536773;color:#dce7eb;width:34px;height:32px;cursor:pointer}.icon-button:hover{background:#2b414d}.viewer-body{position:relative;flex:1;min-height:320px}.canvas-host{position:absolute;inset:0}.canvas-host :deep(canvas){display:block;width:100%;height:100%}.tools-panel{position:absolute;top:14px;right:14px;width:190px;padding:12px;background:#17242ce8;border:1px solid #52616b;display:grid;gap:8px}.tools-panel label{color:#c9d6dc;font-size:.75rem}.tools-panel output{float:right;color:#7fd1b9}.tools-panel input[type=range]{width:100%;accent-color:#56b4d3}.tools-panel select{background:#101820;color:#e8f0f2;border:1px solid #52616b;padding:5px}.check{display:flex;gap:7px;align-items:center}.stats{display:grid;grid-template-columns:1fr auto;gap:4px;border-top:1px solid #40515c;padding-top:8px;color:#9db0ba}.stats b{color:#e8f0f2}.overlay{position:absolute;inset:0;display:grid;place-items:center;background:#101820aa;color:#dce7eb;gap:8px}.overlay.error{color:#ffb4a9}.viewer-shell footer{padding:7px 16px;color:#91a4ad;background:#17242c;border-top:1px solid #40515c;font-size:.72rem}
.measure-button,.clear-button{border:1px solid #52616b;background:#101820;color:#dce7eb;padding:6px;text-align:left;cursor:pointer}.measure-button.active{border-color:#ffcf56;color:#ffcf56}.clear-button{color:#ffb4a9}.measure-result{display:flex;justify-content:space-between;border-top:1px solid #40515c;padding-top:8px;color:#ffcf56}
</style>
