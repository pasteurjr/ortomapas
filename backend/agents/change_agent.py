"""
Change detection agent.

Compares two ortomapas (before / after) to identify areas of change,
producing a binary change mask and a classified change map.
"""

import json
import logging
import os
import time
from datetime import datetime

import numpy as np

try:
    import rasterio
    from rasterio.windows import from_bounds
except ImportError:
    rasterio = None

from backend.database.connection import execute_query
from backend.config import ANALISES_DIR

logger = logging.getLogger("agent.change")


class ChangeAgent:
    """Detect changes between two ortomapas."""

    CHANGE_LABELS = {
        1: "desmatamento",
        2: "construcao",
        3: "erosao",
        4: "inundacao",
        5: "outro",
    }

    def execute(self, task):
        """
        Parameters inside task['parametros'] (JSON):
            ortomapa_antes_id  – id of the "before" ortomapa
            ortomapa_depois_id – id of the "after" ortomapa
            threshold          – mean band diff threshold (default 30)
        """
        t0 = time.time()

        if rasterio is None:
            raise RuntimeError("rasterio is not installed")

        # --- 1. Parse params ---
        params = task.get("parametros")
        if isinstance(params, str):
            params = json.loads(params)
        params = params or {}

        antes_id = params.get("ortomapa_antes_id") or task.get("ortomapa_id")
        depois_id = params.get("ortomapa_depois_id")
        threshold = float(params.get("threshold", 30.0))

        if antes_id is None or depois_id is None:
            raise ValueError(
                "Both ortomapa_antes_id and ortomapa_depois_id are required"
            )

        # --- 2. Get paths ---
        ortomapa_antes = execute_query(
            "SELECT * FROM ortomapas WHERE id = %s", (antes_id,), fetch_one=True
        )
        ortomapa_depois = execute_query(
            "SELECT * FROM ortomapas WHERE id = %s", (depois_id,), fetch_one=True
        )
        if ortomapa_antes is None:
            raise ValueError(f"Ortomapa antes {antes_id} not found")
        if ortomapa_depois is None:
            raise ValueError(f"Ortomapa depois {depois_id} not found")

        path_antes = ortomapa_antes["caminho_arquivo"]
        path_depois = ortomapa_depois["caminho_arquivo"]

        for p in (path_antes, path_depois):
            if not os.path.isfile(p):
                raise FileNotFoundError(f"Raster not found: {p}")

        logger.info(
            "Change detection: antes=%d depois=%d threshold=%.1f",
            antes_id,
            depois_id,
            threshold,
        )

        # --- 3. Read both rasters, crop to intersection ---
        with rasterio.open(path_antes) as src_a, rasterio.open(path_depois) as src_d:
            # Compute intersection bounds
            bounds_a = src_a.bounds
            bounds_d = src_d.bounds

            inter_left = max(bounds_a.left, bounds_d.left)
            inter_bottom = max(bounds_a.bottom, bounds_d.bottom)
            inter_right = min(bounds_a.right, bounds_d.right)
            inter_top = min(bounds_a.top, bounds_d.top)

            if inter_left >= inter_right or inter_bottom >= inter_top:
                raise ValueError("The two ortomapas do not overlap spatially")

            # Windows in each raster
            win_a = from_bounds(
                inter_left, inter_bottom, inter_right, inter_top, src_a.transform
            )
            win_d = from_bounds(
                inter_left, inter_bottom, inter_right, inter_top, src_d.transform
            )

            # Read bands (take min band count, usually 3)
            n_bands = min(src_a.count, src_d.count, 3)
            data_a = src_a.read(
                list(range(1, n_bands + 1)), window=win_a
            ).astype(np.float64)
            data_d = src_d.read(
                list(range(1, n_bands + 1)), window=win_d
            ).astype(np.float64)

            # Resample to same shape if needed (use the smaller shape)
            h = min(data_a.shape[1], data_d.shape[1])
            w = min(data_a.shape[2], data_d.shape[2])
            data_a = data_a[:, :h, :w]
            data_d = data_d[:, :h, :w]

            # Use the 'antes' raster metadata for output
            out_transform = rasterio.transform.from_bounds(
                inter_left, inter_bottom, inter_right, inter_top, w, h
            )
            crs = src_a.crs
            pixel_area_m2 = abs(out_transform.a) * abs(out_transform.e)

        # --- 4. Per-band absolute difference ---
        diff = np.abs(data_a - data_d)  # (bands, H, W)
        mean_diff = np.mean(diff, axis=0)  # (H, W)

        # --- 5. Binary change mask ---
        change_mask = (mean_diff > threshold).astype(np.uint8)  # 0 = no change, 1 = change

        # --- 6. Classify changes by dominant band ---
        # Determine which band has the largest change at each pixel
        dominant_band = np.argmax(diff, axis=0)  # 0=R, 1=G, 2=B

        classified = np.zeros((h, w), dtype=np.uint8)

        # Only classify where change was detected
        mask = change_mask == 1

        # Heuristic classification based on band dominance and sign
        sign_diff = data_d - data_a  # positive = brighter after
        mean_sign = np.mean(sign_diff, axis=0)

        # Green dominant + getting less green -> desmatamento
        classified[mask & (dominant_band == 1) & (sign_diff[1][mask & (dominant_band == 1)] < 0 if np.any(mask & (dominant_band == 1)) else False)] = 1
        # Simplified heuristic approach:
        for row in range(h):
            for col in range(w):
                if not mask[row, col]:
                    continue
                db = dominant_band[row, col]
                ms = mean_sign[row, col]
                green_change = sign_diff[1, row, col] if n_bands > 1 else 0
                red_change = sign_diff[0, row, col]

                if db == 1 and green_change < 0:
                    # Loss of green -> desmatamento
                    classified[row, col] = 1
                elif db == 0 and red_change > 0 and ms > 0:
                    # Getting brighter, red dominant -> construcao
                    classified[row, col] = 2
                elif db == 0 and red_change > 0 and ms < 0:
                    # Red bright but overall darker -> erosao
                    classified[row, col] = 3
                elif db == 2:
                    # Blue dominant -> inundacao
                    classified[row, col] = 4
                else:
                    classified[row, col] = 5

        # Vectorised approach (much faster, replaces the loop above for large images)
        # Reset classified where mask is True and apply vectorised logic
        classified_v = np.full((h, w), 5, dtype=np.uint8)  # default = outro
        green_ch = sign_diff[1] if n_bands > 1 else np.zeros((h, w))
        red_ch = sign_diff[0]

        classified_v[(dominant_band == 1) & (green_ch < 0)] = 1  # desmatamento
        classified_v[(dominant_band == 0) & (red_ch > 0) & (mean_sign > 0)] = 2  # construcao
        classified_v[(dominant_band == 0) & (red_ch > 0) & (mean_sign <= 0)] = 3  # erosao
        classified_v[dominant_band == 2] = 4  # inundacao

        # Apply only where change detected
        classified = np.where(mask, classified_v, 0).astype(np.uint8)

        # --- 7. Write change map GeoTIFF ---
        os.makedirs(ANALISES_DIR, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        change_filename = f"change_{antes_id}_{depois_id}_{ts}.tif"
        change_path = os.path.join(ANALISES_DIR, change_filename)

        out_profile = {
            "driver": "GTiff",
            "dtype": "uint8",
            "width": w,
            "height": h,
            "count": 1,
            "crs": crs,
            "transform": out_transform,
            "compress": "lzw",
            "nodata": 0,
        }
        with rasterio.open(change_path, "w", **out_profile) as dst:
            dst.write(classified, 1)

        logger.info("Change map saved: %s", change_path)

        # --- 8. Statistics ---
        total_pixels = h * w
        changed_pixels = int(np.sum(change_mask))
        area_changed_m2 = changed_pixels * pixel_area_m2
        pct_changed = round(100.0 * changed_pixels / total_pixels, 2) if total_pixels > 0 else 0

        class_stats = {}
        for val, label in self.CHANGE_LABELS.items():
            count = int(np.sum(classified == val))
            area = count * pixel_area_m2
            class_stats[label] = {
                "pixels": count,
                "area_m2": round(area, 2),
                "area_ha": round(area / 10000.0, 4),
                "pct": round(100.0 * count / total_pixels, 2) if total_pixels > 0 else 0,
            }

        stats = {
            "total_pixels": total_pixels,
            "changed_pixels": changed_pixels,
            "area_changed_m2": round(area_changed_m2, 2),
            "area_changed_ha": round(area_changed_m2 / 10000.0, 4),
            "pct_changed": pct_changed,
            "threshold": threshold,
            "change_classes": class_stats,
        }

        elapsed = round(time.time() - t0, 2)

        # --- 9. Register in analises table ---
        analise_id = execute_query(
            """
            INSERT INTO analises
                (ortomapa_id, projeto_id, tipo_analise, nome, descricao,
                 parametros, resultado_path, resultado_json,
                 agente_ia, status, tempo_processamento_seg)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                task["ortomapa_id"],
                ortomapa_antes["projeto_id"],
                "deteccao_mudancas",
                f"Deteccao Mudancas {antes_id} vs {depois_id}",
                f"Comparacao temporal entre ortomapas {antes_id} e {depois_id}",
                json.dumps(params, ensure_ascii=False),
                change_path,
                json.dumps(stats, ensure_ascii=False),
                "agente_mudanca",
                "concluido",
                elapsed,
            ),
            commit=True,
        )

        # Register in comparacoes_temporais table
        try:
            # Get dates from the ortomapas
            data_antes = ortomapa_antes.get("data_processamento") or ortomapa_antes.get("created_at") or datetime.now()
            data_depois = ortomapa_depois.get("data_processamento") or ortomapa_depois.get("created_at") or datetime.now()

            execute_query(
                """
                INSERT INTO comparacoes_temporais
                    (projeto_id, ortomapa_antes_id, ortomapa_depois_id,
                     data_antes, data_depois, tipo_comparacao,
                     resultado_path, resultado_thumbnail, estatisticas)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    ortomapa_antes["projeto_id"],
                    antes_id,
                    depois_id,
                    data_antes,
                    data_depois,
                    "deteccao_mudancas",
                    change_path,
                    None,
                    json.dumps(stats, ensure_ascii=False),
                ),
                commit=True,
            )
        except Exception as e:
            logger.warning("Failed to insert into comparacoes_temporais: %s", e)

        logger.info(
            "Change detection complete. analise_id=%s changed=%.2f%% elapsed=%.1fs",
            analise_id,
            pct_changed,
            elapsed,
        )

        # --- 10. Return ---
        return {
            "analise_id": analise_id,
            "change_map": change_path,
            "statistics": stats,
            "elapsed_seconds": elapsed,
        }
