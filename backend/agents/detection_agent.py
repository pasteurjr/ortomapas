"""
Object detection agent.

Uses YOLOv8 to detect objects in an ortomapa, tiling the raster into
640x640 patches, running inference, converting pixel coordinates to
geographic coordinates, applying cross-tile NMS, and saving results
as GeoJSON.
"""

import json
import logging
import math
import os
import time
from datetime import datetime

import numpy as np

try:
    import rasterio
    from rasterio.windows import Window
except ImportError:
    rasterio = None

from backend.database.connection import execute_query
from backend.config import ANALISES_DIR

logger = logging.getLogger("agent.detection")

# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def _pixel_to_geo(transform, col, row):
    """Convert pixel (col, row) to geographic (x, y) using an affine transform."""
    x = transform.c + col * transform.a + row * transform.b
    y = transform.f + col * transform.d + row * transform.e
    return x, y


def _iou(box_a, box_b):
    """Compute IoU between two boxes [x1, y1, x2, y2]."""
    x1 = max(box_a[0], box_b[0])
    y1 = max(box_a[1], box_b[1])
    x2 = min(box_a[2], box_b[2])
    y2 = min(box_a[3], box_b[3])
    inter = max(0, x2 - x1) * max(0, y2 - y1)
    area_a = (box_a[2] - box_a[0]) * (box_a[3] - box_a[1])
    area_b = (box_b[2] - box_b[0]) * (box_b[3] - box_b[1])
    union = area_a + area_b - inter
    return inter / union if union > 0 else 0.0


def _nms(detections, iou_threshold=0.5):
    """
    Non-maximum suppression across tiles.
    Each detection: dict with 'bbox_geo' [x1,y1,x2,y2], 'confidence', 'class_name'.
    """
    if not detections:
        return detections

    # Sort by confidence descending
    detections = sorted(detections, key=lambda d: d["confidence"], reverse=True)
    keep = []
    for det in detections:
        suppress = False
        for kept in keep:
            if det["class_name"] == kept["class_name"]:
                if _iou(det["bbox_geo"], kept["bbox_geo"]) >= iou_threshold:
                    suppress = True
                    break
        if not suppress:
            keep.append(det)
    return keep


class DetectionAgent:
    """Detect objects in an ortomapa using YOLOv8."""

    TILE_SIZE = 640
    OVERLAP = 64  # pixels of overlap between adjacent tiles

    def execute(self, task):
        """
        Parameters inside task['parametros'] (JSON):
            model_path           – path to YOLOv8 weights (default yolov8n.pt)
            confidence_threshold – detection confidence cutoff (default 0.25)
            iou_threshold        – NMS IoU threshold (default 0.5)
            classes              – list of class ids to filter (optional)
        """
        t0 = time.time()

        if rasterio is None:
            raise RuntimeError("rasterio is not installed")

        try:
            from ultralytics import YOLO
        except ImportError:
            raise RuntimeError(
                "ultralytics is not installed. Install with: pip install ultralytics"
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

        model_path = params.get("model_path", "yolov8n.pt")
        conf_threshold = float(params.get("confidence_threshold", 0.25))
        iou_threshold = float(params.get("iou_threshold", 0.5))
        filter_classes = params.get("classes")  # list of int or None

        logger.info(
            "Detection on ortomapa %d model=%s conf=%.2f",
            ortomapa_id,
            model_path,
            conf_threshold,
        )

        # --- 3. Load model ---
        model = YOLO(model_path)

        # --- 4. Tile the raster and run inference ---
        all_detections = []

        with rasterio.open(raster_path) as src:
            img_h = src.height
            img_w = src.width
            transform = src.transform
            crs = src.crs

            step = self.TILE_SIZE - self.OVERLAP

            n_tiles_x = max(1, math.ceil((img_w - self.OVERLAP) / step))
            n_tiles_y = max(1, math.ceil((img_h - self.OVERLAP) / step))
            total_tiles = n_tiles_x * n_tiles_y

            logger.info(
                "Image %dx%d -> %d tiles (%dx%d grid)",
                img_w, img_h, total_tiles, n_tiles_x, n_tiles_y,
            )

            tile_idx = 0
            for ty in range(n_tiles_y):
                for tx in range(n_tiles_x):
                    tile_idx += 1
                    col_off = tx * step
                    row_off = ty * step

                    # Clamp to image bounds
                    win_w = min(self.TILE_SIZE, img_w - col_off)
                    win_h = min(self.TILE_SIZE, img_h - row_off)
                    if win_w < 32 or win_h < 32:
                        continue

                    window = Window(col_off, row_off, win_w, win_h)
                    # Read RGB (bands 1-3)
                    num_bands = min(src.count, 3)
                    tile_data = src.read(
                        list(range(1, num_bands + 1)), window=window
                    )  # shape (C, H, W)

                    # Pad to TILE_SIZE if needed
                    if win_w < self.TILE_SIZE or win_h < self.TILE_SIZE:
                        padded = np.zeros(
                            (num_bands, self.TILE_SIZE, self.TILE_SIZE),
                            dtype=tile_data.dtype,
                        )
                        padded[:, :win_h, :win_w] = tile_data
                        tile_data = padded

                    # Convert to HWC for YOLO (expects uint8 RGB image)
                    tile_rgb = np.transpose(tile_data, (1, 2, 0))
                    if tile_rgb.dtype != np.uint8:
                        tile_rgb = np.clip(tile_rgb, 0, 255).astype(np.uint8)
                    # Ensure 3 channels
                    if tile_rgb.shape[2] == 1:
                        tile_rgb = np.repeat(tile_rgb, 3, axis=2)
                    elif tile_rgb.shape[2] == 2:
                        tile_rgb = np.concatenate(
                            [tile_rgb, tile_rgb[:, :, :1]], axis=2
                        )

                    # --- 5. Inference ---
                    results = model.predict(
                        tile_rgb,
                        conf=conf_threshold,
                        verbose=False,
                        imgsz=self.TILE_SIZE,
                    )

                    for r in results:
                        boxes = r.boxes
                        if boxes is None or len(boxes) == 0:
                            continue
                        for i in range(len(boxes)):
                            cls_id = int(boxes.cls[i].item())
                            if filter_classes and cls_id not in filter_classes:
                                continue
                            conf = float(boxes.conf[i].item())
                            # Box in tile pixel coords (xyxy)
                            x1t, y1t, x2t, y2t = boxes.xyxy[i].tolist()

                            # Convert to full-image pixel coords
                            x1_img = col_off + x1t
                            y1_img = row_off + y1t
                            x2_img = col_off + x2t
                            y2_img = row_off + y2t

                            # --- 6. Pixel -> geographic ---
                            gx1, gy1 = _pixel_to_geo(transform, x1_img, y1_img)
                            gx2, gy2 = _pixel_to_geo(transform, x2_img, y2_img)

                            # Centre point
                            cx = (gx1 + gx2) / 2.0
                            cy = (gy1 + gy2) / 2.0

                            class_name = model.names.get(cls_id, f"class_{cls_id}")
                            all_detections.append(
                                {
                                    "class_id": cls_id,
                                    "class_name": class_name,
                                    "confidence": round(conf, 4),
                                    "bbox_pixel": [
                                        round(x1_img, 1),
                                        round(y1_img, 1),
                                        round(x2_img, 1),
                                        round(y2_img, 1),
                                    ],
                                    "bbox_geo": [gx1, gy1, gx2, gy2],
                                    "center_geo": [cx, cy],
                                }
                            )

                    if tile_idx % 50 == 0:
                        logger.info(
                            "  tile %d/%d – %d detections so far",
                            tile_idx,
                            total_tiles,
                            len(all_detections),
                        )

        # --- 7. NMS across tiles ---
        before_nms = len(all_detections)
        all_detections = _nms(all_detections, iou_threshold)
        logger.info(
            "NMS: %d -> %d detections (iou=%.2f)",
            before_nms,
            len(all_detections),
            iou_threshold,
        )

        # --- 8. Save GeoJSON ---
        os.makedirs(ANALISES_DIR, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        geojson_filename = f"det_{ortomapa_id}_{ts}.geojson"
        geojson_path = os.path.join(ANALISES_DIR, geojson_filename)

        crs_str = str(crs) if crs else "EPSG:4326"

        features = []
        for det in all_detections:
            bx1, by1, bx2, by2 = det["bbox_geo"]
            cx, cy = det["center_geo"]
            features.append(
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [cx, cy],
                    },
                    "properties": {
                        "class_id": det["class_id"],
                        "class_name": det["class_name"],
                        "confidence": det["confidence"],
                        "bbox": [bx1, by1, bx2, by2],
                    },
                }
            )

        geojson = {
            "type": "FeatureCollection",
            "crs": {"type": "name", "properties": {"name": crs_str}},
            "features": features,
        }

        with open(geojson_path, "w", encoding="utf-8") as f:
            json.dump(geojson, f, ensure_ascii=False, indent=2)

        logger.info("GeoJSON saved: %s (%d features)", geojson_path, len(features))

        # --- Count per class ---
        class_counts = {}
        for det in all_detections:
            cn = det["class_name"]
            class_counts[cn] = class_counts.get(cn, 0) + 1

        elapsed = round(time.time() - t0, 2)

        summary = {
            "total_detections": len(all_detections),
            "class_counts": class_counts,
            "tiles_processed": total_tiles,
            "model": model_path,
            "confidence_threshold": conf_threshold,
            "iou_threshold": iou_threshold,
        }

        # --- 9. Register in analises table ---
        analise_id = execute_query(
            """
            INSERT INTO analises
                (ortomapa_id, projeto_id, tipo_analise, nome, descricao,
                 parametros, resultado_path, resultado_json,
                 modelo_ia, agente_ia, status, tempo_processamento_seg)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                ortomapa_id,
                ortomapa["projeto_id"],
                "deteccao_objetos",
                "Deteccao de Objetos YOLOv8",
                f"Deteccao com modelo {model_path}, conf>{conf_threshold}",
                json.dumps(params, ensure_ascii=False),
                geojson_path,
                json.dumps(summary, ensure_ascii=False),
                model_path,
                "agente_deteccao",
                "concluido",
                elapsed,
            ),
            commit=True,
        )

        # Register individual detections in anotacoes table
        for det in all_detections:
            cx, cy = det["center_geo"]
            bx1, by1, bx2, by2 = det["bbox_geo"]
            wkt_bbox = (
                f"POLYGON(({bx1} {by1}, {bx2} {by1}, {bx2} {by2}, {bx1} {by2}, {bx1} {by1}))"
            )
            try:
                execute_query(
                    """
                    INSERT INTO anotacoes
                        (ortomapa_id, analise_id, tipo, categoria, rotulo,
                         geometria_wkt, centro_lat, centro_lon, confianca, fonte, criado_por)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        ortomapa_id,
                        analise_id,
                        "bbox",
                        det["class_name"],
                        f"{det['class_name']} ({det['confidence']:.2f})",
                        wkt_bbox,
                        cy,
                        cx,
                        det["confidence"],
                        "ia",
                        "agente_deteccao",
                    ),
                    commit=True,
                )
            except Exception as e:
                logger.warning("Failed to insert anotacao: %s", e)

        logger.info(
            "Detection complete. analise_id=%s detections=%d elapsed=%.1fs",
            analise_id,
            len(all_detections),
            elapsed,
        )

        # --- 10. Return summary ---
        return {
            "analise_id": analise_id,
            "geojson_path": geojson_path,
            "total_detections": len(all_detections),
            "class_counts": class_counts,
            "elapsed_seconds": elapsed,
        }
