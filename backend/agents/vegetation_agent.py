"""
Vegetation index agent.

Computes RGB-based vegetation indices on an ortomapa, classifies the result
into health categories, and writes GeoTIFF outputs.
"""

import json
import logging
import os
import time
from datetime import datetime

import numpy as np

try:
    import rasterio
    from rasterio.transform import array_bounds
except ImportError:
    rasterio = None

from backend.database.connection import execute_query
from backend.config import ANALISES_DIR

logger = logging.getLogger("agent.vegetation")


class VegetationAgent:
    """Compute RGB vegetation indices and classify health."""

    # Indices that work on visible-band (RGB) imagery.
    # Each lambda receives R, G, B as float64 arrays in [0, 255].
    INDICES = {
        "VARI": lambda r, g, b: np.where(
            (g + r - b) != 0,
            (g - r) / (g + r - b + 1e-10),
            0.0,
        ),
        "TGI": lambda r, g, b: g - 0.39 * r - 0.61 * b,
        "ExG": lambda r, g, b: 2.0 * g - r - b,
        "ExR": lambda r, g, b: 1.4 * r - g,
        "ExGR": lambda r, g, b: (2.0 * g - r - b) - (1.4 * r - g),
        "GLI": lambda r, g, b: np.where(
            (2.0 * g + r + b) != 0,
            (2.0 * g - r - b) / (2.0 * g + r + b + 1e-10),
            0.0,
        ),
        "RGBVI": lambda r, g, b: np.where(
            (g * g + r * b) != 0,
            (g * g - r * b) / (g * g + r * b + 1e-10),
            0.0,
        ),
        "MGRVI": lambda r, g, b: np.where(
            (g * g + r * r) != 0,
            (g * g - r * r) / (g * g + r * r + 1e-10),
            0.0,
        ),
    }

    # ------------------------------------------------------------------
    def execute(self, task):
        """
        Main entry point called by the orchestrator.

        Parameters inside task['parametros'] (JSON):
            index       – index name (default "VARI")
            threshold_high – above this = healthy (default 0.1)
            threshold_low  – below this = no vegetation (default -0.1)
        """
        t0 = time.time()

        if rasterio is None:
            raise RuntimeError("rasterio is not installed")

        # --- 1. Resolve ortomapa path from DB ---
        ortomapa_id = task["ortomapa_id"]
        ortomapa = execute_query(
            "SELECT * FROM ortomapas WHERE id = %s",
            (ortomapa_id,),
            fetch_one=True,
        )
        if ortomapa is None:
            raise ValueError(f"Ortomapa {ortomapa_id} not found")
        raster_path = ortomapa["caminho_arquivo"]
        if not os.path.isfile(raster_path):
            raise FileNotFoundError(f"Raster file not found: {raster_path}")

        # --- 2. Parse parameters ---
        params = task.get("parametros")
        if isinstance(params, str):
            params = json.loads(params)
        params = params or {}
        index_name = params.get("index", "VARI")
        threshold_high = float(params.get("threshold_high", 0.1))
        threshold_low = float(params.get("threshold_low", -0.1))

        if index_name not in self.INDICES:
            raise ValueError(
                f"Unknown index '{index_name}'. Available: {list(self.INDICES.keys())}"
            )

        logger.info(
            "Computing %s for ortomapa %d (%s)", index_name, ortomapa_id, raster_path
        )

        # --- 3. Read raster ---
        with rasterio.open(raster_path) as src:
            # Assume bands 1, 2, 3 = R, G, B
            r = src.read(1).astype(np.float64)
            g = src.read(2).astype(np.float64)
            b = src.read(3).astype(np.float64)
            profile = src.profile.copy()
            transform = src.transform
            crs = src.crs
            pixel_width = abs(transform.a)
            pixel_height = abs(transform.e)
            pixel_area_m2 = pixel_width * pixel_height  # assumes projected CRS in metres

        # --- 4. Compute index ---
        index_fn = self.INDICES[index_name]
        index_arr = index_fn(r, g, b).astype(np.float32)

        # --- 5. Classify ---
        classified = np.zeros_like(index_arr, dtype=np.uint8)
        classified[index_arr >= threshold_high] = 3  # healthy
        classified[
            (index_arr >= threshold_low) & (index_arr < threshold_high)
        ] = 2  # stressed
        classified[index_arr < threshold_low] = 1  # no vegetation

        class_labels = {1: "sem_vegetacao", 2: "estressada", 3: "saudavel"}

        # --- 6. Write index GeoTIFF ---
        os.makedirs(ANALISES_DIR, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        index_filename = f"vi_{index_name}_{ortomapa_id}_{ts}.tif"
        index_path = os.path.join(ANALISES_DIR, index_filename)

        idx_profile = profile.copy()
        idx_profile.update(
            dtype="float32",
            count=1,
            compress="lzw",
            nodata=-9999.0,
        )
        with rasterio.open(index_path, "w", **idx_profile) as dst:
            dst.write(index_arr, 1)

        logger.info("Index raster saved: %s", index_path)

        # --- 7. Write classified GeoTIFF ---
        cls_filename = f"vi_class_{index_name}_{ortomapa_id}_{ts}.tif"
        cls_path = os.path.join(ANALISES_DIR, cls_filename)

        cls_profile = profile.copy()
        cls_profile.update(
            dtype="uint8",
            count=1,
            compress="lzw",
            nodata=0,
        )
        with rasterio.open(cls_path, "w", **cls_profile) as dst:
            dst.write(classified, 1)

        logger.info("Classified raster saved: %s", cls_path)

        # --- 8. Statistics ---
        total_pixels = int(classified.size)
        stats_classes = {}
        for val, label in class_labels.items():
            count = int(np.sum(classified == val))
            area_m2 = count * pixel_area_m2
            stats_classes[label] = {
                "pixels": count,
                "area_m2": round(area_m2, 2),
                "area_ha": round(area_m2 / 10000.0, 4),
                "pct": round(100.0 * count / total_pixels, 2) if total_pixels > 0 else 0,
            }

        valid_mask = (classified > 0)
        index_valid = index_arr[valid_mask] if np.any(valid_mask) else index_arr
        stats = {
            "index": index_name,
            "mean": round(float(np.mean(index_valid)), 6),
            "std": round(float(np.std(index_valid)), 6),
            "min": round(float(np.min(index_valid)), 6),
            "max": round(float(np.max(index_valid)), 6),
            "classes": stats_classes,
            "thresholds": {
                "high": threshold_high,
                "low": threshold_low,
            },
            "total_pixels": total_pixels,
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
                ortomapa_id,
                ortomapa["projeto_id"],
                "indice_vegetacao",
                f"Indice {index_name}",
                f"Analise de vegetacao com indice {index_name}",
                json.dumps(params, ensure_ascii=False),
                index_path,
                json.dumps(stats, ensure_ascii=False),
                "agente_vegetacao",
                "concluido",
                elapsed,
            ),
            commit=True,
        )

        logger.info(
            "Vegetation analysis complete. analise_id=%s elapsed=%.1fs",
            analise_id,
            elapsed,
        )

        # --- 10. Return result ---
        return {
            "analise_id": analise_id,
            "index_name": index_name,
            "index_raster": index_path,
            "classified_raster": cls_path,
            "statistics": stats,
            "elapsed_seconds": elapsed,
        }
