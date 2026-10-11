import assert from 'node:assert/strict'
import { cloudTransform, cloudPosition, sourceDistance } from '../src/utils/cloudGeometry.js'

const a = [500000, 8600000, 100]
const b = [500003, 8600004, 112]
const transform = cloudTransform({ min: a, max: b })
assert.equal(sourceDistance(a, b), 13)
const x = cloudPosition(a, transform)
const y = cloudPosition(b, transform)
assert.ok(Math.abs(sourceDistance(x, y) / transform.scale - 13) < 1e-10)
assert.ok(y[2] < x[2], 'North must be negative scene Z')
assert.equal(sourceDistance(a, b), 13, 'Distance remains in original metric coordinates')
const exaggerated = cloudPosition(b, transform, 3)
assert.equal(exaggerated[1], y[1]*3)
assert.equal(exaggerated[0], y[0])
assert.equal(exaggerated[2], y[2])
assert.equal(sourceDistance(a,b),13, 'Visual exaggeration must not change physical measurement')
console.log('Cloud metric geometry: passed')
