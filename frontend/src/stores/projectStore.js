import { defineStore } from 'pinia'
import { useMapStore } from './mapStore'
import {
  getProjects,
  getProject,
  createProject as apiCreateProject,
  getOrtomapas,
  getAnalises,
  getAnotacoes,
  getAgentTasks,
} from '../api/client'

export const useProjectStore = defineStore('project', {
  state: () => ({
    projects: [],
    activeProject: null,
    ortomapas: [],
    analises: [],
    anotacoes: [],
    agentTasks: [],
    loading: false,
    error: null,
    pollInterval: null,
  }),

  getters: {
    activeProjectId: (state) => state.activeProject?.id,
    canEdit: (state) => state.activeProject?.pode_editar === true,
    ortomapasForProject: (state) => state.ortomapas,
    completedAnalises: (state) =>
      state.analises.filter((a) => a.status === 'concluida'),
    pendingAnalises: (state) =>
      state.analises.filter((a) =>
        ['em_fila', 'processando'].includes(a.status)
      ),
    anotacoesByCategoria: (state) => {
      const grouped = {}
      for (const a of state.anotacoes) {
        const cat = a.categoria || 'sem_categoria'
        if (!grouped[cat]) grouped[cat] = []
        grouped[cat].push(a)
      }
      return grouped
    },
  },

  actions: {
    async fetchProjects() {
      this.loading = true
      try {
        const res = await getProjects()
        this.projects = res.data.projetos || res.data
      } catch (e) {
        this.error = e.message
      } finally {
        this.loading = false
      }
    },

    async setActiveProject(project) {
      useMapStore().clearAllLayers()
      this.ortomapas = []; this.analises = []; this.anotacoes = []
      this.activeProject = project
      if (project) {
        let details
        try { details = await getProject(project.id) }
        catch (e) {
          if (this.activeProject?.id === project.id) { this.activeProject = null; this.error = e.message; this.stopPolling() }
          return
        }
        if (this.activeProject?.id !== project.id) return
        this.activeProject = details.data
        await Promise.all([
          this.fetchOrtomapas(),
          this.fetchAnalises(),
          this.fetchAnotacoes(),
        ])
        this.startPolling()
      } else {
        this.ortomapas = []
        this.analises = []
        this.anotacoes = []
        this.stopPolling()
      }
    },

    async fetchOrtomapas() {
      if (!this.activeProject) return
      try {
        const id = this.activeProject.id
        const res = await getOrtomapas(id)
        if (this.activeProject?.id === id) this.ortomapas = res.data.ortomapas || res.data
      } catch (e) {
        this.error = e.message
      }
    },

    async fetchAnalises() {
      if (!this.activeProject) return
      try {
        const id = this.activeProject.id
        const res = await getAnalises(id)
        if (this.activeProject?.id === id) this.analises = res.data.analises || res.data
      } catch (e) {
        this.error = e.message
      }
    },

    async fetchAnotacoes() {
      if (!this.activeProject) return
      try {
        const id = this.activeProject.id
        const res = await getAnotacoes(id)
        if (this.activeProject?.id === id) this.anotacoes = res.data.anotacoes || res.data
      } catch (e) {
        this.error = e.message
      }
    },

    async pollAgentTasks() {
      try {
        const res = await getAgentTasks('em_fila,processando')
        this.agentTasks = res.data
      } catch (e) {
        // silent polling failure
      }
    },

    startPolling() {
      this.stopPolling()
      this.pollInterval = setInterval(() => {
        this.pollAgentTasks()
        this.fetchAnalises()
      }, 5000)
    },

    stopPolling() {
      if (this.pollInterval) {
        clearInterval(this.pollInterval)
        this.pollInterval = null
      }
    },

    async createProject(data) {
      try {
        const res = await apiCreateProject(data)
        this.projects.push(res.data)
        return res.data
      } catch (e) {
        this.error = e.message
        throw e
      }
    },
  },
})
