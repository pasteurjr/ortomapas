#!/usr/bin/env node
// UI integration proof for the mission planner's project/mission map extent.
// API is stubbed in-browser. Geographic limits originate from a local real DSM.
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright')
const path = require('node:path')

const BASE = process.env.ORTOMAPAS_URL || 'http://127.0.0.1:5176'
const OUT = __dirname
const DSM = { west: -81.75440181730262, south: 41.302851160113434, east: -81.74992313476743, north: 41.30554043878053 }
const AOI = { west: -81.75379922754675, south: 41.30482632770099, east: -81.75349079947462, north: 41.30505888564006 }
const CENTER = { lat: (DSM.south + DSM.north) / 2, lon: (DSM.west + DSM.east) / 2 }
const projects = [
  { id: 901, nome: 'Aukerman — extensão do ortomapa', pode_editar: true },
  { id: 902, nome: 'Aukerman — limites cadastrados', pode_editar: true, bbox_oeste: DSM.west, bbox_sul: DSM.south, bbox_leste: DSM.east, bbox_norte: DSM.north },
  { id: 903, nome: 'Projeto sem extensão espacial', pode_editar: true },
  { id: 904, nome: 'Projeto com centro cadastrado', pode_editar: true, centro_lat: CENTER.lat, centro_lon: CENTER.lon },
  { id: 905, nome: 'Projeto com bbox inválido', pode_editar: true, bbox_sul: -5, bbox_norte: 95, bbox_oeste: 19, bbox_leste: 21, centro_lat: CENTER.lat, centro_lon: CENTER.lon },
]
const mission = {
  id: 701, nome: 'Missão Aukerman — AOI salva', camera_perfil: { formato: 'JPEG' },
  parametros: { gsd_cm_px: 1.5, altitude_m: 50, overlap_frontal: 0.8, overlap_lateral: 0.7, velocidade_ms: 4, gimbal_graus: -90 },
  areas: [{ tipo: 'aoi', geometria: { type: 'Polygon', coordinates: [[[AOI.west, AOI.south], [AOI.east, AOI.south], [AOI.east, AOI.north], [AOI.west, AOI.north], [AOI.west, AOI.south]]] } }],
  takeoff: { lat: AOI.south + 0.00003, lon: AOI.west + 0.00003 }, waypoints: [], canonical: {},
}

function expect(condition, message) { if (!condition) throw new Error(message) }
function contains(outer, inner, eps = 1e-6) {
  const [south, west, north, east] = outer
  return south <= inner.south + eps && west <= inner.west + eps && north >= inner.north - eps && east >= inner.east - eps
}

async function createPage(browser) {
  const context = await browser.newContext({ viewport: { width: 1600, height: 1000 }, deviceScaleFactor: 1 })
  await context.addInitScript("localStorage.setItem('ortomapas_token','fixture-token')")
  const page = await context.newPage()
  await page.route(`${BASE}/api/**`, async route => {
    const req = route.request(), url = new URL(req.url()), endpoint = url.pathname.replace('/api', '')
    const id = Number(endpoint.match(/^\/projetos\/(\d+)$/)?.[1])
    let body = {}, status = 200
    if (endpoint === '/auth/me') body = { id: 60, email: 'fixture@example.invalid', nome: 'Validação visual', perfil: 'admin', ativo: true }
    else if (endpoint === '/projetos') body = { projetos: projects }
    else if (id && projects.some(p => p.id === id)) body = projects.find(p => p.id === id)
    else if (endpoint === '/ortomapas') {
      const projectId = Number(url.searchParams.get('projeto_id'))
      body = { ortomapas: projectId === 901 ? [{ id: 9901, projeto_id: 901, nome: 'DSM Aukerman (metadados reais)', bbox_oeste: DSM.west, bbox_sul: DSM.south, bbox_leste: DSM.east, bbox_norte: DSM.north }] : [] }
    } else if (endpoint === '/analises') body = { analises: [] }
    else if (endpoint === '/anotacoes') body = { anotacoes: [] }
    else if (endpoint === '/missoes-captura') body = { missoes: [{ id: mission.id, nome: mission.nome, versao: 1 }] }
    else if (endpoint === '/missoes-captura/701') body = mission
    else if (endpoint === '/voos') body = { voos: [] }
    else if (endpoint === '/copilot/threads') body = { conversas: [] }
    else if (endpoint === '/copilot/memories') body = { memorias: [] }
    else if (endpoint === '/agents/layers') body = { camadas: [] }
    else if (endpoint === '/odm/produtos') body = { produtos: [] }
    await route.fulfill({ status, contentType: 'application/json', body: JSON.stringify(body) })
  })
  await page.goto(BASE)
  await page.locator('.app-layout').waitFor({ timeout: 15000 })
  await page.locator('.project-selector').click()
  await page.getByRole('option', { name: projects[0].nome }).click()
  await page.getByRole('button', { name: 'Planejar missao' }).click()
  await page.locator('[data-testid="mission-map"]').waitFor()
  await page.waitForFunction(() => {
    const m = document.querySelector('[data-testid="mission-map"]')
    return m?.dataset.viewContext && m.dataset.viewContext !== 'loading' && m.dataset.viewBounds
  }, { timeout: 15000 })
  return { context, page }
}

async function chooseProject(page, project) {
  await page.getByRole('button', { name: 'Fechar planejador' }).click()
  await page.locator('.project-selector').click()
  await page.getByRole('option', { name: project.nome }).click()
  await page.getByRole('button', { name: 'Planejar missao' }).click()
  await page.waitForFunction(() => {
    const m = document.querySelector('[data-testid="mission-map"]')
    return m?.dataset.viewContext && m.dataset.viewContext !== 'loading' && m.dataset.viewBounds
  }, { timeout: 15000 })
}

async function captureAndRead(page, name) {
  const notice = page.locator('.map-notice')
  if (await notice.count()) await notice.waitFor({ state: 'hidden', timeout: 5000 }).catch(() => {})
  await page.waitForFunction(() => {
    const tiles = [...(document.querySelector('[data-testid="mission-map"]')?.querySelectorAll('.leaflet-tile') || [])]
    return tiles.length >= 8 && tiles.filter(tile => tile.complete && tile.naturalWidth > 0).length >= 8
  }, { timeout: 20000 })
  await page.waitForTimeout(1200)
  const map = page.locator('[data-testid="mission-map"]')
  const data = await map.evaluate(el => ({
    context: el.dataset.viewContext,
    bounds: JSON.parse(el.dataset.viewBounds || 'null'),
  }))
  const contextLabel = await page.getByTestId('mission-map-context').innerText()
  await page.screenshot({ path: path.join(OUT, name), fullPage: true })
  return { ...data, contextLabel }
}

async function main() {
  const browser = await chromium.launch({ headless: true, executablePath: process.env.CHROME_EXECUTABLE || '/usr/bin/google-chrome', args: ['--no-sandbox'] })
  const assertions = []
  try {
    const { context, page } = await createPage(browser)
    let result = await captureAndRead(page, '01_aukerman_extent_ortomapa.png')
    expect(result.context === 'project-ortomapa', `esperado project-ortomapa, obtido ${result.context}`)
    expect(contains(result.bounds, DSM), `extent mostrado ${result.bounds} não contém bounds reais do DSM ${JSON.stringify(DSM)}`)
    assertions.push({ caso: 'extensão do DSM real do projeto', status: 'aprovado', contexto: result.context, bounds_exibidos: result.bounds, bounds_reais: DSM, rótulo: result.contextLabel })

    await chooseProject(page, projects[1])
    result = await captureAndRead(page, '02_aukerman_limites_projeto.png')
    expect(result.context === 'project-bounds', `esperado project-bounds, obtido ${result.context}`)
    expect(contains(result.bounds, DSM), 'limites do projeto não estão enquadrados')
    assertions.push({ caso: 'prioridade dos limites cadastrados no projeto', status: 'aprovado', contexto: result.context, bounds_exibidos: result.bounds })

    await chooseProject(page, projects[2])
    result = await captureAndRead(page, '03_projeto_sem_extensao.png')
    expect(result.context === 'world', `esperado world no projeto sem extent, obtido ${result.context}`)
    expect(result.contextLabel.includes('sem extensão espacial'), `aviso de ausência de extensão não está visível: ${result.contextLabel}`)
    expect(Math.abs((result.bounds[0] + result.bounds[2]) / 2) < 5 && Math.abs((result.bounds[1] + result.bounds[3]) / 2) < 5, `fallback global incorreto: ${result.bounds}`)
    assertions.push({ caso: 'projeto sem extent e centro', status: 'aprovado', contexto: result.context, bounds_exibidos: result.bounds, mensagem: result.contextLabel })

    await chooseProject(page, projects[3])
    result = await captureAndRead(page, '04_projeto_centro_cadastrado.png')
    expect(result.context === 'project-center', `esperado project-center, obtido ${result.context}`)
    expect(Math.abs((result.bounds[0] + result.bounds[2]) / 2 - CENTER.lat) < 0.2 && Math.abs((result.bounds[1] + result.bounds[3]) / 2 - CENTER.lon) < 0.2, `mapa não está centrado no ponto do projeto: ${result.bounds}`)
    assertions.push({ caso: 'fallback pelo centro cadastrado', status: 'aprovado', contexto: result.context, bounds_exibidos: result.bounds, centro_de_referencia: CENTER })

    await chooseProject(page, projects[4])
    result = await captureAndRead(page, '05_bbox_invalido_descartado.png')
    expect(result.context === 'project-center', `bbox fora de faixa deveria ser ignorado; contexto ${result.context}`)
    assertions.push({ caso: 'bbox fora da faixa geográfica rejeitado', status: 'aprovado', contexto: result.context, bounds_exibidos: result.bounds })

    await chooseProject(page, projects[0])
    await page.getByRole('combobox', { name: 'Abrir missao existente' }).selectOption(String(mission.id))
    await page.getByTestId('mission-map-context').filter({ hasText: 'AOI salva na missão' }).waitFor()
    await page.waitForFunction(() => document.querySelector('[data-testid="mission-map"]')?.dataset.viewContext === 'mission-aoi')
    result = await captureAndRead(page, '06_missao_salva_aoi.png')
    expect(result.context === 'mission-aoi', `esperado mission-aoi, obtido ${result.context}`)
    expect(contains(result.bounds, AOI, 1e-7), `AOI da missão não está enquadrada: ${result.bounds}`)
    assertions.push({ caso: 'reabertura de missão e enquadramento de sua AOI', status: 'aprovado', contexto: result.context, bounds_exibidos: result.bounds, bounds_aoi: AOI })
    await context.close()

    require('node:fs').writeFileSync(path.join(OUT, 'resultado.json'), JSON.stringify({ etapa: '3/6', total: assertions.length, aprovados: assertions.length, reprovados: 0, assertions }, null, 2) + '\n')
    console.log(JSON.stringify({ total: assertions.length, aprovados: assertions.length, reprovados: 0, assertions }, null, 2))
  } finally { await browser.close() }
}

main().catch(error => { console.error(error); process.exit(1) })
