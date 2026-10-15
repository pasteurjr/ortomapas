"""
Hydrology analysis tools for DTM/DSM rasters.

Implements sink filling, D8 flow direction, flow accumulation, stream
extraction, watershed delineation, and Topographic Wetness Index (TWI).
"""

import json
import heapq
import logging
from collections import deque

import numpy as np
import rasterio
from rasterio.features import shapes as rasterio_shapes
from rasterio.enums import Resampling
from rasterio.warp import transform_geom
from shapely.geometry import LineString, mapping, shape
from shapely.ops import linemerge, unary_union
from scipy.ndimage import gaussian_filter
from backend.utils.raster_metrics import metric_jacobian, terrain_gradient

logger = logging.getLogger(__name__)


def _strip_block_options(profile):
    for option in ('blockxsize','blockysize','tiled'):
        profile.pop(option,None)
    return profile

# D8 direction encoding (powers of 2, following ESRI convention):
#   32 64 128
#   16  0   1
#    8  4   2
#
# Neighbor offsets (row_offset, col_offset) indexed by direction value:
_D8_DIRS = {
    1:   (0,  1),
    2:   (1,  1),
    4:   (1,  0),
    8:   (1, -1),
    16:  (0, -1),
    32: (-1, -1),
    64: (-1,  0),
    128:(-1,  1),
}

_D8_VALUES = [1, 2, 4, 8, 16, 32, 64, 128]
_D8_OFFSETS = [(0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1), (-1, 0), (-1, 1)]


def fill_sinks(dtm_path: str, output_path: str) -> str:
    """
    Fill sinks in a DTM using an iterative approach (simplified Planchon-Darboux).

    Each iteration raises cells that are lower than all neighbours to the
    minimum neighbour value. Repeats until no changes occur.

    Parameters
    ----------
    dtm_path : str
        Input DTM raster.
    output_path : str
        Filled DTM output.

    Returns
    -------
    str
        output_path on success.
    """
    with rasterio.open(dtm_path) as src:
        dem = src.read(1, masked=True).astype(np.float64)
        profile = src.profile.copy()
        nodata = src.nodata
    values=np.asarray(dem);valid=~np.ma.getmaskarray(dem)&np.isfinite(values)
    if not valid.any():
        raise ValueError('Modelo de terreno sem celulas validas')
    filled=values.copy();rows,cols=filled.shape;visited=np.zeros((rows,cols),dtype=bool);heap=[]
    boundary=np.zeros_like(valid)
    boundary[[0,-1],:]=valid[[0,-1],:];boundary[:,[0,-1]]=valid[:,[0,-1]]
    padded=np.pad(valid,1,constant_values=False)
    adjacent_to_nodata=np.zeros_like(valid)
    for dr,dc in _D8_OFFSETS:
        adjacent_to_nodata |= valid & ~padded[1+dr:rows+1+dr,1+dc:cols+1+dc]
    boundary |= adjacent_to_nodata
    for row,col in np.argwhere(boundary):
        visited[row,col]=True;heapq.heappush(heap,(float(filled[row,col]),int(row),int(col)))
    epsilon=max(float(np.nanmax(values[valid])-np.nanmin(values[valid]))*1e-9,1e-6)
    raised=0
    while heap:
        elevation,row,col=heapq.heappop(heap)
        for dr,dc in _D8_OFFSETS:
            nr,nc=row+dr,col+dc
            if not (0<=nr<rows and 0<=nc<cols) or visited[nr,nc] or not valid[nr,nc]:
                continue
            visited[nr,nc]=True
            original=float(filled[nr,nc]);new=max(original,elevation+epsilon)
            if new>original: raised+=1;filled[nr,nc]=new
            heapq.heappush(heap,(new,nr,nc))
    filled[~valid]=nodata if nodata is not None else np.nan

    _strip_block_options(profile).update(dtype=rasterio.float32, count=1, compress="lzw")

    with rasterio.open(output_path, "w", **profile) as dst:
        dst.write(filled.astype(np.float32), 1)
        dst.update_tags(operation='priority-flood',raised_cells=raised,epsilon=epsilon)

    logger.info("Sink-filled DTM written to %s (raised=%d)", output_path, raised)
    return output_path


def flow_direction(dtm_path: str, output_path: str) -> str:
    """
    Compute D8 flow direction from a DTM.

    Each cell is assigned the direction (D8 encoding) towards the steepest
    downslope neighbour.

    Returns
    -------
    str
        output_path on success.
    """
    with rasterio.open(dtm_path) as src:
        dem = src.read(1).astype(np.float64)
        transform = src.transform
        profile = src.profile.copy()
        nodata = src.nodata
        crs = src.crs

    rows, cols = dem.shape
    matrix=metric_jacobian(crs,transform)
    distances=[float(np.linalg.norm(matrix@np.array([dc,dr]))) for dr,dc in _D8_OFFSETS]

    padded = np.pad(dem, 1, mode="constant", constant_values=np.nan)
    flow_dir = np.zeros((rows, cols), dtype=np.int16)

    max_slope = np.full((rows, cols), -np.inf)

    for i, (dr, dc) in enumerate(_D8_OFFSETS):
        neighbour = padded[1 + dr: rows + 1 + dr, 1 + dc: cols + 1 + dc]
        slope = (dem - neighbour) / distances[i]
        update_mask = np.isfinite(slope) & (slope > max_slope) & (slope > 0)
        max_slope[update_mask] = slope[update_mask]
        flow_dir[update_mask] = _D8_VALUES[i]

    # Flat areas and nodata get direction 0
    flow_dir[~np.isfinite(dem)]=0
    if nodata is not None: flow_dir[dem==nodata]=0

    _strip_block_options(profile).update(dtype=rasterio.int16, count=1, compress="lzw", nodata=0)

    with rasterio.open(output_path, "w", **profile) as dst:
        dst.write(flow_dir, 1)

    logger.info("Flow direction raster written to %s", output_path)
    return output_path


def flow_accumulation(flow_dir_path: str, output_path: str) -> str:
    """
    Compute flow accumulation from a D8 flow direction raster.

    Each cell's value represents the number of upstream cells that flow into it.

    Returns
    -------
    str
        output_path on success.
    """
    with rasterio.open(flow_dir_path) as src:
        fdir = src.read(1).astype(np.int16)
        profile = src.profile.copy()

    rows, cols = fdir.shape
    acc = np.ones((rows, cols), dtype=np.int32)  # each cell counts itself

    # Build receiver map: for each cell, find which cell it drains to
    # Then do topological sort (cells with no inflow first)
    inflow_count = np.zeros((rows, cols), dtype=np.int32)

    # Count how many cells flow into each cell
    for i, (dr, dc) in enumerate(_D8_OFFSETS):
        direction_val = _D8_VALUES[i]
        # Cells with this flow direction drain to (r+dr, c+dc)
        mask = fdir == direction_val
        r_src, c_src = np.where(mask)
        r_dst = r_src + dr
        c_dst = c_src + dc
        valid = (r_dst >= 0) & (r_dst < rows) & (c_dst >= 0) & (c_dst < cols)
        r_dst = r_dst[valid]
        c_dst = c_dst[valid]
        np.add.at(inflow_count,(r_dst,c_dst),1)

    # Topological sort using queue
    from collections import deque
    queue = deque()

    # Start with cells that have no inflow
    no_inflow = np.argwhere(inflow_count == 0)
    for r, c in no_inflow:
        queue.append((r, c))

    processed = np.zeros((rows, cols), dtype=bool)

    while queue:
        r, c = queue.popleft()
        if processed[r, c]:
            continue
        processed[r, c] = True

        direction = fdir[r, c]
        if direction == 0:
            continue

        # Find target cell
        if direction in _D8_DIRS:
            dr, dc_off = _D8_DIRS[direction]
            nr, nc = r + dr, c + dc_off
            if 0 <= nr < rows and 0 <= nc < cols:
                acc[nr, nc] += acc[r, c]
                inflow_count[nr, nc] -= 1
                if inflow_count[nr, nc] <= 0:
                    queue.append((nr, nc))

    _strip_block_options(profile).update(dtype=rasterio.int32, count=1, compress="lzw", nodata=0)

    with rasterio.open(output_path, "w", **profile) as dst:
        dst.write(acc, 1)

    logger.info("Flow accumulation raster written to %s", output_path)
    return output_path


def extract_streams(
    flow_acc_path: str,
    output_geojson_path: str,
    threshold: int = 100,
) -> str:
    """
    Extract stream network by thresholding flow accumulation and vectorizing.

    Parameters
    ----------
    flow_acc_path : str
        Flow accumulation raster.
    output_geojson_path : str
        Output GeoJSON file path.
    threshold : int
        Minimum accumulation to classify as stream.

    Returns
    -------
    str
        output_geojson_path on success.
    """
    with rasterio.open(flow_acc_path) as src:
        acc = src.read(1)
        transform = src.transform
        crs = src.crs

    stream_mask = (acc >= threshold).astype(np.uint8)

    features = []
    for geom, value in rasterio_shapes(stream_mask, mask=stream_mask == 1, transform=transform):
        features.append({
            "type": "Feature",
            "geometry": geom,
            "properties": {"stream": 1},
        })

    geojson = {
        "type": "FeatureCollection",
        "crs": {
            "type": "name",
            "properties": {"name": str(crs) if crs else "EPSG:4326"},
        },
        "features": features,
    }

    with open(output_geojson_path, "w") as f:
        json.dump(geojson, f)

    logger.info("Extracted %d stream features to %s", len(features), output_geojson_path)
    return output_geojson_path


def prepare_dem(dtm_path: str, output_path: str, max_dimension: int = 1024) -> dict:
    """Create a bounded, metric hydrology grid while preserving the source extent."""
    if not 128 <= max_dimension <= 4096:
        raise ValueError('Dimensao de trabalho deve estar entre 128 e 4096 pixels')
    with rasterio.open(dtm_path) as src:
        metric_jacobian(src.crs,src.transform)
        scale=min(1.0,max_dimension/max(src.width,src.height))
        width=max(1,int(round(src.width*scale)));height=max(1,int(round(src.height*scale)))
        transform=src.transform*src.transform.scale(src.width/width,src.height/height)
        values=src.read(1,out_shape=(height,width),masked=True,resampling=Resampling.bilinear)
        profile=src.profile.copy();source_shape=[src.height,src.width]
    valid=(~np.ma.getmaskarray(values)).astype(float);raw=np.ma.asarray(values).filled(0).astype(float)
    weights=gaussian_filter(valid,1,mode='nearest');smoothed=gaussian_filter(raw*valid,1,mode='nearest')/np.maximum(weights,1e-12)
    values=np.ma.array(smoothed,mask=weights<0.5)
    for option in ('blockxsize','blockysize','tiled'): profile.pop(option,None)
    profile.update(width=width,height=height,transform=transform,dtype='float32',count=1,compress='lzw',nodata=-9999)
    with rasterio.open(output_path,'w',**profile) as dst:
        dst.write(values.astype('float32').filled(-9999),1)
        dst.update_tags(operation='hydrology-working-grid',source_shape='x'.join(map(str,source_shape)),scale=scale,smoothing_sigma_cells=1)
    matrix=metric_jacobian(profile['crs'],transform);pixel_area=abs(float(np.linalg.det(matrix)))
    return {'source_shape':source_shape,'working_shape':[height,width],
            'scale':scale,'pixel_area_m2':pixel_area,'cell_size_m':float(np.sqrt(pixel_area)),'smoothing_sigma_cells':1}


def extract_stream_lines(flow_acc_path: str, flow_dir_path: str, output_geojson_path: str,
                         minimum_area_m2: float) -> dict:
    """Vectorize D8 receiver links whose upstream contributing area passes a metric threshold."""
    if not np.isfinite(minimum_area_m2) or minimum_area_m2 <= 0:
        raise ValueError('Area contribuinte minima deve ser positiva')
    with rasterio.open(flow_acc_path) as acc_src,rasterio.open(flow_dir_path) as dir_src:
        acc=acc_src.read(1);fdir=dir_src.read(1);transform=acc_src.transform;crs=acc_src.crs
    matrix=metric_jacobian(crs,transform);pixel_area=abs(float(np.linalg.det(matrix)))
    threshold=max(1,int(np.ceil(minimum_area_m2/pixel_area)));stream=acc>=threshold
    segments=[];length=0.0
    for direction,(dr,dc) in _D8_DIRS.items():
        rows,cols=np.where(stream&(fdir==direction))
        targets_r=rows+dr;targets_c=cols+dc
        keep=(targets_r>=0)&(targets_r<fdir.shape[0])&(targets_c>=0)&(targets_c<fdir.shape[1])
        rows,cols,targets_r,targets_c=rows[keep],cols[keep],targets_r[keep],targets_c[keep]
        keep=stream[targets_r,targets_c];rows,cols,targets_r,targets_c=rows[keep],cols[keep],targets_r[keep],targets_c[keep]
        step=float(np.linalg.norm(matrix@np.array([dc,dr])))
        for row,col,tr,tc in zip(rows,cols,targets_r,targets_c):
            x1,y1=rasterio.transform.xy(transform,int(row),int(col));x2,y2=rasterio.transform.xy(transform,int(tr),int(tc))
            segments.append(LineString([(x1,y1),(x2,y2)]));length+=step
    if not segments:
        raise ValueError('Nenhum canal atingiu a area contribuinte minima')
    merged=linemerge(unary_union(segments));parts=list(merged.geoms) if merged.geom_type=='MultiLineString' else [merged]
    features=[]
    for number,line in enumerate(parts,1):
        geometry=transform_geom(crs,'EPSG:4326',mapping(line),precision=8)
        features.append({'type':'Feature','geometry':geometry,'properties':{'segmento':number}})
    geojson={'type':'FeatureCollection','features':features}
    with open(output_geojson_path,'w',encoding='utf-8') as stream_file: json.dump(geojson,stream_file)
    return {'output_path':output_geojson_path,'geojson':geojson,'feature_count':len(features),
            'stream_cells':int(stream.sum()),'minimum_area_m2':minimum_area_m2,
            'threshold_cells':threshold,'total_length_m':length,'pixel_area_m2':pixel_area}


def snap_pour_point(flow_acc_path: str, x: float, y: float, radius_m: float) -> dict:
    """Snap an outlet to the highest accumulation cell within a metric radius."""
    if not np.isfinite([x,y,radius_m]).all() or radius_m < 0:
        raise ValueError('Exutorio ou raio de ajuste invalido')
    with rasterio.open(flow_acc_path) as src:
        acc=src.read(1);transform=src.transform;crs=src.crs
    matrix=metric_jacobian(crs,transform);cell_size=np.sqrt(abs(float(np.linalg.det(matrix))))
    row,col=rasterio.transform.rowcol(transform,x,y)
    if not (0<=row<acc.shape[0] and 0<=col<acc.shape[1]): raise ValueError('Ponto de exutorio fora do modelo')
    radius=int(np.ceil(radius_m/cell_size));r0=max(0,row-radius);r1=min(acc.shape[0],row+radius+1);c0=max(0,col-radius);c1=min(acc.shape[1],col+radius+1)
    window=acc[r0:r1,c0:c1].astype(float)
    rr,cc=np.indices(window.shape);distance=np.hypot(rr+(r0-row),cc+(c0-col))*cell_size;window[distance>radius_m]=-np.inf
    if not np.isfinite(window).any(): raise ValueError('Sem celula valida proxima ao exutorio')
    local=np.unravel_index(np.nanargmax(window),window.shape);snapped_row=r0+local[0];snapped_col=c0+local[1]
    sx,sy=rasterio.transform.xy(transform,snapped_row,snapped_col)
    return {'requested_xy':[x,y],'snapped_xy':[sx,sy],'row':int(snapped_row),'col':int(snapped_col),
            'snap_distance_m':float(np.hypot(sx-x,sy-y)),'accumulation_cells':int(acc[snapped_row,snapped_col])}


def watershed_from_flow(flow_dir_path: str, output_path: str, row: int, col: int) -> dict:
    """Trace upstream D8 cells without constructing a per-cell adjacency dictionary."""
    with rasterio.open(flow_dir_path) as src:
        fdir=src.read(1);profile=src.profile.copy();transform=src.transform;crs=src.crs
    rows,cols=fdir.shape
    if not (0<=row<rows and 0<=col<cols): raise ValueError('Celula de exutorio fora do modelo')
    watershed=np.zeros((rows,cols),dtype='uint8');watershed[row,col]=1;queue=deque([(row,col)])
    while queue:
        current_r,current_c=queue.popleft()
        for direction,(dr,dc) in _D8_DIRS.items():
            upstream_r,upstream_c=current_r-dr,current_c-dc
            if 0<=upstream_r<rows and 0<=upstream_c<cols and not watershed[upstream_r,upstream_c] and fdir[upstream_r,upstream_c]==direction:
                watershed[upstream_r,upstream_c]=1;queue.append((upstream_r,upstream_c))
    _strip_block_options(profile).update(dtype='uint8',count=1,nodata=0,compress='lzw')
    with rasterio.open(output_path,'w',**profile) as dst: dst.write(watershed,1);dst.update_tags(operation='D8 watershed')
    pixel_area=abs(float(np.linalg.det(metric_jacobian(crs,transform))));cells=int(watershed.sum())
    return {'output_path':output_path,'watershed_cells':cells,'area_m2':cells*pixel_area,'area_ha':cells*pixel_area/10000,
            'pixel_area_m2':pixel_area}


def delineate_watershed(
    dtm_path: str,
    pour_point_coords: tuple[float, float],
    output_path: str,
) -> str:
    """
    Delineate a watershed by tracing upstream from a pour point.

    Steps:
    1. Fill sinks in the DTM.
    2. Compute flow direction.
    3. Trace all cells that drain to the pour point.
    4. Write the watershed mask as a GeoTIFF.

    Parameters
    ----------
    dtm_path : str
        Input DTM raster.
    pour_point_coords : tuple[float, float]
        (x, y) coordinates of the outlet in the raster's CRS.
    output_path : str
        Destination for the watershed mask GeoTIFF (1=in watershed, 0=outside).

    Returns
    -------
    str
        output_path on success.
    """
    import tempfile
    import os

    tmp_filled_fd, tmp_filled = tempfile.mkstemp(suffix="_filled.tif")
    tmp_fdir_fd, tmp_fdir = tempfile.mkstemp(suffix="_fdir.tif")
    os.close(tmp_filled_fd)
    os.close(tmp_fdir_fd)

    try:
        fill_sinks(dtm_path, tmp_filled)
        flow_direction(tmp_filled, tmp_fdir)

        with rasterio.open(tmp_fdir) as src:
            fdir = src.read(1).astype(np.int16)
            transform = src.transform
            profile = src.profile.copy()

        rows, cols = fdir.shape

        # Convert pour point coords to row, col
        inv_transform = ~transform
        px, py = pour_point_coords
        col_pp, row_pp = inv_transform * (px, py)
        col_pp, row_pp = int(round(col_pp)), int(round(row_pp))

        if not (0 <= row_pp < rows and 0 <= col_pp < cols):
            raise ValueError(
                f"Pour point ({px}, {py}) is outside raster bounds. "
                f"Row={row_pp}, Col={col_pp}, Shape=({rows},{cols})"
            )

        # Build reverse flow map: for each cell, find which cells flow into it
        # Then BFS upstream from pour point
        # Pre-compute: for each cell, where does it flow to?
        target_r = np.full((rows, cols), -1, dtype=np.int32)
        target_c = np.full((rows, cols), -1, dtype=np.int32)

        for i, (dr, dc) in enumerate(_D8_OFFSETS):
            direction_val = _D8_VALUES[i]
            mask = fdir == direction_val
            r_src, c_src = np.where(mask)
            r_dst = r_src + dr
            c_dst = c_src + dc
            valid = (r_dst >= 0) & (r_dst < rows) & (c_dst >= 0) & (c_dst < cols)
            target_r[r_src[valid], c_src[valid]] = r_dst[valid]
            target_c[r_src[valid], c_src[valid]] = c_dst[valid]

        # BFS upstream from pour point
        watershed = np.zeros((rows, cols), dtype=np.uint8)
        from collections import deque

        # Build reverse adjacency: who flows into (r,c)?
        # For efficiency, iterate through all cells and record their target
        reverse_adj = {}
        for r in range(rows):
            for c in range(cols):
                tr, tc = target_r[r, c], target_c[r, c]
                if tr >= 0 and tc >= 0:
                    key = (tr, tc)
                    if key not in reverse_adj:
                        reverse_adj[key] = []
                    reverse_adj[key].append((r, c))

        queue = deque()
        queue.append((row_pp, col_pp))
        watershed[row_pp, col_pp] = 1

        while queue:
            r, c = queue.popleft()
            for ur, uc in reverse_adj.get((r, c), []):
                if watershed[ur, uc] == 0:
                    watershed[ur, uc] = 1
                    queue.append((ur, uc))

    finally:
        for p in (tmp_filled, tmp_fdir):
            if os.path.exists(p):
                os.remove(p)

        _strip_block_options(profile).update(dtype=rasterio.uint8, count=1, compress="lzw", nodata=0)

    with rasterio.open(output_path, "w", **profile) as dst:
        dst.write(watershed, 1)

    watershed_cells = int(np.sum(watershed))
    logger.info("Watershed delineated: %d cells, written to %s", watershed_cells, output_path)
    return output_path


def calc_twi(
    slope_path: str,
    flow_acc_path: str,
    output_path: str,
) -> str:
    """
    Calculate the Topographic Wetness Index: TWI = ln(a / tan(b))

    where:
    - a = specific catchment area (flow accumulation * cell area / cell width)
    - b = slope in radians

    Parameters
    ----------
    slope_path : str
        Slope raster in degrees.
    flow_acc_path : str
        Flow accumulation raster (cell counts).
    output_path : str
        Destination TWI raster.

    Returns
    -------
    str
        output_path on success.
    """
    with rasterio.open(slope_path) as src:
        slope_deg = src.read(1).astype(np.float64)
        transform = src.transform
        profile = src.profile.copy()
        nodata_slope = src.nodata

    with rasterio.open(flow_acc_path) as src:
        flow_acc = src.read(1).astype(np.float64)

    cell_size = abs(transform.a)
    # Specific catchment area
    sca = flow_acc * (cell_size ** 2) / cell_size  # = flow_acc * cell_size

    # Slope in radians, avoid zero
    slope_rad = np.radians(slope_deg)
    slope_rad[slope_rad < 0.001] = 0.001

    tan_slope = np.tan(slope_rad)
    tan_slope[tan_slope < 1e-10] = 1e-10

    twi = np.log(sca / tan_slope)
    twi[~np.isfinite(twi)] = -9999.0

    if nodata_slope is not None:
        twi[slope_deg == nodata_slope] = -9999.0

    _strip_block_options(profile).update(dtype=rasterio.float32, count=1, compress="lzw", nodata=-9999.0)

    with rasterio.open(output_path, "w", **profile) as dst:
        dst.write(twi.astype(np.float32), 1)

    logger.info("TWI raster written to %s", output_path)
    return output_path
