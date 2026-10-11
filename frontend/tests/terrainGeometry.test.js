import assert from 'node:assert/strict'
import { terrainGeometry } from '../src/utils/terrainGeometry.js'
import * as THREE from 'three'

const data = { units: 'm', width: 2, height: 2, min: 0, max: 5, x: [[0, 100], [0, 100]], y: [[0, 0], [200, 200]], elevations: [[0, 1], [2, 3]] }
const g = terrainGeometry(data), p = g.getAttribute('position'), index = g.index.array
assert.equal(index.length, 6)
for(let i = 0; i < index.length; i += 3) {
  const a = new THREE.Vector3().fromBufferAttribute(p, index[i]), b = new THREE.Vector3().fromBufferAttribute(p, index[i+1]), c = new THREE.Vector3().fromBufferAttribute(p, index[i+2])
  assert.ok(b.sub(a).cross(c.sub(a)).length() / 2 > 10000)
}
assert.equal(g.boundingBox.max.x - g.boundingBox.min.x, 100)
assert.equal(g.boundingBox.max.z - g.boundingBox.min.z, 200)
const hole = terrainGeometry({ ...data, elevations: [[0, null], [2, 3]] })
assert.equal(hole.index.count, 3)
assert.throws(() => terrainGeometry({ ...data, units: 'degrees' }))
console.log('Terrain geometry: 2 non-degenerate triangles, metric dimensions, nodata and units OK')
