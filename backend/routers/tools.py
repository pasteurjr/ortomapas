"""Spatial analysis tools router."""
from fastapi import APIRouter, HTTPException, Depends
from pathlib import Path
from uuid import uuid4
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import os
import logging
import json
import rasterio
from rasterio.enums import Resampling
from datetime import datetime

from backend.config import ANALISES_DIR, DATA_DIR
from backend.tools import gdal_tools, raster_analysis, change_detection, classification, hydrology, volumetry, segmentation
from backend.utils.resource_access import authorize_tools, data_path, tool_context
from backend.utils.analysis_products import terrain_source, publish_terrain, publish_contours
from backend.utils.terrain_aoi import prepare_aoi, mask_derivative
from backend.utils.contour_products import contour_result, contour_input
from backend.utils.raster_metrics import metric_jacobian

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/tools", tags=["tools"], dependencies=[Depends(authorize_tools)])

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

class HillshadeRequest(BaseModel):
    input_path: str
    output_name: str
    azimuth: float = Field(default=315, ge=0, le=360)
    altitude: float = Field(default=45, ge=0, le=90)
    ortomapa_id: Optional[int] = None
    projeto_id: Optional[int] = None
    aoi: Optional[dict] = None

class VegetationRequest(BaseModel):
    input_path: str
    output_name: str
    index_name: str = "VARI"

class SlopeRequest(BaseModel):
    input_path: str
    output_name: str
    ortomapa_id: Optional[int] = None
    projeto_id: Optional[int] = None
    aoi: Optional[dict] = None

class AspectRequest(SlopeRequest):
    pass

class ContourRequest(SlopeRequest):
    interval: float = Field(default=5.0, gt=0, le=10000)

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
    threshold: int = Field(default=100, gt=0, description="Acumulacao minima de fluxo (> 0)")

class VolumeRequest(BaseModel):
    dsm_path: str
    reference_elevation: float = Field(allow_inf_nan=False)
    output_name: Optional[str] = None
    ortomapa_id: Optional[int] = None
    projeto_id: Optional[int] = None
    aoi: Optional[dict] = None

    @property
    def input_path(self):
        return self.dsm_path

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
    return str(data_path(path))

def _output_path(name: str, ext: str = ".tif") -> str:
    """Generate output path in analises directory."""
    context = tool_context.get()
    if not context:
        raise HTTPException(status_code=403, detail="Contexto de projeto necessario")
    if Path(name).name != name or "\\" in name:
        raise HTTPException(status_code=422, detail="Nome de arquivo invalido")
    if not name.endswith(ext):
        name += ext
    folder = Path(ANALISES_DIR) / "projetos" / str(context[1])
    folder.mkdir(parents=True, exist_ok=True)
    return str(folder / (uuid4().hex + "_" + name))

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
        source = terrain_source(req)
        input_path = _resolve_path(req.input_path)
        import rasterio
        with rasterio.open(input_path) as ds:
            metric_jacobian(ds.crs, ds.transform)
            crs = ds.crs
        aoi = prepare_aoi(input_path, req.aoi)
        output = _output_path(req.output_name, ".geojson")
        with contour_input(input_path,aoi) as model:
            result = gdal_tools.generate_contours(model, output, interval=req.interval)
        metadata = contour_result(output, crs, req.interval, aoi)
        analysis = publish_contours(source, output, metadata, req.model_dump()) if source else None
        return {"status": "success", "output_path": result, "geojson": metadata['geojson'], "analise": analysis, "statistics": metadata['stats']}
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/hillshade")
async def create_hillshade(req: HillshadeRequest):
    try:
        source=terrain_source(req)
        input_path = _resolve_path(req.input_path)
        aoi = prepare_aoi(input_path, req.aoi)
        output = _output_path(req.output_name)
        result = gdal_tools.hillshade(input_path, output, azimuth=req.azimuth, altitude=req.altitude)
        mask_derivative(output, aoi)
        stats=raster_analysis.raster_statistics(output)
        analysis=publish_terrain(source,'hillshade',output,stats,req.model_dump(),aoi) if source else None
        return {"status": "success", "output_path": result, "statistics": stats, "analise": analysis}
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
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
        source=terrain_source(req)
        input_path = _resolve_path(req.input_path)
        aoi = prepare_aoi(input_path, req.aoi)
        output = _output_path(req.output_name)
        result = raster_analysis.calc_slope(input_path, output)
        mask_derivative(output, aoi)
        stats = raster_analysis.raster_statistics(output)
        analysis=publish_terrain(source,'slope',output,stats,req.model_dump(),aoi) if source else None
        return {"status": "success", "output_path": result, "statistics": stats, "analise": analysis}
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/aspect")
async def calc_aspect(req: AspectRequest):
    try:
        source=terrain_source(req)
        input_path = _resolve_path(req.input_path)
        aoi = prepare_aoi(input_path, req.aoi)
        output = _output_path(req.output_name)
        result = raster_analysis.calc_aspect(input_path, output)
        mask_derivative(output, aoi)
        stats = raster_analysis.raster_statistics(output)
        analysis=publish_terrain(source,'aspect',output,stats,req.model_dump(),aoi) if source else None
        return {"status": "success", "output_path": result, "statistics": stats, "analise": analysis}
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
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
        # O pipeline D8 usa estruturas em memoria; reduzimos rasters muito grandes
        # para manter tempo e memoria previsiveis, preservando a extensao espacial.
        with rasterio.open(dtm) as src:
            scale = min(1.0, 512 / max(src.width, src.height))
            if scale < 1.0:
                work = _output_path(f"{req.output_name}_resampled", ".tif")
                h, w = max(1, int(src.height * scale)), max(1, int(src.width * scale))
                profile = src.profile.copy(); profile.update(height=h, width=w, transform=src.transform * src.transform.scale(src.width / w, src.height / h))
                with rasterio.open(work, 'w', **profile) as dst: dst.write(src.read(1, out_shape=(h, w), resampling=Resampling.bilinear), 1)
                dtm = work
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
    except (FileNotFoundError, rasterio.errors.RasterioIOError) as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/volume")
async def calc_volume(req: VolumeRequest):
    try:
        source = terrain_source(req)
        dsm = _resolve_path(req.dsm_path)
        aoi = prepare_aoi(dsm, req.aoi)
        output = _output_path(req.output_name or 'volume') if req.output_name or source else None
        result = volumetry.calc_volume(dsm, req.reference_elevation, output, aoi)
        analysis = None
        if source:
            stats = raster_analysis.raster_statistics(output)
            stats['band_1'].update({key:value for key,value in result.items() if isinstance(value,(int,float)) and not isinstance(value,bool)})
            analysis = publish_terrain(source,'volume',output,stats,req.model_dump(),aoi)
        return {"status": "success", **result, "analise": analysis}
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
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
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
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
