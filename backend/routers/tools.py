"""Spatial analysis tools router."""
from fastapi import APIRouter, HTTPException, Depends
from pathlib import Path
from uuid import uuid4
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import os
import logging
import json
import tempfile
import numpy as np
import rasterio
from rasterio.enums import Resampling
from datetime import datetime
from pyproj import Transformer

from backend.config import ANALISES_DIR, DATA_DIR
from backend.tools import gdal_tools, raster_analysis, change_detection, classification, hydrology, volumetry, segmentation
from backend.utils.resource_access import authorize_tools, data_path, tool_context
from backend.utils.analysis_products import (terrain_source, publish_terrain, publish_contours,
                                             image_source, publish_image_analysis, publish_hydrology)
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
    ortomapa_id: Optional[int] = None
    projeto_id: Optional[int] = None
    aoi: Optional[dict] = None

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
    n_clusters: int = Field(default=7, ge=2, le=12)
    training_samples: Optional[List[Dict[str, Any]]] = None
    output_name: Optional[str] = None
    ortomapa_id: Optional[int] = None
    projeto_id: Optional[int] = None
    aoi: Optional[dict] = None

class WatershedRequest(BaseModel):
    dtm_path: str
    pour_point: Dict[str, float]  # {lat, lon}
    output_name: str
    ortomapa_id: Optional[int] = None
    projeto_id: Optional[int] = None
    snap_radius_m: float = Field(default=5, ge=0, le=1000, allow_inf_nan=False)
    max_dimension: int = Field(default=1024, ge=128, le=4096)

    @property
    def input_path(self): return self.dtm_path

class StreamsRequest(BaseModel):
    dtm_path: str
    output_name: str
    minimum_area_m2: float = Field(default=100, gt=0, allow_inf_nan=False)
    threshold: Optional[int] = Field(default=None, gt=0, description="Compatibilidade: acumulacao minima em celulas")
    ortomapa_id: Optional[int] = None
    projeto_id: Optional[int] = None
    max_dimension: int = Field(default=1024, ge=128, le=4096)

    @property
    def input_path(self): return self.dtm_path

class TWIRequest(BaseModel):
    dtm_path: str
    output_name: str
    ortomapa_id: Optional[int] = None
    projeto_id: Optional[int] = None
    max_dimension: int = Field(default=1024, ge=128, le=4096)

    @property
    def input_path(self): return self.dtm_path

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
    ortomapa_antes_id: int
    ortomapa_depois_id: int
    projeto_id: int
    threshold: float = Field(default=0.1, ge=0, allow_inf_nan=False)
    aoi: Optional[dict] = None

class SegmentRequest(BaseModel):
    input_path: str
    output_name: str
    n_clusters: int = Field(default=7, ge=2, le=12)

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
        source=image_source(req,req.input_path)
        input_path = _resolve_path(req.input_path)
        aoi=prepare_aoi(input_path,req.aoi)
        output = _output_path(req.output_name)
        result = raster_analysis.calc_vegetation_index(input_path, output, index_name=req.index_name,aoi=aoi)
        stats = raster_analysis.raster_statistics(output)
        analysis=publish_image_analysis(source,'vegetation',output,stats,req.model_dump(),aoi) if source else None
        return {"status": "success", "output_path": result, "statistics": stats,"analise":analysis}
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=422,detail=str(e))
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
        source=image_source(req,req.ortomapa_path)
        input_path = _resolve_path(req.ortomapa_path)
        aoi=prepare_aoi(input_path,req.aoi)
        algorithm=req.algorithm.lower()
        output = _output_path(req.output_name or f"classified_{algorithm}")
        analysis=None
        if algorithm == "kmeans":
            result = segmentation.segment_ortomapa(input_path, output, n_clusters=req.n_clusters,aoi=aoi)
            if source:
                stats=raster_analysis.raster_statistics(output)
                analysis=publish_image_analysis(source,'classification',output,stats,req.model_dump(),aoi,result)
        else:
            if algorithm not in {'random_forest','svm'}:
                raise ValueError('Algoritmo deve ser kmeans, random_forest ou svm')
            if req.training_samples:
                model_path = os.path.join(ANALISES_DIR, "model.joblib")
                training=classification.train_classifier(input_path,req.training_samples,algorithm=algorithm,output_model_path=model_path)
                classification.classify_raster(input_path,model_path,output)
                result={"output_path":output,"training":training}
            else:
                raise ValueError('Classificacao supervisionada exige amostras rotuladas')
        return {"status": "success", "output_path": output, **result,"analise":analysis}
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=422,detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/hydrology/watershed")
async def delineate_watershed(req: WatershedRequest):
    try:
        source=terrain_source(req);dtm=_resolve_path(req.dtm_path);output=_output_path(req.output_name)
        lat=float(req.pour_point['lat']);lon=float(req.pour_point['lon'])
        if not np.isfinite([lat,lon]).all() or not -90<=lat<=90 or not -180<=lon<=180:
            raise ValueError('Exutorio deve conter latitude/longitude WGS84 validas')
        with tempfile.TemporaryDirectory(prefix='ortomapas_hydro_') as folder:
            work=os.path.join(folder,'dem.tif');filled=os.path.join(folder,'filled.tif')
            direction=os.path.join(folder,'direction.tif');accumulation=os.path.join(folder,'accumulation.tif')
            grid=hydrology.prepare_dem(dtm,work,req.max_dimension);hydrology.fill_sinks(work,filled)
            hydrology.flow_direction(filled,direction);hydrology.flow_accumulation(direction,accumulation)
            with rasterio.open(work) as dataset:
                forward=Transformer.from_crs(4326,dataset.crs,always_xy=True);reverse=Transformer.from_crs(dataset.crs,4326,always_xy=True)
            x,y=forward.transform(lon,lat);snap=hydrology.snap_pour_point(accumulation,x,y,req.snap_radius_m)
            result=hydrology.watershed_from_flow(direction,output,snap['row'],snap['col'])
            snapped_lon,snapped_lat=reverse.transform(*snap['snapped_xy'])
        result.update(working_grid=grid,requested_outlet={'lat':lat,'lon':lon},
                      snapped_outlet={'lat':snapped_lat,'lon':snapped_lon,'distance_m':snap['snap_distance_m'],
                                      'accumulation_cells':snap['accumulation_cells']})
        analysis=publish_hydrology(source,'watershed',output,result,req.model_dump()) if source else None
        return {"status":"success",**result,"analise":analysis}
    except HTTPException:
        raise
    except (ValueError,KeyError,TypeError) as e:
        raise HTTPException(status_code=422,detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/hydrology/streams")
async def extract_streams(req: StreamsRequest):
    try:
        source=terrain_source(req);dtm=_resolve_path(req.dtm_path);output=_output_path(req.output_name,'.geojson')
        with tempfile.TemporaryDirectory(prefix='ortomapas_hydro_') as folder:
            work=os.path.join(folder,'dem.tif');filled=os.path.join(folder,'filled.tif')
            direction=os.path.join(folder,'direction.tif');accumulation=os.path.join(folder,'accumulation.tif')
            grid=hydrology.prepare_dem(dtm,work,req.max_dimension);hydrology.fill_sinks(work,filled)
            hydrology.flow_direction(filled,direction);hydrology.flow_accumulation(direction,accumulation)
            minimum=req.threshold*grid['pixel_area_m2'] if req.threshold is not None else req.minimum_area_m2
            result=hydrology.extract_stream_lines(accumulation,direction,output,minimum)
        result['working_grid']=grid
        analysis=publish_hydrology(source,'streams',output,result,req.model_dump()) if source else None
        return {"status":"success",**result,"analise":analysis}
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=422,detail=str(e))
    except (FileNotFoundError, rasterio.errors.RasterioIOError) as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post('/hydrology/twi')
async def topographic_wetness(req: TWIRequest):
    try:
        source=terrain_source(req);dtm=_resolve_path(req.dtm_path);output=_output_path(req.output_name)
        with tempfile.TemporaryDirectory(prefix='ortomapas_hydro_') as folder:
            work=os.path.join(folder,'dem.tif');filled=os.path.join(folder,'filled.tif')
            direction=os.path.join(folder,'direction.tif');accumulation=os.path.join(folder,'accumulation.tif');slope=os.path.join(folder,'slope.tif')
            grid=hydrology.prepare_dem(dtm,work,req.max_dimension);hydrology.fill_sinks(work,filled)
            hydrology.flow_direction(filled,direction);hydrology.flow_accumulation(direction,accumulation)
            raster_analysis.calc_slope(filled,slope);hydrology.calc_twi(slope,accumulation,output)
        stats=raster_analysis.raster_statistics(output);details={**stats['band_1'],'working_grid':grid}
        analysis=publish_hydrology(source,'twi',output,details,req.model_dump()) if source else None
        return {'status':'success','output_path':output,'statistics':stats,'working_grid':grid,'analise':analysis}
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=422,detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500,detail=str(e))

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
        from backend.utils.analysis_products import comparison_sources, publish_elevation_change
        before, after = comparison_sources(req)
        d1 = _resolve_path(req.dsm1_path)
        d2 = _resolve_path(req.dsm2_path)
        aoi = prepare_aoi(d1, req.aoi)
        output = _output_path(req.output_name)
        result = volumetry.cut_fill_analysis(d1, d2, output, req.threshold, aoi)
        stats = raster_analysis.raster_statistics(output)
        redundant = {'min_diff_m','max_diff_m','mean_diff_m','std_diff_m'}
        stats['band_1'].update({key:value for key,value in result.items() if key not in redundant
                                if isinstance(value,(int,float)) and not isinstance(value,bool)})
        analysis, comparison_id = publish_elevation_change(before, after, output, stats, req.model_dump(), aoi)
        return {"status": "success", **result, "analise": analysis, "comparacao_id": comparison_id}
    except HTTPException:
        raise
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
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
