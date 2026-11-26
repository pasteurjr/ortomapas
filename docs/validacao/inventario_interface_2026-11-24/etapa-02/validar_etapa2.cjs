#!/usr/bin/env node
// UI-only deletion validation. Every API response is a browser fixture; no
// backend or database is contacted. Set PLAYWRIGHT_MODULE if Playwright is not
// installed in this repository's Node resolution path.
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright')
const path = require('node:path')

const BASE_URL = process.env.ORTOMAPAS_URL || 'http://127.0.0.1:5176'
const OUT = __dirname
const ORTHO = {
  id: 955,
  nome: 'ORTO TESTE DESCARTAVEL 26-11',
  projeto_id: 88,
  tipo: 'RGB',
  formato: 'GeoTIFF',
  caminho_arquivo: 'fixture-only/not-a-real-file.tif',
  status: 'concluido',
}

async function waitForMap(page) {
  await page.waitForFunction(() => {
    const tiles = [...(document.querySelector('.map-container')?.querySelectorAll('.leaflet-tile') || [])]
    return tiles.length >= 12 && tiles.filter(tile => tile.complete && tile.naturalWidth > 0).length >= 12
  }, { timeout: 20000 })
}

async function createScenario(browser, canEdit) {
  const context = await browser.newContext({ viewport: { width: 1600, height: 1000 } })
  await context.addInitScript("localStorage.setItem('ortomapas_token', 'fixture-token')")
  const page = await context.newPage()
  let present = true
  let deleteCalls = 0

  await page.route(`${BASE_URL}/api/**`, async route => {
    const request = route.request()
    const endpoint = new URL(request.url()).pathname.replace('/api', '')
    let status = 200
    let body = {}
    const project = {
      id: 88,
      nome: 'Projeto UI descartavel',
      status: 'ativo',
      pode_editar: canEdit,
      bbox_norte: -12,
      bbox_sul: -12.1,
      bbox_leste: -38,
      bbox_oeste: -38.1,
    }

    if (endpoint === '/auth/me') body = { id: 60, email: 'fixture@example.invalid', nome: 'Teste', perfil: 'admin', ativo: true }
    else if (endpoint === '/projetos') body = { total: 1, projetos: [project] }
    else if (endpoint === '/projetos/88') body = project
    else if (endpoint === '/ortomapas' && request.method() === 'GET') body = { total: present ? 1 : 0, ortomapas: present ? [ORTHO] : [] }
    else if (endpoint === '/ortomapas/955' && request.method() === 'DELETE') {
      deleteCalls += 1
      if (deleteCalls === 1) {
        status = 500
        body = { detail: 'Falha simulada de serviço' }
      } else {
        present = false
        body = { message: 'Ortomapa deletado com sucesso', id: ORTHO.id }
      }
    } else if (endpoint === '/analises') body = { total: 0, analises: [] }
    else if (endpoint === '/anotacoes') body = { total: 0, anotacoes: [] }
    else if (endpoint === '/voos' || endpoint === '/missoes-captura') body = { total: 0, voos: [], missoes: [] }
    else if (endpoint === '/copilot/threads') body = { conversas: [] }
    else if (endpoint === '/agents/layers') body = { camadas: [] }
    else if (endpoint === '/copilot/memories') body = { memorias: [] }
    else if (endpoint === '/odm/produtos') body = { total: 0, produtos: [] }

    await route.fulfill({ status, contentType: 'application/json', body: JSON.stringify(body) })
  })

  await page.goto(BASE_URL)
  await page.locator('.app-layout').waitFor()
  await page.getByRole('combobox').first().click()
  await page.getByRole('option', { name: 'Projeto UI descartavel' }).click()
  await page.locator('.ortomapa-card').waitFor()
  await waitForMap(page)
  return { context, page, getDeleteCalls: () => deleteCalls }
}

async function main() {
  const browser = await chromium.launch({ headless: true, executablePath: process.env.CHROME_EXECUTABLE || '/usr/bin/google-chrome', args: ['--no-sandbox'] })
  const results = []
  try {
    const editable = await createScenario(browser, true)
    const page = editable.page
    const card = page.locator('.ortomapa-card')
    const deleteButton = card.getByRole('button', { name: `Remover ${ORTHO.nome} do catálogo` })

    await deleteButton.click()
    const dialog = page.locator('.p-dialog')
    await dialog.waitFor()
    await dialog.getByText('arquivo raster será mantido').waitFor()
    await page.screenshot({ path: path.join(OUT, '01_confirmacao.png'), fullPage: true })
    results.push({ check: 'Confirmação identifica o produto e explica que o raster fica preservado', result: 'PASS' })

    await dialog.getByRole('button', { name: 'Cancelar' }).click()
    if (await card.count() !== 1 || editable.getDeleteCalls() !== 0) throw new Error('Cancelar alterou o item ou enviou DELETE')
    results.push({ check: 'Cancelar mantém o item e não chama a API', result: 'PASS' })

    await deleteButton.click()
    await page.locator('.p-dialog').getByRole('button', { name: 'Remover do catálogo' }).click()
    await page.getByRole('alert').waitFor()
    if (await card.count() !== 1) throw new Error('Falha HTTP removeu o item localmente')
    await page.screenshot({ path: path.join(OUT, '02_erro_preserva_item.png'), fullPage: true })
    results.push({ check: 'Erro de API mostra mensagem e conserva o produto', result: 'PASS' })

    await page.locator('.p-dialog').getByRole('button', { name: 'Remover do catálogo' }).click()
    await page.getByText(/removido do catálogo; o arquivo raster foi mantido/).waitFor()
    await page.locator('.p-dialog').waitFor({ state: 'hidden' })
    if (await page.locator('.ortomapa-card').count() !== 0 || editable.getDeleteCalls() !== 2) throw new Error('Confirmação não atualizou o catálogo')
    await page.screenshot({ path: path.join(OUT, '03_remocao_confirmada.png'), fullPage: true })
    results.push({ check: 'Sucesso remove card/camada da interface e informa retenção do raster', result: 'PASS' })

    await page.reload()
    await page.locator('.app-layout').waitFor()
    await page.getByRole('combobox').first().click()
    await page.getByRole('option', { name: 'Projeto UI descartavel' }).click()
    await page.getByText('Nenhum ortomapa carregado').waitFor()
    await page.screenshot({ path: path.join(OUT, '04_apos_recarregar.png'), fullPage: true })
    results.push({ check: 'Após recarga, o registro removido não volta ao catálogo', result: 'PASS' })

    const readOnly = await createScenario(browser, false)
    if (await readOnly.page.locator('.ortomapa-card button[aria-label^="Remover"]').count() !== 0) throw new Error('Ação de remoção visível sem permissão de edição')
    await readOnly.page.screenshot({ path: path.join(OUT, '05_sem_permissao.png'), fullPage: true })
    results.push({ check: 'Usuário sem permissão de edição não vê controle de remoção', result: 'PASS' })

    const output = { result: 'PASS', api_mode: 'browser fixtures only; no backend or database writes', delete_calls: editable.getDeleteCalls(), checks: results }
    require('node:fs').writeFileSync(path.join(OUT, 'resultado.json'), JSON.stringify(output, null, 2) + '\n')
    console.log(JSON.stringify(output, null, 2))
    await editable.context.close()
    await readOnly.context.close()
  } finally {
    await browser.close()
  }
}

main().catch(error => { console.error(error); process.exit(1) })
