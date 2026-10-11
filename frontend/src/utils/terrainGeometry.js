import * as THREE from 'three'

export function terrainGeometry(data) {
  if (data.units !== 'm' || !data.x || !data.y) throw new Error('Superficie sem coordenadas metricas')
  const positions = [], colors = [], indexes = []
  const { width: w, height: h, elevations: values } = data
  const valid = (r, c) => Number.isFinite(values[r][c])
  for (let r = 0; r < h; r++) for (let c = 0; c < w; c++) {
    const z = valid(r, c) ? values[r][c] : data.min
    positions.push(data.x[r][c], z - data.min, -data.y[r][c])
    const t = (z - data.min) / Math.max(data.max - data.min, 1e-9)
    const color = new THREE.Color().setHSL(.68 - t * .68, .65, .5)
    colors.push(color.r, color.g, color.b)
  }
  for (let r = 0; r < h - 1; r++) for (let c = 0; c < w - 1; c++) {
    const a = r * w + c, b = a + 1, d = a + w, e = d + 1
    if (valid(r, c) && valid(r, c + 1) && valid(r + 1, c + 1)) indexes.push(a, e, b)
    if (valid(r, c) && valid(r + 1, c + 1) && valid(r + 1, c)) indexes.push(a, d, e)
  }
  if (!indexes.length) throw new Error('Superficie sem triangulos validos')
  const geometry = new THREE.BufferGeometry()
  geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3))
  geometry.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3))
  geometry.setIndex(indexes); geometry.computeVertexNormals(); geometry.computeBoundingBox()
  return geometry
}
