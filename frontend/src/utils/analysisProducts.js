export function analysisRasterLayer(analysis) {
  const result = analysis.resultado
  if (!analysis.resultado_path || !result?.style) return null
  return { id: `analysis-raster-${analysis.id}`, sourceId: analysis.id, type: 'analysis-raster',
    name: analysis.nome, legend: result.style, resource: result, projectId: analysis.projeto_id }
}
