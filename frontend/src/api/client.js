import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json',
  },
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('ortomapas_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message)
    return Promise.reject(error)
  }
)

// Projects
export function getProjects() {
  return api.get('/projetos')
}

export function getProject(id) {
  return api.get(`/projetos/${id}`)
}

export function createProject(data) {
  return api.post('/projetos', data)
}

export function updateProject(id, data) {
  return api.put(`/projetos/${id}`, data)
}

export function deleteProject(id) {
  return api.delete(`/projetos/${id}`)
}

export function searchProjects(q) {
  return api.get('/projetos/search', { params: { q } })
}

export function login(data) {
  return api.post('/auth/login', data)
}

export function registerUser(data) {
  return api.post('/auth/register', data)
}

// Voos (Flights)
export function getVoos(projetoId) {
  return api.get('/voos', { params: { projeto_id: projetoId } })
}

export function getVoo(id) {
  return api.get(`/voos/${id}`)
}

export function createVoo(data) {
  return api.post('/voos', data)
}

export function updateVoo(id, data) {
  return api.put(`/voos/${id}`, data)
}

export function deleteVoo(id) {
  return api.delete(`/voos/${id}`)
}

export function createOdmTask(formData) {
  return api.post('/odm/tasks', formData, { headers: { 'Content-Type': 'multipart/form-data' }, timeout: 300000 })
}

export function getOdmProcessamentos(projetoId) {
  return api.get('/odm/processamentos', { params: { projeto_id: projetoId } })
}

export function importOdmProducts(processingId) {
  return api.post(`/odm/processamentos/${processingId}/importar`)
}

export function getOdmProducts(projetoId) {
  return api.get('/odm/produtos', { params: { projeto_id: projetoId } })
}

export function getPointCloud(productId, maxPoints = 100000, bbox = {}) {
  return api.get(`/odm/produtos/${productId}/points`, { params: { max_points: maxPoints, ...bbox }, timeout: 120000 })
}

export function getSurfaceGrid(productId, maxSize = 128) {
  return api.get(`/odm/produtos/${productId}/surface`, { params: { max_size: maxSize }, timeout: 120000 })
}

export function getElevationDifference(processingId, maxSize = 128) {
  return api.get(`/odm/processamentos/${processingId}/elevacao-diferenca`, { params: { max_size: maxSize }, timeout: 120000 })
}

export function downloadOdmProduct(productId) {
  return api.get(`/odm/produtos/${productId}/download`, { responseType: 'blob', timeout: 120000 })
}

export function getOdmQuality(processingId) {
  return api.get(`/odm/processamentos/${processingId}/qualidade`)
}

// Ortomapas
export function getOrtomapas(projetoId) {
  return api.get('/ortomapas', { params: { projeto_id: projetoId } })
}

export function getOrtomapa(id) {
  return api.get(`/ortomapas/${id}`)
}

export function uploadOrtomapa(formData, { projeto_id, tipo } = {}) {
  return api.post('/ortomapas/upload', formData, {
    params: { projeto_id, tipo },
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 300000,
  })
}

export function updateOrtomapa(id, data) {
  return api.put(`/ortomapas/${id}`, data)
}

export function deleteOrtomapa(id) {
  return api.delete(`/ortomapas/${id}`)
}

// Analises
export function getAnalises(projetoId) {
  return api.get('/analises', { params: { projeto_id: projetoId } })
}

export function getAnalise(id) {
  return api.get(`/analises/${id}`)
}

export function createAnalise(data) {
  return api.post('/analises', data)
}

export function deleteAnalise(id) {
  return api.delete(`/analises/${id}`)
}

// Anotacoes
export function getAnotacoes(projetoId) {
  return api.get('/anotacoes', { params: { projeto_id: projetoId } })
}

export function createAnotacao(data) {
  return api.post('/anotacoes', data)
}

export function updateAnotacao(id, data) {
  return api.put(`/anotacoes/${id}`, data)
}

export function deleteAnotacao(id) {
  return api.delete(`/anotacoes/${id}`)
}

// Tools
export function runTool(toolName, params) {
  return api.post(`/tools/${toolName}`, params)
}

// Agent Tasks
export function getAgentTasks(status) {
  return api.get('/analises', { params: { status } })
}

// Export
export function exportLayer(params) {
  return api.post('/tools/exportar', params, { responseType: 'blob' })
}

export default api
