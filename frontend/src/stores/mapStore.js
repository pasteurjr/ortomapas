import { defineStore } from 'pinia'

export const useMapStore = defineStore('map', {
  state: () => ({
    activeLayers: [],
    basemap: 'osm',
    zoom: 13,
    center: [-15.78, -47.93],
    cursorCoords: { lat: 0, lng: 0 },
    selectedFeature: null,
    measureMode: null, // 'distance' | 'area' | null
    drawMode: null, // 'point' | 'line' | 'polygon' | 'rectangle' | null
    compareMode: false,
    compareLeft: null,
    compareRight: null,
    pourPointCallback: null,
    clipBbox: (() => { try { return JSON.parse(localStorage.getItem('ortomapas.clipBbox') || 'null') } catch { return null } })(),
    selectedGeometry: null,
  }),

  getters: {
    visibleLayers: (state) =>
      state.activeLayers.filter((l) => l.visible),
    isLayerVisible: (state) => (layerId) =>
      state.activeLayers.some((l) => l.id === layerId && l.visible),
  },

  actions: {
    addLayer(layer) {
      const existing = this.activeLayers.find((l) => l.id === layer.id)
      if (!existing) {
        this.activeLayers.push({ ...layer, visible: true, opacity: 1.0 })
      }
    },

    removeLayer(layerId) {
      this.activeLayers = this.activeLayers.filter((l) => l.id !== layerId)
    },

    toggleLayer(layerId) {
      const layer = this.activeLayers.find((l) => l.id === layerId)
      if (layer) {
        layer.visible = !layer.visible
      }
    },

    setLayerOpacity(layerId, opacity) {
      const layer = this.activeLayers.find((l) => l.id === layerId)
      if (layer) {
        layer.opacity = opacity
      }
    },

    setView(center, zoom) {
      this.center = center
      if (zoom !== undefined) this.zoom = zoom
    },

    setCursorCoords(lat, lng) {
      this.cursorCoords = { lat, lng }
    },

    setMeasureMode(mode) {
      this.measureMode = mode
      if (mode) this.drawMode = null
    },

    setDrawMode(mode) {
      this.drawMode = mode
      if (mode) this.measureMode = null
    },

    setSelectedFeature(feature) {
      this.selectedFeature = feature
    },

    setCompareMode(enabled) {
      this.compareMode = enabled
    },

    setCompareLayers(left, right) {
      this.compareLeft = left
      this.compareRight = right
    },

    setPourPointCallback(callback) {
      this.pourPointCallback = callback
    },

    setClipBbox(bbox) { this.clipBbox = bbox; try { localStorage.setItem('ortomapas.clipBbox', JSON.stringify(bbox)) } catch {} },
    setSelectedGeometry(geometry) { this.selectedGeometry = geometry },

    handleMapClick(lat, lng) {
      if (this.pourPointCallback) {
        this.pourPointCallback(lat, lng)
        this.pourPointCallback = null
      }
    },

    clearAllLayers() {
      this.activeLayers = []
    },
  },
})
