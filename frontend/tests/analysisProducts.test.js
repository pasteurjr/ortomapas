import assert from 'node:assert/strict'
import { analysisRasterLayer, analysisVectorLayer } from '../src/utils/analysisProducts.js'
import { asFeatureCollection } from '../src/utils/vectorExport.js'

assert.equal(analysisRasterLayer({ id: 1, ortomapa_id: 34, resultado: {} }), null)
const result = { id: 71, projeto_id: 62, nome: 'Declividade', resultado_path: 'output.tif', resultado: { style: { kind: 'slope' } } }
assert.equal(analysisRasterLayer(result).sourceId, 71)
assert.equal(analysisRasterLayer(result).type, 'analysis-raster')
assert.equal(analysisRasterLayer(result).projectId, 62)
console.log('Analysis products: genuine output IDs; no source-map fallback')
const vector = { ...result, resultado: { style: { kind: 'contours' }, geojson: { type: 'FeatureCollection', features: [] } } }
assert.equal(analysisRasterLayer(vector), null)
assert.equal(analysisVectorLayer(vector).sourceId, 71)
assert.equal(analysisVectorLayer(vector).kind, 'contours')
assert.equal(asFeatureCollection(vector.resultado.geojson), vector.resultado.geojson)
assert.equal(asFeatureCollection({ type: 'Feature', properties: { elevation: 240 }, geometry: null }).features[0].properties.elevation, 240)
