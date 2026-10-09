"""Seed idempotente de produtos sintéticos para a demonstração de Guarajuba.

Os rasters são deliberadamente marcados como sintéticos; não representam um
levantamento aéreo real nem substituem dados de campo.
"""

from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import laspy
import numpy as np
import rasterio
from psycopg2.extras import Json
from rasterio.transform import from_bounds

from backend.database.connection import get_connection

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "demo_guarajuba"
DATA.mkdir(parents=True, exist_ok=True)
PROJECT_NAME = "Guarajuba - Condomínio Paraíso (Demonstração)"
BOUNDS = (-38.0758, -12.6538, -38.0680, -12.6470)  # west, south, east, north
CRS = "EPSG:4326"


def write_rasters() -> dict[str, Path]:
    west, south, east, north = BOUNDS
    width = height = 256
    transform = from_bounds(west, south, east, north, width, height)
    y, x = np.mgrid[0:height, 0:width]
    undulation = 4 * np.sin(x / 18) + 3 * np.cos(y / 21)
    buildings = (((x // 22 + y // 18) % 5) == 0) * 7
    dtm = 18 + undulation
    dsm = dtm + buildings
    red = np.clip(100 + 40 * np.sin(x / 30), 0, 255).astype("uint8")
    green = np.clip(125 + 45 * np.cos(y / 27), 0, 255).astype("uint8")
    blue = np.clip(150 + 35 * np.sin((x + y) / 35), 0, 255).astype("uint8")
    green_f = green.astype("float32")
    red_f = red.astype("float32")
    ndvi = np.clip((green_f - red_f) / (green_f + red_f + 1), -1, 1).astype("float32")
    paths = {}
    for name, array, count, dtype in (("ortho", np.stack([red, green, blue]), 3, "uint8"), ("dtm", dtm.astype("float32"), 1, "float32"), ("dsm", dsm.astype("float32"), 1, "float32"), ("ndvi", ndvi, 1, "float32")):
        path = DATA / f"guarajuba_{name}_demo.tif"
        with rasterio.open(path, "w", driver="GTiff", height=height, width=width, count=count, dtype=dtype, crs=CRS, transform=transform, compress="deflate") as dst:
            dst.write(array if count > 1 else array[np.newaxis, ...])
            dst.update_tags(origem="simulado", finalidade="demonstracao", area="Condominio Paraiso Guarajuba")
        paths[name] = path
    return paths


def write_cloud() -> Path:
    path = DATA / "guarajuba_nuvem_demo.laz"
    header = laspy.LasHeader(point_format=3, version="1.2")
    header.add_extra_dim(laspy.ExtraBytesParams(name="classificacao_demo", type=np.uint8))
    cloud = laspy.LasData(header)
    rng = np.random.default_rng(42)
    count = 120_000
    cloud.x = rng.uniform(BOUNDS[0], BOUNDS[2], count)
    cloud.y = rng.uniform(BOUNDS[1], BOUNDS[3], count)
    cloud.z = 18 + 4 * np.sin(np.arange(count) / 300) + rng.normal(0, 0.3, count)
    cloud.intensity = rng.integers(0, 255, count, dtype=np.uint16)
    cloud.classificacao_demo = rng.integers(1, 6, count, dtype=np.uint8)
    cloud.header.offsets = [0, 0, 0]
    cloud.header.scales = [1e-7, 1e-7, 0.01]
    cloud.write(path)
    return path


def relative(path: Path) -> str:
    return str(path.relative_to(ROOT / "data"))


def main() -> None:
    rasters = write_rasters()
    cloud = write_cloud()
    with get_connection() as conn:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT id FROM usuarios WHERE email = %s", ("phase1-1791391595@example.test",))
        user = cur.fetchone()
        if not user:
            raise RuntimeError("Usuario de demonstração não encontrado")
        cur.execute("SELECT id FROM projetos WHERE nome = %s", (PROJECT_NAME,))
        old = cur.fetchone()
        if old:
            cur.execute("DELETE FROM projetos WHERE id = %s", (old["id"],))
        cur.execute("""INSERT INTO projetos (nome, descricao, area_estudo, bbox_norte, bbox_sul, bbox_leste, bbox_oeste, centro_lat, centro_lon, objetivo, responsavel, status)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'em_andamento') RETURNING id""", (PROJECT_NAME, "Seed reproduzível com cartografia OSM e produtos raster sintéticos.", "Condomínio Paraíso, Guarajuba, Camaçari/BA", BOUNDS[3], BOUNDS[1], BOUNDS[2], BOUNDS[0], (-12.6538 - 12.6470) / 2, (-38.0758 - 38.0680) / 2, "Demonstrar o ciclo de dados, ODM, análises e visualização 3D", "Seed Ortomapas"))
        project_id = cur.fetchone()["id"]
        cur.execute("INSERT INTO projeto_usuarios (projeto_id, usuario_id, papel) VALUES (%s,%s,'proprietario')", (project_id, user["id"]))
        cur.execute("""INSERT INTO voos (projeto_id,data_voo,local_decolagem_lat,local_decolagem_lon,altitude_voo_m,sobreposicao_frontal,sobreposicao_lateral,velocidade_ms,num_fotos,resolucao_foto,formato_foto,gsd_cm,area_coberta_ha,num_baterias,app_voo,observacoes)
            VALUES (%s,now(),-12.6504521,-38.0714399,80,80,70,4,24,'4000x3000','JPEG',1.5,5.2,1,'Litchi Mission Hub','Fotos e telemetria sintéticas para demonstração') RETURNING id""", (project_id,))
        flight_id = cur.fetchone()["id"]
        cur.execute("""INSERT INTO processamentos_odm (projeto_id,voo_id,odm_task_id,endpoint,engine,engine_version,parametros,status,progresso,etapa,criado_por,inicio_em,fim_em)
            VALUES (%s,%s,%s,%s,'NodeODM','3.9.0',%s,'concluido',100,'Produtos importados',%s,now()-interval '12 minutes',now()-interval '2 minutes') RETURNING id""", (project_id, flight_id, "seed-guarajuba-concluido", "http://localhost:8021", Json({"origem": "seed", "sintetico": True}), user["id"]))
        processing_id = cur.fetchone()["id"]
        cur.execute("""INSERT INTO processamentos_odm (projeto_id,voo_id,odm_task_id,endpoint,engine,status,progresso,etapa,criado_por) VALUES (%s,%s,%s,%s,'NodeODM','processando',48,'Gerando DSM',%s)""", (project_id, flight_id, "seed-guarajuba-processando", "http://localhost:8021", user["id"]))
        cur.execute("""INSERT INTO processamentos_odm (projeto_id,voo_id,odm_task_id,endpoint,engine,status,progresso,etapa,erro,criado_por) VALUES (%s,%s,%s,%s,'NodeODM','erro',62,'Reconstrução','Exemplo de falha recuperável para demonstração',%s)""", (project_id, flight_id, "seed-guarajuba-erro", "http://localhost:8021", user["id"]))
        bbox_sql = "ST_GeomFromText('POLYGON((-38.0758 -12.6538,-38.0680 -12.6538,-38.0680 -12.6470,-38.0758 -12.6470,-38.0758 -12.6538))',4326)"
        ortho_ids = {}
        for name, kind, path, bands in (("Ortomosaico sintético Guarajuba", "ortomosaico", rasters["ortho"], 3), ("DSM sintético Guarajuba", "dsm", rasters["dsm"], 1), ("DTM sintético Guarajuba", "dtm", rasters["dtm"], 1), ("NDVI sintético Guarajuba", "ndvi", rasters["ndvi"], 1)):
            cur.execute(f"""INSERT INTO ortomapas (voo_id,projeto_id,nome,tipo,formato,resolucao_cm,largura_px,altura_px,tamanho_arquivo_mb,sistema_coordenadas,bbox_norte,bbox_sul,bbox_leste,bbox_oeste,centro_lat,centro_lon,caminho_arquivo,webodm_task_id,status,data_processamento,observacoes)
                VALUES (%s,%s,%s,%s,'GeoTIFF',2.5,256,256,%s,'EPSG:4326',%s,%s,%s,%s,-12.6504,-38.0719,%s,'seed-guarajuba-concluido','disponivel',now(),'DADO SINTÉTICO - não representa levantamento aéreo real') RETURNING id""", (flight_id, project_id, name, kind, path.stat().st_size / 1048576, BOUNDS[3], BOUNDS[1], BOUNDS[2], BOUNDS[0], relative(path)))
            ortho_ids[kind] = cur.fetchone()["id"]
            cur.execute(f"INSERT INTO produtos_processamento (processamento_id,ortomapa_id,tipo,caminho,formato,tamanho_arquivo_mb,crs,resolucao,largura_px,altura_px,bandas,bbox) VALUES (%s,%s,%s,%s,'GeoTIFF',%s,'EPSG:4326',0.000025,256,256,%s,{bbox_sql})", (processing_id, ortho_ids[kind], kind, relative(path), path.stat().st_size / 1048576, bands))
        cur.execute("INSERT INTO produtos_processamento (processamento_id,tipo,caminho,formato,tamanho_arquivo_mb,crs,bbox) VALUES (%s,'nuvem_pontos',%s,'LAZ',%s,'EPSG:4326'," + bbox_sql + ")", (processing_id, relative(cloud), cloud.stat().st_size / 1048576))
        for kind, name, ortho_id, result in (("vegetacao", "NDVI sintético - estatísticas", ortho_ids["ndvi"], {"min": -0.42, "max": 0.68, "mean": 0.21, "std": 0.18}), ("terreno", "Declividade sintética", ortho_ids["dsm"], {"min": 0.2, "max": 18.4, "mean": 4.7}), ("mudancas", "Diferença DSM-DTM sintética", ortho_ids["dsm"], {"min": 0, "max": 7, "mean": 1.8}), ("volume", "Volume sintético de corte e aterro", ortho_ids["dsm"], {"corte_m3": 1240.5, "aterro_m3": 830.2})):
            cur.execute("INSERT INTO analises (ortomapa_id,projeto_id,tipo_analise,nome,descricao,parametros,resultado_json,modelo_ia,agente_ia,status,tempo_processamento_seg,data_analise,observacoes) VALUES (%s,%s,%s,%s,%s,%s,%s,'seed-demo','SeedDemoAgent','concluido',12,now(),'Resultado sintético para demonstração')", (ortho_id, project_id, kind, name, "Resultado sintético identificado como demonstração", Json({"sintetico": True}), Json(result)))
        conn.commit()
    print(json.dumps({"project_id": project_id, "flight_id": flight_id, "processing_id": processing_id, "ortomapas": list(ortho_ids.values()), "products": 5, "analyses": 4, "data_dir": str(DATA)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
