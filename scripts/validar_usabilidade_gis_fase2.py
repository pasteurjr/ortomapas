"""Real UI drawing, elevation profile, exports and aligned terrain products."""
import json
from pathlib import Path
import numpy as np
import rasterio
from pyproj import Transformer
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/validacao/usabilidade_gis_fase2_2026-10-11'


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    result={'accepted':False,'screens':[],'errors':[]}
    output=OUT/'resultado.json';output.write_text(json.dumps(result))
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True)
        page=browser.new_page(viewport={'width':1440,'height':900})
        page.set_default_timeout(60000)
        page.on('pageerror',lambda e:(result['errors'].append(str(e)),print('JS ERROR',e.stack,flush=True)))
        profiles=[];differences=[]
        def response(r):
            if '/agents/tools/execute' in r.url and r.status==200:
                data=r.json().get('dados',{})
                if 'distancias_m' in data:profiles.append(data)
            if '/elevacao-diferenca?' in r.url and r.status==200:differences.append(r.json())
        page.on('response',response)
        page.goto('http://127.0.0.1:5302',wait_until='networkidle')
        page.locator('input[type=email]').fill('phase1-1791391595@example.test')
        page.locator('input[type=password]').fill('fase1-senha-segura')
        page.get_by_role('button',name='Entrar',exact=True).click()
        page.locator('.project-selector').click();page.get_by_role('option',name='Teste PostgreSQL UI',exact=True).click()
        page.locator('.ortomapa-card').filter(has_text='ODM ortomosaico f7563d3d').get_by_title('Visibilidade',exact=True).click()
        page.wait_for_function("""() => { const tiles=[...document.querySelectorAll('.leaflet-tile-pane img')].filter(i=>i.src.includes('/api/ortomapas/')); return tiles.length>0 && tiles.every(i=>i.complete && i.naturalWidth===256 && getComputedStyle(i).opacity==='1') }""")
        def settle():page.evaluate('()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))')
        def capture(name):
            settle();page.screenshot(path=str(OUT/(name+'.png')));result['screens'].append(name+'.png')
        capture('01_contexto_ortofoto')
        page.locator('.workspace-subnav').get_by_text('Perfil altimetrico',exact=True).click()
        page.locator('.elevation-profile select').select_option('5')
        page.get_by_title('Desenhar linha de perfil',exact=True).click();settle()
        print('Modo de desenho ativado',flush=True)
        box=page.locator('.leaflet-container').bounding_box()
        clicks=[(box['x']+box['width']*x,box['y']+box['height']*y) for x,y in ((.35,.5),(.5,.48),(.65,.5))]
        for x,y in clicks:
            page.mouse.click(x,y)
            # Leaflet Draw debounces vertex clicks; simulate separate human inputs.
            page.wait_for_timeout(300)
        page.get_by_title('Concluir linha de perfil',exact=True).click()
        page.screenshot(path=str(OUT/'diagnostico_linha.png'))
        print('Linha desenhada, aguardando perfil',flush=True)
        page.locator('.profile-chart').wait_for();assert profiles
        profile=profiles[-1]
        assert profile['geometry']['type']=='LineString'
        assert profile['pontos']==200 and profile['comprimento_m']>0
        assert sum(v is not None for v in profile['elevacoes'])>50
        with rasterio.open(ROOT/'data/ortomapas/odm_2_dsm.tif') as ds:
            xy=Transformer.from_crs(4326,ds.crs,always_xy=True).transform(*np.array(profile['coordinates_wgs84']).T)
            expected=[None if np.ma.is_masked(v[0]) else float(v[0]) for v in ds.sample(zip(*xy),indexes=1,masked=True)]
        assert all((a is None and b is None) or (a is not None and b is not None and abs(a-b)<1e-6) for a,b in zip(expected,profile['elevacoes']))
        assert 'L' in page.locator('.profile-chart path').get_attribute('d')
        capture('02_linha_e_perfil_dsm_real')
        chart=page.locator('.profile-chart').bounding_box();page.mouse.move(chart['x']+chart['width']*.55,chart['y']+chart['height']*.5)
        assert page.locator('.profile-chart line[stroke="#ffd85c"]').count()==1
        capture('03_inspecao_grafico')
        with page.expect_download() as d:page.get_by_title('Exportar perfil CSV',exact=True).click()
        d.value.save_as('/tmp/perfil_gis_fase2.csv')
        rows=Path('/tmp/perfil_gis_fase2.csv').read_text().splitlines()
        assert len(rows)==201
        with page.expect_response(lambda r:'/agents/tools/execute' in r.url and r.status==200 and r.request.post_data_json.get('arguments',{}).get('produto_id')==6) as returned:
            page.locator('.elevation-profile select').select_option('6')
        dtm=returned.value.json()['dados'];page.locator('.profile-chart').wait_for()
        assert dtm['comprimento_m']==profile['comprimento_m'] and dtm['pontos']==200
        with rasterio.open(ROOT/'data/ortomapas/odm_2_dtm.tif') as ds:
            xy=Transformer.from_crs(4326,ds.crs,always_xy=True).transform(*np.array(dtm['coordinates_wgs84']).T)
            expected=[None if np.ma.is_masked(v[0]) else float(v[0]) for v in ds.sample(zip(*xy),indexes=1,masked=True)]
        assert all((a is None and b is None) or (a is not None and b is not None and abs(a-b)<1e-6) for a,b in zip(expected,dtm['elevacoes']))
        capture('09_perfil_dtm_mesma_linha')
        page.locator('.elevation-profile select').select_option('5')
        page.wait_for_function("!document.querySelector('.elevation-profile [role=status]') && document.querySelector('.profile-chart')")
        page.get_by_title('Desenhar linha de perfil',exact=True).click()
        page.get_by_title('Cancelar linha de perfil',exact=True).click()
        assert page.get_by_title('Desenhar linha de perfil').get_attribute('aria-pressed')=='false'
        assert page.locator('.profile-chart').count()==1
        page.set_viewport_size({'width':1024,'height':768});settle()
        page.wait_for_function("document.querySelector('.sidebar-right').getBoundingClientRect().width < 40")
        page.evaluate('()=>document.fonts.ready')
        map_box=page.locator('.leaflet-container').bounding_box();panel=page.locator('.elevation-profile').bounding_box()
        assert map_box['y']+map_box['height']<=panel['y']+1
        capture('04_perfil_tablet')
        page.set_viewport_size({'width':1440,'height':900});page.get_by_title('Fechar perfil',exact=True).click()
        page.locator('.workspace-sidebar-nav').get_by_text('Copiloto',exact=True).click()
        page.wait_for_function("document.querySelector('.sidebar-right').getBoundingClientRect().width < 40")
        assert page.locator('.leaflet-tile-pane img[src*="/api/ortomapas/"]').count()>0
        capture('05_copiloto_preserva_ortofoto')
        page.get_by_title('Recolher navegacao',exact=True).focus();page.keyboard.press('Enter')
        page.wait_for_function("document.querySelector('.sidebar-left').getBoundingClientRect().width < 60")
        assert page.locator('.workspace-nav-item[title="Voos e ODM"]').count()==1
        capture('10_navegacao_icones_teclado')
        page.get_by_title('Expandir navegacao',exact=True).click()
        page.wait_for_function("document.querySelector('.sidebar-left').getBoundingClientRect().width > 280")
        page.locator('.workspace-sidebar-nav').get_by_text('Voos e ODM',exact=True).click()
        task=page.locator('.task-row').filter(has_text='f7563d3d')
        task.get_by_role('button',name='DSM 3D',exact=True).click()
        page.wait_for_function("document.querySelector('.surface-view footer')?.textContent.includes('triangulos') && !document.querySelector('.surface-view .overlay')")
        capture('06_terreno_1x')
        page.get_by_label('Exagero vertical do terreno',exact=True).fill('3');capture('07_terreno_3x')
        assert 'Vertical 3x' in page.locator('.surface-view footer').inner_text()
        page.get_by_title('Fechar',exact=True).click()
        task.get_by_role('button',name='Diferença',exact=True).click()
        page.locator('.diff-view footer').wait_for();assert differences
        diff=differences[-1]
        assert diff['valid_pixels']>0
        assert page.locator('.diff-view canvas').evaluate('c=>Array.from(c.getContext("2d").getImageData(0,0,c.width,c.height).data).filter((v,i)=>i%4===3&&v>0).length')==diff['valid_pixels']
        capture('08_diferenca_alinhada_real')
        result['profile']={'length_m':profile['comprimento_m'],'samples':profile['pontos'],'valid_samples':sum(v is not None for v in profile['elevacoes']),'min':min(v for v in profile['elevacoes'] if v is not None),'max':max(v for v in profile['elevacoes'] if v is not None),'independent_raster_samples_match':True,'csv_rows':200,'geometry':profile['geometry']}
        result['dtm_profile']={'valid_samples':sum(v is not None for v in dtm['elevacoes']),'min':min(v for v in dtm['elevacoes'] if v is not None),'max':max(v for v in dtm['elevacoes'] if v is not None)}
        result['difference']={k:v for k,v in diff.items() if k!='differences'}
        assert not result['errors'],result['errors'];browser.close()
    result['accepted']=True;output.write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))


if __name__=='__main__':main()
