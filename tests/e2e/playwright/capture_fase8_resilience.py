"""Fase 8 resilience checks; no LLM calls and no persistent valid data."""
import json, os, sys
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from backend.config import ORTOMAPAS_DIR
from backend.database.connection import get_connection
OUT=ROOT/'docs/validacao/ortomapas_conclusao/etapa-08'
FRONT=os.getenv('FRONTEND_URL','http://127.0.0.1:5176').rstrip('/')
API=os.getenv('API_URL','http://127.0.0.1:8888/api').rstrip('/')
EMAIL=os.getenv('E2E_EMAIL','phase1-1791391595@example.test')
PASSWORD=os.getenv('E2E_PASSWORD','fase1-senha-segura')
PROJECT='Guarajuba - Condomínio Paraíso (Demonstração)'
def count_rows(project_id):
    with get_connection() as conn:
        cur=conn.cursor();cur.execute('SELECT count(*) FROM ortomapas WHERE projeto_id=%s',(project_id,));return cur.fetchone()[0]
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    result={'started_at':datetime.now().astimezone().isoformat(),'checks':[],'llm_calls':0,'cleanup':{}}
    js_errors=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,executable_path='/usr/bin/google-chrome')
        context=browser.new_context(viewport={'width':1600,'height':1000})
        page=context.new_page();page.on('pageerror',lambda e:js_errors.append(str(e)));page.set_default_timeout(20000)
        page.goto(FRONT,wait_until='networkidle')
        page.screenshot(path=str(OUT/'f8_01_login.png'))
        page.locator('input[type=email]').fill(EMAIL);page.locator('input[type=password]').fill(PASSWORD)
        page.get_by_role('button',name='Entrar').click();page.get_by_text('Sistema de Ortomapas',exact=True).wait_for()
        token=page.evaluate("localStorage.getItem('ortomapas_token')")
        projects=page.request.get(f'{API}/projetos',headers={'Authorization':f'Bearer {token}'})
        assert projects.status==200,projects.text()
        project_list=projects.json().get('projetos',[]) if isinstance(projects.json(),dict) else projects.json()
        project=next(x for x in project_list if x['nome']==PROJECT)
        project_id=int(project['id'])
        page.get_by_text(PROJECT,exact=True).click();page.locator('.leaflet-container').wait_for()
        page.screenshot(path=str(OUT/'f8_02_projeto_operacional.png'))
        result['checks'].append({'id':'F8-01','expected':'login, sessão válida e mapa carregado','obtained':'HTTP 200 em /projetos; projeto selecionado e mapa renderizado','status':'passed','screenshot':'f8_02_projeto_operacional.png'})
        bad=page.request.get(f'{API}/auth/me',headers={'Authorization':'Bearer expired.invalid.token'})
        assert bad.status==401,bad.status
        result['checks'].append({'id':'F8-02','expected':'token inválido recebe 401','obtained':f'HTTP {bad.status}; API não autorizou a sessão inválida','status':'passed'})
        api_files_before=set(Path(ORTOMAPAS_DIR).glob('*')) if Path(ORTOMAPAS_DIR).exists() else set()
        rows_before=count_rows(project_id)
        rejected=page.request.post(f'{API}/ortomapas/upload?projeto_id={project_id}',headers={'Authorization':f'Bearer {token}'},multipart={'file':{'name':'f8_invalido.tif','mimeType':'image/tiff','buffer':b'nao e um GeoTIFF'}})
        assert rejected.status==400,(rejected.status,rejected.text())
        rows_after=count_rows(project_id)
        files_after=set(Path(ORTOMAPAS_DIR).glob('*')) if Path(ORTOMAPAS_DIR).exists() else set()
        assert rows_before==rows_after,(rows_before,rows_after)
        assert api_files_before==files_after,'Upload inválido deixou arquivo órfão'
        result['checks'].append({'id':'F8-03','expected':'upload corrompido rejeitado e sem registro/arquivo residual','obtained':f'HTTP {rejected.status}; registros {rows_before}->{rows_after}; arquivos órfãos 0','status':'passed'})
        failures=[]
        def unavailable(route):
            failures.append(route.request.url);route.fulfill(status=503,content_type='application/json',body='{"detail":"falha simulada de API"}')
        context.route('**/api/projetos',unavailable)
        page.reload(wait_until='domcontentloaded');page.wait_for_timeout(700)
        page.screenshot(path=str(OUT/'f8_03_api_indisponivel.png'))
        assert failures,'Interceptor não atingiu requisição da API'
        assert page.get_by_role('alert').filter(has_text='Não foi possível carregar os projetos').is_visible(), 'A indisponibilidade foi confundida com lista vazia ou não foi informada'
        context.unroute('**/api/projetos',unavailable)
        page.get_by_role('button',name='Tentar novamente').click();page.get_by_text(PROJECT,exact=True).wait_for(timeout=15000)
        page.screenshot(path=str(OUT/'f8_04_recuperacao_api.png'))
        result['checks'].append({'id':'F8-04','expected':'503 aparece como erro acionável; retry recupera projetos sem recarregar página','obtained':f'{len(failures)} chamada(s) receberam 503 simulado; alerta explícito e retry carregou o projeto','status':'passed','screenshots':['f8_03_api_indisponivel.png','f8_04_recuperacao_api.png']})
        # Exercise real 401 in the UI and observe whether authentication is reset.
        page.evaluate("localStorage.setItem('ortomapas_token','expired.invalid.token')")
        page.reload(wait_until='networkidle');page.wait_for_timeout(700)
        page.wait_for_function("() => document.querySelector('input[type=email]') !== null", timeout=10000)
        page.screenshot(path=str(OUT/'f8_05_sessao_expirada.png'))
        login_visible=page.locator('input[type=email]').count()>0
        token_retained=bool(page.evaluate("localStorage.getItem('ortomapas_token')"))
        assert login_visible and not token_retained, {'login_visible':login_visible,'token_retained':token_retained}
        assert page.get_by_role('alert').filter(has_text='Sua sessão expirou').is_visible(), 'A tela não informou que a sessão expirou'
        result['expired_token_ui']={'login_visible':login_visible,'token_retained':token_retained,'screenshot':'f8_05_sessao_expirada.png','status':'passed'}
        result['page_errors']=js_errors
        browser.close()
    result['finished_at']=datetime.now().astimezone().isoformat()
    (OUT/'fase8_result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
