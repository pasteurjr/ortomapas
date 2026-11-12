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
    # The filled surface is persisted as float32.  A fixed 1e-6 m increment
    # can round away at ordinary terrain elevations (for example, the float32
    # ULP near 300 m is about 3e-5 m), leaving flats unresolved for D8.  Use a
    # small increment that survives that conversion while remaining far below
    # the source DEM's vertical precision.
    elevation_scale=max(float(np.nanmax(np.abs(values[valid]))),1.0)
    float32_ulp=abs(float(np.spacing(np.float32(elevation_scale))))
    epsilon=max(float(np.nanmax(values[valid])-np.nanmin(values[valid]))*1e-9,
                float32_ulp*2,1e-6)
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


def condition_dem_with_hydrography(dtm_path: str, hydrography_path: str, output_path: str,
                                   burn_depth_m: float = 0.05) -> dict:
    """Condition a filled DEM along supplied linework before D8 routing.

    3D linework uses its vertex elevations. For 2D connectors, a continuous
    profile is interpolated between the DEM elevations at the clipped line
    endpoints. The conditioning is opt-in because vector hydrography can be
    incomplete or inconsistent with the source terrain.
    """
    import fiona
    from pyproj import CRS, Transformer
    from shapely.geometry import Point, box
    from shapely.ops import transform as transform_geometry
    from rasterio.features import rasterize

    if not np.isfinite(burn_depth_m) or not 0 <= burn_depth_m <= 20:
        raise ValueError('Profundidade de condicionamento deve ficar entre 0 e 20 m')
    with rasterio.open(dtm_path) as src:
        surface = src.read(1).astype(np.float64)
        profile = src.profile.copy()
        transform = src.transform
        raster_crs = src.crs
        nodata = src.nodata
        valid = np.isfinite(surface)
        if nodata is not None:
            valid &= surface != nodata
        if raster_crs is None:
            raise ValueError('DEM precisa ter sistema de coordenadas definido')
        bounds = box(*src.bounds)

    conditioned = surface.copy()
    features_used = 0
    cells_conditioned = 0
    max_cut = 0.0

    def lines_from(geometry):
        if geometry.geom_type == 'LineString':
            return [geometry]
        if geometry.geom_type in {'MultiLineString', 'GeometryCollection'}:
            return [line for part in geometry.geoms for line in lines_from(part)]
        return []

    with fiona.open(hydrography_path) as collection:
        source_crs = collection.crs_wkt or collection.crs or 'EPSG:4326'
        try:
            transformer = Transformer.from_crs(CRS.from_user_input(source_crs), raster_crs, always_xy=True)
        except Exception as exc:
            raise ValueError('CRS da hidrografia invalido') from exc
        for feature in collection:
            if not feature.get('geometry'):
                continue
            source_geometry = shape(feature['geometry'])
            projected = transform_geometry(
                lambda x, y, z=None: (*transformer.transform(x, y), z) if z is not None
                else transformer.transform(x, y), source_geometry)
            for candidate in lines_from(projected.intersection(bounds)):
                if candidate.length <= 0 or len(candidate.coords) < 2:
                    continue
                line_mask = rasterize([(mapping(candidate), 1)], out_shape=surface.shape,
                                      transform=transform, fill=0, all_touched=True).astype(bool)
                line_mask &= valid
                rows, cols = np.where(line_mask)
                if not rows.size:
                    continue
                xs = transform.c + transform.a * (cols + 0.5) + transform.b * (rows + 0.5)
                ys = transform.f + transform.d * (cols + 0.5) + transform.e * (rows + 0.5)
                measures = [candidate.project(Point(float(x), float(y))) for x, y in zip(xs, ys)]
                if candidate.has_z:
                    targets = np.asarray([candidate.interpolate(float(m)).z for m in measures]) - burn_depth_m
                else:
                    start_row, start_col = rasterio.transform.rowcol(transform, *candidate.coords[0][:2])
                    end_row, end_col = rasterio.transform.rowcol(transform, *candidate.coords[-1][:2])
                    start_row = min(max(int(start_row), 0), surface.shape[0] - 1)
                    end_row = min(max(int(end_row), 0), surface.shape[0] - 1)
                    start_col = min(max(int(start_col), 0), surface.shape[1] - 1)
                    end_col = min(max(int(end_col), 0), surface.shape[1] - 1)
                    z_start = float(surface[start_row, start_col])
                    z_end = float(surface[end_row, end_col])
                    targets = z_start + (z_end - z_start) * (np.asarray(measures) / candidate.length) - burn_depth_m
                old = conditioned[rows, cols].copy()
                conditioned[rows, cols] = np.minimum(old, targets)
                cuts = old - conditioned[rows, cols]
                features_used += 1
                cells_conditioned += int(np.count_nonzero(cuts > 0))
                if cuts.size:
                    max_cut = max(max_cut, float(np.max(cuts)))

    if not features_used:
        raise ValueError('Nenhuma linha de hidrografia intersecta o DEM')
    _strip_block_options(profile).update(dtype=rasterio.float32, count=1, compress='lzw')
    with rasterio.open(output_path, 'w', **profile) as dst:
        dst.write(conditioned.astype(np.float32), 1)
        dst.update_tags(operation='hydrography-conditioned-dem',
                        hydrography_source=str(hydrography_path),
                        burn_depth_m=burn_depth_m, features_used=features_used,
                        cells_conditioned=cells_conditioned, maximum_cut_m=max_cut)
    return {'output_path': output_path, 'features_used': features_used,
            'cells_conditioned': cells_conditioned, 'burn_depth_m': float(burn_depth_m),
            'maximum_cut_m': max_cut}


def flow_direction(dtm_path: str, output_path: str) -> str:
    """
    Compute D8 flow direction from a DTM.

    Each cell is assigned the direction (D8 encoding) towards the steepest
    meaningful downslope neighbour. Elevation differences within the float32
    rounding tolerance are resolved across the flat toward a downhill seed.

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
    valid = np.isfinite(dem)
    if nodata is not None:
        valid &= dem != nodata
    if not valid.any():
        raise ValueError('Modelo de terreno sem celulas validas')

    # Float32 DEMs often contain artificial sub-millimetre gradients after
    # sink filling. Treat differences within several representable float32
    # steps as flats, then route those cells toward the nearest cell that has
    # a meaningful downslope direction. This avoids letting raster write
    # rounding and priority-queue tie order choose a drainage path.
    elevation_scale = max(float(np.max(np.abs(dem[valid]))), 1.0)
    float32_ulp = abs(float(np.spacing(np.float32(elevation_scale))))
    flat_tolerance = max(float32_ulp * 8.0, 1e-7)

    matrix=metric_jacobian(crs,transform)
    distances=[float(np.linalg.norm(matrix@np.array([dc,dr]))) for dr,dc in _D8_OFFSETS]

    safe_dem = np.where(valid, dem, np.nan)
    padded = np.pad(safe_dem, 1, mode="constant", constant_values=np.nan)
    flow_dir = np.zeros((rows, cols), dtype=np.int16)

    max_slope = np.full((rows, cols), -np.inf)

    for i, (dr, dc) in enumerate(_D8_OFFSETS):
        neighbour = padded[1 + dr: rows + 1 + dr, 1 + dc: cols + 1 + dc]
        elevation_drop = safe_dem - neighbour
        slope = elevation_drop / distances[i]
        update_mask = valid & np.isfinite(slope) & (elevation_drop > flat_tolerance) & (slope > max_slope)
        max_slope[update_mask] = slope[update_mask]
        flow_dir[update_mask] = _D8_VALUES[i]

    # Resolve near-flat cells with a deterministic multi-source breadth-first
    # traversal. Each assigned cell points to an already-routed neighbor, so
    # the flat routing is acyclic and ultimately reaches a downslope seed.
    from collections import deque
    queue = deque(map(tuple, np.argwhere(valid & (flow_dir != 0))))
    reverse_direction = {(-dr, -dc): value for value, (dr, dc) in _D8_DIRS.items()}
    flats_resolved = 0
    while queue:
        row, col = queue.popleft()
        for dr, dc in _D8_OFFSETS:
            nr, nc = row + dr, col + dc
            if (0 <= nr < rows and 0 <= nc < cols and valid[nr, nc]
                    and flow_dir[nr, nc] == 0
                    and abs(float(dem[nr, nc] - dem[row, col])) <= flat_tolerance):
                flow_dir[nr, nc] = reverse_direction[(dr, dc)]
                flats_resolved += 1
                queue.append((nr, nc))

    _strip_block_options(profile).update(dtype=rasterio.int16, count=1, compress="lzw", nodata=0)

    with rasterio.open(output_path, "w", **profile) as dst:
        dst.write(flow_dir, 1)
        dst.update_tags(operation='d8-flow-direction', flat_tolerance_m=flat_tolerance,
                        near_flat_cells_resolved=flats_resolved)

    logger.info("Flow direction raster written to %s (flat tolerance %.8g m, near-flat cells resolved %d)",
                output_path, flat_tolerance, flats_resolved)
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
                         minimum_area_m2: float, minimum_strahler_order: int = 1) -> dict:
    """Vectorize D8 links by contributing area and optional Strahler order.

    The area threshold identifies candidate channel cells. Strahler order can
    then suppress low-order headwater branches when a generalized network is
    wanted; order 1 preserves the historical all-channel behavior.
    """
    if not np.isfinite(minimum_area_m2) or minimum_area_m2 <= 0:
        raise ValueError('Area contribuinte minima deve ser positiva')
    if isinstance(minimum_strahler_order, bool) or int(minimum_strahler_order) != minimum_strahler_order or not 1 <= int(minimum_strahler_order) <= 12:
        raise ValueError('Ordem de Strahler minima deve ser um inteiro entre 1 e 12')
    minimum_strahler_order = int(minimum_strahler_order)
    with rasterio.open(flow_acc_path) as acc_src,rasterio.open(flow_dir_path) as dir_src:
        acc=acc_src.read(1, masked=True).filled(0);fdir=dir_src.read(1);transform=acc_src.transform;crs=acc_src.crs
    matrix=metric_jacobian(crs,transform);pixel_area=abs(float(np.linalg.det(matrix)))
    threshold=max(1,int(np.ceil(minimum_area_m2/pixel_area)));candidate=acc>=threshold
    # Compute Strahler order on the candidate D8 graph. A topological queue is
    # used instead of elevation sorting so equal accumulation values remain safe.
    indegree=np.zeros(fdir.shape,dtype=np.uint8)
    receiver=np.full(fdir.size,-1,dtype=np.int64)
    for direction,(dr,dc) in _D8_DIRS.items():
        rows,cols=np.where(candidate & (fdir==direction))
        tr,tc=rows+dr,cols+dc
        keep=(tr>=0)&(tr<fdir.shape[0])&(tc>=0)&(tc<fdir.shape[1])
        rows,cols,tr,tc=rows[keep],cols[keep],tr[keep],tc[keep]
        keep=candidate[tr,tc]
        rows,cols,tr,tc=rows[keep],cols[keep],tr[keep],tc[keep]
        indegree[tr,tc]+=1
        receiver[rows*fdir.shape[1]+cols]=tr*fdir.shape[1]+tc
    order=np.zeros(fdir.shape,dtype=np.uint8)
    max_upstream_order=np.zeros_like(order)
    max_order_count=np.zeros_like(order)
    queue=deque((int(r),int(c)) for r,c in np.argwhere(candidate & (indegree==0)))
    processed=0
    while queue:
        row,col=queue.popleft();processed+=1
        if order[row,col]==0:
            order[row,col]=1
        target_id=int(receiver[row*fdir.shape[1]+col])
        if target_id>=0:
            target_row,target_col=divmod(target_id,fdir.shape[1])
            if not candidate[target_row,target_col]:
                continue
            source_order=int(order[row,col])
            if source_order>max_upstream_order[target_row,target_col]:
                max_upstream_order[target_row,target_col]=source_order
                max_order_count[target_row,target_col]=1
            elif source_order==max_upstream_order[target_row,target_col]:
                max_order_count[target_row,target_col]+=1
            indegree[target_row,target_col]-=1
            if indegree[target_row,target_col]==0:
                order[target_row,target_col]=max_upstream_order[target_row,target_col]+(
                    max_order_count[target_row,target_col]>=2)
                queue.append((target_row,target_col))
    if processed!=int(candidate.sum()):
        raise ValueError('A rede D8 candidata contém ciclo; não é possível calcular a ordem de Strahler')
    stream=candidate & (order>=minimum_strahler_order)
    segments_by_order={};length_by_order={}
    for row,col in zip(*np.where(stream)):
        target_id=int(receiver[row*fdir.shape[1]+col])
        if target_id<0:
            continue
        tr,tc=divmod(target_id,fdir.shape[1])
        if not stream[tr,tc]:
            continue
        dr,dc=tr-row,tc-col
        x1,y1=rasterio.transform.xy(transform,row,col);x2,y2=rasterio.transform.xy(transform,tr,tc)
        stream_order=int(order[row,col])
        segments_by_order.setdefault(stream_order,[]).append(LineString([(x1,y1),(x2,y2)]))
        length_by_order[stream_order]=length_by_order.get(stream_order,0.0)+float(
            np.linalg.norm(matrix@np.array([dc,dr])))
    if not segments_by_order:
        raise ValueError('Nenhum canal atingiu a area contribuinte minima')
    features=[];number=0
    for stream_order,segments in sorted(segments_by_order.items()):
        merged=linemerge(unary_union(segments));parts=list(merged.geoms) if merged.geom_type=='MultiLineString' else [merged]
        for line in parts:
            number+=1
            geometry=transform_geom(crs,'EPSG:4326',mapping(line),precision=8)
            features.append({'type':'Feature','geometry':geometry,'properties':{'segmento':number,
                              'ordem_strahler':stream_order,
                              'ordem_strahler_minima':minimum_strahler_order}})
    geojson={'type':'FeatureCollection','features':features}
    with open(output_geojson_path,'w',encoding='utf-8') as stream_file: json.dump(geojson,stream_file)
    return {'output_path':output_geojson_path,'geojson':geojson,'feature_count':len(features),
            'stream_cells':int(stream.sum()),'candidate_cells':int(candidate.sum()),
            'minimum_area_m2':minimum_area_m2,'minimum_strahler_order':minimum_strahler_order,
            'maximum_strahler_order':int(order.max()),
            'order_lengths_m':{str(key):value for key,value in sorted(length_by_order.items())},
            'threshold_cells':threshold,'total_length_m':sum(length_by_order.values()),'pixel_area_m2':pixel_area}


def snap_pour_point(flow_acc_path: str, x: float, y: float, radius_m: float) -> dict:
    """Snap an outlet to the highest-accumulation pixel center in a metric radius.

    The search radius is measured from the requested map coordinate to pixel
    centers in map units. A zero radius means use the pixel containing the
    requested point without searching neighboring cells.
    """
    if not np.isfinite([x,y,radius_m]).all() or radius_m < 0:
        raise ValueError('Exutorio ou raio de ajuste invalido')
    with rasterio.open(flow_acc_path) as src:
        acc=src.read(1, masked=True).astype(float).filled(np.nan)
        transform=src.transform;crs=src.crs
    matrix=metric_jacobian(crs,transform)
    col_float,row_float=(~transform)*(x,y)
    row,col=int(np.floor(row_float)),int(np.floor(col_float))
    if not (0<=row<acc.shape[0] and 0<=col<acc.shape[1]): raise ValueError('Ponto de exutorio fora do modelo')
    if radius_m == 0:
        snapped_row,snapped_col=row,col
        if not np.isfinite(acc[snapped_row,snapped_col]):
            raise ValueError('Celula do exutorio sem acumulacao valida')
    else:
        inverse=np.linalg.inv(matrix)
        row_radius=int(np.ceil(radius_m*np.linalg.norm(inverse[1,:])))+1
        col_radius=int(np.ceil(radius_m*np.linalg.norm(inverse[0,:])))+1
        r0=max(0,row-row_radius);r1=min(acc.shape[0],row+row_radius+1)
        c0=max(0,col-col_radius);c1=min(acc.shape[1],col+col_radius+1)
        window=acc[r0:r1,c0:c1]
        rr,cc=np.indices(window.shape)
        dcol=cc+c0+0.5-col_float;drow=rr+r0+0.5-row_float
        dx=matrix[0,0]*dcol+matrix[0,1]*drow
        dy=matrix[1,0]*dcol+matrix[1,1]*drow
        distance=np.hypot(dx,dy)
        window=np.where(distance<=radius_m,window,-np.inf)
        if not np.isfinite(window).any(): raise ValueError('Sem celula valida proxima ao exutorio dentro do raio')
        maximum=np.nanmax(window)
        tied=np.argwhere(window==maximum)
        tied_distances=distance[tied[:,0],tied[:,1]]
        local=tuple(tied[np.argmin(tied_distances)])
        snapped_row,snapped_col=r0+local[0],c0+local[1]
    sx,sy=rasterio.transform.xy(transform,snapped_row,snapped_col)
    dcol=snapped_col+0.5-col_float;drow=snapped_row+0.5-row_float
    delta=matrix@np.array([dcol,drow])
    actual_distance=float(np.linalg.norm(delta))
    return {'requested_xy':[x,y],'snapped_xy':[sx,sy],'row':int(snapped_row),'col':int(snapped_col),
            'snap_distance_m':actual_distance,'accumulation_cells':int(acc[snapped_row,snapped_col]),
            'snap_strategy':'containing_cell' if radius_m==0 else 'maximum_accumulation_within_center_radius'}


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
