"""
Hydrology analysis tools for DTM/DSM rasters.

Implements sink filling, D8 flow direction, flow accumulation, stream
extraction, watershed delineation, and Topographic Wetness Index (TWI).
"""

import json
import logging

import numpy as np
import rasterio
from rasterio.features import shapes as rasterio_shapes

logger = logging.getLogger(__name__)

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
        dem = src.read(1).astype(np.float64)
        profile = src.profile.copy()
        nodata = src.nodata

    if nodata is not None:
        mask = dem == nodata
    else:
        mask = ~np.isfinite(dem)

    filled = dem.copy()
    rows, cols = filled.shape

    max_iterations = 1000
    for iteration in range(max_iterations):
        changed = False
        # Pad with large value for boundary handling
        padded = np.pad(filled, 1, mode="constant", constant_values=np.inf)

        for dr, dc in _D8_OFFSETS:
            neighbour = padded[1 + dr: rows + 1 + dr, 1 + dc: cols + 1 + dc]
            # Where current cell is lower than this neighbour is tracked
            # We need: for each cell, the minimum neighbour value
            pass  # handled below

        # Compute min of all 8 neighbours
        min_neighbour = np.full_like(filled, np.inf)
        for dr, dc in _D8_OFFSETS:
            neighbour = padded[1 + dr: rows + 1 + dr, 1 + dc: cols + 1 + dc]
            min_neighbour = np.minimum(min_neighbour, neighbour)

        # Cells that are sinks: lower than all neighbours (i.e., lower than min_neighbour)
        # Raise them to min_neighbour + tiny increment
        sink_mask = (filled < min_neighbour) & (~mask)
        # Only fill interior sinks, not valid drainage to edges
        # A true sink is where cell < min_neighbour by more than float precision
        epsilon = 1e-5
        to_fill = sink_mask & ((min_neighbour - filled) > epsilon)

        if not np.any(to_fill):
            break

        filled[to_fill] = min_neighbour[to_fill] + epsilon
        changed = True

        if not changed:
            break

    # Restore nodata
    if nodata is not None:
        filled[mask] = nodata

    profile.update(dtype=rasterio.float32, count=1, compress="lzw")

    with rasterio.open(output_path, "w", **profile) as dst:
        dst.write(filled.astype(np.float32), 1)

    logger.info("Sink-filled DTM written to %s (iterations=%d)", output_path, iteration + 1)
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

    rows, cols = dem.shape
    dx = abs(transform.a)
    dy = abs(transform.e)

    # Distance to each neighbour
    distances = []
    for dr, dc in _D8_OFFSETS:
        dist = np.sqrt((dr * dy) ** 2 + (dc * dx) ** 2)
        distances.append(dist)

    padded = np.pad(dem, 1, mode="constant", constant_values=np.nan)
    flow_dir = np.zeros((rows, cols), dtype=np.int16)

    max_slope = np.full((rows, cols), -np.inf)

    for i, (dr, dc) in enumerate(_D8_OFFSETS):
        neighbour = padded[1 + dr: rows + 1 + dr, 1 + dc: cols + 1 + dc]
        slope = (dem - neighbour) / distances[i]
        update_mask = slope > max_slope
        max_slope[update_mask] = slope[update_mask]
        flow_dir[update_mask] = _D8_VALUES[i]

    # Flat areas and nodata get direction 0
    if nodata is not None:
        flow_dir[dem == nodata] = 0

    profile.update(dtype=rasterio.int16, count=1, compress="lzw", nodata=0)

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
        for rr, cc in zip(r_dst, c_dst):
            inflow_count[rr, cc] += 1

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

    profile.update(dtype=rasterio.int32, count=1, compress="lzw", nodata=0)

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

    profile.update(dtype=rasterio.uint8, count=1, compress="lzw", nodata=0)

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

    profile.update(dtype=rasterio.float32, count=1, compress="lzw", nodata=-9999.0)

    with rasterio.open(output_path, "w", **profile) as dst:
        dst.write(twi.astype(np.float32), 1)

    logger.info("TWI raster written to %s", output_path)
    return output_path
