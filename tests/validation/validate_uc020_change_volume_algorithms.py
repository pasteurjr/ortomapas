"""Deterministic core checks for the UC-020 change/volume queue operations.

Run with the repository Conda environment:
  python tests/validation/validate_uc020_change_volume_algorithms.py
The fixtures are synthetic and validate algorithm contracts, not field accuracy.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import from_origin

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from backend.tools.change_detection import change_statistics, detect_changes
from backend.tools.volumetry import calc_volume


def write_raster(path: Path, data: np.ndarray, dtype: str) -> None:
    count, height, width = data.shape
    with rasterio.open(path, "w", driver="GTiff", width=width, height=height,
                       count=count, dtype=dtype, crs="EPSG:32623",
                       transform=from_origin(500000, 8000000, 2, 2), nodata=None) as dst:
        dst.write(data.astype(dtype))


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="uc020-change-volume-") as folder:
        root = Path(folder)
        before = np.zeros((3, 8, 8), dtype=np.uint8)
        after = before.copy()
        after[:, 2:4, 3:5] = 100
        p_before, p_after, p_mask = root / "before.tif", root / "after.tif", root / "mask.tif"
        write_raster(p_before, before, "uint8")
        write_raster(p_after, after, "uint8")
        detect_changes(str(p_before), str(p_after), str(p_mask), threshold=50)
        change_stats = change_statistics(str(p_mask))
        with rasterio.open(p_mask) as raster:
            changed_pixels = int(np.count_nonzero(raster.read(1) == 255))
        assert changed_pixels == 4, changed_pixels
        assert change_stats["changed_pixels"] == 4, change_stats

        dem = np.array([[11, 11, 11], [9, 9, 9], [10, 10, 10]], dtype=np.float32)[None, :, :]
        p_dem, p_volume = root / "dem.tif", root / "volume.tif"
        write_raster(p_dem, dem, "float32")
        volume = calc_volume(str(p_dem), 10.0, str(p_volume))
        assert volume["volume_above_m3"] == 12.0, volume
        assert volume["volume_below_m3"] == 12.0, volume
        assert volume["net_volume_m3"] == 0.0, volume
        assert volume["valid_pixels"] == 9, volume
        result = {
            "classification": "synthetic deterministic fixture; not field accuracy",
            "change_rgb": {"expected_changed_pixels": 4, "actual_changed_pixels": changed_pixels,
                           "threshold_dn": 50, "result": "PASS"},
            "volume": {"expected_cut_m3": 12.0, "actual_cut_m3": volume["volume_above_m3"],
                       "expected_fill_m3": 12.0, "actual_fill_m3": volume["volume_below_m3"],
                       "expected_net_m3": 0.0, "actual_net_m3": volume["net_volume_m3"],
                       "pixel_size_m": 2, "result": "PASS"},
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
