"""Exercise real HTTP project isolation, media scope and GeoTIFF upload on PostgreSQL."""
import io
import json
from pathlib import Path

import numpy as np
import rasterio
import requests
from rasterio.io import MemoryFile
from rasterio.transform import from_origin

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/validacao/mapa_fase1_2026-10-10"
API = "http://127.0.0.1:5018/api"


def session(email, password):
    client = requests.Session()
    result = client.post(API + "/auth/login", json={"email": email, "senha": password})
    result.raise_for_status()
    client.headers["Authorization"] = "Bearer " + result.json()["access_token"]
    return client


def main():
    result = {"accepted": False, "checks": []}
    OUT.mkdir(parents=True, exist_ok=True)
    output = OUT / "seguranca_http.json"
    output.write_text(json.dumps(result))
    owner = session("phase1-1791391595@example.test", "fase1-senha-segura")
    email, password = "fase1-outsider@example.test", "validacao-fase1-outsider"
    response = requests.post(API + "/auth/register", json={"email": email, "nome": "Validacao isolamento", "senha": password})
    assert response.status_code in {201, 409}
    outsider = session(email, password)
    anonymous = requests.Session()
    def check(name, response, expected):
        actual = response.status_code
        result["checks"].append({"name": name, "expected": expected, "actual": actual, "accepted": actual == expected})
        assert actual == expected, (name, response.text[:400])
    target = "/ortomapas/30"
    check("metadados sem login", anonymous.get(API + target), 401)
    check("metadados de outro projeto", outsider.get(API + target), 403)
    check("lista de outro projeto", outsider.get(API + "/ortomapas", params={"projeto_id": 62}), 403)
    check("metadados do proprietario", owner.get(API + target), 200)
    check("tile sem login", anonymous.get(API + target + "/tile/17/35770/48995.png"), 401)
    check("tile de outro projeto", outsider.get(API + target + "/tile/17/35770/48995.png"), 403)
    access = owner.get(API + target + "/tile-access"); access.raise_for_status()
    url = access.json()["url"].replace("{z}", "17").replace("{x}", "35770").replace("{y}", "48995")
    ticket = url.split("ticket=", 1)[1]
    check("tile com ticket restrito", anonymous.get("http://127.0.0.1:5018" + url), 200)
    check("ticket usado em outro produto", anonymous.get(API + "/ortomapas/2/tile/17/35770/48995.png", params={"ticket": ticket}), 401)
    check("ticket usado como token geral", requests.get(API + "/auth/me", headers={"Authorization": "Bearer " + ticket}), 401)
    check("arquivo estatico sem login", anonymous.get("http://127.0.0.1:5018/data/ortomapas/odm_2_ortomosaico.tif"), 401)
    check("arquivo de outro projeto", outsider.get("http://127.0.0.1:5018/data/ortomapas/odm_2_ortomosaico.tif"), 403)
    check("estatisticas sem login", anonymous.post(API + "/tools/statistics", json={"input_path": "ortomapas/odm_2_ortomosaico.tif"}), 401)
    check("estatisticas de outro projeto", outsider.post(API + "/tools/statistics", json={"input_path": "ortomapas/odm_2_ortomosaico.tif"}), 403)
    check("cadastro publico de admin bloqueado", anonymous.post(API + "/auth/register", json={"email": "forbidden@example.test", "nome": "Teste", "senha": password, "perfil": "admin"}), 403)
    check("metadados sem voo", owner.post(API + "/ortomapas", json={"projeto_id": 62, "nome": "Sem voo"}), 400)
    other_projects = outsider.get(API + "/projetos").json()["projetos"]
    project = next((p for p in other_projects if p["nome"] == "Validacao isolamento - projeto B"), None)
    if project is None:
        response = outsider.post(API + "/projetos", json={"nome": "Validacao isolamento - projeto B"}); response.raise_for_status(); project = response.json()
    flight = outsider.post(API + "/voos", json={"projeto_id": project["id"], "data_voo": "2026-10-10"}); flight.raise_for_status()
    fid = flight.json()["id"]
    check("voo de outro projeto recusado", owner.post(API + "/ortomapas", json={"projeto_id": 62, "voo_id": fid, "nome": "Voo incorreto"}), 400)
    with MemoryFile() as memory:
        with memory.open(driver="GTiff", width=64, height=64, count=3, dtype="uint8", crs="EPSG:32617", transform=from_origin(436850, 4572900, .05, .05)) as ds:
            ds.write(np.full((3, 64, 64), 125, dtype=np.uint8))
        blob = memory.read()
    upload = outsider.post(API + "/ortomapas/upload", params={"projeto_id": project["id"], "voo_id": fid, "nome": "Fixture sintetica de contrato HTTP"}, files={"file": ("contrato_http.tif", blob, "image/tiff")})
    check("upload GeoTIFF com projeto e voo", upload, 201)
    product = upload.json()["ortomapa"]
    assert product["id"] and abs(product["resolucao_cm"] - 5) < .001
    result["upload"] = {"id": product["id"], "project_id": product["projeto_id"], "resolution_cm": product["resolucao_cm"]}
    check("proprietario A nao acessa produto B", owner.get(API + f"/ortomapas/{product['id']}"), 403)
    stats = outsider.post(API + "/tools/statistics", json={"input_path": product["caminho_arquivo"]})
    check("estatisticas da propria entrada", stats, 200)
    generated = outsider.post(API + '/tools/reproject', json={'input_path': product['caminho_arquivo'], 'output_name': 'saida_autorizada', 'target_epsg': 32617})
    check('reprojecao em pasta do proprio projeto', generated, 200)
    path = generated.json()['output_path']
    check('resultado do projeto B recusado a A', owner.post(API + '/media/access', json={'path': path}), 403)
    access = outsider.post(API + '/media/access', json={'path': path}); check('link do resultado autorizado', access, 200)
    check('download do resultado autorizado', anonymous.get('http://127.0.0.1:5018' + access.json()['url']), 200)
    check("saida com traversal recusada", outsider.post(API + "/tools/hillshade", json={"input_path": product["caminho_arquivo"], "output_name": "../escape"}), 422)
    check("entrada fora de data recusada", outsider.post(API + "/tools/statistics", json={"input_path": "/etc/passwd"}), 403)
    media = outsider.post(API + "/media/access", json={"path": product["caminho_thumbnail"]}); check("link de miniatura autorizado", media, 200)
    check("miniatura com link restrito", anonymous.get("http://127.0.0.1:5018" + media.json()["url"]), 200)
    check('visualizador nao altera metadados', owner.put(API + '/ortomapas/3', json={'nome':'Nao alterar'}), 403)
    check('visualizador nao gera arquivos no projeto alheio', owner.post(API + '/tools/reproject', json={'input_path':'ortomapas/odm_2_dsm.tif','output_name':'proibido','target_epsg':32617}), 403)
    permission = owner.get(API + '/projetos/2'); check('papel de visualizador consultado', permission, 200)
    assert permission.json()['pode_editar'] is False
    result["accepted"] = True
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
