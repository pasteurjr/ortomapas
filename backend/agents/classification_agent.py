"""
Land-cover classification agent.

Classifies each pixel of an ortomapa into one of seven land-cover classes
using either unsupervised K-Means or supervised Random Forest.
"""

import json
import logging
import os
import time
from datetime import datetime

import numpy as np

try:
    import rasterio
except ImportError:
    rasterio = None

try:
    from scipy.ndimage import generic_filter
except ImportError:
    generic_filter = None

try:
    from sklearn.cluster import KMeans
    from sklearn.ensemble import RandomForestClassifier
except ImportError:
    KMeans = None
    RandomForestClassifier = None

from backend.database.connection import execute_query
from backend.config import ANALISES_DIR

logger = logging.getLogger("agent.classification")


def _majority_filter(arr, size=3):
    """Apply a majority (mode) filter using a square kernel."""
    if generic_filter is not None:
        def _mode(values):
            vals, counts = np.unique(values.astype(int), return_counts=True)
            return vals[np.argmax(counts)]

        return generic_filter(arr.astype(float), _mode, size=size).astype(arr.dtype)
    else:
        # Fallback: no smoothing if scipy is unavailable
        logger.warning("scipy not available; skipping majority filter")
        return arr


class ClassificationAgent:
    """Land-cover classification from RGB ortomapa."""

    CLASS_NAMES = [
        "vegetacao_densa",
        "vegetacao_rasteira",
        "solo_exposto",
        "agua",
        "urbano",
        "agricola",
        "rocha",
    ]

    def execute(self, task):
        """
        Parameters inside task['parametros'] (JSON):
            algorithm         – 'kmeans' (default) or 'random_forest'
            n_clusters        – for kmeans (default 7)
            training_samples  – list of dicts with {class_id, pixels: [[row,col],...]}
                                required for random_forest
            smooth            – apply majority filter (default True)
        """
        t0 = time.time()

        if rasterio is None:
            raise RuntimeError("rasterio is not installed")
        if KMeans is None:
            raise RuntimeError(
                "scikit-learn is not installed. Install with: pip install scikit-learn"
            )

        # --- 1. Resolve ortomapa ---
        ortomapa_id = task["ortomapa_id"]
        ortomapa = execute_query(
            "SELECT * FROM ortomapas WHERE id = %s", (ortomapa_id,), fetch_one=True
        )
        if ortomapa is None:
            raise ValueError(f"Ortomapa {ortomapa_id} not found")

        raster_path = ortomapa["caminho_arquivo"]
        if not os.path.isfile(raster_path):
            raise FileNotFoundError(f"Raster not found: {raster_path}")

        # --- 2. Parse params ---
        params = task.get("parametros")
        if isinstance(params, str):
            params = json.loads(params)
        params = params or {}

        training_samples = params.get("training_samples")
        algorithm = params.get("algorithm", "kmeans")
        n_clusters = int(params.get("n_clusters", 7))
        do_smooth = params.get("smooth", True)

        if training_samples:
            algorithm = "random_forest"

        logger.info(
            "Classification ortomapa %d algorithm=%s", ortomapa_id, algorithm
        )

        # --- 3. Read raster and compute features ---
        with rasterio.open(raster_path) as src:
            r = src.read(1).astype(np.float64)
            g = src.read(2).astype(np.float64)
            b = src.read(3).astype(np.float64)
            profile = src.profile.copy()
            transform = src.transform
            pixel_area_m2 = abs(transform.a) * abs(transform.e)

        h, w = r.shape

        # --- 5. 6 features per pixel: R, G, B, VARI, TGI, ExG ---
        vari = np.where(
            (g + r - b) != 0, (g - r) / (g + r - b + 1e-10), 0.0
        )
        tgi = g - 0.39 * r - 0.61 * b
        exg = 2.0 * g - r - b

        # Stack into (n_pixels, 6) feature matrix
        features = np.stack([r, g, b, vari, tgi, exg], axis=-1)  # (H, W, 6)
        features_flat = features.reshape(-1, 6)

        # Handle NaN / inf
        features_flat = np.nan_to_num(features_flat, nan=0.0, posinf=0.0, neginf=0.0)

        # --- 4/5. Classification ---
        if algorithm == "random_forest" and training_samples:
            logger.info("Using supervised Random Forest with %d sample groups", len(training_samples))
            train_X = []
            train_y = []
            for sample in training_samples:
                class_id = int(sample["class_id"])
                for px in sample["pixels"]:
                    row, col = int(px[0]), int(px[1])
                    if 0 <= row < h and 0 <= col < w:
                        train_X.append(features[row, col])
                        train_y.append(class_id)

            if len(train_X) < 10:
                raise ValueError(
                    f"Not enough valid training samples ({len(train_X)}). Need at least 10."
                )

            train_X = np.array(train_X)
            train_y = np.array(train_y)

            clf = RandomForestClassifier(
                n_estimators=100, max_depth=20, n_jobs=-1, random_state=42
            )
            clf.fit(train_X, train_y)
            labels = clf.predict(features_flat)
        else:
            logger.info("Using unsupervised KMeans with %d clusters", n_clusters)
            # Sub-sample for speed on large images
            n_pixels = features_flat.shape[0]
            max_samples = 500_000
            if n_pixels > max_samples:
                idx = np.random.RandomState(42).choice(
                    n_pixels, max_samples, replace=False
                )
                sample_features = features_flat[idx]
            else:
                sample_features = features_flat

            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            kmeans.fit(sample_features)
            labels = kmeans.predict(features_flat)
            # KMeans labels are 0-based; shift to 1-based for consistency
            labels = labels + 1

        # --- 6. Reshape to image ---
        classified = labels.reshape(h, w).astype(np.uint8)

        # --- 7. Majority filter ---
        if do_smooth:
            logger.info("Applying 3x3 majority filter")
            classified = _majority_filter(classified, size=3)

        # --- 8. Write classified GeoTIFF ---
        os.makedirs(ANALISES_DIR, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        cls_filename = f"class_{algorithm}_{ortomapa_id}_{ts}.tif"
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

        # --- 9. Area per class ---
        unique_labels = np.unique(classified)
        class_stats = {}
        total_pixels = int(classified.size)
        for lbl in unique_labels:
            lbl_int = int(lbl)
            if lbl_int == 0:
                continue
            count = int(np.sum(classified == lbl))
            area_m2 = count * pixel_area_m2
            # Map label to class name if within range
            if 1 <= lbl_int <= len(self.CLASS_NAMES):
                name = self.CLASS_NAMES[lbl_int - 1]
            else:
                name = f"classe_{lbl_int}"
            class_stats[name] = {
                "class_id": lbl_int,
                "pixels": count,
                "area_m2": round(area_m2, 2),
                "area_ha": round(area_m2 / 10000.0, 4),
                "pct": round(100.0 * count / total_pixels, 2) if total_pixels > 0 else 0,
            }

        elapsed = round(time.time() - t0, 2)

        result_json = {
            "algorithm": algorithm,
            "n_classes": len(class_stats),
            "classes": class_stats,
            "total_pixels": total_pixels,
            "smoothed": do_smooth,
        }

        # --- 10. Register in analises table ---
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
                "classificacao_solo",
                f"Classificacao {algorithm}",
                f"Classificacao de cobertura do solo ({algorithm})",
                json.dumps(params, ensure_ascii=False),
                cls_path,
                json.dumps(result_json, ensure_ascii=False),
                "agente_classificacao",
                "concluido",
                elapsed,
            ),
            commit=True,
        )

        logger.info(
            "Classification complete. analise_id=%s elapsed=%.1fs", analise_id, elapsed
        )

        # --- 11. Return ---
        return {
            "analise_id": analise_id,
            "classified_raster": cls_path,
            "algorithm": algorithm,
            "class_statistics": class_stats,
            "elapsed_seconds": elapsed,
        }
