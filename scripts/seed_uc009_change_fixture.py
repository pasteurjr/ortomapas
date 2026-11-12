"""Create an isolated UC-009 RGB change fixture from an existing real ODM ortho.

The baseline is a 512x512 crop of the real Aukerman/ODM orthomosaic. The
posterior copy changes only a known 100x100 RGB rectangle; its alpha mask and
all other pixels are preserved. A new validation project and two product rows
are created in PostgreSQL so the UI can execute the workflow end to end.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from rasterio.warp import transform_bounds

ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(ROOT))
from backend.database.connection import get_connection

SOURCE_ID = 70
SOURCE_PATH = ROOT / "data/ortomapas/odm_21_ortomosaico.tif"
OUTPUT_DIR = ROOT / "data/ortomapas/uc009_controlled"
WINDOW = rasterio.windows.Window(1000, 1000, 512, 512)
PATCH = (slice(200, 300), slice(200, 300))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    before_path = OUTPUT_DIR / "aukerman_uc009_antes.tif"
    after_path = OUTPUT_DIR / "aukerman_uc009_depois_patch_rgb_100x100.tif"
    user_id = int(__import__("os").environ.get("VALIDATION_USER_ID", "60"))

    with rasterio.open(SOURCE_PATH) as source:
        if source.count < 3 or source.crs is None or not source.crs.is_projected:
            raise RuntimeError("O ortomosaico-fonte precisa ter RGB e CRS projetado")
        data = source.read(window=WINDOW)
        profile = source.profile.copy()
        profile.update(width=512, height=512,
                       transform=rasterio.windows.transform(WINDOW, source.transform),
                       compress="deflate")
        with rasterio.open(before_path, "w", **profile) as destination:
            destination.write(data)
        changed = data.copy()
        changed[:3, PATCH[0], PATCH[1]] = 255 - changed[:3, PATCH[0], PATCH[1]]
        with rasterio.open(after_path, "w", **profile) as destination:
            destination.write(changed)
        valid = source.dataset_mask(window=WINDOW) > 0
        expected_pixels = int(valid[PATCH].sum())
        pixel_area = abs(profile["transform"].a * profile["transform"].e
                         - profile["transform"].b * profile["transform"].d)
        west, south, east, north = transform_bounds(profile["crs"], "EPSG:4326",
                                                      *rasterio.transform.array_bounds(512, 512, profile["transform"]))
        crs_name = source.crs.to_string()
        resolution_cm = float(max(abs(profile["transform"].a), abs(profile["transform"].e)) * 100)

    with get_connection() as conn:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT id FROM usuarios WHERE id=%s AND ativo=TRUE", (user_id,))
        if not cur.fetchone():
            raise RuntimeError(f"Usuario de validacao {user_id} nao encontrado/ativo")
        suffix = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        project_name = f"Validacao UC-009 RGB {suffix}"
        cur.execute("""INSERT INTO projetos (nome,descricao,area_estudo,status)
                       VALUES (%s,%s,%s,'ativo') RETURNING id""",
                    (project_name,
                     "Projeto isolado de validacao de mudanca RGB; derivado de ortomosaico ODM real com patch sintetico conhecido.",
                     "Aukerman / Westerville, Ohio"))
        project_id = cur.fetchone()["id"]
        cur.execute("INSERT INTO projeto_usuarios (projeto_id,usuario_id,papel) VALUES (%s,%s,'proprietario')",
                    (project_id, user_id))

        records = []
        for name, path, note in (
            ("UC-009 antes — recorte real do ortomosaico ODM #70", before_path,
             f"Recorte 512x512 do produto ODM #70; arquivo original {SOURCE_PATH.name}."),
            ("UC-009 depois — patch RGB sintético 100x100", after_path,
             "Copia do recorte anterior com RGB invertido somente nas linhas 200:300/colunas 200:300; alpha preservado."),
        ):
            size_mb = path.stat().st_size / (1024 * 1024)
            cur.execute("""INSERT INTO ortomapas
                (projeto_id,nome,tipo,formato,resolucao_cm,largura_px,altura_px,tamanho_arquivo_mb,
                 sistema_coordenadas,bbox_norte,bbox_sul,bbox_leste,bbox_oeste,centro_lat,centro_lon,
                 caminho_arquivo,status,data_processamento,observacoes)
                VALUES (%s,%s,'ortomosaico','GeoTIFF',%s,512,512,%s,%s,%s,%s,%s,%s,%s,%s,%s,'concluido',now(),%s)
                RETURNING id""",
                (project_id,name,resolution_cm,size_mb,crs_name,north,south,east,west,
                 (north+south)/2,(east+west)/2,
                 str(path.relative_to(ROOT / "data")),note))
            records.append(cur.fetchone()["id"])
        conn.commit()

    manifest = {
        "created_at": datetime.now().astimezone().isoformat(),
        "project_id": project_id,
        "source_product_id": SOURCE_ID,
        "source_path": str(SOURCE_PATH.relative_to(ROOT)),
        "source_sha256": sha256(SOURCE_PATH),
        "before_product_id": records[0],
        "after_product_id": records[1],
        "before_path": str(before_path.relative_to(ROOT)),
        "before_sha256": sha256(before_path),
        "after_path": str(after_path.relative_to(ROOT)),
        "after_sha256": sha256(after_path),
        "crs": crs_name,
        "grid": [512, 512],
        "pixel_area_m2": pixel_area,
        "known_change_window_zero_based": {"rows": [200, 300], "columns": [200, 300]},
        "expected_changed_pixels": expected_pixels,
        "expected_changed_area_m2": expected_pixels * pixel_area,
        "synthetic_change": "RGB inverted (255 - channel) in the known 100x100 window; alpha unchanged.",
        "llm_calls": 0,
    }
    manifest_path = OUTPUT_DIR / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"project_id": project_id, "before_product_id": records[0],
                      "after_product_id": records[1], "expected_changed_pixels": expected_pixels,
                      "expected_changed_area_m2": round(expected_pixels * pixel_area, 4),
                      "manifest": str(manifest_path.relative_to(ROOT))}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
