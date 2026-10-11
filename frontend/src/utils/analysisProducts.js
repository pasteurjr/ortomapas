export function analysisRasterLayer(analysis) {
  const result = analysis.resultado
  if (!analysis.resultado_path || !result?.style || result.geojson) return null
  return { id: `analysis-raster-${analysis.id}`, sourceId: analysis.id, type: 'analysis-raster',
    name: analysis.nome, legend: result.style, resource: result, projectId: analysis.projeto_id }
}

export function analysisVectorLayer(analysis) {
  const result = analysis.resultado
  if (!analysis.resultado_path || result?.geojson?.type !== 'FeatureCollection') return null
  return { id: `analysis-vector-${analysis.id}`, sourceId: analysis.id, type: 'analysis',
    name: analysis.nome, legend: result.style, resource: result, projectId: analysis.projeto_id,
    geojson: result.geojson, kind: result.style?.kind }
}
