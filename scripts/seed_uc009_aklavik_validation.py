"""Register the public Aklavik 2022/2024 orthomosaics as an isolated UC-009 project.

The source imagery is downloaded separately; this script creates only local
PostgreSQL metadata, two capture records, and two ortho product records.
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import date, datetime, timezone
from pathlib import Path

import rasterio
from pyproj import CRS
from rasterio.warp import transform_bounds

ROOT = Path(__file__).resolve().parents[1]
sys_path = str(ROOT)
import sys
if sys_path not in sys.path:
    sys.path.insert(0, sys_path)

from backend.database.connection import get_connection
from backend.utils.thumbnail import generate_thumbnail

PROJECT_NAME = "Validacao UC-009 Aklavik 2022-2024"
USER_ID = int(os.environ.get("VALIDATION_USER_ID", "60"))
SOURCE_DIR = ROOT / "data/validacao/uc009_aklavik"
THUMB_DIR = ROOT / "data/thumbnails"
OUTPUT_MANIFEST = ROOT / "docs/validacao/ortomapas_conclusao/etapa-10/uc009_independent_campaigns/seed_manifest.json"
DOI = "https://doi.org/10.5281/zenodo.14608566"
SOURCES = [
    {
        "date": date(2022, 9, 21),
        "window": "2022-09-19..2022-09-21",
        "local": SOURCE_DIR / "2022_ortomosaico.tif",
        "relative": "validacao/uc009_aklavik/2022_ortomosaico.tif",
        "original": "20220921_DJI_Mini2_UndercoverEisAgenten_Orthomosaic_Aklavik_Town_10cm.tif",
        "md5": "53bf718e84bc8335f54732b554222ed0",
        "product_name": "Ortomosaico Aklavik — campanha 2022",
        "flight_name": "Campanha UAV Aklavik 2022",
    },
    {
        "date": date(2024, 3, 24),
        "window": "2024-03-22..2024-03-24",
        "local": SOURCE_DIR / "2024_ortomosaico.tif",
        "relative": "validacao/uc009_aklavik/2024_ortomosaico.tif",
        "original": "20240324_DJI_Mini2_UndercoverEisAgenten_Orthomosaic_Aklavik_Town_10cm.tif",
        "md5": "0429640ef35fd1475a54fa33ce8328bb",
        "product_name": "Ortomosaico Aklavik — campanha 2024",
        "flight_name": "Campanha UAV Aklavik 2024",
    },
]


def digest(path: Path, algorithm: str) -> str:
    checksum = hashlib.new(algorithm)
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            checksum.update(block)
    return checksum.hexdigest()


def raster_metadata(source: dict) -> dict:
    path = source["local"]
    if not path.is_file():
        raise FileNotFoundError(f"GeoTIFF ainda não baixado: {path}")
    actual_md5 = digest(path, "md5")
    if actual_md5 != source["md5"]:
        raise ValueError(f"MD5 divergente para {path.name}: {actual_md5}")
    metadata = {"md5": actual_md5, "sha256": digest(path, "sha256"), "size_bytes": path.stat().st_size}
    with rasterio.open(path) as raster:
        if raster.crs is None or raster.count < 3 or not raster.crs.is_projected:
            raise ValueError(f"{path.name} precisa ser RGB georreferenciado em CRS projetado")
        metadata.update({
            "width": raster.width,
            "height": raster.height,
            "bands": raster.count,
            "crs": raster.crs.to_string(),
            "transform": list(raster.transform)[:6],
            "bounds_projected": [raster.bounds.left, raster.bounds.bottom, raster.bounds.right, raster.bounds.top],
            "bounds_wgs84": list(transform_bounds(raster.crs, "EPSG:4326", *raster.bounds)),
            "resolution_m": [abs(value) * CRS.from_user_input(raster.crs).axis_info[0].unit_conversion_factor for value in raster.res],
            "nodata": raster.nodata,
        })
    thumb = THUMB_DIR / f"uc009_aklavik_{source['date'].year}.png"
    THUMB_DIR.mkdir(parents=True, exist_ok=True)
    generate_thumbnail(str(path), str(thumb), size=(512, 512))
    metadata["thumbnail"] = str(thumb)
    return metadata


def main() -> None:
    OUTPUT_MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    metadata = [raster_metadata(item) for item in SOURCES]
    if metadata[0]["crs"] != metadata[1]["crs"]:
        raise ValueError("Campanhas estão em CRS diferentes; não registrar sem reconciliação explícita")
    with get_connection() as conn:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT id FROM usuarios WHERE id=%s AND ativo=TRUE", (USER_ID,))
        if not cur.fetchone():
            raise RuntimeError(f"Usuário de validação ativo {USER_ID} não encontrado")
        cur.execute("SELECT id FROM projetos WHERE nome=%s ORDER BY id", (PROJECT_NAME,))
        rows = cur.fetchall()
        if len(rows) > 1:
            raise RuntimeError("Há projetos de validação duplicados; revise o banco antes de prosseguir")
        if rows:
            project_id = int(rows[0]["id"])
        else:
            cur.execute("""INSERT INTO projetos (nome,descricao,area_estudo,objetivo,status,data_inicio,data_fim)
                           VALUES (%s,%s,%s,%s,'ativo',%s,%s) RETURNING id""",
                        (PROJECT_NAME,
                         "Fixture de validação UC-009 criada a partir de dois ortomosaicos públicos de campanhas UAV independentes.",
                         "Aklavik, Northwest Territories, Canadá",
                         "Verificar comparação RGB entre campanhas independentes; sem alegação de acurácia de campo.",
                         SOURCES[0]["date"], SOURCES[1]["date"]))
            project_id = int(cur.fetchone()["id"])
        cur.execute("""INSERT INTO projeto_usuarios (projeto_id,usuario_id,papel)
                       VALUES (%s,%s,'proprietario') ON CONFLICT (projeto_id,usuario_id) DO NOTHING""",
                    (project_id, USER_ID))

        flight_ids = []
        product_ids = []
        for source, meta in zip(SOURCES, metadata):
            cur.execute("SELECT id FROM voos WHERE projeto_id=%s AND app_voo=%s ORDER BY id",
                        (project_id, source["flight_name"]))
            existing = cur.fetchall()
            if len(existing) > 1:
                raise RuntimeError(f"Voos duplicados: {source['flight_name']}")
            if existing:
                flight_id = int(existing[0]["id"])
            else:
                cur.execute("""INSERT INTO voos (projeto_id,data_voo,app_voo,observacoes)
                               VALUES (%s,%s,%s,%s) RETURNING id""",
                            (project_id, source["date"],
                             source["flight_name"],
                             f"Janela de aquisição: {source['window']}. Dataset: {DOI}. "
                             "DJI Mini 2. As imagens originais não foram baixadas; este registro documenta a campanha e seu ortomosaico publicado."))
                flight_id = int(cur.fetchone()["id"])
            flight_ids.append(flight_id)
            cur.execute("SELECT id,caminho_arquivo,voo_id FROM ortomapas WHERE projeto_id=%s AND nome=%s ORDER BY id",
                        (project_id, source["product_name"]))
            existing = cur.fetchall()
            if len(existing) > 1:
                raise RuntimeError(f"Produtos duplicados: {source['product_name']}")
            if existing:
                product = existing[0]
                if product["caminho_arquivo"] != source["relative"] or product["voo_id"] != flight_id:
                    raise RuntimeError(f"Produto existente não coincide com esta fixture: #{product['id']}")
                product_id = int(product["id"])
            else:
                west, south, east, north = meta["bounds_wgs84"]
                resolution_cm = 100 * sum(meta["resolution_m"]) / 2
                cur.execute("""INSERT INTO ortomapas
                    (projeto_id,voo_id,nome,tipo,formato,resolucao_cm,largura_px,altura_px,tamanho_arquivo_mb,
                     sistema_coordenadas,bbox_norte,bbox_sul,bbox_leste,bbox_oeste,centro_lat,centro_lon,
                     caminho_arquivo,caminho_thumbnail,status,data_processamento,observacoes)
                    VALUES (%s,%s,%s,'ortomosaico','GeoTIFF',%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                            'disponivel',now(),%s) RETURNING id""",
                    (project_id, flight_id, source["product_name"], resolution_cm,
                     meta["width"], meta["height"], meta["size_bytes"] / (1024 * 1024), meta["crs"],
                     north, south, east, west, (north + south) / 2, (east + west) / 2,
                     source["relative"], meta["thumbnail"],
                     f"Ortomosaico público da campanha {source['window']}; DOI {DOI}. "
                     "O registro e o arquivo de ortomosaico são dados de validação; sem GCP independentes."))
                product_id = int(cur.fetchone()["id"])
            product_ids.append(product_id)
        conn.commit()

    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "project_id": project_id,
        "user_id": USER_ID,
        "project_name": PROJECT_NAME,
        "source": DOI,
        "dataset_title": "High-resolution UAV Orthomosaic and DSM Dataset — Aklavik, NWT, CA [2022, 2024]",
        "campaigns": [
            {"flight_id": flight_ids[i], "product_id": product_ids[i], "date": source["date"].isoformat(),
             "acquisition_window": source["window"], "original_filename": source["original"],
             "local_path": str(source["local"].relative_to(ROOT)), **metadata[i]}
            for i, source in enumerate(SOURCES)
        ],
        "important_limitations": [
            "Two acquisition campaigns are independent by collection date; orthomosaics are already reported aligned in the source dataset.",
            "No GCP/checkpoint truth or manually labeled change polygons are included in this validation.",
            "The source report states a horizontal/vertical alignment procedure; this app run does not independently estimate camera geometry.",
            "Only the two RGB orthomosaics were downloaded. Raw photos and DSMs were not downloaded.",
        ],
        "llm_calls": 0,
    }
    OUTPUT_MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"project_id": project_id, "flight_ids": flight_ids, "product_ids": product_ids,
                      "manifest": str(OUTPUT_MANIFEST.relative_to(ROOT)),
                      "rasters": [{k: m[k] for k in ("width","height","crs","resolution_m","size_bytes","md5")} for m in metadata]},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
