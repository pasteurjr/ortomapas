"""Spatial analysis tools router."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
import logging
import json
from datetime import datetime

from backend.config import ANALISES_DIR, DATA_DIR
from backend.tools import gdal_tools, raster_analysis, change_detection, classification, hydrology, volumetry, segmentation

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/tools", tags=["tools"])

# --- Request Models ---

class ClipRequest(BaseModel):
    input_path: str
    output_name: str
    bbox: Optional[Dict[str, float]] = None  # {north, south, east, west}
    polygon_wkt: Optional[str] = None

class ReprojectRequest(BaseModel):
    input_path: str
    output_name: str
    target_epsg: int

class MergeRequest(BaseModel):
    input_paths: List[str]
    output_name: str

class ContourRequest(BaseModel):
    input_path: str
    output_name: str
    interval: float = 5.0

class HillshadeRequest(BaseModel):
    input_path: str
    output_name: str
    azimuth: float = 315
    altitude: float = 45

class VegetationRequest(BaseModel):
    input_path: str
    output_name: str
    index_name: str = "VARI"

class SlopeRequest(BaseModel):
    input_path: str
    output_name: str

class AspectRequest(BaseModel):
    input_path: str
    output_name: str

class StatisticsRequest(BaseModel):
    input_path: str

class ZonalStatsRequest(BaseModel):
    raster_path: str
    zones_geojson_path: str

class CalculatorRequest(BaseModel):
    expression: str
    input_paths: Dict[str, str]
    output_name: str

class ChangeDetectionRequest(BaseModel):
    raster1_path: str
    raster2_path: str
    output_name: str
    threshold: float = 30.0

class ClassifyRequest(BaseModel):
    ortomapa_path: str
    algorithm: str = "kmeans"
    n_clusters: int = 7
    training_samples: Optional[List[Dict[str, Any]]] = None

class WatershedRequest(BaseModel):
    dtm_path: str
    pour_point: Dict[str, float]  # {lat, lon}
    output_name: str

class StreamsRequest(BaseModel):
    dtm_path: str
    output_name: str
    threshold: int = 100

class VolumeRequest(BaseModel):
    dsm_path: str
    reference_elevation: float
    output_name: Optional[str] = None

class DSMDiffRequest(BaseModel):
    dsm1_path: str
    dsm2_path: str
    output_name: str

class SegmentRequest(BaseModel):
    input_path: str
    output_name: str
    n_clusters: int = 7

def _resolve_path(path: str) -> str:
    """Resolve relative path to absolute.

    Handles three cases:
    1. Absolute path: returned as-is
    2. Path with 'data/' prefix (e.g., 'data/ortomapas/file.tif'): strip prefix, join with DATA_DIR
    3. Relative path (e.g., 'ortomapas/file.tif'): join with DATA_DIR
    """
    if os.path.isabs(path):
        return path
    # Strip leading 'data/' prefix if present, since DATA_DIR already points to the data folder
    if path.startswith("data/") or path.startswith("data\\"):
        path = path[5:]  # len("data/") == 5
    return os.path.join(DATA_DIR, path)

def _output_path(name: str, ext: str = ".tif") -> str:
    """Generate output path in analises directory."""
    if not name.endswith(ext):
        name += ext
    return os.path.join(ANALISES_DIR, name)

# --- Endpoints ---

@router.post("/clip")
async def clip_raster(req: ClipRequest):
    try:
        input_path = _resolve_path(req.input_path)
        output = _output_path(req.output_name)
        bbox = None
        if req.bbox:
            bbox = (req.bbox["west"], req.bbox["south"], req.bbox["east"], req.bbox["north"])
        result = gdal_tools.clip_raster(input_path, output, bbox=bbox, polygon_wkt=req.polygon_wkt)
        return {"status": "success", "output_path": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reproject")
async def reproject_raster(req: ReprojectRequest):
    try:
        input_path = _resolve_path(req.input_path)
        output = _output_path(req.output_name)
        result = gdal_tools.reproject_raster(input_path, output, req.target_epsg)
        return {"status": "success", "output_path": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/merge")
async def merge_rasters(req: MergeRequest):
    try:
        inputs = [_resolve_path(p) for p in req.input_paths]
        output = _output_path(req.output_name)
        result = gdal_tools.merge_rasters(inputs, output)
        return {"status": "success", "output_path": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/contours")
async def generate_contours(req: ContourRequest):
    try:
        input_path = _resolve_path(req.input_path)
        output = _output_path(req.output_name, ".geojson")
        result = gdal_tools.generate_contours(input_path, output, interval=req.interval)
        return {"status": "success", "output_path": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/hillshade")
async def create_hillshade(req: HillshadeRequest):
    try:
        input_path = _resolve_path(req.input_path)
        output = _output_path(req.output_name)
        result = gdal_tools.hillshade(input_path, output, azimuth=req.azimuth, altitude=req.altitude)
        return {"status": "success", "output_path": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/vegetation")
async def calc_vegetation_index(req: VegetationRequest):
    try:
        input_path = _resolve_path(req.input_path)
        output = _output_path(req.output_name)
        result = raster_analysis.calc_vegetation_index(input_path, output, index_name=req.index_name)
        stats = raster_analysis.raster_statistics(output)
        return {"status": "success", "output_path": result, "statistics": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/slope")
async def calc_slope(req: SlopeRequest):
    try:
        input_path = _resolve_path(req.input_path)
        output = _output_path(req.output_name)
        result = raster_analysis.calc_slope(input_path, output)
        stats = raster_analysis.raster_statistics(output)
        return {"status": "success", "output_path": result, "statistics": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/aspect")
async def calc_aspect(req: AspectRequest):
    try:
        input_path = _resolve_path(req.input_path)
        output = _output_path(req.output_name)
        result = raster_analysis.calc_aspect(input_path, output)
        stats = raster_analysis.raster_statistics(output)
        return {"status": "success", "output_path": result, "statistics": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/statistics")
async def get_statistics(req: StatisticsRequest):
    try:
        input_path = _resolve_path(req.input_path)
        stats = raster_analysis.raster_statistics(input_path)
        return {"status": "success", "statistics": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/zonal-stats")
async def get_zonal_stats(req: ZonalStatsRequest):
    try:
        raster = _resolve_path(req.raster_path)
        zones = _resolve_path(req.zones_geojson_path)
        result = raster_analysis.zonal_statistics(raster, zones)
        return {"status": "success", "statistics": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/calculator")
async def raster_calculator(req: CalculatorRequest):
    try:
        inputs = {k: _resolve_path(v) for k, v in req.input_paths.items()}
        output = _output_path(req.output_name)
        result = raster_analysis.raster_calculator(req.expression, inputs, output)
        return {"status": "success", "output_path": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/changes")
async def detect_changes(req: ChangeDetectionRequest):
    try:
        r1 = _resolve_path(req.raster1_path)
        r2 = _resolve_path(req.raster2_path)
        output = _output_path(req.output_name)
        change_detection.detect_changes(r1, r2, output, threshold=req.threshold)
        stats = change_detection.change_statistics(output)
        return {"status": "success", "output_path": output, "statistics": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/classify")
async def classify_raster(req: ClassifyRequest):
    try:
        input_path = _resolve_path(req.ortomapa_path)
        output = _output_path(f"classified_{req.algorithm}")
        if req.algorithm == "kmeans":
            result = segmentation.segment_ortomapa(input_path, output, n_clusters=req.n_clusters)
        else:
            if req.training_samples:
                model_path = os.path.join(ANALISES_DIR, "model.joblib")
                classification.train_classifier(input_path, req.training_samples, algorithm=req.algorithm, output_model_path=model_path)
                result = classification.classify_raster(input_path, model_path, output)
            else:
                result = segmentation.segment_ortomapa(input_path, output, n_clusters=req.n_clusters)
        return {"status": "success", "output_path": output, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/hydrology/watershed")
async def delineate_watershed(req: WatershedRequest):
    try:
        dtm = _resolve_path(req.dtm_path)
        output = _output_path(req.output_name)
        result = hydrology.delineate_watershed(dtm, (req.pour_point["lat"], req.pour_point["lon"]), output)
        return {"status": "success", "output_path": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/hydrology/streams")
async def extract_streams(req: StreamsRequest):
    try:
        dtm = _resolve_path(req.dtm_path)
        # Generate intermediate products
        filled = _output_path(f"{req.output_name}_filled")
        flow_dir = _output_path(f"{req.output_name}_flowdir")
        flow_acc = _output_path(f"{req.output_name}_flowacc")
        output = _output_path(req.output_name, ".geojson")

        hydrology.fill_sinks(dtm, filled)
        hydrology.flow_direction(filled, flow_dir)
        hydrology.flow_accumulation(flow_dir, flow_acc)
        result = hydrology.extract_streams(flow_acc, output, threshold=req.threshold)
        return {"status": "success", "output_path": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/volume")
async def calc_volume(req: VolumeRequest):
    try:
        dsm = _resolve_path(req.dsm_path)
        output = _output_path(req.output_name) if req.output_name else None
        result = volumetry.calc_volume(dsm, req.reference_elevation, output)
        return {"status": "success", **result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/volume/difference")
async def dsm_diff(req: DSMDiffRequest):
    try:
        d1 = _resolve_path(req.dsm1_path)
        d2 = _resolve_path(req.dsm2_path)
        output = _output_path(req.output_name)
        result = volumetry.cut_fill_analysis(d1, d2, output)
        return {"status": "success", **result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/segment")
async def segment_raster(req: SegmentRequest):
    try:
        input_path = _resolve_path(req.input_path)
        output = _output_path(req.output_name)
        result = segmentation.segment_ortomapa(input_path, output, n_clusters=req.n_clusters)
        return {"status": "success", **result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
