export function asFeatureCollection(geojson) {
  if (geojson?.type === 'FeatureCollection') return geojson
  if (geojson?.type === 'Feature') return { type: 'FeatureCollection', features: [geojson] }
  return { type: 'FeatureCollection', features: [{ type: 'Feature', properties: {}, geometry: geojson }] }
}

export function vectorKml(geojson, name) {
  const ns = 'http://www.opengis.net/kml/2.2'
  const doc = document.implementation.createDocument(ns, 'kml', null)
  const node = (tag, text) => {
    const el = doc.createElementNS(ns, tag)
    if (text !== undefined) el.textContent = String(text)
    return el
  }
  const coords = points => points.map(([x, y, z = 0]) => `${x},${y},${z}`).join(' ')
  function geometry(g) {
    if (!g) return null
    if (g.type.startsWith('Multi') || g.type === 'GeometryCollection') {
      const group = node('MultiGeometry')
      const types = { MultiPoint: 'Point', MultiLineString: 'LineString', MultiPolygon: 'Polygon' }
      const parts = g.geometries || g.coordinates.map(coordinates => ({ type: types[g.type], coordinates }))
      parts.forEach(part => { const el = geometry(part); if (el) group.appendChild(el) })
      return group
    }
    const el = node(g.type)
    if (g.type === 'Polygon') {
      g.coordinates.forEach((ring, index) => {
        const boundary = node(index ? 'innerBoundaryIs' : 'outerBoundaryIs')
        const linear = node('LinearRing'); linear.appendChild(node('coordinates', coords(ring)))
        boundary.appendChild(linear); el.appendChild(boundary)
      })
    } else el.appendChild(node('coordinates', coords(g.type === 'Point' ? [g.coordinates] : g.coordinates)))
    return el
  }
  const content = node('Document'); content.appendChild(node('name', name))
  asFeatureCollection(geojson).features.forEach(feature => {
    const placemark = node('Placemark'); const props = feature.properties || {}
    placemark.appendChild(node('name', props.elevation_m != null ? `${props.elevation_m} m` : props.name || name))
    const data = node('ExtendedData')
    Object.entries(props).forEach(([key, value]) => {
      const entry = node('Data'); entry.setAttribute('name', key)
      entry.appendChild(node('value', typeof value === 'object' ? JSON.stringify(value) : value)); data.appendChild(entry)
    })
    placemark.appendChild(data)
    const geom = geometry(feature.geometry); if (geom) placemark.appendChild(geom)
    content.appendChild(placemark)
  })
  doc.documentElement.appendChild(content)
  return new XMLSerializer().serializeToString(doc)
}
