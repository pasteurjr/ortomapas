import assert from 'node:assert/strict'
import { analysisRasterLayer } from '../src/utils/analysisProducts.js'

assert.equal(analysisRasterLayer({ id: 1, ortomapa_id: 34, resultado: {} }), null)
const result = { id: 71, projeto_id: 62, nome: 'Declividade', resultado_path: 'output.tif', resultado: { style: { kind: 'slope' } } }
assert.equal(analysisRasterLayer(result).sourceId, 71)
assert.equal(analysisRasterLayer(result).type, 'analysis-raster')
assert.equal(analysisRasterLayer(result).projectId, 62)
console.log('Analysis products: genuine output IDs; no source-map fallback')
