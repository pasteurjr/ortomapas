export function cloudTransform (bounds) {
  const origin = bounds.min.map((value, i) => (value + bounds.max[i]) / 2)
  const scale = 10 / Math.max(...bounds.max.map((value, i) => value - bounds.min[i]), 1e-9)
  return { origin, scale }
}

export function cloudPosition (point, transform) {
  const { origin, scale } = transform
  return [(point[0] - origin[0]) * scale, (point[2] - origin[2]) * scale, -(point[1] - origin[1]) * scale]
}

export function sourceDistance (a, b) {
  return Math.hypot(...a.map((value, i) => value - b[i]))
}
